"""
Physics Engine for Urban Heat Modeling and Surface Energy Balance (SEB) Computations.
Enforces thermodynamic plausibility, energy conservation, and monotonic physical bounds.
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Union, Optional
from model.config import (
    STEFAN_BOLTZMANN,
    AIR_DENSITY,
    AIR_SPECIFIC_HEAT,
    MONOTONIC_CONSTRAINTS,
    ALL_FEATURES
)


class SurfaceEnergyBalance:
    """
    Computes diagnostic surface energy balance components:
        R_n = H + LE + G
    where:
        R_n: Net all-wave radiation (W/m^2)
        H: Sensible heat flux to atmosphere (W/m^2)
        LE: Latent heat flux via evapotranspiration (W/m^2)
        G: Ground/substrate conductive heat storage (W/m^2)
    """

    @staticmethod
    def compute_net_radiation(
        solar_radiation: np.ndarray,
        albedo: np.ndarray,
        temp_air_k: np.ndarray,
        temp_surface_k: np.ndarray,
        emissivity: float = 0.96,
    ) -> np.ndarray:
        """
        Calculates Net Radiation (R_n):
        R_n = (1 - albedo) * S_down + epsilon * L_down - epsilon * sigma * T_s^4
        where L_down is estimated from air temperature via Swinbank's / Brutsaert's formulation.
        """
        # Shortwave net
        sw_net = (1.0 - np.clip(albedo, 0.05, 0.85)) * np.maximum(solar_radiation, 0.0)

        # Longwave incoming approximation: L_down ~ 0.85 * sigma * T_air^4
        lw_in = 0.85 * STEFAN_BOLTZMANN * (temp_air_k ** 4)

        # Longwave outgoing: L_out = epsilon * sigma * T_surf^4
        lw_out = emissivity * STEFAN_BOLTZMANN * (temp_surface_k ** 4)

        r_net = sw_net + lw_in - lw_out
        return r_net

    @staticmethod
    def compute_latent_heat_flux(
        ndvi: np.ndarray,
        r_net: np.ndarray,
        vpd: np.ndarray,
        wind_speed: np.ndarray,
    ) -> np.ndarray:
        """
        Estimates Latent Heat Flux (LE) representing evaporative/transpirative cooling.
        Vegetated surfaces (high NDVI) with adequate solar radiation convert energy into latent heat.
        """
        # Vegetation fraction from NDVI: FVC = ((NDVI - NDVI_min) / (NDVI_max - NDVI_min))^2
        ndvi_clamped = np.clip(ndvi, 0.0, 0.9)
        fvc = np.clip((ndvi_clamped - 0.05) / 0.75, 0.0, 1.0) ** 2

        # Evaporative fraction increases with vegetation and moderate VPD
        evap_fraction = 0.65 * fvc / (1.0 + 0.3 * np.clip(vpd, 0.1, 5.0))
        le = evap_fraction * np.maximum(r_net, 0.0)
        return le

    @staticmethod
    def compute_ground_heat_flux(
        ndbi: np.ndarray,
        building_fraction: np.ndarray,
        r_net: np.ndarray,
    ) -> np.ndarray:
        """
        Estimates Ground Heat Storage Flux (G).
        Dense urban surfaces (high NDBI / concrete) absorb significant solar energy as conductive storage.
        """
        # Concrete/impervious surfaces have G/Rn ~ 0.35 - 0.50, whereas green areas have G/Rn ~ 0.10 - 0.20
        urban_impervious = np.clip((ndbi + 0.3) / 0.8, 0.1, 0.9)
        g_fraction = 0.10 + 0.35 * urban_impervious + 0.10 * np.clip(building_fraction / 100.0, 0.0, 1.0)
        g = np.clip(g_fraction, 0.10, 0.55) * r_net
        return g

    @staticmethod
    def compute_sensible_heat_flux(
        temp_surface_k: np.ndarray,
        temp_air_k: np.ndarray,
        wind_speed: np.ndarray,
        roughness_length: np.ndarray = 0.5,
    ) -> np.ndarray:
        """
        Estimates Sensible Heat Flux (H) via aerodynamic bulk transfer:
        H = rho * c_p * (T_s - T_a) / r_ah
        """
        # Aerodynamic resistance r_ah (s/m) ~ ln(z_m/z_0)^2 / (k^2 * u)
        u_adj = np.maximum(wind_speed, 0.5)
        # Simplified bulk aerodynamic conductance
        g_ah = 0.005 + 0.003 * u_adj
        h = AIR_DENSITY * AIR_SPECIFIC_HEAT * g_ah * (temp_surface_k - temp_air_k)
        return h

    @classmethod
    def estimate_radiative_prior_lst(
        cls,
        temp_air_c: np.ndarray,
        solar_rad: np.ndarray,
        albedo: np.ndarray,
        ndvi: np.ndarray,
        ndbi: np.ndarray,
        wind_speed: np.ndarray,
    ) -> np.ndarray:
        """
        Calculates a physical prior for Land Surface Temperature (LST in deg C)
        based on linearized surface energy equilibrium before non-linear urban morphology residual.
        """
        temp_air_k = temp_air_c + 273.15
        absorbed_solar = (1.0 - np.clip(albedo, 0.05, 0.85)) * np.maximum(solar_rad, 0.0)

        # Vegetation cooling factor
        veg_cooling = 4.5 * np.clip(ndvi, 0.0, 0.9)

        # Impervious heating factor
        built_heating = 3.8 * np.clip((ndbi + 0.2) / 0.8, 0.0, 1.0)

        # Convective wind cooling parameter
        wind_cooling = 1.2 * np.sqrt(np.maximum(wind_speed, 0.2))

        # Solar heating delta ~ absorbed_solar / (radiative_conductance + aerodynamic_conductance)
        solar_delta = (absorbed_solar * 0.018) / (1.0 + 0.15 * wind_cooling)

        prior_lst_c = temp_air_c + solar_delta + built_heating - veg_cooling
        return prior_lst_c


def get_monotonic_constraints_tuple(feature_names: list) -> tuple:
    """
    Returns a tuple of monotonic constraints corresponding to feature order
    for XGBoost / LightGBM.
    """
    return tuple(MONOTONIC_CONSTRAINTS.get(feat, 0) for feat in feature_names)


def compute_physical_violation_rate(
    model,
    X_test: pd.DataFrame,
    features_to_check: Optional[list] = None,
    delta: float = 0.05,
) -> Dict[str, float]:
    """
    Evaluates how often model predictions violate physical laws.
    For instance:
      - Increasing NDVI should decrease or maintain LST (dLST/dNDVI <= 0).
      - Increasing Albedo should decrease or maintain LST (dLST/dAlbedo <= 0).
      - Increasing NDBI should increase or maintain LST (dLST/dNDBI >= 0).
      - Increasing Air Temp should increase or maintain LST (dLST/dTemp >= 0).

    Returns:
        Dict mapping checked feature -> violation percentage (0.0% to 100.0%).
    """
    if features_to_check is None:
        features_to_check = ["ndvi", "albedo", "ndbi", "temp_2m", "solar_radiation"]

    violations: Dict[str, float] = {}
    base_preds = model.predict(X_test)

    for feat in features_to_check:
        if feat not in X_test.columns:
            continue

        direction = MONOTONIC_CONSTRAINTS.get(feat, 0)
        if direction == 0:
            continue

        X_perturbed = X_test.copy()
        X_perturbed[feat] = X_perturbed[feat] + delta
        pert_preds = model.predict(X_perturbed)

        diff = pert_preds - base_preds

        if direction == -1:
            # Expected diff <= 0. Violation occurs if diff > +1e-4
            violation_count = np.sum(diff > 1e-4)
        elif direction == 1:
            # Expected diff >= 0. Violation occurs if diff < -1e-4
            violation_count = np.sum(diff < -1e-4)
        else:
            violation_count = 0

        violation_rate = (violation_count / len(X_test)) * 100.0
        violations[feat] = round(float(violation_rate), 2)

    violations["overall_mean_violation_pct"] = round(
        float(np.mean(list(violations.values()))), 2
    )
    return violations
