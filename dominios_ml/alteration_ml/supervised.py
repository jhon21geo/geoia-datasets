"""Clasificadores supervisados del flujo metodológico.

Entrena Random Forest, k-NN, red neuronal (MLP) y SVM sobre geoquímica
estandarizada para predecir MOD_ALT. Los hiperparámetros por defecto
siguen las Tablas 19–22, con un perfil `robust` opcional.
"""

from __future__ import annotations

from dataclasses import dataclass
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC

from alteration_ml.constants import ROBUST_HYPERPARAMS, TARGET_COLUMN, THESIS_HYPERPARAMS


MODEL_BUILDERS = {
    "random_forest": lambda p: RandomForestClassifier(**p),
    "knn": lambda p: KNeighborsClassifier(**p),
    "neural_network": lambda p: MLPClassifier(**p),
    "svm": lambda p: SVC(**p),
}


@dataclass
class SplitData:
    X_train: np.ndarray
    X_test: np.ndarray
    y_train: pd.Series
    y_test: pd.Series


def split_labeled(
    frame: pd.DataFrame,
    feature_cols: list[str],
    test_size: float = 0.20,
    random_state: int = 42,
) -> SplitData:
    labeled = frame[frame.get("labeled", True) == True] if "labeled" in frame.columns else frame  # noqa: E712
    X = labeled[feature_cols].to_numpy()
    y = labeled[TARGET_COLUMN]
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )
    return SplitData(X_train, X_test, y_train, y_test)


def hyperparams_for(profile: str = "thesis") -> dict[str, dict]:
    if profile == "robust":
        return ROBUST_HYPERPARAMS
    if profile == "thesis":
        return THESIS_HYPERPARAMS
    raise ValueError("profile debe ser 'thesis' o 'robust'")


def train_models(split: SplitData, profile: str = "thesis") -> dict:
    params = hyperparams_for(profile)
    fitted = {}
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        for name, builder in MODEL_BUILDERS.items():
            model = builder(params[name])
            model.fit(split.X_train, split.y_train)
            fitted[name] = model
    return fitted


def predict_frame(model, frame: pd.DataFrame, feature_cols: list[str], prefix: str) -> pd.DataFrame:
    out = frame.copy()
    features = frame[feature_cols].to_numpy()
    out[f"{prefix}_pred"] = model.predict(features)
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(features)
        for i, cls in enumerate(model.classes_):
            out[f"{prefix}_p_{cls}"] = proba[:, i]
    return out
