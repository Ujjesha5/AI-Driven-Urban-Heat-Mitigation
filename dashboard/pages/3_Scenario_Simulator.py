import numpy as np
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import streamlit as st

st.title("Scenario Simulator")

with st.expander("About this page"):
    st.write(
        "Simulates the effect of a cooling intervention (e.g., increased tree canopy, cool roofs) "
        "on Land Surface Temperature within a chosen area. "
        "Currently showing placeholder data — will be replaced with real InVEST Urban Cooling Model output."
    )


def render_raster_to_png(data, vmin, vmax, out_path, cmap_name="RdYlBu_r"):
    """Same rendering approach used on the Hotspot Map page, for visual consistency."""
    cmap = plt.colormaps[cmap_name].copy()
    cmap.set_bad(color=(0, 0, 0, 0))
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax, clip=True)
    rgba = cmap(norm(data))
    plt.imsave(out_path, rgba)


# --- DUMMY DATA SECTION ---
# Person C (or whoever runs InVEST): replace this function with code that:
#   1. Runs InVEST's Urban Cooling Model on the baseline LULC raster -> "before" array
#   2. Runs it again on a modified LULC raster (with the intervention applied) -> "after" array
#   3. Returns both arrays, aligned to the same shape and geographic extent
@st.cache_data
def get_dummy_scenario(intervention_pct):
    rng = np.random.default_rng(seed=7)
    base = rng.uniform(28, 42, (150, 150))
    # Fake cooling effect: higher intervention % = more cooling, with some spatial variation
    cooling_pattern = rng.uniform(0.5, 1.0, (150, 150))
    after = base - (intervention_pct / 100) * 8 * cooling_pattern
    return base, after


with st.sidebar:
    st.header("Scenario Controls")
    intervention_type = st.selectbox(
        "Intervention type",
        ["Tree canopy increase", "Cool roofs (albedo change)", "Green roofs", "Water body addition"],
    )
    intervention_pct = st.slider("Intervention coverage (% of area)", 0, 100, 20)

before, after = get_dummy_scenario(intervention_pct)
difference = after - before

vmin, vmax = 20, 42
render_raster_to_png(before, vmin, vmax, "data/_render_scenario_before.png")
render_raster_to_png(after, vmin, vmax, "data/_render_scenario_after.png")

st.subheader(f"{intervention_type} — {intervention_pct}% coverage")

col1, col2 = st.columns(2)
with col1:
    st.image("data/_render_scenario_before.png", caption="Before intervention", use_container_width=True)
with col2:
    st.image("data/_render_scenario_after.png", caption="After intervention", use_container_width=True)

st.divider()

avg_cooling = -difference.mean()
max_cooling = -difference.min()

m1, m2, m3 = st.columns(3)
m1.metric("Average cooling", f"{avg_cooling:.2f} °C")
m2.metric("Max cooling (hottest pixel)", f"{max_cooling:.2f} °C")
m3.metric("Area covered", f"{intervention_pct}%")

st.caption(
    "Placeholder data — cooling effect is a simplified formula, not a real physical simulation. "
    "Will be replaced with real InVEST Urban Cooling Model output once Week 3 setup is complete."
)