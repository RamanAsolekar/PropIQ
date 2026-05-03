"""
India Circle Rates — IGR/Guidance Value Data
Cities: Pune, Mumbai, Bangalore
Source: State registration authority ready-reckoner 2024-25
"""

# ── Pune ───────────────────────────────────────────────────────────────────
PUNE_RATES = {
    "Koregaon Park": {
        "zone_tier": "prime",
        "city": "Pune",
        "lat": 18.5362,
        "lon": 73.8938,
        "residential_apartment": 12500,
        "residential_plot": 18000,
        "commercial_shop": 22000,
        "commercial_office": 16000,
        "industrial": 8000,
    },
    "Shivajinagar": {
        "zone_tier": "prime",
        "city": "Pune",
        "lat": 18.5308,
        "lon": 73.8474,
        "residential_apartment": 13000,
        "residential_plot": 19000,
        "commercial_shop": 24000,
        "commercial_office": 17000,
        "industrial": 9000,
    },
    "Baner": {
        "zone_tier": "prime",
        "city": "Pune",
        "lat": 18.5590,
        "lon": 73.7868,
        "residential_apartment": 10800,
        "residential_plot": 14000,
        "commercial_shop": 18000,
        "commercial_office": 13500,
        "industrial": 6500,
    },
    "Kothrud": {
        "zone_tier": "prime",
        "city": "Pune",
        "lat": 18.5074,
        "lon": 73.8077,
        "residential_apartment": 11200,
        "residential_plot": 15000,
        "commercial_shop": 19000,
        "commercial_office": 14000,
        "industrial": 7000,
    },
    "Aundh": {
        "zone_tier": "prime",
        "city": "Pune",
        "lat": 18.5578,
        "lon": 73.8073,
        "residential_apartment": 11500,
        "residential_plot": 15500,
        "commercial_shop": 20000,
        "commercial_office": 14500,
        "industrial": 7500,
    },
    "Viman Nagar": {
        "zone_tier": "prime",
        "city": "Pune",
        "lat": 18.5679,
        "lon": 73.9143,
        "residential_apartment": 10500,
        "residential_plot": 14500,
        "commercial_shop": 18500,
        "commercial_office": 13000,
        "industrial": 6800,
    },
    "Kalyani Nagar": {
        "zone_tier": "prime",
        "city": "Pune",
        "lat": 18.5456,
        "lon": 73.9010,
        "residential_apartment": 11000,
        "residential_plot": 15000,
        "commercial_shop": 19500,
        "commercial_office": 14000,
        "industrial": 7000,
    },
    "Magarpatta": {
        "zone_tier": "prime",
        "city": "Pune",
        "lat": 18.5114,
        "lon": 73.9274,
        "residential_apartment": 10200,
        "residential_plot": 13500,
        "commercial_shop": 18000,
        "commercial_office": 13000,
        "industrial": 6500,
    },
    "Bavdhan": {
        "zone_tier": "prime",
        "city": "Pune",
        "lat": 18.5196,
        "lon": 73.7805,
        "residential_apartment": 10000,
        "residential_plot": 13000,
        "commercial_shop": 17500,
        "commercial_office": 12500,
        "industrial": 6200,
    },
    "Wakad": {
        "zone_tier": "mid",
        "city": "Pune",
        "lat": 18.5975,
        "lon": 73.7614,
        "residential_apartment": 8200,
        "residential_plot": 10500,
        "commercial_shop": 13000,
        "commercial_office": 10000,
        "industrial": 5500,
    },
    "Hinjewadi": {
        "zone_tier": "mid",
        "city": "Pune",
        "lat": 18.5912,
        "lon": 73.7380,
        "residential_apartment": 7800,
        "residential_plot": 9800,
        "commercial_shop": 12000,
        "commercial_office": 9500,
        "industrial": 5800,
    },
    "Hadapsar": {
        "zone_tier": "mid",
        "city": "Pune",
        "lat": 18.5018,
        "lon": 73.9260,
        "residential_apartment": 7200,
        "residential_plot": 9000,
        "commercial_shop": 11500,
        "commercial_office": 9000,
        "industrial": 5200,
    },
    "Pimpri": {
        "zone_tier": "mid",
        "city": "Pune",
        "lat": 18.6279,
        "lon": 73.7997,
        "residential_apartment": 7500,
        "residential_plot": 9500,
        "commercial_shop": 12500,
        "commercial_office": 9800,
        "industrial": 5600,
    },
    "Chinchwad": {
        "zone_tier": "mid",
        "city": "Pune",
        "lat": 18.6436,
        "lon": 73.7983,
        "residential_apartment": 7800,
        "residential_plot": 10000,
        "commercial_shop": 13000,
        "commercial_office": 10000,
        "industrial": 5800,
    },
    "Katraj": {
        "zone_tier": "mid",
        "city": "Pune",
        "lat": 18.4601,
        "lon": 73.8669,
        "residential_apartment": 6800,
        "residential_plot": 8500,
        "commercial_shop": 11000,
        "commercial_office": 8500,
        "industrial": 4800,
    },
    "Kondhwa": {
        "zone_tier": "mid",
        "city": "Pune",
        "lat": 18.4672,
        "lon": 73.8924,
        "residential_apartment": 6500,
        "residential_plot": 8200,
        "commercial_shop": 10500,
        "commercial_office": 8000,
        "industrial": 4600,
    },
    "Nibm": {
        "zone_tier": "mid",
        "city": "Pune",
        "lat": 18.4608,
        "lon": 73.8980,
        "residential_apartment": 6200,
        "residential_plot": 7800,
        "commercial_shop": 10000,
        "commercial_office": 7800,
        "industrial": 4400,
    },
    "Dhanori": {
        "zone_tier": "mid",
        "city": "Pune",
        "lat": 18.5896,
        "lon": 73.9155,
        "residential_apartment": 6000,
        "residential_plot": 7500,
        "commercial_shop": 9500,
        "commercial_office": 7500,
        "industrial": 4200,
    },
    "Vishrantwadi": {
        "zone_tier": "mid",
        "city": "Pune",
        "lat": 18.5810,
        "lon": 73.9010,
        "residential_apartment": 6400,
        "residential_plot": 8000,
        "commercial_shop": 10200,
        "commercial_office": 8000,
        "industrial": 4500,
    },
    "Ravet": {
        "zone_tier": "mid",
        "city": "Pune",
        "lat": 18.6434,
        "lon": 73.7449,
        "residential_apartment": 7000,
        "residential_plot": 8800,
        "commercial_shop": 11200,
        "commercial_office": 8800,
        "industrial": 5000,
    },
    "Wagholi": {
        "zone_tier": "peripheral",
        "city": "Pune",
        "lat": 18.5617,
        "lon": 73.9757,
        "residential_apartment": 5500,
        "residential_plot": 7000,
        "commercial_shop": 9000,
        "commercial_office": 7000,
        "industrial": 4000,
    },
    "Talegaon": {
        "zone_tier": "peripheral",
        "city": "Pune",
        "lat": 18.7332,
        "lon": 73.6723,
        "residential_apartment": 4800,
        "residential_plot": 6200,
        "commercial_shop": 8000,
        "commercial_office": 6000,
        "industrial": 3500,
    },
    "Chakan": {
        "zone_tier": "peripheral",
        "city": "Pune",
        "lat": 18.7601,
        "lon": 73.8637,
        "residential_apartment": 4500,
        "residential_plot": 5800,
        "commercial_shop": 7500,
        "commercial_office": 5500,
        "industrial": 4500,
    },
    "Ambegaon": {
        "zone_tier": "peripheral",
        "city": "Pune",
        "lat": 18.4489,
        "lon": 73.8526,
        "residential_apartment": 5200,
        "residential_plot": 6500,
        "commercial_shop": 8500,
        "commercial_office": 6500,
        "industrial": 3800,
    },
    "Undri": {
        "zone_tier": "peripheral",
        "city": "Pune",
        "lat": 18.4524,
        "lon": 73.9009,
        "residential_apartment": 5000,
        "residential_plot": 6200,
        "commercial_shop": 8000,
        "commercial_office": 6200,
        "industrial": 3600,
    },
    "Fursungi": {
        "zone_tier": "peripheral",
        "city": "Pune",
        "lat": 18.4842,
        "lon": 73.9279,
        "residential_apartment": 4600,
        "residential_plot": 5800,
        "commercial_shop": 7500,
        "commercial_office": 5800,
        "industrial": 3300,
    },
}

# ── Mumbai ─────────────────────────────────────────────────────────────────
MUMBAI_RATES = {
    "Bandra West": {
        "zone_tier": "prime",
        "city": "Mumbai",
        "lat": 19.0596,
        "lon": 72.8295,
        "residential_apartment": 42000,
        "residential_plot": 65000,
        "commercial_shop": 75000,
        "commercial_office": 55000,
        "industrial": 20000,
    },
    "Worli": {
        "zone_tier": "prime",
        "city": "Mumbai",
        "lat": 19.0176,
        "lon": 72.8178,
        "residential_apartment": 38000,
        "residential_plot": 58000,
        "commercial_shop": 68000,
        "commercial_office": 50000,
        "industrial": 18000,
    },
    "Powai": {
        "zone_tier": "prime",
        "city": "Mumbai",
        "lat": 19.1197,
        "lon": 72.9051,
        "residential_apartment": 22000,
        "residential_plot": 32000,
        "commercial_shop": 40000,
        "commercial_office": 30000,
        "industrial": 12000,
    },
    "Andheri West": {
        "zone_tier": "prime",
        "city": "Mumbai",
        "lat": 19.1313,
        "lon": 72.8258,
        "residential_apartment": 20000,
        "residential_plot": 28000,
        "commercial_shop": 35000,
        "commercial_office": 26000,
        "industrial": 10000,
    },
    "Andheri East": {
        "zone_tier": "mid",
        "city": "Mumbai",
        "lat": 19.1136,
        "lon": 72.8697,
        "residential_apartment": 16000,
        "residential_plot": 22000,
        "commercial_shop": 28000,
        "commercial_office": 21000,
        "industrial": 9000,
    },
    "Thane": {
        "zone_tier": "mid",
        "city": "Mumbai",
        "lat": 19.2183,
        "lon": 72.9781,
        "residential_apartment": 12000,
        "residential_plot": 16000,
        "commercial_shop": 20000,
        "commercial_office": 15000,
        "industrial": 7500,
    },
    "Navi Mumbai": {
        "zone_tier": "mid",
        "city": "Mumbai",
        "lat": 19.0368,
        "lon": 73.0158,
        "residential_apartment": 11000,
        "residential_plot": 14500,
        "commercial_shop": 18000,
        "commercial_office": 13500,
        "industrial": 7000,
    },
    "Dadar": {
        "zone_tier": "prime",
        "city": "Mumbai",
        "lat": 19.0186,
        "lon": 72.8430,
        "residential_apartment": 28000,
        "residential_plot": 42000,
        "commercial_shop": 55000,
        "commercial_office": 38000,
        "industrial": 15000,
    },
    "Borivali": {
        "zone_tier": "mid",
        "city": "Mumbai",
        "lat": 19.2288,
        "lon": 72.8563,
        "residential_apartment": 14000,
        "residential_plot": 19000,
        "commercial_shop": 24000,
        "commercial_office": 18000,
        "industrial": 8500,
    },
    "Goregaon": {
        "zone_tier": "mid",
        "city": "Mumbai",
        "lat": 19.1663,
        "lon": 72.8526,
        "residential_apartment": 15000,
        "residential_plot": 20000,
        "commercial_shop": 25000,
        "commercial_office": 19000,
        "industrial": 9000,
    },
    "Malad": {
        "zone_tier": "mid",
        "city": "Mumbai",
        "lat": 19.1872,
        "lon": 72.8484,
        "residential_apartment": 14500,
        "residential_plot": 19500,
        "commercial_shop": 24500,
        "commercial_office": 18500,
        "industrial": 8800,
    },
    "Kandivali": {
        "zone_tier": "mid",
        "city": "Mumbai",
        "lat": 19.2071,
        "lon": 72.8546,
        "residential_apartment": 13500,
        "residential_plot": 18000,
        "commercial_shop": 22500,
        "commercial_office": 17000,
        "industrial": 8000,
    },
    "Kurla": {
        "zone_tier": "mid",
        "city": "Mumbai",
        "lat": 19.0726,
        "lon": 72.8826,
        "residential_apartment": 13000,
        "residential_plot": 17500,
        "commercial_shop": 22000,
        "commercial_office": 16500,
        "industrial": 8000,
    },
    "Ghatkopar": {
        "zone_tier": "mid",
        "city": "Mumbai",
        "lat": 19.0867,
        "lon": 72.9082,
        "residential_apartment": 14000,
        "residential_plot": 18500,
        "commercial_shop": 23500,
        "commercial_office": 17500,
        "industrial": 8500,
    },
    "Mulund": {
        "zone_tier": "mid",
        "city": "Mumbai",
        "lat": 19.1726,
        "lon": 72.9560,
        "residential_apartment": 13000,
        "residential_plot": 17000,
        "commercial_shop": 21500,
        "commercial_office": 16000,
        "industrial": 7800,
    },
    "Chembur": {
        "zone_tier": "mid",
        "city": "Mumbai",
        "lat": 19.0522,
        "lon": 72.8994,
        "residential_apartment": 15500,
        "residential_plot": 21000,
        "commercial_shop": 27000,
        "commercial_office": 20000,
        "industrial": 9500,
    },
    "Mira Road": {
        "zone_tier": "peripheral",
        "city": "Mumbai",
        "lat": 19.2815,
        "lon": 72.8656,
        "residential_apartment": 8500,
        "residential_plot": 11000,
        "commercial_shop": 14000,
        "commercial_office": 10500,
        "industrial": 5500,
    },
    "Virar": {
        "zone_tier": "peripheral",
        "city": "Mumbai",
        "lat": 19.4647,
        "lon": 72.8108,
        "residential_apartment": 5500,
        "residential_plot": 7200,
        "commercial_shop": 9000,
        "commercial_office": 7000,
        "industrial": 4000,
    },
    "Panvel": {
        "zone_tier": "peripheral",
        "city": "Mumbai",
        "lat": 18.9894,
        "lon": 73.1175,
        "residential_apartment": 6500,
        "residential_plot": 8500,
        "commercial_shop": 11000,
        "commercial_office": 8500,
        "industrial": 5000,
    },
    "Kharghar": {
        "zone_tier": "mid",
        "city": "Mumbai",
        "lat": 19.0473,
        "lon": 73.0687,
        "residential_apartment": 10000,
        "residential_plot": 13500,
        "commercial_shop": 17000,
        "commercial_office": 12500,
        "industrial": 6500,
    },
}

# ── Bangalore ──────────────────────────────────────────────────────────────
BANGALORE_RATES = {
    "Koramangala": {
        "zone_tier": "prime",
        "city": "Bangalore",
        "lat": 12.9279,
        "lon": 77.6271,
        "residential_apartment": 14500,
        "residential_plot": 22000,
        "commercial_shop": 28000,
        "commercial_office": 20000,
        "industrial": 9000,
    },
    "Indiranagar": {
        "zone_tier": "prime",
        "city": "Bangalore",
        "lat": 12.9716,
        "lon": 77.6412,
        "residential_apartment": 13000,
        "residential_plot": 19000,
        "commercial_shop": 25000,
        "commercial_office": 18000,
        "industrial": 8500,
    },
    "Whitefield": {
        "zone_tier": "prime",
        "city": "Bangalore",
        "lat": 12.9698,
        "lon": 77.7499,
        "residential_apartment": 10000,
        "residential_plot": 14000,
        "commercial_shop": 18000,
        "commercial_office": 14000,
        "industrial": 7000,
    },
    "HSR Layout": {
        "zone_tier": "prime",
        "city": "Bangalore",
        "lat": 12.9082,
        "lon": 77.6476,
        "residential_apartment": 11500,
        "residential_plot": 16000,
        "commercial_shop": 21000,
        "commercial_office": 15500,
        "industrial": 7500,
    },
    "Jayanagar": {
        "zone_tier": "prime",
        "city": "Bangalore",
        "lat": 12.9259,
        "lon": 77.5937,
        "residential_apartment": 12500,
        "residential_plot": 18000,
        "commercial_shop": 24000,
        "commercial_office": 17500,
        "industrial": 8000,
    },
    "JP Nagar": {
        "zone_tier": "prime",
        "city": "Bangalore",
        "lat": 12.9067,
        "lon": 77.5856,
        "residential_apartment": 11000,
        "residential_plot": 15500,
        "commercial_shop": 20000,
        "commercial_office": 14500,
        "industrial": 7200,
    },
    "Electronic City": {
        "zone_tier": "mid",
        "city": "Bangalore",
        "lat": 12.8399,
        "lon": 77.6770,
        "residential_apartment": 7500,
        "residential_plot": 10000,
        "commercial_shop": 13000,
        "commercial_office": 10000,
        "industrial": 6000,
    },
    "Marathahalli": {
        "zone_tier": "mid",
        "city": "Bangalore",
        "lat": 12.9591,
        "lon": 77.7001,
        "residential_apartment": 8200,
        "residential_plot": 11000,
        "commercial_shop": 14500,
        "commercial_office": 11000,
        "industrial": 5800,
    },
    "Sarjapur Road": {
        "zone_tier": "mid",
        "city": "Bangalore",
        "lat": 12.8954,
        "lon": 77.6795,
        "residential_apartment": 8800,
        "residential_plot": 12000,
        "commercial_shop": 15500,
        "commercial_office": 11500,
        "industrial": 6200,
    },
    "Yelahanka": {
        "zone_tier": "mid",
        "city": "Bangalore",
        "lat": 13.1004,
        "lon": 77.5963,
        "residential_apartment": 7000,
        "residential_plot": 9500,
        "commercial_shop": 12000,
        "commercial_office": 9000,
        "industrial": 5200,
    },
    "Hebbal": {
        "zone_tier": "mid",
        "city": "Bangalore",
        "lat": 13.0358,
        "lon": 77.5970,
        "residential_apartment": 9000,
        "residential_plot": 12500,
        "commercial_shop": 16000,
        "commercial_office": 12000,
        "industrial": 6500,
    },
    "Rajajinagar": {
        "zone_tier": "mid",
        "city": "Bangalore",
        "lat": 12.9913,
        "lon": 77.5560,
        "residential_apartment": 9500,
        "residential_plot": 13000,
        "commercial_shop": 17000,
        "commercial_office": 12500,
        "industrial": 6800,
    },
    "Banashankari": {
        "zone_tier": "mid",
        "city": "Bangalore",
        "lat": 12.9249,
        "lon": 77.5468,
        "residential_apartment": 8500,
        "residential_plot": 11500,
        "commercial_shop": 15000,
        "commercial_office": 11000,
        "industrial": 6000,
    },
    "Bannerghatta": {
        "zone_tier": "peripheral",
        "city": "Bangalore",
        "lat": 12.8624,
        "lon": 77.5982,
        "residential_apartment": 5800,
        "residential_plot": 7800,
        "commercial_shop": 10000,
        "commercial_office": 7800,
        "industrial": 4500,
    },
    "Devanahalli": {
        "zone_tier": "peripheral",
        "city": "Bangalore",
        "lat": 13.2468,
        "lon": 77.7137,
        "residential_apartment": 5000,
        "residential_plot": 6800,
        "commercial_shop": 8500,
        "commercial_office": 6500,
        "industrial": 4000,
    },
    "Tumkur Road": {
        "zone_tier": "peripheral",
        "city": "Bangalore",
        "lat": 13.0298,
        "lon": 77.4968,
        "residential_apartment": 5500,
        "residential_plot": 7200,
        "commercial_shop": 9500,
        "commercial_office": 7200,
        "industrial": 4200,
    },
    "Kanakapura Road": {
        "zone_tier": "peripheral",
        "city": "Bangalore",
        "lat": 12.8724,
        "lon": 77.5581,
        "residential_apartment": 5200,
        "residential_plot": 7000,
        "commercial_shop": 9000,
        "commercial_office": 7000,
        "industrial": 4000,
    },
}

# ── Merged lookup ──────────────────────────────────────────────────────────
ALL_CIRCLE_RATES = {**PUNE_RATES, **MUMBAI_RATES, **BANGALORE_RATES}

CITY_LOCALITIES = {
    "Pune": list(PUNE_RATES.keys()),
    "Mumbai": list(MUMBAI_RATES.keys()),
    "Bangalore": list(BANGALORE_RATES.keys()),
}

ZONE_MULTIPLIERS = {
    "prime": {"min": 1.7, "mid": 2.1, "max": 2.6},
    "mid": {"min": 1.2, "mid": 1.45, "max": 1.75},
    "peripheral": {"min": 0.85, "mid": 1.05, "max": 1.25},
}

PROPERTY_TYPE_MAP = {
    "2bhk_apartment": "residential_apartment",
    "3bhk_apartment": "residential_apartment",
    "1bhk_apartment": "residential_apartment",
    "4bhk_apartment": "residential_apartment",
    "villa": "residential_apartment",
    "plot": "residential_plot",
    "shop": "commercial_shop",
    "office": "commercial_office",
    "warehouse": "industrial",
    "factory": "industrial",
    "residential_apartment": "residential_apartment",
    "commercial_shop": "commercial_shop",
    "office": "commercial_office",
    "plot": "residential_plot",
}


def _lookup_static_rate(locality: str, prop_key: str) -> dict:
    normalized = locality.strip().title()
    data = ALL_CIRCLE_RATES.get(normalized)
    if not data:
        for loc_name, loc_data in ALL_CIRCLE_RATES.items():
            if normalized in loc_name or loc_name in normalized:
                data = loc_data
                normalized = loc_name
                break

    if data:
        rate_val = data.get(prop_key, data.get("residential_apartment", 6000))
        return {
            "locality": normalized,
            "city": data.get("city", "Pune"),
            "zone_tier": data.get("zone_tier", "mid"),
            "circle_rate_per_sqft": rate_val,
            "property_type_key": prop_key,
            "lat": data.get("lat"),
            "lon": data.get("lon"),
        }

    return {
        "locality": locality,
        "city": "Pune",
        "zone_tier": "mid",
        "circle_rate_per_sqft": 6000,
        "property_type_key": prop_key,
        "lat": None,
        "lon": None,
    }


def get_circle_rate(
    locality: str, property_type: str, geo_lat: float = None, geo_lon: float = None
) -> dict:
    from app.core.db import SessionLocal
    from app.models.db_models import CircleRate

    normalized = locality.strip().title()
    prop_key = PROPERTY_TYPE_MAP.get(property_type.lower(), "residential_apartment")

    db = SessionLocal()
    try:
        # If exact coordinates are provided, use nearest known locality for micro-market mapping.
        if geo_lat is not None and geo_lon is not None:
            import math

            all_rates = db.query(CircleRate).all()
            if all_rates:

                def dist(r):
                    if r.lat is None or r.lon is None:
                        return float("inf")
                    return math.hypot(
                        float(r.lat) - float(geo_lat), float(r.lon) - float(geo_lon)
                    )

                rate = min(all_rates, key=dist)
            else:
                rate = None
        else:
            # Perform an ILIKE query for substring match, just like the old logic
            rate = (
                db.query(CircleRate)
                .filter(CircleRate.locality.ilike(f"%{normalized}%"))
                .first()
            )

        if rate:
            # Dynamically get the appropriate property rate column
            rate_val = getattr(rate, prop_key, rate.residential_apartment)
            return {
                "locality": rate.locality,
                "city": rate.city,
                "zone_tier": rate.zone_tier,
                "circle_rate_per_sqft": rate_val,
                "property_type_key": prop_key,
                "lat": rate.lat,
                "lon": rate.lon,
            }
        # DB is available but locality may be unknown: fallback to static set
        return _lookup_static_rate(locality, prop_key)
    except Exception:
        # Critical fallback for tests/unseeded DB: use static rates table
        return _lookup_static_rate(locality, prop_key)
    finally:
        db.close()


def get_localities_by_city() -> dict:
    from app.core.db import SessionLocal
    from app.models.db_models import CircleRate

    db = SessionLocal()
    try:
        rates = db.query(CircleRate.city, CircleRate.locality).all()
        result = {}
        for city, locality in rates:
            if city not in result:
                result[city] = []
            result[city].append(locality)
        if result:
            return result
        return CITY_LOCALITIES
    except Exception:
        return CITY_LOCALITIES
    finally:
        db.close()
