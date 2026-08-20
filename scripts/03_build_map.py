"""
Turn the cluster classification into a labeled map + portfolio-style
interactive Folium map (satellite basemap, same visual pattern as the rest
of the site).

Cluster -> class label uses a simple, data-driven rule on the index means
(no hardcoded cluster numbers, so it still works if K-means order changes
on a re-run):
  - NDVI clearly above the scene median          -> Vegetated / forest fringe
  - iron-oxide band depth clearly above median
    AND NDVI at/below median                     -> Iron-oxide waste rock / tailings
  - everything else                               -> Mixed bare surface / benches

Honest caveat kept in the legend: mine-water pixels were not confidently
separated as their own cluster at 30m without atmospheric correction (the
McFeeters water index range across clusters was too narrow to trust) --
noted as a follow-up rather than overclaimed.
"""
import os
import json
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
import matplotlib.pyplot as plt
import folium

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIF = os.path.join(BASE, "Noamundi_Hyperion_16Apr2011.tif")
OUT = os.path.join(BASE, "outputs")

CLASS_COLORS = {
    "Vegetated / forest fringe": "#3E8E4F",
    "Iron-oxide waste rock / tailings": "#B5541F",
    "Mixed bare surface / benches": "#B9A582",
}


def main():
    data = np.load(os.path.join(OUT, "classification.npz"), allow_pickle=True)
    labels = data["labels"]
    valid_mask = data["valid_mask"]
    cluster_stats = list(data["cluster_stats"])

    ndvi_med = np.median([s["ndvi"] for s in cluster_stats])
    iron_med = np.median([s["iron"] for s in cluster_stats])

    cluster_to_class = {}
    for s in cluster_stats:
        if s["ndvi"] > ndvi_med + 0.01:
            cluster_to_class[s["cluster"]] = "Vegetated / forest fringe"
        elif s["iron"] > iron_med and s["ndvi"] <= ndvi_med + 0.01:
            cluster_to_class[s["cluster"]] = "Iron-oxide waste rock / tailings"
        else:
            cluster_to_class[s["cluster"]] = "Mixed bare surface / benches"

    print("Cluster -> class assignment:")
    for c, cls in sorted(cluster_to_class.items()):
        print(f"  cluster {c}: {cls}")

    class_names = list(CLASS_COLORS.keys())
    class_idx = {name: i for i, name in enumerate(class_names)}
    rows, cols = labels.shape
    class_map = np.full((rows, cols), -1, dtype=np.int16)
    for c, cls in cluster_to_class.items():
        class_map[labels == c] = class_idx[cls]

    # ---- colorized RGBA PNG for the overlay ----
    rgba = np.zeros((rows, cols, 4), dtype=np.uint8)
    for name, idx in class_idx.items():
        hexcolor = CLASS_COLORS[name]
        r = int(hexcolor[1:3], 16); g = int(hexcolor[3:5], 16); b = int(hexcolor[5:7], 16)
        m = class_map == idx
        rgba[m] = [r, g, b, 235]
    rgba[~valid_mask] = [0, 0, 0, 0]

    overlay_png = os.path.join(OUT, "classification_overlay.png")
    plt.imsave(overlay_png, rgba)

    # ---- reproject raster bounds to WGS84 for Folium ----
    with rasterio.open(TIF) as src:
        bounds = src.bounds
        src_crs = src.crs
    wgs_bounds = transform_bounds(src_crs, "EPSG:4326", *bounds)  # (left, bottom, right, top)
    lon_min, lat_min, lon_max, lat_max = wgs_bounds
    center = [(lat_min + lat_max) / 2, (lon_min + lon_max) / 2]

    # ---- build the Folium map, same satellite-basemap style as the rest of the portfolio ----
    m = folium.Map(location=center, zoom_start=15, tiles=None, control_scale=True)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri, Maxar, Earthstar Geographics, and the GIS User Community",
        name="Satellite",
        control=False,
    ).add_to(m)

    folium.raster_layers.ImageOverlay(
        image=overlay_png,
        bounds=[[lat_min, lon_min], [lat_max, lon_max]],
        opacity=0.75,
        name="Hyperion material classification",
    ).add_to(m)

    folium.Marker(
        location=center,
        tooltip="Noamundi iron ore mine -- Hyperion scene, 16 Apr 2011",
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(m)

    legend_html = f"""
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999;
                background: rgba(10,27,38,0.92); color: #F2F2F0; padding: 14px 18px;
                border-radius: 8px; font-family: 'Poppins', sans-serif; font-size: 13px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.4); max-width: 300px;">
      <div style="font-weight:600; margin-bottom:8px; font-size:14px;">Surface Classification</div>
      {"".join(f'<div style="margin-bottom:4px;"><span style="display:inline-block;width:12px;height:12px;background:{CLASS_COLORS[n]};margin-right:8px;border-radius:2px;"></span>{n}</div>' for n in class_names)}
      <div style="margin-top:10px; padding-top:8px; border-top:1px solid rgba(169,211,197,0.3); font-size:11px; color:#A9D3C5; line-height:1.4;">
        Unsupervised K-means on 163 clean Hyperion bands (425-2396nm), shape-normalized per pixel.
        Mine-water bodies were not confidently separated at 30m without atmospheric correction --
        flagged as follow-up work rather than mapped here.
      </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl(collapsed=False).add_to(m)

    out_html = os.path.join(OUT, "noamundi_classification_map.html")
    m.save(out_html)
    print(f"\nSaved: {out_html}")
    print(f"Saved: {overlay_png}")

    # class pixel counts for the write-up
    for name, idx in class_idx.items():
        n = int((class_map == idx).sum())
        print(f"  {name}: {n} px ({n*900/1e6:.2f} sq km)")


if __name__ == "__main__":
    main()
