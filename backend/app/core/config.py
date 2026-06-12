"""
PropIQ Central Configuration
All environment variables and constants in one place.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent.parent  # backend/

# Load .env from backend/ first, then fall back to project root (../)
_env_backend = BASE_DIR / ".env"
_env_root = BASE_DIR.parent / ".env"
if _env_backend.exists():
    load_dotenv(_env_backend, override=False)
if _env_root.exists():
    load_dotenv(_env_root, override=False)


class Settings:
    # App
    APP_NAME: str = "PropIQ"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Paths
    DATA_DIR: Path = BASE_DIR / "data"
    MODEL_DIR: Path = BASE_DIR / "data" / "models"
    RAW_DIR: Path = BASE_DIR / "data" / "raw"
    PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"

    # API
    API_PREFIX: str = "/api/v1"
    # CORS — env-driven allow-list. Defaults to local dev origins instead of "*".
    # Set CORS_ORIGINS="https://app.example.com,https://admin.example.com" in prod.
    CORS_ORIGINS: list = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if o.strip()
    ]

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # ── MLOps stack toggles (graceful degradation when servers absent) ──────
    # MLflow: if MLFLOW_TRACKING_URI unset, falls back to local file store.
    MLFLOW_TRACKING_URI: str = os.getenv(
        "MLFLOW_TRACKING_URI", f"file:{(BASE_DIR / 'data' / 'mlruns').as_posix()}"
    )
    MLFLOW_EXPERIMENT: str = os.getenv("MLFLOW_EXPERIMENT", "propiq-valuation")
    # Feast feature repo (local registry by default — no server needed)
    FEAST_REPO_PATH: Path = BASE_DIR / "feature_repo"
    ENABLE_FEAST: bool = os.getenv("ENABLE_FEAST", "false").lower() == "true"
    # Drift monitoring
    DRIFT_PSI_WARN: float = float(os.getenv("DRIFT_PSI_WARN", "0.1"))
    DRIFT_PSI_ALERT: float = float(os.getenv("DRIFT_PSI_ALERT", "0.25"))

    # ── AIML capability layer (all optional, graceful degradation) ──────────
    # LLM provider routing (only "groq" wired today; abstraction allows swap)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    LLM_AGENT_PROVIDER: str = os.getenv("LLM_AGENT_PROVIDER", "groq")
    # RAG / vector search
    VECTOR_BACKEND: str = os.getenv("VECTOR_BACKEND", "auto")  # auto|chroma|pgvector|memory
    CHROMA_DIR: Path = BASE_DIR / "data" / "chroma"
    KNOWLEDGE_DIR: Path = BASE_DIR / "app" / "data" / "knowledge"
    EMBEDDINGS_MODEL: str = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "256"))  # hashing-fallback dim
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "4"))
    # Fraud / duplicate detection
    DUPLICATE_SIM_THRESHOLD: float = float(os.getenv("DUPLICATE_SIM_THRESHOLD", "0.92"))
    # Forecasting
    FORECAST_ENGINE: str = os.getenv("FORECAST_ENGINE", "auto")  # auto|prophet|statsmodels|numpy
    # Knowledge graph
    KG_BACKEND: str = os.getenv("KG_BACKEND", "auto")  # auto|networkx|dict

    # Model
    MODEL_FILE: str = "propiq_model.pkl"
    MODEL_META_FILE: str = "model_meta.json"

    # Enrichment
    NOMINATIM_URL: str = "https://nominatim.openstreetmap.org/search"
    OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"
    OVERPASS_TIMEOUT: int = 8
    GEOCODE_TIMEOUT: int = 5

    # Infra score fallbacks when OSM is unavailable
    INFRA_SCORE_FALLBACK: dict = {
        "prime": 72,
        "mid": 52,
        "peripheral": 32,
    }

    # CV Module
    CLIP_MODEL_NAME: str = "openai/clip-vit-base-patch32"
    CV_ENABLED: bool = True

    # PDF
    PDF_BRAND_COLOR: str = "#534AB7"
    PDF_TEAL_COLOR: str = "#0F6E56"


settings = Settings()
