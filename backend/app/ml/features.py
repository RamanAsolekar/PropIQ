"""
PropIQ Canonical Feature Transform — the single source of truth.

WHY THIS EXISTS (train/serve skew fix, audit gap G4):
Previously the 22 model features were engineered in TWO places that disagreed:
  - training:  app/ml/data_generator.py  (e.g. developer_grade ~ random A/B/C)
  - serving:   PropIQModel._build_feature_row  (e.g. developer_grade hardcoded = 2)
That meant the model saw a different feature distribution in production than it
was trained on — silent accuracy loss.

Now BOTH training and serving call `build_feature_row()` here. There is exactly
one definition of every feature. This module is also the transform layer behind
the Feast feature store (see feature_repo/) so offline (training) and online
(serving) feature values are guaranteed identical.

The feature CONTRACT (order + names) is frozen in FEATURE_COLS and versioned via
FEATURE_SCHEMA_VERSION. Any change here is a breaking model-retrain event and
must bump the version + be recorded in the model registry.
"""

from __future__ import annotations

from typing import Dict

# ── Frozen feature contract ─────────────────────────────────────────────────
FEATURE_SCHEMA_VERSION = "2.0.0"

FEATURE_COLS = [
    "size_sqft",
    "age_years",
    "floor_num",
    "is_freehold",
    "is_rera_registered",
    "rental_yield_pct",
    "infra_score",
    "listing_density",
    "is_standard_config",
    "circle_rate_per_sqft",
    "location_multiplier",
    "age_depreciation_factor",
    "zone_tier_encoded",
    "neighbourhood_quality_score",
    "micro_market_cycle",
    "bid_ask_spread_pct",
    "buyer_pool_depth_index",
    "comp_velocity_score",
    "rental_cap_rate",
    "developer_grade",
    "floor_zone_premium",
]

PROP_TYPE_ENCODING = {
    "1bhk_apartment": 0,
    "2bhk_apartment": 1,
    "3bhk_apartment": 2,
    "4bhk_apartment": 3,
    "villa": 4,
    "shop": 5,
    "office": 6,
    "plot": 7,
    "warehouse": 8,
    "factory": 9,
}

ZONE_TIER_ENCODING = {"prime": 2, "mid": 1, "peripheral": 0}
ZONE_NEIGHBOURHOOD_BASE = {"prime": 78.0, "mid": 58.0, "peripheral": 40.0}
STANDARD_CONFIG_TYPES = {"2bhk_apartment", "3bhk_apartment"}


# ── Deterministic feature derivations (used at train AND serve) ─────────────


def age_depreciation_factor(age_years: float) -> float:
    """RBI-aligned depreciation: 1.25%/yr, floored at 55%."""
    return max(0.55, 1.0 - age_years * 0.0125)


def micro_market_cycle_encoded(yoy_price_growth_pct: float) -> int:
    """0=contraction, 1=stable, 2=expansion."""
    if yoy_price_growth_pct > 7.0:
        return 2
    if yoy_price_growth_pct < 2.0:
        return 0
    return 1


def bid_ask_spread_pct(months_of_inventory: float, yoy_price_growth_pct: float) -> float:
    return max(1.0, (months_of_inventory / 6.0) * 4.0 + max(0.0, 10.0 - yoy_price_growth_pct))


def buyer_pool_depth_index(listing_density: float, infra_score: float) -> float:
    return min(100.0, max(0.0, listing_density * 60.0 + infra_score * 0.4))


def comp_velocity_score(listing_velocity: float) -> float:
    return listing_velocity * 10.0


def rental_cap_rate(rental_yield_pct: float, age_years: float) -> float:
    """Cap rate as a percentage; 0 when not rented."""
    if rental_yield_pct <= 0:
        return 0.0
    return (rental_yield_pct / (1.0 + age_years * 0.02)) * 100.0


def floor_zone_premium(floor_num: int, zone_tier: str) -> float:
    return floor_num * (0.01 if zone_tier == "prime" else 0.005)


def build_feature_row(d: Dict) -> Dict[str, float]:
    """
    Canonical raw-inputs -> 22 model features. The ONLY place features are built.

    `d` must already carry the enriched signals (infra_score, listing_density,
    months_of_inventory, yoy_price_growth_pct, circle_rate_per_sqft, etc.) —
    these come from the enrichment layer at serve time and from the synthetic
    generator at train time, but the *transform* below is identical in both.
    """
    prop_type = str(d.get("prop_type", "2bhk_apartment")).lower().replace(" ", "_")
    zone_tier = d.get("zone_tier", "mid")
    age = float(d.get("age_years", 10))
    rental = float(d.get("rental_yield_pct", 0.0))
    infra = float(d.get("infra_score", 50.0))
    ld = float(d.get("listing_density", 0.5))
    floor_num = int(d.get("floor_num", 3))
    yoy = float(d.get("yoy_price_growth_pct", 5.0))
    moi = float(d.get("months_of_inventory", 6.0))
    listing_velocity = float(d.get("listing_velocity", 0.5))

    # developer_grade: derived from a real signal (RERA + zone) instead of a
    # train-only random draw or a serve-only hardcoded constant. Same at both ends.
    is_rera = int(d.get("is_rera_registered", 1))
    dev_grade = 3 if (is_rera and zone_tier == "prime") else (2 if is_rera else 1)

    is_standard = (
        int(d.get("is_standard_config"))
        if d.get("is_standard_config") is not None
        else (1 if prop_type in STANDARD_CONFIG_TYPES else 0)
    )

    return {
        "size_sqft": float(d.get("size_sqft", 800)),
        "age_years": age,
        "floor_num": floor_num,
        "is_freehold": int(d.get("is_freehold", 1)),
        "is_rera_registered": is_rera,
        "rental_yield_pct": rental,
        "infra_score": infra,
        "listing_density": ld,
        "is_standard_config": is_standard,
        "circle_rate_per_sqft": float(d.get("circle_rate_per_sqft", 7500)),
        "location_multiplier": float(d.get("location_multiplier", 1.4)),
        "age_depreciation_factor": age_depreciation_factor(age),
        "zone_tier_encoded": ZONE_TIER_ENCODING.get(zone_tier, 1),
        "neighbourhood_quality_score": float(
            d.get("neighbourhood_quality_score", ZONE_NEIGHBOURHOOD_BASE.get(zone_tier, 58.0))
        ),
        "micro_market_cycle": micro_market_cycle_encoded(yoy),
        "bid_ask_spread_pct": bid_ask_spread_pct(moi, yoy),
        "buyer_pool_depth_index": buyer_pool_depth_index(ld, infra),
        "comp_velocity_score": comp_velocity_score(listing_velocity),
        "rental_cap_rate": rental_cap_rate(rental, age),
        "developer_grade": dev_grade,
        "floor_zone_premium": floor_zone_premium(floor_num, zone_tier),
        "prop_type_encoded": PROP_TYPE_ENCODING.get(prop_type, 1),
    }


def feature_vector(d: Dict) -> Dict[str, float]:
    """Feature row including prop_type_encoded, ordered as the model expects."""
    row = build_feature_row(d)
    cols = FEATURE_COLS + ["prop_type_encoded"]
    return {c: row[c] for c in cols}
