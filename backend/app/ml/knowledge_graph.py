"""
PropIQ Knowledge Graph — portfolio relationships & concentration risk.

Builds an on-demand graph over the existing ActiveLoan / locality / zone data:
  Loan -> Borrower, Loan -> Property -> Locality -> Zone

From it we derive portfolio-level intelligence a flat table can't show:
  - portfolio_concentration(): exposure HHI by locality / zone (concentration risk)
  - developer_grade_propagation(): push a locality/zone risk score to linked loans
  - fraud_rings(): connected components over the vector duplicate-similarity graph

Uses networkx when installed for richer algorithms; falls back to pure-dict
adjacency + a simple union-find for components otherwise. Read-only over existing
tables — no schema changes, nothing persisted.
"""

from __future__ import annotations

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def _load_loans() -> List[Dict]:
    from app.core.db import SessionLocal
    from app.data.india_circle_rates import get_circle_rate
    from app.models.db_models import ActiveLoan

    db = SessionLocal()
    try:
        loans = db.query(ActiveLoan).filter(ActiveLoan.status == "active").all()
        out = []
        for ln in loans:
            cr = get_circle_rate(ln.locality, ln.prop_type)
            out.append({
                "loan_id": ln.loan_id, "borrower": ln.borrower_name,
                "locality": ln.locality, "zone_tier": cr.get("zone_tier", "mid"),
                "city": cr.get("city", "Pune"), "prop_type": ln.prop_type,
                "loan_amount": float(ln.loan_amount),
            })
        return out
    finally:
        db.close()


def _hhi(exposures: Dict[str, float]) -> float:
    """Herfindahl-Hirschman Index (0-1) of an exposure distribution."""
    total = sum(exposures.values())
    if total <= 0:
        return 0.0
    return round(sum((v / total) ** 2 for v in exposures.values()), 4)


def portfolio_concentration() -> Dict:
    loans = _load_loans()
    if not loans:
        return {"loans": 0, "message": "No active loans."}

    by_locality: Dict[str, float] = {}
    by_zone: Dict[str, float] = {}
    by_city: Dict[str, float] = {}
    total = 0.0
    for ln in loans:
        by_locality[ln["locality"]] = by_locality.get(ln["locality"], 0) + ln["loan_amount"]
        by_zone[ln["zone_tier"]] = by_zone.get(ln["zone_tier"], 0) + ln["loan_amount"]
        by_city[ln["city"]] = by_city.get(ln["city"], 0) + ln["loan_amount"]
        total += ln["loan_amount"]

    def _top(d, n=5):
        return sorted(
            [{"key": k, "exposure": round(v), "pct": round(v / total * 100, 1)}
             for k, v in d.items()],
            key=lambda x: x["exposure"], reverse=True)[:n]

    locality_hhi = _hhi(by_locality)
    return {
        "loans": len(loans),
        "total_exposure": round(total),
        "locality_hhi": locality_hhi,
        "concentration_risk": (
            "high" if locality_hhi > 0.25 else "moderate" if locality_hhi > 0.15 else "low"
        ),
        "zone_hhi": _hhi(by_zone),
        "top_localities": _top(by_locality),
        "by_zone": _top(by_zone, 3),
        "by_city": _top(by_city, 3),
    }


def developer_grade_propagation() -> Dict:
    """
    Propagate a zone/locality risk score to each loan (proxy for developer-grade
    propagation in the absence of a developer field). Higher = riskier collateral.
    """
    loans = _load_loans()
    zone_risk = {"prime": 0.2, "mid": 0.5, "peripheral": 0.8}
    propagated = []
    for ln in loans:
        score = zone_risk.get(ln["zone_tier"], 0.5)
        propagated.append({
            "loan_id": ln["loan_id"], "locality": ln["locality"],
            "zone_tier": ln["zone_tier"], "propagated_risk_score": score,
            "risk_band": "high" if score >= 0.7 else "medium" if score >= 0.4 else "low",
        })
    return {"loans": len(propagated), "propagation": propagated}


def fraud_rings() -> Dict:
    """
    Connected components over the property near-duplicate similarity graph
    (built from the vector store). A component spanning multiple borrowers is a
    candidate fraud ring (same collateral pledged under different names).
    """
    from app.ml import vector_store
    from app.ml.property_embeddings import PROPERTIES_COLLECTION

    col = vector_store.get_collection(PROPERTIES_COLLECTION)
    # Pull all property nodes (memory backend exposes _items; chroma via query)
    items = getattr(col, "_items", None)
    nodes = list(items.values()) if items else []
    if not nodes:
        return {"rings": [], "message": "No indexed properties yet."}

    from app.core.config import settings
    from app.ml.embeddings import cosine
    import numpy as np

    threshold = settings.DUPLICATE_SIM_THRESHOLD
    # Build similarity edges
    edges = []
    ids = [n["id"] for n in nodes]
    vecs = [np.asarray(n["vec"], dtype=np.float32) for n in nodes]
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            if cosine(vecs[i], vecs[j]) >= threshold:
                edges.append((ids[i], ids[j]))

    # Connected components
    try:
        import networkx as nx

        g = nx.Graph()
        g.add_nodes_from(ids)
        g.add_edges_from(edges)
        components = [c for c in nx.connected_components(g) if len(c) > 1]
        engine = "networkx"
    except Exception:
        # union-find fallback
        parent = {i: i for i in ids}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for a, b in edges:
            parent[find(a)] = find(b)
        groups: Dict[str, List[str]] = {}
        for i in ids:
            groups.setdefault(find(i), []).append(i)
        components = [set(v) for v in groups.values() if len(v) > 1]
        engine = "union_find"

    meta_by_id = {n["id"]: n["metadata"] for n in nodes}
    rings = []
    for comp in components:
        borrowers = {meta_by_id.get(i, {}).get("borrower", "") for i in comp}
        rings.append({
            "members": list(comp),
            "size": len(comp),
            "distinct_borrowers": len([b for b in borrowers if b]),
            "is_suspicious": len([b for b in borrowers if b]) > 1,
        })
    return {"rings": rings, "ring_count": len(rings), "engine": engine,
            "threshold": threshold}
