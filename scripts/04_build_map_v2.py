"""
v2 interactive map -- adds the ferric-iron and clay/jarosite band-depth
heatmaps as toggleable layers alongside the material classification, so the
map itself carries the same "what the absorption features mean" story as
the poster and theoretical foundations doc, not just a flat class map.
"""
import os
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
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
    labels = data["labels"]; valid_mask = data["valid_mask"]
    iron_arr = data["iron_oxide"]; clay_arr = data["bd2200"]
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

    class_names = list(CLASS_COLORS.keys())
    class_idx = {name: i for i, name in enumerate(class_names)}
    rows, cols = labels.shape
    class_map = np.full((rows, cols), -1, dtype=np.int16)
    for c, cls in cluster_to_class.items():
        class_map[labels == c] = class_idx[cls]

    rgba = np.zeros((rows, cols, 4), dtype=np.uint8)
    for name, idx in class_idx.items():
        hexcolor = CLASS_COLORS[name]
        r = int(hexcolor[1:3], 16); g = int(hexcolor[3:5], 16); b = int(hexcolor[5:7], 16)
        m = class_map == idx
        rgba[m] = [r, g, b, 235]
    rgba[~valid_mask] = [0, 0, 0, 0]
    overlay_png = os.path.join(OUT, "classification_overlay.png")
    plt.imsave(overlay_png, rgba)

    def save_heatmap(arr, cmap_name, out_name):
        finite = np.isfinite(arr) & valid_mask
        vmin = np.nanpercentile(arr[finite], 3); vmax = np.nanpercentile(arr[finite], 97)
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
        cmap_obj = cm.get_cmap(cmap_name)
        out = cmap_obj(norm(arr))
        out[..., 3] = np.where(finite, 0.92, 0.0)
        path = os.path.join(OUT, out_name)
        plt.imsave(path, out)
        return path

    iron_png = save_heatmap(iron_arr, "YlOrRd", "iron_oxide_heatmap.png")
    clay_png = save_heatmap(clay_arr, "PuBuGn", "clay_heatmap.png")

    with rasterio.open(TIF) as src:
        bounds = src.bounds; src_crs = src.crs
    wgs_bounds = transform_bounds(src_crs, "EPSG:4326", *bounds)
    lon_min, lat_min, lon_max, lat_max = wgs_bounds
    center = [(lat_min + lat_max) / 2, (lon_min + lon_max) / 2]
    img_bounds = [[lat_min, lon_min], [lat_max, lon_max]]

    m = folium.Map(location=center, zoom_start=15, tiles=None, control_scale=True)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri, Maxar, Earthstar Geographics, and the GIS User Community",
        name="Satellite", control=False,
    ).add_to(m)

    folium.raster_layers.ImageOverlay(
        image=overlay_png, bounds=img_bounds, opacity=0.75,
        name="Material Classification", show=True,
    ).add_to(m)
    folium.raster_layers.ImageOverlay(
        image=iron_png, bounds=img_bounds, opacity=0.8,
        name="Ferric-Iron Band Depth (~870nm)", show=False,
    ).add_to(m)
    folium.raster_layers.ImageOverlay(
        image=clay_png, bounds=img_bounds, opacity=0.8,
        name="Al/Fe-OH Clay Band Depth (~2200nm)", show=False,
    ).add_to(m)

    folium.Marker(
        location=center,
        tooltip="Noamundi iron ore mine -- Hyperion scene, 16 Apr 2011",
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(m)

    legend_html = f"""
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999;
                background: rgba(10,27,38,0.94); color: #F2F2F0; padding: 14px 18px;
                border-radius: 8px; font-family: 'Poppins', sans-serif; font-size: 13px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.4); max-width: 310px;">
      <div style="font-weight:600; margin-bottom:8px; font-size:14px;">Rust Signature — Noamundi</div>
      <div style="font-size:11.5px; color:#A9D3C5; margin-bottom:8px;">Use the layer control (top right) to switch between the material classification and the two diagnostic absorption-depth heatmaps.</div>
      {"".join(f'<div style="margin-bottom:4px;"><span style="display:inline-block;width:12px;height:12px;background:{CLASS_COLORS[n]};margin-right:8px;border-radius:2px;"></span>{n}</div>' for n in class_names)}
      <div style="margin-top:10px; padding-top:8px; border-top:1px solid rgba(169,211,197,0.3); font-size:11px; color:#A9D3C5; line-height:1.4;">
        198-band Hyperion scene, shape-normalized K-means (163 QA'd bands). Mine-water bodies not confidently
        separated at 30m without atmospheric correction — flagged as follow-up, not mapped here.
      </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl(collapsed=False).add_to(m)

    out_html = os.path.join(OUT, "noamundi_classification_map.html")
    m.save(out_html)
    print(f"Saved: {out_html}")


if __name__ == "__main__":
    main()
