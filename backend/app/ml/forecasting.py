"""
PropIQ Price Forecasting — learned/statistical horizon forecasting.

Replaces the "deterministic formula is the output" approach: the existing
`generate_price_trend` becomes the HISTORY feed, and this module fits a model on
that history to project future prices WITH a confidence band.

Engine tiers (auto):
  1. prophet      — additive trend+seasonality with CI (if installed)
  2. statsmodels  — Holt-Winters exponential smoothing (if installed)
  3. numpy        — least-squares linear trend + monthly seasonal + residual CI
                    (always available fallback)
"""

from __future__ import annotations

import logging
from typing import Dict, List

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


def _history_series(locality: str, prop_type: str, months: int = 36) -> List[Dict]:
    from app.data.india_circle_rates import ZONE_MULTIPLIERS, get_circle_rate
    from app.services.price_trends import generate_price_trend

    cr = get_circle_rate(locality, prop_type)
    base = cr["circle_rate_per_sqft"] * ZONE_MULTIPLIERS[cr["zone_tier"]]["mid"]
    return generate_price_trend(locality, cr["zone_tier"], cr.get("city", "Pune"),
                                base, months=months)


def _resolve_engine() -> str:
    want = settings.FORECAST_ENGINE
    if want == "prophet":
        try:
            import prophet  # noqa
            return "prophet"
        except Exception:
            pass
    if want in ("statsmodels", "auto"):
        try:
            import statsmodels  # noqa
            return "statsmodels"
        except Exception:
            pass
    if want == "auto":
        try:
            import prophet  # noqa
            return "prophet"
        except Exception:
            try:
                import statsmodels  # noqa
                return "statsmodels"
            except Exception:
                return "numpy"
    return "numpy"


def _numpy_forecast(prices: np.ndarray, horizon: int) -> Dict:
    """Least-squares linear trend + month-of-year seasonal + residual-based CI."""
    n = len(prices)
    t = np.arange(n)
    # Linear trend
    A = np.vstack([t, np.ones(n)]).T
    slope, intercept = np.linalg.lstsq(A, prices, rcond=None)[0]
    trend = slope * t + intercept
    # Seasonal component (period 12)
    resid = prices - trend
    season = np.zeros(12)
    for m in range(12):
        idx = np.arange(m, n, 12)
        if len(idx):
            season[m] = resid[idx].mean()
    detrended_resid = resid - season[np.arange(n) % 12]
    sigma = float(np.std(detrended_resid)) if n > 2 else float(np.std(prices)) * 0.05

    fut_t = np.arange(n, n + horizon)
    fut_trend = slope * fut_t + intercept
    fut_season = season[fut_t % 12]
    fut = fut_trend + fut_season
    # Widening CI: sqrt(h) growth
    ci = 1.96 * sigma * np.sqrt(np.arange(1, horizon + 1))
    return {"forecast": fut, "ci_low": fut - ci, "ci_high": fut + ci, "sigma": sigma}


def _statsmodels_forecast(prices: np.ndarray, horizon: int) -> Dict:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    seasonal = "add" if len(prices) >= 24 else None
    sp = 12 if seasonal else None
    model = ExponentialSmoothing(prices, trend="add", seasonal=seasonal,
                                 seasonal_periods=sp).fit()
    fut = np.asarray(model.forecast(horizon))
    resid = prices - np.asarray(model.fittedvalues)
    sigma = float(np.std(resid))
    ci = 1.96 * sigma * np.sqrt(np.arange(1, horizon + 1))
    return {"forecast": fut, "ci_low": fut - ci, "ci_high": fut + ci, "sigma": sigma}


def _prophet_forecast(history: List[Dict], horizon: int) -> Dict:
    import pandas as pd
    from prophet import Prophet

    df = pd.DataFrame({
        "ds": pd.to_datetime([f"{h['year']}-{h['month']:02d}-01" for h in history]),
        "y": [h["price_per_sqft"] for h in history],
    })
    m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    m.fit(df)
    future = m.make_future_dataframe(periods=horizon, freq="MS")
    fc = m.predict(future).tail(horizon)
    return {"forecast": fc["yhat"].values, "ci_low": fc["yhat_lower"].values,
            "ci_high": fc["yhat_upper"].values, "sigma": None}


def forecast_locality(locality: str, prop_type: str = "2bhk_apartment",
                      horizon_months: int = 6) -> Dict:
    """Forecast price/sqft for a locality. Never raises — degrades to numpy."""
    history = _history_series(locality, prop_type, months=36)
    prices = np.array([h["price_per_sqft"] for h in history], dtype=float)
    engine = _resolve_engine()

    try:
        if engine == "prophet":
            res = _prophet_forecast(history, horizon_months)
        elif engine == "statsmodels":
            res = _statsmodels_forecast(prices, horizon_months)
        else:
            res = _numpy_forecast(prices, horizon_months)
    except Exception as e:
        logger.warning("Forecast engine %s failed (%s) — numpy fallback.", engine, e)
        engine = "numpy"
        res = _numpy_forecast(prices, horizon_months)

    last_price = float(prices[-1])
    fc = [round(float(x)) for x in res["forecast"]]
    pct_6m = round((fc[min(5, len(fc) - 1)] - last_price) / last_price * 100, 1) if fc else 0.0
    momentum = "rising" if pct_6m > 1.5 else "falling" if pct_6m < -1.5 else "flat"

    return {
        "locality": locality,
        "prop_type": prop_type,
        "engine": engine,
        "history": [{"label": h["label"], "price_per_sqft": h["price_per_sqft"]}
                    for h in history[-12:]],
        "forecast": [
            {"month_ahead": i + 1, "price_per_sqft": fc[i],
             "ci_low": round(float(res["ci_low"][i])),
             "ci_high": round(float(res["ci_high"][i]))}
            for i in range(len(fc))
        ],
        "current_price_per_sqft": round(last_price),
        "forecast_pct_change": pct_6m,
        "momentum_signal": momentum,
    }
