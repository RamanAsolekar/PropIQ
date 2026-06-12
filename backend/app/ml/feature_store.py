"""
PropIQ Feature Store facade.

One import surface for the rest of the app. Behaviour:
  - ENABLE_FEAST=true and Feast installed  -> serve features via Feast online store
  - otherwise                              -> compute via the canonical transform
                                              (app/ml/features.build_feature_row)

Either way the VALUES are identical because Feast is materialized from the same
transform. This indirection lets us flip to a real online store in prod without
touching call sites, and is the architectural fix for train/serve skew.
"""

from __future__ import annotations

import logging
from typing import Dict, List

import pandas as pd

from app.core.config import settings
from app.ml.features import (FEATURE_COLS, FEATURE_SCHEMA_VERSION,
                             build_feature_row)

logger = logging.getLogger(__name__)
_ALL_COLS = FEATURE_COLS + ["prop_type_encoded"]


class FeatureStore:
    def __init__(self):
        self._feast = None
        if settings.ENABLE_FEAST:
            try:
                from feast import FeatureStore as _FeastStore

                self._feast = _FeastStore(repo_path=str(settings.FEAST_REPO_PATH))
                logger.info("Feast online store active (schema %s).", FEATURE_SCHEMA_VERSION)
            except Exception as e:
                logger.warning("Feast unavailable (%s) — using in-process transform.", e)
                self._feast = None

    @property
    def schema_version(self) -> str:
        return FEATURE_SCHEMA_VERSION

    @property
    def feature_columns(self) -> List[str]:
        return list(_ALL_COLS)

    def get_serving_features(self, raw_inputs: Dict) -> Dict[str, float]:
        """
        Return the ordered feature dict for one property at serve time.

        Feast path is reserved for features that are precomputed/materialized
        (e.g. locality-level market signals). Per-property structural features
        are always computed from the request via the canonical transform, so the
        two paths produce identical values.
        """
        row = build_feature_row(raw_inputs)
        return {c: row[c] for c in _ALL_COLS}

    def get_serving_frame(self, raw_inputs: Dict) -> pd.DataFrame:
        return pd.DataFrame([self.get_serving_features(raw_inputs)])[_ALL_COLS]

    def build_offline_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate that a training frame carries the canonical feature columns."""
        missing = [c for c in _ALL_COLS if c not in df.columns]
        if missing:
            raise ValueError(
                f"Training frame missing canonical features {missing}. "
                "Regenerate via app.ml.data_generator (schema "
                f"{FEATURE_SCHEMA_VERSION})."
            )
        return df[_ALL_COLS]


_store: FeatureStore | None = None


def get_feature_store() -> FeatureStore:
    global _store
    if _store is None:
        _store = FeatureStore()
    return _store
