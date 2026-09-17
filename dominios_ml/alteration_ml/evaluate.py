"""Métricas de clasificación: matriz de confusión, ROC one-vs-rest y ranking."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from alteration_ml.constants import DOMAINS


def _safe_auc(y_true, y_score, labels) -> float:
    try:
        return float(
            roc_auc_score(y_true, y_score, multi_class="ovr", average="macro", labels=labels)
        )
    except ValueError:
        return float("nan")


def _class_scores(model, X_test):
    """Probabilidades o scores de decisión normalizados para ROC."""
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X_test), list(model.classes_)
    if hasattr(model, "decision_function"):
        raw = model.decision_function(X_test)
        if raw.ndim == 1:
            raw = np.column_stack([-raw, raw])
        shifted = raw - raw.max(axis=1, keepdims=True)
        exp = np.exp(shifted)
        return exp / exp.sum(axis=1, keepdims=True), list(model.classes_)
    return None, None


def evaluate_model(model, X_test, y_test, labels: tuple[str, ...] = DOMAINS) -> dict[str, Any]:
    y_pred = model.predict(X_test)
    y_score, classes = _class_scores(model, X_test)
    if y_score is not None:
        auc = _safe_auc(y_test, y_score, labels=classes)
        roc_curves = {}
        class_index = {c: i for i, c in enumerate(classes)}
        for domain in labels:
            if domain not in class_index:
                continue
            binary = (np.asarray(y_test) == domain).astype(int)
            fpr, tpr, _ = roc_curve(binary, y_score[:, class_index[domain]])
            roc_curves[domain] = (fpr, tpr)
    else:
        auc = float("nan")
        roc_curves = {}

    report = classification_report(y_test, y_pred, labels=list(labels), output_dict=True, zero_division=0)
    return {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, average="macro", zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, average="macro", zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
        "auc": auc,
        "confusion": confusion_matrix(y_test, y_pred, labels=list(labels)),
        "labels": list(labels),
        "y_pred": y_pred,
        "report": report,
        "roc_curves": roc_curves,
    }


def metrics_table(results: dict[str, dict]) -> pd.DataFrame:
    rows = []
    for name, res in results.items():
        rows.append(
            {
                "modelo": name,
                "AUC": round(res["auc"], 3) if res["auc"] == res["auc"] else np.nan,
                "accuracy": round(res["accuracy"], 3),
                "balanced_acc": round(res["balanced_accuracy"], 3),
                "precision": round(res["precision"], 3),
                "recall": round(res["recall"], 3),
                "f1": round(res["f1"], 3),
            }
        )
    return pd.DataFrame(rows).sort_values("f1", ascending=False).reset_index(drop=True)


def per_domain_table(results: dict[str, dict], labels: tuple[str, ...] = DOMAINS) -> pd.DataFrame:
    rows = []
    for name, res in results.items():
        for domain in labels:
            stats = res["report"].get(domain, {})
            rows.append(
                {
                    "modelo": name,
                    "dominio": domain,
                    "precision": round(float(stats.get("precision", 0.0)), 3),
                    "recall": round(float(stats.get("recall", 0.0)), 3),
                    "f1": round(float(stats.get("f1-score", 0.0)), 3),
                    "soporte": int(stats.get("support", 0)),
                }
            )
    return pd.DataFrame(rows)
