package com.propiq.field.data.local

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * One field assessment that could not reach the backend and is waiting to be
 * retried.
 *
 * The captured photos are NOT stored as blobs — only their on-disk paths. A
 * four-photo assessment is several megabytes; putting that through SQLite would
 * blow past the CursorWindow limit and make the queue screen janky. The files
 * live in the app's cache dir and are deleted once the row is submitted.
 */
@Entity(tableName = "queued_assessments")
data class QueuedAssessment(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,

    /** Loan file context. Local-only — PropertyInput has no such field. */
    @ColumnInfo(name = "loan_ref") val loanRef: String = "",
    @ColumnInfo(name = "borrower_name") val borrowerName: String = "",

    // Property fields — mirrors PropertyInput in backend/app/models/schemas.py
    val locality: String,
    @ColumnInfo(name = "prop_type") val propType: String,
    @ColumnInfo(name = "size_sqft") val sizeSqft: Double,
    @ColumnInfo(name = "age_years") val ageYears: Double,
    @ColumnInfo(name = "floor_num") val floorNum: Int,
    @ColumnInfo(name = "is_freehold") val isFreehold: Int,
    @ColumnInfo(name = "is_rera_registered") val isReraRegistered: Int,
    val occupancy: String,
    @ColumnInfo(name = "rental_yield_pct") val rentalYieldPct: Double,
    @ColumnInfo(name = "has_clear_title") val hasClearTitle: Int,
    @ColumnInfo(name = "has_encumbrance") val hasEncumbrance: Int,
    @ColumnInfo(name = "has_legal_dispute") val hasLegalDispute: Int,
    @ColumnInfo(name = "zoning_approved") val zoningApproved: Int,
    @ColumnInfo(name = "geo_lat") val geoLat: Double?,
    @ColumnInfo(name = "geo_lon") val geoLon: Double?,

    /** Absolute paths, pipe-delimited, in capture order. */
    @ColumnInfo(name = "photo_paths") val photoPaths: String,
    /** Tags aligned to photoPaths, pipe-delimited: exterior|interior|... */
    @ColumnInfo(name = "photo_tags") val photoTags: String,

    @ColumnInfo(name = "created_at") val createdAt: Long = System.currentTimeMillis(),
    @ColumnInfo(name = "attempt_count") val attemptCount: Int = 0,
    @ColumnInfo(name = "last_error") val lastError: String? = null,
    @ColumnInfo(name = "status") val status: String = STATUS_PENDING,

    /** Populated once the retry succeeds, so the queue screen can show results. */
    @ColumnInfo(name = "result_json") val resultJson: String? = null,
) {
    val photoPathList: List<String>
        get() = photoPaths.split("|").filter { it.isNotBlank() }

    val photoTagList: List<String>
        get() = photoTags.split("|").filter { it.isNotBlank() }

    companion object {
        const val STATUS_PENDING = "pending"
        const val STATUS_SYNCING = "syncing"
        const val STATUS_SYNCED = "synced"
        const val STATUS_FAILED_PERMANENT = "failed_permanent"

        const val MAX_ATTEMPTS = 8
    }
}

/**
 * A completed assessment kept for the Home screen's recent list and for
 * re-opening/exporting without another round trip.
 */
@Entity(tableName = "assessment_history")
data class AssessmentHistory(
    @PrimaryKey val requestId: String,
    @ColumnInfo(name = "loan_ref") val loanRef: String = "",
    @ColumnInfo(name = "borrower_name") val borrowerName: String = "",
    val locality: String,
    @ColumnInfo(name = "prop_type") val propType: String,
    @ColumnInfo(name = "market_value_mid") val marketValueMid: Long,
    @ColumnInfo(name = "resale_potential_index") val rpi: Double,
    @ColumnInfo(name = "flag_count") val flagCount: Int,
    @ColumnInfo(name = "has_fraud_alert") val hasFraudAlert: Boolean,
    @ColumnInfo(name = "created_at") val createdAt: Long,
    @ColumnInfo(name = "result_json") val resultJson: String,
    @ColumnInfo(name = "was_demo") val wasDemo: Boolean = false,
)
