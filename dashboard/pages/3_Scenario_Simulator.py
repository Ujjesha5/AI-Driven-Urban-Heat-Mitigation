import pandas as pd
import streamlit as st
from theme import apply_theme, top_nav

st.set_page_config(page_title="Scenario Simulator | GreenGrid", layout="wide")
c = apply_theme()
top_nav("scenario")

st.markdown('<h1>Scenario simulator</h1>', unsafe_allow_html=True)
st.markdown('<p class="sec-sub">Test interventions before committing budget</p>', unsafe_allow_html=True)


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