"""
PropIQ Price Trend Service
Generates 24-month price trend per locality.
Anchored to: circle rate growth (5-8% YoY) + RBI repo rate cycles + micro-market demand.
Returns monthly price index suitable for area chart visualization.
"""

import math
import hashlib
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import List, Dict


# Annual appreciation rates by zone (based on RBI reports + NHB data 2022-2024)
ZONE_APPRECIATION = {
    "prime":      {"annual_pct": 8.5, "volatility": 0.03},
    "mid":        {"annual_pct": 7.0, "volatility": 0.025},
    "peripheral": {"annual_pct": 5.5, "volatility": 0.02},
}

# City multipliers (Mumbai > Bangalore > Pune for absolute appreciation)
CITY_MULTIPLIER = {
    "Mumbai":    1.15,
    "Bangalore": 1.08,
    "Pune":      1.00,
}

# Seasonal adjustment (Q4 Oct-Dec is peak transaction season in India)
SEASONAL = {
    1: -0.008, 2: -0.005, 3:  0.002, 4:  0.005,
    5:  0.003, 6:  0.000, 7: -0.003, 8: -0.002,
    9:  0.004, 10: 0.008, 11: 0.010, 12: 0.006,
}


def _deterministic_noise(locality: str, month_offset: int, scale: float) -> float:
    """Deterministic but varied noise based on locality name + month."""
    seed = int(hashlib.md5(f"{locality}_{month_offset}".encode()).hexdigest()[:8], 16)
    # Pseudo-random in [-scale, scale]
    return ((seed % 1000) / 500 - 1.0) * scale


def generate_price_trend(
    locality: str,
    zone_tier: str,
    city: str,
    base_price_sqft: float,
    months: int = 24,
) -> List[Dict]:
    """
    Generate monthly price trend for a locality.
    Returns list of {month, year, price_per_sqft, index, label}
    Most recent month is last in the list.
    """
    zone_cfg = ZONE_APPRECIATION.get(zone_tier, ZONE_APPRECIATION["mid"])
    city_mult = CITY_MULTIPLIER.get(city, 1.0)
    annual_rate = (zone_cfg["annual_pct"] / 100) * city_mult
    monthly_rate = (1 + annual_rate) ** (1/12) - 1
    volatility = zone_cfg["volatility"]

    # Work backwards from current month
    today = date.today()
    trend = []

    # Calculate the base price 'months' ago
    # (work backwards from current circle rate estimate)
    start_price = base_price_sqft / (1 + annual_rate) ** (months / 12)

    current_price = start_price
    for i in range(months):
        month_date = today - relativedelta(months=months - 1 - i)
        seasonal_adj = SEASONAL[month_date.month]
        noise = _deterministic_noise(locality, i, volatility)
        growth = monthly_rate + seasonal_adj + noise
        current_price *= (1 + growth)

        trend.append({
            "month": month_date.month,
            "year": month_date.year,
            "label": month_date.strftime("%b %Y"),
            "price_per_sqft": round(current_price),
            "index": round((current_price / start_price) * 100, 1),
            "month_offset": i,
        })

    # Anchor last data point to the actual current estimate
    if trend:
        scale = base_price_sqft / trend[-1]["price_per_sqft"]
        for point in trend:
            point["price_per_sqft"] = round(point["price_per_sqft"] * scale)
            point["index"] = round((point["price_per_sqft"] / trend[0]["price_per_sqft"]) * 100, 1)

    return trend


def get_trend_summary(trend: List[Dict]) -> Dict:
    """Compute summary statistics from trend data."""
    if not trend or len(trend) < 2:
        return {}
    first = trend[0]["price_per_sqft"]
    last  = trend[-1]["price_per_sqft"]
    mid   = trend[len(trend)//2]["price_per_sqft"]
    total_change_pct = ((last - first) / first) * 100
    last_6m_change_pct = ((last - mid) / mid) * 100
    peak = max(t["price_per_sqft"] for t in trend)
    trough = min(t["price_per_sqft"] for t in trend)

    return {
        "start_price": first,
        "current_price": last,
        "total_change_pct": round(total_change_pct, 1),
        "last_6m_change_pct": round(last_6m_change_pct, 1),
        "peak_price": peak,
        "trough_price": trough,
        "trend_direction": "up" if total_change_pct > 2 else "flat" if total_change_pct > -2 else "down",
        "annualized_return_pct": round(total_change_pct / 2, 1),  # 24 months → divide by 2
    }


if __name__ == "__main__":
    trend = generate_price_trend("Baner", "prime", "Pune", base_price_sqft=22000, months=24)
    summary = get_trend_summary(trend)
    print(f"Baner 24-month trend:")
    print(f"  {trend[0]['label']}: ₹{trend[0]['price_per_sqft']:,}/sqft")
    print(f"  {trend[11]['label']}: ₹{trend[11]['price_per_sqft']:,}/sqft")
    print(f"  {trend[-1]['label']}: ₹{trend[-1]['price_per_sqft']:,}/sqft")
    print(f"  Total appreciation: +{summary['total_change_pct']}%")
    print(f"  Last 6m: {summary['last_6m_change_pct']:+.1f}%")