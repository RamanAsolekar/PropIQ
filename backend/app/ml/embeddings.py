"""
PropIQ Embeddings — text -> vector, with graceful degradation.

Tiers (auto-selected, best available first):
  1. sentence-transformers (all-MiniLM-L6-v2)  — real semantic embeddings
  2. hashing / TF-IDF-style (pure numpy)        — deterministic fallback, always works

The hashing fallback is a feature-hashing bag-of-words with L2 norm: it gives
stable, reproducible vectors with NO heavy dependency, so RAG, duplicate
detection and the KG all work out of the box. Same pattern as the CV module's
"Groq VLM when available, deterministic hash fallback otherwise".
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import List

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

_st_model = None  # cached sentence-transformers model
_st_tried = False


def _get_st_model():
    global _st_model, _st_tried
    if _st_tried:
        return _st_model
    _st_tried = True
    try:
        from sentence_transformers import SentenceTransformer

        _st_model = SentenceTransformer(settings.EMBEDDINGS_MODEL)
        logger.info("Embeddings: sentence-transformers (%s).", settings.EMBEDDINGS_MODEL)
    except Exception as e:
        logger.info("Embeddings: hashing fallback (sentence-transformers absent: %s).", e)
        _st_model = None
    return _st_model


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


def _hash_embed_one(text: str, dim: int) -> np.ndarray:
    """Deterministic feature-hashing embedding (bag-of-words, signed, L2-normed)."""
    vec = np.zeros(dim, dtype=np.float32)
    tokens = _tokenize(text)
    if not tokens:
        return vec
    for tok in tokens:
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
        vec[idx] += sign
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def embed(texts: List[str]) -> np.ndarray:
    """Embed a list of texts. Returns (n, dim) float32 array. Never raises."""
    if isinstance(texts, str):
        texts = [texts]
    model = _get_st_model()
    if model is not None:
        try:
            arr = np.asarray(model.encode(texts, normalize_embeddings=True), dtype=np.float32)
            return arr
        except Exception as e:
            logger.warning("ST encode failed (%s) — hashing fallback.", e)
    dim = settings.EMBEDDING_DIM
    return np.vstack([_hash_embed_one(t, dim) for t in texts])


def embed_one(text: str) -> np.ndarray:
    return embed([text])[0]


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def active_tier() -> str:
    return "sentence_transformers" if _get_st_model() is not None else "hashing_fallback"
