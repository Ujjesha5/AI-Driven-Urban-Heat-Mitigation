"""
Explainable AI (XAI) Module for Urban Heat Mitigation.
Computes TreeSHAP feature attributions, partial dependence response functions,
and exports structured explainability artifacts for dashboard rendering.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
import shap

from model.config import (
    ALL_FEATURES,
    ARTIFACTS_DIR,
    FEATURE_LABEL_MAP,
    SPECTRAL_FEATURES,
    TOPOGRAPHIC_FEATURES,
    MORPHOLOGICAL_FEATURES,
    METEOROLOGICAL_FEATURES,
    SPATIAL_FEATURES,
)
from model.dataset_builder import MultiSourceGeospatialFusion, SpatialTemporalSplitter
from model.models import PhysicsGuidedXGBoostModel, PhysicsResidualHybridModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class HeatMitigationExplainer:
    """Computes global and local explainability metrics using SHAP & Partial Dependence."""

    def __init__(self, model_path: Optional[Path] = None):
        if model_path is None:
            model_path = ARTIFACTS_DIR / "best_pg_model.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Model artifact not found at {model_path}. Run train.py first.")

        self.model = joblib.load(model_path)
        self.underlying_tree_model = self._extract_tree_model(self.model)
        self.explainer = shap.TreeExplainer(self.underlying_tree_model)

    @staticmethod
    def _extract_tree_model(model_obj):
        """Extracts the underlying XGBoost booster from custom wrapper if applicable."""
        if hasattr(model_obj, "model") and model_obj.model is not None:
            return model_obj.model
        elif hasattr(model_obj, "residual_model") and model_obj.residual_model is not None:
            return model_obj.residual_model
        return model_obj

    def compute_shap_importance(
        self,
        X_sample: pd.DataFrame,
        n_background: int = 1500,
    ) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Computes Mean Absolute SHAP values across test samples.
        Returns a DataFrame formatted for direct use in the Streamlit Driver Analysis page.
        """
        if len(X_sample) > n_background:
            X_eval = X_sample.sample(n=n_background, random_state=42)
        else:
            X_eval = X_sample

        shap_values = self.explainer.shap_values(X_eval)

        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)

        # Categorize features
        def categorize(feat):
            if feat in SPECTRAL_FEATURES:
                return "Spectral / Surface Cover"
            if feat in TOPOGRAPHIC_FEATURES:
                return "Topography & Terrain"
            if feat in MORPHOLOGICAL_FEATURES:
                return "Urban Morphology"
            if feat in METEOROLOGICAL_FEATURES:
                return "Meteorology"
            if feat in SPATIAL_FEATURES:
                return "Spatial Proximity"
            return "Other"

        importance_df = pd.DataFrame({
            "feature": X_eval.columns,
            "driver": [FEATURE_LABEL_MAP.get(f, f) for f in X_eval.columns],
            "importance": mean_abs_shap,
            "category": [categorize(f) for f in X_eval.columns],
        }).sort_values("importance", ascending=False).reset_index(drop=True)

        return importance_df, shap_values

    def compute_partial_dependence(
        self,
        X_sample: pd.DataFrame,
        feature_name: str,
        grid_resolution: int = 30,
    ) -> Dict[str, Any]:
        """Computes 1D Partial Dependence curve for a chosen feature."""
        if feature_name not in X_sample.columns:
            raise ValueError(f"Feature {feature_name} not found in sample columns.")

        vals = X_sample[feature_name].values
        q_low, q_high = np.percentile(vals, [2, 98])
        grid = np.linspace(q_low, q_high, grid_resolution)

        # Marginal response curve
        pdp_values = []
        sample_subset = X_sample.sample(min(300, len(X_sample)), random_state=42).copy()

        for val in grid:
            temp_X = sample_subset.copy()
            temp_X[feature_name] = val
            preds = self.model.predict(temp_X)
            pdp_values.append(float(np.mean(preds)))

        baseline_pred = float(np.mean(self.model.predict(sample_subset)))
        cooling_response = [float(baseline_pred - p) for p in pdp_values]

        return {
            "feature": feature_name,
            "feature_label": FEATURE_LABEL_MAP.get(feature_name, feature_name),
            "grid_values": [round(float(v), 4) for v in grid],
            "marginal_lst_pred": [round(float(p), 3) for p in pdp_values],
            "marginal_cooling_delta": [round(float(c), 3) for c in cooling_response],
        }

    def generate_and_save_all_explanations(self) -> Dict[str, Any]:
        """Computes all global attributions and PDP curves, saving artifacts to disk."""
        logging.info("Generating SHAP and XAI explanations...")
        fusion = MultiSourceGeospatialFusion()
        df = fusion.get_dataset(use_cache=True)
        _, _, test_df = SpatialTemporalSplitter.train_val_test_split(df, test_year=2026)
        X_test, _ = SpatialTemporalSplitter.get_features_and_target(test_df)

        importance_df, shap_values = self.compute_shap_importance(X_test)

        # Save driver importance CSV for dashboard
        importance_path = ARTIFACTS_DIR / "driver_importance.csv"
        importance_df.to_csv(importance_path, index=False)
        logging.info(f"Driver importance saved to {importance_path}")

        # Compute key intervention PDPs (NDVI, Albedo, Building Fraction, Wind Speed)
        pdp_results = {}
        for feat in ["ndvi", "albedo", "building_fraction", "wind_speed_10m", "ndbi"]:
            if feat in X_test.columns:
                pdp_results[feat] = self.compute_partial_dependence(X_test, feat)

        pdp_path = ARTIFACTS_DIR / "pdp_curves.json"
        with open(pdp_path, "w") as f:
            json.dump(pdp_results, f, indent=2)
        logging.info(f"PDP curves saved to {pdp_path}")

        summary = {
            "top_driver": importance_df.iloc[0]["driver"],
            "top_driver_importance": round(float(importance_df.iloc[0]["importance"]), 4),
            "driver_ranking": importance_df.to_dict(orient="records"),
        }
        return summary


def run_explainability_pipeline():
    explainer = HeatMitigationExplainer()
    return explainer.generate_and_save_all_explanations()


if __name__ == "__main__":
    run_explainability_pipeline()
