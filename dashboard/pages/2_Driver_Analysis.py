import json
import pandas as pd
import streamlit as st
from theme import apply_theme, top_nav, DRIVER_COLORS

st.set_page_config(page_title="Driver Analysis | GreenGrid", layout="wide", page_icon="🌳")
c = apply_theme()
top_nav("driver")

st.markdown('<h1>Driver analysis</h1>', unsafe_allow_html=True)
# max-width:none lets the description run the full width of the page
st.markdown(
    '<p class="sec-sub" style="max-width:none;">What\'s driving urban heat across the Mumbai Metropolitan Region — '
    'ranked by TreeSHAP explainability on the trained Physics-Residual Hybrid model.</p>',
    unsafe_allow_html=True,
)


@st.cache_data
def load_driver_importance():
    df = pd.read_csv("model/artifacts/driver_importance.csv", encoding="utf-8")
    return df.sort_values("importance", ascending=False)


@st.cache_data
def load_metrics():
    with open("model/artifacts/metrics.json", encoding="utf-8") as f:
        return json.load(f)


try:
    driver_df = load_driver_importance()
    metrics = load_metrics()
except Exception:
    st.error("Couldn't load the model artifacts. Check that model/artifacts/driver_importance.csv and metrics.json are present.")
    st.stop()


# One distinct colour per driver, assigned by rank in the full ranking (driver_df is
# already sorted by importance). The top 6 are therefore always six different colours,
# and a driver keeps the same colour in the bars and in the full ranking below.
DRIVER_COLOR_MAP = {name: DRIVER_COLORS[i % len(DRIVER_COLORS)] for i, name in enumerate(driver_df["driver"])}


def color_for_driver(driver: str) -> str:
    return DRIVER_COLOR_MAP[driver]


def swatch(color: str) -> str:
    return (f'<span style="width:10px;height:10px;border-radius:50%;background:{color};'
            f'display:inline-block;flex:none;"></span>')


BAR_H = 18  # bar thickness in px

main_col, side_col = st.columns([1.6, 1])

with main_col:
    top6 = driver_df.head(6).reset_index(drop=True)
    max_val = top6["importance"].max()

    # Build the whole card as ONE html string so the bars sit inside the card
    # (separate st.markdown calls can't share an open <div>).
    bars_html = (
        '<div class="card"><p class="card-label" style="margin-bottom:14px;">'
        'Contribution to heat (relative importance)</p>'
    )
    for i, row in top6.iterrows():
        pct_width = int((row["importance"] / max_val) * 100)
        bar_color = color_for_driver(row["driver"])
        bars_html += (
            f'<div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:5px;">'
            f'<span style="display:inline-flex;align-items:center;gap:8px;">{swatch(bar_color)}{row["driver"]}</span>'
            f'<span>{row["importance"]:.3f}</span></div>'
            f'<div class="bar-bg" style="height:{BAR_H}px;border-radius:{BAR_H // 2}px;">'
            f'<div class="bar" style="width:{pct_width}%;background:{bar_color};border-radius:{BAR_H // 2}px;"></div></div>'
            f'<div style="height:16px;"></div>'
        )
    bars_html += '</div>'
    st.markdown(bars_html, unsafe_allow_html=True)

with side_col:
    top_driver = driver_df.iloc[0]
    st.markdown(
        f'<div class="card"><p class="card-label">Top driver</p>'
        f'<p class="stat-lg" style="font-size:18px;">{top_driver["driver"]}</p>'
        f'<p class="card-label" style="margin-top:2px;">{top_driver["category"]}</p></div>',
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        f'<div class="card"><p class="card-label">Model</p>'
        f'<p class="stat" style="font-size:16px;">{metrics["best_model_name"]}</p>'
        f'<p class="card-label" style="margin-top:2px;">R² {metrics["test_r2"]:.4f} · RMSE {metrics["test_rmse"]:.3f}°C</p></div>',
        unsafe_allow_html=True,
    )

st.write("")
st.markdown('<p class="card-label">Full driver ranking</p>', unsafe_allow_html=True)
for _, row in driver_df.iterrows():
    st.markdown(
        f'<div class="row"><span style="display:inline-flex;align-items:center;gap:8px;">'
        f'{swatch(color_for_driver(row["driver"]))}{row["driver"]}</span>'
        f'<span>{row["importance"]:.3f} · {row["category"]}</span></div>',
        unsafe_allow_html=True,
    )

st.write("")
st.write("")

# ---- Model performance ----
st.markdown('<div class="eyebrow">Model performance</div>', unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)
m1.metric("R²", f"{metrics['test_r2']:.4f}")
m2.metric("RMSE", f"{metrics['test_rmse']:.3f} °C")
m3.metric("Physics violations", f"{metrics['physics_violation_rate']*100:.1f}%")
m4.metric("Training samples", f"{metrics['total_training_samples']:,}")

st.write("")
st.markdown('<p class="card-label">Model comparison</p>', unsafe_allow_html=True)
comparison_df = pd.DataFrame(metrics["models_summary"])[
    ["model_name", "r2_score", "rmse_celsius", "physics_violation_rate_pct"]
].rename(columns={
    "model_name": "Model", "r2_score": "R²",
    "rmse_celsius": "RMSE (°C)", "physics_violation_rate_pct": "Physics violation (%)",
})
st.dataframe(comparison_df, use_container_width=True, hide_index=True)
st.caption(
    "The Physics-Residual Hybrid model achieves the best RMSE while maintaining a 0% physics "
    "violation rate, unlike unconstrained baselines which show non-zero violations of expected "
    "physical relationships (e.g., temperature decreasing with NDVI)."
)