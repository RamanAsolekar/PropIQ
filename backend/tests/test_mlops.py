"""
Tests for the PropIQ AIML/MLOps layer:
  - canonical feature transform (train/serve parity)
  - feature store schema validation
  - ensemble reconciliation + band calibration
  - drift PSI
  - model registry
"""

import numpy as np
import pytest


def test_canonical_features_train_serve_parity():
    """The same raw inputs must yield identical features (no skew)."""
    from app.ml.features import FEATURE_COLS, build_feature_row

    raw = {
        "prop_type": "2bhk_apartment", "zone_tier": "prime", "size_sqft": 850,
        "age_years": 8, "is_rera_registered": 1, "infra_score": 72,
        "listing_density": 0.7, "circle_rate_per_sqft": 10800,
        "location_multiplier": 2.1, "yoy_price_growth_pct": 8.5,
        "months_of_inventory": 4, "listing_velocity": 0.8,
    }
    a = build_feature_row(raw)
    b = build_feature_row(dict(raw))
    assert a == b
    # All canonical columns present
    for col in FEATURE_COLS:
        assert col in a
    # developer_grade is now DERIVED (RERA+prime -> 3), not hardcoded 2
    assert a["developer_grade"] == 3


def test_feature_store_schema_validation():
    from app.ml.feature_store import get_feature_store
    import pandas as pd

    store = get_feature_store()
    feats = store.get_serving_features({
        "prop_type": "3bhk_apartment", "zone_tier": "mid", "size_sqft": 1200,
        "age_years": 5,
    })
    assert len(feats) == len(store.feature_columns)
    # build_offline_frame rejects frames missing canonical cols
    with pytest.raises(ValueError):
        store.build_offline_frame(pd.DataFrame([{"size_sqft": 1}]))


def test_ensemble_reconciliation_weights_normalize():
    from app.ml.ensemble import reconcile

    avm = {"value": 10_000_000, "confidence": 0.8}
    comps = {"approach": "sales_comparison", "value": 11_000_000, "confidence": 0.7}
    income = {"approach": "income_capitalization", "value": 9_000_000, "confidence": 0.6}
    out = reconcile(avm, comps, income, "2bhk_apartment")
    assert 9_000_000 <= out["reconciled_value"] <= 11_000_000
    total_w = sum(c["normalized_weight"] for c in out["contributions"])
    assert abs(total_w - 1.0) < 0.01  # normalized weights rounded to 3dp
    assert 0.0 <= out["agreement_score"] <= 1.0


def test_band_calibration_widens_on_disagreement():
    from app.ml.ensemble import calibrate_band

    # Low agreement should widen the band vs high agreement
    wide = calibrate_band(90, 100, 110, agreement_score=0.2, reconciled_value=100)
    narrow = calibrate_band(90, 100, 110, agreement_score=0.95, reconciled_value=100)
    assert wide["band_widen_factor"] > narrow["band_widen_factor"]
    assert wide["calibrated_p10"] <= narrow["calibrated_p10"]
    assert wide["calibrated_p90"] >= narrow["calibrated_p90"]


def test_psi_detects_drift():
    from app.ml.monitoring import population_stability_index

    base = np.random.normal(0, 1, 2000)
    same = np.random.normal(0, 1, 1000)
    shifted = np.random.normal(3, 1, 1000)  # large mean shift
    assert population_stability_index(base, same) < 0.1
    assert population_stability_index(base, shifted) > 0.25


def test_registry_register_and_promote(tmp_path, monkeypatch):
    from app.ml import tracking

    monkeypatch.setattr(tracking, "REGISTRY_PATH", tmp_path / "registry.json")
    tracking.register_model_version("v1", {"cv_mape": 0.08}, "2.0.0", "hashA")
    tracking.register_model_version("v2", {"cv_mape": 0.07}, "2.0.0", "hashB")
    tracking.promote_to_production("v2")
    prod = tracking.get_production_version()
    assert prod["version"] == "v2"
    assert prod["stage"] == "Production"
