package com.propiq.field.ui.capture

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.propiq.field.AppContainer
import com.propiq.field.core.FailureKind
import com.propiq.field.core.Outcome
import com.propiq.field.core.userMessage
import com.propiq.field.data.demo.DemoFixtures
import com.propiq.field.data.demo.Localities
import com.propiq.field.data.repo.CapturedPhoto
import com.propiq.field.ondevice.PhotoVerdict
import com.propiq.field.speech.VoiceEvent
import com.propiq.field.sync.SyncWorker
import android.content.Context
import kotlinx.coroutines.Job
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.launch
import java.io.File

/**
 * Owns the whole capture flow: GPS, voice, the on-device photo gate, and
 * submission.
 *
 * No business logic lives in the Composables — they render [uiState] and call
 * intent methods here. That boundary is what makes the hybrid pipeline legible
 * in a walkthrough: this class calls [com.propiq.field.ondevice.PhotoGate]
 * (local NPU) and then [com.propiq.field.data.repo.AssessmentRepository]
 * (cloud), and nothing else in the app crosses that line.
 */
class CaptureViewModel(
    private val container: AppContainer,
    private val appContext: Context,
) : ViewModel() {

    private val _uiState = MutableStateFlow(CaptureUiState())
    val uiState: StateFlow<CaptureUiState> = _uiState.asStateFlow()

    private val _events = Channel<CaptureEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    private var voiceJob: Job? = null

    init {
        viewModelScope.launch {
            container.connectivity.observe().collect { online ->
                _uiState.value = _uiState.value.copy(isOnline = online)
            }
        }
        viewModelScope.launch {
            container.settings.demoMode.collect { demo ->
                _uiState.value = _uiState.value.copy(demoMode = demo)
                if (demo && _uiState.value.draft.locality.isBlank()) {
                    // Pre-seed the sample property so the stage flow is one tap.
                    _uiState.value = _uiState.value.copy(draft = PropertyDraft.sample())
                }
            }
        }
    }

    // ── Form ──────────────────────────────────────────────────────────────

    fun updateDraft(transform: (PropertyDraft) -> PropertyDraft) {
        _uiState.value = _uiState.value.copy(draft = transform(_uiState.value.draft))
    }

    fun loadSampleProperty() {
        _uiState.value = _uiState.value.copy(draft = PropertyDraft.sample(), error = null)
    }

    // ── Location ──────────────────────────────────────────────────────────

    /**
     * Called on screen open once the permission result is known. A denial is
     * not an error state — the assessment proceeds with the locality centroid,
     * which is what the backend would have geocoded to anyway.
     */
    fun captureLocation(granted: Boolean) {
        if (!granted) {
            _uiState.value = _uiState.value.copy(locationDenied = true, locating = false)
            return
        }
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(locating = true, locationDenied = false)
            val fix = container.locationProvider.currentFix()
            val state = _uiState.value
            var draft = state.draft
            // Only auto-select a locality if the officer has not already chosen one.
            if (fix != null && draft.locality.isBlank()) {
                val nearest = fix.nearestLocality(Localities.coordinateMap())
                if (nearest != null) {
                    val entry = Localities.byName(nearest)
                    draft = draft.copy(
                        locality = nearest,
                        city = entry?.city ?: draft.city,
                    )
                }
            }
            _uiState.value = state.copy(geoFix = fix, locating = false, draft = draft)
        }
    }

    // ── Voice ─────────────────────────────────────────────────────────────

    fun startVoice(granted: Boolean) {
        if (!granted) {
            _uiState.value = _uiState.value.copy(
                voiceStatus = "Microphone permission is needed for hands-free capture."
            )
            return
        }
        if (!container.voiceCapture.isAvailable()) {
            _uiState.value = _uiState.value.copy(
                voiceStatus = "This device has no speech recogniser. Type the description instead."
            )
            return
        }
        voiceJob?.cancel()
        _uiState.value = _uiState.value.copy(
            voiceActive = true,
            voiceTranscript = "",
            voicePartial = "",
            voiceStatus = null,
        )
        voiceJob = viewModelScope.launch {
            container.voiceCapture.listen().collect { event ->
                val s = _uiState.value
                _uiState.value = when (event) {
                    is VoiceEvent.Ready -> s.copy(
                        voiceOnDevice = event.onDevice,
                        voiceStatus = if (event.onDevice)
                            "Listening on-device — works with no signal"
                        else "Listening",
                    )
                    VoiceEvent.Listening -> s.copy(voiceStatus = s.voiceStatus ?: "Listening")
                    VoiceEvent.Processing -> s.copy(voiceStatus = "Processing speech…")
                    is VoiceEvent.Amplitude -> s.copy(voiceAmplitude = event.level)
                    is VoiceEvent.Partial -> s.copy(voicePartial = event.text)
                    is VoiceEvent.Final -> {
                        val text = event.text.ifBlank { s.voicePartial }
                        s.copy(
                            voiceActive = false,
                            voiceTranscript = text,
                            voicePartial = "",
                            voiceStatus = if (text.isBlank()) "Nothing was captured." else null,
                        ).also { if (text.isNotBlank()) interpret(text) }
                    }
                    is VoiceEvent.Error -> s.copy(
                        voiceActive = false,
                        voiceStatus = event.message,
                    )
                    is VoiceEvent.Unavailable -> s.copy(
                        voiceActive = false,
                        voiceStatus = event.message,
                    )
                }
            }
        }
    }

    fun stopVoice() {
        voiceJob?.cancel()
        voiceJob = null
        _uiState.value = _uiState.value.copy(voiceActive = false, voiceAmplitude = 0f)
    }

    fun setTranscript(text: String) {
        _uiState.value = _uiState.value.copy(voiceTranscript = text)
    }

    /**
     * Sends the transcript to /api/v1/chat and folds any extracted fields into
     * the form. Reuses the backend's existing agentic extractor rather than
     * duplicating NL parsing on the device.
     */
    fun interpret(text: String = _uiState.value.voiceTranscript) {
        if (text.isBlank()) return

        if (_uiState.value.demoMode) {
            // Stage-safe: no network dependency in the voice step either.
            _uiState.value = _uiState.value.copy(
                draft = PropertyDraft.sample(),
                voiceStatus = "Demo Mode — sample property loaded from the description.",
            )
            return
        }

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(voiceParsing = true, voiceStatus = "Reading the description…")
            val d = _uiState.value.draft
            val context = buildMap<String, Any?> {
                if (d.locality.isNotBlank()) put("locality", d.locality)
                put("prop_type", d.propType)
                d.sizeSqft.toDoubleOrNull()?.let { put("size_sqft", it) }
                d.ageYears.toDoubleOrNull()?.let { put("age_years", it) }
            }

            when (val result = container.repository.interpretDescription(text, context)) {
                is Outcome.Success -> {
                    val fields = result.data.extractedFields
                    if (result.data.isAutoAssess && fields != null) {
                        val entry = fields.locality?.let { Localities.byName(it) }
                        _uiState.value = _uiState.value.copy(
                            voiceParsing = false,
                            voiceStatus = "Understood — check the fields below, then capture.",
                            draft = _uiState.value.draft.copy(
                                locality = entry?.name ?: fields.locality ?: _uiState.value.draft.locality,
                                city = entry?.city ?: _uiState.value.draft.city,
                                propType = fields.propType ?: _uiState.value.draft.propType,
                                sizeSqft = fields.sizeSqft?.toInt()?.toString()
                                    ?: _uiState.value.draft.sizeSqft,
                                ageYears = fields.ageYears?.toInt()?.toString()
                                    ?: _uiState.value.draft.ageYears,
                                floorNum = fields.floorNum?.toString() ?: _uiState.value.draft.floorNum,
                                isFreehold = fields.isFreehold?.let { it == 1 }
                                    ?: _uiState.value.draft.isFreehold,
                                isReraRegistered = fields.isReraRegistered?.let { it == 1 }
                                    ?: _uiState.value.draft.isReraRegistered,
                            ),
                        )
                    } else {
                        _uiState.value = _uiState.value.copy(
                            voiceParsing = false,
                            voiceStatus = result.data.reply?.take(160)
                                ?: "Couldn't pull property details out of that. Try including " +
                                "locality, type, size and age.",
                        )
                    }
                }
                is Outcome.Failure -> _uiState.value = _uiState.value.copy(
                    voiceParsing = false,
                    voiceStatus = result.kind.userMessage(),
                )
                is Outcome.Queued -> _uiState.value = _uiState.value.copy(voiceParsing = false)
            }
        }
    }

    // ── Camera + on-device gate ───────────────────────────────────────────

    fun setActiveTag(tag: String) {
        _uiState.value = _uiState.value.copy(activeTag = tag)
    }

    fun openCamera() {
        _uiState.value = _uiState.value.copy(stage = CaptureStage.CAMERA, cameraError = null)
    }

    fun closeCamera() {
        _uiState.value = _uiState.value.copy(stage = CaptureStage.FORM, lastVerdict = null)
    }

    fun reportCameraError(message: String) {
        _uiState.value = _uiState.value.copy(cameraError = message)
    }

    /**
     * Runs the on-device pre-check. A blocking verdict never reaches the queue
     * or the network — the file is deleted immediately and the officer is told
     * why, in-frame, in a few hundred milliseconds.
     */
    fun onPhotoCaptured(file: File) {
        val tag = _uiState.value.activeTag
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(analyzing = true, lastVerdict = null)
            val verdict = container.photoGate.evaluate(file, tag)

            if (verdict.reason.isBlocking) {
                runCatching { file.delete() }
                _uiState.value = _uiState.value.copy(analyzing = false, lastVerdict = verdict)
                return@launch
            }

            val frames = (_uiState.value.frames + CapturedFrame(file.absolutePath, tag, verdict))
                .take(MAX_FRAMES)
            _uiState.value = _uiState.value.copy(
                analyzing = false,
                lastVerdict = verdict,
                frames = frames,
                // Nudge toward a balanced exterior/interior pair, which the
                // backend weights 60/40.
                activeTag = if (tag == "exterior" && frames.none { it.tag == "interior" })
                    "interior" else tag,
            )
        }
    }

    fun dismissVerdict() {
        _uiState.value = _uiState.value.copy(lastVerdict = null)
    }

    fun removeFrame(path: String) {
        runCatching { File(path).delete() }
        _uiState.value = _uiState.value.copy(
            frames = _uiState.value.frames.filterNot { it.path == path }
        )
    }

    // ── Submit ────────────────────────────────────────────────────────────

    fun submit(forceFraudDemo: Boolean = false) {
        val state = _uiState.value
        if (!state.draft.isComplete) {
            _uiState.value = state.copy(error = "Fill locality, size, age and floor first.")
            return
        }
        if (state.frames.isEmpty() && !state.demoMode) {
            _uiState.value = state.copy(error = "Capture at least one photo of the property.")
            return
        }

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                stage = CaptureStage.SUBMITTING,
                error = null,
                submitStatus = if (state.demoMode) "Running sample assessment…"
                else "Uploading ${state.frames.size} photo(s) to the valuation engine…",
            )

            val fallback = Localities.byName(state.draft.locality)?.let { it.lat to it.lon }
            val request = state.draft.toRequest(state.geoFix, fallback, forceFraudDemo)
            val photos = state.frames.map {
                CapturedPhoto(it.path, it.tag, it.verdict.qualityScore, it.verdict.detectedScene.label)
            }

            when (val outcome = container.repository.assess(request, photos)) {
                is Outcome.Success -> {
                    _uiState.value = _uiState.value.copy(stage = CaptureStage.FORM, submitStatus = "")
                    outcome.data.requestId?.let {
                        _events.send(CaptureEvent.NavigateToResults(it))
                    }
                }
                is Outcome.Queued -> {
                    SyncWorker.schedule(appContext)
                    _uiState.value = _uiState.value.copy(
                        stage = CaptureStage.FORM,
                        submitStatus = "",
                        frames = emptyList(),
                    )
                    _events.send(CaptureEvent.Queued(outcome.reason.userMessage()))
                }
                is Outcome.Failure -> {
                    _uiState.value = _uiState.value.copy(
                        stage = CaptureStage.FORM,
                        submitStatus = "",
                        error = outcome.kind.userMessage(),
                    )
                }
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    override fun onCleared() {
        voiceJob?.cancel()
        super.onCleared()
    }

    companion object {
        /** The backend reads at most four tagged images (image_tag_0..3). */
        const val MAX_FRAMES = 4

        fun factory(container: AppContainer, context: Context) = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T =
                CaptureViewModel(container, context.applicationContext) as T
        }
    }
}
