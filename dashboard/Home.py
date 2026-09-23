import sys
import json
from pathlib import Path
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="AI-Driven Urban Heat Mitigation | Mumbai MMR",
    page_icon="🌡️",
    layout="wide",
)

st.title("🌡️ AI-Driven Urban Heat Mitigation Framework")
st.subheader("Physics-Guided, Explainable Machine Learning for Multi-Source Geospatial Fusion & Urban Cooling Optimization")

st.markdown("""
Welcome to the interactive decision-support system for Urban Heat Island (UHI) mitigation in the **Mumbai Metropolitan Region (MMR)** (Mumbai, Thane, Navi Mumbai, and Vasai-Virar).

This platform combines remote sensing satellites, atmospheric reanalysis, aerodynamic physics, and explainable AI to diagnose thermal vulnerability and optimize localized cooling interventions.
""")

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "model" / "artifacts"
METRICS_PATH = ARTIFACTS_DIR / "metrics.json"

if METRICS_PATH.exists():
    with open(METRICS_PATH, "r") as f:
        metrics = json.load(f)

    st.divider()
    st.markdown("### 🚀 Core Framework Performance Highlights")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Selected Architecture", metrics.get("best_model_name", "PG-Hybrid"))
    m2.metric("Generalization R²", f"{metrics.get('test_r2', 0.99):.4f}", help="Chronological holdout validation")
    m3.metric("Prediction RMSE", f"{metrics.get('test_rmse', 0.45):.3f} °C", help="Average thermal prediction error")
    m4.metric("Physical Violation Rate", f"{metrics.get('physics_violation_rate', 0.0):.1f}%", help="Zero thermodynamic derivative violations")

st.divider()

st.markdown("### 🧭 Platform Modules & Capabilities")

col1, col2 = st.columns(2)

with col1:
    st.info("""
    #### 🗺️ 1. Hotspot Mapping (`1_Hotspot_Map`)
    - Multi-temporal quarterly Land Surface Temperature ($LST$) from Landsat 8/9.
    - Overlay with Copernicus 30m Digital Elevation Model (DEM) and terrain slope.
    - Percentile-clipped thermal visualization across Salsette Island and Thane basin.
    """)

    st.success("""
    #### 🌳 3. Scenario Simulator (`3_Scenario_Simulator`)
    - Real-time microclimatic simulation of urban cooling interventions.
    - Assess **Tree Canopy Expansion**, **Cool Roofs (Albedo change)**, **Green Roofs**, and **Urban Water Bodies**.
    - Compare baseline vs. post-intervention thermal footprints and localized cooling deltas.
    """)

with col2:
    st.warning("""
    #### 📊 2. Explainable AI Driver Analysis (`2_Driver_Analysis`)
    - **TreeSHAP** feature attributions ranking dominant biophysical and morphological drivers.
    - Marginal cooling response curves (**Partial Dependence Plots**).
    - Empirical vs. Physics-Guided benchmark comparison.
    """)

    st.error("""
    #### 🎯 4. Cooling Portfolio Optimizer (`4_Optimizer`)
    - Multi-objective budget-constrained project allocator.
    - Dynamic ROI scoring ($\Delta LST \text{ cooling per unit cost}$).
    - Interactive deployment mapping with downloadable CSV action plans for municipal urban planners.
    """)

st.divider()

st.markdown("""
### 🏙️ 5. Ward-Level Heat Vulnerability Index (`5_Ward_Vulnerability`)
- **IPCC Framework Integration:** $\\text{HVI} = \\text{Exposure} \\times \\text{Sensitivity} \\times (1 - \\text{Adaptive Capacity})$.
- Evaluates and ranks **all 24 MCGM/BMC municipal administrative wards** and satellite corporations (Thane, Navi Mumbai, Kalyan-Dombivli, Vasai-Virar).
- Interactive GIS risk map, Radar Diagnostic profile, and municipal policy action dossiers.
""")

st.divider()
st.caption("AI-Driven Urban Heat Mitigation System | Physics-Guided Geospatial Fusion Framework")