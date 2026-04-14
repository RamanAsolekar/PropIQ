"""
PropIQ Security — API Key Authentication + Rate Limiting
Simple but production-looking security layer for the demo.
"""

import time
from collections import defaultdict
from fastapi import HTTPException, Security, Request
from fastapi.security.api_key import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Demo API keys — in production these would be in a database
VALID_API_KEYS = {
    "propiq-demo-2026":     {"name": "Demo Key", "tier": "standard", "rate_limit": 100},
    "propiq-pfl-internal":  {"name": "PFL Internal", "tier": "premium", "rate_limit": 500},
    "propiq-hackathon":     {"name": "Hackathon", "tier": "standard", "rate_limit": 200},
}

# In-memory rate limiting (per API key, per minute)
_rate_store: dict = defaultdict(list)
RATE_WINDOW_SECONDS = 60


def check_rate_limit(api_key: str, limit: int):
    now = time.time()
    window_start = now - RATE_WINDOW_SECONDS
    # Clean old entries
    _rate_store[api_key] = [t for t in _rate_store[api_key] if t > window_start]
    if len(_rate_store[api_key]) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {limit} requests/minute. Try again shortly."
        )
    _rate_store[api_key].append(now)


async def get_api_key(api_key_header: str = Security(API_KEY_HEADER)):
    """
    Optional API key validation.
    If no key provided — allow with standard rate limit (demo mode).
    If invalid key — reject.
    If valid key — apply tier-specific rate limit.
    """
    if api_key_header is None:
        # Allow unauthenticated access for demo (rate limit applies)
        check_rate_limit("anonymous", 50)
        return {"name": "Anonymous", "tier": "demo", "rate_limit": 50}

    if api_key_header not in VALID_API_KEYS:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key. Use X-API-Key header. Demo key: propiq-demo-2026"
        )

    key_info = VALID_API_KEYS[api_key_header]
    check_rate_limit(api_key_header, key_info["rate_limit"])
    return key_info