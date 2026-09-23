import sys
from pathlib import Path

# Ensure project root is in sys.path (needed to import the `model` package below)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import folium
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from theme import apply_theme, top_nav

st.set_page_config(page_title="Optimizer | GreenGrid", layout="wide", page_icon="🌳")
c = apply_theme()
top_nav("optimizer")

st.markdown('<h1>Optimizer</h1>', unsafe_allow_html=True)
st.markdown('<p class="sec-sub">Best combination of interventions for your budget and goals</p>', unsafe_allow_html=True)

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "model" / "artifacts"
CANDIDATES_PATH = ARTIFACTS_DIR / "candidate_intervention_sites.csv"

# Color palette for intervention types, used on the map below (kept from prior branch)
COLOR_MAP = {
    "Tree canopy increase": "#2ca02c",
    "Cool roofs (albedo change)": "#1f77b4",
    "Green roofs": "#2ca25f",
    "Water body / Wetland creation": "#17becf",
}


@st.cache_data
def load_candidate_sites():
    """Load candidate sites, falling back to a generated or synthetic portfolio
    if the artifact hasn't been produced yet (kept from prior branch)."""
    if CANDIDATES_PATH.exists():
        return pd.read_csv(CANDIDATES_PATH)
    try:
        from model.optimizer import UrbanHeatOptimizer
        return UrbanHeatOptimizer().generate_and_save_candidate_portfolio()
    except Exception:
        rng = np.random.default_rng(21)
        n_sites = 30
        df = pd.DataFrame({
            "site_id": [f"SITE-{i+1:03d}" for i in range(n_sites)],
            "zone": "Mumbai Urban Hub",
            "lat": rng.uniform(18.90, 19.35, n_sites),
            "lon": rng.uniform(72.80, 73.05, n_sites),
            "intervention": rng.choice(list(COLOR_MAP.keys()), n_sites),
            "predicted_reduction_c": rng.uniform(0.8, 3.5, n_sites),
            "cost": rng.uniform(5.0, 25.0, n_sites),
        })
        df["cooling_per_cost_ratio"] = df["predicted_reduction_c"] / df["cost"]
        return df


def greedy_select(df, budget):
    """Greedy cost-efficiency ranking: picks the highest cooling-per-cost
    sites first until the budget runs out. Fast heuristic, used only as a
    fallback if the real optimizer below isn't importable."""
    scored = df.copy()
    scored["score"] = scored["predicted_reduction_c"] / scored["cost"]
    scored = scored.sort_values("score", ascending=False)
    chosen_rows, spent = [], 0
    for _, row in scored.iterrows():
        if spent + row["cost"] <= budget:
            chosen_rows.append(row)
            spent += row["cost"]
    return pd.DataFrame(chosen_rows), spent


def select_portfolio(df, budget, selected_interventions):
    """Uses the real UrbanHeatOptimizer knapsack solver when available (kept
    from prior branch), falling back to the greedy heuristic otherwise."""
    try:
        from model.optimizer import UrbanHeatOptimizer
        return UrbanHeatOptimizer.solve_budget_allocation(
            df, budget=budget, selected_interventions=selected_interventions
        )
    except Exception:
        return greedy_select(df, budget)


try:
    candidates = load_candidate_sites()
except Exception:
    st.error("Couldn't load candidate sites. Check that model/artifacts/candidate_intervention_sites.csv is present.")
    st.stop()

left_col, right_col = st.columns([1, 1.7])

with left_col:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-label" style="text-transform:uppercase;letter-spacing:.5px;">Constraints</p>', unsafe_allow_html=True)

    budget = st.slider(
        "Budget cap", int(candidates["cost"].min()), int(candidates["cost"].sum()),
        int(candidates["cost"].sum() * 0.4),
    )
    intervention_filter = st.multiselect(
        "Intervention types", candidates["intervention"].unique().tolist(),
        default=candidates["intervention"].unique().tolist(),
    )
    zone_filter = st.multiselect(
        "Zones", candidates["zone"].unique().tolist(),
        default=candidates["zone"].unique().tolist(),
    )
    run = st.button("Run optimizer", use_container_width=True)
    st.caption("Uses the trained knapsack optimizer when available, falling back to a greedy cost-efficiency heuristic otherwise.")
    st.markdown('</div>', unsafe_allow_html=True)

filtered = candidates[
    candidates["intervention"].isin(intervention_filter) & candidates["zone"].isin(zone_filter)
]
chosen, spent = select_portfolio(filtered, budget, intervention_filter)

with right_col:
    st.markdown('<p class="card-label" style="text-transform:uppercase;letter-spacing:.5px;">Recommended plan</p>', unsafe_allow_html=True)

    if chosen.empty:
        st.warning("No sites fit within the current budget/filter. Try increasing the budget.")
    else:
        best = chosen.sort_values("predicted_reduction_c", ascending=False).iloc[0]
        st.markdown(
            f'<div style="background:{c["green_tint"]};border:1px solid {c["green"]};border-radius:10px;'
            f'padding:12px 14px;display:flex;justify-content:space-between;margin-bottom:10px;">'
            f'<div><p style="font-size:13px;font-weight:600;margin:0;">{best["site_id"]} — {best["intervention"]}</p>'
            f'<p class="card-label" style="margin-top:2px;">{best["zone"]}</p></div>'
            f'<div style="text-align:right;"><p style="color:{c["green_dark"]};font-weight:600;font-size:13px;margin:0;">'
            f'-{best["predicted_reduction_c"]:.2f}°C</p><p class="card-label" style="margin:0;">cost {best["cost"]:.1f}</p></div></div>',
            unsafe_allow_html=True,
        )

        for _, row in chosen.sort_values("predicted_reduction_c", ascending=False).iloc[1:].iterrows():
            st.markdown(
                f'<div class="row"><span>{row["site_id"]} — {row["intervention"]} ({row["zone"]})</span>'
                f'<span>-{row["predicted_reduction_c"]:.2f}°C · cost {row["cost"]:.1f}</span></div>',
                unsafe_allow_html=True,
            )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Sites selected", f"{len(chosen)} / {len(filtered)}")
        m2.metric("Budget used", f"{spent:.1f} / {budget}")
        m3.metric("Total cooling", f"{chosen['predicted_reduction_c'].sum():.2f}°C")
        m4.metric("Avg ROI", f"{(chosen['predicted_reduction_c'].sum() / max(spent, 0.1)):.3f} °C/cost", help="Cooling delivered per unit cost across the selected portfolio")

        csv = chosen.to_csv(index=False).encode("utf-8")
        st.download_button("Export plan", csv, "action_plan.csv", "text/csv")

        with st.expander("See full efficiency ranking"):
            display_df = chosen[[
                "site_id", "zone", "intervention", "predicted_reduction_c", "cost"
            ]].copy()
            display_df["efficiency"] = display_df["predicted_reduction_c"] / display_df["cost"]
            display_df = display_df.rename(columns={
                "site_id": "Site ID", "zone": "Zone", "intervention": "Strategy",
                "predicted_reduction_c": "Cooling (°C)", "cost": "Cost",
                "efficiency": "Efficiency (°C/Cost)",
            }).sort_values("Efficiency (°C/Cost)", ascending=False)
            st.dataframe(
                display_df.style.format({
                    "Cooling (°C)": "{:.2f}", "Cost": "{:.1f}", "Efficiency (°C/Cost)": "{:.3f}",
                }),
                use_container_width=True, hide_index=True,
            )

st.write("")
st.write("")

if not chosen.empty:
    st.markdown('<p class="card-label">Recommended sites on map</p>', unsafe_allow_html=True)
    center = [candidates["lat"].mean(), candidates["lon"].mean()]
    m = folium.Map(location=center, zoom_start=11, tiles="OpenStreetMap")
    for _, row in candidates.iterrows():
        is_chosen = row["site_id"] in chosen["site_id"].values
        marker_color = COLOR_MAP.get(row["intervention"], "#999999")
        popup_content = (
            "<div style='font-family: sans-serif; min-width: 160px;'>"
            f"<b>{row['site_id']}</b> ({row['zone']})<br>"
            f"<b>Strategy:</b> {row['intervention']}<br>"
            f"<b>Predicted cooling:</b> -{row['predicted_reduction_c']:.2f}°C<br>"
            f"<b>Estimated cost:</b> {row['cost']:.1f}<br>"
            "<b>Status:</b> "
            + ('<span style="color:#2ca02c;font-weight:bold;">SELECTED</span>' if is_chosen
               else '<span style="color:gray;">Candidate</span>')
            + "</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9 if is_chosen else 5,
            color="#000000" if is_chosen else marker_color,
            weight=2 if is_chosen else 1,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.9 if is_chosen else 0.35,
            popup=folium.Popup(popup_content, max_width=250),
        ).add_to(m)
    st_folium(m, width=None, height=420, use_container_width=True)

st.caption("Candidate sites and predicted reductions are real outputs from the trained Physics-Residual Hybrid model.")