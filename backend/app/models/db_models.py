"""
SQLAlchemy ORM models for properties, valuations, and audit logs.
"""

from app.core.db import Base
from sqlalchemy import (JSON, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.sql import func


class CircleRate(Base):
    """Replacement for static india_circle_rates.py"""

    __tablename__ = "circle_rates"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True, nullable=False)
    locality = Column(String, index=True, unique=True, nullable=False)
    zone_tier = Column(String, nullable=False)  # prime, mid, peripheral
    residential_apartment = Column(Float, nullable=False)
    commercial_shop = Column(Float, nullable=False)
    commercial_office = Column(Float, nullable=False)
    industrial = Column(Float, nullable=False)
    residential_plot = Column(Float, nullable=False)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    locality = Column(String, index=True, nullable=False)
    prop_type = Column(String, index=True, nullable=False)
    size_sqft = Column(Float, nullable=False)
    age_years = Column(Float, nullable=False)
    floor_num = Column(Integer, default=3)
    is_freehold = Column(Integer, default=1)
    is_rera_registered = Column(Integer, default=1)
    occupancy = Column(String, default="self_occupied")
    rental_yield_pct = Column(Float, default=0.0)
    geo_lat = Column(Float, nullable=True)
    geo_lon = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ValuationResult(Base):
    __tablename__ = "valuation_results"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    base_value_estimate = Column(Float, nullable=False)
    p10_estimate = Column(Float, nullable=False)
    p90_estimate = Column(Float, nullable=False)
    price_per_sqft_estimate = Column(Float, nullable=False)
    cv_condition = Column(String, nullable=True)
    cv_adjustment_factor = Column(Float, nullable=True)
    rpi_score = Column(Float, nullable=True)
    max_ltv_pct = Column(Float, nullable=True)
    shap_values = Column(JSON, nullable=True)
    credit_memo = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String, index=True, nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)
    request_payload = Column(JSON, nullable=True)
    response_payload = Column(JSON, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ActiveLoan(Base):
    """Represents a disbursed loan under collateral health monitoring."""

    __tablename__ = "active_loans"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(String, unique=True, index=True, nullable=False)
    borrower_name = Column(String, nullable=False)
    borrower_email = Column(String, nullable=True)
    locality = Column(String, nullable=False)
    prop_type = Column(String, nullable=False)
    size_sqft = Column(Float, nullable=False)
    age_years = Column(Float, nullable=False)
    floor_num = Column(Integer, default=3)
    geo_lat = Column(Float, nullable=True)
    geo_lon = Column(Float, nullable=True)
    loan_amount = Column(Float, nullable=False)
    original_value = Column(Float, nullable=False)
    original_ltv = Column(Float, nullable=False)
    disbursed_on = Column(DateTime, nullable=False)
    status = Column(String, default="active")  # active | npa | closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CollateralHealthSnapshot(Base):
    """Point-in-time health assessment of a loan's collateral."""

    __tablename__ = "collateral_health_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(String, index=True, nullable=False)
    assessed_on = Column(DateTime(timezone=True), server_default=func.now())
    current_value = Column(Float, nullable=False)
    current_ltv = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)  # green | amber | red
    delta_pct = Column(Float, nullable=False)  # % change vs original
    alert_fired = Column(Integer, default=0)
    email_sent = Column(Integer, default=0)
    snapshot_detail = Column(JSON, nullable=True)


class PredictionLog(Base):
    """
    Every model prediction is logged here with its feature vector + model version.
    This is the foundation of the realized-outcome loop and drift monitoring —
    without it the model can never be validated against reality (audit gap G2).
    """

    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    model_version = Column(String, index=True, nullable=True)
    feature_schema_version = Column(String, nullable=True)
    locality = Column(String, index=True, nullable=True)
    prop_type = Column(String, index=True, nullable=True)
    predicted_value_mid = Column(Float, nullable=False)
    predicted_p10 = Column(Float, nullable=True)
    predicted_p90 = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    resale_potential_index = Column(Float, nullable=True)
    feature_vector = Column(JSON, nullable=True)  # for drift reference
    endpoint = Column(String, default="/assess")


class RealizedOutcome(Base):
    """
    The ground truth: what the property ACTUALLY sold / was recovered for.
    Joined back to PredictionLog by request_id to compute true error and feed
    automated retraining. This is the proprietary data flywheel.
    """

    __tablename__ = "realized_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True, nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    outcome_type = Column(String, nullable=False)  # sale | auction_recovery | revaluation
    realized_value = Column(Float, nullable=False)
    realized_on = Column(DateTime, nullable=True)
    days_to_liquidate = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    # Computed at write time for fast querying
    abs_pct_error = Column(Float, nullable=True)
    signed_pct_error = Column(Float, nullable=True)
