package com.propiq.field.data.demo

import com.propiq.field.data.remote.AssessmentResponse
import com.propiq.field.data.remote.CvAssessment
import com.propiq.field.data.remote.Enrichment
import com.propiq.field.data.remote.KeyDriver
import com.propiq.field.data.remote.LiquidityProfile
import com.propiq.field.data.remote.LtvAnalysis
import com.propiq.field.data.remote.PerImageResult
import com.propiq.field.data.remote.RiskFlag
import com.propiq.field.data.remote.VlmAnalysis

/**
 * Stage-safe demo payloads.
 *
 * Demo Mode exists because a 3-minute pitch cannot be hostage to venue wifi and
 * a cold Render instance doing ML init. These fixtures are shaped exactly like
 * a real `/api/v1/assess/image` response — same field names, same nesting, same
 * value magnitudes — so the results screen renders through the identical code
 * path and nothing on stage is a special case.
 *
 * The matching sample property form lives at PropertyDraft.sample() in the
 * capture package — fixtures for the *response* belong here, fixtures for the
 * *form* belong with the form.
 *
 * The numbers are internally consistent with the real engine's behaviour:
 * a Baner 3BHK at prime zone tier, distress values banded below market, and an
 * LTV that has been capped by the presence of a high-severity flag (which is
 * what backend/app/services/ltv_audit.py actually does).
 */
object DemoFixtures {

    /** The clean path: a well-maintained flat, healthy LTV, no fraud. */
    fun clean(): AssessmentResponse = base().copy(
        requestId = "DEMO-CLN1",
        riskFlags = listOf(
            RiskFlag(
                flag = "moderate_inventory_pressure",
                severity = "low",
                detail = "Locality inventory is 6.4 months — slightly above the 6-month " +
                    "balanced-market benchmark. Minor liquidity drag only.",
            ),
        ),
        riskFlagsSummary = listOf("moderate_inventory_pressure"),
        cvAssessment = cleanCv(),
        ltvAnalysis = LtvAnalysis(
            recommendedLtvPct = 70.0,
            rbiMaxLtvPct = 75.0,
            pflInternalLtvPct = 70.0,
            maxLoanAmount = 13_580_000,
            maxLoanOnDistress = 11_004_000,
            rbiRationale = "RBI Master Circular caps LAP against residential apartment " +
                "collateral above ₹75L at 75% LTV.",
            pflRationale = "No high-severity flags. RPI of 82.4 supports the full internal band.",
            ltvZone = "green",
            zoneTier = "prime",
            disclaimer = "LTV computed per RBI Master Circular on Housing Loans 2024. " +
                "Subject to internal credit policy and borrower creditworthiness assessment.",
        ),
    )

    /**
     * The fraud path — this is the one to demo. The claimed property type is a
     * 3BHK apartment; the VLM sees a warehouse floor. This is the exact
     * `cv_property_type_mismatch` flag raised in
     * backend/app/main.py `assess_with_image`.
     */
    fun fraud(): AssessmentResponse = base().copy(
        requestId = "DEMO-FRD1",
        marketValueRange = listOf(15_480_000, 18_920_000),
        marketValueMid = 17_200_000,
        distressValueRange = listOf(12_040_000, 14_620_000),
        distressValue90d = 13_330_000,
        resalePotentialIndex = 54.8,
        confidenceScore = 0.71,
        pricePerSqft = 11_862,
        riskFlags = listOf(
            RiskFlag(
                flag = "cv_property_type_mismatch",
                severity = "high",
                detail = "VLM Verification Failed: The images show an open industrial floor " +
                    "plate with exposed roof trusses, a roller shutter and pallet racking. " +
                    "This is inconsistent with the claimed 3BHK residential apartment.",
            ),
            RiskFlag(
                flag = "vector_duplicate_collateral",
                severity = "high",
                detail = "Vector match: 2 near-identical prior pledge(s) detected " +
                    "(risk: high).",
            ),
            RiskFlag(
                flag = "cv_fair_condition",
                severity = "medium",
                detail = "CV analysis detected FAIR property condition. Moderate valuation " +
                    "discount applied.",
            ),
        ),
        riskFlagsSummary = listOf(
            "cv_property_type_mismatch",
            "vector_duplicate_collateral",
            "cv_fair_condition",
        ),
        cvAssessment = fraudCv(),
        ltvAnalysis = LtvAnalysis(
            recommendedLtvPct = 40.0,
            rbiMaxLtvPct = 75.0,
            pflInternalLtvPct = 40.0,
            maxLoanAmount = 6_880_000,
            maxLoanOnDistress = 5_332_000,
            rbiRationale = "RBI Master Circular caps LAP against residential apartment " +
                "collateral above ₹75L at 75% LTV.",
            pflRationale = "2 high-severity flags present (property-type mismatch, duplicate " +
                "collateral). Internal policy caps LTV at 40% pending physical re-verification.",
            ltvZone = "red",
            zoneTier = "prime",
            disclaimer = "LTV computed per RBI Master Circular on Housing Loans 2024. " +
                "Subject to internal credit policy and borrower creditworthiness assessment.",
        ),
    )

    private fun base() = AssessmentResponse(
        requestId = "DEMO-0001",
        locality = "Baner",
        city = "Pune",
        propType = "3bhk_apartment",
        sizeSqft = 1450.0,
        ageYears = 8.0,
        floorNum = 7,
        marketValueRange = listOf(17_400_000, 21_260_000),
        marketValueMid = 19_400_000,
        distressValueRange = listOf(14_550_000, 17_460_000),
        distressValue30d = 14_550_000,
        distressValue90d = 16_005_000,
        distressValue180d = 17_460_000,
        resalePotentialIndex = 82.4,
        timeToSellDays = listOf(28, 62),
        liquidityProfile = LiquidityProfile(
            absorptionRate = 8.4,
            buyerPoolDepth = 78.2,
            bidAskSpread = 4.1,
            microMarketCycle = "expansion",
            inventoryPressure = "moderate",
            demandVelocity = "high",
            timeToSellDays = listOf(28, 62),
        ),
        confidenceScore = 0.87,
        pricePerSqft = 13_379,
        modelMapePct = 8.3,
        anomalyScore = 0.12,
        keyDrivers = listOf(
            KeyDriver("circle_rate_per_sqft", 5_240_000, "positive"),
            KeyDriver("infra_score", 2_180_000, "positive"),
            KeyDriver("neighbourhood_quality_score", 1_460_000, "positive"),
            KeyDriver("age_years", -820_000, "negative"),
            KeyDriver("months_of_inventory", -410_000, "negative"),
        ),
        keyDriversSummary = listOf(
            "prime_zone_circle_rate",
            "metro_and_it_corridor_proximity",
            "standard_3bhk_configuration",
        ),
        enrichment = Enrichment(
            zoneTier = "prime",
            circleRatePerSqft = 10_800,
            infraScore = 81.5,
            listingDensity = 0.68,
            neighbourhoodQuality = 79.4,
            dominantLanduse = "residential",
            monthsOfInventory = 6.4,
            yoyPriceGrowthPct = 7.8,
            city = "Pune",
        ),
        creditMemo = "COLLATERAL APPRAISAL SUMMARY — Baner, Pune\n\n" +
            "Subject is a 1,450 sqft 3BHK apartment on floor 7 of a RERA-registered, " +
            "freehold development in Baner (prime zone tier), aged 8 years.\n\n" +
            "The AVM triangulates a market value of ₹1.94 Cr (₹13,379/sqft) against a " +
            "prime-tier IGR circle rate of ₹10,800/sqft, an implied premium of 23.9% that " +
            "is consistent with observed Baner transactions.\n\n" +
            "Liquidity is strong: RPI 82.4, absorption 8.4%/month and a buyer-pool depth " +
            "index of 78.2 support an estimated 28-62 day disposal window.\n\n" +
            "RECOMMENDATION: Sanction up to ₹1.36 Cr at 70% LTV against market value.",
        processingTimeMs = 1_284,
    )

    private fun cleanCv() = CvAssessment(
        condition = "good",
        qualityScore = 74.5,
        adjustmentFactor = 1.0,
        adjustmentDescription = "Good condition — baseline valuation",
        cvConfidence = 0.88,
        imageAnalyzed = true,
        imagesCount = 2,
        exteriorCount = 1,
        interiorCount = 1,
        exteriorCondition = "good",
        interiorCondition = "good",
        isFraudDetected = false,
        isPropTypeMismatch = false,
        compositeRawScore = 2.0,
        perImage = listOf(
            PerImageResult(
                tag = "exterior",
                condition = "good",
                qualityScore = 76.0,
                vlmAnalysis = VlmAnalysis(
                    description = "A mid-rise residential tower with a clean rendered facade, " +
                        "uniform glazing and maintained common balconies. No structural " +
                        "distress visible at the elevation shown.",
                    observations = listOf(
                        "Uniform facade paint",
                        "Intact balcony railings",
                        "Landscaped setback",
                    ),
                    defects = listOf("Minor weathering at the parapet line"),
                ),
            ),
            PerImageResult(
                tag = "interior",
                condition = "good",
                qualityScore = 73.0,
                vlmAnalysis = VlmAnalysis(
                    description = "Vitrified-tile flooring in sound condition, plastered and " +
                        "painted walls, no visible damp staining or cracking.",
                    observations = listOf("Vitrified flooring", "No damp ingress"),
                    defects = listOf("Light scuffing on skirting"),
                ),
            ),
        ),
    )

    private fun fraudCv() = CvAssessment(
        condition = "fair",
        qualityScore = 58.0,
        adjustmentFactor = 0.92,
        adjustmentDescription = "Fair condition — 8% valuation discount",
        cvConfidence = 0.91,
        imageAnalyzed = true,
        imagesCount = 2,
        exteriorCount = 1,
        interiorCount = 1,
        exteriorCondition = "fair",
        interiorCondition = "fair",
        isFraudDetected = false,
        isPropTypeMismatch = true,
        mismatchReason = "Images show an industrial warehouse interior, not a residential " +
            "3BHK apartment as claimed.",
        compositeRawScore = 1.0,
        perImage = listOf(
            PerImageResult(
                tag = "exterior",
                condition = "fair",
                qualityScore = 60.0,
                vlmAnalysis = VlmAnalysis(
                    description = "A single-storey shed structure with profiled metal sheeting " +
                        "and a wide roller shutter opening onto a hardstanding yard. This is " +
                        "a light-industrial unit, not a residential apartment building.",
                    observations = listOf(
                        "Roller shutter access",
                        "Profiled metal cladding",
                        "Yard hardstanding",
                    ),
                    defects = listOf("Surface corrosion on cladding", "Ponding in the yard"),
                ),
            ),
            PerImageResult(
                tag = "interior",
                condition = "fair",
                qualityScore = 56.0,
                vlmAnalysis = VlmAnalysis(
                    description = "Open floor plate with exposed steel roof trusses, high-bay " +
                        "lighting and pallet racking against one wall. There are no internal " +
                        "partitions, kitchen or bathroom consistent with a 3BHK dwelling.",
                    observations = listOf("Exposed trusses", "Pallet racking", "Power-float slab"),
                    defects = listOf("Slab cracking near the shutter line"),
                ),
            ),
        ),
    )
}
