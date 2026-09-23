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
from theme import apply_theme, top_nav

st.set_page_config(page_title="Hotspot Maps | GreenGrid", layout="wide", page_icon="🌳")
c = apply_theme()
top_nav("hotspot")

st.markdown('<h1>Hotspot maps</h1>', unsafe_allow_html=True)
st.markdown('<p class="sec-sub">Where heat is worst across Mumbai, Thane, and Vasai-Virar</p>', unsafe_allow_html=True)

# Colorblind-safe alternative to the default red-blue thermal ramp. RdYlBu_r is
# a common heatmap choice but is hard to read for red-deficient color vision;
# viridis is perceptually uniform and colorblind-safe, so we offer both rather
# than forcing one on everyone.
CMAP_OPTIONS = {"Thermal (red–blue)": "RdYlBu_r", "Colorblind-safe (viridis)": "viridis"}


def render_raster_to_png(data, vmin, vmax, out_path, cmap_name="RdYlBu_r"):
    cmap = plt.colormaps[cmap_name].copy()
    cmap.set_bad(color=(0, 0, 0, 0))
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax, clip=True)
    rgba = cmap(norm(data))
    plt.imsave(out_path, rgba)


@st.cache_data
def get_available_lst_quarters():
    files = glob.glob("data/mumbai_LST_*.tif")
    quarters = []
    for f in files:
        match = re.search(r"mumbai_LST_(\d{4}_Q\d)\.tif", os.path.basename(f))
        if match:
            quarters.append(match.group(1))
    return sorted(quarters)


@st.cache_data
def load_and_render_lst(quarter, cmap_name):
    path = f"data/mumbai_LST_{quarter}.tif"
    with rasterio.open(path) as src:
        data = src.read(1)
        bounds = src.bounds
    valid = data[~np.isnan(data)]
    vmin = float(np.nanpercentile(valid, 2))
    vmax = float(np.nanpercentile(valid, 98))
    png_path = f"data/_render_lst_{quarter}_{cmap_name}.png"
    render_raster_to_png(data, vmin, vmax, png_path, cmap_name=cmap_name)
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

# ---- Real controls, with visible labels this time (previously label_visibility
# ="collapsed" left the dropdown with no visible caption, discoverable only
# after the fact via the chip row below). ----
fcol1, fcol2, fcol3 = st.columns([1, 1, 2])
with fcol1:
    selected_quarter = st.selectbox("Quarter", quarters, index=len(quarters) - 1)
with fcol2:
    cmap_label = st.selectbox("Color scale", list(CMAP_OPTIONS.keys()))
cmap_name = CMAP_OPTIONS[cmap_label]

try:
    lst_png, lst_bounds, center, lst_vmin, lst_vmax = load_and_render_lst(selected_quarter, cmap_name)
    dem_png, dem_bounds, dem_vmin, dem_vmax = load_and_render_dem()
except Exception:
    st.error("Couldn't load the raster data for this quarter. Check that the files under data/ are present and readable.")
    st.stop()

# Legend gradient sampled from the same colormap used to paint the raster,
# so the legend always matches the map colours.
_cmap = plt.colormaps[cmap_name]
legend_gradient = ", ".join(mcolors.to_hex(_cmap(v)) for v in np.linspace(0, 1, 9))

# Read-only status summary — no fake "▾" carets here, since these chips aren't
# clickable; the real controls are the selects above.
st.markdown(
    f'<span class="chip">Layer: Surface Temp</span>'
    f'<span class="chip">Quarter: {selected_quarter}</span>'
    f'<span class="chip">Region: MMR</span>',
    unsafe_allow_html=True,
)
st.write("")

# ---- Map + side stats ----
map_col, side_col = st.columns([2.3, 1])

with map_col:
    m = folium.Map(location=center, zoom_start=11, tiles="OpenStreetMap")
    Fullscreen(position="topleft").add_to(m)
    folium.raster_layers.ImageOverlay(
        image=lst_png, bounds=lst_bounds,
        name=f"Land Surface Temperature — {selected_quarter}", opacity=0.75,
    ).add_to(m)
    folium.raster_layers.ImageOverlay(
        image=dem_png, bounds=dem_bounds,
        name="Elevation (DEM)", opacity=0.5, show=False,
    ).add_to(m)
    folium.LayerControl(collapsed=True).add_to(m)
    st_folium(m, width=None, height=520, use_container_width=True)

with side_col:
    st.markdown(
        f'<div class="card"><p class="card-label">Hottest zone</p>'
        f'<p class="stat-lg" style="font-size:20px;">{lst_vmax:.1f}°C</p>'
        f'<p class="card-label" style="margin-top:2px;">{selected_quarter}, percentile-clipped max</p></div>',
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        f'<div class="card"><p class="card-label">Coolest zone</p>'
        f'<p class="stat" style="font-size:20px;">{lst_vmin:.1f}°C</p>'
        f'<p class="card-label" style="margin-top:2px;">Typically coastal water / green cover</p></div>',
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        f'<div class="card"><p class="card-label">Legend — LST {selected_quarter} (°C)</p>'
        f'<div style="height:12px;border-radius:4px;margin:8px 0 6px 0;'
        f'background:linear-gradient(to right,{legend_gradient});"></div>'
        f'<div style="display:flex;justify-content:space-between;font-size:12.5px;color:{c["slate_60"]};">'
        f'<span>{lst_vmin:.1f}°C (cooler)</span><span>{lst_vmax:.1f}°C (hotter)</span></div></div>',
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        f'<div class="card"><p class="card-label">Legend — Elevation (DEM)</p>'
        f'<div style="height:12px;border-radius:4px;margin:8px 0 6px 0;'
        f'background:linear-gradient(to right,#333015,#5a8f4a,#a8d08a,#e8e4c9,#ffffff);"></div>'
        f'<div style="display:flex;justify-content:space-between;font-size:12.5px;color:{c["slate_60"]};">'
        f'<span>{dem_vmin:.0f} m (low)</span><span>{dem_vmax:.0f} m (high)</span></div>'
        f'<p class="card-label" style="margin-top:6px;">Toggle "Elevation (DEM)" in the map\'s layer control to view.</p></div>',
        unsafe_allow_html=True,
    )

st.caption(
    f"Raw file range this quarter: {lst_vmin:.1f}°C to {lst_vmax:.1f}°C "
    "(percentile-clipped for display — actual file min/max may include outlier pixels)."
)