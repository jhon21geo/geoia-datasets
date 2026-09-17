"""Procesamiento de abundancias espectrales SWIR/VNIR.

La tesis trabaja con scores minerales (Ausspec), no con espectros crudos.
Este módulo filtra minerales no informativos, resume ensambles y opcionalmente
reconstruye un espectro SWIR sintético en las bandas diagnósticas.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from alteration_ml.constants import DIAGNOSTIC_WAVELENGTHS_NM, SPECTRAL_MINERALS, VNIR_MINERALS


def drop_zero_mean_minerals(frame: pd.DataFrame, minerals: list[str] | None = None) -> list[str]:
    minerals = minerals or list(SPECTRAL_MINERALS)
    means = frame[minerals].mean()
    return means[means > 0].index.tolist()


def dominant_mineral(frame: pd.DataFrame, minerals: list[str] | None = None) -> pd.Series:
    minerals = minerals or list(SPECTRAL_MINERALS)
    return frame[minerals].idxmax(axis=1)


def assemblage_flags(frame: pd.DataFrame) -> pd.DataFrame:
    """Indicadores binarios de ensambles usados en la asignación de dominios."""
    out = pd.DataFrame(index=frame.index)
    out["ensamble_argavd"] = (frame["Pyrophyllite"] + frame["Alunite"]) > 40
    out["ensamble_fil"] = (frame["WhiteMica"] > 30) & (frame["Alunite"] < 20)
    out["ensamble_arg"] = (frame["Kaolinite"] > 25) & (frame["WhiteMica"] > 8)
    out["ensamble_pro"] = (frame["Chlorite"] + frame["Montmor"] + frame["Carbonate"]) > 25
    out["ensamble_sk"] = (
        (frame["Chlorite"] > 8)
        & (frame["WhiteMica"] > 8)
        & (frame["Kaolinite"] > 5)
        & (frame["Montmor"] > 5)
    )
    hematite = frame["Hematite"] if "Hematite" in frame.columns else 0
    goethite = frame["Goethite"] if "Goethite" in frame.columns else 0
    out["ensamble_oxd"] = (hematite + goethite) > 25
    return out


def synthetic_swir_curve(mineral_row: pd.Series, wavelengths: np.ndarray | None = None) -> pd.DataFrame:
    """Reconstruye una curva SWIR 1300–2500 nm a partir de scores minerales.

    Cada mineral aporta un valle gaussiano en sus longitudes diagnósticas,
    ponderado por su abundancia relativa. Útil para visualizar, no para
    sustituir un espectro ASD real.
    """
    if wavelengths is None:
        wavelengths = np.arange(1300, 2501, 2)
    reflectance = np.full(wavelengths.shape, 0.55, dtype=float)
    total = max(float(mineral_row[list(SPECTRAL_MINERALS)].sum()), 1.0)
    mineral_to_key = {
        "Alunite": "Alunite",
        "Pyrophyllite": "Pyrophyllite",
        "Kaolinite": "Kaolinite",
        "WhiteMica": "Illite",
        "Chlorite": "Chlorite",
        "Epidote": "Epidote",
        "Dickite": "Kaolinite",
    }
    for mineral, key in mineral_to_key.items():
        weight = float(mineral_row.get(mineral, 0.0)) / total
        if weight < 0.02:
            continue
        for center in DIAGNOSTIC_WAVELENGTHS_NM[key]:
            reflectance -= weight * 0.22 * np.exp(-0.5 * ((wavelengths - center) / 18.0) ** 2)
    reflectance = np.clip(reflectance, 0.08, 0.85)
    return pd.DataFrame({"wavelength_nm": wavelengths, "reflectance": reflectance})


def spectral_summary(frame: pd.DataFrame) -> pd.DataFrame:
    minerals = [m for m in SPECTRAL_MINERALS if m in frame.columns]
    stats = frame[minerals].agg(["count", "mean", "median", "std", "min", "max"]).T
    stats.index.name = "mineral"
    return stats.reset_index()
