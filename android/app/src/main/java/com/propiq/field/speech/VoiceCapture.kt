package com.propiq.field.speech

import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow

/**
 * Hands-free property description via the platform SpeechRecognizer.
 *
 * The officer is usually holding the phone up to a wall with a torch in the
 * other hand; typing "3bhk apartment in Baner, 1450 square feet, 8 years old"
 * on a phone keyboard while standing in an empty flat is the actual friction
 * this removes.
 *
 * On API 31+ we request `createOnDeviceSpeechRecognizer` where the device
 * offers it, so dictation keeps working with the radio off — which is the whole
 * point in a basement. We fall back to the standard recogniser (which may use
 * the network) when on-device recognition is unavailable, and report which one
 * is actually in use so the UI can be honest about it.
 *
 * The transcript is not parsed on-device. It is posted to the backend's
 * /api/v1/chat endpoint, whose agentic extractor (`_extract_property_fields`,
 * backend/app/main.py:1548) returns `action:"auto_assess"` with structured
 * fields — reusing the exact NL understanding the web app already has instead
 * of writing a second, weaker parser here.
 */
class VoiceCapture(private val context: Context) {

    fun isAvailable(): Boolean = SpeechRecognizer.isRecognitionAvailable(context)

    fun supportsOnDevice(): Boolean =
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
            runCatching { SpeechRecognizer.isOnDeviceRecognitionAvailable(context) }
                .getOrDefault(false)

    /**
     * Cold-flow dictation session. Collecting starts the microphone; cancelling
     * the collector tears the recogniser down. SpeechRecognizer is main-thread
     * only, so the caller must collect on the main dispatcher.
     */
    fun listen(): Flow<VoiceEvent> = callbackFlow {
        if (!isAvailable()) {
            trySend(VoiceEvent.Unavailable("No speech recognition service on this device."))
            close()
            return@callbackFlow
        }

        val onDevice = supportsOnDevice()
        val recognizer = runCatching {
            if (onDevice) SpeechRecognizer.createOnDeviceSpeechRecognizer(context)
            else SpeechRecognizer.createSpeechRecognizer(context)
        }.getOrNull()

        if (recognizer == null) {
            trySend(VoiceEvent.Unavailable("Could not start the speech recogniser."))
            close()
            return@callbackFlow
        }

        trySend(VoiceEvent.Ready(onDevice = onDevice))

        val listener = object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                trySend(VoiceEvent.Listening)
            }

            override fun onRmsChanged(rmsdB: Float) {
                // Normalised 0..1 for the live waveform in the capture sheet.
                trySend(VoiceEvent.Amplitude(((rmsdB + 2f) / 12f).coerceIn(0f, 1f)))
            }

            override fun onPartialResults(partialResults: Bundle?) {
                partialResults
                    ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    ?.firstOrNull()
                    ?.let { trySend(VoiceEvent.Partial(it)) }
            }

            override fun onResults(results: Bundle?) {
                val text = results
                    ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    ?.firstOrNull()
                    .orEmpty()
                trySend(VoiceEvent.Final(text))
                close()
            }

            override fun onError(error: Int) {
                trySend(VoiceEvent.Error(describe(error), recoverable = isRecoverable(error)))
                close()
            }

            override fun onEndOfSpeech() { trySend(VoiceEvent.Processing) }
            override fun onBeginningOfSpeech() {}
            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEvent(eventType: Int, params: Bundle?) {}
        }

        recognizer.setRecognitionListener(listener)

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM,
            )
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            // Indian English gets "lakh", "BHK" and locality names markedly better
            // than en-US does.
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-IN")
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 1800L)
        }

        runCatching { recognizer.startListening(intent) }
            .onFailure {
                trySend(VoiceEvent.Error("Microphone unavailable.", recoverable = true))
                close()
            }

        awaitClose {
            runCatching {
                recognizer.stopListening()
                recognizer.destroy()
            }
        }
    }

    private fun isRecoverable(error: Int): Boolean = when (error) {
        SpeechRecognizer.ERROR_NO_MATCH,
        SpeechRecognizer.ERROR_SPEECH_TIMEOUT,
        SpeechRecognizer.ERROR_NETWORK_TIMEOUT,
        SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> true
        else -> false
    }

    private fun describe(error: Int): String = when (error) {
        SpeechRecognizer.ERROR_AUDIO -> "Microphone error. Try again."
        SpeechRecognizer.ERROR_CLIENT -> "Recogniser stopped unexpectedly."
        SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS ->
            "Microphone permission is required for voice capture."
        SpeechRecognizer.ERROR_NETWORK ->
            "Speech recognition needs a network on this device. Type the description instead."
        SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Speech service timed out."
        SpeechRecognizer.ERROR_NO_MATCH -> "Didn't catch that. Say it again."
        SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Recogniser is busy. Try again."
        SpeechRecognizer.ERROR_SERVER -> "Speech server error."
        SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "No speech detected."
        else -> "Voice capture failed."
    }
}

sealed interface VoiceEvent {
    data class Ready(val onDevice: Boolean) : VoiceEvent
    data object Listening : VoiceEvent
    data object Processing : VoiceEvent
    data class Amplitude(val level: Float) : VoiceEvent
    data class Partial(val text: String) : VoiceEvent
    data class Final(val text: String) : VoiceEvent
    data class Error(val message: String, val recoverable: Boolean) : VoiceEvent
    data class Unavailable(val message: String) : VoiceEvent
}
