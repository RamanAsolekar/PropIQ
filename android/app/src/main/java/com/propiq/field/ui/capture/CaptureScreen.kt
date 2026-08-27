package com.propiq.field.ui.capture

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Memory
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.camera.view.PreviewView
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil.compose.AsyncImage
import com.propiq.field.data.demo.Localities
import com.propiq.field.ondevice.LlmState
import com.propiq.field.ondevice.PhotoReason
import com.propiq.field.speech.VoiceLanguage
import com.propiq.field.ui.components.ErrorState
import com.propiq.field.ui.components.OfflineBanner
import com.propiq.field.ui.components.Pill
import com.propiq.field.ui.components.Permissions
import com.propiq.field.ui.components.ResultsSkeleton
import com.propiq.field.ui.components.SectionCard
import com.propiq.field.ui.components.SectionLabel
import com.propiq.field.ui.components.rememberPermissionFlow
import com.propiq.field.ui.theme.InkMuted
import com.propiq.field.ui.theme.InkSecondary
import com.propiq.field.ui.theme.NavyInk
import com.propiq.field.ui.theme.RiskHigh
import com.propiq.field.ui.theme.RiskLow
import com.propiq.field.ui.theme.RiskMedium
import com.propiq.field.ui.theme.TealPrimary
import kotlinx.coroutines.launch
import java.io.File

private val PROP_TYPES = listOf(
    "1bhk_apartment", "2bhk_apartment", "3bhk_apartment", "4bhk_apartment",
    "villa", "shop", "office", "plot", "warehouse", "factory",
)
private val OCCUPANCY = listOf("self_occupied", "rented", "vacant")

@Composable
fun CaptureScreen(
    viewModel: CaptureViewModel,
    onBack: () -> Unit,
    onResults: (String) -> Unit,
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val snackbar = remember { SnackbarHostState() }
    val context = LocalContext.current

    // GPS is captured on screen open, not on a button — the officer should never
    // have to think about it.
    val requestLocation = rememberPermissionFlow(Permissions.Location) { granted ->
        viewModel.captureLocation(granted)
    }
    LaunchedEffect(Unit) { requestLocation() }

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is CaptureEvent.NavigateToResults -> onResults(event.requestId)
                is CaptureEvent.Queued -> snackbar.showSnackbar(event.message)
                is CaptureEvent.Toast ->
                    Toast.makeText(context, event.message, Toast.LENGTH_SHORT).show()
            }
        }
    }

    LaunchedEffect(state.error) {
        state.error?.let {
            snackbar.showSnackbar(it)
            viewModel.clearError()
        }
    }

    if (state.stage == CaptureStage.CAMERA) {
        CameraStage(viewModel = viewModel, state = state)
        return
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbar) },
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding)) {
            CaptureTopBar(onBack = onBack, demoMode = state.demoMode)

            if (!state.isOnline) OfflineBanner(queued = 0)

            if (state.stage == CaptureStage.SUBMITTING) {
                ResultsSkeleton(
                    statusLine = state.submitStatus.ifBlank { "Running assessment…" }
                )
                return@Column
            }

            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                item { LocationCard(state = state, onRetry = { requestLocation() }) }
                item { VoiceCard(state = state, viewModel = viewModel) }
                item { PhotoCard(state = state, viewModel = viewModel) }
                item { PropertyFormCard(state = state, viewModel = viewModel) }
                item { SubmitBlock(state = state, viewModel = viewModel) }
            }
        }
    }
}

@Composable
private fun CaptureTopBar(onBack: () -> Unit, demoMode: Boolean) {
    Surface(color = NavyInk) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onBack) {
                Icon(
                    Icons.AutoMirrored.Filled.ArrowBack,
                    contentDescription = "Back",
                    tint = Color.White,
                )
            }
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    "New assessment",
                    style = MaterialTheme.typography.titleMedium,
                    color = Color.White,
                )
                Text(
                    "Capture the property you're standing in",
                    style = MaterialTheme.typography.bodySmall,
                    color = TealPrimary,
                )
            }
            if (demoMode) {
                Pill("DEMO", fg = NavyInk, bg = TealPrimary, modifier = Modifier.padding(end = 12.dp))
            }
        }
    }
}

@Composable
private fun LocationCard(state: CaptureUiState, onRetry: () -> Unit) {
    SectionCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                Icons.Default.LocationOn,
                contentDescription = null,
                tint = if (state.geoFix != null) RiskLow else InkMuted,
                modifier = Modifier.size(18.dp),
            )
            Spacer(Modifier.width(8.dp))
            SectionLabel("Site location", Modifier.weight(1f))
            if (state.locating) {
                CircularProgressIndicator(modifier = Modifier.size(14.dp), strokeWidth = 2.dp)
            }
        }
        Spacer(Modifier.height(8.dp))
        when {
            state.geoFix != null -> {
                Text(
                    state.geoFix.areaName ?: "Coordinates captured",
                    style = MaterialTheme.typography.titleMedium,
                )
                Text(
                    "${state.geoFix.display} · ${state.geoFix.accuracyLabel}",
                    style = MaterialTheme.typography.bodySmall,
                    color = InkSecondary,
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    "Sent with the assessment so the server skips geocoding.",
                    style = MaterialTheme.typography.bodySmall,
                    color = InkMuted,
                )
            }
            state.locating -> Text(
                "Getting a GPS fix…",
                style = MaterialTheme.typography.bodyMedium,
                color = InkSecondary,
            )
            state.locationDenied -> {
                Text(
                    "Location is off — the valuation will use the locality centroid instead.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = InkSecondary,
                )
                TextButton(onClick = onRetry) { Text("Enable location") }
            }
            else -> {
                Text(
                    "No fix yet.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = InkSecondary,
                )
                TextButton(onClick = onRetry) { Text("Retry") }
            }
        }
    }
}

@Composable
private fun VoiceCard(state: CaptureUiState, viewModel: CaptureViewModel) {
    val requestMic = rememberPermissionFlow(Permissions.Microphone) { granted ->
        viewModel.startVoice(granted)
    }
    SectionCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                Icons.Default.Mic,
                contentDescription = null,
                tint = if (state.voiceActive) RiskHigh else InkMuted,
                modifier = Modifier.size(18.dp),
            )
            Spacer(Modifier.width(8.dp))
            SectionLabel("Describe it out loud", Modifier.weight(1f))
            when (val llm = state.llmState) {
                is LlmState.Ready -> Pill("LLM ON-DEVICE", severity = "low")
                LlmState.Loading -> Pill("LOADING MODEL", severity = "medium")
                else -> if (state.voiceOnDevice) Pill("SPEECH ON-DEVICE", severity = "low")
            }
        }
        Spacer(Modifier.height(10.dp))

        // Language matters here: a Pune officer dictates in Marathi as often as
        // English, and picking the wrong locale wrecks locality recognition.
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            VoiceLanguage.entries.forEach { lang ->
                FilterChip(
                    selected = state.voiceLanguage == lang,
                    onClick = { viewModel.setVoiceLanguage(lang) },
                    label = { Text(lang.nativeLabel) },
                    enabled = !state.voiceActive,
                )
            }
        }
        Spacer(Modifier.height(10.dp))
        Text(
            "\"Three BHK apartment in Baner, fourteen fifty square feet, eight years old, " +
                "seventh floor\"",
            style = MaterialTheme.typography.bodySmall,
            color = InkMuted,
        )
        Spacer(Modifier.height(12.dp))

        if (state.voiceActive) {
            LinearProgressIndicator(
                progress = { state.voiceAmplitude },
                modifier = Modifier.fillMaxWidth().height(6.dp),
                color = RiskHigh,
                trackColor = InkMuted.copy(alpha = 0.12f),
            )
            Spacer(Modifier.height(10.dp))
            Text(
                state.voicePartial.ifBlank { "Listening…" },
                style = MaterialTheme.typography.bodyMedium,
            )
            Spacer(Modifier.height(10.dp))
            Button(
                onClick = viewModel::stopVoice,
                colors = ButtonDefaults.buttonColors(containerColor = RiskHigh),
            ) {
                Icon(Icons.Default.Stop, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(8.dp))
                Text("Stop")
            }
        } else {
            OutlinedTextField(
                value = state.voiceTranscript,
                onValueChange = viewModel::setTranscript,
                label = { Text("Transcript (editable)") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 2,
            )
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Button(onClick = { requestMic() }) {
                    Icon(Icons.Default.Mic, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Speak")
                }
                if (state.voiceTranscript.isNotBlank()) {
                    TextButton(
                        onClick = { viewModel.interpret() },
                        enabled = !state.voiceParsing,
                    ) {
                        if (state.voiceParsing) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(14.dp),
                                strokeWidth = 2.dp,
                            )
                            Spacer(Modifier.width(8.dp))
                        } else {
                            Icon(
                                Icons.Default.AutoAwesome,
                                contentDescription = null,
                                modifier = Modifier.size(18.dp),
                            )
                            Spacer(Modifier.width(8.dp))
                        }
                        Text("Fill the form")
                    }
                }
            }
        }

        state.voiceStatus?.let {
            Spacer(Modifier.height(10.dp))
            Text(it, style = MaterialTheme.typography.bodySmall, color = InkSecondary)
        }

        state.lastParsedBy?.let { source ->
            Spacer(Modifier.height(8.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    Icons.Default.Memory,
                    contentDescription = null,
                    tint = if (source == ParseSource.ON_DEVICE) TealPrimary else InkMuted,
                    modifier = Modifier.size(14.dp),
                )
                Spacer(Modifier.width(6.dp))
                Text(
                    source.label,
                    style = MaterialTheme.typography.labelSmall,
                    color = if (source == ParseSource.ON_DEVICE) TealPrimary else InkMuted,
                )
            }
        }

        // Honest about what is not available, rather than silently degrading.
        (state.llmState as? LlmState.Unavailable)?.let {
            Spacer(Modifier.height(6.dp))
            Text(
                it.reason,
                style = MaterialTheme.typography.labelSmall,
                color = InkMuted,
            )
        }
    }
}

@Composable
private fun PhotoCard(state: CaptureUiState, viewModel: CaptureViewModel) {
    val requestCamera = rememberPermissionFlow(Permissions.Camera) { granted ->
        if (granted) viewModel.openCamera()
        else viewModel.reportCameraError(Permissions.Camera.deniedMessage)
    }
    SectionCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            SectionLabel("Property photos", Modifier.weight(1f))
            Text(
                "${state.frames.size}/${CaptureViewModel.MAX_FRAMES}",
                style = MaterialTheme.typography.labelLarge,
                color = if (state.frames.isEmpty()) RiskMedium else RiskLow,
            )
        }
        Spacer(Modifier.height(6.dp))
        Text(
            "Live camera only. Each frame is screened on-device before upload. " +
                "Exterior and interior are weighted 60/40 by the valuation engine.",
            style = MaterialTheme.typography.bodySmall,
            color = InkMuted,
        )
        Spacer(Modifier.height(12.dp))

        if (state.frames.isNotEmpty()) {
            LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                items(state.frames.size) { index ->
                    val frame = state.frames[index]
                    Box {
                        Column {
                            AsyncImage(
                                model = File(frame.path),
                                contentDescription = frame.tag,
                                contentScale = ContentScale.Crop,
                                modifier = Modifier
                                    .size(96.dp)
                                    .clip(RoundedCornerShape(10.dp)),
                            )
                            Spacer(Modifier.height(4.dp))
                            Text(
                                "${frame.tag} · Q${frame.verdict.qualityScore}",
                                style = MaterialTheme.typography.labelSmall,
                                color = InkMuted,
                            )
                        }
                        Box(
                            modifier = Modifier
                                .align(Alignment.TopEnd)
                                .padding(4.dp)
                                .size(22.dp)
                                .background(Color.Black.copy(alpha = 0.6f), RoundedCornerShape(11.dp))
                                .clickable { viewModel.removeFrame(frame.path) },
                            contentAlignment = Alignment.Center,
                        ) {
                            Icon(
                                Icons.Default.Close,
                                contentDescription = "Remove",
                                tint = Color.White,
                                modifier = Modifier.size(14.dp),
                            )
                        }
                    }
                }
            }
            Spacer(Modifier.height(12.dp))
        }

        Button(
            onClick = { requestCamera() },
            modifier = Modifier.fillMaxWidth().height(50.dp),
            enabled = state.frames.size < CaptureViewModel.MAX_FRAMES,
            colors = ButtonDefaults.buttonColors(containerColor = NavyInk),
        ) {
            Icon(Icons.Default.CameraAlt, contentDescription = null)
            Spacer(Modifier.width(10.dp))
            Text(if (state.frames.isEmpty()) "Open camera" else "Capture another")
        }

        state.cameraError?.let {
            Spacer(Modifier.height(10.dp))
            Text(it, style = MaterialTheme.typography.bodySmall, color = RiskHigh)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun PropertyFormCard(state: CaptureUiState, viewModel: CaptureViewModel) {
    val draft = state.draft
    SectionCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            SectionLabel("Property details", Modifier.weight(1f))
            TextButton(onClick = viewModel::loadSampleProperty) { Text("Use sample") }
        }
        Spacer(Modifier.height(10.dp))

        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            OutlinedTextField(
                value = draft.loanRef,
                onValueChange = { v -> viewModel.updateDraft { it.copy(loanRef = v) } },
                label = { Text("Loan file ref") },
                placeholder = { Text("LAP-2026-…") },
                singleLine = true,
                modifier = Modifier.weight(1f),
            )
            OutlinedTextField(
                value = draft.borrowerName,
                onValueChange = { v -> viewModel.updateDraft { it.copy(borrowerName = v) } },
                label = { Text("Borrower") },
                singleLine = true,
                modifier = Modifier.weight(1f),
            )
        }
        Spacer(Modifier.height(10.dp))

        DropdownField(
            label = "City",
            value = draft.city,
            options = Localities.cities,
            onSelect = { city ->
                viewModel.updateDraft { it.copy(city = city, locality = "") }
            },
        )
        Spacer(Modifier.height(10.dp))

        DropdownField(
            label = "Locality",
            value = draft.locality.ifBlank { "Select locality" },
            options = Localities.forCity(draft.city).map { it.name },
            onSelect = { loc -> viewModel.updateDraft { it.copy(locality = loc) } },
        )
        Spacer(Modifier.height(10.dp))

        DropdownField(
            label = "Property type",
            value = draft.propType,
            options = PROP_TYPES,
            onSelect = { t -> viewModel.updateDraft { it.copy(propType = t) } },
        )
        Spacer(Modifier.height(10.dp))

        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            OutlinedTextField(
                value = draft.sizeSqft,
                onValueChange = { v -> viewModel.updateDraft { it.copy(sizeSqft = v) } },
                label = { Text("Size (sqft)") },
                isError = draft.sizeError != null,
                supportingText = draft.sizeError?.let { { Text(it) } },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                singleLine = true,
                modifier = Modifier.weight(1f),
            )
            OutlinedTextField(
                value = draft.ageYears,
                onValueChange = { v -> viewModel.updateDraft { it.copy(ageYears = v) } },
                label = { Text("Age (yrs)") },
                isError = draft.ageError != null,
                supportingText = draft.ageError?.let { { Text(it) } },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                singleLine = true,
                modifier = Modifier.weight(1f),
            )
        }
        Spacer(Modifier.height(10.dp))

        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            OutlinedTextField(
                value = draft.floorNum,
                onValueChange = { v -> viewModel.updateDraft { it.copy(floorNum = v) } },
                label = { Text("Floor") },
                isError = draft.floorError != null,
                supportingText = draft.floorError?.let { { Text(it) } },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                singleLine = true,
                modifier = Modifier.weight(1f),
            )
            OutlinedTextField(
                value = draft.rentalYieldPct,
                onValueChange = { v -> viewModel.updateDraft { it.copy(rentalYieldPct = v) } },
                label = { Text("Rental yield %") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                singleLine = true,
                modifier = Modifier.weight(1f),
            )
        }
        Spacer(Modifier.height(10.dp))

        DropdownField(
            label = "Occupancy",
            value = draft.occupancy,
            options = OCCUPANCY,
            onSelect = { o -> viewModel.updateDraft { it.copy(occupancy = o) } },
        )
        Spacer(Modifier.height(14.dp))

        ToggleRow("Freehold", draft.isFreehold) { v ->
            viewModel.updateDraft { it.copy(isFreehold = v) }
        }
        ToggleRow("RERA registered", draft.isReraRegistered) { v ->
            viewModel.updateDraft { it.copy(isReraRegistered = v) }
        }
        ToggleRow("Clear title", draft.hasClearTitle) { v ->
            viewModel.updateDraft { it.copy(hasClearTitle = v) }
        }
        ToggleRow("Zoning approved", draft.zoningApproved) { v ->
            viewModel.updateDraft { it.copy(zoningApproved = v) }
        }
        ToggleRow("Encumbrance present", draft.hasEncumbrance) { v ->
            viewModel.updateDraft { it.copy(hasEncumbrance = v) }
        }
        ToggleRow("Legal dispute", draft.hasLegalDispute) { v ->
            viewModel.updateDraft { it.copy(hasLegalDispute = v) }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun DropdownField(
    label: String,
    value: String,
    options: List<String>,
    onSelect: (String) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    ExposedDropdownMenuBox(
        expanded = expanded,
        onExpandedChange = { expanded = it },
    ) {
        OutlinedTextField(
            value = value,
            onValueChange = {},
            readOnly = true,
            label = { Text(label) },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
            modifier = Modifier
                .fillMaxWidth()
                .menuAnchor(androidx.compose.material3.MenuAnchorType.PrimaryNotEditable),
        )
        ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            options.forEach { option ->
                DropdownMenuItem(
                    text = { Text(option) },
                    onClick = {
                        onSelect(option)
                        expanded = false
                    },
                )
            }
        }
    }
}

@Composable
private fun ToggleRow(label: String, checked: Boolean, onChange: (Boolean) -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 2.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(label, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
        Switch(checked = checked, onCheckedChange = onChange)
    }
}

@Composable
private fun SubmitBlock(state: CaptureUiState, viewModel: CaptureViewModel) {
    Column {
        Button(
            onClick = { viewModel.submit() },
            enabled = state.canSubmit || (state.demoMode && state.draft.isComplete),
            modifier = Modifier.fillMaxWidth().height(56.dp),
            shape = RoundedCornerShape(14.dp),
            colors = ButtonDefaults.buttonColors(containerColor = TealPrimary),
        ) {
            Text(
                if (state.isOnline || state.demoMode) "Run valuation"
                else "Save offline & queue",
                style = MaterialTheme.typography.titleMedium,
                color = NavyInk,
                fontWeight = FontWeight.Bold,
            )
        }
        if (state.demoMode) {
            Spacer(Modifier.height(8.dp))
            TextButton(
                onClick = { viewModel.submit(forceFraudDemo = true) },
                modifier = Modifier.fillMaxWidth(),
            ) { Text("Run the fraud-detection scenario") }
        }
        if (!state.draft.isComplete) {
            Spacer(Modifier.height(8.dp))
            Text(
                "Locality, size, age and floor are required.",
                style = MaterialTheme.typography.bodySmall,
                color = InkMuted,
            )
        }
    }
}

// ── Camera stage ──────────────────────────────────────────────────────────

@Composable
private fun CameraStage(viewModel: CaptureViewModel, state: CaptureUiState) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val scope = rememberCoroutineScope()
    val controller = remember { CameraController(context) }
    var bindError by remember { mutableStateOf<String?>(null) }
    var capturing by remember { mutableStateOf(false) }

    DisposableEffect(Unit) {
        onDispose { controller.release() }
    }

    if (bindError != null) {
        ErrorState(
            title = "Camera unavailable",
            message = bindError!!,
            primaryLabel = "Try again",
            onPrimary = { bindError = null },
            secondaryLabel = "Back to form",
            onSecondary = viewModel::closeCamera,
            modifier = Modifier.fillMaxSize(),
        )
        return
    }

    Box(modifier = Modifier.fillMaxSize().background(Color.Black)) {
        AndroidView(
            factory = { ctx ->
                PreviewView(ctx).also { view ->
                    view.scaleType = PreviewView.ScaleType.FILL_CENTER
                    scope.launch {
                        controller.bind(lifecycleOwner, view)
                            .onFailure {
                                bindError = it.message
                                    ?: "The camera could not be started on this device."
                            }
                    }
                }
            },
            modifier = Modifier.fillMaxSize(),
        )

        // Top: tag selector
        Row(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = viewModel::closeCamera) {
                Icon(Icons.Default.Close, contentDescription = "Close", tint = Color.White)
            }
            Spacer(Modifier.width(8.dp))
            listOf("exterior", "interior").forEach { tag ->
                FilterChip(
                    selected = state.activeTag == tag,
                    onClick = { viewModel.setActiveTag(tag) },
                    label = { Text(tag.replaceFirstChar { it.uppercase() }) },
                    modifier = Modifier.padding(end = 8.dp),
                )
            }
        }

        // Bottom: verdict + shutter
        Column(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .padding(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            state.lastVerdict?.let { verdict ->
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = if (verdict.reason.isBlocking) RiskHigh else Color.Black.copy(alpha = 0.72f),
                    modifier = Modifier.fillMaxWidth().padding(bottom = 14.dp),
                ) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                Icons.Default.Memory,
                                contentDescription = null,
                                tint = if (verdict.reason == PhotoReason.OK) TealPrimary else Color.White,
                                modifier = Modifier.size(16.dp),
                            )
                            Spacer(Modifier.width(8.dp))
                            Text(
                                "ON-DEVICE PRE-CHECK",
                                style = MaterialTheme.typography.labelSmall,
                                color = Color.White.copy(alpha = 0.75f),
                                modifier = Modifier.weight(1f),
                            )
                            Text(
                                "Q${verdict.qualityScore}",
                                style = MaterialTheme.typography.labelLarge,
                                color = Color.White,
                            )
                        }
                        Spacer(Modifier.height(6.dp))
                        Text(
                            verdict.headline,
                            style = MaterialTheme.typography.titleMedium,
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                        )
                        Spacer(Modifier.height(3.dp))
                        Text(
                            verdict.detail,
                            style = MaterialTheme.typography.bodySmall,
                            color = Color.White.copy(alpha = 0.85f),
                        )
                        if (verdict.reason.isBlocking) {
                            Spacer(Modifier.height(8.dp))
                            TextButton(onClick = viewModel::dismissVerdict) {
                                Text("Retake", color = Color.White)
                            }
                        }
                    }
                }
            }

            if (state.analyzing) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(16.dp),
                        strokeWidth = 2.dp,
                        color = TealPrimary,
                    )
                    Spacer(Modifier.width(10.dp))
                    Text(
                        "Screening on-device…",
                        style = MaterialTheme.typography.bodySmall,
                        color = Color.White,
                    )
                }
                Spacer(Modifier.height(12.dp))
            }

            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(72.dp)
                        .clip(RoundedCornerShape(36.dp))
                        .background(if (capturing) InkMuted else Color.White)
                        .clickable(enabled = !capturing && !state.analyzing) {
                            capturing = true
                            scope.launch {
                                controller.capture(File(context.cacheDir, "captures"))
                                    .onSuccess { viewModel.onPhotoCaptured(it) }
                                    .onFailure {
                                        viewModel.reportCameraError(
                                            it.message ?: "The photo could not be saved."
                                        )
                                    }
                                capturing = false
                            }
                        },
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        Icons.Default.CameraAlt,
                        contentDescription = "Capture",
                        tint = NavyInk,
                        modifier = Modifier.size(28.dp),
                    )
                }
                Spacer(Modifier.width(20.dp))
                if (state.frames.isNotEmpty()) {
                    Button(
                        onClick = viewModel::closeCamera,
                        colors = ButtonDefaults.buttonColors(containerColor = TealPrimary),
                    ) {
                        Text(
                            "Done (${state.frames.size})",
                            color = NavyInk,
                            fontWeight = FontWeight.Bold,
                        )
                    }
                }
            }
        }
    }
}
