"""
PropIQ Model Monitoring — data drift + performance.

Compares the LIVE feature distribution (from prediction_logs) against the
TRAINING reference distribution and flags drift via:
  - PSI (Population Stability Index) per feature  [pure numpy, always available]
  - Evidently DataDriftPreset report               [when evidently installed]

Drift is the early-warning that the world has moved away from what the model
learned — the trigger for automated retraining. Without the prediction-log
(outcome loop) this would be impossible; the two systems are paired.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from app.core.config import settings
from app.ml.features import FEATURE_COLS

logger = logging.getLogger(__name__)


def population_stability_index(
    expected: np.ndarray, actual: np.ndarray, buckets: int = 10
) -> float:
    """PSI between a reference (expected) and live (actual) sample.
    <0.1 no drift · 0.1–0.25 moderate · >0.25 significant drift."""
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    if len(expected) < 2 or len(actual) < 1:
        return 0.0
    # Quantile edges from the reference; guard against constant features
    edges = np.unique(np.quantile(expected, np.linspace(0, 1, buckets + 1)))
    if len(edges) < 3:
        return 0.0
    e_counts, _ = np.histogram(expected, bins=edges)
    a_counts, _ = np.histogram(actual, bins=edges)
    e_pct = np.clip(e_counts / max(e_counts.sum(), 1), 1e-6, None)
    a_pct = np.clip(a_counts / max(a_counts.sum(), 1), 1e-6, None)
    return float(np.sum((a_pct - e_pct) * np.log(a_pct / e_pct)))


def _load_reference() -> Optional[pd.DataFrame]:
    path = settings.PROCESSED_DIR / "synthetic_training_data.csv"
    if path.exists():
        return pd.read_csv(path)
    return None


def _load_live_features(limit: int = 1000) -> pd.DataFrame:
    from app.core.db import SessionLocal
    from app.models.db_models import PredictionLog

    db = SessionLocal()
    try:
        rows = (
            db.query(PredictionLog)
            .order_by(PredictionLog.id.desc())
            .limit(limit)
            .all()
        )
        records = [r.feature_vector for r in rows if r.feature_vector]
        return pd.DataFrame(records) if records else pd.DataFrame()
    finally:
        db.close()


def compute_drift(limit: int = 1000) -> Dict:
    """Per-feature PSI drift report comparing live predictions vs training data."""
    ref = _load_reference()
    live = _load_live_features(limit)
    if ref is None:
        return {"status": "no_reference", "message": "Training data not found."}
    if live.empty:
        return {
            "status": "insufficient_live_data",
            "message": "No logged predictions yet — make some /assess calls first.",
            "n_live": 0,
        }

    warn, alert = settings.DRIFT_PSI_WARN, settings.DRIFT_PSI_ALERT
    per_feature: List[Dict] = []
    drifted = 0
    for col in FEATURE_COLS:
        if col in ref.columns and col in live.columns:
            psi = round(population_stability_index(ref[col].values, live[col].values), 4)
            status = "alert" if psi >= alert else "warn" if psi >= warn else "ok"
            if status != "ok":
                drifted += 1
            per_feature.append({"feature": col, "psi": psi, "status": status})

    per_feature.sort(key=lambda x: x["psi"], reverse=True)
    overall = (
        "alert" if any(f["status"] == "alert" for f in per_feature)
        else "warn" if any(f["status"] == "warn" for f in per_feature)
        else "ok"
    )
    return {
        "status": "ok",
        "overall_drift": overall,
        "n_reference": int(len(ref)),
        "n_live": int(len(live)),
        "drifted_feature_count": drifted,
        "thresholds": {"warn_psi": warn, "alert_psi": alert},
        "retraining_recommended": overall == "alert",
        "per_feature": per_feature,
        "engine": "psi_numpy",
    }


def evidently_report_html(limit: int = 1000) -> Optional[str]:
    """Full Evidently DataDriftPreset report as HTML (when installed)."""
    try:
        from evidently.metric_preset import DataDriftPreset
        from evidently.report import Report

        ref = _load_reference()
        live = _load_live_features(limit)
        if ref is None or live.empty:
            return None
        cols = [c for c in FEATURE_COLS if c in ref.columns and c in live.columns]
        report = Report(metrics=[DataDriftPreset()])
        report.run(reference_data=ref[cols], current_data=live[cols])
        return report.get_html()
    except Exception as e:
        logger.warning("Evidently report unavailable (%s).", e)
        return None
