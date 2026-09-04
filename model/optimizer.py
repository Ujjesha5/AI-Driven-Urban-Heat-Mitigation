"""
Urban Cooling Intervention Optimizer & Scenario Simulator.
Evaluates ML-driven cooling efficacy for urban heat mitigation strategies
(Tree Canopy, Cool Roofs, Green Roofs, Urban Water Bodies) and solves
budget-constrained spatial allocation problems.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import joblib
import numpy as np
import pandas as pd

from model.config import (
    ALL_FEATURES,
    ARTIFACTS_DIR,
    LAT_MAX,
    LAT_MIN,
    LON_MAX,
    LON_MIN,
)
from model.dataset_builder import MultiSourceGeospatialFusion

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


INTERVENTION_SPECIFICATIONS = {
    "Tree canopy increase": {
        "description": "Urban afforestation & street tree planting. Boosts evapotranspiration and solar shading.",
        "delta_ndvi": 0.32,
        "delta_albedo": 0.04,
        "delta_ndbi": -0.15,
        "unit_cost_range": (8.0, 18.0),
    },
    "Cool roofs (albedo change)": {
        "description": "High-reflectance solar reflective coating on building roofs. Reflects shortwave radiation.",
        "delta_ndvi": 0.0,
        "delta_albedo": 0.45,
        "delta_ndbi": -0.05,
        "unit_cost_range": (4.0, 10.0),
    },
    "Green roofs": {
        "description": "Vegetated rooftop infrastructure combining thermal insulation and vegetative cooling.",
        "delta_ndvi": 0.22,
        "delta_albedo": 0.12,
        "delta_ndbi": -0.10,
        "unit_cost_range": (12.0, 26.0),
    },
    "Water body / Wetland creation": {
        "description": "Urban retention ponds, bioswales, and wetland restoration. Provides evaporative cooling.",
        "delta_ndvi": 0.10,
        "delta_albedo": -0.02,
        "delta_ndbi": -0.25,
        "delta_mndwi": 0.45,
        "unit_cost_range": (15.0, 32.0),
    },
}


class InterventionSimulator:
    """Simulates the physical and ML-predicted cooling effect of specific interventions."""

    def __init__(self, model_path: Optional[Path] = None):
        if model_path is None:
            model_path = ARTIFACTS_DIR / "best_pg_model.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Model artifact not found at {model_path}. Run train.py first.")
        self.model = joblib.load(model_path)

    def simulate_grid_intervention(
        self,
        base_features: pd.DataFrame,
        intervention_type: str,
        coverage_pct: float = 50.0,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Simulates cooling effect across a spatial feature matrix.
        Returns:
            (before_lst, after_lst, difference_delta_lst)
        """
        if intervention_type not in INTERVENTION_SPECIFICATIONS:
            intervention_type = "Tree canopy increase"

        spec = INTERVENTION_SPECIFICATIONS[intervention_type]
        scale = np.clip(coverage_pct / 100.0, 0.0, 1.0)

        # Filter to model features
        feature_cols = [c for c in ALL_FEATURES if c in base_features.columns]
        base_input = base_features[feature_cols].copy()

        # Baseline prediction
        before_lst = self.model.predict(base_input)

        # Modified features
        mod_features = base_input.copy()
        if "delta_ndvi" in spec and "ndvi" in mod_features.columns:
            mod_features["ndvi"] = np.clip(mod_features["ndvi"] + spec["delta_ndvi"] * scale, 0.0, 0.95)
        if "delta_albedo" in spec and "albedo" in mod_features.columns:
            mod_features["albedo"] = np.clip(mod_features["albedo"] + spec["delta_albedo"] * scale, 0.05, 0.85)
        if "delta_ndbi" in spec and "ndbi" in mod_features.columns:
            mod_features["ndbi"] = np.clip(mod_features["ndbi"] + spec["delta_ndbi"] * scale, -0.6, 0.7)
        if "delta_mndwi" in spec and "mndwi" in mod_features.columns:
            mod_features["mndwi"] = np.clip(mod_features["mndwi"] + spec["delta_mndwi"] * scale, -0.8, 0.9)

        after_lst = self.model.predict(mod_features)
        difference = after_lst - before_lst  # Negative means cooling
        return before_lst, after_lst, difference


class UrbanHeatOptimizer:
    """Generates candidate intervention sites, evaluates cooling per cost, and solves budget allocation."""

    def __init__(self, model_path: Optional[Path] = None):
        self.simulator = InterventionSimulator(model_path=model_path)

    def generate_candidate_sites(
        self,
        n_sites: int = 40,
        random_seed: int = 42,
    ) -> pd.DataFrame:
        """
        Generates realistic candidate intervention sites across key hotspot areas in Mumbai MMR.
        """
        rng = np.random.default_rng(random_seed)

        # Key geographic neighborhood anchors across MMR
        zones = [
            ("BKC Commercial Hub", 72.868, 19.065, "High density corporate district"),
            ("Dharavi / Sion", 72.855, 19.040, "Dense residential settlement"),
            ("Andheri East Industrial", 72.869, 19.115, "Industrial & logistics corridor"),
            ("Kurla Station Ward", 72.879, 19.070, "Dense transit node"),
            ("Thane Wagle Estate", 72.950, 19.185, "Industrial manufacturing area"),
            ("Kalyan-Dombivli Hub", 73.080, 19.220, "Rapidly urbanizing satellite center"),
            ("Vasai East Zone", 72.835, 19.375, "Low-albedo industrial pocket"),
            ("Navi Mumbai MIDC", 73.020, 19.095, "Chemical/industrial zone"),
            ("Malad West Link Rd", 72.835, 19.180, "Commercial corridor"),
            ("Ghatkopar Industrial", 72.910, 19.085, "High-density concrete cluster"),
        ]

        candidates = []
        intervention_types = list(INTERVENTION_SPECIFICATIONS.keys())

        site_idx = 1
        for zone_name, base_lon, base_lat, zone_desc in zones:
            # 4 sites per zone
            for _ in range(n_sites // len(zones)):
                site_id = f"SITE-{site_idx:03d}"
                lon = float(base_lon + rng.normal(0, 0.012))
                lat = float(base_lat + rng.normal(0, 0.012))
                intervention = str(rng.choice(intervention_types))
                spec = INTERVENTION_SPECIFICATIONS[intervention]

                # Base synthetic feature vector for this site
                feat = {
                    "lon": lon,
                    "lat": lat,
                    "ndvi": float(rng.uniform(0.08, 0.22)),
                    "ndbi": float(rng.uniform(0.25, 0.58)),
                    "albedo": float(rng.uniform(0.10, 0.16)),
                    "mndwi": float(rng.uniform(-0.45, -0.15)),
                    "dem": float(rng.uniform(8.0, 35.0)),
                    "slope": float(rng.uniform(1.0, 6.0)),
                    "sky_view_factor": float(rng.uniform(0.40, 0.70)),
                    "building_height": float(rng.uniform(15.0, 45.0)),
                    "building_fraction": float(rng.uniform(45.0, 85.0)),
                    "roughness_length": float(rng.uniform(0.8, 2.2)),
                    "temp_2m": 33.5,
                    "dewpoint_2m": 26.5,
                    "wind_speed_10m": 3.0,
                    "solar_radiation": 750.0,
                    "vapor_pressure_deficit": 2.1,
                    "dist_to_coast": float(np.maximum(0.5, (lon - 72.79) * 105.0)),
                    "dist_to_water": float(rng.uniform(0.8, 4.5)),
                    "dist_to_greenspace": float(rng.uniform(1.2, 5.0)),
                }

                feat_df = pd.DataFrame([feat])
                before, after, diff = self.simulator.simulate_grid_intervention(
                    feat_df, intervention, coverage_pct=60.0
                )

                predicted_reduction = float(np.round(-diff[0], 2))  # Positive cooling in deg C
                c_min, c_max = spec["unit_cost_range"]
                cost = float(np.round(rng.uniform(c_min, c_max), 1))

                efficiency = round(predicted_reduction / cost, 3)

                candidates.append({
                    "site_id": site_id,
                    "zone": zone_name,
                    "description": zone_desc,
                    "lat": round(lat, 5),
                    "lon": round(lon, 5),
                    "intervention": intervention,
                    "baseline_lst_c": round(float(before[0]), 2),
                    "post_intervention_lst_c": round(float(after[0]), 2),
                    "predicted_reduction_c": max(0.2, predicted_reduction),
                    "cost": cost,
                    "cooling_per_cost_ratio": efficiency,
                })
                site_idx += 1

        df = pd.DataFrame(candidates)
        return df

    @staticmethod
    def solve_budget_allocation(
        candidate_df: pd.DataFrame,
        budget: float,
        selected_interventions: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, float]:
        """
        Ranks candidate sites by cooling efficiency (predicted cooling / cost)
        and greedily selects the optimal portfolio within budget constraints.
        """
        filtered = candidate_df.copy()
        if selected_interventions:
            filtered = filtered[filtered["intervention"].isin(selected_interventions)]

        if filtered.empty:
            return pd.DataFrame(), 0.0

        scored = filtered.sort_values("cooling_per_cost_ratio", ascending=False)

        selected_rows = []
        spent = 0.0

        for _, row in scored.iterrows():
            if spent + row["cost"] <= budget:
                selected_rows.append(row)
                spent += row["cost"]

        chosen_df = pd.DataFrame(selected_rows)
        return chosen_df, round(spent, 1)

    def generate_and_save_candidate_portfolio(self) -> pd.DataFrame:
        """Builds and serializes the candidate portfolio for the dashboard."""
        logging.info("Generating candidate intervention sites and computing ML cooling scores...")
        candidates = self.generate_candidate_sites(n_sites=40)
        out_path = ARTIFACTS_DIR / "candidate_intervention_sites.csv"
        candidates.to_csv(out_path, index=False)
        logging.info(f"Candidate intervention sites saved to {out_path}")
        return candidates


def run_optimizer_pipeline():
    opt = UrbanHeatOptimizer()
    return opt.generate_and_save_candidate_portfolio()


if __name__ == "__main__":
    run_optimizer_pipeline()
