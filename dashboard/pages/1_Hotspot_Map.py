import os
import re
import glob
import numpy as np
import rasterio
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import folium
from folium.plugins import Fullscreen
import streamlit as st
from streamlit_folium import st_folium

st.title("Hotspot Map")

with st.expander("About this map"):
    st.write(
        "Real LST data for the Mumbai Metropolitan Region (Mumbai, Thane, Vasai-Virar). "
        "Values are scaled to the 2nd-98th percentile to avoid extreme outlier pixels distorting the color scale."
    )


def render_raster_to_png(data, vmin, vmax, out_path, cmap_name="RdYlBu_r"):
    """Convert a 2D array into a color PNG, making NaN pixels fully transparent."""
    cmap = plt.colormaps[cmap_name].copy()
    cmap.set_bad(color=(0, 0, 0, 0))  # transparent for NaN/missing pixels
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax, clip=True)
    rgba = cmap(norm(data))
    plt.imsave(out_path, rgba)


@st.cache_data
def get_available_lst_quarters():
    """Scan the data folder for whichever LST quarter files actually exist locally."""
    files = glob.glob("data/mumbai_LST_*.tif")
    quarters = []
    for f in files:
        match = re.search(r"mumbai_LST_(\d{4}_Q\d)\.tif", os.path.basename(f))
        if match:
            quarters.append(match.group(1))
    return sorted(quarters)


@st.cache_data
def load_and_render_lst(quarter):
    path = f"data/mumbai_LST_{quarter}.tif"
    with rasterio.open(path) as src:
        data = src.read(1)
        bounds = src.bounds

    valid = data[~np.isnan(data)]
    vmin = float(np.nanpercentile(valid, 2))
    vmax = float(np.nanpercentile(valid, 98))

    png_path = f"data/_render_lst_{quarter}.png"
    render_raster_to_png(data, vmin, vmax, png_path)

    map_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
    center = [(bounds.bottom + bounds.top) / 2, (bounds.left + bounds.right) / 2]
    return png_path, map_bounds, center, vmin, vmax


@st.cache_data
def load_and_render_dem():
    path = "data/mumbai_DEM.tif"
    with rasterio.open(path) as src:
        data = src.read(1)
        bounds = src.bounds

    valid = data[~np.isnan(data)]
    vmin = float(np.nanpercentile(valid, 2))
    vmax = float(np.nanpercentile(valid, 98))

    png_path = "data/_render_dem.png"
    render_raster_to_png(data, vmin, vmax, png_path, cmap_name="terrain")

    map_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
    return png_path, map_bounds, vmin, vmax


quarters = get_available_lst_quarters()

if not quarters:
    st.warning("No LST files found in data/. Add mumbai_LST_<year>_<quarter>.tif files there.")
    st.stop()

# Controls live in the sidebar so they don't eat vertical space above the map
with st.sidebar:
    st.header("Hotspot Map Controls")
    selected_quarter = st.selectbox("Select quarter", quarters, index=len(quarters) - 1)
    size_option = st.radio("Map size", ["Compact", "Standard", "Large"], index=1)

size_map = {
    "Compact": (700, 350),
    "Standard": (900, 550),
    "Large": (1100, 750),
}
map_width, map_height = size_map[size_option]

lst_png, lst_bounds, center, lst_vmin, lst_vmax = load_and_render_lst(selected_quarter)
dem_png, dem_bounds, dem_vmin, dem_vmax = load_and_render_dem()

m = folium.Map(location=center, zoom_start=11, tiles="cartodbpositron")
Fullscreen(position="topleft").add_to(m)

folium.raster_layers.ImageOverlay(
    image=lst_png,
    bounds=lst_bounds,
    name=f"Land Surface Temperature — {selected_quarter}",
    opacity=0.75,
).add_to(m)

folium.raster_layers.ImageOverlay(
    image=dem_png,
    bounds=dem_bounds,
    name="Elevation (DEM)",
    opacity=0.5,
    show=False,  # off by default so LST is the focus on load
).add_to(m)

folium.LayerControl(collapsed=True).add_to(m)

legend_html = f"""
<div style="
    position: fixed;
    bottom: 20px;
    left: 20px;
    z-index: 9999;
    background: white;
    padding: 8px 12px;
    border: 1px solid #999;
    border-radius: 4px;
    font-size: 12px;
">
<b style="color:black;">LST — {selected_quarter} (&deg;C, 2nd-98th percentile)</b><br>
<div style="background: linear-gradient(to right, blue, yellow, red); width: 180px; height: 12px; margin-top:4px;"></div>
<div style="display:flex; justify-content:space-between; width:180px; color:black;">
<span>{lst_vmin:.1f}</span><span>{lst_vmax:.1f}</span>
</div>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, width=map_width, height=map_height)

st.caption(
    f"Raw file range this quarter: {lst_vmin:.1f}°C to {lst_vmax:.1f}°C "
    "(percentile-clipped for display — actual file min/max may include outlier pixels)."
)