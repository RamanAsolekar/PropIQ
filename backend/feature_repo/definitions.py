"""
PropIQ Feast feature definitions.

These register the canonical 22 model features (engineered by app/ml/features.py)
as a Feast FeatureView keyed on `locality`. The SAME transform produces offline
(training) and online (serving) values, so this store is the contract that
guarantees train/serve parity.

Run `feast apply` from this directory to materialize the registry. The rest of
PropIQ degrades gracefully if Feast is not installed (ENABLE_FEAST=false), so
this is additive, not a hard dependency.
"""

from datetime import timedelta

try:
    from feast import (Entity, FeatureView, Field, FileSource,
                       ValueType)
    from feast.types import Float32, Int64

    locality = Entity(
        name="locality",
        join_keys=["locality"],
        value_type=ValueType.STRING,
        description="Micro-market locality (e.g. Baner, Whitefield).",
    )

    # Offline source: the synthetic/real training table exported to parquet.
    property_source = FileSource(
        name="property_features_source",
        path="data/feast_source/property_features.parquet",
        timestamp_field="event_timestamp",
    )

    NUMERIC_FIELDS = [
        "size_sqft", "age_years", "floor_num", "is_freehold",
        "is_rera_registered", "rental_yield_pct", "infra_score",
        "listing_density", "is_standard_config", "circle_rate_per_sqft",
        "location_multiplier", "age_depreciation_factor", "zone_tier_encoded",
        "neighbourhood_quality_score", "micro_market_cycle", "bid_ask_spread_pct",
        "buyer_pool_depth_index", "comp_velocity_score", "rental_cap_rate",
        "developer_grade", "floor_zone_premium", "prop_type_encoded",
    ]

    property_features = FeatureView(
        name="property_valuation_features",
        entities=[locality],
        ttl=timedelta(days=90),
        schema=[Field(name=f, dtype=Float32) for f in NUMERIC_FIELDS],
        source=property_source,
        online=True,
        tags={"team": "collateral-ml", "schema_version": "2.0.0"},
    )
except Exception:  # pragma: no cover - Feast optional
    # Feast not installed — definitions are inert. PropIQ still runs.
    locality = None
    property_features = None
