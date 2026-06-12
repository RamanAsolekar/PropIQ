"""
PropIQ Realized-Outcome Loop — the data flywheel.

The audit's #1 finding: the model never learns whether its valuations were
right. This module closes that loop:

  log_prediction(result)         -> persist every prediction + its features
  record_outcome(request_id, ..) -> later, record the ACTUAL sale/recovery value
  outcome_performance()          -> true MAPE / bias / interval coverage vs reality

That true error (not MAPE-on-synthetic) is the only metric an NBFC can trust,
and the labelled (prediction, outcome) pairs become the training set that makes
PropIQ improve with every closed loan.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from app.core.db import SessionLocal
from app.models.db_models import PredictionLog, RealizedOutcome

logger = logging.getLogger(__name__)


def _model_version() -> Optional[str]:
    try:
        from app.ml.tracking import get_production_version

        prod = get_production_version()
        return prod.get("version") if prod else None
    except Exception:
        return None


def log_prediction(result: dict, endpoint: str = "/assess") -> None:
    """Persist a prediction with its feature vector for outcome-tracking + drift.
    Best-effort: never raises into the request path."""
    db = SessionLocal()
    try:
        mv = result.get("market_value_range", [None, None])
        row = PredictionLog(
            request_id=result.get("request_id", ""),
            model_version=_model_version(),
            feature_schema_version=result.get("feature_schema_version"),
            locality=result.get("locality"),
            prop_type=result.get("prop_type"),
            predicted_value_mid=float(result.get("market_value_mid", 0) or 0),
            predicted_p10=(mv[0] if mv and mv[0] is not None else None),
            predicted_p90=(mv[1] if mv and len(mv) > 1 else None),
            confidence_score=result.get("confidence_score"),
            resale_potential_index=result.get("resale_potential_index"),
            feature_vector=result.get("_feature_vector"),
            endpoint=endpoint,
        )
        db.add(row)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning("log_prediction failed (non-fatal): %s", e)
    finally:
        db.close()


def record_outcome(
    request_id: str,
    realized_value: float,
    outcome_type: str = "sale",
    realized_on: Optional[str] = None,
    days_to_liquidate: Optional[int] = None,
    notes: Optional[str] = None,
) -> dict:
    """Record the actual realized value and compute true error vs the prediction."""
    db = SessionLocal()
    try:
        pred = (
            db.query(PredictionLog)
            .filter(PredictionLog.request_id == request_id)
            .order_by(PredictionLog.id.desc())
            .first()
        )
        abs_err = signed_err = None
        if pred and pred.predicted_value_mid:
            signed_err = (realized_value - pred.predicted_value_mid) / pred.predicted_value_mid * 100
            abs_err = abs(signed_err)

        outcome = RealizedOutcome(
            request_id=request_id,
            outcome_type=outcome_type,
            realized_value=float(realized_value),
            realized_on=datetime.fromisoformat(realized_on) if realized_on else None,
            days_to_liquidate=days_to_liquidate,
            notes=notes,
            abs_pct_error=abs_err,
            signed_pct_error=signed_err,
        )
        db.add(outcome)
        db.commit()
        db.refresh(outcome)
        return {
            "request_id": request_id,
            "realized_value": realized_value,
            "predicted_value_mid": pred.predicted_value_mid if pred else None,
            "abs_pct_error": round(abs_err, 2) if abs_err is not None else None,
            "signed_pct_error": round(signed_err, 2) if signed_err is not None else None,
            "matched_prediction": pred is not None,
        }
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


def outcome_performance() -> dict:
    """
    True performance vs realized outcomes — the metric that actually matters.
    Returns real MAPE, bias (mean signed error), and P10–P90 interval coverage.
    """
    db = SessionLocal()
    try:
        outcomes = db.query(RealizedOutcome).all()
        if not outcomes:
            return {
                "n_outcomes": 0,
                "message": "No realized outcomes yet. Record sales/recoveries via "
                "POST /api/v1/outcomes to start measuring true model accuracy.",
            }

        abs_errs = [o.abs_pct_error for o in outcomes if o.abs_pct_error is not None]
        signed = [o.signed_pct_error for o in outcomes if o.signed_pct_error is not None]

        # Interval coverage: realized value within the logged [P10, P90]
        covered = total = 0
        for o in outcomes:
            pred = (
                db.query(PredictionLog)
                .filter(PredictionLog.request_id == o.request_id)
                .order_by(PredictionLog.id.desc())
                .first()
            )
            if pred and pred.predicted_p10 and pred.predicted_p90:
                total += 1
                if pred.predicted_p10 <= o.realized_value <= pred.predicted_p90:
                    covered += 1

        n = len(abs_errs)
        return {
            "n_outcomes": len(outcomes),
            "true_mape_pct": round(sum(abs_errs) / n, 2) if n else None,
            "bias_pct": round(sum(signed) / len(signed), 2) if signed else None,
            "p10_p90_coverage_pct": round(covered / total * 100, 1) if total else None,
            "interpretation": (
                "Positive bias => model under-values vs market; "
                "negative => over-values. Coverage should approach 80%."
            ),
        }
    finally:
        db.close()
