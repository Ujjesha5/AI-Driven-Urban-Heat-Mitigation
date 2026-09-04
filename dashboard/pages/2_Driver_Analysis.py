import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.title("Driver Analysis")

with st.expander("About this page"):
    st.write(
        "Shows which factors most strongly influence Land Surface Temperature (LST) in a given area, "
        "based on SHAP (SHapley Additive exPlanations) values from the ML model. "
        "Currently showing placeholder data — will be replaced with real SHAP output from Person B's trained model."
    )


# --- DUMMY DATA SECTION ---
# Person B: replace this whole function with code that loads your real SHAP values,
# e.g. from a saved .csv or .pkl file produced by your model training script.
# Keep the same output shape: a DataFrame with columns "driver" and "importance".
@st.cache_data
def get_dummy_driver_importance():
    drivers = [
        "Impervious surface %",
        "NDVI (vegetation)",
        "Building density",
        "Distance to water body",
        "Sky view factor",
        "NDBI (built-up index)",
        "Elevation",
        "Wind speed",
        "Humidity",
        "Slope",
    ]
    # Random but sorted-looking fake importance values, just for layout purposes
    rng = np.random.default_rng(seed=42)  # fixed seed so dummy values don't change every rerun
    importance = np.sort(rng.uniform(0.02, 0.35, len(drivers)))[::-1]
    return pd.DataFrame({"driver": drivers, "importance": importance})


driver_df = get_dummy_driver_importance()

st.subheader("Driver importance ranking")

fig = px.bar(
    driver_df.sort_values("importance"),
    x="importance",
    y="driver",
    orientation="h",
    labels={"importance": "Mean |SHAP value| (relative influence on LST)", "driver": ""},
    color="importance",
    color_continuous_scale="RdYlBu_r",
)
fig.update_layout(coloraxis_showscale=False, height=450, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Placeholder data (randomly generated, fixed seed for consistent layout). "
    "Will be replaced with real SHAP values once Person B's model is trained and validated."
)

st.divider()

st.subheader("Model validation metrics")
col1, col2, col3 = st.columns(3)
col1.metric("RMSE", "—", help="Root Mean Squared Error — pending real model")
col2.metric("R²", "—", help="Coefficient of determination — pending real model")
col3.metric("Training samples", "—", help="Number of data points used to train the model")
st.caption("Metrics will populate once Person B's model training is complete.")