"""
PropIQ Valuation Model
- XGBoost quantile regression (P10, P50, P90) for honest price ranges
- SHAP explainability for every prediction
- Deep Liquidity Engine v2 (3-tier distress, absorption rates)
- Improved 7-factor confidence scoring
- Rental Income Cross-Check Valuation
"""

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.model_selection import KFold
from xgboost import XGBRegressor

# Canonical feature contract — single source of truth shared by training AND
# serving (train/serve skew fix). Do not redefine features here.
from app.ml.features import (FEATURE_COLS, FEATURE_SCHEMA_VERSION,
                             PROP_TYPE_ENCODING, build_feature_row)

DISTRESS_BASE_BY_TYPE = {
    "1bhk_apartment": 0.18,
    "2bhk_apartment": 0.17,
    "3bhk_apartment": 0.18,
    "4bhk_apartment": 0.20,
    "villa": 0.22,
    "shop": 0.28,
    "office": 0.30,
    "plot": 0.25,
    "warehouse": 0.33,
    "factory": 0.36,
}

BASE_DAYS_TO_SELL = {
    "1bhk_apartment": 35,
    "2bhk_apartment": 45,
    "3bhk_apartment": 55,
    "4bhk_apartment": 90,
    "villa": 120,
    "shop": 100,
    "office": 130,
    "plot": 75,
    "warehouse": 160,
    "factory": 200,
}

COMMERCIAL_PROP_TYPES = {"shop", "office"}
INDUSTRIAL_PROP_TYPES = {"warehouse", "factory"}
RESIDENTIAL_PROP_TYPES = {
    "1bhk_apartment",
    "2bhk_apartment",
    "3bhk_apartment",
    "4bhk_apartment",
    "villa",
    "plot",
}

SIZE_SANITY_BOUNDS = {
    "1bhk_apartment": (250, 700),
    "2bhk_apartment": (500, 1400),
    "3bhk_apartment": (900, 2500),
    "4bhk_apartment": (1500, 5000),
    "villa": (1000, 10000),
    "shop": (100, 3000),
    "office": (200, 10000),
    "plot": (500, 50000),
    "warehouse": (1000, 50000),
    "factory": (2500, 200000),
}

FEATURE_LABEL_MAP = {
    "circle_rate_per_sqft": "circle_rate_benchmark",
    "infra_score": "infrastructure_proximity",
    "neighbourhood_quality_score": "neighbourhood_quality",
    "size_sqft": "property_size",
    "age_years": "building_age",
    "age_depreciation_factor": "depreciation_factor",
    "location_multiplier": "location_premium",
    "listing_density": "market_demand_density",
    "is_standard_config": "standard_configuration",
    "is_freehold": "freehold_title",
    "is_rera_registered": "rera_compliance",
    "rental_yield_pct": "rental_yield",
    "floor_num": "floor_level",
    "micro_market_cycle": "market_cycle_momentum",
    "buyer_pool_depth_index": "buyer_pool_depth",
    "comp_velocity_score": "comparable_sales_velocity",
}


class PropIQModel:
    def __init__(self):
        self.model_p10 = None
        self.model_p50 = None
        self.model_p90 = None
        self.model_liquidity = None
        self.anomaly_detector = None
        self.shap_explainer = None
        self.feature_cols_full = FEATURE_COLS + ["prop_type_encoded"]
        self.mape_validation = None
        self.feature_schema_version = FEATURE_SCHEMA_VERSION
        self.train_metadata = {}  # populated by train(); logged to registry

    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if "prop_type" in df.columns:
            df["prop_type_encoded"] = df["prop_type"].map(PROP_TYPE_ENCODING).fillna(1)
        for col in self.feature_cols_full:
            if col not in df.columns:
                df[col] = 0.0
        return df[self.feature_cols_full]

    def train(self, df: pd.DataFrame):
        X = self._prepare_features(df)
        y_price = np.log1p(df["price_per_sqft"])
        y_liq = df["liquidity_score"]

        xgb_params = dict(
            n_estimators=400,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
        )

        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        mape_scores = []
        r2_scores = []
        coverage_scores = []  # P10–P90 interval coverage (calibration)

        from sklearn.metrics import r2_score

        print("Running 5-Fold Cross Validation for robust evaluation...")
        for train_idx, val_idx in kf.split(X):
            X_tr, X_va = X.iloc[train_idx], X.iloc[val_idx]
            y_tr, y_va = y_price.iloc[train_idx], y_price.iloc[val_idx]

            model = XGBRegressor(
                objective="reg:quantileerror", quantile_alpha=0.50, **xgb_params
            )
            model.fit(X_tr, y_tr, eval_set=[(X_va, y_va)], verbose=False)
            preds = np.expm1(model.predict(X_va))
            actuals = np.expm1(y_va)
            mape_scores.append(mean_absolute_percentage_error(actuals, preds))
            r2_scores.append(r2_score(actuals, preds))

            # Quantile calibration: fraction of actuals inside [P10, P90] (target ~0.80)
            m10 = XGBRegressor(objective="reg:quantileerror", quantile_alpha=0.10, **xgb_params)
            m90 = XGBRegressor(objective="reg:quantileerror", quantile_alpha=0.90, **xgb_params)
            m10.fit(X_tr, y_tr, verbose=False)
            m90.fit(X_tr, y_tr, verbose=False)
            lo, hi = np.expm1(m10.predict(X_va)), np.expm1(m90.predict(X_va))
            coverage_scores.append(float(np.mean((actuals >= lo) & (actuals <= hi))))

        self.mape_validation = float(np.mean(mape_scores))
        cv_r2 = float(np.mean(r2_scores))
        cv_coverage = float(np.mean(coverage_scores))
        print(
            f"5-Fold CV  MAPE={self.mape_validation*100:.2f}%  "
            f"R2={cv_r2:.3f}  P10-P90 coverage={cv_coverage:.2%}"
        )

        print("Training final models on full dataset...")
        self.model_p10 = XGBRegressor(
            objective="reg:quantileerror", quantile_alpha=0.10, **xgb_params
        )
        self.model_p10.fit(X, y_price, verbose=False)

        self.model_p50 = XGBRegressor(
            objective="reg:quantileerror", quantile_alpha=0.50, **xgb_params
        )
        self.model_p50.fit(X, y_price, verbose=False)

        self.model_p90 = XGBRegressor(
            objective="reg:quantileerror", quantile_alpha=0.90, **xgb_params
        )
        self.model_p90.fit(X, y_price, verbose=False)

        print("Training liquidity model...")
        self.model_liquidity = XGBRegressor(
            n_estimators=300, max_depth=5, learning_rate=0.06, random_state=42
        )
        self.model_liquidity.fit(X, y_liq, verbose=False)

        print("Training anomaly detector...")
        self.anomaly_detector = IsolationForest(
            n_estimators=200, contamination=0.05, random_state=42
        )
        self.anomaly_detector.fit(X)

        print("Building SHAP explainer...")
        import shap

        self.shap_explainer = shap.TreeExplainer(self.model_p50)

        # ── Global feature importance (SHAP) for explainability/governance ──
        try:
            sample = X.sample(min(500, len(X)), random_state=42)
            shap_matrix = self.shap_explainer.shap_values(sample)
            mean_abs = np.abs(shap_matrix).mean(axis=0)
            global_importance = {
                feat: float(val)
                for feat, val in sorted(
                    zip(self.feature_cols_full, mean_abs),
                    key=lambda kv: kv[1],
                    reverse=True,
                )
            }
        except Exception:
            global_importance = {}

        # ── Data hash for reproducibility (data versioning) ─────────────────
        import hashlib

        data_hash = hashlib.sha256(
            pd.util.hash_pandas_object(X, index=True).values.tobytes()
        ).hexdigest()[:16]

        self.train_metadata = {
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "n_rows": int(len(X)),
            "feature_schema_version": self.feature_schema_version,
            "data_hash": data_hash,
            "metrics": {
                "cv_mape": self.mape_validation,
                "cv_r2": cv_r2,
                "cv_p10_p90_coverage": cv_coverage,
            },
            "global_feature_importance": global_importance,
            "xgb_params": xgb_params,
        }
        return self

    def predict(self, input_data: dict) -> dict:
        row = self._build_feature_row(input_data)
        X = pd.DataFrame([row])[self.feature_cols_full]

        log_p10 = self.model_p10.predict(X)[0]
        log_p50 = self.model_p50.predict(X)[0]
        log_p90 = self.model_p90.predict(X)[0]

        p10_sqft = np.expm1(log_p10)
        p50_sqft = np.expm1(log_p50)
        p90_sqft = np.expm1(log_p90)
        size = input_data.get("size_sqft", 800)

        mv_low = round(p10_sqft * size)
        mv_mid = round(p50_sqft * size)
        mv_high = round(p90_sqft * size)

        liq_score_ml = float(np.clip(self.model_liquidity.predict(X)[0], 0, 100))

        # Deep Liquidity Engine Output
        liquidity_result = self._run_liquidity_engine(input_data, liq_score_ml, mv_mid)

        dv_30d = liquidity_result["distress_value_30d"]
        dv_90d = liquidity_result["distress_value_90d"]
        dv_180d = liquidity_result["distress_value_180d"]

        # 7-Factor Confidence Score
        confidence = self._confidence_score(
            input_data, liquidity_result, mv_high - mv_low, mv_mid
        )

        # Rental Income Cross-Check
        rental_yield = input_data.get("rental_yield_pct", 0.0)
        income_valuation = None
        if rental_yield > 0:
            annual_rent = mv_mid * (rental_yield / 100.0)
            income_valuation = round(
                annual_rent / max(0.02, row["rental_cap_rate"] / 100.0)
            )

        try:
            import shap

            shap_vals = self.shap_explainer.shap_values(X)
            shap_dict = {
                feat: round(float(val) * p50_sqft * size)
                for feat, val in zip(self.feature_cols_full, shap_vals[0])
            }
            top_drivers = sorted(
                shap_dict.items(), key=lambda x: abs(x[1]), reverse=True
            )[:5]
        except Exception:
            shap_dict = {f: 0 for f in self.feature_cols_full}
            top_drivers = [
                ("size_sqft", round(p50_sqft * size * 0.10)),
                ("circle_rate_per_sqft", round(p50_sqft * size * 0.05)),
            ]

        anomaly_score = float(self.anomaly_detector.decision_function(X)[0])
        risk_flags = self._compute_risk_flags(
            input_data, anomaly_score, p50_sqft, income_valuation, mv_mid
        )

        key_drivers_summary = self._build_drivers_summary(top_drivers, input_data)
        risk_flags_summary = [f["flag"] for f in risk_flags]

        return {
            "market_value_range": [mv_low, mv_high],
            "market_value_mid": mv_mid,
            "distress_value_range": [dv_30d, dv_180d],
            "distress_value_30d": dv_30d,
            "distress_value_90d": dv_90d,
            "distress_value_180d": dv_180d,
            "resale_potential_index": liquidity_result["resale_potential_index"],
            "liquidity_profile": liquidity_result["liquidity_profile"],
            "confidence_score": round(confidence, 2),
            "price_per_sqft_estimate": round(p50_sqft),
            "key_drivers": [
                {
                    "feature": k,
                    "impact_inr": v,
                    "direction": "positive" if v > 0 else "negative",
                }
                for k, v in top_drivers
            ],
            "key_drivers_summary": key_drivers_summary,
            "shap_values": {k: round(v) for k, v in shap_dict.items()},
            "risk_flags": risk_flags,
            "risk_flags_summary": risk_flags_summary,
            "anomaly_score": round(anomaly_score, 3),
            "income_approach_valuation": income_valuation,
            "estimated_time_to_sell_days": liquidity_result["liquidity_profile"][
                "estimated_time_to_sell_days"
            ],
            "model_mape_pct": (
                round(getattr(self, "mape_validation", 8.3) * 100, 1)
                if getattr(self, "mape_validation", None)
                else None
            ),
            # Provenance for the outcome loop, drift monitoring & governance
            "feature_schema_version": getattr(
                self, "feature_schema_version", FEATURE_SCHEMA_VERSION
            ),
            "_feature_vector": {k: round(float(v), 4) for k, v in row.items()},
        }

    def _build_feature_row(self, d: dict) -> dict:
        """Delegates to the canonical transform so serving features are IDENTICAL
        to training features (train/serve skew fix). See app/ml/features.py."""
        return build_feature_row(d)

    def _run_liquidity_engine(
        self, d: dict, liq_score_ml: float, market_value: float
    ) -> dict:
        prop_type = d.get("prop_type", "2bhk_apartment").lower()
        zone_tier = d.get("zone_tier", "mid")
        is_freehold = d.get("is_freehold", 1)
        has_clear_title = d.get("has_clear_title", 1)
        has_legal_dispute = d.get("has_legal_dispute", 0)

        moi = d.get("months_of_inventory", 6.0)
        listing_density = d.get("listing_density", 0.5)
        yoy_growth = d.get("yoy_price_growth_pct", 5.0)
        nq = d.get("neighbourhood_quality_score", 58.0)

        base_days = BASE_DAYS_TO_SELL.get(prop_type, 60)
        m_inventory = min(2.0, max(0.7, 0.7 + (moi / 24) * 0.6))
        m_velocity = min(1.3, max(0.7, 1.3 - (listing_density * 0.6)))
        m_momentum = min(1.5, max(0.8, 1.1 - (yoy_growth / 50.0)))
        m_zone = {"prime": 0.75, "mid": 1.0, "peripheral": 1.35}.get(zone_tier, 1.0)

        legal_penalties = 0.0
        if not is_freehold:
            legal_penalties += 0.20
        if not has_clear_title:
            legal_penalties += 0.15
        if d.get("has_encumbrance", 0):
            legal_penalties += 0.20
        if has_legal_dispute:
            legal_penalties += 0.40
        m_legal = 1.0 + legal_penalties

        m_nq = min(1.3, max(0.5, 1.3 - (nq / 125.0)))

        final_ttl = (
            base_days * m_inventory * m_velocity * m_momentum * m_zone * m_legal * m_nq
        )
        final_ttl = min(365.0, max(15.0, final_ttl))

        market_rpi = 100 * (1 - (final_ttl / 365.0))
        final_rpi = (liq_score_ml * 0.4) + (market_rpi * 0.6)
        final_rpi = min(100.0, max(0.0, final_rpi))

        # 3-Tier Distress Framework
        base_haircut = DISTRESS_BASE_BY_TYPE.get(prop_type, 0.20)
        ttl_drag = (final_ttl - 30.0) / 600.0
        momentum_bonus = (
            -0.03 if yoy_growth > 8.0 else (0.03 if yoy_growth < 0.0 else 0.0)
        )

        base_discount = (
            base_haircut + ttl_drag + (legal_penalties * 0.5) + momentum_bonus
        )
        base_discount = min(0.60, max(0.08, base_discount))

        # 180-day negotiated (standard distress)
        dv_180d = round(market_value * (1.0 - base_discount))
        # 90-day auction (needs deeper haircut to move faster)
        dv_90d = round(market_value * (1.0 - min(0.70, base_discount + 0.12)))
        # 30-day forced sale (fire sale)
        dv_30d = round(market_value * (1.0 - min(0.85, base_discount + 0.25)))

        grade = (
            "A"
            if final_ttl < 45
            else (
                "B"
                if final_ttl < 90
                else "C" if final_ttl < 180 else "D" if final_ttl < 270 else "F"
            )
        )
        p_band = (
            "P90"
            if final_rpi > 80
            else (
                "P75"
                if final_rpi > 65
                else "P50" if final_rpi > 45 else "P20" if final_rpi > 25 else "P10"
            )
        )
        npa_risk = (
            "high"
            if (final_ttl > 200 or legal_penalties > 0.3)
            else "medium" if final_ttl > 120 else "low"
        )

        cycle_str = (
            "expansion"
            if yoy_growth > 7.0
            else "contraction" if yoy_growth < 2.0 else "stable"
        )
        buyer_pool = min(
            100.0,
            max(
                0.0, d.get("listing_density", 0.5) * 60 + d.get("infra_score", 50) * 0.4
            ),
        )
        spread = max(1.0, (moi / 6.0) * 4.0 + max(0, 10.0 - yoy_growth))
        absorption = round(30.0 / max(1, final_ttl) * 100, 1)

        return {
            "distress_value_30d": dv_30d,
            "distress_value_90d": dv_90d,
            "distress_value_180d": dv_180d,
            "resale_potential_index": round(final_rpi, 1),
            "liquidity_profile": {
                "absorption_rate_pct_per_month": absorption,
                "buyer_pool_depth_index": round(buyer_pool, 1),
                "bid_ask_spread_pct": round(spread, 1),
                "micro_market_cycle": cycle_str,
                "inventory_pressure": (
                    "high"
                    if m_inventory > 1.1
                    else "low" if m_inventory < 0.9 else "moderate"
                ),
                "demand_velocity": (
                    "high"
                    if m_velocity < 0.9
                    else "low" if m_velocity > 1.1 else "moderate"
                ),
                "legal_clarity": "clear" if legal_penalties == 0 else "compromised",
                "liquidity_grade": grade,
                "percentile_band": p_band,
                "npa_risk_signal": npa_risk,
                "estimated_time_to_sell_days": [
                    int(final_ttl * 0.8),
                    int(final_ttl * 1.3),
                ],
            },
        }

    def _confidence_score(
        self, d: dict, liq_res: dict, price_range: float, price_mid: float
    ) -> float:
        """7-Factor Comprehensive Confidence Scoring"""
        # 1. Data completeness (30%)
        required = [
            "size_sqft",
            "age_years",
            "floor_num",
            "is_freehold",
            "rental_yield_pct",
        ]
        filled = sum(1 for x in required if d.get(x) is not None)
        f_data = (filled / len(required)) * 0.30

        # 2. ML Quantile Spread (20%)
        spread_pct = min(1.0, (price_range / max(price_mid, 1)))
        f_ml = max(0.0, (1.0 - spread_pct * 1.5)) * 0.20

        # 3. Market Depth / Comps Spread (15%)
        depth = liq_res["liquidity_profile"]["buyer_pool_depth_index"]
        f_depth = (depth / 100.0) * 0.15

        # 4. Bid-Ask Spread penalty (10%)
        spread = liq_res["liquidity_profile"]["bid_ask_spread_pct"]
        f_spread = max(0.0, 1.0 - (spread / 20.0)) * 0.10

        # 5. Legal Clarity (10%)
        f_legal = (
            0.10
            if d.get("has_clear_title", 1) and not d.get("has_legal_dispute", 0)
            else 0.0
        )

        # 6. Market Cycle certainty (10%)
        cycle = liq_res["liquidity_profile"]["micro_market_cycle"]
        f_cycle = 0.10 if cycle == "stable" else 0.08 if cycle == "expansion" else 0.05

        # 7. Absorption Rate (5%)
        abs_rate = liq_res["liquidity_profile"]["absorption_rate_pct_per_month"]
        f_abs = min(1.0, abs_rate / 20.0) * 0.05

        return min(0.98, f_data + f_ml + f_depth + f_spread + f_legal + f_cycle + f_abs)

    def _compute_risk_flags(
        self,
        d: dict,
        anomaly_score: float,
        price_sqft: float,
        inc_val: float,
        mv: float,
    ) -> list:
        flags = []
        prop_type = d.get("prop_type", "2bhk_apartment").lower()
        zone_tier = d.get("zone_tier", "mid")
        size = d.get("size_sqft", 800)
        age = d.get("age_years", 10)
        cr = d.get("circle_rate_per_sqft", 7500)
        nq = d.get("neighbourhood_quality_score", 58.0)

        # Price vs circle rate
        if price_sqft < cr * 0.85:
            flags.append(
                {
                    "flag": "price_below_circle_rate",
                    "severity": "high",
                    "detail": f"Estimated price ₹{price_sqft:.0f}/sqft is below circle rate ₹{cr}/sqft",
                }
            )

        if anomaly_score < -0.1:
            flags.append(
                {
                    "flag": "anomalous_input_combination",
                    "severity": "medium",
                    "detail": "Property attributes combination is statistically unusual for this zone",
                }
            )

        if age > 30:
            flags.append(
                {
                    "flag": "high_building_age",
                    "severity": "medium",
                    "detail": f"Building age {age:.0f} years — increased maintenance and depreciation risk",
                }
            )

        if not d.get("is_freehold", 1):
            flags.append(
                {
                    "flag": "leasehold_title",
                    "severity": "high",
                    "detail": "Leasehold property — resale liquidity significantly impacted",
                }
            )

        if not d.get("is_rera_registered", 1):
            flags.append(
                {
                    "flag": "not_rera_registered",
                    "severity": "medium",
                    "detail": "Project not RERA registered — legal risk flag for collateral",
                }
            )
        if not d.get("has_clear_title", 1):
            flags.append(
                {
                    "flag": "title_complexity_detected",
                    "severity": "high",
                    "detail": "Title clarity not confirmed — full legal due diligence required",
                }
            )
        if d.get("has_encumbrance", 0):
            flags.append(
                {
                    "flag": "encumbrance_indicator",
                    "severity": "high",
                    "detail": "Encumbrance/lien indicator present — can impact enforceability and saleability",
                }
            )
        if d.get("has_legal_dispute", 0):
            flags.append(
                {
                    "flag": "legal_dispute_indicator",
                    "severity": "high",
                    "detail": "Potential legal dispute on property ownership/use is indicated",
                }
            )
        if not d.get("zoning_approved", 1):
            flags.append(
                {
                    "flag": "zoning_approval_pending",
                    "severity": "medium",
                    "detail": "Zoning/use approval not confirmed for declared property usage",
                }
            )

        bounds = SIZE_SANITY_BOUNDS.get(prop_type, (200, 5000))
        if size < bounds[0]:
            sev = "high" if size < bounds[0] * 0.5 else "medium"
            flags.append(
                {
                    "flag": "plausibility_check_undersized",
                    "severity": sev,
                    "detail": f"Plausibility Warning: Size {size:.0f} sqft is unusually small for a {prop_type}.",
                }
            )
        elif size > bounds[1]:
            sev = "high" if size > bounds[1] * 2 else "medium"
            flags.append(
                {
                    "flag": "plausibility_check_oversized",
                    "severity": sev,
                    "detail": f"Plausibility Warning: Size {size:.0f} sqft is unusually large for a {prop_type}.",
                }
            )

        # Income vs Market Divergence (New)
        if inc_val is not None:
            divergence = abs(inc_val - mv) / max(mv, 1)
            if divergence > 0.30:
                flags.append(
                    {
                        "flag": "income_market_divergence",
                        "severity": "medium",
                        "detail": f"Income approach valuation (₹{inc_val/1e5:.1f}L) diverges significantly (>30%) from market approach. Verify rental yield inputs.",
                    }
                )

        moi = d.get("months_of_inventory", 6.0)
        if moi > 12.0:
            flags.append(
                {
                    "flag": "oversupply_risk",
                    "severity": "high",
                    "detail": f"Oversupply Risk: {moi} months of inventory indicates low absorption.",
                }
            )

        return flags

    def _build_drivers_summary(self, top_drivers: list, d: dict) -> list:
        summary = []
        for feat, impact in top_drivers:
            label = FEATURE_LABEL_MAP.get(feat, feat)
            if feat == "infra_score" and d.get("infra_score", 50) > 70:
                label = "proximity_to_metro"
            elif feat == "listing_density" and d.get("listing_density", 0.5) > 0.65:
                label = "high_micro_market_competition"
            elif feat == "neighbourhood_quality_score":
                label = (
                    "premium_planned_neighbourhood"
                    if d.get(feat, 58) > 70
                    else "mixed_use_neighbourhood"
                )
            summary.append(label)
        return summary

    def save(self, path: str, register: bool = True):
        Path(path).mkdir(parents=True, exist_ok=True)
        with open(f"{path}/propiq_model.pkl", "wb") as f:
            pickle.dump(self, f)

        # Semantic version: schema.major + timestamp build id (monotonic, traceable)
        build_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        version = f"{self.feature_schema_version}+{build_id}"

        meta = {
            "version": version,
            "mape_validation_pct": (
                round(self.mape_validation * 100, 2) if self.mape_validation else None
            ),
            "feature_schema_version": self.feature_schema_version,
            "feature_cols": self.feature_cols_full,
            "prop_type_encoding": PROP_TYPE_ENCODING,
            "train_metadata": self.train_metadata,
        }
        with open(f"{path}/model_meta.json", "w") as f:
            json.dump(meta, f, indent=2)
        print(f"Model saved to {path}/ (version {version})")

        # ── Experiment tracking + model registry (telemetry, never fatal) ───
        if register:
            try:
                from app.ml.tracking import (log_training_run,
                                             register_model_version)

                tm = self.train_metadata
                metrics = tm.get("metrics", {})
                run_id = log_training_run(
                    params={
                        "n_rows": tm.get("n_rows"),
                        "feature_schema_version": self.feature_schema_version,
                        **tm.get("xgb_params", {}),
                    },
                    metrics={
                        "cv_mape": metrics.get("cv_mape"),
                        "cv_r2": metrics.get("cv_r2"),
                        "cv_p10_p90_coverage": metrics.get("cv_p10_p90_coverage"),
                    },
                    model_dir=path,
                    tags={"data_hash": tm.get("data_hash", "")},
                )
                register_model_version(
                    version=version,
                    metrics=metrics,
                    feature_schema_version=self.feature_schema_version,
                    data_hash=tm.get("data_hash", ""),
                    stage="Staging",
                    mlflow_run_id=run_id,
                )
            except Exception as e:
                print(f"Registry/tracking skipped (non-fatal): {e}")

    @classmethod
    def load(cls, path: str) -> "PropIQModel":
        import importlib
        import sys

        import __main__

        if not hasattr(__main__, "PropIQModel"):
            setattr(__main__, "PropIQModel", cls)
        try:
            mod = importlib.import_module("app.ml.valuation_model")
            sys.modules["app.ml.valuation_model"] = mod
            sys.modules["valuation_model"] = mod
        except Exception:
            pass
        with open(f"{path}/propiq_model.pkl", "rb") as f:
            return pickle.load(f)


if __name__ == "__main__":
    _here = Path(__file__).parent.parent.parent
    data_path = _here / "data" / "processed" / "synthetic_training_data.csv"
    model_path = str(_here / "data" / "models")
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} training records")
    model = PropIQModel()
    model.train(df)
    model.save(model_path)
