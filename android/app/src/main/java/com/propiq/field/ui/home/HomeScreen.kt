package com.propiq.field.ui.home

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.CloudQueue
import androidx.compose.material.icons.filled.ErrorOutline
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.WarningAmber
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.propiq.field.core.Fmt
import com.propiq.field.core.Money
import com.propiq.field.data.local.QueuedAssessment
import com.propiq.field.ui.components.MetricTile
import com.propiq.field.ui.components.OfflineBanner
import com.propiq.field.ui.components.Pill
import com.propiq.field.ui.components.SectionCard
import com.propiq.field.ui.components.SectionLabel
import com.propiq.field.ui.theme.InkMuted
import com.propiq.field.ui.theme.InkSecondary
import com.propiq.field.ui.theme.NavyInk
import com.propiq.field.ui.theme.NavyLine
import com.propiq.field.ui.theme.RiskHigh
import com.propiq.field.ui.theme.RiskLow
import com.propiq.field.ui.theme.RiskMedium
import com.propiq.field.ui.theme.TealPrimary

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    viewModel: HomeViewModel,
    onStartCapture: () -> Unit,
    onOpenResult: (String) -> Unit,
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val snackbar = remember { SnackbarHostState() }
    var showSettings by remember { mutableStateOf(false) }
    var showQueue by remember { mutableStateOf(false) }
    val sheetState = rememberModalBottomSheetState()

    LaunchedEffect(state.message) {
        state.message?.let {
            snackbar.showSnackbar(it)
            viewModel.clearMessage()
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbar) },
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding)) {

            HomeHeader(
                demoMode = state.demoMode,
                onSettings = { showSettings = true },
            )

            if (!state.isOnline) {
                OfflineBanner(queued = state.pendingCount)
            }

            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                item { ValueProposition() }

                item {
                    Button(
                        onClick = onStartCapture,
                        modifier = Modifier.fillMaxWidth().height(58.dp),
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = NavyInk),
                    ) {
                        Icon(Icons.Default.CameraAlt, contentDescription = null)
                        Spacer(Modifier.width(10.dp))
                        Text(
                            "Start field assessment",
                            style = MaterialTheme.typography.titleMedium,
                        )
                    }
                }

                item {
                    StatusRow(
                        state = state,
                        onCheck = viewModel::checkBackend,
                        onQueueClick = { showQueue = true },
                    )
                }

                if (state.history.isNotEmpty()) {
                    item {
                        SectionLabel("Recent assessments", Modifier.padding(top = 6.dp))
                    }
                    items(state.history, key = { it.requestId }) { entry ->
                        HistoryRow(entry = entry, onClick = { onOpenResult(entry.requestId) })
                    }
                } else {
                    item { EmptyHistory() }
                }
            }
        }
    }

    if (showSettings) {
        ModalBottomSheet(
            onDismissRequest = { showSettings = false },
            sheetState = sheetState,
        ) {
            SettingsSheet(
                state = state,
                onBaseUrl = viewModel::updateBaseUrl,
                onApiKey = viewModel::updateApiKey,
                onDemoMode = viewModel::setDemoMode,
                onCheck = viewModel::checkBackend,
            )
        }
    }

    if (showQueue) {
        ModalBottomSheet(
            onDismissRequest = { showQueue = false },
            sheetState = sheetState,
        ) {
            QueueSheet(
                items = state.queued,
                onRetry = viewModel::retryQueueNow,
                onDiscard = viewModel::discardQueued,
            )
        }
    }
}

@Composable
private fun HomeHeader(demoMode: Boolean, onSettings: () -> Unit) {
    Surface(color = NavyInk) {
        Column(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        "PropIQ Field",
                        style = MaterialTheme.typography.titleLarge,
                        color = androidx.compose.ui.graphics.Color.White,
                        fontWeight = FontWeight.Bold,
                    )
                    Text(
                        "Collateral valuation, on site",
                        style = MaterialTheme.typography.bodySmall,
                        color = TealPrimary,
                    )
                }
                if (demoMode) {
                    Pill(
                        text = "DEMO MODE",
                        fg = NavyInk,
                        bg = TealPrimary,
                        modifier = Modifier.padding(end = 10.dp),
                    )
                }
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .clip(RoundedCornerShape(10.dp))
                        .background(androidx.compose.ui.graphics.Color.White.copy(alpha = 0.10f))
                        .clickable(onClick = onSettings),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        Icons.Default.Settings,
                        contentDescription = "Settings",
                        tint = androidx.compose.ui.graphics.Color.White,
                        modifier = Modifier.size(20.dp),
                    )
                }
            }
        }
    }
}

/**
 * The novelty framing, stated once, at the top. Judges see the "2-3 weeks to
 * under a minute" claim before they see any number.
 */
@Composable
private fun ValueProposition() {
    Surface(
        shape = RoundedCornerShape(14.dp),
        color = NavyInk,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    Icons.Default.Bolt,
                    contentDescription = null,
                    tint = TealPrimary,
                    modifier = Modifier.size(18.dp),
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    "LAP collateral valuation",
                    style = MaterialTheme.typography.labelSmall,
                    color = TealPrimary,
                )
            }
            Spacer(Modifier.height(10.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column {
                    Text(
                        "2-3 weeks",
                        style = MaterialTheme.typography.titleMedium,
                        color = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.55f),
                        textDecoration = androidx.compose.ui.text.style.TextDecoration.LineThrough,
                    )
                    Text(
                        "manual site visit + panel valuer",
                        style = MaterialTheme.typography.bodySmall,
                        color = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.45f),
                    )
                }
                Spacer(Modifier.width(16.dp))
                Text(
                    "→",
                    style = MaterialTheme.typography.titleLarge,
                    color = TealPrimary,
                )
                Spacer(Modifier.width(16.dp))
                Column {
                    Text(
                        "< 60 seconds",
                        style = MaterialTheme.typography.titleMedium,
                        color = TealPrimary,
                        fontWeight = FontWeight.Bold,
                    )
                    Text(
                        "on the officer's own phone",
                        style = MaterialTheme.typography.bodySmall,
                        color = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.7f),
                    )
                }
            }
        }
    }
}

@Composable
private fun StatusRow(
    state: HomeUiState,
    onCheck: () -> Unit,
    onQueueClick: () -> Unit,
) {
    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        val (statusText, statusColor) = when {
            state.checkingBackend -> "Checking…" to InkMuted
            state.demoMode -> "Demo" to TealPrimary
            state.backendStatus is BackendStatus.Reachable -> "Online" to RiskLow
            state.backendStatus is BackendStatus.Unreachable -> "Unreachable" to RiskHigh
            !state.isOnline -> "Offline" to RiskMedium
            else -> "Not checked" to InkMuted
        }
        MetricTile(
            label = "Backend",
            value = statusText,
            valueColor = statusColor,
            caption = "tap to test",
            modifier = Modifier.weight(1f).clickable(onClick = onCheck),
        )
        MetricTile(
            label = "Queued",
            value = state.pendingCount.toString(),
            valueColor = if (state.pendingCount > 0) RiskMedium else InkSecondary,
            caption = if (state.pendingCount > 0) "tap to review" else "all submitted",
            modifier = Modifier.weight(1f).clickable(onClick = onQueueClick),
        )
        MetricTile(
            label = "Completed",
            value = state.history.size.toString(),
            caption = "on this device",
            modifier = Modifier.weight(1f),
        )
    }
}

@Composable
private fun HistoryRow(
    entry: com.propiq.field.data.local.AssessmentHistory,
    onClick: () -> Unit,
) {
    SectionCard(modifier = Modifier.clickable(onClick = onClick)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        Money.compact(entry.marketValueMid),
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                    )
                    Spacer(Modifier.width(8.dp))
                    if (entry.hasFraudAlert) {
                        Pill("FRAUD FLAG", severity = "high")
                    } else if (entry.flagCount > 0) {
                        Pill("${entry.flagCount} flag${if (entry.flagCount == 1) "" else "s"}", severity = "medium")
                    }
                    if (entry.wasDemo) {
                        Spacer(Modifier.width(6.dp))
                        Pill("demo", fg = InkMuted, bg = MaterialTheme.colorScheme.surfaceVariant)
                    }
                }
                Spacer(Modifier.height(3.dp))
                Text(
                    "${Fmt.propType(entry.propType)} · ${entry.locality} · RPI ${entry.rpi}",
                    style = MaterialTheme.typography.bodySmall,
                    color = InkSecondary,
                )
                // The loan file is what makes a list of six site visits
                // navigable; without it every row looks the same.
                if (entry.loanRef.isNotBlank() || entry.borrowerName.isNotBlank()) {
                    Spacer(Modifier.height(2.dp))
                    Text(
                        listOf(entry.loanRef, entry.borrowerName)
                            .filter { it.isNotBlank() }
                            .joinToString(" · "),
                        style = MaterialTheme.typography.labelSmall,
                        color = InkMuted,
                    )
                }
            }
            Text(
                Fmt.relative(entry.createdAt),
                style = MaterialTheme.typography.bodySmall,
                color = InkMuted,
            )
        }
    }
}

@Composable
private fun EmptyHistory() {
    SectionCard {
        Text(
            "No assessments yet",
            style = MaterialTheme.typography.titleMedium,
        )
        Spacer(Modifier.height(6.dp))
        Text(
            "Stand in front of a property, capture it, and the valuation lands here. " +
                "Everything you complete is kept on the device.",
            style = MaterialTheme.typography.bodyMedium,
            color = InkSecondary,
        )
    }
}

// ── Sheets ────────────────────────────────────────────────────────────────

@Composable
private fun SettingsSheet(
    state: HomeUiState,
    onBaseUrl: (String) -> Unit,
    onApiKey: (String) -> Unit,
    onDemoMode: (Boolean) -> Unit,
    onCheck: () -> Unit,
) {
    var url by remember(state.baseUrl) { mutableStateOf(state.baseUrl) }
    var key by remember(state.apiKey) { mutableStateOf(state.apiKey) }

    Column(
        modifier = Modifier.fillMaxWidth().padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Text("Settings", style = MaterialTheme.typography.titleLarge)

        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(modifier = Modifier.weight(1f)) {
                Text("Demo Mode", style = MaterialTheme.typography.titleMedium)
                Text(
                    "Returns the pre-seeded sample property instantly. No network, " +
                        "no cold-start wait — use this on stage.",
                    style = MaterialTheme.typography.bodySmall,
                    color = InkSecondary,
                )
            }
            Switch(checked = state.demoMode, onCheckedChange = onDemoMode)
        }

        OutlinedTextField(
            value = url,
            onValueChange = { url = it },
            label = { Text("Backend base URL") },
            supportingText = {
                Text("10.0.2.2 is the emulator's route to your laptop's localhost. On a real phone use the LAN IP or the deployed URL.")
            },
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri),
            modifier = Modifier.fillMaxWidth(),
        )

        OutlinedTextField(
            value = key,
            onValueChange = { key = it },
            label = { Text("X-API-Key") },
            supportingText = { Text("Must match PROPIQ_API_KEYS on the server.") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )

        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Button(
                onClick = {
                    onBaseUrl(url)
                    onApiKey(key)
                    onCheck()
                },
                modifier = Modifier.weight(1f),
            ) { Text("Save & test") }
            TextButton(onClick = onCheck) {
                Icon(Icons.Default.Refresh, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(6.dp))
                Text("Test")
            }
        }

        when (val s = state.backendStatus) {
            is BackendStatus.Reachable -> StatusLine(
                icon = Icons.Default.CheckCircle,
                tint = RiskLow,
                text = "Backend reachable.",
            )
            is BackendStatus.Unreachable -> StatusLine(
                icon = Icons.Default.ErrorOutline,
                tint = RiskHigh,
                text = s.reason,
            )
            BackendStatus.Unknown -> Unit
        }

        Spacer(Modifier.height(8.dp))
    }
}

@Composable
private fun StatusLine(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    tint: androidx.compose.ui.graphics.Color,
    text: String,
) {
    Row(verticalAlignment = Alignment.Top) {
        Icon(icon, contentDescription = null, tint = tint, modifier = Modifier.size(18.dp))
        Spacer(Modifier.width(8.dp))
        Text(text, style = MaterialTheme.typography.bodySmall, color = InkSecondary)
    }
}

@Composable
private fun QueueSheet(
    items: List<QueuedAssessment>,
    onRetry: () -> Unit,
    onDiscard: (Long) -> Unit,
) {
    Column(
        modifier = Modifier.fillMaxWidth().padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(modifier = Modifier.weight(1f)) {
                Text("Offline queue", style = MaterialTheme.typography.titleLarge)
                Text(
                    "Assessments captured without a connection. These submit " +
                        "automatically when the device is back online.",
                    style = MaterialTheme.typography.bodySmall,
                    color = InkSecondary,
                )
            }
            TextButton(onClick = onRetry) { Text("Retry now") }
        }

        if (items.isEmpty()) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    Icons.Default.CloudQueue,
                    contentDescription = null,
                    tint = InkMuted,
                    modifier = Modifier.size(20.dp),
                )
                Spacer(Modifier.width(10.dp))
                Text(
                    "Nothing queued — everything has been submitted.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = InkSecondary,
                )
            }
        } else {
            items.forEach { item ->
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    border = BorderStroke(1.dp, NavyLine.copy(alpha = 0.2f)),
                    color = MaterialTheme.colorScheme.surface,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                "${Fmt.propType(item.propType)} · ${item.locality}",
                                style = MaterialTheme.typography.titleMedium,
                                modifier = Modifier.weight(1f),
                            )
                            when (item.status) {
                                QueuedAssessment.STATUS_FAILED_PERMANENT ->
                                    Pill("Failed", severity = "high")
                                QueuedAssessment.STATUS_SYNCING ->
                                    Pill("Sending", severity = "medium")
                                else -> Pill("Pending", severity = "medium")
                            }
                        }
                        Spacer(Modifier.height(4.dp))
                        Text(
                            "${item.sizeSqft.toInt()} sqft · captured ${Fmt.relative(item.createdAt)} · " +
                                "${item.photoPathList.size} photo(s) · attempt ${item.attemptCount}",
                            style = MaterialTheme.typography.bodySmall,
                            color = InkSecondary,
                        )
                        item.lastError?.takeIf { item.status == QueuedAssessment.STATUS_FAILED_PERMANENT }
                            ?.let {
                                Spacer(Modifier.height(6.dp))
                                Row(verticalAlignment = Alignment.Top) {
                                    Icon(
                                        Icons.Default.WarningAmber,
                                        contentDescription = null,
                                        tint = RiskHigh,
                                        modifier = Modifier.size(15.dp),
                                    )
                                    Spacer(Modifier.width(6.dp))
                                    Text(
                                        it.take(160),
                                        style = MaterialTheme.typography.bodySmall,
                                        color = RiskHigh,
                                    )
                                }
                                TextButton(onClick = { onDiscard(item.id) }) { Text("Discard") }
                            }
                    }
                }
            }
        }
        Spacer(Modifier.height(8.dp))
    }
}
