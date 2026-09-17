"""Carga tablas espectrales, geoquímicas y etiquetas."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from alteration_ml.constants import TARGET_COLUMN


def load_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró {path}. Ejecuta: python -m alteration_ml.cli generate")
    return pd.read_csv(path)


def merge_spectral_chemistry(
    spectral: pd.DataFrame,
    chemistry: pd.DataFrame,
    labels: pd.DataFrame | None = None,
    on: str = "sample_id",
) -> pd.DataFrame:
    """Une espectro + química (+ etiquetas) por identificador de muestra."""
    merged = spectral.merge(chemistry, on=on, how="inner", suffixes=("", "_chem"))
    drop = [c for c in merged.columns if c.endswith("_chem")]
    merged = merged.drop(columns=drop)
    if labels is not None:
        merged = merged.merge(labels[[on, TARGET_COLUMN, "labeled"]] if "labeled" in labels.columns else labels, on=on, how="left")
    return merged
