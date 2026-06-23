"""
Tests for the deep AIML capability layer (RAG, agent, verifier, forecasting,
vector duplicate detection, knowledge graph, fairness). All run on the
graceful-degradation tier (no optional deps required).
"""

import asyncio

import numpy as np
import pytest


# ── Embeddings ──────────────────────────────────────────────────────────────


def test_embeddings_deterministic_and_normalized():
    from app.ml.embeddings import cosine, embed_one

    a = embed_one("2bhk apartment in Baner prime zone")
    b = embed_one("2bhk apartment in Baner prime zone")
    c = embed_one("warehouse in Chakan peripheral zone industrial")
    assert np.allclose(a, b)  # deterministic
    assert cosine(a, b) > 0.99
    assert cosine(a, c) < cosine(a, b)  # different text less similar


# ── Vector store (memory backend) ───────────────────────────────────────────


def test_vector_store_upsert_query():
    from app.ml.vector_store import get_collection

    col = get_collection("test_collection_unit")
    col.upsert("d1", "RBI LTV norms for commercial shop max 65 percent", {"src": "rbi"})
    col.upsert("d2", "residential apartment villa freehold rera", {"src": "policy"})
    hits = col.query("commercial shop LTV", k=2)
    assert len(hits) >= 1
    assert hits[0]["score"] >= hits[-1]["score"]  # sorted by score


# ── RAG ─────────────────────────────────────────────────────────────────────


def test_rag_seed_and_retrieve_with_citations():
    from app.services.rag import rag_stats, retrieve_context, seed_knowledge

    seed_knowledge()
    stats = rag_stats()
    assert stats["knowledge_chunks"] > 0
    hits = retrieve_context("maximum LTV for commercial shop", k=3)
    assert len(hits) >= 1
    assert all("citation" in h and "snippet" in h for h in hits)


def test_rag_chunks_overlap():
    """Adjacent chunks must share words so facts straddling a boundary stay
    retrievable (previously chunks had zero overlap despite the docstring)."""
    from app.services.rag import _CHUNK_OVERLAP, _chunk

    body = "# Section\n" + " ".join(f"w{i}" for i in range(300))
    chunks = _chunk(body, "doc")
    assert len(chunks) >= 2
    shared = set(chunks[0]["text"].split()) & set(chunks[1]["text"].split())
    assert len(shared) == _CHUNK_OVERLAP


def test_rag_retrieval_scores_are_valid_cosine():
    """Similarity scores must be valid cosine values in [-1, 1] and consistent
    regardless of the active vector backend (memory vs chroma-cosine)."""
    from app.services.rag import retrieve_context, seed_knowledge

    seed_knowledge()
    hits = retrieve_context("LTV cap for loans above 75 lakh", k=3)
    assert hits, "expected at least one hit"
    assert all(-1.0 <= h["score"] <= 1.0 for h in hits)
    # Scores must be sorted descending (most relevant first).
    scores = [h["score"] for h in hits]
    assert scores == sorted(scores, reverse=True)


# ── Agent + verifier ────────────────────────────────────────────────────────


def test_agent_deterministic_runs_all_tools(monkeypatch):
    # Force the no-LLM deterministic path so the test is hermetic
    from app.services import llm_provider, valuation_agent

    monkeypatch.setattr(llm_provider, "is_available", lambda: False)
    from app.core.bootstrap import ensure_circle_rates_seeded

    ensure_circle_rates_seeded()
    prop = {"locality": "Baner", "prop_type": "2bhk_apartment", "size_sqft": 850,
            "age_years": 8, "floor_num": 5, "rental_yield_pct": 3.5}
    out = asyncio.run(valuation_agent.run_valuation_agent(prop))
    assert out["planner"] == "deterministic"
    for tool in ["lookup_circle_rate", "run_avm", "fetch_comps", "run_ensemble",
                 "compute_ltv", "check_policy"]:
        assert tool in out["tool_ledger"]
    assert out["answer"]


def test_verifier_flags_unsupported_number():
    from app.services.verifier_agent import verify

    ledger = {"run_avm": {"value": 19000000, "source": "avm", "detail": {}}}
    # supported number present, plus a hallucinated 99999999
    good = verify("The value is 19000000.", ledger)
    assert good["verified"] is True
    bad = verify("The value is 19000000 but also 99999999.", ledger)
    assert bad["verified"] is False
    assert 99999999.0 in bad["unsupported_claims"]


# ── Forecasting ─────────────────────────────────────────────────────────────


def test_forecast_returns_band(monkeypatch):
    from app.core.bootstrap import ensure_circle_rates_seeded
    from app.ml.forecasting import forecast_locality

    ensure_circle_rates_seeded()
    f = forecast_locality("Baner", "2bhk_apartment", 6)
    assert f["engine"] in ("prophet", "statsmodels", "numpy")
    assert len(f["forecast"]) == 6
    for pt in f["forecast"]:
        assert pt["ci_low"] <= pt["price_per_sqft"] <= pt["ci_high"]


def test_forecast_numpy_tier_forced(monkeypatch):
    from app.core import config
    from app.ml import forecasting

    monkeypatch.setattr(config.settings, "FORECAST_ENGINE", "numpy")
    # _resolve_engine should return numpy when forced and prophet/sm not requested
    assert forecasting._resolve_engine() == "numpy"


# ── Vector duplicate detection ──────────────────────────────────────────────


def test_duplicate_detection_finds_near_identical():
    from app.ml.property_embeddings import duplicate_risk, find_near_duplicates

    base = {"locality": "Baner", "prop_type": "2bhk_apartment", "size_sqft": 850,
            "age_years": 8, "floor_num": 5, "is_freehold": 1, "is_rera_registered": 1}
    duplicate_risk(base, "REQ-AAA", borrower="Alice")
    # An identical property under a different borrower => critical
    dup = duplicate_risk(dict(base), "REQ-BBB", borrower="Bob")
    assert dup["duplicate_count"] >= 1
    assert dup["risk_level"] in ("high", "critical")


# ── Knowledge graph ─────────────────────────────────────────────────────────


def test_kg_concentration_hhi():
    from app.core.bootstrap import ensure_circle_rates_seeded
    from app.ml.knowledge_graph import portfolio_concentration
    from app.services.chm_engine import seed_demo_loans

    ensure_circle_rates_seeded()
    seed_demo_loans()
    conc = portfolio_concentration()
    if conc.get("loans", 0) > 0:
        assert 0.0 <= conc["locality_hhi"] <= 1.0
        assert conc["concentration_risk"] in ("low", "moderate", "high")


# ── Fairness ────────────────────────────────────────────────────────────────


def test_fairness_audit_runs():
    from app.ml.fairness import bias_audit

    result = bias_audit()
    # Either no data yet, or a valid audit structure
    assert "n" in result
    if result["n"] > 0:
        assert "disparate_impact_ratio" in result
