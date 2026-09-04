"""
Comprehensive Evaluation Suite for Physics-Guided Urban Heat Mitigation ML.
Tests spatial generalization, bootstrap confidence intervals, and physical plausibility.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from model.config import ALL_FEATURES, ARTIFACTS_DIR
from model.dataset_builder import MultiSourceGeospatialFusion, SpatialTemporalSplitter
from model.physics_engine import compute_physical_violation_rate

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def bootstrap_metric_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_bootstraps: int = 500,
    confidence_level: float = 0.95,
    random_seed: int = 42,
) -> Dict[str, Tuple[float, float, float]]:
    """Calculates bootstrap mean and confidence intervals (95% CI) for R2 and RMSE."""
    rng = np.random.default_rng(random_seed)
    n = len(y_true)
    r2_boot = []
    rmse_boot = []
    mae_boot = []

    for _ in range(n_bootstraps):
        idx = rng.choice(n, size=n, replace=True)
        y_t = y_true[idx]
        y_p = y_pred[idx]
        r2_boot.append(r2_score(y_t, y_p))
        rmse_boot.append(np.sqrt(mean_squared_error(y_t, y_p)))
        mae_boot.append(mean_absolute_error(y_t, y_p))

    alpha_low = ((1.0 - confidence_level) / 2.0) * 100
    alpha_high = (1.0 - (1.0 - confidence_level) / 2.0) * 100

    return {
        "r2": (
            round(float(np.mean(r2_boot)), 4),
            round(float(np.percentile(r2_boot, alpha_low)), 4),
            round(float(np.percentile(r2_boot, alpha_high)), 4),
        ),
        "rmse": (
            round(float(np.mean(rmse_boot)), 3),
            round(float(np.percentile(rmse_boot, alpha_low)), 3),
            round(float(np.percentile(rmse_boot, alpha_high)), 3),
        ),
        "mae": (
            round(float(np.mean(mae_boot)), 3),
            round(float(np.percentile(mae_boot, alpha_low)), 3),
            round(float(np.percentile(mae_boot, alpha_high)), 3),
        ),
    }


def run_full_evaluation() -> Dict[str, Any]:
    """Runs rigorous benchmarking on the trained best model."""
    logging.info("Starting evaluation benchmark...")
    model_path = ARTIFACTS_DIR / "best_pg_model.joblib"
    if not model_path.exists():
        raise FileNotFoundError(f"Model artifact not found at {model_path}. Run train.py first.")

    model = joblib.load(model_path)
    fusion = MultiSourceGeospatialFusion()
    df = fusion.get_dataset(use_cache=True)

    _, _, test_df = SpatialTemporalSplitter.train_val_test_split(df, test_year=2026)
    X_test, y_test = SpatialTemporalSplitter.get_features_and_target(test_df)

    y_pred = model.predict(X_test)
    y_true = y_test.values

    # Bootstrap CIs
    ci_metrics = bootstrap_metric_ci(y_true, y_pred)

    # Physical violation breakdown
    violations = compute_physical_violation_rate(model, X_test)

    # Spatial Slice Error Analysis (by Urban vs Coastal vs Suburban)
    test_df_eval = test_df.copy()
    test_df_eval["pred"] = y_pred
    test_df_eval["error"] = np.abs(y_true - y_pred)

    spatial_slices = {}
    test_df_eval["zone_type"] = np.where(
        test_df_eval["dist_to_coast"] < 3.0, "Coastal Belt",
        np.where(test_df_eval["building_fraction"] > 55.0, "Dense Urban Core", "Suburban / Rural Fringe")
    )

    for zone, group in test_df_eval.groupby("zone_type"):
        spatial_slices[zone] = {
            "samples": len(group),
            "mean_actual_lst": round(float(group["lst_celsius"].mean()), 2),
            "mean_pred_lst": round(float(group["pred"].mean()), 2),
            "rmse": round(float(np.sqrt(mean_squared_error(group["lst_celsius"], group["pred"]))), 3),
            "mae": round(float(mean_absolute_error(group["lst_celsius"], group["pred"])), 3),
        }

    evaluation_report = {
        "bootstrap_ci_95": {
            "r2_score": {"mean": ci_metrics["r2"][0], "ci_lower": ci_metrics["r2"][1], "ci_upper": ci_metrics["r2"][2]},
            "rmse_celsius": {"mean": ci_metrics["rmse"][0], "ci_lower": ci_metrics["rmse"][1], "ci_upper": ci_metrics["rmse"][2]},
            "mae_celsius": {"mean": ci_metrics["mae"][0], "ci_lower": ci_metrics["mae"][1], "ci_upper": ci_metrics["mae"][2]},
        },
        "physics_violation_summary": violations,
        "spatial_slice_analysis": spatial_slices,
    }

    eval_out_path = ARTIFACTS_DIR / "evaluation_report.json"
    with open(eval_out_path, "w") as f:
        json.dump(evaluation_report, f, indent=2)

    logging.info("Evaluation report completed successfully.")
    return evaluation_report


if __name__ == "__main__":
    run_full_evaluation()
