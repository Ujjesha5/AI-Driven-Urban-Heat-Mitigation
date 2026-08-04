import numpy as np
import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium

st.title("Optimizer")

with st.expander("About this page"):
    st.write(
        "Ranks candidate intervention sites by predicted cooling effect per unit cost, "
        "then recommends a set of sites that fit within a chosen budget. "
        "Currently using placeholder candidate sites and predicted reductions — "
        "will be replaced with real outputs from the ML model (Person B) and InVEST scenarios (Person C)."
    )


# --- DUMMY DATA SECTION ---
# Replace this function once real inputs exist:
#   - "predicted_reduction_c" should come from running each candidate site through
#     the trained ML model or InVEST, comparing baseline vs. intervention
#   - "lat"/"lon" should come from Person A's feasibility mask (buildable/plantable areas)
#   - "cost" is a placeholder unit-cost estimate per site; refine with real cost assumptions later
@st.cache_data
def get_dummy_candidate_sites():
    rng = np.random.default_rng(seed=21)
    n_sites = 25
    # Roughly scattered around the Mumbai Metropolitan Region bounds
    lats = rng.uniform(18.85, 19.45, n_sites)
    lons = rng.uniform(72.75, 73.05, n_sites)
    interventions = rng.choice(
        ["Tree canopy", "Cool roof", "Green roof", "Water body"], n_sites
    )
    predicted_reduction = rng.uniform(0.5, 3.2, n_sites)
    cost = rng.uniform(3, 25, n_sites)

    return pd.DataFrame({
        "site_id": [f"S{i+1:02d}" for i in range(n_sites)],
        "lat": lats,
        "lon": lons,
        "intervention": interventions,
        "predicted_reduction_c": predicted_reduction,
        "cost": cost,
    })


def greedy_select(df, budget):
    """Simple greedy optimizer: rank by cooling-per-cost, pick sites until budget runs out."""
    scored = df.copy()
    scored["score"] = scored["predicted_reduction_c"] / scored["cost"]
    scored = scored.sort_values("score", ascending=False)

    chosen_rows = []
    spent = 0
    for _, row in scored.iterrows():
        if spent + row["cost"] <= budget:
            chosen_rows.append(row)
            spent += row["cost"]

    chosen = pd.DataFrame(chosen_rows)
    return chosen, spent


candidates = get_dummy_candidate_sites()

with st.sidebar:
    st.header("Optimizer Controls")
    budget = st.slider("Budget (arbitrary cost units)", 10, 150, 60)
    intervention_filter = st.multiselect(
        "Intervention types to consider",
        options=candidates["intervention"].unique().tolist(),
        default=candidates["intervention"].unique().tolist(),
    )

filtered = candidates[candidates["intervention"].isin(intervention_filter)]
chosen, spent = greedy_select(filtered, budget)

st.subheader("Recommended intervention plan")

if chosen.empty:
    st.warning("No sites fit within the current budget/filter. Try increasing the budget.")
else:
    m1, m2, m3 = st.columns(3)
    m1.metric("Sites selected", len(chosen))
    m2.metric("Budget used", f"{spent:.1f} / {budget}")
    m3.metric("Total predicted cooling", f"{chosen['predicted_reduction_c'].sum():.1f} °C (summed)")

    st.dataframe(
        chosen[["site_id", "intervention", "predicted_reduction_c", "cost"]]
        .rename(columns={
            "site_id": "Site",
            "intervention": "Intervention",
            "predicted_reduction_c": "Predicted reduction (°C)",
            "cost": "Cost",
        })
        .sort_values("Predicted reduction (°C)", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    csv = chosen.to_csv(index=False).encode("utf-8")
    st.download_button("Download action plan (CSV)", csv, "action_plan.csv", "text/csv")

    st.subheader("Recommended sites on map")
    center = [candidates["lat"].mean(), candidates["lon"].mean()]
    m = folium.Map(location=center, zoom_start=10, tiles="cartodbpositron")

    for _, row in candidates.iterrows():
        is_chosen = row["site_id"] in chosen["site_id"].values
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=7 if is_chosen else 4,
            color="#d62728" if is_chosen else "#999999",
            fill=True,
            fill_opacity=0.8 if is_chosen else 0.3,
            popup=f"{row['site_id']}: {row['intervention']}, {row['predicted_reduction_c']:.1f}°C reduction",
        ).add_to(m)

    st_folium(m, width=900, height=500)

st.caption(
    "Placeholder candidate sites and predicted reductions. "
    "Will be replaced with real feasibility-masked sites (Person A) and real predicted reductions (Person B / InVEST)."
)