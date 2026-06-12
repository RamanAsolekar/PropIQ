"""
PropIQ Bootstrap — idempotent startup seeding.

Centralizes the "make sure reference data exists" logic so it runs from one
place (the FastAPI startup hook) instead of only via the manual
`scripts/seed_db.py`. Safe to call repeatedly — it no-ops when already seeded.
"""

import logging

logger = logging.getLogger(__name__)


def ensure_circle_rates_seeded() -> int:
    """
    Seed the `circle_rates` table from the static india_circle_rates dataset
    if the table is empty. Returns the number of rows inserted (0 if already
    seeded). The DB is the source of truth at runtime; the static dict is the
    seed + offline fallback.
    """
    from app.core.db import Base, SessionLocal, engine
    from app.data.india_circle_rates import ALL_CIRCLE_RATES
    from app.models.db_models import CircleRate

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(CircleRate).first():
            return 0

        records = []
        for locality, data in ALL_CIRCLE_RATES.items():
            records.append(
                CircleRate(
                    city=data.get("city", "Pune"),
                    locality=locality,
                    zone_tier=data["zone_tier"],
                    residential_apartment=data["residential_apartment"],
                    commercial_shop=data["commercial_shop"],
                    commercial_office=data["commercial_office"],
                    industrial=data["industrial"],
                    residential_plot=data["residential_plot"],
                    lat=data.get("lat"),
                    lon=data.get("lon"),
                )
            )
        db.bulk_save_objects(records)
        db.commit()
        logger.info("Seeded %d circle rates into DB.", len(records))
        return len(records)
    except Exception as e:
        db.rollback()
        logger.error("Circle-rate seed failed: %s", e)
        raise
    finally:
        db.close()
