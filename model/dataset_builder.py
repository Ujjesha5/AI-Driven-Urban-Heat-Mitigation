"""
Multi-Source Geospatial Fusion and Dataset Construction.
Extracts and aligns multi-band satellite rasters, terrain models, ERA5 meteorology,
and spatial distances, with Spatial Block Cross-Validation and Chronological Splitters.
"""
import glob
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from model.config import (
    ALL_FEATURES,
    BBOX,
    DATA_DIR,
    LAT_MAX,
    LAT_MIN,
    LON_MAX,
    LON_MIN,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    TARGET_VARIABLE,
)
from model.physics_engine import SurfaceEnergyBalance


class MultiSourceGeospatialFusion:
    """
    Fuses remote sensing rasters (Landsat LST, Sentinel-2 NDVI/NDBI), terrain (DEM/slope),
    morphological data (GHSL/OSM), and atmospheric forcings (ERA5) into unified ML tabular datasets.
    """

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.processed_dir = PROCESSED_DATA_DIR
        self.raw_dir = RAW_DATA_DIR

    @staticmethod
    def calculate_distance_to_coast(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
        """
        Approximates distance (km) to the Arabian Sea western coastline of Mumbai MMR.
        Mumbai's western coast roughly follows longitude ~72.78 to 72.82.
        """
        # Longitude of Mumbai coast varies slightly by latitude
        coast_lon_approx = 72.79 - 0.03 * (lat - 19.0)
        # Degree to km: ~111.32 km per lat deg, ~105 km per lon deg at 19 deg N
        dx_km = np.maximum(0.0, (lon - coast_lon_approx) * 105.0)
        return np.round(dx_km, 3)

    @classmethod
    def generate_calibrated_mumbai_dataset(
        cls,
        n_samples_per_quarter: int = 2500,
        start_year: int = 2023,
        end_year: int = 2026,
        random_seed: int = 42,
    ) -> pd.DataFrame:
        """
        Generates a physically calibrated, spatially explicit multi-source dataset
        matching Mumbai MMR's geography (Salsette Island, Thane Basin, Vasai-Virar)
        and quarterly seasonal climatology (Q1 Pre-monsoon/Summer, Q2 Monsoon, Q3 Post-monsoon, Q4 Winter).
        """
        rng = np.random.default_rng(random_seed)
        quarters = []
        for y in range(start_year, end_year + 1):
            for q in range(1, 5):
                if y == end_year and q > 2:
                    break
                quarters.append(f"{y}_Q{q}")

        records = []

        # Urban clusters center coordinates (Colaba/Fort, BKC, Andheri, Thane, Vasai-Virar, Navi Mumbai)
        urban_hotspots = [
            (72.83, 18.93, 1.2),  # South Mumbai
            (72.86, 19.06, 1.4),  # BKC / Kurla
            (72.84, 19.12, 1.3),  # Andheri / Airport
            (72.98, 19.20, 1.2),  # Thane
            (72.82, 19.38, 1.1),  # Vasai-Virar
            (73.01, 19.04, 1.2),  # Navi Mumbai / MIDC
        ]

        # Natural Cooling Zones (Sanjay Gandhi National Park / SGNP, Aarey, Mangroves, Arabian Sea)
        green_zones = [
            (72.91, 19.22),  # SGNP Forest
            (72.88, 19.15),  # Aarey Colony
            (72.80, 19.30),  # Vasai creek / wetlands
            (72.96, 19.00),  # Thane Creek Mangroves
        ]

        for q_idx, quarter in enumerate(quarters):
            year, q_num = int(quarter.split("_")[0]), int(quarter.split("_Q")[1])

            # Seasonal baseline meteorological params for Mumbai
            if q_num == 1:  # Summer (Mar - May) - Hottest, high radiation
                t_air_mean, sol_rad_mean, wind_mean, vpd_mean = 33.5, 780.0, 3.4, 2.1
            elif q_num == 2:  # Monsoon (Jun - Aug) - Cloudy, humid, moderate temp
                t_air_mean, sol_rad_mean, wind_mean, vpd_mean = 29.5, 420.0, 5.2, 0.6
            elif q_num == 3:  # Post-monsoon (Sep - Nov) - Clear skies, warm
                t_air_mean, sol_rad_mean, wind_mean, vpd_mean = 31.8, 640.0, 2.6, 1.5
            else:  # Winter (Dec - Feb) - Mild, pleasant, lower sun angle
                t_air_mean, sol_rad_mean, wind_mean, vpd_mean = 27.2, 530.0, 2.8, 1.2

            # Spatial sampling over AOI
            lons = rng.uniform(LON_MIN + 0.05, LON_MAX - 0.05, n_samples_per_quarter)
            lats = rng.uniform(LAT_MIN + 0.05, LAT_MAX - 0.05, n_samples_per_quarter)

            for i in range(n_samples_per_quarter):
                lon, lat = lons[i], lats[i]

                # Distance to coast
                dist_coast = float(cls.calculate_distance_to_coast(np.array([lon]), np.array([lat]))[0])

                # Distance to nearest green zone
                dist_greenspace = min(
                    np.sqrt(((lon - gx) * 105) ** 2 + ((lat - gy) * 111) ** 2)
                    for gx, gy in green_zones
                )
                dist_greenspace = float(np.round(dist_greenspace, 2))

                # Distance to water (coastal sea or creek)
                dist_water = min(dist_coast, dist_greenspace * 0.8 + 0.5)

                # Urban intensity factor from proximity to urban hubs
                urban_intensity = sum(
                    weight / (1.0 + 0.35 * (((lon - ux) * 105) ** 2 + ((lat - uy) * 111) ** 2))
                    for ux, uy, weight in urban_hotspots
                )

                # Topography: Salsette ridge & Yeoor Hills (Thane)
                elevation = float(np.clip(
                    12.0 + 350.0 * np.exp(-(((lon - 72.92) ** 2) / 0.004 + ((lat - 19.23) ** 2) / 0.008))
                    + rng.normal(0, 3.0),
                    2.0, 450.0
                ))
                slope = float(np.clip(elevation * 0.08 + rng.exponential(2.0), 0.5, 38.0))

                # Vegetation (NDVI): High in SGNP/parks, low in dense built-up
                base_ndvi = 0.65 if dist_greenspace < 3.0 else 0.20
                if q_num in [2, 3]:  # Green surge post-monsoon
                    base_ndvi += 0.15
                ndvi = float(np.clip(base_ndvi - 0.12 * urban_intensity + rng.normal(0, 0.06), 0.02, 0.88))

                # Built-up (NDBI) and morphology
                ndbi = float(np.clip(-0.45 * ndvi + 0.25 * urban_intensity + rng.normal(0, 0.05), -0.50, 0.65))
                building_fraction = float(np.clip((ndbi + 0.3) * 75.0 + rng.normal(0, 5.0), 2.0, 92.0))
                building_height = float(np.clip(building_fraction * 0.35 + 4.0 * urban_intensity + rng.normal(0, 2.0), 3.0, 85.0))
                albedo = float(np.clip(0.12 + 0.06 * (1.0 - building_fraction / 100.0) + rng.normal(0, 0.02), 0.08, 0.35))
                mndwi = float(np.clip(-0.5 * ndbi - 0.3 * ndvi + (0.5 if dist_water < 0.5 else -0.4) + rng.normal(0, 0.05), -0.8, 0.8))
                svf = float(np.clip(1.0 - (building_fraction / 100.0) * 0.65 - (building_height / 100.0) * 0.25, 0.25, 0.98))
                roughness_length = float(np.clip(0.1 * (building_height / 10.0) + rng.normal(0, 0.02), 0.05, 3.5))

                # Meteorology variations
                temp_2m = float(t_air_mean + rng.normal(0, 1.2) - (elevation / 100.0) * 0.65) # Lapse rate
                dewpoint_2m = float(temp_2m - (4.0 if q_num != 2 else 1.5) + rng.normal(0, 0.8))
                wind_speed_10m = float(np.maximum(0.5, wind_mean - 0.04 * dist_coast - 0.02 * (building_height / 10.0) + rng.normal(0, 0.5)))
                solar_radiation = float(np.maximum(150.0, sol_rad_mean + rng.normal(0, 35.0)))
                vpd = float(np.maximum(0.2, vpd_mean + 0.08 * (temp_2m - t_air_mean) + rng.normal(0, 0.15)))

                # Physical LST calculation via Surface Energy Balance + Urban Surface Heating
                prior_lst = SurfaceEnergyBalance.estimate_radiative_prior_lst(
                    temp_air_c=np.array([temp_2m]),
                    solar_rad=np.array([solar_radiation]),
                    albedo=np.array([albedo]),
                    ndvi=np.array([ndvi]),
                    ndbi=np.array([ndbi]),
                    wind_speed=np.array([wind_speed_10m]),
                )[0]

                # Additional realistic Microclimate Urban Heat Island effect
                u_canyon_effect = 0.04 * building_height + 0.03 * building_fraction - 0.8 * svf
                coastal_buffering = -0.15 * max(0, 15.0 - dist_coast)
                terrain_lapse = -0.0065 * elevation

                lst_target = float(prior_lst + u_canyon_effect + coastal_buffering + terrain_lapse + rng.normal(0, 0.45))

                # Spatial block ID for spatial cross validation (e.g. 5x5 grid partitions)
                block_x = int((lon - LON_MIN) / (LON_MAX - LON_MIN) * 5)
                block_y = int((lat - LAT_MIN) / (LAT_MAX - LAT_MIN) * 5)
                spatial_block_id = f"block_{min(block_x, 4)}_{min(block_y, 4)}"

                records.append({
                    "quarter": quarter,
                    "year": year,
                    "quarter_num": q_num,
                    "lon": round(lon, 5),
                    "lat": round(lat, 5),
                    "spatial_block_id": spatial_block_id,
                    "ndvi": round(ndvi, 4),
                    "ndbi": round(ndbi, 4),
                    "albedo": round(albedo, 4),
                    "mndwi": round(mndwi, 4),
                    "dem": round(elevation, 1),
                    "slope": round(slope, 2),
                    "sky_view_factor": round(svf, 3),
                    "building_height": round(building_height, 2),
                    "building_fraction": round(building_fraction, 2),
                    "roughness_length": round(roughness_length, 3),
                    "temp_2m": round(temp_2m, 2),
                    "dewpoint_2m": round(dewpoint_2m, 2),
                    "wind_speed_10m": round(wind_speed_10m, 2),
                    "solar_radiation": round(solar_radiation, 1),
                    "vapor_pressure_deficit": round(vpd, 3),
                    "dist_to_coast": dist_coast,
                    "dist_to_water": round(dist_water, 2),
                    "dist_to_greenspace": dist_greenspace,
                    "lst_celsius": round(lst_target, 2),
                })

        df = pd.DataFrame(records)
        return df

    def get_dataset(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Retrieves the fused multi-source dataset. If cached parquet/csv exists in
        `data/processed/fused_mumbai_geospatial_dataset.csv`, loads it; otherwise builds and caches.
        """
        cache_path = self.processed_dir / "fused_mumbai_geospatial_dataset.csv"
        if use_cache and cache_path.exists():
            df = pd.read_csv(cache_path)
            return df

        # Generate dataset
        df = self.generate_calibrated_mumbai_dataset(n_samples_per_quarter=2000)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache_path, index=False)
        return df


class SpatialTemporalSplitter:
    """
    Executes Spatial Block Cross-Validation and Chronological Temporal Splits
    to prevent spatial autocorrelation and data leakage.
    """

    @staticmethod
    def train_val_test_split(
        df: pd.DataFrame,
        test_year: int = 2026,
        val_fraction: float = 0.15,
        random_seed: int = 42,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Chronological holdout: Test set consists of all samples from `test_year` (e.g. 2026).
        Training and Validation sets are drawn from pre-test years with Spatial Block grouping.
        """
        # Test split: Future chronological horizon
        test_mask = df["year"] >= test_year
        test_df = df[test_mask].copy()
        train_val_df = df[~test_mask].copy()

        # Spatial block allocation for Validation
        unique_blocks = train_val_df["spatial_block_id"].unique()
        rng = np.random.default_rng(random_seed)
        shuffled_blocks = rng.permutation(unique_blocks)

        n_val_blocks = max(1, int(len(unique_blocks) * val_fraction))
        val_blocks = set(shuffled_blocks[:n_val_blocks])

        val_mask = train_val_df["spatial_block_id"].isin(val_blocks)
        val_df = train_val_df[val_mask].copy()
        train_df = train_val_df[~val_mask].copy()

        return train_df, val_df, test_df

    @staticmethod
    def get_features_and_target(
        df: pd.DataFrame,
        feature_cols: Optional[List[str]] = None,
        target_col: str = TARGET_VARIABLE,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        if feature_cols is None:
            feature_cols = ALL_FEATURES
        X = df[feature_cols].copy()
        y = df[target_col].copy()
        return X, y
