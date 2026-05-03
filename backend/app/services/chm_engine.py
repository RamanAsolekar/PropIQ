"""
PropIQ Collateral Health Monitor (CHM) Engine
Re-assesses active loan collaterals and fires alerts when LTV drifts.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List

from app.core.db import SessionLocal
from app.models.db_models import ActiveLoan, CollateralHealthSnapshot
from app.models.schemas import PropertyInput
from app.services.email_alerts import send_alert_email

logger = logging.getLogger(__name__)

# LTV thresholds
LTV_RED = 0.80  # Breach — immediate action
LTV_AMBER = 0.70  # Warning — monitor closely

# ── Seed data ─────────────────────────────────────────────────────────────────
DEMO_LOANS = [
    {
        "loan_id": "PF-1001",
        "borrower_name": "Rajesh Sharma",
        "borrower_email": "rajesh.sharma@demo.com",
        "locality": "Baner",
        "prop_type": "2bhk_apartment",
        "size_sqft": 850.0,
        "age_years": 3.0,
        "floor_num": 5,
        "loan_amount": 7_000_000,
        "original_value": 10_800_000,
        "disbursed_on": datetime(2022, 6, 15),
    },
    {
        "loan_id": "PF-1002",
        "borrower_name": "Priya Mehta",
        "borrower_email": "priya.mehta@demo.com",
        "locality": "Virar",
        "prop_type": "1bhk_apartment",
        "size_sqft": 450.0,
        "age_years": 9.0,
        "floor_num": 2,
        "loan_amount": 3_200_000,
        "original_value": 4_100_000,
        "disbursed_on": datetime(2021, 3, 10),
    },
    {
        "loan_id": "PF-1003",
        "borrower_name": "Anil Kapoor",
        "borrower_email": "anil.kapoor@demo.com",
        "locality": "Koramangala",
        "prop_type": "3bhk_apartment",
        "size_sqft": 1400.0,
        "age_years": 5.0,
        "floor_num": 8,
        "loan_amount": 16_000_000,
        "original_value": 24_000_000,
        "disbursed_on": datetime(2023, 1, 20),
    },
    {
        "loan_id": "PF-1004",
        "borrower_name": "Sunita Desai",
        "borrower_email": "sunita.desai@demo.com",
        "locality": "Hadapsar",
        "prop_type": "shop",
        "size_sqft": 600.0,
        "age_years": 14.0,
        "floor_num": 0,
        "loan_amount": 4_800_000,
        "original_value": 5_800_000,  # Intentionally high original so LTV looks stressed
        "disbursed_on": datetime(2020, 8, 5),
    },
    {
        "loan_id": "PF-1005",
        "borrower_name": "Vikram Nair",
        "borrower_email": "vikram.nair@demo.com",
        "locality": "Thane",
        "prop_type": "2bhk_apartment",
        "size_sqft": 750.0,
        "age_years": 13.0,
        "floor_num": 3,
        "loan_amount": 7_500_000,
        "original_value": 9_500_000,
        "disbursed_on": datetime(2021, 11, 1),
    },
    {
        "loan_id": "PF-1006",
        "borrower_name": "Kavita Joshi",
        "borrower_email": "kavita.joshi@demo.com",
        "locality": "Whitefield",
        "prop_type": "3bhk_apartment",
        "size_sqft": 1200.0,
        "age_years": 4.0,
        "floor_num": 6,
        "loan_amount": 9_000_000,
        "original_value": 14_000_000,
        "disbursed_on": datetime(2023, 5, 18),
    },
    {
        "loan_id": "PF-1007",
        "borrower_name": "Suresh Patil",
        "borrower_email": "suresh.patil@demo.com",
        "locality": "Wagholi",
        "prop_type": "2bhk_apartment",
        "size_sqft": 700.0,
        "age_years": 6.0,
        "floor_num": 2,
        "loan_amount": 3_600_000,
        "original_value": 4_500_000,
        "disbursed_on": datetime(2022, 2, 14),
    },
    {
        "loan_id": "PF-1008",
        "borrower_name": "Meena Iyer",
        "borrower_email": "meena.iyer@demo.com",
        "locality": "Andheri West",
        "prop_type": "2bhk_apartment",
        "size_sqft": 900.0,
        "age_years": 8.0,
        "floor_num": 7,
        "loan_amount": 13_000_000,
        "original_value": 18_500_000,
        "disbursed_on": datetime(2022, 9, 30),
    },
    {
        "loan_id": "PF-1009",
        "borrower_name": "Deepak Rajan",
        "borrower_email": "deepak.rajan@demo.com",
        "locality": "Katraj",
        "prop_type": "plot",
        "size_sqft": 2400.0,
        "age_years": 0.0,
        "floor_num": 0,
        "loan_amount": 5_500_000,
        "original_value": 8_000_000,
        "disbursed_on": datetime(2023, 7, 12),
    },
    {
        "loan_id": "PF-1010",
        "borrower_name": "Anjali Singh",
        "borrower_email": "anjali.singh@demo.com",
        "locality": "Indiranagar",
        "prop_type": "office",
        "size_sqft": 1100.0,
        "age_years": 7.0,
        "floor_num": 4,
        "loan_amount": 11_000_000,
        "original_value": 14_500_000,
        "disbursed_on": datetime(2021, 6, 22),
    },
]


def seed_demo_loans():
    """Insert demo loans if the table is empty."""
    db = SessionLocal()
    try:
        if db.query(ActiveLoan).count() > 0:
            return
        for data in DEMO_LOANS:
            loan = ActiveLoan(
                **{k: v for k, v in data.items()},
                original_ltv=data["loan_amount"] / data["original_value"],
            )
            db.add(loan)
        db.commit()
        logger.info(f"Seeded {len(DEMO_LOANS)} demo loans for CHM.")
    except Exception as e:
        logger.error(f"Failed to seed demo loans: {e}")
        db.rollback()
    finally:
        db.close()


async def assess_loan_health(loan: ActiveLoan) -> dict:
    """
    Re-run the PropIQ valuation model on a loan's collateral and
    compute the current LTV + risk level.
    """
    from app.main import _run_assessment  # late import to avoid circular

    # Age advances since disbursement
    years_elapsed = (datetime.now() - loan.disbursed_on).days / 365.25
    current_age = round(loan.age_years + years_elapsed, 1)

    prop = PropertyInput(
        locality=loan.locality,
        prop_type=loan.prop_type,
        size_sqft=loan.size_sqft,
        age_years=current_age,
        floor_num=loan.floor_num or 3,
        geo_lat=loan.geo_lat,
        geo_lon=loan.geo_lon,
    )

    try:
        result = await _run_assessment(prop)
        current_value = float(result["market_value_mid"])
    except Exception as e:
        logger.error(f"Valuation failed for loan {loan.loan_id}: {e}")
        current_value = loan.original_value  # fallback: no change

    current_ltv = loan.loan_amount / current_value
    delta_pct = (current_value - loan.original_value) / loan.original_value * 100

    if current_ltv >= LTV_RED:
        risk_level = "red"
    elif current_ltv >= LTV_AMBER:
        risk_level = "amber"
    else:
        risk_level = "green"

    return {
        "loan_id": loan.loan_id,
        "current_value": current_value,
        "current_ltv": round(current_ltv, 4),
        "risk_level": risk_level,
        "delta_pct": round(delta_pct, 2),
        "alert_fired": 1 if risk_level in ("red", "amber") else 0,
    }


async def assess_loan_stress(loan: ActiveLoan, shock_pct: float) -> dict:
    """
    Run the PropIQ valuation model, apply a market shock (e.g. -20%),
    and compute the stressed LTV.
    """
    base_assessment = await assess_loan_health(loan)

    # Apply shock to the current market value
    shock_multiplier = 1.0 + (shock_pct / 100.0)
    stressed_value = base_assessment["current_value"] * shock_multiplier

    stressed_ltv = loan.loan_amount / stressed_value
    delta_pct = (stressed_value - loan.original_value) / loan.original_value * 100

    if stressed_ltv >= LTV_RED:
        risk_level = "red"
    elif stressed_ltv >= LTV_AMBER:
        risk_level = "amber"
    else:
        risk_level = "green"

    return {
        "loan_id": loan.loan_id,
        "borrower_name": loan.borrower_name,
        "borrower_email": loan.borrower_email,
        "locality": loan.locality,
        "prop_type": loan.prop_type,
        "loan_amount": loan.loan_amount,
        "original_value": loan.original_value,
        "base_value": base_assessment["current_value"],
        "stressed_value": stressed_value,
        "base_ltv": base_assessment["current_ltv"],
        "stressed_ltv": round(stressed_ltv, 4),
        "risk_level": risk_level,
        "delta_pct": round(delta_pct, 2),
        "is_underwater": 1 if stressed_ltv > 1.0 else 0,
    }


async def run_portfolio_health_check() -> dict:
    """
    Run health check on ALL active loans.
    Saves snapshots to DB and fires email alerts for red/amber.
    Returns summary stats.
    """
    db = SessionLocal()
    try:
        loans = db.query(ActiveLoan).filter(ActiveLoan.status == "active").all()
        if not loans:
            return {"checked": 0, "alerts": 0, "snapshots": []}

        # Run all assessments concurrently
        assessments = await asyncio.gather(
            *[assess_loan_health(loan) for loan in loans], return_exceptions=True
        )

        snapshots_out = []
        alert_count = 0

        for loan, assessment in zip(loans, assessments):
            if isinstance(assessment, Exception):
                logger.error(f"Health check error for {loan.loan_id}: {assessment}")
                continue

            # Persist snapshot
            snap = CollateralHealthSnapshot(**assessment)
            db.add(snap)

            # Send email for alerts
            email_sent = 0
            if assessment["alert_fired"]:
                alert_count += 1
                loan_dict = {
                    "loan_id": loan.loan_id,
                    "borrower_name": loan.borrower_name,
                    "borrower_email": loan.borrower_email,
                    "locality": loan.locality,
                    "prop_type": loan.prop_type,
                    "size_sqft": loan.size_sqft,
                    "age_years": loan.age_years,
                    "loan_amount": loan.loan_amount,
                    "original_value": loan.original_value,
                }
                email_sent = 1 if send_alert_email(loan_dict, assessment) else 0
                snap.email_sent = email_sent

            snapshots_out.append(
                {
                    **assessment,
                    "borrower_name": loan.borrower_name,
                    "locality": loan.locality,
                    "prop_type": loan.prop_type,
                    "size_sqft": loan.size_sqft,
                    "loan_amount": loan.loan_amount,
                    "original_value": loan.original_value,
                    "email_sent": email_sent,
                }
            )

        db.commit()
        return {
            "checked": len(loans),
            "alerts": alert_count,
            "red": sum(1 for s in snapshots_out if s["risk_level"] == "red"),
            "amber": sum(1 for s in snapshots_out if s["risk_level"] == "amber"),
            "green": sum(1 for s in snapshots_out if s["risk_level"] == "green"),
            "snapshots": snapshots_out,
            "assessed_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Portfolio health check failed: {e}")
        raise
    finally:
        db.close()


async def run_stress_test(shock_pct: float) -> dict:
    """
    Apply a macro-economic shock to the entire portfolio.
    Returns the stressed metrics and identifies loans that fall underwater.
    """
    db = SessionLocal()
    try:
        loans = db.query(ActiveLoan).filter(ActiveLoan.status == "active").all()
        if not loans:
            return {"checked": 0, "underwater": 0, "results": []}

        # Run all stressed assessments concurrently
        assessments = await asyncio.gather(
            *[assess_loan_stress(loan, shock_pct) for loan in loans],
            return_exceptions=True,
        )

        results = []
        underwater_count = 0
        from app.services.llm_narration import generate_risk_escalation_alert

        for loan, assessment in zip(loans, assessments):
            if isinstance(assessment, Exception):
                logger.error(f"Stress test error for {loan.loan_id}: {assessment}")
                continue

            # Generate Risk Escalation Alert if LTV > 100% (Underwater)
            if assessment["is_underwater"]:
                underwater_count += 1
                try:
                    alert_memo = await generate_risk_escalation_alert(assessment)
                    assessment["risk_escalation_memo"] = alert_memo
                except Exception as e:
                    logger.error(
                        f"Failed to generate risk alert for {loan.loan_id}: {e}"
                    )
                    assessment["risk_escalation_memo"] = None

            results.append(assessment)

        return {
            "checked": len(loans),
            "shock_applied_pct": shock_pct,
            "underwater_count": underwater_count,
            "red_count": sum(1 for r in results if r["risk_level"] == "red"),
            "results": results,
            "simulated_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        db.close()


def get_portfolio_latest() -> list:
    """Get the most recent snapshot for each active loan."""
    db = SessionLocal()
    try:
        loans = db.query(ActiveLoan).filter(ActiveLoan.status == "active").all()
        result = []
        for loan in loans:
            snap = (
                db.query(CollateralHealthSnapshot)
                .filter(CollateralHealthSnapshot.loan_id == loan.loan_id)
                .order_by(CollateralHealthSnapshot.id.desc())
                .first()
            )
            result.append(
                {
                    "loan_id": loan.loan_id,
                    "borrower_name": loan.borrower_name,
                    "locality": loan.locality,
                    "prop_type": loan.prop_type,
                    "size_sqft": loan.size_sqft,
                    "loan_amount": loan.loan_amount,
                    "original_value": loan.original_value,
                    "original_ltv": round(loan.original_ltv * 100, 1),
                    "disbursed_on": loan.disbursed_on.isoformat(),
                    "status": loan.status,
                    "latest_snapshot": (
                        {
                            "current_value": snap.current_value,
                            "current_ltv": round(snap.current_ltv * 100, 1),
                            "risk_level": snap.risk_level,
                            "delta_pct": snap.delta_pct,
                            "alert_fired": snap.alert_fired,
                            "assessed_on": (
                                snap.assessed_on.isoformat()
                                if snap.assessed_on
                                else None
                            ),
                        }
                        if snap
                        else None
                    ),
                }
            )
        return result
    finally:
        db.close()


def get_loan_history(loan_id: str) -> list:
    """Get all health snapshots for a single loan."""
    db = SessionLocal()
    try:
        snaps = (
            db.query(CollateralHealthSnapshot)
            .filter(CollateralHealthSnapshot.loan_id == loan_id)
            .order_by(CollateralHealthSnapshot.id.desc())
            .all()
        )
        return [
            {
                "assessed_on": s.assessed_on.isoformat() if s.assessed_on else None,
                "current_value": s.current_value,
                "current_ltv": round(s.current_ltv * 100, 1),
                "risk_level": s.risk_level,
                "delta_pct": s.delta_pct,
                "alert_fired": s.alert_fired,
                "email_sent": s.email_sent,
            }
            for s in snaps
        ]
    finally:
        db.close()
