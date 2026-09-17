"""Preprocesamiento geoquímico y espectral.

Replica el protocolo de la sección 3.10: umbral de completitud, imputación
por mediana de sondaje, recorte al percentil 99 y estandarización Z-score.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from alteration_ml.constants import CHEMICAL_COLUMNS, SPECTRAL_MINERALS, VNIR_MINERALS


def completeness(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    return 1.0 - frame[columns].isna().mean()


def drop_sparse_columns(frame: pd.DataFrame, columns: list[str], threshold: float = 0.80) -> list[str]:
    """Retiene variables con completitud >= umbral (80 % en la tesis)."""
    rates = completeness(frame, columns)
    return rates[rates >= threshold].index.tolist()


def impute_median_by_hole(frame: pd.DataFrame, columns: list[str], hole_col: str = "holeid") -> pd.DataFrame:
    """Imputa nulos con la mediana del sondaje y, si falta, la mediana global."""
    out = frame.copy()
    for col in columns:
        hole_median = out.groupby(hole_col)[col].transform("median")
        out[col] = out[col].fillna(hole_median)
        out[col] = out[col].fillna(out[col].median())
    return out


def clip_percentile(frame: pd.DataFrame, columns: list[str], q: float = 0.99) -> pd.DataFrame:
    """Acota colas erráticas al percentil q, sin eliminar filas."""
    out = frame.copy()
    for col in columns:
        upper = out[col].quantile(q)
        out[col] = out[col].clip(upper=upper)
    return out


def zscore_scale(frame: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, StandardScaler]:
    scaler = StandardScaler()
    scaled = scaler.fit_transform(frame[columns])
    out = frame.copy()
    out[[f"{c}__z" for c in columns]] = scaled
    return out, scaler


def prepare_feature_matrix(
    frame: pd.DataFrame,
    feature_kind: str = "chemistry",
    completeness_threshold: float = 0.80,
) -> tuple[pd.DataFrame, list[str], StandardScaler]:
    """Devuelve el dataframe imputado/escalado y la lista de columnas Z-score."""
    if feature_kind == "chemistry":
        candidates = [c for c in CHEMICAL_COLUMNS if c in frame.columns]
    elif feature_kind == "spectral":
        candidates = [c for c in list(SPECTRAL_MINERALS) + list(VNIR_MINERALS) if c in frame.columns]
    else:
        raise ValueError("feature_kind debe ser 'chemistry' o 'spectral'")

    kept = drop_sparse_columns(frame, candidates, threshold=completeness_threshold)
    cleaned = impute_median_by_hole(frame, kept)
    cleaned = clip_percentile(cleaned, kept, q=0.99)
    scaled, scaler = zscore_scale(cleaned, kept)
    z_cols = [f"{c}__z" for c in kept]
    return scaled, z_cols, scaler
