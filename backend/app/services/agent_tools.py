"""
PropIQ Agent Tools — typed tool registry for the valuation agent.

Each tool wraps an EXISTING PropIQ engine and returns a uniform envelope:
    {"value": <primary result>, "source": <engine name>, "detail": {...}}
so the agent can cite every number back to a tool result (the verifier enforces
this). The OpenAI/Groq-style JSON schemas in TOOL_SCHEMAS let the LLM call them.

Nothing here re-implements logic — it's a thin, auditable adapter over
get_circle_rate, the XGBoost model, comps, CV, LTV and RAG.
"""

from __future__ import annotations

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


# ── Tool implementations (sync; agent loop awaits via asyncio.to_thread) ─────


def lookup_circle_rate(locality: str, prop_type: str) -> Dict:
    from app.data.india_circle_rates import get_circle_rate

    cr = get_circle_rate(locality, prop_type)
    return {
        "value": cr["circle_rate_per_sqft"],
        "source": "igr_circle_rate_db",
        "detail": {"locality": cr["locality"], "city": cr.get("city"),
                   "zone_tier": cr["zone_tier"], "property_type_key": cr["property_type_key"]},
    }


def run_avm(locality: str, prop_type: str, size_sqft: float, age_years: float,
            floor_num: int = 3, **kwargs) -> Dict:
    from app.data.india_circle_rates import ZONE_MULTIPLIERS, get_circle_rate
    from app.main import get_model

    cr = get_circle_rate(locality, prop_type)
    zone = cr["zone_tier"]
    model_input = {
        "locality": locality, "zone_tier": zone, "prop_type": prop_type,
        "size_sqft": size_sqft, "age_years": age_years, "floor_num": floor_num,
        "is_freehold": kwargs.get("is_freehold", 1),
        "is_rera_registered": kwargs.get("is_rera_registered", 1),
        "rental_yield_pct": kwargs.get("rental_yield_pct", 0.0),
        "circle_rate_per_sqft": cr["circle_rate_per_sqft"],
        "location_multiplier": ZONE_MULTIPLIERS[zone]["mid"],
    }
    pred = get_model().predict(model_input)
    pred.pop("_feature_vector", None)
    return {
        "value": pred["market_value_mid"],
        "source": "xgboost_quantile_avm",
        "detail": {"market_value_range": pred["market_value_range"],
                   "price_per_sqft_estimate": pred["price_per_sqft_estimate"],
                   "resale_potential_index": pred["resale_potential_index"],
                   "confidence_score": pred["confidence_score"],
                   "risk_flags": pred.get("risk_flags", [])},
    }


def fetch_comps(locality: str, prop_type: str, size_sqft: float, age_years: float) -> Dict:
    from app.services.comps_engine import find_comps, get_comp_stats

    comps = find_comps(locality, prop_type, size_sqft, age_years, n=5)
    stats = get_comp_stats(locality, prop_type)
    return {
        "value": stats.get("avg_price_sqft"),
        "source": "comps_engine",
        "detail": {"n_comps": len(comps), "avg_price_sqft": stats.get("avg_price_sqft"),
                   "comps": comps[:5]},
    }


def compute_ltv(market_value_mid: float, prop_type_key: str, zone_tier: str,
                distress_value_range: List = None, resale_potential_index: float = 50.0,
                risk_flags: List = None) -> Dict:
    from app.services.ltv_audit import calculate_ltv

    ltv = calculate_ltv(
        market_value_mid=int(market_value_mid),
        distress_value_range=distress_value_range or [int(market_value_mid * 0.7),
                                                      int(market_value_mid * 0.8)],
        prop_type_key=prop_type_key, zone_tier=zone_tier,
        risk_flags=risk_flags or [], resale_potential_index=resale_potential_index,
    )
    return {
        "value": ltv["recommended_ltv_pct"],
        "source": "rbi_ltv_engine",
        "detail": {"max_loan_amount": ltv["max_loan_amount"],
                   "rbi_max_ltv_pct": ltv["rbi_max_ltv_pct"],
                   "pfl_internal_ltv_pct": ltv["pfl_internal_ltv_pct"],
                   "ltv_zone": ltv["ltv_zone"]},
    }


def check_policy(query: str) -> Dict:
    from app.services.rag import retrieve_context

    snippets = retrieve_context(query, k=3)
    return {
        "value": len(snippets),
        "source": "rag_policy_base",
        "detail": {"citations": [s["citation"] for s in snippets],
                   "snippets": [s["snippet"][:200] for s in snippets]},
    }


def run_ensemble(avm_value: float, locality: str, prop_type: str, size_sqft: float,
                 age_years: float, rental_yield_pct: float = 0.0) -> Dict:
    from app.ml.ensemble import (calibrate_band, comps_estimate,
                                 income_estimate, reconcile)

    avm = {"value": int(avm_value), "confidence": 0.75}
    comps = comps_estimate(locality, prop_type, size_sqft, age_years)
    income = income_estimate(avm_value, rental_yield_pct, age_years)
    recon = reconcile(avm, comps, income, prop_type)
    return {
        "value": recon["reconciled_value"],
        "source": "multi_model_ensemble",
        "detail": {"approaches_used": recon["approaches_used"],
                   "agreement_score": recon["agreement_score"],
                   "contributions": recon["contributions"]},
    }


TOOLS = {
    "lookup_circle_rate": lookup_circle_rate,
    "run_avm": run_avm,
    "fetch_comps": fetch_comps,
    "compute_ltv": compute_ltv,
    "check_policy": check_policy,
    "run_ensemble": run_ensemble,
}


# ── Tool schemas (Groq/OpenAI function-calling format) ──────────────────────

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "lookup_circle_rate",
        "description": "Get the statutory IGR circle rate (₹/sqft floor) and zone tier for a locality. Call FIRST to anchor valuation.",
        "parameters": {"type": "object", "properties": {
            "locality": {"type": "string"}, "prop_type": {"type": "string"}},
            "required": ["locality", "prop_type"]}}},
    {"type": "function", "function": {
        "name": "run_avm",
        "description": "Run the XGBoost AVM to get market value range, RPI, confidence and risk flags. The primary valuation estimate.",
        "parameters": {"type": "object", "properties": {
            "locality": {"type": "string"}, "prop_type": {"type": "string"},
            "size_sqft": {"type": "number"}, "age_years": {"type": "number"},
            "floor_num": {"type": "integer"}, "rental_yield_pct": {"type": "number"}},
            "required": ["locality", "prop_type", "size_sqft", "age_years"]}}},
    {"type": "function", "function": {
        "name": "fetch_comps",
        "description": "Fetch comparable sales and market stats for the locality (sales-comparison approach).",
        "parameters": {"type": "object", "properties": {
            "locality": {"type": "string"}, "prop_type": {"type": "string"},
            "size_sqft": {"type": "number"}, "age_years": {"type": "number"}},
            "required": ["locality", "prop_type", "size_sqft", "age_years"]}}},
    {"type": "function", "function": {
        "name": "run_ensemble",
        "description": "Reconcile AVM + comps + income approaches into one value with an agreement score. Call AFTER run_avm.",
        "parameters": {"type": "object", "properties": {
            "avm_value": {"type": "number"}, "locality": {"type": "string"},
            "prop_type": {"type": "string"}, "size_sqft": {"type": "number"},
            "age_years": {"type": "number"}, "rental_yield_pct": {"type": "number"}},
            "required": ["avm_value", "locality", "prop_type", "size_sqft", "age_years"]}}},
    {"type": "function", "function": {
        "name": "compute_ltv",
        "description": "Compute the RBI-compliant recommended LTV and max loan amount. Call AFTER you have a market value.",
        "parameters": {"type": "object", "properties": {
            "market_value_mid": {"type": "number"}, "prop_type_key": {"type": "string"},
            "zone_tier": {"type": "string"}, "resale_potential_index": {"type": "number"}},
            "required": ["market_value_mid", "prop_type_key", "zone_tier"]}}},
    {"type": "function", "function": {
        "name": "check_policy",
        "description": "Retrieve RBI / internal credit-policy text to ground a recommendation. Use to justify the LTV/acceptability.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}},
            "required": ["query"]}}},
]
