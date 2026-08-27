package com.propiq.field.data.repo

import com.google.gson.Gson
import com.propiq.field.core.AppSettings
import com.propiq.field.core.Connectivity
import com.propiq.field.core.FailureKind
import com.propiq.field.core.Outcome
import com.propiq.field.data.demo.DemoFixtures
import com.propiq.field.data.local.AssessmentHistory
import com.propiq.field.data.local.HistoryDao
import com.propiq.field.data.local.QueueDao
import com.propiq.field.data.local.QueuedAssessment
import com.propiq.field.data.remote.AssessmentResponse
import com.propiq.field.data.remote.ChatMessageDto
import com.propiq.field.data.remote.ChatRequestDto
import com.propiq.field.data.remote.ChatResponseDto
import com.propiq.field.data.remote.PropIQApi
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.Response
import java.io.File
import java.io.IOException
import java.net.ConnectException
import java.net.SocketTimeoutException
import java.net.UnknownHostException

/**
 * The single place that decides whether an assessment goes to the cloud, comes
 * from a fixture, or lands in the retry queue.
 *
 * ViewModels never touch Retrofit or Room directly — they call [assess] and get
 * back an [Outcome] that already encodes the offline path, so the UI has one
 * uniform thing to render.
 */
class AssessmentRepository(
    private val api: PropIQApi,
    private val queueDao: QueueDao,
    private val historyDao: HistoryDao,
    private val connectivity: Connectivity,
    private val settings: AppSettings,
    private val gson: Gson = Gson(),
) {

    fun observeQueue(): Flow<List<QueuedAssessment>> = queueDao.observeOutstanding()
    fun observePendingCount(): Flow<Int> = queueDao.observePendingCount()
    fun observeHistory(): Flow<List<AssessmentHistory>> = historyDao.observeRecent()

    /**
     * Submit a captured property.
     *
     * Order of operations is deliberate:
     *  1. Demo Mode short-circuits before any I/O — a stage demo must never
     *     depend on the radio.
     *  2. If the radio already says offline, queue immediately instead of
     *     burning 15s on a connect timeout the OS could have answered instantly.
     *  3. Only genuinely retryable failures queue. A 400 (bad property fields)
     *     or 403 (bad API key) will fail identically forever, so queueing it
     *     would just build a backlog of garbage.
     */
    suspend fun assess(
        request: FieldAssessmentRequest,
        photos: List<CapturedPhoto>,
    ): Outcome<AssessmentResponse> = withContext(Dispatchers.IO) {

        if (settings.demoMode.value) {
            val demo = if (request.forceFraudDemo) DemoFixtures.fraud() else DemoFixtures.clean()
            persistHistory(demo, true, request.loanRef, request.borrowerName)
            return@withContext Outcome.Success(demo)
        }

        if (photos.isEmpty()) {
            // The backend returns 400 "No images provided"; fail fast with copy
            // the officer can act on rather than round-tripping for it.
            return@withContext Outcome.Failure(
                FailureKind.BAD_REQUEST,
                "Capture at least one photo before running the assessment.",
            )
        }

        if (!connectivity.isOnline()) {
            val id = enqueue(request, photos, FailureKind.NO_NETWORK)
            return@withContext Outcome.Queued(id, FailureKind.NO_NETWORK)
        }

        when (val result = callAssess(request, photos)) {
            is Outcome.Success -> {
                persistHistory(result.data, false, request.loanRef, request.borrowerName)
                result
            }
            is Outcome.Failure -> {
                if (result.kind.isRetryable) {
                    val id = enqueue(request, photos, result.kind)
                    Outcome.Queued(id, result.kind)
                } else {
                    result
                }
            }
            is Outcome.Queued -> result
        }
    }

    /** Used by both [assess] and the sync worker, so retries hit identical code. */
    suspend fun callAssess(
        request: FieldAssessmentRequest,
        photos: List<CapturedPhoto>,
    ): Outcome<AssessmentResponse> = withContext(Dispatchers.IO) {
        try {
            // The backend reads exactly four fixed tag parts (image_tag_0..3),
            // so pad the list rather than sending a variable number of parts.
            val tags = List(4) { idx -> photos.getOrNull(idx)?.tag ?: DEFAULT_TAGS[idx] }

            val parts = photos.take(4).map { photo ->
                val file = File(photo.path)
                val body = file.asRequestBody("image/jpeg".toMediaTypeOrNull())
                MultipartBody.Part.createFormData("images", file.name, body)
            }

            if (parts.isEmpty()) {
                return@withContext Outcome.Failure(
                    FailureKind.BAD_REQUEST,
                    "The captured photos are no longer on this device.",
                )
            }

            val response = api.assessWithImage(
                locality = request.locality.text(),
                propType = request.propType.text(),
                sizeSqft = request.sizeSqft.text(),
                ageYears = request.ageYears.text(),
                floorNum = request.floorNum.text(),
                isFreehold = request.isFreehold.text(),
                isReraRegistered = request.isReraRegistered.text(),
                occupancy = request.occupancy.text(),
                rentalYieldPct = request.rentalYieldPct.text(),
                hasClearTitle = request.hasClearTitle.text(),
                hasEncumbrance = request.hasEncumbrance.text(),
                hasLegalDispute = request.hasLegalDispute.text(),
                zoningApproved = request.zoningApproved.text(),
                geoLat = request.geoLat?.text(),
                geoLon = request.geoLon?.text(),
                imageTag0 = tags[0].text(),
                imageTag1 = tags[1].text(),
                imageTag2 = tags[2].text(),
                imageTag3 = tags[3].text(),
                images = parts,
            )
            mapResponse(response)
        } catch (e: Throwable) {
            Outcome.Failure(classify(e), e.message ?: "Request failed", e)
        }
    }

    /**
     * Posts a spoken/typed description to the agentic chat endpoint. When the
     * backend's extractor recognises a property it returns
     * `action:"auto_assess"` plus structured fields, which the capture screen
     * folds straight into the form.
     */
    suspend fun interpretDescription(
        transcript: String,
        formContext: Map<String, Any?>,
    ): Outcome<ChatResponseDto> = withContext(Dispatchers.IO) {
        if (!connectivity.isOnline()) {
            return@withContext Outcome.Failure(
                FailureKind.NO_NETWORK,
                "Voice parsing needs a connection. Your transcript is kept — fill the " +
                    "fields manually or try again when you're back online.",
            )
        }
        try {
            val response = api.chat(
                ChatRequestDto(
                    messages = listOf(ChatMessageDto(role = "user", content = transcript)),
                    formContext = formContext,
                )
            )
            mapResponse(response)
        } catch (e: Throwable) {
            Outcome.Failure(classify(e), e.message ?: "Chat request failed", e)
        }
    }

    suspend fun pingBackend(): Outcome<Boolean> = withContext(Dispatchers.IO) {
        if (!connectivity.isOnline()) {
            return@withContext Outcome.Failure(FailureKind.NO_NETWORK, "Device is offline.")
        }
        try {
            val r = api.health()
            if (r.isSuccessful) Outcome.Success(true)
            else Outcome.Failure(httpKind(r.code()), "Backend returned HTTP ${r.code()}")
        } catch (e: Throwable) {
            Outcome.Failure(classify(e), e.message ?: "Health check failed", e)
        }
    }

    // ── Queue plumbing ────────────────────────────────────────────────────

    private suspend fun enqueue(
        request: FieldAssessmentRequest,
        photos: List<CapturedPhoto>,
        reason: FailureKind,
    ): Long = queueDao.insert(
        QueuedAssessment(
            loanRef = request.loanRef,
            borrowerName = request.borrowerName,
            locality = request.locality,
            propType = request.propType,
            sizeSqft = request.sizeSqft,
            ageYears = request.ageYears,
            floorNum = request.floorNum,
            isFreehold = request.isFreehold,
            isReraRegistered = request.isReraRegistered,
            occupancy = request.occupancy,
            rentalYieldPct = request.rentalYieldPct,
            hasClearTitle = request.hasClearTitle,
            hasEncumbrance = request.hasEncumbrance,
            hasLegalDispute = request.hasLegalDispute,
            zoningApproved = request.zoningApproved,
            geoLat = request.geoLat,
            geoLon = request.geoLon,
            photoPaths = photos.joinToString("|") { it.path },
            photoTags = photos.joinToString("|") { it.tag },
            lastError = reason.name,
        )
    )

    suspend fun persistHistory(
        result: AssessmentResponse,
        wasDemo: Boolean,
        loanRef: String = "",
        borrowerName: String = "",
    ) {
        val id = result.requestId ?: return
        runCatching {
            historyDao.upsert(
                AssessmentHistory(
                    requestId = id,
                    loanRef = loanRef,
                    borrowerName = borrowerName,
                    locality = result.locality.orEmpty(),
                    propType = result.propType.orEmpty(),
                    marketValueMid = result.marketValueMid ?: 0L,
                    rpi = result.resalePotentialIndex ?: 0.0,
                    flagCount = result.riskFlags?.size ?: 0,
                    hasFraudAlert = result.fraudAlert != null,
                    createdAt = System.currentTimeMillis(),
                    resultJson = gson.toJson(result),
                    wasDemo = wasDemo,
                )
            )
        }
    }

    fun decode(json: String): AssessmentResponse? =
        runCatching { gson.fromJson(json, AssessmentResponse::class.java) }.getOrNull()

    fun encode(result: AssessmentResponse): String = gson.toJson(result)

    // ── Error mapping ─────────────────────────────────────────────────────

    private fun <T> mapResponse(response: Response<T>): Outcome<T> {
        val body = response.body()
        return if (response.isSuccessful && body != null) {
            Outcome.Success(body)
        } else {
            val detail = runCatching { response.errorBody()?.string() }.getOrNull()
            Outcome.Failure(
                httpKind(response.code()),
                detail?.take(300) ?: "HTTP ${response.code()}",
            )
        }
    }

    private fun httpKind(code: Int): FailureKind = when (code) {
        400, 422 -> FailureKind.BAD_REQUEST
        401, 403 -> FailureKind.UNAUTHORIZED
        429 -> FailureKind.RATE_LIMITED
        in 500..599 -> FailureKind.BACKEND_ERROR
        else -> FailureKind.UNKNOWN
    }

    private fun classify(e: Throwable): FailureKind = when (e) {
        is UnknownHostException -> FailureKind.BACKEND_UNREACHABLE
        is ConnectException -> FailureKind.BACKEND_UNREACHABLE
        is SocketTimeoutException -> FailureKind.TIMEOUT
        is IOException -> if (connectivity.isOnline()) FailureKind.BACKEND_UNREACHABLE
        else FailureKind.NO_NETWORK
        else -> FailureKind.UNKNOWN
    }

    private fun Any.text(): RequestBody =
        toString().toRequestBody("text/plain".toMediaTypeOrNull())

    companion object {
        /** Matches the backend's own image_tag_0..3 defaults. */
        private val DEFAULT_TAGS = listOf("exterior", "interior", "exterior", "interior")
    }
}

/** Flat, serialisable snapshot of everything the backend needs. */
data class FieldAssessmentRequest(
    /**
     * Loan file context. Deliberately NOT among the @Part arguments in
     * [PropIQApi.assessWithImage] — the backend's PropertyInput has no such
     * field and would reject it. It exists to tie the local record to the file
     * the officer is actually working, and to stamp the exported PDF.
     */
    val loanRef: String = "",
    val borrowerName: String = "",
    val locality: String,
    val propType: String,
    val sizeSqft: Double,
    val ageYears: Double,
    val floorNum: Int,
    val isFreehold: Int,
    val isReraRegistered: Int,
    val occupancy: String,
    val rentalYieldPct: Double,
    val hasClearTitle: Int,
    val hasEncumbrance: Int,
    val hasLegalDispute: Int,
    val zoningApproved: Int,
    val geoLat: Double?,
    val geoLon: Double?,
    val forceFraudDemo: Boolean = false,
) {
    companion object {
        fun fromQueued(q: QueuedAssessment) = FieldAssessmentRequest(
            loanRef = q.loanRef,
            borrowerName = q.borrowerName,
            locality = q.locality,
            propType = q.propType,
            sizeSqft = q.sizeSqft,
            ageYears = q.ageYears,
            floorNum = q.floorNum,
            isFreehold = q.isFreehold,
            isReraRegistered = q.isReraRegistered,
            occupancy = q.occupancy,
            rentalYieldPct = q.rentalYieldPct,
            hasClearTitle = q.hasClearTitle,
            hasEncumbrance = q.hasEncumbrance,
            hasLegalDispute = q.hasLegalDispute,
            zoningApproved = q.zoningApproved,
            geoLat = q.geoLat,
            geoLon = q.geoLon,
        )
    }
}

data class CapturedPhoto(
    val path: String,
    val tag: String,
    val qualityScore: Int = 0,
    val sceneLabel: String = "",
)
