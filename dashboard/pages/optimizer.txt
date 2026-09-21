import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium
from theme import apply_theme, top_nav

st.set_page_config(page_title="Optimizer | GreenGrid", layout="wide")
c = apply_theme()
top_nav("optimizer")

st.markdown('<h1>Optimizer</h1>', unsafe_allow_html=True)
st.markdown('<p class="sec-sub">Best combination of interventions for your budget and goals</p>', unsafe_allow_html=True)


@st.cache_data
def load_candidate_sites():
    return pd.read_csv("model/artifacts/candidate_intervention_sites.csv", encoding="utf-8")


def greedy_select(df, budget):
    scored = df.copy()
    scored["score"] = scored["predicted_reduction_c"] / scored["cost"]
    scored = scored.sort_values("score", ascending=False)
    chosen_rows, spent = [], 0
    for _, row in scored.iterrows():
        if spent + row["cost"] <= budget:
            chosen_rows.append(row)
            spent += row["cost"]
    return pd.DataFrame(chosen_rows), spent


candidates = load_candidate_sites()

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
    run = st.button("run optimizer", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

filtered = candidates[
    candidates["intervention"].isin(intervention_filter) & candidates["zone"].isin(zone_filter)
]
chosen, spent = greedy_select(filtered, budget)

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

        m1, m2, m3 = st.columns(3)
        m1.metric("Sites selected", len(chosen))
        m2.metric("Budget used", f"{spent:.1f} / {budget}")
        m3.metric("Total cooling", f"{chosen['predicted_reduction_c'].sum():.2f}°C")

        csv = chosen.to_csv(index=False).encode("utf-8")
        st.download_button("export plan", csv, "action_plan.csv", "text/csv")

st.write("")
st.write("")

if not chosen.empty:
    st.markdown('<p class="card-label">Recommended sites on map</p>', unsafe_allow_html=True)
    center = [candidates["lat"].mean(), candidates["lon"].mean()]
    m = folium.Map(location=center, zoom_start=11, tiles="OpenStreetMap")
    for _, row in candidates.iterrows():
        is_chosen = row["site_id"] in chosen["site_id"].values
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8 if is_chosen else 4,
            color=c["coral_dark"] if is_chosen else "#999999",
            fill=True, fill_opacity=0.85 if is_chosen else 0.3,
            popup=f"{row['site_id']} ({row['zone']}): {row['intervention']}, -{row['predicted_reduction_c']:.2f}°C, cost {row['cost']}",
        ).add_to(m)
    st_folium(m, width=None, height=420, use_container_width=True)

st.caption("Candidate sites and predicted reductions are real outputs from the trained Physics-Residual Hybrid model.")