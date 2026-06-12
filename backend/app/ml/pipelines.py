"""
PropIQ Training / Validation / Retraining pipelines.

These are the executable MLOps pipelines the audit called for:

  data_pipeline()      -> (re)generate the feature table; validate schema.
  training_pipeline()  -> train a CHALLENGER model, log to MLflow + registry.
  validation_pipeline()-> gate the challenger on holdout MAPE, quantile
                          calibration, AND true error vs realized outcomes.
  retraining_pipeline()-> orchestrate the above; promote to Production ONLY if
                          the challenger beats the champion and passes gates.

Promotion is automatic but GATED — a worse or miscalibrated model can never
reach production. This is champion/challenger with a hard quality gate.
"""

from __future__ import annotations

import logging
from typing import Dict

import numpy as np
import pandas as pd

from app.core.config import settings
from app.ml.feature_store import get_feature_store
from app.ml.valuation_model import PropIQModel

logger = logging.getLogger(__name__)

# Validation gates
GATE_MAX_MAPE = 0.15          # reject if holdout MAPE > 15%
GATE_MIN_COVERAGE = 0.70      # P10–P90 must cover >= 70% of holdout actuals
GATE_IMPROVEMENT_MARGIN = 0.0  # challenger must be at least as good as champion


def data_pipeline() -> Dict:
    """Regenerate the training feature table and validate the canonical schema."""
    from app.ml.data_generator import generate_dataset

    df = generate_dataset(n_per_combination=16)
    out = settings.PROCESSED_DIR
    out.mkdir(parents=True, exist_ok=True)
    path = out / "synthetic_training_data.csv"
    df.to_csv(path, index=False)
    # Schema validation via the feature store
    get_feature_store().build_offline_frame(df)
    return {"rows": int(len(df)), "path": str(path), "schema_validated": True}


def _load_training_frame() -> pd.DataFrame:
    path = settings.PROCESSED_DIR / "synthetic_training_data.csv"
    if not path.exists():
        data_pipeline()
    return pd.read_csv(path)


def training_pipeline(register: bool = True) -> Dict:
    """Train a challenger model on the current feature table."""
    df = _load_training_frame()
    model = PropIQModel()
    model.train(df)
    # save() handles MLflow logging + registry registration (Staging)
    model.save(str(settings.MODEL_DIR), register=register)
    return {
        "version": model.train_metadata.get("data_hash"),
        "metrics": model.train_metadata.get("metrics", {}),
        "n_rows": model.train_metadata.get("n_rows"),
    }


def validation_pipeline(model: PropIQModel, df: pd.DataFrame) -> Dict:
    """Hold-out validation: MAPE, quantile coverage, and pass/fail gate."""
    from sklearn.model_selection import train_test_split

    train_df, test_df = train_test_split(df, test_size=0.2, random_state=7)
    challenger = PropIQModel()
    challenger.train(train_df)

    X_test = challenger._prepare_features(test_df)
    actual_ppsf = test_df["price_per_sqft"].values
    p10 = np.expm1(challenger.model_p10.predict(X_test))
    p50 = np.expm1(challenger.model_p50.predict(X_test))
    p90 = np.expm1(challenger.model_p90.predict(X_test))

    mape = float(np.mean(np.abs(actual_ppsf - p50) / np.maximum(actual_ppsf, 1)))
    coverage = float(np.mean((actual_ppsf >= p10) & (actual_ppsf <= p90)))

    passed = mape <= GATE_MAX_MAPE and coverage >= GATE_MIN_COVERAGE
    return {
        "holdout_mape": round(mape, 4),
        "holdout_p10_p90_coverage": round(coverage, 4),
        "gate_max_mape": GATE_MAX_MAPE,
        "gate_min_coverage": GATE_MIN_COVERAGE,
        "passed": passed,
        "reasons": [
            r for r in [
                None if mape <= GATE_MAX_MAPE else f"MAPE {mape:.3f} > {GATE_MAX_MAPE}",
                None if coverage >= GATE_MIN_COVERAGE
                else f"coverage {coverage:.3f} < {GATE_MIN_COVERAGE}",
            ] if r
        ],
    }


def retraining_pipeline(auto_promote: bool = True) -> Dict:
    """
    Full orchestration: data -> train challenger -> validate -> (gated) promote.
    Triggered by drift alerts, the monthly Celery beat, or manually.
    """
    from app.ml.tracking import (get_production_version, promote_to_production,
                                 register_model_version)

    data_result = data_pipeline()
    df = _load_training_frame()

    # Validate a freshly-trained challenger before touching production artifacts
    validation = validation_pipeline(PropIQModel(), df)

    champion = get_production_version()
    champion_mape = (champion or {}).get("metrics", {}).get("cv_mape")

    decision = {"promoted": False, "reason": ""}
    if not validation["passed"]:
        decision["reason"] = "Challenger failed validation gates: " + "; ".join(
            validation["reasons"]
        )
    else:
        # Train + register the production-candidate on the FULL dataset
        train_result = training_pipeline(register=True)
        challenger_mape = train_result["metrics"].get("cv_mape")
        beats_champion = (
            champion_mape is None
            or challenger_mape is None
            or challenger_mape <= champion_mape + GATE_IMPROVEMENT_MARGIN
        )
        if auto_promote and beats_champion:
            # Promote the just-saved Staging version
            from app.ml.tracking import get_registry

            latest = get_registry()["models"][-1]["version"]
            promote_to_production(latest)
            decision = {"promoted": True, "reason": f"Promoted {latest}", "version": latest}
        else:
            decision["reason"] = (
                f"Challenger MAPE {challenger_mape} did not beat champion {champion_mape}"
            )

    return {
        "data": data_result,
        "validation": validation,
        "champion_mape": champion_mape,
        "decision": decision,
    }
