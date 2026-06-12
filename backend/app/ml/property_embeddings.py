"""
PropIQ Property Embeddings — vector duplicate / fraud-ring detection.

Each assessed property is turned into a text descriptor and embedded into the
`propiq_properties` vector collection. On every new assessment we query for
near-duplicates: the same flat pledged twice, or suspiciously identical
collateral across different borrowers (fraud ring signal).

Reuses app/ml/vector_store + app/ml/embeddings, so it works on the in-memory
backend with hashing embeddings out of the box, and upgrades to chroma +
sentence-transformers when installed.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from app.core.config import settings
from app.ml import vector_store

logger = logging.getLogger(__name__)

PROPERTIES_COLLECTION = "propiq_properties"


def property_descriptor(prop: Dict, request_id: str = "") -> str:
    """Deterministic text descriptor that captures collateral identity."""
    return (
        f"{prop.get('prop_type','')} {prop.get('locality','')} "
        f"size:{round(float(prop.get('size_sqft', 0)))} "
        f"age:{round(float(prop.get('age_years', 0)))} "
        f"floor:{prop.get('floor_num', '')} "
        f"freehold:{prop.get('is_freehold', 1)} "
        f"rera:{prop.get('is_rera_registered', 1)} "
        f"lat:{round(float(prop.get('geo_lat') or 0), 3)} "
        f"lon:{round(float(prop.get('geo_lon') or 0), 3)}"
    )


def index_property(prop: Dict, request_id: str, borrower: str = "") -> None:
    """Upsert a property into the vector collection. Best-effort."""
    try:
        col = vector_store.get_collection(PROPERTIES_COLLECTION)
        col.upsert(
            request_id,
            property_descriptor(prop, request_id),
            {"request_id": request_id, "locality": prop.get("locality", ""),
             "prop_type": prop.get("prop_type", ""), "borrower": borrower},
        )
    except Exception as e:
        logger.warning("index_property failed: %s", e)


def find_near_duplicates(prop: Dict, threshold: Optional[float] = None,
                         exclude_request_id: str = "", k: int = 5) -> List[Dict]:
    """Return prior pledges highly similar to this property."""
    threshold = threshold if threshold is not None else settings.DUPLICATE_SIM_THRESHOLD
    try:
        col = vector_store.get_collection(PROPERTIES_COLLECTION)
        hits = col.query(property_descriptor(prop), k=k + 1)
    except Exception as e:
        logger.warning("duplicate query failed: %s", e)
        return []
    out = []
    for h in hits:
        if h["id"] == exclude_request_id:
            continue
        if h.get("score", 0) >= threshold:
            meta = h.get("metadata", {})
            out.append({
                "request_id": h["id"], "similarity": h["score"],
                "locality": meta.get("locality"), "prop_type": meta.get("prop_type"),
                "borrower": meta.get("borrower", ""),
            })
    return out[:k]


def duplicate_risk(prop: Dict, request_id: str, borrower: str = "") -> Dict:
    """Index this property then report duplicate risk (call AFTER indexing peers)."""
    dups = find_near_duplicates(prop, exclude_request_id=request_id)
    index_property(prop, request_id, borrower)
    level = "high" if dups else "none"
    distinct_borrowers = {d["borrower"] for d in dups if d.get("borrower")}
    if dups and len(distinct_borrowers) > 1:
        level = "critical"  # same collateral across different borrowers => fraud ring
    return {
        "duplicate_count": len(dups),
        "risk_level": level,
        "matches": dups,
        "threshold": settings.DUPLICATE_SIM_THRESHOLD,
        "backend": vector_store.active_backend(),
    }
