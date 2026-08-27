package com.propiq.field.ui.components

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

/**
 * Permission flow with a real rationale step.
 *
 * The sequence is: explain *why this specific feature needs this permission* →
 * request → if permanently denied, offer Settings. A blind
 * `launcher.launch(CAMERA)` on screen open is what produces the reflexive
 * "Deny" that then breaks the demo, so the rationale is shown before the system
 * dialog, not after a denial.
 */
class PermissionSpec(
    val permission: String,
    val title: String,
    val rationale: String,
    val deniedMessage: String,
)

object Permissions {
    val Camera = PermissionSpec(
        permission = android.Manifest.permission.CAMERA,
        title = "Camera access",
        rationale = "PropIQ Field grades the property's condition from photos you take on the " +
            "spot. Frames are checked on this device first, then sent to the valuation engine. " +
            "There is no gallery import — a collateral photo has to come from the site visit.",
        deniedMessage = "Camera access is off, so the property cannot be captured. Turn it on in " +
            "Settings to run an assessment.",
    )

    val Location = PermissionSpec(
        permission = android.Manifest.permission.ACCESS_FINE_LOCATION,
        title = "Location access",
        rationale = "Your GPS coordinates are attached to the assessment so the valuation is " +
            "pinned to where you're standing, not to a locality centroid. It also lets the " +
            "server skip a geocoding lookup, which makes the result come back faster.",
        deniedMessage = "Without location the assessment still works — it falls back to the " +
            "locality you pick, which is slightly less precise.",
    )

    val Microphone = PermissionSpec(
        permission = android.Manifest.permission.RECORD_AUDIO,
        title = "Microphone access",
        rationale = "Describe the property out loud instead of typing it — useful when you're " +
            "holding the phone up to a wall. Where the device supports it, speech is " +
            "transcribed entirely on-device.",
        deniedMessage = "Voice capture is off. You can still type the property details.",
    )
}

fun Context.hasPermission(permission: String): Boolean =
    ContextCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED

/**
 * Remembers a launcher that shows [spec]'s rationale first.
 *
 * Returns a callable: invoke it to begin the flow. [onResult] fires with the
 * final grant state either way, so callers can degrade gracefully rather than
 * blocking.
 */
@Composable
fun rememberPermissionFlow(
    spec: PermissionSpec,
    onResult: (Boolean) -> Unit,
): () -> Unit {
    val context = LocalContext.current
    var showRationale by remember { mutableStateOf(false) }
    var showBlocked by remember { mutableStateOf(false) }

    val launcher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (!granted) {
            val activity = context as? Activity
            // shouldShowRationale == false after a denial means "don't ask again".
            val permanentlyDenied = activity != null &&
                !ActivityCompat.shouldShowRequestPermissionRationale(activity, spec.permission)
            if (permanentlyDenied) showBlocked = true
        }
        onResult(granted)
    }

    if (showRationale) {
        AlertDialog(
            onDismissRequest = {
                showRationale = false
                onResult(false)
            },
            title = { Text(spec.title) },
            text = { Text(spec.rationale) },
            confirmButton = {
                TextButton(onClick = {
                    showRationale = false
                    launcher.launch(spec.permission)
                }) { Text("Continue") }
            },
            dismissButton = {
                TextButton(onClick = {
                    showRationale = false
                    onResult(false)
                }) { Text("Not now") }
            },
        )
    }

    if (showBlocked) {
        AlertDialog(
            onDismissRequest = { showBlocked = false },
            title = { Text("${spec.title} is blocked") },
            text = { Text(spec.deniedMessage) },
            confirmButton = {
                TextButton(onClick = {
                    showBlocked = false
                    runCatching {
                        context.startActivity(
                            Intent(
                                Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                                Uri.fromParts("package", context.packageName, null),
                            )
                        )
                    }
                }) { Text("Open Settings") }
            },
            dismissButton = {
                TextButton(onClick = { showBlocked = false }) { Text("Dismiss") }
            },
        )
    }

    return {
        when {
            context.hasPermission(spec.permission) -> onResult(true)
            else -> showRationale = true
        }
    }
}
