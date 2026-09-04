"""
Model and System Configuration for Physics-Guided Urban Heat Mitigation ML Framework.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any

# Root Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RAW_DATA_DIR = DATA_DIR / "raw"
MODEL_DIR = BASE_DIR / "model"
ARTIFACTS_DIR = MODEL_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Mumbai Metropolitan Region (MMR) AOI Coordinates (EPSG:4326)
LON_MIN, LAT_MIN, LON_MAX, LAT_MAX = 72.5833, 18.7833, 73.2000, 19.6000
BBOX = [LON_MIN, LAT_MIN, LON_MAX, LAT_MAX]
CRS_GEO = "EPSG:4326"
CRS_UTM = "EPSG:32643"  # UTM Zone 43N

# Physical Thermodynamic Constants
STEFAN_BOLTZMANN = 5.670374419e-8  # W / (m^2 * K^4)
AIR_DENSITY = 1.18                 # kg / m^3 at ~25-30 deg C
AIR_SPECIFIC_HEAT = 1005.0         # J / (kg * K)
VON_KARMAN = 0.40                  # dimensionless
WATER_LATENT_HEAT_VAP = 2.45e6     # J / kg (evaporation)
EMISSIVITY_DEFAULT = 0.96          # Surface emissivity default

# Feature Definitions
SPECTRAL_FEATURES = ["ndvi", "ndbi", "albedo", "mndwi"]
TOPOGRAPHIC_FEATURES = ["dem", "slope", "sky_view_factor"]
MORPHOLOGICAL_FEATURES = ["building_height", "building_fraction", "roughness_length"]
METEOROLOGICAL_FEATURES = ["temp_2m", "dewpoint_2m", "wind_speed_10m", "solar_radiation", "vapor_pressure_deficit"]
SPATIAL_FEATURES = ["dist_to_coast", "dist_to_water", "dist_to_greenspace"]

ALL_FEATURES = (
    SPECTRAL_FEATURES
    + TOPOGRAPHIC_FEATURES
    + MORPHOLOGICAL_FEATURES
    + METEOROLOGICAL_FEATURES
    + SPATIAL_FEATURES
)

TARGET_VARIABLE = "lst_celsius"

# Feature Display Names for XAI / Dashboard
FEATURE_LABEL_MAP: Dict[str, str] = {
    "ndvi": "NDVI (Vegetation Density)",
    "ndbi": "NDBI (Built-up Index)",
    "albedo": "Surface Albedo (Reflectance)",
    "mndwi": "MNDWI (Water Index)",
    "dem": "Elevation / DEM (m)",
    "slope": "Terrain Slope (deg)",
    "sky_view_factor": "Sky View Factor (SVF)",
    "building_height": "Building Height (m)",
    "building_fraction": "Building Footprint Density (%)",
    "roughness_length": "Surface Roughness Length (m)",
    "temp_2m": "2m Air Temperature (°C)",
    "dewpoint_2m": "2m Dewpoint Temp (°C)",
    "wind_speed_10m": "10m Wind Speed (m/s)",
    "solar_radiation": "Downwelling Solar Radiation (W/m²)",
    "vapor_pressure_deficit": "Vapor Pressure Deficit (kPa)",
    "dist_to_coast": "Distance to Coastline (km)",
    "dist_to_water": "Distance to Water Bodies (km)",
    "dist_to_greenspace": "Distance to Green Space (km)",
}

# Monotonicity constraints for Physics-Guided Tree Models:
# +1 indicates target should increase with feature, -1 indicates target should decrease with feature, 0 indicates unconstrained
MONOTONIC_CONSTRAINTS: Dict[str, int] = {
    "ndvi": -1,                # Higher vegetation -> Lower LST
    "ndbi": 1,                 # Higher impervious/built-up -> Higher LST
    "albedo": -1,              # Higher solar reflectance -> Lower LST
    "mndwi": -1,               # Higher moisture/water presence -> Lower LST
    "dem": -1,                 # Higher elevation -> Lower LST (adiabatic lapse rate)
    "slope": 0,                # Complex interaction with solar aspect
    "sky_view_factor": -1,     # Better ventilation/radiative cooling at night
    "building_height": 1,      # Higher thermal mass/canyon trapping -> Higher heat
    "building_fraction": 1,    # More dense concrete -> Higher LST
    "roughness_length": 0,     # Complex turbulence effect
    "temp_2m": 1,              # Higher air temp -> Higher LST
    "dewpoint_2m": 0,          # Mixed humidity interaction
    "wind_speed_10m": -1,      # Increased convective cooling -> Lower LST
    "solar_radiation": 1,      # Higher insolation -> Higher LST
    "vapor_pressure_deficit": 1,# High VPD -> Stomatal closure / less evaporative cooling
    "dist_to_coast": 1,        # Further inland from sea breeze -> Higher LST
    "dist_to_water": 1,        # Farther from cooling water -> Higher LST
    "dist_to_greenspace": 1,   # Farther from urban park buffer -> Higher LST
}

@dataclass
class ModelTrainingConfig:
    random_seed: int = 42
    n_spatial_blocks: int = 5
    test_size: float = 0.20
    val_size: float = 0.15
    n_estimators: int = 250
    learning_rate: float = 0.05
    max_depth: int = 6
    subsample: float = 0.85
    colsample_bytree: float = 0.85
    physics_loss_weight: float = 0.35
    early_stopping_rounds: int = 20
