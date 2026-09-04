"""
Training Pipeline for Urban Heat Mitigation Models.
Performs model training, cross-validation, physical violation auditing,
and artifact serializations.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from model.config import (
    ALL_FEATURES,
    ARTIFACTS_DIR,
    TARGET_VARIABLE,
    ModelTrainingConfig,
)
from model.dataset_builder import MultiSourceGeospatialFusion, SpatialTemporalSplitter
from model.models import (
    BaselineRandomForestModel,
    BaselineRidgeModel,
    PhysicsGuidedXGBoostModel,
    PhysicsResidualHybridModel,
    UnconstrainedXGBoostModel,
)
from model.physics_engine import compute_physical_violation_rate

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def evaluate_model_performance(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_name: str,
) -> Dict[str, Any]:
    """Computes statistical metrics (R2, RMSE, MAE) and Physics Violation Rate (PVR)."""
    preds = model.predict(X_test)

    r2 = float(r2_score(y_test, preds))
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    mae = float(mean_absolute_error(y_test, preds))
    mape = float(np.mean(np.abs((y_test - preds) / y_test)) * 100.0)

    # Compute physical violation rate (derivative sign check)
    violations = compute_physical_violation_rate(model, X_test)
    pvr_mean = violations.get("overall_mean_violation_pct", 0.0)

    metrics = {
        "model_name": model_name,
        "r2_score": round(r2, 4),
        "rmse_celsius": round(rmse, 3),
        "mae_celsius": round(mae, 3),
        "mape_percent": round(mape, 2),
        "physics_violation_rate_pct": round(pvr_mean, 2),
        "feature_violations": violations,
    }
    return metrics


def run_training_pipeline() -> Dict[str, Any]:
    """Executes the full end-to-end model training, comparison, and serialization."""
    logging.info("Step 1: Loading / fusing multi-source geospatial dataset...")
    fusion = MultiSourceGeospatialFusion()
    df = fusion.get_dataset(use_cache=True)
    logging.info(f"Dataset ready with {len(df):,} samples across {df['quarter'].nunique()} quarters.")

    logging.info("Step 2: Partitioning via Spatial Block CV and Chronological Holdout...")
    train_df, val_df, test_df = SpatialTemporalSplitter.train_val_test_split(df, test_year=2026)

    X_train, y_train = SpatialTemporalSplitter.get_features_and_target(train_df)
    X_val, y_val = SpatialTemporalSplitter.get_features_and_target(val_df)
    X_test, y_test = SpatialTemporalSplitter.get_features_and_target(test_df)

    logging.info(f"Train samples: {len(X_train):,}, Val samples: {len(X_val):,}, Test samples: {len(X_test):,}")

    # Models candidate suite
    models = {
        "Baseline Ridge": BaselineRidgeModel(alpha=10.0),
        "Baseline Random Forest": BaselineRandomForestModel(n_estimators=100, max_depth=10),
        "Unconstrained XGBoost": UnconstrainedXGBoostModel(n_estimators=200, max_depth=6),
        "Physics-Guided XGBoost (PG-XGB)": PhysicsGuidedXGBoostModel(n_estimators=200, max_depth=6),
        "Physics-Residual Hybrid": PhysicsResidualHybridModel(n_estimators=180, max_depth=5),
    }

    results = []
    trained_models = {}

    logging.info("Step 3: Training and evaluating all model architectures...")
    for name, model_instance in models.items():
        logging.info(f"--- Training {name} ---")
        if isinstance(model_instance, (UnconstrainedXGBoostModel, PhysicsGuidedXGBoostModel, PhysicsResidualHybridModel)):
            model_instance.fit(X_train, y_train, eval_set=[(X_val, y_val)])
        else:
            model_instance.fit(X_train, y_train)

        metrics = evaluate_model_performance(model_instance, X_test, y_test, name)
        results.append(metrics)
        trained_models[name] = model_instance
        logging.info(
            f"[{name}] Test R²: {metrics['r2_score']:.4f} | "
            f"RMSE: {metrics['rmse_celsius']:.3f}°C | "
            f"MAE: {metrics['mae_celsius']:.3f}°C | "
            f"Phys Violation Rate: {metrics['physics_violation_rate_pct']:.1f}%"
        )

    # Convert results to DataFrame
    comparison_df = pd.DataFrame([
        {
            "Model": r["model_name"],
            "R² Score": r["r2_score"],
            "RMSE (°C)": r["rmse_celsius"],
            "MAE (°C)": r["mae_celsius"],
            "MAPE (%)": r["mape_percent"],
            "Physics Violation Rate (%)": r["physics_violation_rate_pct"],
        }
        for r in results
    ])

    # Select Best Physics-Guided Model (Prioritizing high R2 with near-zero physical violation)
    pg_models = [r for r in results if "Physics" in r["model_name"]]
    best_pg_metric = max(pg_models, key=lambda x: (x["r2_score"] - 0.05 * x["physics_violation_rate_pct"]))
    best_model_name = best_pg_metric["model_name"]
    best_model = trained_models[best_model_name]

    logging.info(f"Step 4: Selected Best PG Model: {best_model_name}")

    # Save artifacts
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    best_model_path = ARTIFACTS_DIR / "best_pg_model.joblib"
    joblib.dump(best_model, best_model_path)

    comparison_path = ARTIFACTS_DIR / "model_comparison.csv"
    comparison_df.to_csv(comparison_path, index=False)

    summary_metrics = {
        "best_model_name": best_model_name,
        "test_r2": best_pg_metric["r2_score"],
        "test_rmse": best_pg_metric["rmse_celsius"],
        "test_mae": best_pg_metric["mae_celsius"],
        "physics_violation_rate": best_pg_metric["physics_violation_rate_pct"],
        "total_training_samples": len(X_train),
        "total_validation_samples": len(X_val),
        "total_test_samples": len(X_test),
        "features": ALL_FEATURES,
        "target": TARGET_VARIABLE,
        "models_summary": results,
    }

    metrics_path = ARTIFACTS_DIR / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(summary_metrics, f, indent=2)

    logging.info(f"Artifacts successfully saved to {ARTIFACTS_DIR}")
    return summary_metrics


if __name__ == "__main__":
    run_training_pipeline()
