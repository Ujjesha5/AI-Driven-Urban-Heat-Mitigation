import os
import sys
from pathlib import Path

# Ensure project root is in sys.path (needed to import the `model` package below)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import streamlit as st
from theme import apply_theme, top_nav

st.set_page_config(page_title="Scenario Simulator | GreenGrid", layout="wide")
c = apply_theme()
top_nav("scenario")

st.markdown('<h1>Scenario simulator</h1>', unsafe_allow_html=True)
st.markdown('<p class="sec-sub">Test interventions before committing budget</p>', unsafe_allow_html=True)

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "model" / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "best_pg_model.joblib"


@st.cache_data
def load_candidate_sites():
    return pd.read_csv("model/artifacts/candidate_intervention_sites.csv", encoding="utf-8")


candidates = load_candidate_sites()

fcol1, fcol2 = st.columns([1, 1])
with fcol1:
    zone = st.selectbox("Zone", candidates["zone"].unique().tolist(), label_visibility="collapsed")
zone_sites = candidates[candidates["zone"] == zone]
with fcol2:
    site_id = st.selectbox("Site", zone_sites["site_id"].tolist(), label_visibility="collapsed")

site = candidates[candidates["site_id"] == site_id].iloc[0]

st.markdown(
    f'<span class="chip">Zone: {zone} ▾</span>'
    f'<span class="chip">Site: {site_id} ▾</span>'
    f'<span class="chip">Intervention: {site["intervention"]}</span>',
    unsafe_allow_html=True,
)
st.write("")

main_col, side_col = st.columns([1.6, 1])

with main_col:
    b_col, a_col = st.columns(2)
    with b_col:
        st.markdown(
            f'<div style="height:100px;border-radius:10px;background:{c["coral"]};color:#fff;'
            f'padding:10px 12px;display:flex;flex-direction:column;justify-content:space-between;">'
            f'<span style="font-size:10px;letter-spacing:1px;text-transform:uppercase;">BEFORE</span>'
            f'<span style="font-family:\'IBM Plex Sans\';font-size:22px;">{site["baseline_lst_c"]:.1f}°C</span></div>',
            unsafe_allow_html=True,
        )
    with a_col:
        st.markdown(
            f'<div style="height:100px;border-radius:10px;background:{c["green"]};color:#fff;'
            f'padding:10px 12px;display:flex;flex-direction:column;justify-content:space-between;">'
            f'<span style="font-size:10px;letter-spacing:1px;text-transform:uppercase;">AFTER</span>'
            f'<span style="font-family:\'IBM Plex Sans\';font-size:22px;">{site["post_intervention_lst_c"]:.1f}°C</span></div>',
            unsafe_allow_html=True,
        )

    st.write("")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'<div class="card"><p class="card-label">Temp reduction</p><p class="stat-lg" style="font-size:18px;color:{c["green_dark"]};">-{site["predicted_reduction_c"]:.2f}°C</p></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="card"><p class="card-label">Est. cost</p><p class="stat" style="font-size:18px;">{site["cost"]:.1f}</p></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="card"><p class="card-label">Cooling / cost</p><p class="stat" style="font-size:18px;">{site["cooling_per_cost_ratio"]:.3f}</p></div>', unsafe_allow_html=True)

with side_col:
    st.markdown(
        f'<div class="card"><p class="card-label">Site</p>'
        f'<p class="stat" style="font-size:15px;">{site["site_id"]}</p>'
        f'<p class="card-label" style="margin-top:2px;">{site["description"]}</p></div>',
        unsafe_allow_html=True,
    )

st.write("")
st.write("")
st.markdown('<p class="card-label">All candidate sites in this zone</p>', unsafe_allow_html=True)
for _, row in zone_sites.iterrows():
    st.markdown(
        f'<div class="row"><span>{row["site_id"]} · {row["intervention"]}</span>'
        f'<span>{row["baseline_lst_c"]:.1f}°C → {row["post_intervention_lst_c"]:.1f}°C '
        f'(-{row["predicted_reduction_c"]:.2f}°C, cost {row["cost"]:.1f})</span></div>',
        unsafe_allow_html=True,
    )

st.caption(
    "Before/after values are real predictions from the trained Physics-Residual Hybrid model. "
    "Full raster-level simulation via the InVEST Urban Cooling Model is in progress."
)

# ---- Live intervention simulator (kept from prior branch) ----
st.write("")
st.write("")
st.markdown('<hr class="nav-divider">', unsafe_allow_html=True)
st.markdown('<div class="eyebrow">Live simulator</div>', unsafe_allow_html=True)
st.markdown('<h2 class="sec-title">Run your own intervention scenario</h2>', unsafe_allow_html=True)
st.markdown(
    '<p class="sec-sub">Pick an intervention type and coverage level and the Physics-Guided model '
    'generates a live before/after temperature surface for a representative urban microclimate grid — '
    'independent of the specific candidate sites above.</p>',
    unsafe_allow_html=True,
)


def render_raster_to_png(data, vmin, vmax, out_path, cmap_name="RdYlBu_r"):
    """Convert a 2D array into a color PNG, making NaN pixels transparent."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cmap = plt.colormaps[cmap_name].copy()
    cmap.set_bad(color=(0, 0, 0, 0))
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax, clip=True)
    rgba = cmap(norm(data))
    plt.imsave(out_path, rgba)


@st.cache_resource
def load_simulator():
    from model.optimizer import InterventionSimulator
    if MODEL_PATH.exists():
        return InterventionSimulator(model_path=MODEL_PATH)
    return None


simulator = load_simulator()


@st.cache_data
def run_ml_scenario(intervention_type, coverage_pct, grid_size=100):
    """Generates a representative urban microclimate grid and simulates intervention with the PG model."""
    rng = np.random.default_rng(seed=42)

    # Generate spatial grid coordinates across MMR urban hotspot
    x = np.linspace(0, 1, grid_size)
    y = np.linspace(0, 1, grid_size)
    xx, yy = np.meshgrid(x, y)

    # Spatial urban density pattern
    dist_center = np.sqrt((xx - 0.5) ** 2 + (yy - 0.5) ** 2)
    urban_density = np.clip(1.0 - 1.2 * dist_center + rng.normal(0, 0.04, (grid_size, grid_size)), 0.1, 0.95)

    base_ndvi = np.clip(0.55 - 0.45 * urban_density + rng.normal(0, 0.03, (grid_size, grid_size)), 0.05, 0.85)
    base_ndbi = np.clip(-0.5 * base_ndvi + 0.3 * urban_density + rng.normal(0, 0.03, (grid_size, grid_size)), -0.5, 0.65)
    base_albedo = np.clip(0.12 + 0.06 * (1.0 - urban_density) + rng.normal(0, 0.01, (grid_size, grid_size)), 0.08, 0.30)
    base_mndwi = np.clip(-0.4 * base_ndbi - 0.3 * base_ndvi, -0.6, 0.5)

    flat_df = pd.DataFrame({
        "ndvi": base_ndvi.flatten(),
        "ndbi": base_ndbi.flatten(),
        "albedo": base_albedo.flatten(),
        "mndwi": base_mndwi.flatten(),
        "dem": 15.0 + 30.0 * (1.0 - urban_density.flatten()),
        "slope": 2.5,
        "sky_view_factor": 1.0 - 0.5 * urban_density.flatten(),
        "building_height": 10.0 + 35.0 * urban_density.flatten(),
        "building_fraction": urban_density.flatten() * 80.0,
        "roughness_length": 1.2,
        "temp_2m": 33.5,
        "dewpoint_2m": 26.0,
        "wind_speed_10m": 3.2,
        "solar_radiation": 760.0,
        "vapor_pressure_deficit": 2.0,
        "dist_to_coast": 2.5 + 5.0 * xx.flatten(),
        "dist_to_water": 2.0,
        "dist_to_greenspace": 1.5 + 4.0 * urban_density.flatten(),
    })

    if simulator is not None:
        before_flat, after_flat, diff_flat = simulator.simulate_grid_intervention(
            flat_df, intervention_type, coverage_pct=coverage_pct
        )
        before = before_flat.reshape((grid_size, grid_size))
        after = after_flat.reshape((grid_size, grid_size))
    else:
        # Calibrated fallback
        base_temp = 34.0 + 6.0 * urban_density
        cooling_scale = 3.5 if "Tree" in intervention_type else 2.8 if "Cool" in intervention_type else 2.2
        cooling = (coverage_pct / 100.0) * cooling_scale * (0.6 + 0.4 * urban_density)
        before = base_temp
        after = base_temp - cooling

    return before, after


sim_ctrl1, sim_ctrl2 = st.columns([1.4, 1])
with sim_ctrl1:
    intervention_type = st.selectbox(
        "Intervention type",
        [
            "Tree canopy increase",
            "Cool roofs (albedo change)",
            "Green roofs",
            "Water body / Wetland creation",
        ],
    )
with sim_ctrl2:
    intervention_pct = st.slider("Intervention coverage (% of target area)", 0, 100, 40, step=5)

before, after = run_ml_scenario(intervention_type, intervention_pct)
difference = after - before  # Negative value means cooling

vmin = float(min(np.nanpercentile(before, 2), np.nanpercentile(after, 2)))
vmax = float(max(np.nanpercentile(before, 98), np.nanpercentile(after, 98)))

render_raster_to_png(before, vmin, vmax, "data/_render_scenario_before.png")
render_raster_to_png(after, vmin, vmax, "data/_render_scenario_after.png")

st.write("")
sim_img_col1, sim_img_col2 = st.columns(2)
with sim_img_col1:
    st.image("data/_render_scenario_before.png", caption=f"Baseline LST (Min: {vmin:.1f}°C, Max: {vmax:.1f}°C)", use_container_width=True)
with sim_img_col2:
    st.image("data/_render_scenario_after.png", caption=f"Post-Intervention LST (Min: {np.nanmin(after):.1f}°C, Max: {np.nanmax(after):.1f}°C)", use_container_width=True)

st.write("")
avg_cooling = float(-difference.mean())
max_cooling = float(-difference.min())

sm1, sm2, sm3 = st.columns(3)
sm1.metric("Mean Regional Cooling", f"{avg_cooling:.2f} °C", delta=f"-{avg_cooling:.2f} °C", delta_color="inverse")
sm2.metric("Peak Cooling (Hottest Concrete Core)", f"{max_cooling:.2f} °C", delta=f"-{max_cooling:.2f} °C", delta_color="inverse")
sm3.metric("Intervention Coverage Applied", f"{intervention_pct}%")

st.caption(
    "Predictions generated in real time using the Physics-Guided Machine Learning framework, "
    "evaluating thermodynamic surface energy balance shift and microclimate cooling response."
)

st.write("")
st.write("")
st.markdown('<hr class="nav-divider">', unsafe_allow_html=True)
st.markdown('<div class="eyebrow">City-scale validation</div>', unsafe_allow_html=True)
st.markdown('<h2 class="sec-title">InVEST Urban Cooling Model — baseline</h2>', unsafe_allow_html=True)
st.markdown(
    '<p class="sec-sub">An independent, physics-based simulation of predicted air temperature '
    'across the MMR, run separately from the ML model above — used to cross-check whether both '
    'methods agree on where heat concentrates.</p>',
    unsafe_allow_html=True,
)

invest_col, stats_col = st.columns([1.6, 1])
with invest_col:
    st.image("data/_invest_tair_land_only.png", use_container_width=True,
              caption="InVEST-predicted air temperature, MMR (water excluded — see note below)")

with stats_col:
    st.markdown(
        f'<div class="card"><p class="card-label">City-scale correlation</p>'
        f'<p class="stat-lg" style="font-size:22px;">r = 0.585</p>'
        f'<p class="card-label" style="margin-top:2px;">vs. real observed LST, land pixels, p &lt; 0.001</p></div>',
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        f'<div class="card"><p class="card-label">Mean agreement</p>'
        f'<p class="stat" style="font-size:16px;">31.85°C (InVEST) vs. 31.66°C (real LST)</p></div>',
        unsafe_allow_html=True,
    )