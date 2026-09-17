"""Visor de producción: Dominios ML (SWIR + geoquímica + clasificadores)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from alteration_ml.constants import (
    CHEMICAL_COLUMNS,
    DOMAIN_ASSEMBLAGES,
    DOMAIN_COLORS,
    DOMAIN_LABELS,
    DOMAINS,
    SPECTRAL_MINERALS,
    TARGET_COLUMN,
    THESIS_HYPERPARAMS,
    VNIR_MINERALS,
)
from alteration_ml.evaluate import evaluate_model, metrics_table
from alteration_ml.preprocess import prepare_feature_matrix
from alteration_ml.supervised import split_labeled, train_models
from alteration_ml.unsupervised import fit_kmeans, fit_pca

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FRONTEND = ROOT
DATA_PATH = ROOT / "data" / "synthetic" / "synthetic_merged.csv"

app = FastAPI(
    title="GeoIA — Dominios ML",
    description="Delimitación de dominios de alteración hidrotermal con SWIR, geoquímica y machine learning.",
    version="1.0.0",
)

_STATE: dict[str, Any] = {}


def _frontend() -> Path:
    if (FRONTEND / "index.html").is_file():
        return FRONTEND
    return HERE


def _inlined_index() -> str:
    base = _frontend()
    html = (base / "index.html").read_text(encoding="utf-8")
    css = (base / "css" / "style.css").read_text(encoding="utf-8")
    js = (base / "js" / "app.js").read_text(encoding="utf-8")
    html = html.replace(
        '<link rel="stylesheet" href="css/style.css">',
        "<style>\n" + css + "\n</style>",
    )
    html = html.replace(
        '<script src="js/app.js"></script>',
        "<script>\n" + js + "\n</script>",
    )
    return html


def _index_response() -> HTMLResponse:
    return HTMLResponse(
        _inlined_index(),
        headers={"X-GeoIA-Visor": "dominios-ml", "Cache-Control": "no-store"},
    )


def _load_frame() -> pd.DataFrame:
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"No está el CSV sintético: {DATA_PATH}")
    frame = pd.read_csv(DATA_PATH)
    if "labeled" in frame.columns:
        frame["labeled"] = frame["labeled"].astype(str).str.lower().isin(("1", "true", "yes"))
    return frame


def _boot() -> dict[str, Any]:
    if _STATE:
        return _STATE

    frame = _load_frame()
    spectral_ready, spectral_z, _ = prepare_feature_matrix(frame, feature_kind="spectral")
    X_spec = spectral_ready[spectral_z].to_numpy()
    _pca, scores, var_ratio = fit_pca(X_spec, n_components=min(5, X_spec.shape[1]))
    _kmeans, clusters, silhouette = fit_kmeans(X_spec, n_clusters=5)

    work = spectral_ready.copy()
    work["pc1"] = scores[:, 0]
    work["pc2"] = scores[:, 1]
    work["cluster_k5"] = clusters

    labeled_n = int(work["labeled"].sum()) if "labeled" in work.columns else int(len(work))
    counts = (
        work.loc[work["labeled"] == True, TARGET_COLUMN].value_counts()  # noqa: E712
        if "labeled" in work.columns
        else work[TARGET_COLUMN].value_counts()
    )

    minerals = [m for m in list(SPECTRAL_MINERALS) + list(VNIR_MINERALS) if m in work.columns]
    mineral_means: dict[str, dict[str, float | None]] = {}
    grouped = work.groupby(TARGET_COLUMN)[minerals].mean().reindex(list(DOMAINS))
    for domain, row in grouped.iterrows():
        mineral_means[str(domain)] = {
            str(name): (None if pd.isna(value) else round(float(value), 2)) for name, value in row.items()
        }

    _STATE.update(
        {
            "frame": work,
            "spectral_z": spectral_z,
            "variance": [float(v) for v in var_ratio[:2]],
            "silhouette": float(silhouette),
            "n": int(len(work)),
            "holes": int(work["holeid"].nunique()),
            "labeled": labeled_n,
            "unlabeled": int(len(work) - labeled_n),
            "counts": {str(k): int(v) for k, v in counts.to_dict().items()},
            "mineral_means": mineral_means,
            "models": None,
        }
    )
    return _STATE


@app.on_event("startup")
def _startup() -> None:
    _boot()
    print("GeoIA Dominios ML: HTML en GET /", flush=True)


@app.get("/health")
@app.head("/health")
def health():
    return {"status": "ok", "service": "dominios-ml"}


@app.get("/")
@app.head("/")
def index():
    return _index_response()


@app.get("/index.html")
def index_html():
    return _index_response()


@app.get("/css/style.css")
def css_file():
    path = _frontend() / "css" / "style.css"
    if not path.is_file():
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    return FileResponse(path, media_type="text/css")


@app.get("/js/app.js")
def js_file():
    path = _frontend() / "js" / "app.js"
    if not path.is_file():
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    return FileResponse(path, media_type="application/javascript")


@app.get("/api/summary")
def api_summary():
    state = _boot()
    domains = []
    for code in DOMAINS:
        domains.append(
            {
                "code": code,
                "label": DOMAIN_LABELS[code],
                "color": DOMAIN_COLORS[code],
                "assemblage": DOMAIN_ASSEMBLAGES[code],
                "n": int(state["counts"].get(code, 0)),
            }
        )
    return {
        "n": state["n"],
        "holes": state["holes"],
        "labeled": state["labeled"],
        "unlabeled": state["unlabeled"],
        "variance_pc1_pc2": state["variance"],
        "silhouette_kmeans": round(state["silhouette"], 3),
        "domains": domains,
        "minerals": [m for m in SPECTRAL_MINERALS],
        "chemistry": [c for c in CHEMICAL_COLUMNS],
        "mineral_means": state["mineral_means"],
        "thesis": {
            "title": "Delimitación de los dominios geológicos de alteración desde firmas espectrales y geoquímica mediante el empleo de machine learning",
            "author": "Jhonatan Paul Mallma Espinoza",
            "advisor": "MSc. César Augusto Mendoza Tarazona",
            "year": 2026,
            "institution": "FIGMM · Universidad Nacional de Ingeniería",
            "pages": "https://jhon21geo.github.io/geologia-ML-dominios-alteracion/",
            "repo": "https://github.com/jhon21geo/geologia-ML-dominios-alteracion",
            "colab": "https://colab.research.google.com/github/jhon21geo/geologia-ML-dominios-alteracion/blob/main/notebooks/00_colab_pipeline.ipynb",
        },
    }


@app.get("/api/scatter")
def api_scatter(limit: int = 0):
    state = _boot()
    frame = state["frame"]
    if limit and limit > 0 and limit < len(frame):
        frame = frame.sample(n=limit, random_state=42).sort_index()
    cols = {
        "x": _num(frame, "x"),
        "y": _num(frame, "y"),
        "z": _num(frame, "z"),
        "from_m": _num(frame, "from_m"),
        "to_m": _num(frame, "to_m"),
        "pc1": _num(frame, "pc1"),
        "pc2": _num(frame, "pc2"),
        "cluster": [int(v) for v in frame["cluster_k5"].tolist()],
        "domain": [str(v) for v in frame[TARGET_COLUMN].tolist()],
        "holeid": [str(v) for v in frame["holeid"].tolist()],
        "labeled": [bool(v) for v in frame["labeled"].tolist()],
    }
    return {"n": len(frame["x"]), **cols}


@app.get("/api/hole/{holeid}")
def api_hole(holeid: str):
    state = _boot()
    sub = state["frame"][state["frame"]["holeid"] == holeid].sort_values("from_m")
    if sub.empty:
        return JSONResponse({"detail": "Sondaje no encontrado"}, status_code=404)
    minerals = [m for m in SPECTRAL_MINERALS if m in sub.columns]
    return {
        "holeid": holeid,
        "n": int(len(sub)),
        "from_m": _num(sub, "from_m"),
        "to_m": _num(sub, "to_m"),
        "domain": [str(v) for v in sub[TARGET_COLUMN].tolist()],
        "cluster": [int(v) for v in sub["cluster_k5"].tolist()],
        "minerals": {m: _num(sub, m) for m in minerals},
    }


@app.get("/api/models")
def api_models():
    return _fit_models()


def _fit_models() -> dict[str, Any]:
    state = _boot()
    cached = state.get("models")
    if cached is not None:
        return cached

    frame = state["frame"]
    chem_ready, chem_z, _ = prepare_feature_matrix(frame, feature_kind="chemistry")
    labeled = chem_ready[chem_ready["labeled"]].copy()
    split = split_labeled(labeled, chem_z, test_size=0.20, random_state=42)
    THESIS_HYPERPARAMS["random_forest"]["n_jobs"] = 1
    models = train_models(split, profile="thesis")
    results = {name: evaluate_model(model, split.X_test, split.y_test) for name, model in models.items()}
    ranking = metrics_table(results)
    best_name = str(ranking.iloc[0]["modelo"])
    best = results[best_name]
    payload = {
        "best_model": best_name,
        "n_train": int(len(split.y_train)),
        "n_test": int(len(split.y_test)),
        "ranking": json.loads(ranking.to_json(orient="records")),
        "confusion": {
            "labels": list(DOMAINS),
            "matrix": best["confusion"].astype(int).tolist(),
            "modelo": best_name,
        },
        "note": "Hiperparámetros de las Tablas 19–22 (perfil thesis). Random Forest fue el más estable en la tesis; el ranking sintético se recalcula aquí.",
    }
    state["models"] = payload
    return payload


def _num(frame: pd.DataFrame, col: str) -> list[float | None]:
    values = []
    for value in frame[col].tolist():
        if value is None or (isinstance(value, float) and np.isnan(value)):
            values.append(None)
        else:
            values.append(round(float(value), 4))
    return values
