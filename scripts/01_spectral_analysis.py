"""
Noamundi Hyperion scene -- band QA, spectral indices, and unsupervised
material discrimination for tailings / waste-rock / mine-water bodies.

Working notes:
- Scene is EO-1 Hyperion, 16 Apr 2011, GEE EO1/HYPERION export, 198 calibrated
  bands (B008-B057 VNIR, B077-B224 SWIR -- the standard "good band" subset,
  the 44 non-functioning/overlap bands are already stripped by GEE).
- No atmospheric correction available for this AOI, so I'm working with
  radiance DN and doing percentile-stretch normalization per band -- fine for
  relative material discrimination within one scene, which is all a
  case-study needs. Flagging this instead of pretending it's surface reflectance.
- Wavelength centers use the standard linear approximation for Hyperion's two
  spectrometer arrays (VNIR ~355.6nm start / SWIR ~852.4nm start, ~10.1nm
  spacing) -- close enough for index band selection, not for lab-grade
  mineral ID.
"""
import os
import numpy as np
import rasterio
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIF = os.path.join(BASE, "Noamundi_Hyperion_16Apr2011.tif")
OUT = os.path.join(BASE, "outputs")
os.makedirs(OUT, exist_ok=True)


def band_wavelength(band_num):
    """Approximate center wavelength (nm) for a Hyperion band number."""
    if band_num <= 70:
        return 355.59 + (band_num - 1) * 10.0184
    return 852.44 + (band_num - 71) * 10.0862


def load_cube():
    with rasterio.open(TIF) as src:
        cube = src.read().astype(np.float32)  # (bands, rows, cols)
        band_nums = [int(d[1:]) for d in src.descriptions]
        profile = src.profile
        transform = src.transform
        crs = src.crs
    wavelengths = np.array([band_wavelength(b) for b in band_nums])
    valid_mask = cube[0] > 0  # 0 = outside AOI circle (export artifact)
    for b in range(cube.shape[0]):
        valid_mask &= (cube[b] >= 0)
    return cube, band_nums, wavelengths, valid_mask, profile, transform, crs


def flag_bad_bands(cube, valid_mask, wavelengths):
    """Auto-flag low-signal / noisy bands instead of hardcoding a list."""
    n_bands = cube.shape[0]
    means = np.array([cube[b][valid_mask].mean() for b in range(n_bands)])
    stds = np.array([cube[b][valid_mask].std() for b in range(n_bands)])
    snr = np.divide(means, stds, out=np.zeros_like(means), where=stds > 0)

    # water-vapor absorption windows (SWIR) -- signal genuinely collapses here
    water_vapor_windows = [(1330, 1490), (1780, 1970)]
    in_water_vapor = np.zeros(n_bands, dtype=bool)
    for lo, hi in water_vapor_windows:
        in_water_vapor |= (wavelengths >= lo) & (wavelengths <= hi)

    low_signal = means < np.percentile(means, 8)  # bottom ~8% mean DN
    bad = in_water_vapor | low_signal
    good_idx = np.where(~bad)[0]
    print(f"Bands total: {n_bands} | flagged bad/noisy: {bad.sum()} | kept: {len(good_idx)}")
    return good_idx, means, stds, snr


def save_signal_qa_plot(wavelengths, means, bad_mask):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(wavelengths, means, color="#307B8E", linewidth=1.2, label="mean DN (all bands)")
    ax.scatter(wavelengths[bad_mask], means[bad_mask], color="#C0392B", s=10,
               label="flagged bad/noisy", zorder=5)
    ax.set_xlabel("Wavelength (nm, approx.)")
    ax.set_ylabel("Mean radiance DN")
    ax.set_title("Noamundi Hyperion -- band signal QA (16 Apr 2011)")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "band_signal_qa.png"), dpi=150)
    plt.close(fig)


def nearest_band(wavelengths, good_idx, target_nm):
    sub = wavelengths[good_idx]
    i = np.argmin(np.abs(sub - target_nm))
    return good_idx[i]


def main():
    cube, band_nums, wavelengths, valid_mask, profile, transform, crs = load_cube()
    good_idx, means, stds, snr = flag_bad_bands(cube, valid_mask, wavelengths)
    bad_mask = np.ones(len(wavelengths), dtype=bool)
    bad_mask[good_idx] = False
    save_signal_qa_plot(wavelengths, means, bad_mask)

    print("\nWavelength range kept:", wavelengths[good_idx].min(), "-", wavelengths[good_idx].max(), "nm")
    print("Sample kept bands (nm):", np.round(wavelengths[good_idx][:5], 1), "...",
          np.round(wavelengths[good_idx][-5:], 1))

    np.savez(
        os.path.join(OUT, "cube_qa.npz"),
        cube=cube, wavelengths=wavelengths, good_idx=good_idx,
        valid_mask=valid_mask, band_nums=np.array(band_nums),
    )
    print("\nSaved: outputs/band_signal_qa.png, outputs/cube_qa.npz")


if __name__ == "__main__":
    main()
