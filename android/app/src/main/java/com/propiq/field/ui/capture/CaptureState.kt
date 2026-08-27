package com.propiq.field.ui.capture

import com.propiq.field.data.repo.FieldAssessmentRequest
import com.propiq.field.location.GeoFix
import com.propiq.field.ondevice.LlmState
import com.propiq.field.ondevice.PhotoVerdict
import com.propiq.field.speech.VoiceLanguage

/**
 * The property form as the officer is filling it.
 *
 * Numeric fields are held as Strings because a half-typed "14" must not be
 * coerced to 14.0 and then re-rendered — that fights the keyboard. Validation
 * and conversion happen once, in [toRequest].
 */
data class PropertyDraft(
    /**
     * The loan file this collateral belongs to. Not sent to the valuation
     * endpoint (PropertyInput has no such field) — it is stamped on the local
     * record and the exported PDF, which is what makes the app usable across
     * six site visits in a day instead of one.
     */
    val loanRef: String = "",
    val borrowerName: String = "",
    val city: String = "Pune",
    val locality: String = "",
    val propType: String = "2bhk_apartment",
    val sizeSqft: String = "",
    val ageYears: String = "",
    val floorNum: String = "3",
    val isFreehold: Boolean = true,
    val isReraRegistered: Boolean = true,
    val occupancy: String = "self_occupied",
    val rentalYieldPct: String = "0",
    val hasClearTitle: Boolean = true,
    val hasEncumbrance: Boolean = false,
    val hasLegalDispute: Boolean = false,
    val zoningApproved: Boolean = true,
) {
    /**
     * Mirrors the server-side Field constraints in
     * backend/app/models/schemas.py (`size_sqft` gt 100 lt 50000, `age_years`
     * 0..80, `floor_num` 0..50) so an invalid form is caught on the phone
     * rather than costing a round trip and a 422.
     */
    val sizeError: String?
        get() {
            val v = sizeSqft.toDoubleOrNull() ?: return if (sizeSqft.isBlank()) null else "Enter a number"
            return when {
                v <= 100 -> "Must be over 100 sqft"
                v >= 50_000 -> "Must be under 50,000 sqft"
                else -> null
            }
        }

    val ageError: String?
        get() {
            val v = ageYears.toDoubleOrNull() ?: return if (ageYears.isBlank()) null else "Enter a number"
            return if (v < 0 || v > 80) "Must be 0-80 years" else null
        }

    val floorError: String?
        get() {
            val v = floorNum.toIntOrNull() ?: return if (floorNum.isBlank()) null else "Enter a number"
            return if (v < 0 || v > 50) "Must be 0-50" else null
        }

    val isComplete: Boolean
        get() = locality.isNotBlank() &&
            sizeSqft.toDoubleOrNull()?.let { it > 100 && it < 50_000 } == true &&
            ageYears.toDoubleOrNull()?.let { it in 0.0..80.0 } == true &&
            floorNum.toIntOrNull()?.let { it in 0..50 } == true

    companion object {
        /**
         * The pre-seeded stage property: a Baner 3BHK that the backend values
         * around Rs 1.94 Cr. Pairs with DemoFixtures' canned responses so Demo
         * Mode runs the full flow with no network.
         */
        fun sample() = PropertyDraft(
            loanRef = "LAP-2026-04417",
            borrowerName = "S. Deshpande",
            city = "Pune",
            locality = "Baner",
            propType = "3bhk_apartment",
            sizeSqft = "1450",
            ageYears = "8",
            floorNum = "7",
            isFreehold = true,
            isReraRegistered = true,
            occupancy = "self_occupied",
            rentalYieldPct = "3.2",
            hasClearTitle = true,
            hasEncumbrance = false,
            hasLegalDispute = false,
            zoningApproved = true,
        )
    }

    fun toRequest(fix: GeoFix?, fallbackLatLon: Pair<Double, Double>?, forceFraudDemo: Boolean = false) =
        FieldAssessmentRequest(
            loanRef = loanRef.trim(),
            borrowerName = borrowerName.trim(),
            locality = locality.trim(),
            propType = propType,
            sizeSqft = sizeSqft.toDoubleOrNull() ?: 0.0,
            ageYears = ageYears.toDoubleOrNull() ?: 0.0,
            floorNum = floorNum.toIntOrNull() ?: 3,
            isFreehold = if (isFreehold) 1 else 0,
            isReraRegistered = if (isReraRegistered) 1 else 0,
            occupancy = occupancy,
            rentalYieldPct = rentalYieldPct.toDoubleOrNull() ?: 0.0,
            hasClearTitle = if (hasClearTitle) 1 else 0,
            hasEncumbrance = if (hasEncumbrance) 1 else 0,
            hasLegalDispute = if (hasLegalDispute) 1 else 0,
            zoningApproved = if (zoningApproved) 1 else 0,
            geoLat = fix?.lat ?: fallbackLatLon?.first,
            geoLon = fix?.lon ?: fallbackLatLon?.second,
            forceFraudDemo = forceFraudDemo,
        )
}

/** A frame the officer kept, with its on-device verdict attached. */
data class CapturedFrame(
    val path: String,
    val tag: String,
    val verdict: PhotoVerdict,
)

enum class CaptureStage { FORM, CAMERA, SUBMITTING }

data class CaptureUiState(
    val stage: CaptureStage = CaptureStage.FORM,
    val draft: PropertyDraft = PropertyDraft(),
    val frames: List<CapturedFrame> = emptyList(),
    val activeTag: String = "exterior",

    // Device data
    val geoFix: GeoFix? = null,
    val locating: Boolean = false,
    val locationDenied: Boolean = false,

    // Voice
    val voiceLanguage: VoiceLanguage = VoiceLanguage.ENGLISH_IN,
    val voiceActive: Boolean = false,
    val voiceOnDevice: Boolean = false,
    val voiceAmplitude: Float = 0f,
    val voiceTranscript: String = "",
    val voicePartial: String = "",
    val voiceStatus: String? = null,
    val voiceParsing: Boolean = false,
    /** Which engine actually parsed the last transcript — shown to the officer. */
    val lastParsedBy: ParseSource? = null,

    // On-device LLM
    val llmState: LlmState = LlmState.NotInitialised,

    // On-device gate feedback for the most recent shot
    val lastVerdict: PhotoVerdict? = null,
    val analyzing: Boolean = false,

    val cameraError: String? = null,
    val submitStatus: String = "",
    val error: String? = null,
    val isOnline: Boolean = true,
    val demoMode: Boolean = false,
) {
    val canSubmit: Boolean
        get() = draft.isComplete && frames.isNotEmpty() && stage != CaptureStage.SUBMITTING

    val exteriorCount: Int get() = frames.count { it.tag == "exterior" }
    val interiorCount: Int get() = frames.count { it.tag == "interior" }
}

/** Which extractor produced the current form values. */
enum class ParseSource(val label: String) {
    ON_DEVICE("Parsed on-device"),
    CLOUD("Parsed in cloud"),
}

/** One-shot events the screen consumes and clears. */
sealed interface CaptureEvent {
    data class NavigateToResults(val requestId: String) : CaptureEvent
    data class Queued(val message: String) : CaptureEvent
    data class Toast(val message: String) : CaptureEvent
}
