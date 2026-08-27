package com.propiq.field.ondevice

import android.content.Context
import android.util.Log
import com.google.mediapipe.tasks.genai.llminference.LlmInference
import com.google.mediapipe.tasks.genai.llminference.LlmInferenceSession
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import org.json.JSONObject
import java.io.File

/**
 * On-device LLM, running a small quantised open-weights model (Gemma 3 1B / Phi-3-mini
 * class) through MediaPipe's LLM Inference API on the phone's GPU/NPU.
 *
 * WHY THIS EXISTS
 * ---------------
 * The offline queue already lets an officer *submit* an assessment with no
 * signal. But until now they still had to type the property in by hand,
 * because the voice-to-structured-data step round-tripped to the backend's
 * /api/v1/chat extractor. In a basement that step was dead — which is exactly
 * the scenario the queue was built for. This closes that hole: the same spoken
 * description is parsed into structured fields entirely on the handset.
 *
 * It also changes what the phone *is* in this product. Without it the device is
 * a camera and a GPS chip in front of a cloud model. With it, real inference
 * happens on the hardware in the officer's hand.
 *
 * FAILURE POSTURE — read this before changing anything here
 * ---------------------------------------------------------
 * The model file is 0.5-1.3 GB, is licence-gated, and is side-loaded to the
 * device (see android/README.md). It is NOT in the APK and NOT in the repo.
 * Therefore this class is written so that *every* failure — absent file,
 * corrupt file, OOM, unsupported backend, slow inference — degrades silently to
 * [LlmState.Unavailable], and the caller falls back to the cloud extractor.
 *
 * Nothing in the app is allowed to require this. It is strictly additive.
 */
class LocalLlm(private val context: Context) {

    private val _state = MutableStateFlow<LlmState>(LlmState.NotInitialised)
    val state: StateFlow<LlmState> = _state.asStateFlow()

    @Volatile private var engine: LlmInference? = null

    /**
     * Locates a side-loaded model. Checked in priority order so a demo machine
     * and a dev machine can differ without a code change.
     */
    fun findModel(): File? = MODEL_SEARCH_PATHS
        .asSequence()
        .map { File(it) }
        .firstOrNull { it.exists() && it.length() > MIN_PLAUSIBLE_MODEL_BYTES }

    fun isReady(): Boolean = engine != null && _state.value is LlmState.Ready

    /**
     * Loads the model. Safe to call repeatedly; only the first call does work.
     *
     * Deliberately NOT called at app startup — loading a 1 GB model costs
     * seconds and memory, and most sessions never need it. The capture screen
     * warms it when it opens.
     */
    suspend fun warmUp(): LlmState = withContext(Dispatchers.IO) {
        if (engine != null) return@withContext _state.value

        val model = findModel()
        if (model == null) {
            _state.value = LlmState.Unavailable(
                "No on-device model found. Voice parsing will use the cloud."
            )
            return@withContext _state.value
        }

        _state.value = LlmState.Loading
        try {
            val options = LlmInference.LlmInferenceOptions.builder()
                .setModelPath(model.absolutePath)
                .setMaxTokens(MAX_TOKENS)
                // PreferredBackend.GPU delegates to the Adreno/NPU path where the
                // device exposes it, and falls back to CPU on its own if not.
                .setPreferredBackend(LlmInference.Backend.GPU)
                .build()

            engine = LlmInference.createFromOptions(context, options)
            _state.value = LlmState.Ready(
                modelName = model.name,
                sizeMb = (model.length() / 1_048_576L).toInt(),
            )
        } catch (t: Throwable) {
            // OOM, missing native lib, unsupported quantisation, corrupt file —
            // all of it lands here and all of it means "use the cloud".
            Log.w(TAG, "On-device LLM unavailable: ${t.message}")
            runCatching { engine?.close() }
            engine = null
            _state.value = LlmState.Unavailable(
                "On-device model could not be loaded on this device."
            )
        }
        _state.value
    }

    /**
     * Parses a spoken/typed property description into structured fields.
     *
     * Returns null on any failure so the caller can fall through to the cloud
     * extractor. A null here is never surfaced to the officer as an error — it
     * is just a quieter path.
     */
    suspend fun extractProperty(
        transcript: String,
        knownLocalities: List<String>,
    ): LocalExtraction? = withContext(Dispatchers.Default) {
        val inference = engine ?: return@withContext null
        if (transcript.isBlank()) return@withContext null

        val raw = withTimeoutOrNull(INFERENCE_TIMEOUT_MS) {
            runCatching {
                // A fresh session per call: this is a stateless extraction, and
                // carrying context between two unrelated properties would let one
                // bleed into the next.
                LlmInferenceSession.createFromOptions(
                    inference,
                    LlmInferenceSession.LlmInferenceSessionOptions.builder()
                        .setTemperature(0.1f)
                        .setTopK(TOP_K)
                        .build(),
                ).use { session ->
                    session.addQueryChunk(buildPrompt(transcript, knownLocalities))
                    session.generateResponse()
                }
            }.getOrNull()
        } ?: return@withContext null

        parseResponse(raw, knownLocalities)
    }

    fun close() {
        runCatching { engine?.close() }
        engine = null
        _state.value = LlmState.NotInitialised
    }

    // ── Prompting ─────────────────────────────────────────────────────────

    /**
     * Mirrors the field contract of the backend's own extractor
     * (`_EXTRACTION_SYSTEM_PROMPT` / `_extract_property_fields` in
     * backend/app/main.py) so both paths produce the same shape and the rest of
     * the app cannot tell which one ran.
     *
     * A 1B model needs the constraints spelled out far harder than a 70B does:
     * the locality allow-list is inlined, the enum is enumerated, and the output
     * contract is shown rather than described.
     */
    private fun buildPrompt(transcript: String, localities: List<String>): String {
        // Keep the allow-list short enough not to dominate the context window.
        val shortlist = localities.take(MAX_LOCALITIES_IN_PROMPT).joinToString(", ")
        return """
You extract Indian property details from a loan officer's spoken description.

Return ONLY a JSON object. No explanation, no markdown fence.

Schema:
{"locality":string,"prop_type":string,"size_sqft":number,"age_years":number,"floor_num":number}

prop_type must be exactly one of:
1bhk_apartment, 2bhk_apartment, 3bhk_apartment, 4bhk_apartment, villa, shop, office, plot, warehouse, factory

locality must be the closest match from this list: $shortlist

Rules:
- "3 BHK", "three bhk", "3bhk" all mean 3bhk_apartment.
- Sizes are in square feet. "fourteen fifty" means 1450. "1.2 thousand" means 1200.
- Indian numbering may appear: "one lakh" = 100000.
- If a field is genuinely not stated, omit that key. Never invent a value.

Description: "$transcript"

JSON:
""".trimIndent()
    }

    // ── Response handling ─────────────────────────────────────────────────

    /**
     * Small models leak prose, markdown fences and trailing commentary around
     * the JSON no matter how the prompt is worded, so we extract the first
     * balanced object rather than trusting the whole response.
     */
    private fun parseResponse(raw: String, localities: List<String>): LocalExtraction? {
        val json = extractFirstJsonObject(raw) ?: return null
        return runCatching {
            val obj = JSONObject(json)

            val locality = obj.optString("locality").takeIf { it.isNotBlank() }
                ?.let { snapToKnownLocality(it, localities) }
            val propType = obj.optString("prop_type").takeIf { it.isNotBlank() }
                ?.lowercase()?.replace(" ", "_")
                ?.takeIf { it in VALID_PROP_TYPES }
            val size = obj.optDouble("size_sqft").takeIf { !it.isNaN() && it > 100 && it < 50_000 }
            val age = obj.optDouble("age_years").takeIf { !it.isNaN() && it >= 0 && it <= 80 }
            val floor = obj.optInt("floor_num", -1).takeIf { it in 0..50 }

            // Anything less is not worth pre-filling a form with — fall through
            // to the cloud rather than half-populating and misleading the officer.
            if (locality == null && propType == null && size == null) return null

            LocalExtraction(
                locality = locality,
                propType = propType,
                sizeSqft = size,
                ageYears = age,
                floorNum = floor,
            )
        }.getOrNull()
    }

    private fun extractFirstJsonObject(raw: String): String? {
        val start = raw.indexOf('{')
        if (start < 0) return null
        var depth = 0
        for (i in start until raw.length) {
            when (raw[i]) {
                '{' -> depth++
                '}' -> {
                    depth--
                    if (depth == 0) return raw.substring(start, i + 1)
                }
            }
        }
        return null
    }

    /**
     * A small model will happily emit "Banner" or "Baner Road". The picker only
     * accepts localities the valuation model actually knows, so snap to the
     * nearest known name and drop it entirely if nothing is close.
     */
    private fun snapToKnownLocality(candidate: String, localities: List<String>): String? {
        val c = candidate.trim().lowercase()
        localities.firstOrNull { it.lowercase() == c }?.let { return it }
        localities.firstOrNull { it.lowercase().startsWith(c) || c.startsWith(it.lowercase()) }
            ?.let { return it }
        return localities.minByOrNull { levenshtein(c, it.lowercase()) }
            ?.takeIf { levenshtein(c, it.lowercase()) <= MAX_LOCALITY_EDIT_DISTANCE }
    }

    private fun levenshtein(a: String, b: String): Int {
        if (a == b) return 0
        if (a.isEmpty()) return b.length
        if (b.isEmpty()) return a.length
        var prev = IntArray(b.length + 1) { it }
        var cur = IntArray(b.length + 1)
        for (i in 1..a.length) {
            cur[0] = i
            for (j in 1..b.length) {
                val cost = if (a[i - 1] == b[j - 1]) 0 else 1
                cur[j] = minOf(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
            }
            val swap = prev; prev = cur; cur = swap
        }
        return prev[b.length]
    }

    companion object {
        private const val TAG = "LocalLlm"

        private const val MAX_TOKENS = 1024
        private const val TOP_K = 40
        private const val INFERENCE_TIMEOUT_MS = 25_000L
        private const val MAX_LOCALITIES_IN_PROMPT = 24
        private const val MAX_LOCALITY_EDIT_DISTANCE = 3

        /** Guards against a truncated or failed adb push being treated as a model. */
        private const val MIN_PLAUSIBLE_MODEL_BYTES = 50L * 1024 * 1024

        /**
         * Side-load targets, in priority order. /data/local/tmp is the adb push
         * destination that needs no storage permission and survives reinstalls.
         */
        val MODEL_SEARCH_PATHS = listOf(
            "/data/local/tmp/propiq/model.task",
            "/data/local/tmp/llm/model.task",
            "/sdcard/Download/propiq-model.task",
            "/sdcard/propiq/model.task",
        )

        private val VALID_PROP_TYPES = setOf(
            "1bhk_apartment", "2bhk_apartment", "3bhk_apartment", "4bhk_apartment",
            "villa", "shop", "office", "plot", "warehouse", "factory",
        )
    }
}

sealed interface LlmState {
    data object NotInitialised : LlmState
    data object Loading : LlmState
    data class Ready(val modelName: String, val sizeMb: Int) : LlmState
    data class Unavailable(val reason: String) : LlmState
}

/** Field-for-field compatible with the backend's `extracted_fields` block. */
data class LocalExtraction(
    val locality: String?,
    val propType: String?,
    val sizeSqft: Double?,
    val ageYears: Double?,
    val floorNum: Int?,
)
