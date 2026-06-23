from pathlib import Path

import pytest
from app.ml.valuation_model import PropIQModel


@pytest.fixture(scope="module")
def trained_model():
    model_path = str(Path(__file__).parent.parent / "data" / "models")
    return PropIQModel.load(model_path)


def test_quantile_range_is_monotonic(trained_model):
    """Regression test: the P10/P50/P90 quantile models are trained
    independently and can cross (XGBoost quantile crossing), which previously
    surfaced inverted price ranges (mv_low > mv_mid > mv_high). The predict()
    path now sorts the quantiles, so the range must always be monotonic across
    a wide sweep of inputs."""
    crossed = []
    for size in (300, 800, 2000, 9000):
        for age in (1, 25, 60):
            for zone in ("prime", "mid", "peripheral"):
                r = trained_model.predict(
                    {
                        "size_sqft": size,
                        "age_years": age,
                        "zone_tier": zone,
                        "prop_type": "2bhk_apartment",
                        "circle_rate_per_sqft": 7500,
                    }
                )
                lo, hi = r["market_value_range"]
                mid = r["market_value_mid"]
                if not (lo <= mid <= hi):
                    crossed.append((zone, size, age, lo, mid, hi))
    assert not crossed, f"quantile crossing detected in {len(crossed)} cases: {crossed[:3]}"


def test_model_mape_pct_is_real_or_none(trained_model):
    """model_mape_pct should reflect the real validated MAPE (or be None) —
    never a fabricated constant."""
    r = trained_model.predict(
        {"size_sqft": 850, "age_years": 8, "zone_tier": "prime",
         "prop_type": "2bhk_apartment", "circle_rate_per_sqft": 10800}
    )
    mape = r["model_mape_pct"]
    if mape is not None:
        assert mape == round(trained_model.mape_validation * 100, 1)


def test_model_boundary_conditions():
    # Load an untrained or mock model, but since training requires data,
    # we'll test the boundaries of the helper methods without needing weights.
    model = PropIQModel()

    # Test property encoder mapping fallback
    row = model._build_feature_row({"prop_type": "unknown_type"})
    assert row["size_sqft"] == 800.0  # Should use defaults for missing fields

    # Test risk flags — pass all required positional args: d, anomaly_score, price_sqft, inc_val, mv
    flags = model._compute_risk_flags(
        {"age_years": 50},
        anomaly_score=-0.2,
        price_sqft=5000,
        inc_val=None,  # No income approach in this test
        mv=5000000,  # Mock market value
    )
    assert any(f["flag"] == "high_building_age" for f in flags)
    assert any(f["flag"] == "anomalous_input_combination" for f in flags)


def test_ltv_logic():
    from app.services.ltv_audit import calculate_ltv

    # Standard residential with no flags -> 70% LTV (PFL Conservative Cap for Prime Zone)
    ltv = calculate_ltv(
        10000000, [8000000, 9000000], "residential_apartment", "prime", []
    )
    assert ltv["recommended_ltv_pct"] == 70.0
    assert ltv["max_loan_amount"] == 7000000

    # Risk flags reduce LTV
    ltv_risk = calculate_ltv(
        10000000,
        [8000000, 9000000],
        "residential_apartment",
        "prime",
        [{"severity": "high"}],
    )
    assert ltv_risk["recommended_ltv_pct"] < 80.0
