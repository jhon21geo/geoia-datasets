"""Aprendizaje no supervisado: PCA, clustering jerárquico y K-Means.

El dendrograma se calcula sobre los 13 minerales (variables), como en la
tesis, para revelar ensambles. K-Means se aplica a las muestras (k=5).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

from alteration_ml.constants import SPECTRAL_MINERALS


def fit_pca(X: np.ndarray, n_components: int = 5) -> tuple[PCA, np.ndarray, np.ndarray]:
    pca = PCA(n_components=n_components, random_state=42)
    scores = pca.fit_transform(X)
    return pca, scores, pca.explained_variance_ratio_


def mineral_hierarchical_clusters(
    frame: pd.DataFrame,
    minerals: list[str] | None = None,
    n_clusters: int = 5,
    method: str = "ward",
) -> tuple[np.ndarray, pd.DataFrame]:
    """Agrupa minerales por similitud de perfil entre muestras."""
    minerals = minerals or [m for m in SPECTRAL_MINERALS if m in frame.columns]
    matrix = frame[minerals].to_numpy().T  # minerales × muestras
    z = linkage(matrix, method=method, metric="euclidean")
    labels = fcluster(z, t=n_clusters, criterion="maxclust")
    table = pd.DataFrame({"mineral": minerals, "cluster_h": labels}).sort_values("cluster_h")
    return z, table


def fit_kmeans(X: np.ndarray, n_clusters: int = 5, random_state: int = 42) -> tuple[KMeans, np.ndarray, float]:
    model = KMeans(n_clusters=n_clusters, n_init=20, random_state=random_state)
    labels = model.fit_predict(X)
    sil = float(silhouette_score(X, labels)) if len(np.unique(labels)) > 1 else 0.0
    return model, labels, sil


def cluster_mineral_profiles(frame: pd.DataFrame, cluster_col: str, minerals: list[str] | None = None) -> pd.DataFrame:
    minerals = minerals or [m for m in SPECTRAL_MINERALS if m in frame.columns]
    return frame.groupby(cluster_col)[minerals].mean().round(2)
