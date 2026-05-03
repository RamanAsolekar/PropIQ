"""
Celery tasks for PropIQ background processing.
These tasks run in worker processes, separate from the FastAPI web server.
"""

import asyncio
import time
import uuid

from app.core.celery_app import celery_app
from app.core.config import settings
from app.data.india_circle_rates import ZONE_MULTIPLIERS, get_circle_rate
from app.ml.valuation_model import PropIQModel
from app.services.comps_engine import find_comps, get_comp_stats
from app.services.enrichment import enrich_property
from app.services.llm_narration import \
    generate_credit_memo as _generate_credit_memo_async
from app.services.ltv_audit import calculate_ltv, log_assessment
from app.services.price_trends import generate_price_trend, get_trend_summary

# Module-level model cache for the worker process
_worker_model = None


def _get_worker_model() -> PropIQModel:
    global _worker_model
    if _worker_model is None:
        _worker_model = PropIQModel.load(str(settings.MODEL_DIR))
    return _worker_model


def _run_single_assessment(property_data: dict) -> dict:
    """
    Synchronous implementation of a single property assessment for workers.
    """
    try:
        t0 = time.time()
        request_id = str(uuid.uuid4())[:8].upper()

        locality = property_data["locality"]
        prop_type = property_data["prop_type"]
        size_sqft = property_data["size_sqft"]
        age_years = property_data["age_years"]
        floor_num = property_data.get("floor_num", 3)
        is_freehold = property_data.get("is_freehold", 1)
        is_rera_registered = property_data.get("is_rera_registered", 1)
        occupancy = property_data.get("occupancy", "self_occupied")
        rental_yield_pct = property_data.get("rental_yield_pct", 0.0)

        cr_data = get_circle_rate(locality, prop_type)
        zone_tier = cr_data["zone_tier"]

        # Run enrichment synchronously in worker
        enrichment = asyncio.run(enrich_property(locality, zone_tier=zone_tier))
        infra_score = enrichment.get(
            "infra_score", settings.INFRA_SCORE_FALLBACK.get(zone_tier, 50.0)
        )
        listing_density = enrichment.get("listing_density", 0.5)
        neighbourhood_quality_score = enrichment.get(
            "neighbourhood_quality_score", 58.0
        )
        location_mult = ZONE_MULTIPLIERS[zone_tier]["mid"]
        is_standard = 1 if prop_type in ["2bhk_apartment", "3bhk_apartment"] else 0
        comp_stats = get_comp_stats(locality, prop_type)

        model_input = {
            "locality": locality,
            "zone_tier": zone_tier,
            "prop_type": prop_type,
            "size_sqft": size_sqft,
            "age_years": age_years,
            "floor_num": floor_num,
            "is_freehold": is_freehold,
            "is_rera_registered": is_rera_registered,
            "has_clear_title": property_data.get("has_clear_title", 1),
            "has_encumbrance": property_data.get("has_encumbrance", 0),
            "has_legal_dispute": property_data.get("has_legal_dispute", 0),
            "zoning_approved": property_data.get("zoning_approved", 1),
            "rental_yield_pct": rental_yield_pct,
            "infra_score": infra_score,
            "listing_density": listing_density,
            "is_standard_config": is_standard,
            "circle_rate_per_sqft": cr_data["circle_rate_per_sqft"],
            "location_multiplier": location_mult,
            "neighbourhood_quality_score": neighbourhood_quality_score,
            "dominant_landuse": enrichment.get("dominant_landuse", "residential"),
            "months_of_inventory": enrichment.get("months_of_inventory", 6.0),
            "dominant_prop_type": comp_stats.get("dominant_prop_type"),
            "listing_velocity": enrichment.get("listing_velocity", 0.5),
            "transaction_indicator": enrichment.get("transaction_indicator", 0.5),
            "yoy_price_growth_pct": enrichment.get("yoy_price_growth_pct", 5.0),
        }

        prediction = _get_worker_model().predict(model_input)

        result = {
            "request_id": request_id,
            "locality": cr_data["locality"],
            "city": cr_data.get("city", "Pune"),
            "prop_type": prop_type,
            "size_sqft": size_sqft,
            "age_years": age_years,
            "floor_num": floor_num,
            "is_freehold": is_freehold,
            "is_rera_registered": is_rera_registered,
            "occupancy": occupancy,
            "rental_yield_pct": rental_yield_pct,
            **prediction,
            "enrichment": {
                "zone_tier": zone_tier,
                "circle_rate_per_sqft": cr_data["circle_rate_per_sqft"],
                "infra_score": infra_score,
                "listing_density": listing_density,
                "neighbourhood_quality_score": neighbourhood_quality_score,
                "city": cr_data.get("city", "Pune"),
                "dominant_landuse": enrichment.get("dominant_landuse", "residential"),
                "months_of_inventory": enrichment.get("months_of_inventory", 6.0),
                "yoy_price_growth_pct": enrichment.get("yoy_price_growth_pct", 5.0),
            },
            "cv_assessment": None,
        }

        # Comps and trends (synchronous in worker)
        comps = find_comps(locality, prop_type, size_sqft, age_years)
        trend_data = generate_price_trend(
            locality,
            zone_tier,
            cr_data.get("city", "Pune"),
            result["price_per_sqft_estimate"],
            months=24,
        )

        result["comps"] = comps
        result["comp_stats"] = get_comp_stats(locality, prop_type)
        result["price_trend"] = trend_data
        result["trend_summary"] = get_trend_summary(trend_data)
        result["ltv_analysis"] = calculate_ltv(
            result["market_value_mid"],
            result["distress_value_range"],
            cr_data["property_type_key"],
            zone_tier,
            result.get("risk_flags", []),
            result.get("resale_potential_index", 50.0),
            result.get("liquidity_profile", {}),
            result.get("distress_value_90d"),
        )
        result["credit_memo"] = None  # Skip LLM in batch workers to save API calls
        result["processing_time_ms"] = int((time.time() - t0) * 1000)
        result["status"] = "success"

        log_assessment(result, "/assess/batch")
        return result

    except Exception as e:
        import traceback

        traceback.print_exc()
        return {
            "locality": property_data.get("locality", "unknown"),
            "prop_type": property_data.get("prop_type", "unknown"),
            "status": "error",
            "error": str(e),
        }


@celery_app.task(bind=True, name="propiq.assess_single")
def assess_single_task(self, property_data: dict) -> dict:
    return _run_single_assessment(property_data)


@celery_app.task(bind=True, name="propiq.assess_batch")
def assess_batch_task(self, properties: list) -> dict:
    """
    Celery task that processes a batch of properties sequentially in a worker.
    Updates task state with progress for polling.
    """
    total = len(properties)
    results = []

    for idx, prop_data in enumerate(properties):
        self.update_state(
            state="PROGRESS",
            meta={"current": idx, "total": total, "percent": int((idx / total) * 100)},
        )
        result = _run_single_assessment(prop_data)
        results.append(result)

    success_count = sum(1 for r in results if r.get("status") == "success")
    return {
        "batch_size": total,
        "results": results,
        "success_count": success_count,
        "status": "completed",
    }


@celery_app.task(name="propiq.automated_health_check")
def automated_health_check():
    """
    Periodic task triggered by Celery Beat to run a full portfolio health check.
    """
    from app.services.chm_engine import run_portfolio_health_check

    # run_portfolio_health_check is async, so we use asyncio.run
    try:
        result = asyncio.run(run_portfolio_health_check())
        return result
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"status": "error", "error": str(e)}
