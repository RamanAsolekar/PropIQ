"""
PropIQ Fairness / Bias Audit — fair-lending guardrail.

Locality is a strong valuation driver and can proxy socio-economic status, so a
model that systematically under-values peripheral-zone collateral would push
those borrowers to lower LTVs — a fair-lending concern. This module audits the
LOGGED predictions (PredictionLog) grouped by zone_tier (the SES proxy) and
reports group disparities + the disparate-impact (80%) rule.

Pure numpy/pandas (always available). `fairlearn` is optional for richer metrics.
"""

from __future__ import annotations

import logging
from typing import Dict

logger = logging.getLogger(__name__)


def _zone_for(locality: str) -> str:
    try:
        from app.data.india_circle_rates import get_circle_rate

        return get_circle_rate(locality, "2bhk_apartment").get("zone_tier", "unknown")
    except Exception:
        return "unknown"


def bias_audit(limit: int = 2000) -> Dict:
    """Group-wise fairness metrics over logged predictions, grouped by zone tier."""
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
    finally:
        db.close()

    if not rows:
        return {"n": 0, "message": "No predictions logged yet — run some /assess calls."}

    # Group by zone tier (protected-attribute proxy)
    groups: Dict[str, list] = {}
    for r in rows:
        fv = r.feature_vector or {}
        zte = fv.get("zone_tier_encoded")
        zone = {2: "prime", 1: "mid", 0: "peripheral"}.get(zte)
        if zone is None:
            zone = _zone_for(r.locality or "")
        groups.setdefault(zone, []).append(r)

    # Per-group metrics: avg confidence (a proxy for "favorable assessment rate"),
    # avg RPI, avg predicted value/sqft-ish, and a "favorable" rate (conf >= 0.8)
    group_stats = {}
    for zone, items in groups.items():
        confs = [i.confidence_score for i in items if i.confidence_score is not None]
        rpis = [i.resale_potential_index for i in items if i.resale_potential_index is not None]
        favorable = [1 for i in items if (i.confidence_score or 0) >= 0.8]
        n = len(items)
        group_stats[zone] = {
            "n": n,
            "favorable_rate": round(len(favorable) / n, 3) if n else 0.0,
            "avg_confidence": round(sum(confs) / len(confs), 3) if confs else None,
            "avg_rpi": round(sum(rpis) / len(rpis), 1) if rpis else None,
        }

    # Disparate impact (80% rule): min favorable rate / max favorable rate
    rates = {z: s["favorable_rate"] for z, s in group_stats.items() if s["n"] >= 1}
    di_ratio = None
    di_pass = None
    if len(rates) >= 2 and max(rates.values()) > 0:
        di_ratio = round(min(rates.values()) / max(rates.values()), 3)
        di_pass = di_ratio >= 0.8

    # Demographic parity gap = max - min favorable rate
    dp_gap = round(max(rates.values()) - min(rates.values()), 3) if len(rates) >= 2 else None

    # Optional fairlearn enrichment
    engine = "numpy"
    try:
        import fairlearn  # noqa
        engine = "numpy+fairlearn_available"
    except Exception:
        pass

    return {
        "n": len(rows),
        "protected_attribute": "zone_tier (socio-economic proxy)",
        "group_stats": group_stats,
        "disparate_impact_ratio": di_ratio,
        "disparate_impact_pass_80pct_rule": di_pass,
        "demographic_parity_gap": dp_gap,
        "engine": engine,
        "interpretation": (
            "Disparate-impact ratio >= 0.80 passes the four-fifths rule. A large "
            "demographic-parity gap across zone tiers warrants fair-lending review."
        ),
    }
