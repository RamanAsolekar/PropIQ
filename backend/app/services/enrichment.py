"""
PropIQ Enrichment Services
- GeoEnricher: geocoding via Nominatim (skipped if lat/lon provided directly)
- InfraScorer: infrastructure proximity via OSM Overpass API
- NeighbourhoodQualityScorer: planned vs unplanned zone quality signal
- MarketSignalService: listing density proxy
- All services are async and fire in parallel
"""

import asyncio
import json
import math
import sqlite3
from datetime import datetime
from functools import lru_cache
from typing import Optional

import aiohttp

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

INFRA_QUERIES = {
    "metro_station": ('node["railway"="station"]', 2000, 15),
    "metro_halt": ('node["railway"="halt"]', 1500, 10),
    "hospital": ('node["amenity"="hospital"]', 3000, 12),
    "school": ('node["amenity"="school"]', 1500, 8),
    "college": ('node["amenity"="college"]', 2000, 8),
    "supermarket": ('node["shop"="supermarket"]', 1000, 5),
    "mall": ('node["shop"="mall"]', 3000, 7),
    "it_park": ('node["office"="it"]', 5000, 10),
    "highway": ('way["highway"="primary"]', 1000, 6),
    "bus_stop": ('node["highway"="bus_stop"]', 500, 4),
}

# Gap 1: OSM queries for neighbourhood quality scoring
NEIGHBOURHOOD_QUERIES = {
    "residential_land": ('way["landuse"="residential"]', 1000, 20),
    "commercial_land": ('way["landuse"="commercial"]', 1000, -10),
    "industrial_land": ('way["landuse"="industrial"]', 2000, -20),
    "park": ('way["leisure"="park"]', 1500, 10),
    "religious": ('node["amenity"="place_of_worship"]', 500, 3),
    "slum": ('way["landuse"="slum"]', 1000, -25),
}

PUNE_COORDS = {
    # Pune
    "Koregaon Park": (18.5362, 73.8938),
    "Baner": (18.5590, 73.7868),
    "Kothrud": (18.5074, 73.8077),
    "Wakad": (18.5975, 73.7614),
    "Hinjewadi": (18.5912, 73.7380),
    "Hadapsar": (18.5018, 73.9260),
    "Wagholi": (18.5617, 73.9757),
    "Talegaon": (18.7332, 73.6723),
    "Chakan": (18.7601, 73.8637),
    "Shivajinagar": (18.5308, 73.8474),
    "Aundh": (18.5578, 73.8073),
    "Viman Nagar": (18.5679, 73.9143),
    "Pimpri": (18.6279, 73.7997),
    "Chinchwad": (18.6436, 73.7983),
    "Katraj": (18.4601, 73.8669),
    "Ambegaon": (18.4489, 73.8526),
    "Kalyani Nagar": (18.5456, 73.9010),
    "Magarpatta": (18.5114, 73.9274),
    "Bavdhan": (18.5196, 73.7805),
    "Kondhwa": (18.4672, 73.8924),
    "Nibm": (18.4608, 73.8980),
    "Dhanori": (18.5896, 73.9155),
    "Vishrantwadi": (18.5810, 73.9010),
    "Ravet": (18.6434, 73.7449),
    "Undri": (18.4524, 73.9009),
    "Fursungi": (18.4842, 73.9279),
    # Mumbai
    "Bandra West": (19.0596, 72.8295),
    "Worli": (19.0178, 72.8148),
    "Powai": (19.1197, 72.9052),
    "Andheri West": (19.1365, 72.8304),
    "Andheri East": (19.1197, 72.8697),
    "Thane": (19.2183, 72.9781),
    "Navi Mumbai": (19.0330, 73.0297),
    "Dadar": (19.0178, 72.8452),
    "Borivali": (19.2323, 72.8563),
    "Mira Road": (19.2876, 72.8689),
    "Virar": (19.4588, 72.7987),
    "Kharghar": (19.0478, 73.0760),
    "Goregaon": (19.1663, 72.8526),
    "Malad": (19.1872, 72.8484),
    "Kandivali": (19.2071, 72.8546),
    "Kurla": (19.0726, 72.8826),
    "Ghatkopar": (19.0867, 72.9082),
    "Mulund": (19.1726, 72.9560),
    "Chembur": (19.0522, 72.8994),
    "Panvel": (18.9894, 73.1175),
    # Bangalore
    "Koramangala": (12.9352, 77.6245),
    "Indiranagar": (12.9716, 77.6412),
    "Whitefield": (12.9698, 77.7499),
    "HSR Layout": (12.9116, 77.6474),
    "Electronic City": (12.8450, 77.6601),
    "Marathahalli": (12.9591, 77.6974),
    "Sarjapur Road": (12.9102, 77.6789),
    "Yelahanka": (13.1006, 77.5963),
    "Bannerghatta": (12.8636, 77.5994),
    "Devanahalli": (13.2467, 77.7108),
    "Tumkur Road": (13.0230, 77.5540),
    "Jayanagar": (12.9259, 77.5937),
    "JP Nagar": (12.9067, 77.5856),
    "Hebbal": (13.0358, 77.5970),
    "Rajajinagar": (12.9913, 77.5560),
    "Banashankari": (12.9249, 77.5468),
    "Kanakapura Road": (12.8724, 77.5581),
}

# Gap 1: Baseline neighbourhood quality scores per zone tier (deterministic fallback)
ZONE_NEIGHBOURHOOD_BASE = {
    "prime": 78.0,
    "mid": 58.0,
    "peripheral": 40.0,
}

LISTING_DENSITY_ESTIMATES = {
    "prime": {"density": 0.75, "median_asking_premium": 1.18},
    "mid": {"density": 0.55, "median_asking_premium": 1.06},
    "peripheral": {"density": 0.35, "median_asking_premium": 0.95},
}


def _market_activity_from_comps(locality: str, zone_tier: str = "mid") -> dict:
    """
    Market activity proxy built from comp listing recency/volume.
    Uses local comps DB when available; falls back to neutral values.
    """
    try:
        from app.services.comps_engine import DB_PATH

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        total = c.execute(
            "SELECT COUNT(*) FROM comps WHERE locality = ?", (locality,)
        ).fetchone()[0]
        recent_60d = c.execute(
            "SELECT COUNT(*) FROM comps WHERE locality = ? AND listing_date >= date('now','-60 day')",
            (locality,),
        ).fetchone()[0]
        conn.close()

        # Base YoY growth by zone tier
        base_growth = {"prime": 8.5, "mid": 5.0, "peripheral": 2.0}.get(zone_tier, 5.0)

        if total <= 0:
            return {
                "listing_velocity": 0.5,
                "transaction_indicator": 0.5,
                "months_of_inventory": 6.0,
                "yoy_price_growth_pct": base_growth,
                "source": "proxy_neutral",
            }

        velocity = min(1.0, recent_60d / max(total, 1))
        txn_indicator = min(1.0, (recent_60d / 8.0))

        # Calculate MOI (Months of Inventory)
        monthly_absorption = max(recent_60d / 2.0, 0.5)
        moi = min(36.0, round(total / monthly_absorption, 1))

        # Adjust YoY growth based on velocity
        yoy_growth = round(base_growth + ((velocity - 0.5) * 10), 1)

        return {
            "listing_velocity": round(velocity, 3),
            "transaction_indicator": round(txn_indicator, 3),
            "months_of_inventory": moi,
            "yoy_price_growth_pct": yoy_growth,
            "source": "comps_listing_proxy",
        }
    except Exception:
        return {
            "listing_velocity": 0.5,
            "transaction_indicator": 0.5,
            "months_of_inventory": 6.0,
            "yoy_price_growth_pct": 5.0,
            "source": "proxy_neutral",
        }


async def geocode_address(address: str, session: aiohttp.ClientSession) -> dict:
    """Convert address to lat/long using Nominatim."""
    # Check known localities first (fast path)
    for locality, coords in PUNE_COORDS.items():
        if locality.lower() in address.lower():
            return {
                "lat": coords[0],
                "lon": coords[1],
                "display_name": f"{locality}, Maharashtra",
                "locality": locality,
                "source": "lookup",
            }
    # Nominatim fallback
    try:
        params = {"q": f"{address}, Maharashtra, India", "format": "json", "limit": 1}
        headers = {"User-Agent": "PropIQ/1.0 (hackathon project)"}
        async with session.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=5),
        ) as r:
            data = await r.json()
            if data:
                return {
                    "lat": float(data[0]["lat"]),
                    "lon": float(data[0]["lon"]),
                    "display_name": data[0].get("display_name", address),
                    "locality": address,
                    "source": "nominatim",
                }
    except Exception:
        pass
    # Last resort: Pune city center
    return {
        "lat": 18.5204,
        "lon": 73.8567,
        "display_name": address,
        "locality": address,
        "source": "default",
    }


async def compute_infra_score(
    lat: float, lon: float, session: aiohttp.ClientSession, zone_tier: str = "mid"
) -> dict:
    """Score infrastructure proximity using OSM Overpass API. Uses zone-based fallback on failure."""
    scores = {}
    total_score = 0.0
    total_weight = 0.0

    async def query_feature(
        feature_name: str, query_part: str, radius: int, weight: int
    ):
        overpass_q = f"[out:json][timeout:8];{query_part}(around:{radius},{lat},{lon});out count;"
        try:
            async with session.post(
                OVERPASS_URL,
                data={"data": overpass_q},
                timeout=aiohttp.ClientTimeout(total=8),
            ) as r:
                data = await r.json()
                count = data.get("elements", [{}])[0].get("tags", {}).get("total", 0)
                count = int(count) if count else 0
                return feature_name, min(count, 5), weight
        except Exception:
            return feature_name, 0, weight

    tasks = [
        query_feature(name, qp, radius, weight)
        for name, (qp, radius, weight) in INFRA_QUERIES.items()
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            continue
        fname, count, weight = result
        feature_score = min(1.0, count / 3.0) * 100
        scores[fname] = {
            "count": count,
            "score": round(feature_score, 1),
            "weight": weight,
        }
        total_score += feature_score * weight
        total_weight += weight

    if total_weight > 0:
        infra_score = total_score / total_weight
    else:
        # Fallback if API fails to prevent massive distress discounts (Error #1)
        infra_score = {"prime": 75.0, "mid": 55.0, "peripheral": 35.0}.get(
            zone_tier, 55.0
        )

    infra_score = min(100.0, max(0.0, infra_score))

    return {
        "infra_score": round(infra_score, 1),
        "breakdown": scores,
        "data_source": "openstreetmap_overpass",
    }


# Gap 1: Neighbourhood quality score
async def compute_neighbourhood_quality(
    lat: float, lon: float, zone_tier: str, session: aiohttp.ClientSession
) -> dict:
    """
    Score neighbourhood quality: planned vs unplanned zones, land-use mix.
    Returns dict with 0-100 score and dominant_landuse.
    Falls back to zone_tier baseline if OSM unavailable.
    """
    base_score = ZONE_NEIGHBOURHOOD_BASE.get(zone_tier, 58.0)
    adjustment = 0.0
    landuse_counts = {"residential": 0, "commercial": 0, "industrial": 0}

    async def query_nq(feature_name: str, query_part: str, radius: int, weight: int):
        overpass_q = f"[out:json][timeout:6];{query_part}(around:{radius},{lat},{lon});out count;"
        try:
            async with session.post(
                OVERPASS_URL,
                data={"data": overpass_q},
                timeout=aiohttp.ClientTimeout(total=6),
            ) as r:
                data = await r.json()
                count = data.get("elements", [{}])[0].get("tags", {}).get("total", 0)
                count = int(count) if count else 0
                return feature_name, weight if count > 0 else 0, count
        except Exception:
            return feature_name, 0, 0

    tasks = [
        query_nq(name, qp, radius, weight)
        for name, (qp, radius, weight) in NEIGHBOURHOOD_QUERIES.items()
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for r in results:
        if isinstance(r, tuple) and len(r) == 3:
            fname, adj, count = r
            adjustment += adj
            if fname == "residential_land":
                landuse_counts["residential"] += count
            if fname == "commercial_land":
                landuse_counts["commercial"] += count
            if fname == "industrial_land":
                landuse_counts["industrial"] += count

    final = min(100.0, max(10.0, base_score + adjustment))

    dominant_landuse = "residential"  # default
    max_count = 0
    for lu, count in landuse_counts.items():
        if count > max_count:
            max_count = count
            dominant_landuse = lu

    return {"score": round(final, 1), "dominant_landuse": dominant_landuse}


def estimate_listing_density(zone_tier: str, locality: str) -> dict:
    """Proxy for market listing density — based on zone tier + locality signals."""
    base = LISTING_DENSITY_ESTIMATES.get(zone_tier, LISTING_DENSITY_ESTIMATES["mid"])
    import hashlib
    import random

    # Deterministic noise per locality
    seed = int(hashlib.md5(locality.encode()).hexdigest()[:6], 16) % 1000
    rng = random.Random(seed)
    noise = rng.uniform(-0.08, 0.08)
    density = round(min(0.95, max(0.1, base["density"] + noise)), 3)
    market_proxy = _market_activity_from_comps(locality, zone_tier)
    blended = round(
        min(0.95, max(0.1, density * 0.7 + market_proxy["listing_velocity"] * 0.3)), 3
    )
    return {
        "listing_density": blended,
        "listing_density_base": density,
        "median_asking_premium": base["median_asking_premium"],
        "listing_velocity": market_proxy["listing_velocity"],
        "transaction_indicator": market_proxy["transaction_indicator"],
        "months_of_inventory": market_proxy["months_of_inventory"],
        "yoy_price_growth_pct": market_proxy["yoy_price_growth_pct"],
        "zone_tier": zone_tier,
        "data_source": f"tier_proxy+{market_proxy['source']}",
    }


async def enrich_property(
    address: str,
    zone_tier: str = "mid",
    geo_lat: Optional[float] = None,
    geo_lon: Optional[float] = None,
) -> dict:
    """
    Main enrichment function — fires all services in parallel.
    Gap 6 fix: If geo_lat/geo_lon are provided, skip geocoding entirely.
    Returns a consolidated enrichment dict ready for the ML model.
    """
    async with aiohttp.ClientSession() as session:
        # Gap 6 fix: bypass geocoding if coordinates are already known
        if geo_lat is not None and geo_lon is not None:
            geo_result = {
                "lat": geo_lat,
                "lon": geo_lon,
                "display_name": address,
                "locality": address,
                "source": "user_provided",
            }
        else:
            geo_result = await geocode_address(address, session)

        lat, lon = geo_result["lat"], geo_result["lon"]

        # Fire infra score and neighbourhood quality in parallel
        infra_task = compute_infra_score(lat, lon, session, zone_tier)
        nq_task = compute_neighbourhood_quality(lat, lon, zone_tier, session)
        infra_result, nq_result = await asyncio.gather(infra_task, nq_task)
        nq_score = nq_result["score"]
        dominant_landuse = nq_result["dominant_landuse"]

    listing_result = estimate_listing_density(
        zone_tier, geo_result.get("locality", address)
    )

    return {
        "geo": geo_result,
        "infra": infra_result,
        "market": listing_result,
        "infra_score": infra_result["infra_score"],
        "listing_density": listing_result["listing_density"],
        "listing_velocity": listing_result.get("listing_velocity", 0.5),
        "transaction_indicator": listing_result.get("transaction_indicator", 0.5),
        "neighbourhood_quality_score": nq_score,
        "dominant_landuse": dominant_landuse,
        "months_of_inventory": listing_result["months_of_inventory"],
        "yoy_price_growth_pct": listing_result["yoy_price_growth_pct"],
    }


if __name__ == "__main__":
    result = asyncio.run(enrich_property("Baner, Pune", zone_tier="prime"))
    print(json.dumps(result, indent=2))
