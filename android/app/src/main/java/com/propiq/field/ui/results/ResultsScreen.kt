package com.propiq.field.ui.results

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.GppMaybe
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import kotlin.math.abs
import com.propiq.field.core.Fmt
import com.propiq.field.core.Money
import com.propiq.field.data.remote.AssessmentResponse
import com.propiq.field.data.remote.RiskFlag
import com.propiq.field.ui.components.ErrorState
import com.propiq.field.ui.components.MetricTile
import com.propiq.field.ui.components.Pill
import com.propiq.field.ui.components.ResultsSkeleton
import com.propiq.field.ui.components.SectionCard
import com.propiq.field.ui.components.SectionLabel
import com.propiq.field.ui.theme.InkMuted
import com.propiq.field.ui.theme.InkSecondary
import com.propiq.field.ui.theme.NavyInk
import com.propiq.field.ui.theme.RiskHigh
import com.propiq.field.ui.theme.RiskHighWash
import com.propiq.field.ui.theme.RiskLow
import com.propiq.field.ui.theme.RiskMedium
import com.propiq.field.ui.theme.TealPrimary
import com.propiq.field.ui.theme.ZoneAmber
import com.propiq.field.ui.theme.ZoneGreen
import com.propiq.field.ui.theme.ZoneRed

@Composable
fun ResultsScreen(
    requestId: String,
    viewModel: ResultsViewModel,
    onBack: () -> Unit,
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val snackbar = remember { SnackbarHostState() }

    LaunchedEffect(requestId) { viewModel.load(requestId) }

    LaunchedEffect(state.exportMessage) {
        state.exportMessage?.let {
            snackbar.showSnackbar(it)
            viewModel.clearExportMessage()
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbar) },
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding)) {
            ResultsTopBar(
                subtitle = state.result?.requestId ?: requestId,
                isDemo = state.wasDemo,
                onBack = onBack,
            )

            when {
                state.loading -> ResultsSkeleton("Loading assessment…")
                state.notFound || state.result == null -> ErrorState(
                    title = "Assessment not found",
                    message = "This result is no longer stored on the device.",
                    primaryLabel = "Back to home",
                    onPrimary = onBack,
                )
                else -> ResultsBody(
                    result = state.result!!,
                    exporting = state.exporting,
                    onExport = viewModel::export,
                )
            }
        }
    }
}

@Composable
private fun ResultsTopBar(subtitle: String, isDemo: Boolean, onBack: () -> Unit) {
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
                    "Assessment",
                    style = MaterialTheme.typography.titleMedium,
                    color = Color.White,
                )
                Text(
                    subtitle,
                    style = MaterialTheme.typography.bodySmall,
                    color = TealPrimary,
                )
            }
            if (isDemo) {
                Pill("DEMO", fg = NavyInk, bg = TealPrimary, modifier = Modifier.padding(end = 12.dp))
            }
        }
    }
}

@Composable
private fun ResultsBody(
    result: AssessmentResponse,
    exporting: Boolean,
    onExport: () -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        // 1. The number. Nothing above it.
        item { HeroValue(result) }

        // 2. Fraud, if any — deliberately second, before the routine metrics.
        result.fraudAlert?.let { flag ->
            item { FraudBanner(flag) }
        }

        // 3. The three numbers a credit officer actually decides on.
        item { KeyMetrics(result) }

        item { LtvPanel(result) }

        item { RiskPanel(result) }

        result.cvAssessment?.let { item { VisualConditionPanel(result) } }

        item { DriversPanel(result) }

        item { ProvenancePanel(result) }

        item {
            Button(
                onClick = onExport,
                enabled = !exporting,
                modifier = Modifier.fillMaxWidth().height(52.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(containerColor = NavyInk),
            ) {
                if (exporting) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(18.dp),
                        strokeWidth = 2.dp,
                        color = Color.White,
                    )
                } else {
                    Icon(Icons.Default.Download, contentDescription = null)
                }
                Spacer(Modifier.width(10.dp))
                Text(if (exporting) "Exporting…" else "Export assessment (PDF + JSON)")
            }
        }
        item {
            Text(
                "Saves to the device's Downloads folder — ready to pull across to a laptop.",
                style = MaterialTheme.typography.bodySmall,
                color = InkMuted,
                modifier = Modifier.fillMaxWidth(),
            )
        }
    }
}

/**
 * The 3-second read: one enormous number, its band, and the confidence. A jury
 * watching a 3-minute pitch should not have to hunt for the valuation.
 */
@Composable
private fun HeroValue(result: AssessmentResponse) {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = NavyInk,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                "ASSESSED MARKET VALUE",
                style = MaterialTheme.typography.labelSmall,
                color = TealPrimary,
            )
            Spacer(Modifier.height(8.dp))
            Text(
                Money.compact(result.marketValueMid),
                style = MaterialTheme.typography.displayLarge,
                color = Color.White,
            )
            Spacer(Modifier.height(4.dp))
            Text(
                Money.full(result.marketValueMid),
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.6f),
            )
            Spacer(Modifier.height(14.dp))
            Text(
                "Range ${Money.range(result.marketValueRange)}  ·  ${Money.full(result.pricePerSqft)}/sqft",
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.85f),
            )
            Spacer(Modifier.height(12.dp))

            val confidence = ((result.confidenceScore ?: 0.0) * 100).toInt()
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    "Confidence $confidence%",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.White.copy(alpha = 0.7f),
                )
                Spacer(Modifier.width(10.dp))
                LinearProgressIndicator(
                    progress = { (result.confidenceScore ?: 0.0).toFloat().coerceIn(0f, 1f) },
                    modifier = Modifier.weight(1f).height(5.dp),
                    color = TealPrimary,
                    trackColor = Color.White.copy(alpha = 0.15f),
                )
            }
            Spacer(Modifier.height(12.dp))
            Text(
                "${Fmt.propType(result.propType)} · ${result.locality ?: "—"}, ${result.city ?: "—"} · " +
                    "${result.sizeSqft?.toInt() ?: "—"} sqft · ${result.ageYears?.toInt() ?: "—"} yrs",
                style = MaterialTheme.typography.bodySmall,
                color = Color.White.copy(alpha = 0.55f),
            )
        }
    }
}

/**
 * Fraud gets its own full-width red banner rather than a row in the flag list.
 * This is the novelty claim — a VLM catching "claimed apartment, photo shows a
 * warehouse" — so it is impossible to miss on a phone screen.
 */
@Composable
private fun FraudBanner(flag: RiskFlag) {
    Surface(
        shape = RoundedCornerShape(14.dp),
        color = RiskHighWash,
        border = androidx.compose.foundation.BorderStroke(1.5.dp, RiskHigh),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(34.dp)
                        .background(RiskHigh, RoundedCornerShape(9.dp)),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        Icons.Default.GppMaybe,
                        contentDescription = null,
                        tint = Color.White,
                        modifier = Modifier.size(20.dp),
                    )
                }
                Spacer(Modifier.width(12.dp))
                Column {
                    Text(
                        "COLLATERAL FRAUD SIGNAL",
                        style = MaterialTheme.typography.labelSmall,
                        color = RiskHigh,
                    )
                    Text(
                        Fmt.flagLabel(flag.flag),
                        style = MaterialTheme.typography.titleMedium,
                        color = RiskHigh,
                        fontWeight = FontWeight.Bold,
                    )
                }
            }
            Spacer(Modifier.height(10.dp))
            Text(
                flag.detail ?: "The visual evidence contradicts the declared property.",
                style = MaterialTheme.typography.bodyMedium,
                color = RiskHigh,
            )
            Spacer(Modifier.height(10.dp))
            Text(
                "Caught by the vision model during this assessment — before disbursal, " +
                    "not during recovery.",
                style = MaterialTheme.typography.bodySmall,
                color = RiskHigh.copy(alpha = 0.75f),
            )
        }
    }
}

@Composable
private fun KeyMetrics(result: AssessmentResponse) {
    val rpi = result.resalePotentialIndex ?: 0.0
    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        MetricTile(
            label = "Resale Potential",
            value = String.format("%.1f", rpi),
            valueColor = when {
                rpi >= 70 -> RiskLow
                rpi >= 45 -> RiskMedium
                else -> RiskHigh
            },
            caption = "index / 100",
            modifier = Modifier.weight(1f),
        )
        MetricTile(
            label = "Time to sell",
            value = result.resolvedTimeToSell?.let { "${it[0]}-${it[1]}" } ?: "—",
            caption = "days",
            modifier = Modifier.weight(1f),
        )
        MetricTile(
            label = "Distress 90d",
            value = Money.compact(result.distressValue90d ?: result.distressValueRange?.firstOrNull()),
            caption = "forced sale",
            modifier = Modifier.weight(1f),
        )
    }
}

@Composable
private fun LtvPanel(result: AssessmentResponse) {
    val ltv = result.ltvAnalysis ?: return
    val zoneColor = when (ltv.ltvZone?.lowercase()) {
        "green" -> ZoneGreen
        "amber" -> ZoneAmber
        "red" -> ZoneRed
        else -> InkSecondary
    }
    SectionCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            SectionLabel("Recommended LTV", Modifier.weight(1f))
            Pill(
                (ltv.ltvZone ?: "—").uppercase(),
                fg = Color.White,
                bg = zoneColor,
            )
        }
        Spacer(Modifier.height(10.dp))
        Row(verticalAlignment = Alignment.Bottom) {
            Text(
                "${ltv.recommendedLtvPct ?: "—"}%",
                style = MaterialTheme.typography.headlineMedium,
                color = zoneColor,
                fontWeight = FontWeight.Bold,
            )
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.padding(bottom = 3.dp)) {
                Text(
                    "Max loan ${Money.compact(ltv.maxLoanAmount)}",
                    style = MaterialTheme.typography.titleMedium,
                )
                Text(
                    "RBI ceiling ${ltv.rbiMaxLtvPct ?: "—"}%",
                    style = MaterialTheme.typography.bodySmall,
                    color = InkMuted,
                )
            }
        }
        ltv.pflRationale?.let {
            Spacer(Modifier.height(10.dp))
            Text(it, style = MaterialTheme.typography.bodySmall, color = InkSecondary)
        }
    }
}

@Composable
private fun RiskPanel(result: AssessmentResponse) {
    val flags = result.rankedFlags
    SectionCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            SectionLabel("Risk flags", Modifier.weight(1f))
            Text(
                "${flags.size}",
                style = MaterialTheme.typography.labelLarge,
                color = if (flags.isEmpty()) RiskLow else RiskHigh,
            )
        }
        Spacer(Modifier.height(10.dp))
        if (flags.isEmpty()) {
            Text(
                "No risk flags raised on this collateral.",
                style = MaterialTheme.typography.bodyMedium,
                color = InkSecondary,
            )
        } else {
            flags.take(4).forEachIndexed { index, flag ->
                if (index > 0) Spacer(Modifier.height(12.dp))
                Row(verticalAlignment = Alignment.Top) {
                    Pill(flag.severity?.uppercase() ?: "—", severity = flag.severity)
                    Spacer(Modifier.width(10.dp))
                    Column {
                        Text(
                            Fmt.flagLabel(flag.flag),
                            style = MaterialTheme.typography.titleMedium,
                        )
                        flag.detail?.let {
                            Spacer(Modifier.height(2.dp))
                            Text(
                                it,
                                style = MaterialTheme.typography.bodySmall,
                                color = InkSecondary,
                            )
                        }
                    }
                }
            }
            if (flags.size > 4) {
                Spacer(Modifier.height(10.dp))
                Text(
                    "+${flags.size - 4} more in the exported report",
                    style = MaterialTheme.typography.bodySmall,
                    color = InkMuted,
                )
            }
        }
    }
}

@Composable
private fun VisualConditionPanel(result: AssessmentResponse) {
    val cv = result.cvAssessment ?: return
    SectionCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                Icons.Default.Visibility,
                contentDescription = null,
                tint = InkMuted,
                modifier = Modifier.size(16.dp),
            )
            Spacer(Modifier.width(8.dp))
            SectionLabel("Visual condition (cloud VLM)", Modifier.weight(1f))
            Pill(
                cv.condition?.uppercase() ?: "—",
                severity = when (cv.condition?.lowercase()) {
                    "poor" -> "high"
                    "fair" -> "medium"
                    else -> "low"
                },
            )
        }
        Spacer(Modifier.height(10.dp))
        Text(
            "${cv.imagesCount ?: 0} image(s) analysed · ${cv.exteriorCount ?: 0} exterior, " +
                "${cv.interiorCount ?: 0} interior · quality ${cv.qualityScore ?: "—"}/100",
            style = MaterialTheme.typography.bodySmall,
            color = InkSecondary,
        )
        cv.adjustmentDescription?.let {
            Spacer(Modifier.height(6.dp))
            Text(
                it,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Medium,
            )
        }
        cv.perImage?.forEach { img ->
            img.vlmAnalysis?.description?.let { desc ->
                Spacer(Modifier.height(12.dp))
                Text(
                    "[${img.tag?.uppercase() ?: "IMAGE"}]",
                    style = MaterialTheme.typography.labelSmall,
                    color = InkMuted,
                )
                Spacer(Modifier.height(3.dp))
                Text(desc, style = MaterialTheme.typography.bodySmall, color = InkSecondary)
            }
        }
    }
}

@Composable
private fun DriversPanel(result: AssessmentResponse) {
    val drivers = result.keyDrivers?.take(5).orEmpty()
    if (drivers.isEmpty()) return
    SectionCard {
        SectionLabel("What moved the valuation (SHAP)")
        Spacer(Modifier.height(12.dp))
        val maxImpact = drivers.maxOfOrNull { abs(it.impactInr ?: 0L) } ?: 1L
        drivers.forEachIndexed { index, d ->
            if (index > 0) Spacer(Modifier.height(10.dp))
            val positive = (d.impactInr ?: 0L) >= 0
            Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        Fmt.flagLabel(d.feature),
                        style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.weight(1f),
                    )
                    Text(
                        (if (positive) "+" else "−") + Money.compact(abs(d.impactInr ?: 0L)),
                        style = MaterialTheme.typography.labelLarge,
                        color = if (positive) RiskLow else RiskHigh,
                    )
                }
                Spacer(Modifier.height(4.dp))
                LinearProgressIndicator(
                    progress = {
                        (abs(d.impactInr ?: 0L).toFloat() / maxImpact.toFloat())
                            .coerceIn(0f, 1f)
                    },
                    modifier = Modifier.fillMaxWidth().height(4.dp),
                    color = if (positive) RiskLow else RiskHigh,
                    trackColor = InkMuted.copy(alpha = 0.12f),
                )
            }
        }
    }
}

@Composable
private fun ProvenancePanel(result: AssessmentResponse) {
    SectionCard {
        SectionLabel("Model provenance")
        Spacer(Modifier.height(10.dp))
        val rows = listOfNotNull(
            "Request ID" to (result.requestId ?: "—"),
            "Validation MAPE" to "${result.resolvedMape}%",
            "Server time" to "${result.processingTimeMs ?: "—"} ms",
            result.enrichment?.zoneTier?.let { "Zone tier" to it },
            result.enrichment?.circleRatePerSqft?.let { "IGR circle rate" to "${Money.full(it)}/sqft" },
            result.enrichment?.infraScore?.let { "Infra score" to String.format("%.1f", it) },
        )
        rows.forEachIndexed { index, (k, v) ->
            if (index > 0) Spacer(Modifier.height(7.dp))
            Row {
                Text(
                    k,
                    style = MaterialTheme.typography.bodySmall,
                    color = InkMuted,
                    modifier = Modifier.weight(1f),
                )
                Text(v, style = MaterialTheme.typography.bodySmall)
            }
        }
        Spacer(Modifier.height(12.dp))
        Text(
            "AI-assisted estimate for underwriting triage. Not a substitute for a " +
                "registered valuer's certificate.",
            style = MaterialTheme.typography.bodySmall,
            color = InkMuted,
        )
    }
}
