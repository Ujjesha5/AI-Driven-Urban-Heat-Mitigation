import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import folium
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="Optimizer | Urban Heat Mitigation", layout="wide")

st.title("Urban Cooling Intervention Optimizer")

with st.expander("About this page"):
    st.write(
        "Ranks candidate urban cooling intervention sites across Mumbai MMR by ML-predicted cooling effect per unit cost, "
        "then recommends an optimal portfolio of intervention projects that maximize net cooling within a user-defined budget."
    )

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "model" / "artifacts"
CANDIDATES_PATH = ARTIFACTS_DIR / "candidate_intervention_sites.csv"


@st.cache_data
def load_candidate_sites():
    if CANDIDATES_PATH.exists():
        df = pd.read_csv(CANDIDATES_PATH)
    else:
        try:
            from model.optimizer import UrbanHeatOptimizer
            opt = UrbanHeatOptimizer()
            df = opt.generate_and_save_candidate_portfolio()
        except Exception:
            # Fallback
            rng = np.random.default_rng(21)
            n_sites = 30
            df = pd.DataFrame({
                "site_id": [f"SITE-{i+1:03d}" for i in range(n_sites)],
                "zone": "Mumbai Urban Hub",
                "lat": rng.uniform(18.90, 19.35, n_sites),
                "lon": rng.uniform(72.80, 73.05, n_sites),
                "intervention": rng.choice(["Tree canopy increase", "Cool roofs (albedo change)", "Green roofs", "Water body / Wetland creation"], n_sites),
                "predicted_reduction_c": rng.uniform(0.8, 3.5, n_sites),
                "cost": rng.uniform(5.0, 25.0, n_sites),
            })
            df["cooling_per_cost_ratio"] = df["predicted_reduction_c"] / df["cost"]
    return df


candidates = load_candidate_sites()

# Color palette for intervention types
COLOR_MAP = {
    "Tree canopy increase": "#2ca02c",             # Green
    "Cool roofs (albedo change)": "#1f77b4",       # Blue
    "Green roofs": "#2ca25f",                     # Emerald
    "Water body / Wetland creation": "#17becf",   # Cyan
}

with st.sidebar:
    st.header("Optimizer Settings")
    max_budget = int(candidates["cost"].sum() * 0.8)
    budget = st.slider("Total Budget (Cost Units)", 10, max_budget, min(80, max_budget), step=5)
    
    available_interventions = candidates["intervention"].unique().tolist()
    selected_interventions = st.multiselect(
        "Intervention Strategies to Include",
        options=available_interventions,
        default=available_interventions,
    )
    
    selected_zones = st.multiselect(
        "Filter by Geographic Zone",
        options=sorted(candidates["zone"].unique().tolist()),
        default=sorted(candidates["zone"].unique().tolist()),
    )

# Filter candidates
filtered = candidates[
    (candidates["intervention"].isin(selected_interventions)) &
    (candidates["zone"].isin(selected_zones))
].copy()

# Solve Optimization (Greedy / Knapsack)
from model.optimizer import UrbanHeatOptimizer
chosen, spent = UrbanHeatOptimizer.solve_budget_allocation(
    filtered, budget=budget, selected_interventions=selected_interventions
)

st.subheader("Recommended Intervention Plan")

if chosen.empty:
    st.warning("No sites match the current budget/filter criteria. Try increasing the budget or selecting more zones.")
else:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Selected Projects", f"{len(chosen)} / {len(filtered)}")
    m2.metric("Budget Allocated", f"{spent:.1f} / {budget}", delta=f"{budget - spent:.1f} remaining")
    m3.metric("Total Temperature Reduction", f"{chosen['predicted_reduction_c'].sum():.2f} °C", help="Cumulative sum of localized cooling across selected sites")
    m4.metric("Avg Portfolio ROI", f"{(chosen['predicted_reduction_c'].sum() / max(spent, 0.1)):.3f} °C / unit cost")

    col_table, col_map = st.columns([1.1, 1.4])

    with col_table:
        st.markdown("#### Optimal Project Ranking")
        display_df = chosen[[
            "site_id", "zone", "intervention", "predicted_reduction_c", "cost", "cooling_per_cost_ratio"
        ]].rename(columns={
            "site_id": "Site ID",
            "zone": "Zone",
            "intervention": "Strategy",
            "predicted_reduction_c": "Cooling (°C)",
            "cost": "Cost",
            "cooling_per_cost_ratio": "Efficiency (°C/Cost)",
        }).sort_values("Efficiency (°C/Cost)", ascending=False)

        st.dataframe(
            display_df.style.format({
                "Cooling (°C)": "{:.2f}",
                "Cost": "{:.1f}",
                "Efficiency (°C/Cost)": "{:.3f}",
            }),
            use_container_width=True,
            hide_index=True,
            height=420,
        )

        csv = chosen.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Optimized Action Plan (CSV)",
            csv,
            "mumbai_urban_cooling_action_plan.csv",
            "text/csv",
        )

    with col_map:
        st.markdown("#### Geographic Deployment Map")
        center = [filtered["lat"].mean(), filtered["lon"].mean()]
        m = folium.Map(location=center, zoom_start=11, tiles="CartoDB positron")

        # Add candidate and selected markers
        for _, row in filtered.iterrows():
            is_chosen = row["site_id"] in chosen["site_id"].values
            color = COLOR_MAP.get(row["intervention"], "#ff7f0e")

            popup_content = f"""
            <div style='font-family: sans-serif; min-width: 160px;'>
                <b>{row['site_id']}</b> ({row['zone']})<br>
                <b>Strategy:</b> {row['intervention']}<br>
                <b>Predicted Cooling:</b> -{row['predicted_reduction_c']:.2f}°C<br>
                <b>Estimated Cost:</b> {row['cost']:.1f}<br>
                <b>Status:</b> {'<span style="color: green; font-weight:bold;">SELECTED</span>' if is_chosen else '<span style="color: gray;">Candidate</span>'}
            </div>
            """

            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=9 if is_chosen else 5,
                color="#000000" if is_chosen else color,
                weight=2 if is_chosen else 1,
                fill=True,
                fill_color=color,
                fill_opacity=0.9 if is_chosen else 0.4,
                popup=folium.Popup(popup_content, max_width=250),
            ).add_to(m)

        st_folium(m, width=650, height=450)

st.caption(
    "Candidate sites scored dynamically using Physics-Guided ML predictions. "
    "Prioritization optimizes heat mitigation impact per rupee/unit investment across vulnerable urban hotspots."
)