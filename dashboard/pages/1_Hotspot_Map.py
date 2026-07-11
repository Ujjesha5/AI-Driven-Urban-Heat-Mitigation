import streamlit as st
import numpy as np
import rasterio
from rasterio.transform import from_origin
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from branca.colormap import LinearColormap

st.title("Hotspot Map")
st.write("Preview using dummy data — will be replaced with real LST data from Person A.")


@st.cache_data
def generate_dummy_lst():
    """Fake Land Surface Temperature raster (values between 25-45 degrees C)."""
    fake_data = np.random.uniform(25, 45, (100, 100))
    transform = from_origin(77.0, 28.7, 0.001, 0.001)

    with rasterio.open(
        "data/dummy_lst.tif", "w", driver="GTiff",
        height=100, width=100, count=1, dtype=fake_data.dtype,
        crs="EPSG:4326", transform=transform,
    ) as dst:
        dst.write(fake_data, 1)

    plt.imsave("data/dummy_lst.png", fake_data, cmap="RdYlBu_r")
    return "data/dummy_lst.png"


@st.cache_data
def generate_dummy_lulc():
    """Fake Land Use / Land Cover raster (4 made-up categories)."""
    fake_lulc = np.random.choice([1, 2, 3, 4], size=(100, 100))
    plt.imsave("data/dummy_lulc.png", fake_lulc, cmap="tab10")
    return "data/dummy_lulc.png"


lst_png_path = generate_dummy_lst()
lulc_png_path = generate_dummy_lulc()

# Same bounds for both layers so they line up on the map
bounds = [[28.6, 76.9], [28.8, 77.1]]

m = folium.Map(location=[28.7, 77.0], zoom_start=11)

folium.raster_layers.ImageOverlay(
    image=lst_png_path,
    bounds=bounds,
    name="Land Surface Temperature (dummy)",
    opacity=0.7,
).add_to(m)

folium.raster_layers.ImageOverlay(
    image=lulc_png_path,
    bounds=bounds,
    name="Land Use / Land Cover (dummy)",
    opacity=0.7,
).add_to(m)

# LayerControl must be added AFTER all layers exist, so it can list all of them
folium.LayerControl(collapsed=True).add_to(m)

legend_html = """
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
<b style="color:black;">Land Surface Temperature (&deg;C)</b><br>
<div style="background: linear-gradient(to right, blue, yellow, red); width: 150px; height: 12px; margin-top:4px;"></div>
<div style="display:flex; justify-content:space-between; width:150px; color:black;">
<span>25</span><span>45</span>
</div>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))
st_folium(m, height=500, use_container_width=True)