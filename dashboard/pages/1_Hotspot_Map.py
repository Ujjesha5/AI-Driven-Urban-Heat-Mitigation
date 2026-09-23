import json
import os
import folium
from folium.plugins import Fullscreen
import streamlit as st
from streamlit_folium import st_folium
from theme import apply_theme, top_nav

st.set_page_config(page_title="Hotspot Maps | GreenGrid", layout="wide")
c = apply_theme()
top_nav("hotspot")

st.markdown('<h1>Hotspot maps</h1>', unsafe_allow_html=True)
st.markdown('<p class="sec-sub">Where heat is worst across Mumbai, Thane, and Vasai-Virar</p>', unsafe_allow_html=True)

CACHE_PATH = "data/cache/raster_cache.json"

# Fallback only used if an older cache predates the legend_gradient_lst field.
_FALLBACK_LEGEND = [
    "#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8",
    "#ffffbf", "#fee090", "#fdae61", "#f46d43", "#d73027", "#a50026",
]


@st.cache_data
def load_raster_cache():
    if not os.path.exists(CACHE_PATH):
        return None
    with open(CACHE_PATH) as f:
        return json.load(f)


cache = load_raster_cache()
if not cache or not cache.get("lst_quarters"):
    st.warning(
        "No pre-rendered LST data found in data/cache/. Run "
        "`python dashboard/prerender_rasters.py` locally (with the raw GeoTIFFs "
        "on disk) and commit the data/cache/ folder."
    )
    st.stop()

quarters = sorted(cache["lst_quarters"].keys())

# ---- Filter chips (real controls, styled as the chip row from the reference) ----
fcol1, fcol2 = st.columns([1, 3])
with fcol1:
    selected_quarter = st.selectbox("Quarter", quarters, index=len(quarters) - 1, label_visibility="collapsed")

lst_info = cache["lst_quarters"][selected_quarter]
lst_png = os.path.join("data", lst_info["png"])
lst_bounds = lst_info["bounds"]
center = lst_info["center"]
lst_vmin, lst_vmax = lst_info["vmin"], lst_info["vmax"]

dem_info = cache.get("dem")

legend_gradient = ", ".join(cache.get("legend_gradient_lst", _FALLBACK_LEGEND))

st.markdown(
    f'<span class="chip">Layer: Surface Temp </span>'
    f'<span class="chip">Quarter: {selected_quarter} </span>'
    f'<span class="chip">Region: MMR </span>',
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
    if dem_info:
        dem_png = os.path.join("data", dem_info["png"])
        folium.raster_layers.ImageOverlay(
            image=dem_png, bounds=dem_info["bounds"],
            name="Elevation (DEM)", opacity=0.5, show=False,
        ).add_to(m)
    folium.LayerControl(collapsed=True).add_to(m)
    st_folium(m, width=None, height=420, use_container_width=True)

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

st.caption(
    f"Raw file range this quarter: {lst_vmin:.1f}°C to {lst_vmax:.1f}°C "
    "(percentile-clipped for display — actual file min/max may include outlier pixels)."
)