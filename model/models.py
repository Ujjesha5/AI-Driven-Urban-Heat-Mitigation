"""
Machine Learning Models for Urban Heat Mitigation.
Includes Baseline Regressors, Physics-Guided GBDT (with Monotonic Constraints),
and Hybrid Physics-Residual Estimators.
"""
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb

from model.config import ALL_FEATURES, MONOTONIC_CONSTRAINTS, ModelTrainingConfig
from model.physics_engine import SurfaceEnergyBalance, get_monotonic_constraints_tuple


class BaselineRidgeModel(BaseEstimator, RegressorMixin):
    """Standard L2 Regularized Ridge Regression Baseline."""

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.model = Pipeline([
            ("scaler", StandardScaler()),
            ("regressor", Ridge(alpha=self.alpha, random_state=42))
        ])

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.feature_names_in_ = list(X.columns)
        self.model.fit(X, y)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X)


class BaselineRandomForestModel(BaseEstimator, RegressorMixin):
    """Standard Random Forest Regressor Baseline."""

    def __init__(self, n_estimators: int = 150, max_depth: int = 12, random_state: int = 42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            n_jobs=-1,
            random_state=self.random_state
        )

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.feature_names_in_ = list(X.columns)
        self.model.fit(X, y)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X)


class UnconstrainedXGBoostModel(BaseEstimator, RegressorMixin):
    """Standard Unconstrained XGBoost Regressor."""

    def __init__(
        self,
        n_estimators: int = 250,
        learning_rate: float = 0.05,
        max_depth: int = 6,
        subsample: float = 0.85,
        colsample_bytree: float = 0.85,
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state
        self.model = None

    def fit(self, X: pd.DataFrame, y: pd.Series, eval_set: Optional[List[Tuple[pd.DataFrame, pd.Series]]] = None):
        self.feature_names_in_ = list(X.columns)
        self.model = xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            random_state=self.random_state,
            n_jobs=-1,
        )
        self.model.fit(X, y, eval_set=eval_set, verbose=False)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X)


class PhysicsGuidedXGBoostModel(BaseEstimator, RegressorMixin):
    """
    Physics-Guided XGBoost Regressor.
    Enforces thermodynamic monotonic constraints (e.g. dLST/dNDVI <= 0, dLST/dAlbedo <= 0, dLST/dNDBI >= 0)
    to prevent physically implausible artifacts.
    """

    def __init__(
        self,
        n_estimators: int = 250,
        learning_rate: float = 0.05,
        max_depth: int = 6,
        subsample: float = 0.85,
        colsample_bytree: float = 0.85,
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state
        self.model = None

    def fit(self, X: pd.DataFrame, y: pd.Series, eval_set: Optional[List[Tuple[pd.DataFrame, pd.Series]]] = None):
        self.feature_names_in_ = list(X.columns)
        # Generate monotonic constraint tuple matching feature column order
        monotone_constraints = get_monotonic_constraints_tuple(self.feature_names_in_)

        self.model = xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            monotone_constraints=monotone_constraints,
            random_state=self.random_state,
            n_jobs=-1,
        )
        self.model.fit(X, y, eval_set=eval_set, verbose=False)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X)


class PhysicsResidualHybridModel(BaseEstimator, RegressorMixin):
    """
    Hybrid Physics-Guided Residual Learning Model.
    1. Base layer: Calculates analytical Surface Energy Balance (SEB) radiative prior LST_prior.
    2. ML layer: Trains a physics-constrained GBDT on the residual delta_LST = LST_true - LST_prior.
    3. Prediction: LST_pred = LST_prior + delta_LST_pred.
    """

    def __init__(
        self,
        n_estimators: int = 200,
        learning_rate: float = 0.05,
        max_depth: int = 5,
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.random_state = random_state
        self.residual_model = None

    def _compute_prior(self, X: pd.DataFrame) -> np.ndarray:
        """Calculates SEB physical baseline."""
        return SurfaceEnergyBalance.estimate_radiative_prior_lst(
            temp_air_c=X["temp_2m"].values,
            solar_rad=X["solar_radiation"].values,
            albedo=X["albedo"].values,
            ndvi=X["ndvi"].values,
            ndbi=X["ndbi"].values,
            wind_speed=X["wind_speed_10m"].values,
        )

    def fit(self, X: pd.DataFrame, y: pd.Series, eval_set: Optional[List[Tuple[pd.DataFrame, pd.Series]]] = None):
        self.feature_names_in_ = list(X.columns)
        prior_y = self._compute_prior(X)
        residual_y = y.values - prior_y

        monotone_constraints = get_monotonic_constraints_tuple(self.feature_names_in_)

        eval_set_residual = None
        if eval_set is not None:
            eval_set_residual = []
            for X_val, y_val in eval_set:
                prior_val = self._compute_prior(X_val)
                res_val = y_val.values - prior_val
                eval_set_residual.append((X_val, res_val))

        self.residual_model = xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            monotone_constraints=monotone_constraints,
            random_state=self.random_state,
            n_jobs=-1,
        )
        self.residual_model.fit(X, residual_y, eval_set=eval_set_residual, verbose=False)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        prior = self._compute_prior(X)
        residual_pred = self.residual_model.predict(X)
        return prior + residual_pred
