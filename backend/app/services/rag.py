"""
PropIQ RAG service — retrieval over the policy/knowledge corpus.

Grounds LLM outputs (credit memos, the agent's check_policy tool) in real RBI /
internal-policy / precedent text instead of free-form generation. Every retrieved
snippet carries a citable source so the model can attribute each policy claim.

Backed by app/ml/vector_store (chroma or in-memory) + app/ml/embeddings (ST or
hashing). Fully degrades: no corpus -> empty context -> memo falls back to its
existing ungrounded path.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List

from app.core.config import settings
from app.ml import vector_store

logger = logging.getLogger(__name__)

KNOWLEDGE_COLLECTION = "propiq_knowledge"
_CHUNK_TOKENS = 120  # approx words per chunk
_CHUNK_OVERLAP = 30  # words shared between adjacent chunks (~25%)


def _chunk(text: str, source: str) -> List[Dict]:
    """Split a doc into overlapping, section-aware chunks.

    Chunks overlap by ``_CHUNK_OVERLAP`` words. Without overlap, a fact that
    straddles a chunk boundary (e.g. "...LTV cap is" | "75% for loans above
    ₹75L") is split across two chunks and becomes unretrievable as a unit —
    the classic RAG boundary-loss problem. The previous implementation stepped
    by the full chunk size (zero overlap) despite its docstring.
    """
    stride = max(1, _CHUNK_TOKENS - _CHUNK_OVERLAP)
    blocks = re.split(r"\n(?=#)", text)
    chunks = []
    idx = 0
    for block in blocks:
        words = block.split()
        if not words:
            continue
        # Capture the nearest heading as a section label (per block).
        heading = ""
        m = re.search(r"#+\s*(.+)", block)
        if m:
            heading = m.group(1).strip()[:60]
        for start in range(0, len(words), stride):
            piece = " ".join(words[start:start + _CHUNK_TOKENS])
            chunks.append({
                "id": f"{source}::{idx}",
                "text": piece,
                "source": source,
                "section": heading,
            })
            idx += 1
            # Stop once the window has consumed the block (avoid a trailing
            # duplicate chunk shorter than the overlap).
            if start + _CHUNK_TOKENS >= len(words):
                break
    return chunks


def seed_knowledge(force: bool = False) -> Dict:
    """Idempotently chunk + embed + upsert the knowledge corpus. Non-fatal."""
    col = vector_store.get_collection(KNOWLEDGE_COLLECTION)
    try:
        existing = col.count()
    except Exception:
        existing = 0
    if existing > 0 and not force:
        return {"status": "already_seeded", "chunks": existing,
                "backend": vector_store.active_backend()}

    kdir: Path = settings.KNOWLEDGE_DIR
    if not kdir.exists():
        return {"status": "no_corpus", "chunks": 0, "dir": str(kdir)}

    total = 0
    for f in sorted(kdir.glob("*")):
        if f.suffix.lower() not in (".md", ".txt"):
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for ch in _chunk(text, source=f.stem):
            col.upsert(ch["id"], ch["text"],
                       {"source": ch["source"], "section": ch["section"]})
            total += 1
    logger.info("Seeded %d knowledge chunks (%s).", total, vector_store.active_backend())
    return {"status": "seeded", "chunks": total, "backend": vector_store.active_backend()}


def retrieve_context(query: str, k: int = None) -> List[Dict]:
    """Return top-k cited snippets for a query."""
    k = k or settings.RAG_TOP_K
    col = vector_store.get_collection(KNOWLEDGE_COLLECTION)
    try:
        if col.count() == 0:
            seed_knowledge()
    except Exception:
        pass
    try:
        hits = col.query(query, k=k)
    except Exception as e:
        logger.warning("RAG query failed: %s", e)
        return []
    out = []
    for h in hits:
        meta = h.get("metadata", {})
        src = meta.get("source", "policy")
        section = meta.get("section", "")
        citation = f"{src}" + (f" §{section}" if section else "")
        out.append({"snippet": h["text"], "source": src, "section": section,
                    "citation": citation, "score": h.get("score", 0.0)})
    return out


def build_grounding_block(snippets: List[Dict]) -> str:
    """Turn retrieved snippets into a cited context block for prompt injection."""
    if not snippets:
        return ""
    lines = ["=== POLICY CONTEXT (cite each claim using the [source] tags) ==="]
    for s in snippets:
        lines.append(f"[{s['citation']}] {s['snippet']}")
    lines.append("=== END POLICY CONTEXT ===")
    return "\n".join(lines)


def rag_stats() -> Dict:
    from app.ml.embeddings import active_tier

    col = vector_store.get_collection(KNOWLEDGE_COLLECTION)
    try:
        n = col.count()
    except Exception:
        n = 0
    return {
        "knowledge_chunks": n,
        "vector_backend": vector_store.active_backend(),
        "embedding_tier": active_tier(),
        "top_k": settings.RAG_TOP_K,
    }
