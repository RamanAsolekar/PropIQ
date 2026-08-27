package com.propiq.field.ui.capture

import android.content.Context
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import kotlinx.coroutines.suspendCancellableCoroutine
import java.io.File
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

/**
 * Thin CameraX wrapper.
 *
 * Live capture only — there is deliberately no gallery picker anywhere in this
 * app. A field valuation is worthless if the officer can attach a photo taken
 * somewhere else at some other time, and the CV fraud checks on the backend
 * assume the frame came off this device's sensor now.
 */
class CameraController(private val context: Context) {

    private var imageCapture: ImageCapture? = null
    private var provider: ProcessCameraProvider? = null

    suspend fun bind(
        lifecycleOwner: androidx.lifecycle.LifecycleOwner,
        previewView: PreviewView,
    ): Result<Unit> = runCatching {
        val cameraProvider = awaitProvider()
        provider = cameraProvider

        val preview = Preview.Builder().build().also {
            it.setSurfaceProvider(previewView.surfaceProvider)
        }
        val capture = ImageCapture.Builder()
            .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
            .build()
        imageCapture = capture

        cameraProvider.unbindAll()
        cameraProvider.bindToLifecycle(
            lifecycleOwner,
            CameraSelector.DEFAULT_BACK_CAMERA,
            preview,
            capture,
        )
        Unit
    }

    suspend fun capture(outputDir: File): Result<File> = runCatching {
        val capture = imageCapture ?: error("Camera is not ready yet.")
        if (!outputDir.exists()) outputDir.mkdirs()
        val file = File(outputDir, "propiq_${System.currentTimeMillis()}.jpg")
        val options = ImageCapture.OutputFileOptions.Builder(file).build()

        suspendCancellableCoroutine { cont ->
            capture.takePicture(
                options,
                ContextCompat.getMainExecutor(context),
                object : ImageCapture.OnImageSavedCallback {
                    override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                        cont.resume(file)
                    }

                    override fun onError(exception: ImageCaptureException) {
                        cont.resumeWithException(exception)
                    }
                },
            )
        }
    }

    fun release() {
        runCatching { provider?.unbindAll() }
        imageCapture = null
        provider = null
    }

    private suspend fun awaitProvider(): ProcessCameraProvider =
        suspendCancellableCoroutine { cont ->
            val future = ProcessCameraProvider.getInstance(context)
            future.addListener(
                {
                    runCatching { future.get() }
                        .onSuccess { cont.resume(it) }
                        .onFailure { cont.resumeWithException(it) }
                },
                ContextCompat.getMainExecutor(context),
            )
        }
}
