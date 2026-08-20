"""
Spectral indices + unsupervised clustering to separate mine-associated
surface classes (tailings/waste-rock, mine water, vegetation, undisturbed
ground) at Noamundi -- the discrimination the existing Hyperion literature
here has never actually done (ore-grade mapping and forest-health threads
both skip tailings/waste-water entirely).

Indices used:
  NDVI        -- standard red/NIR vegetation index
  Iron Oxide  -- R860/R660 ferric-iron ratio (Segal-style), flags oxidized
                 waste-rock / tailings (high in ferric iron -- literally why
                 the mine is called "Noamundi", iron ore)
  BD2200      -- continuum-removed band depth at ~2200nm (Al-OH / Fe-OH
                 absorption). This is the diagnostic feature for jarosite
                 and other sulfate/clay alteration minerals that precipitate
                 from acid mine drainage -- same feature the Iberian Pyrite
                 Belt paper used to map AMD-affected ground with Hyperion.
  Water Index -- (Green-NIR)/(Green+NIR), flags mine pits / settling ponds

Then: K-means on the full clean 163-band cube to get natural material
clusters, cross-referenced against the indices to label them.
"""
import os
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIF = os.path.join(BASE, "Noamundi_Hyperion_16Apr2011.tif")
OUT = os.path.join(BASE, "outputs")

PALETTE = {
    "bg_main": "#0A1B26", "bg_card": "#122B3C",
    "text_primary": "#F2F2F0", "text_secondary": "#A9D3C5",
}


def nearest_band(wavelengths, good_idx, target_nm):
    sub = wavelengths[good_idx]
    i = np.argmin(np.abs(sub - target_nm))
    return good_idx[i]


def band_depth(cube, wavelengths, good_idx, center_nm, left_nm, right_nm):
    bc = nearest_band(wavelengths, good_idx, center_nm)
    bl = nearest_band(wavelengths, good_idx, left_nm)
    br = nearest_band(wavelengths, good_idx, right_nm)
    wl_c, wl_l, wl_r = wavelengths[bc], wavelengths[bl], wavelengths[br]
    frac = (wl_c - wl_l) / (wl_r - wl_l) if wl_r != wl_l else 0.5
    continuum = cube[bl] + frac * (cube[br] - cube[bl])
    with np.errstate(divide="ignore", invalid="ignore"):
        depth = 1.0 - np.divide(cube[bc], continuum, out=np.ones_like(continuum), where=continuum > 0)
    return np.clip(depth, -1, 1)


def main():
    data = np.load(os.path.join(OUT, "cube_qa.npz"))
    cube, wavelengths, good_idx, valid_mask = (
        data["cube"], data["wavelengths"], data["good_idx"], data["valid_mask"]
    )
    rows, cols = valid_mask.shape

    b_red = nearest_band(wavelengths, good_idx, 660)
    b_nir = nearest_band(wavelengths, good_idx, 860)
    b_green = nearest_band(wavelengths, good_idx, 550)

    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = np.divide(cube[b_nir] - cube[b_red], cube[b_nir] + cube[b_red],
                          out=np.zeros((rows, cols), dtype=np.float32), where=(cube[b_nir] + cube[b_red]) > 0)
        water_idx = np.divide(cube[b_green] - cube[b_nir], cube[b_green] + cube[b_nir],
                               out=np.zeros((rows, cols), dtype=np.float32), where=(cube[b_green] + cube[b_nir]) > 0)

    # ferric iron (Fe3+) diagnostic absorption is a trough centered ~860-900nm,
    # not a simple two-band ratio -- continuum-removed band depth is the
    # correct way to isolate it, same method as the clay/jarosite feature below
    iron_oxide = band_depth(cube, wavelengths, good_idx, 870, 700, 1050)
    bd2200 = band_depth(cube, wavelengths, good_idx, 2200, 2120, 2350)

    for name, arr in [("ndvi", ndvi), ("iron_oxide", iron_oxide), ("water_idx", water_idx), ("bd2200", bd2200)]:
        arr[~valid_mask] = np.nan

    # ---- K-means on clean bands, SHAPE-normalized per pixel ----
    # Dividing each pixel's spectrum by its own mean removes overall
    # brightness (topography/shadow/illumination angle) so clustering groups
    # by spectral shape -- i.e. material composition -- instead of by how
    # sunlit a pixel happened to be. Skipping this the first time round just
    # reproduced a brightness map, not a material map.
    X = cube[good_idx][:, valid_mask].T  # (n_valid_px, n_bands)
    px_mean = X.mean(axis=1, keepdims=True)
    px_mean = np.where(px_mean > 0, px_mean, 1)
    Xn = X / px_mean

    K = 6
    km = KMeans(n_clusters=K, random_state=42, n_init=10).fit(Xn)
    labels = np.full((rows, cols), -1, dtype=np.int16)
    labels[valid_mask] = km.labels_

    # per-cluster mean index values, to auto-label clusters
    print(f"\n{'cluster':>7} | {'px':>6} | {'NDVI':>7} | {'IronOx':>7} | {'WaterIdx':>8} | {'BD2200':>7}")
    cluster_stats = []
    for c in range(K):
        m = labels == c
        n = m.sum()
        s = dict(cluster=c, n=n,
                 ndvi=float(np.nanmean(ndvi[m])), iron=float(np.nanmean(iron_oxide[m])),
                 water=float(np.nanmean(water_idx[m])), bd2200=float(np.nanmean(bd2200[m])))
        cluster_stats.append(s)
        print(f"{c:>7} | {n:>6} | {s['ndvi']:>7.3f} | {s['iron']:>7.3f} | {s['water']:>8.3f} | {s['bd2200']:>7.3f}")

    # ---- mean spectral profile per cluster (the key gap-filling figure) ----
    fig, ax = plt.subplots(figsize=(11, 5))
    colors = plt.cm.tab10(np.linspace(0, 1, K))
    wl_kept = wavelengths[good_idx]
    for c in range(K):
        m = labels == c
        profile = cube[good_idx][:, m].mean(axis=1)
        ax.plot(wl_kept, profile, label=f"Cluster {c} (n={m.sum()})", color=colors[c], linewidth=1.6)
    ax.set_xlabel("Wavelength (nm, approx.)")
    ax.set_ylabel("Mean radiance DN")
    ax.set_title("Noamundi -- mean spectral profile per unsupervised cluster")
    ax.legend(fontsize=8, ncol=2)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "cluster_spectral_profiles.png"), dpi=150)
    plt.close(fig)

    # ---- save everything for the mapping step ----
    with rasterio.open(TIF) as src:
        profile = src.profile
        transform = src.transform
        crs = src.crs

    np.savez(
        os.path.join(OUT, "classification.npz"),
        labels=labels, ndvi=ndvi, iron_oxide=iron_oxide, water_idx=water_idx, bd2200=bd2200,
        valid_mask=valid_mask, cluster_stats=cluster_stats,
    )

    out_profile = profile.copy()
    out_profile.update(count=1, dtype="int16", nodata=-1)
    with rasterio.open(os.path.join(OUT, "classification.tif"), "w", **out_profile) as dst:
        dst.write(labels.astype(np.int16), 1)

    print("\nSaved: outputs/cluster_spectral_profiles.png, outputs/classification.npz, outputs/classification.tif")


if __name__ == "__main__":
    main()
