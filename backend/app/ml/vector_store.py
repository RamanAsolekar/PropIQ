"""
PropIQ Vector Store — pluggable similarity search.

Backends (auto-selected):
  - chroma   : persistent local ChromaDB at settings.CHROMA_DIR (no server)
  - memory   : pure-numpy cosine over an in-process + JSON-persisted list
               (always available; the graceful-degradation default)
  - pgvector : reserved for prod (Postgres + vector ext); falls back if absent

One interface for RAG (knowledge collection) AND fraud/duplicate detection
(properties collection). Mirrors the "local file store, no server required"
pattern used by MLflow and comps.db.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from app.core.config import settings
from app.ml.embeddings import cosine, embed

logger = logging.getLogger(__name__)


def _resolve_backend() -> str:
    want = settings.VECTOR_BACKEND
    if want in ("chroma", "memory", "pgvector"):
        if want == "chroma":
            try:
                import chromadb  # noqa: F401

                return "chroma"
            except Exception:
                return "memory"
        return want if want != "pgvector" else "memory"
    # auto
    try:
        import chromadb  # noqa: F401

        return "chroma"
    except Exception:
        return "memory"


class _MemoryCollection:
    """JSON-persisted in-memory cosine index."""

    def __init__(self, name: str):
        self.name = name
        self.path = settings.DATA_DIR / "vectorstore" / f"{name}.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._items: Dict[str, dict] = {}
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text())
                for it in raw:
                    self._items[it["id"]] = it
            except Exception:
                pass

    def _persist(self):
        try:
            self.path.write_text(json.dumps(list(self._items.values())))
        except Exception as e:
            logger.warning("vector persist failed: %s", e)

    def upsert(self, doc_id: str, text: str, metadata: dict):
        vec = embed([text])[0].tolist()
        self._items[doc_id] = {
            "id": doc_id, "text": text, "metadata": metadata or {}, "vec": vec
        }
        self._persist()

    def query(self, text: str, k: int, where: Optional[dict] = None) -> List[dict]:
        if not self._items:
            return []
        q = embed([text])[0]
        results = []
        for it in self._items.values():
            if where and any(it["metadata"].get(kk) != vv for kk, vv in where.items()):
                continue
            score = cosine(q, np.asarray(it["vec"], dtype=np.float32))
            results.append({"id": it["id"], "text": it["text"],
                            "metadata": it["metadata"], "score": round(score, 4)})
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:k]

    def count(self) -> int:
        return len(self._items)


class _ChromaCollection:
    def __init__(self, name: str):
        import chromadb

        self.name = name
        self._client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
        # Force COSINE distance. Chroma defaults to squared-L2, which (a) does
        # not match the in-memory backend's true cosine — so scores were on
        # different scales across backends — and (b) makes the `1 - distance`
        # score conversion below invalid. With cosine space, distance is in
        # [0, 2] and `1 - distance` is a proper cosine similarity in [-1, 1],
        # identical to the memory backend.
        self._col = self._client.get_or_create_collection(
            name=name, metadata={"hnsw:space": "cosine"}
        )

    def upsert(self, doc_id: str, text: str, metadata: dict):
        vec = embed([text])[0].tolist()
        self._col.upsert(ids=[doc_id], embeddings=[vec], documents=[text],
                         metadatas=[metadata or {}])

    def query(self, text: str, k: int, where: Optional[dict] = None) -> List[dict]:
        vec = embed([text])[0].tolist()
        kwargs = dict(query_embeddings=[vec], n_results=k)
        if where:
            kwargs["where"] = where
        res = self._col.query(**kwargs)
        out = []
        ids = (res.get("ids") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        for i, _id in enumerate(ids):
            # Cosine space (set at collection creation): distance in [0, 2],
            # so similarity = 1 - distance in [-1, 1], matching the memory backend.
            dist = dists[i] if i < len(dists) else 0.0
            out.append({"id": _id, "text": docs[i] if i < len(docs) else "",
                        "metadata": metas[i] if i < len(metas) else {},
                        "score": round(1.0 - float(dist), 4)})
        return out

    def count(self) -> int:
        try:
            return self._col.count()
        except Exception:
            return 0


_collections: Dict[str, object] = {}
_backend: Optional[str] = None


def get_collection(name: str):
    global _backend
    if _backend is None:
        _backend = _resolve_backend()
        logger.info("Vector store backend: %s", _backend)
    if name not in _collections:
        if _backend == "chroma":
            try:
                _collections[name] = _ChromaCollection(name)
            except Exception as e:
                logger.warning("Chroma init failed (%s) — memory backend.", e)
                _collections[name] = _MemoryCollection(name)
        else:
            _collections[name] = _MemoryCollection(name)
    return _collections[name]


def active_backend() -> str:
    global _backend
    if _backend is None:
        _backend = _resolve_backend()
    return _backend
