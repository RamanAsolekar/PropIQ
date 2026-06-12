"""
Synthetic training data generator for PropIQ valuation model.
Anchored to Pune circle rates, validated design based on domain rules.
Generates ~22,400 records across all property/zone combinations.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Support both `python -m app.ml.data_generator` (from backend/) and direct run
_backend_dir = Path(__file__).parent.parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.data.india_circle_rates import ALL_CIRCLE_RATES, ZONE_MULTIPLIERS
# Canonical feature transform — training MUST derive model features the same way
# serving does, so we import the single source of truth instead of duplicating it.
from app.ml.features import build_feature_row

np.random.seed(42)

PROPERTY_CONFIGS = {
    "1bhk_apartment": {
        "size_range": (350, 600),
        "floor_range": (0, 15),
        "base_demand": 0.75,
    },
    "2bhk_apartment": {
        "size_range": (650, 1100),
        "floor_range": (0, 20),
        "base_demand": 1.0,
    },
    "3bhk_apartment": {
        "size_range": (1050, 1800),
        "floor_range": (0, 20),
        "base_demand": 0.85,
    },
    "4bhk_apartment": {
        "size_range": (1700, 3000),
        "floor_range": (0, 25),
        "base_demand": 0.6,
    },
    "villa": {"size_range": (2000, 5000), "floor_range": (0, 3), "base_demand": 0.5},
    "shop": {"size_range": (200, 1200), "floor_range": (0, 5), "base_demand": 0.7},
    "office": {"size_range": (500, 3000), "floor_range": (0, 20), "base_demand": 0.65},
    "plot": {"size_range": (1000, 8000), "floor_range": (0, 0), "base_demand": 0.55},
}

PROP_TYPE_TO_CIRCLE_KEY = {
    "1bhk_apartment": "residential_apartment",
    "2bhk_apartment": "residential_apartment",
    "3bhk_apartment": "residential_apartment",
    "4bhk_apartment": "residential_apartment",
    "villa": "residential_apartment",
    "shop": "commercial_shop",
    "office": "commercial_office",
    "plot": "residential_plot",
}


def age_depreciation(age_years: float) -> float:
    """RBI-aligned depreciation: 1.25%/year, floor at 55%."""
    return max(0.55, 1.0 - age_years * 0.0125)


def floor_premium(floor: int, prop_type: str) -> float:
    """Higher floors command premium for apartments."""
    if "apartment" not in prop_type and prop_type != "office":
        return 1.0
    if floor == 0:
        return 0.93
    elif floor <= 3:
        return 0.97
    elif floor <= 10:
        return 1.0 + floor * 0.004
    else:
        return 1.04 + (floor - 10) * 0.002


def infra_premium(infra_score: float) -> float:
    """Infrastructure proximity premium: up to +32%."""
    return 1.0 + (infra_score / 100.0) * 0.32


def rental_yield_signal(prop_type: str, zone_tier: str) -> float:
    """Rental yield affects investor demand and resale certainty."""
    base = {"prime": 3.8, "mid": 3.2, "peripheral": 2.6}[zone_tier]
    noise = np.random.normal(0, 0.3)
    return max(1.5, base + noise)


def generate_record(locality: str, zone_data: dict, prop_type: str) -> dict:
    config = PROPERTY_CONFIGS[prop_type]
    circle_key = PROP_TYPE_TO_CIRCLE_KEY.get(prop_type, "residential_apartment")
    zone_tier = zone_data["zone_tier"]
    circle_rate = zone_data[circle_key]

    # Property attributes
    size_sqft = np.random.uniform(*config["size_range"])
    age_years = np.random.choice(
        [np.random.uniform(0, 5), np.random.uniform(5, 15), np.random.uniform(15, 40)],
        p=[0.3, 0.45, 0.25],
    )
    floor_num = int(np.random.uniform(*config["floor_range"]))

    # Location signals
    mult_range = ZONE_MULTIPLIERS[zone_tier]
    location_mult = np.random.triangular(
        mult_range["min"], mult_range["mid"], mult_range["max"]
    )
    infra_score = np.random.beta(2, 2) * 100
    if zone_tier == "prime":
        infra_score = min(100, infra_score + 25)
    elif zone_tier == "peripheral":
        infra_score = max(0, infra_score - 20)

    # Neighbourhood quality score
    nq_base = {"prime": 78.0, "mid": 58.0, "peripheral": 40.0}[zone_tier]
    nq_score = nq_base + (infra_score - 50) * 0.20 + np.random.normal(0, 6)
    neighbourhood_quality_score = round(min(100, max(10, nq_score)), 1)

    # Legal and occupancy
    is_freehold = np.random.choice([1, 0], p=[0.82, 0.18])
    is_rera_registered = np.random.choice([1, 0], p=[0.75, 0.25])
    occupancy = np.random.choice(
        ["self_occupied", "rented", "vacant"], p=[0.55, 0.30, 0.15]
    )
    rental_yield = (
        rental_yield_signal(prop_type, zone_tier) if occupancy == "rented" else 0.0
    )

    # Market signals & Deep Liquidity Features (RAW signals — legitimate to
    # synthesize. The MODEL features are derived from these via the canonical
    # transform below, exactly as serving does.)
    listing_density = np.random.uniform(0.2, 0.9)
    if zone_tier == "prime":
        listing_density = min(1.0, listing_density + 0.2)
    is_standard_config = 1 if prop_type in ["2bhk_apartment", "3bhk_apartment"] else 0

    micro_market_cycle = np.random.choice(
        ["expansion", "stable", "contraction"], p=[0.3, 0.5, 0.2]
    )
    # Raw market signals that the canonical transform consumes
    yoy_price_growth_pct = {
        "expansion": np.random.uniform(7.5, 14.0),
        "stable": np.random.uniform(3.0, 6.5),
        "contraction": np.random.uniform(-2.0, 1.5),
    }[micro_market_cycle]
    months_of_inventory = (
        np.random.uniform(10.0, 24.0)
        if micro_market_cycle == "contraction"
        else np.random.uniform(2.0, 9.0)
    )
    listing_velocity = (
        np.random.uniform(0.5, 1.0)
        if zone_tier == "prime"
        else np.random.uniform(0.15, 0.7)
    )

    depreciation = age_depreciation(age_years)

    # ── Canonical model features (identical engineering to serving) ─────────
    feat = build_feature_row(
        {
            "prop_type": prop_type,
            "zone_tier": zone_tier,
            "size_sqft": size_sqft,
            "age_years": age_years,
            "floor_num": floor_num,
            "is_freehold": is_freehold,
            "is_rera_registered": is_rera_registered,
            "rental_yield_pct": rental_yield,
            "infra_score": infra_score,
            "listing_density": listing_density,
            "is_standard_config": is_standard_config,
            "circle_rate_per_sqft": circle_rate,
            "location_multiplier": location_mult,
            "neighbourhood_quality_score": neighbourhood_quality_score,
            "yoy_price_growth_pct": yoy_price_growth_pct,
            "months_of_inventory": months_of_inventory,
            "listing_velocity": listing_velocity,
        }
    )

    # Compute modifiers
    floor_factor = floor_premium(floor_num, prop_type)
    infra_factor = infra_premium(infra_score)
    legal_factor = 1.0 if is_freehold else 0.88
    rera_factor = 1.0 if is_rera_registered else 0.94
    demand_factor = config["base_demand"]
    rental_factor = 1.0 + (rental_yield / 100.0) * 0.8 if rental_yield > 0 else 1.0
    cycle_factor = (
        1.05
        if micro_market_cycle == "expansion"
        else (0.95 if micro_market_cycle == "contraction" else 1.0)
    )

    # Market value formula (circle rate anchored)
    noise = np.random.normal(1.0, 0.07)
    price_per_sqft = (
        circle_rate
        * location_mult
        * depreciation
        * floor_factor
        * infra_factor
        * legal_factor
        * rera_factor
        * demand_factor
        * rental_factor
        * cycle_factor
        * noise
    )
    total_market_value = price_per_sqft * size_sqft

    # Liquidity score (0-100) — uses canonical-feature values from `feat`
    liquidity_raw = (
        (infra_score * 0.20)
        + (is_standard_config * 100 * 0.15)
        + (is_freehold * 100 * 0.15)
        + (listing_density * 100 * 0.10)
        + (feat["buyer_pool_depth_index"] * 0.20)
        + (feat["comp_velocity_score"] * 10 * 0.10)
        + (max(0, 100 - age_years * 1.5) * 0.10)
    )
    if micro_market_cycle == "contraction":
        liquidity_raw -= 15
    liquidity_score = min(100, max(0, liquidity_raw + np.random.normal(0, 3)))

    # Time to liquidate (days)
    if liquidity_score >= 75:
        ttl_min, ttl_max = int(np.random.uniform(15, 30)), int(
            np.random.uniform(35, 60)
        )
    elif liquidity_score >= 50:
        ttl_min, ttl_max = int(np.random.uniform(40, 70)), int(
            np.random.uniform(75, 120)
        )
    else:
        ttl_min, ttl_max = int(np.random.uniform(90, 120)), int(
            np.random.uniform(130, 250)
        )

    absorption_rate = round(30.0 / max(1, ttl_max) * 100, 1)

    # Distress value
    if liquidity_score >= 75:
        distress_discount = np.random.uniform(0.82, 0.90)
    elif liquidity_score >= 50:
        distress_discount = np.random.uniform(0.72, 0.82)
    else:
        distress_discount = np.random.uniform(0.55, 0.70)
    distress_value = total_market_value * distress_discount

    return {
        # Inputs
        "locality": locality,
        "zone_tier": zone_tier,
        "prop_type": prop_type,
        "size_sqft": round(size_sqft, 1),
        "age_years": round(age_years, 1),
        "floor_num": floor_num,
        "is_freehold": is_freehold,
        "is_rera_registered": is_rera_registered,
        "occupancy": occupancy,
        "rental_yield_pct": round(rental_yield, 2),
        "infra_score": round(infra_score, 1),
        "listing_density": round(listing_density, 3),
        "is_standard_config": is_standard_config,
        "circle_rate_per_sqft": circle_rate,
        # Extended + derived model features — emitted from the CANONICAL
        # transform (`feat`) so the training CSV columns are byte-for-byte the
        # same engineering the model receives at serve time.
        "micro_market_cycle": feat["micro_market_cycle"],
        "bid_ask_spread_pct": round(feat["bid_ask_spread_pct"], 2),
        "buyer_pool_depth_index": round(feat["buyer_pool_depth_index"], 1),
        "comp_velocity_score": round(feat["comp_velocity_score"], 2),
        "rental_cap_rate": round(feat["rental_cap_rate"], 3),
        "developer_grade": feat["developer_grade"],
        "floor_zone_premium": round(feat["floor_zone_premium"], 3),
        "location_multiplier": round(feat["location_multiplier"], 3),
        "age_depreciation_factor": round(feat["age_depreciation_factor"], 3),
        "zone_tier_encoded": feat["zone_tier_encoded"],
        "neighbourhood_quality_score": neighbourhood_quality_score,
        # Raw market signals (kept for monitoring / Feast offline store)
        "yoy_price_growth_pct": round(yoy_price_growth_pct, 2),
        "months_of_inventory": round(months_of_inventory, 1),
        "listing_velocity": round(listing_velocity, 3),
        # Targets
        "price_per_sqft": round(price_per_sqft, 1),
        "total_market_value": round(total_market_value, 0),
        "distress_value": round(distress_value, 0),
        "liquidity_score": round(liquidity_score, 1),
        "absorption_rate": absorption_rate,
        "ttl_min_days": ttl_min,
        "ttl_max_days": ttl_max,
        "distress_discount": round(distress_discount, 3),
    }


def generate_dataset(n_per_combination: int = 16) -> pd.DataFrame:
    records = []
    for locality, zone_data in ALL_CIRCLE_RATES.items():
        for prop_type in PROPERTY_CONFIGS.keys():
            for _ in range(n_per_combination):
                records.append(generate_record(locality, zone_data, prop_type))
    df = pd.DataFrame(records)
    print(
        f"Generated {len(df)} records across {df['locality'].nunique()} localities, {df['prop_type'].nunique()} property types"
    )
    print(
        f"Price range: INR {df['total_market_value'].min()/1e6:.1f}L - INR {df['total_market_value'].max()/1e6:.1f}Cr"
    )
    print(
        f"Liquidity score range: {df['liquidity_score'].min():.1f} - {df['liquidity_score'].max():.1f}"
    )
    return df


if __name__ == "__main__":
    out = Path(__file__).parent.parent.parent / "data" / "processed"
    out.mkdir(parents=True, exist_ok=True)
    df = generate_dataset(n_per_combination=16)
    df.to_csv(out / "synthetic_training_data.csv", index=False)
    print(f"Saved to {out / 'synthetic_training_data.csv'}")
