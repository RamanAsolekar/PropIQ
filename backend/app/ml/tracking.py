"""
PropIQ Experiment Tracking + Model Registry (MLflow).

Two responsibilities:
  1. log_training_run(...)  — record params, metrics, SHAP stability and the
     model artifact to MLflow on every training run.
  2. A lightweight, file-backed Model Registry (registry.json) that records
     versions, stages (Staging/Production/Archived) and champion/challenger, so
     deployment can pin/rollback a specific model version.

MLflow uses a LOCAL FILE STORE by default (settings.MLFLOW_TRACKING_URI =
file:backend/data/mlruns) so it needs NO server. If MLFLOW_TRACKING_URI points
at a server, it uses that instead. If MLflow isn't installed at all, tracking
degrades to writing the same metadata into the local registry — training never
fails because of telemetry.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

REGISTRY_PATH = settings.MODEL_DIR / "registry.json"


# ── File-backed Model Registry ──────────────────────────────────────────────


def _load_registry() -> dict:
    if REGISTRY_PATH.exists():
        try:
            return json.loads(REGISTRY_PATH.read_text())
        except Exception:
            pass
    return {"models": [], "production": None, "champion": None}


def _save_registry(reg: dict) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(reg, indent=2))


def register_model_version(
    version: str,
    metrics: Dict,
    feature_schema_version: str,
    data_hash: str,
    stage: str = "Staging",
    mlflow_run_id: Optional[str] = None,
) -> dict:
    """Record a new model version in the registry."""
    reg = _load_registry()
    entry = {
        "version": version,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "metrics": metrics,
        "feature_schema_version": feature_schema_version,
        "data_hash": data_hash,
        "mlflow_run_id": mlflow_run_id,
    }
    # de-dupe by version
    reg["models"] = [m for m in reg["models"] if m["version"] != version]
    reg["models"].append(entry)
    _save_registry(reg)
    logger.info("Registered model %s (stage=%s).", version, stage)
    return entry


def promote_to_production(version: str) -> dict:
    """Move a version to Production; archive the previous Production model."""
    reg = _load_registry()
    found = next((m for m in reg["models"] if m["version"] == version), None)
    if not found:
        raise ValueError(f"Model version {version} not in registry.")
    for m in reg["models"]:
        if m["stage"] == "Production" and m["version"] != version:
            m["stage"] = "Archived"
    found["stage"] = "Production"
    reg["production"] = version
    _save_registry(reg)
    logger.info("Promoted %s to Production.", version)
    return found


def get_production_version() -> Optional[dict]:
    reg = _load_registry()
    if reg.get("production"):
        return next((m for m in reg["models"] if m["version"] == reg["production"]), None)
    # default: newest registered
    return reg["models"][-1] if reg["models"] else None


def get_registry() -> dict:
    return _load_registry()


# ── MLflow experiment tracking ──────────────────────────────────────────────


def log_training_run(
    params: Dict,
    metrics: Dict,
    model_dir: str,
    tags: Optional[Dict] = None,
) -> Optional[str]:
    """
    Log a training run to MLflow. Returns the run_id (or None if MLflow absent).
    Never raises — telemetry must not break training.
    """
    try:
        import mlflow

        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        mlflow.set_experiment(settings.MLFLOW_EXPERIMENT)
        with mlflow.start_run() as run:
            mlflow.log_params(params)
            mlflow.log_metrics({k: float(v) for k, v in metrics.items() if v is not None})
            if tags:
                mlflow.set_tags(tags)
            meta = Path(model_dir) / "model_meta.json"
            if meta.exists():
                mlflow.log_artifact(str(meta))
            logger.info("Logged training run %s to MLflow.", run.info.run_id)
            return run.info.run_id
    except Exception as e:
        logger.warning("MLflow logging skipped (%s).", e)
        return None
