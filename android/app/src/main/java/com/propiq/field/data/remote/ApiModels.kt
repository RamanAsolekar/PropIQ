package com.propiq.field.data.remote

import com.google.gson.annotations.SerializedName

/**
 * DTOs mirroring the real PropIQ backend contract.
 *
 * Verified against backend/app/main.py `_run_assessment` (the base dict),
 * `assess_with_image` (the CV augmentation) and `_augment_with_market_outputs`
 * (comps/trends/LTV/memo), plus backend/app/models/schemas.py.
 *
 * Every field is nullable with a default. The backend attaches several blocks
 * "additively, non-fatal" (ensemble, duplicate_risk, price_forecast) — they are
 * absent whenever their optional dependency is missing on the server, so the app
 * must never assume presence. Gson leaves absent fields null, which is exactly
 * the behaviour we want.
 */
data class AssessmentResponse(
    @SerializedName("request_id") val requestId: String? = null,
    val locality: String? = null,
    val city: String? = null,
    @SerializedName("prop_type") val propType: String? = null,
    @SerializedName("size_sqft") val sizeSqft: Double? = null,
    @SerializedName("age_years") val ageYears: Double? = null,
    @SerializedName("floor_num") val floorNum: Int? = null,

    @SerializedName("market_value_range") val marketValueRange: List<Long>? = null,
    @SerializedName("market_value_mid") val marketValueMid: Long? = null,
    @SerializedName("distress_value_range") val distressValueRange: List<Long>? = null,
    @SerializedName("distress_value_30d") val distressValue30d: Long? = null,
    @SerializedName("distress_value_90d") val distressValue90d: Long? = null,
    @SerializedName("distress_value_180d") val distressValue180d: Long? = null,

    @SerializedName("resale_potential_index") val resalePotentialIndex: Double? = null,
    @SerializedName("estimated_time_to_sell_days") val timeToSellDays: List<Int>? = null,
    @SerializedName("liquidity_profile") val liquidityProfile: LiquidityProfile? = null,
    @SerializedName("confidence_score") val confidenceScore: Double? = null,
    @SerializedName("price_per_sqft_estimate") val pricePerSqft: Long? = null,
    @SerializedName("model_mape_pct") val modelMapePct: Double? = null,
    @SerializedName("anomaly_score") val anomalyScore: Double? = null,

    @SerializedName("key_drivers") val keyDrivers: List<KeyDriver>? = null,
    @SerializedName("key_drivers_summary") val keyDriversSummary: List<String>? = null,
    @SerializedName("risk_flags") val riskFlags: List<RiskFlag>? = null,
    @SerializedName("risk_flags_summary") val riskFlagsSummary: List<String>? = null,

    val enrichment: Enrichment? = null,
    @SerializedName("cv_assessment") val cvAssessment: CvAssessment? = null,
    @SerializedName("ltv_analysis") val ltvAnalysis: LtvAnalysis? = null,
    @SerializedName("credit_memo") val creditMemo: String? = null,
    @SerializedName("customer_letter") val customerLetter: String? = null,
    @SerializedName("duplicate_risk") val duplicateRisk: DuplicateRisk? = null,
    @SerializedName("processing_time_ms") val processingTimeMs: Int? = null,
) {
    /**
     * The backend puts `estimated_time_to_sell_days` at the top level AND inside
     * `liquidity_profile`; ResultsDashboard.js falls back between them, so we do
     * the same rather than showing an em-dash when only one is populated.
     */
    val resolvedTimeToSell: List<Int>?
        get() = timeToSellDays ?: liquidityProfile?.timeToSellDays

    val resolvedMape: Double get() = modelMapePct ?: 8.3

    /** Highest-severity flags first — the results screen shows only the top few. */
    val rankedFlags: List<RiskFlag>
        get() = (riskFlags ?: emptyList()).sortedBy {
            when (it.severity?.lowercase()) {
                "high" -> 0
                "medium" -> 1
                else -> 2
            }
        }

    /**
     * Fraud is the headline novelty claim, so it gets its own accessor rather
     * than being buried in the generic flag list. Both the CV block and the
     * vector-duplicate engine can raise it.
     */
    val fraudAlert: RiskFlag?
        get() = (riskFlags ?: emptyList()).firstOrNull {
            it.flag == "cv_property_type_mismatch" ||
                it.flag == "cv_fraud_detected" ||
                it.flag == "vector_duplicate_collateral"
        }
}

data class KeyDriver(
    val feature: String? = null,
    @SerializedName("impact_inr") val impactInr: Long? = null,
    val direction: String? = null,
)

data class RiskFlag(
    val flag: String? = null,
    val severity: String? = null,
    val detail: String? = null,
)

data class LiquidityProfile(
    @SerializedName("absorption_rate_pct_per_month") val absorptionRate: Double? = null,
    @SerializedName("buyer_pool_depth_index") val buyerPoolDepth: Double? = null,
    @SerializedName("bid_ask_spread_pct") val bidAskSpread: Double? = null,
    @SerializedName("micro_market_cycle") val microMarketCycle: String? = null,
    @SerializedName("inventory_pressure") val inventoryPressure: String? = null,
    @SerializedName("demand_velocity") val demandVelocity: String? = null,
    @SerializedName("estimated_time_to_sell_days") val timeToSellDays: List<Int>? = null,
)

data class Enrichment(
    @SerializedName("zone_tier") val zoneTier: String? = null,
    @SerializedName("circle_rate_per_sqft") val circleRatePerSqft: Long? = null,
    @SerializedName("infra_score") val infraScore: Double? = null,
    @SerializedName("listing_density") val listingDensity: Double? = null,
    @SerializedName("neighbourhood_quality_score") val neighbourhoodQuality: Double? = null,
    @SerializedName("dominant_landuse") val dominantLanduse: String? = null,
    @SerializedName("months_of_inventory") val monthsOfInventory: Double? = null,
    @SerializedName("yoy_price_growth_pct") val yoyPriceGrowthPct: Double? = null,
    val city: String? = null,
)

data class CvAssessment(
    val condition: String? = null,
    @SerializedName("quality_score") val qualityScore: Double? = null,
    @SerializedName("valuation_adjustment_factor") val adjustmentFactor: Double? = null,
    @SerializedName("adjustment_description") val adjustmentDescription: String? = null,
    @SerializedName("cv_confidence") val cvConfidence: Double? = null,
    @SerializedName("image_analyzed") val imageAnalyzed: Boolean? = null,
    @SerializedName("images_count") val imagesCount: Int? = null,
    @SerializedName("exterior_count") val exteriorCount: Int? = null,
    @SerializedName("interior_count") val interiorCount: Int? = null,
    @SerializedName("exterior_condition") val exteriorCondition: String? = null,
    @SerializedName("interior_condition") val interiorCondition: String? = null,
    @SerializedName("is_fraud_detected") val isFraudDetected: Boolean? = null,
    @SerializedName("fraud_reason") val fraudReason: String? = null,
    @SerializedName("is_prop_type_mismatch") val isPropTypeMismatch: Boolean? = null,
    @SerializedName("mismatch_reason") val mismatchReason: String? = null,
    @SerializedName("per_image_results") val perImage: List<PerImageResult>? = null,
    @SerializedName("composite_raw_score") val compositeRawScore: Double? = null,
)

data class PerImageResult(
    val tag: String? = null,
    val condition: String? = null,
    @SerializedName("quality_score") val qualityScore: Double? = null,
    @SerializedName("vlm_analysis") val vlmAnalysis: VlmAnalysis? = null,
)

data class VlmAnalysis(
    val description: String? = null,
    val observations: List<String>? = null,
    val defects: List<String>? = null,
)

data class LtvAnalysis(
    @SerializedName("recommended_ltv_pct") val recommendedLtvPct: Double? = null,
    @SerializedName("rbi_max_ltv_pct") val rbiMaxLtvPct: Double? = null,
    @SerializedName("pfl_internal_ltv_pct") val pflInternalLtvPct: Double? = null,
    @SerializedName("max_loan_amount") val maxLoanAmount: Long? = null,
    @SerializedName("max_loan_on_distress_value") val maxLoanOnDistress: Long? = null,
    @SerializedName("rbi_rationale") val rbiRationale: String? = null,
    @SerializedName("pfl_rationale") val pflRationale: String? = null,
    @SerializedName("ltv_zone") val ltvZone: String? = null,
    @SerializedName("zone_tier") val zoneTier: String? = null,
    val disclaimer: String? = null,
)

data class DuplicateRisk(
    @SerializedName("risk_level") val riskLevel: String? = null,
    @SerializedName("duplicate_count") val duplicateCount: Int? = null,
    @SerializedName("max_similarity") val maxSimilarity: Double? = null,
)

// ── Chat (POST /api/v1/chat) ───────────────────────────────────────────────
// Verified against ChatRequest/ChatMessage at backend/app/main.py:1395-1403.

data class ChatMessageDto(val role: String, val content: String)

data class ChatRequestDto(
    val messages: List<ChatMessageDto>,
    @SerializedName("form_context") val formContext: Map<String, Any?> = emptyMap(),
    @SerializedName("assessment_result") val assessmentResult: Map<String, Any?>? = null,
)

/**
 * The chat endpoint has two shapes. Normally `{reply}`. But when the agentic
 * extractor recognises a property description it returns
 * `{reply, action:"auto_assess", extracted_fields:{...}}` — that is the hook the
 * voice flow rides on: speak a description, get back structured fields.
 */
data class ChatResponseDto(
    val reply: String? = null,
    val action: String? = null,
    @SerializedName("extracted_fields") val extractedFields: ExtractedFields? = null,
) {
    val isAutoAssess: Boolean get() = action == "auto_assess"
}

data class ExtractedFields(
    val locality: String? = null,
    @SerializedName("prop_type") val propType: String? = null,
    @SerializedName("size_sqft") val sizeSqft: Double? = null,
    @SerializedName("age_years") val ageYears: Double? = null,
    @SerializedName("floor_num") val floorNum: Int? = null,
    @SerializedName("is_freehold") val isFreehold: Int? = null,
    @SerializedName("is_rera_registered") val isReraRegistered: Int? = null,
)

// ── Reference data (GET /api/v1/localities) ────────────────────────────────

data class LocalitiesResponse(
    @SerializedName("localities_by_city") val localitiesByCity: Map<String, List<String>>? = null,
    val localities: List<String>? = null,
    val city: String? = null,
    val total: Int? = null,
)
