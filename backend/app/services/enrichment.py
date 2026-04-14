"""
PropIQ Enrichment Services
- GeoEnricher: geocoding via Nominatim
- InfraScorer: infrastructure proximity via OSM Overpass API
- MarketSignalService: listing density proxy
- All services are async and fire in parallel
"""

import asyncio
import aiohttp
import json
import math
from typing import Optional
from functools import lru_cache

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

INFRA_QUERIES = {
    "metro_station": ('node["railway"="station"]', 2000, 15),
    "metro_halt":    ('node["railway"="halt"]', 1500, 10),
    "hospital":      ('node["amenity"="hospital"]', 3000, 12),
    "school":        ('node["amenity"="school"]', 1500, 8),
    "college":       ('node["amenity"="college"]', 2000, 8),
    "supermarket":   ('node["shop"="supermarket"]', 1000, 5),
    "mall":          ('node["shop"="mall"]', 3000, 7),
    "it_park":       ('node["office"="it"]', 5000, 10),
    "highway":       ('way["highway"="primary"]', 1000, 6),
    "bus_stop":      ('node["highway"="bus_stop"]', 500, 4),
}

PUNE_COORDS = {
    "Koregaon Park":  (18.5362, 73.8938),
    "Baner":          (18.5590, 73.7868),
    "Kothrud":        (18.5074, 73.8077),
    "Wakad":          (18.5975, 73.7614),
    "Hinjewadi":      (18.5912, 73.7380),
    "Hadapsar":       (18.5018, 73.9260),
    "Wagholi":        (18.5617, 73.9757),
    "Talegaon":       (18.7332, 73.6723),
    "Chakan":         (18.7601, 73.8637),
    "Shivajinagar":   (18.5308, 73.8474),
    "Aundh":          (18.5578, 73.8073),
    "Viman Nagar":    (18.5679, 73.9143),
    "Pimpri":         (18.6279, 73.7997),
    "Chinchwad":      (18.6436, 73.7983),
    "Katraj":         (18.4601, 73.8669),
    "Ambegaon":       (18.4489, 73.8526),
}

LISTING_DENSITY_ESTIMATES = {
    "prime":      {"density": 0.75, "median_asking_premium": 1.18},
    "mid":        {"density": 0.55, "median_asking_premium": 1.06},
    "peripheral": {"density": 0.35, "median_asking_premium": 0.95},
}


async def geocode_address(address: str, session: aiohttp.ClientSession) -> dict:
    """Convert address to lat/long using Nominatim."""
    # Check known localities first (fast path)
    for locality, coords in PUNE_COORDS.items():
        if locality.lower() in address.lower():
            return {
                "lat": coords[0], "lon": coords[1],
                "display_name": f"{locality}, Pune, Maharashtra",
                "locality": locality, "source": "lookup",
            }
    # Nominatim fallback
    try:
        params = {"q": f"{address}, Pune, Maharashtra, India", "format": "json", "limit": 1}
        headers = {"User-Agent": "PropIQ/1.0 (hackathon project)"}
        async with session.get(NOMINATIM_URL, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as r:
            data = await r.json()
            if data:
                return {
                    "lat": float(data[0]["lat"]), "lon": float(data[0]["lon"]),
                    "display_name": data[0].get("display_name", address),
                    "locality": address, "source": "nominatim",
                }
    except Exception:
        pass
    # Last resort: Pune city center
    return {"lat": 18.5204, "lon": 73.8567, "display_name": address, "locality": address, "source": "default"}


async def compute_infra_score(lat: float, lon: float, session: aiohttp.ClientSession) -> dict:
    """Score infrastructure proximity using OSM Overpass API."""
    scores = {}
    total_score = 0.0
    total_weight = 0.0

    async def query_feature(feature_name: str, query_part: str, radius: int, weight: int):
        overpass_q = f"[out:json][timeout:8];{query_part}(around:{radius},{lat},{lon});out count;"
        try:
            async with session.post(
                OVERPASS_URL, data={"data": overpass_q},
                timeout=aiohttp.ClientTimeout(total=8)
            ) as r:
                data = await r.json()
                count = data.get("elements", [{}])[0].get("tags", {}).get("total", 0)
                count = int(count) if count else 0
                return feature_name, min(count, 5), weight
        except Exception:
            return feature_name, 0, weight

    tasks = [query_feature(name, qp, radius, weight) for name, (qp, radius, weight) in INFRA_QUERIES.items()]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            continue
        fname, count, weight = result
        feature_score = min(1.0, count / 3.0) * 100
        scores[fname] = {"count": count, "score": round(feature_score, 1), "weight": weight}
        total_score += feature_score * weight
        total_weight += weight

    infra_score = (total_score / total_weight) if total_weight > 0 else 50.0
    infra_score = min(100, max(0, infra_score))

    return {
        "infra_score": round(infra_score, 1),
        "breakdown": scores,
        "data_source": "openstreetmap_overpass",
    }


def estimate_listing_density(zone_tier: str, locality: str) -> dict:
    """Proxy for market listing density — based on zone tier + locality signals."""
    base = LISTING_DENSITY_ESTIMATES.get(zone_tier, LISTING_DENSITY_ESTIMATES["mid"])
    import random, hashlib
    # Deterministic noise per locality
    seed = int(hashlib.md5(locality.encode()).hexdigest()[:6], 16) % 1000
    rng = random.Random(seed)
    noise = rng.uniform(-0.08, 0.08)
    density = round(min(0.95, max(0.1, base["density"] + noise)), 3)
    return {
        "listing_density": density,
        "median_asking_premium": base["median_asking_premium"],
        "zone_tier": zone_tier,
        "data_source": "proxy_estimate",
    }


async def enrich_property(address: str, zone_tier: str = "mid") -> dict:
    """
    Main enrichment function — fires all services in parallel.
    Returns a consolidated enrichment dict ready for the ML model.
    """
    async with aiohttp.ClientSession() as session:
        geo_task = geocode_address(address, session)
        geo_result = await geo_task
        lat, lon = geo_result["lat"], geo_result["lon"]
        infra_task = compute_infra_score(lat, lon, session)
        infra_result = await infra_task

    listing_result = estimate_listing_density(zone_tier, geo_result.get("locality", address))

    return {
        "geo": geo_result,
        "infra": infra_result,
        "market": listing_result,
        "infra_score": infra_result["infra_score"],
        "listing_density": listing_result["listing_density"],
    }


if __name__ == "__main__":
    result = asyncio.run(enrich_property("Baner, Pune", zone_tier="prime"))
    print(json.dumps(result, indent=2))