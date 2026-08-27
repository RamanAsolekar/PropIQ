package com.propiq.field.ui.components

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CloudOff
import androidx.compose.material.icons.filled.ErrorOutline
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.propiq.field.ui.theme.HairLine
import com.propiq.field.ui.theme.InkMuted
import com.propiq.field.ui.theme.InkSecondary
import com.propiq.field.ui.theme.RiskHigh
import com.propiq.field.ui.theme.RiskHighWash
import com.propiq.field.ui.theme.RiskLow
import com.propiq.field.ui.theme.RiskLowWash
import com.propiq.field.ui.theme.RiskMedium
import com.propiq.field.ui.theme.RiskMediumWash

/** Card shell used by every panel, so spacing and elevation stay consistent. */
@Composable
fun SectionCard(
    modifier: Modifier = Modifier,
    padding: PaddingValues = PaddingValues(16.dp),
    content: @Composable ColumnScope.() -> Unit,
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        color = MaterialTheme.colorScheme.surface,
        border = androidx.compose.foundation.BorderStroke(1.dp, HairLine),
    ) {
        Column(modifier = Modifier.padding(padding), content = content)
    }
}

@Composable
fun SectionLabel(text: String, modifier: Modifier = Modifier) {
    Text(
        text = text.uppercase(),
        style = MaterialTheme.typography.labelSmall,
        color = InkMuted,
        modifier = modifier,
    )
}

/**
 * Shimmering placeholder. Used instead of a bare spinner because the assessment
 * can legitimately take 10-30s against a cold backend, and a skeleton that
 * mirrors the final layout makes that wait read as progress rather than a hang.
 */
@Composable
fun ShimmerBox(
    modifier: Modifier = Modifier,
    height: androidx.compose.ui.unit.Dp = 16.dp,
    corner: androidx.compose.ui.unit.Dp = 6.dp,
) {
    val transition = rememberInfiniteTransition(label = "shimmer")
    val alpha by transition.animateFloat(
        initialValue = 0.35f,
        targetValue = 0.85f,
        animationSpec = infiniteRepeatable(
            animation = tween(900),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "shimmerAlpha",
    )
    Box(
        modifier = modifier
            .height(height)
            .clip(RoundedCornerShape(corner))
            .background(
                Brush.horizontalGradient(
                    listOf(
                        InkMuted.copy(alpha = alpha * 0.25f),
                        InkMuted.copy(alpha = alpha * 0.12f),
                        InkMuted.copy(alpha = alpha * 0.25f),
                    )
                )
            )
    )
}

/** Skeleton shaped like the real results screen, shown while the call is in flight. */
@Composable
fun ResultsSkeleton(statusLine: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.fillMaxWidth().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Text(
            text = statusLine,
            style = MaterialTheme.typography.bodyMedium,
            color = InkSecondary,
        )
        SectionCard {
            ShimmerBox(Modifier.fillMaxWidth(0.45f), height = 12.dp)
            Spacer(Modifier.height(14.dp))
            ShimmerBox(Modifier.fillMaxWidth(0.7f), height = 38.dp)
            Spacer(Modifier.height(12.dp))
            ShimmerBox(Modifier.fillMaxWidth(0.55f), height = 12.dp)
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            repeat(3) {
                SectionCard(modifier = Modifier.weight(1f)) {
                    ShimmerBox(Modifier.fillMaxWidth(0.8f), height = 10.dp)
                    Spacer(Modifier.height(10.dp))
                    ShimmerBox(Modifier.fillMaxWidth(0.6f), height = 20.dp)
                }
            }
        }
        SectionCard {
            ShimmerBox(Modifier.fillMaxWidth(0.35f), height = 12.dp)
            Spacer(Modifier.height(12.dp))
            repeat(3) {
                ShimmerBox(Modifier.fillMaxWidth(), height = 14.dp)
                Spacer(Modifier.height(8.dp))
            }
        }
    }
}

/**
 * Terminal failure state. Every path that can fail routes here rather than
 * showing a toast and an empty screen — the officer always gets a cause and a
 * next action.
 */
@Composable
fun ErrorState(
    title: String,
    message: String,
    modifier: Modifier = Modifier,
    icon: androidx.compose.ui.graphics.vector.ImageVector = Icons.Default.ErrorOutline,
    primaryLabel: String? = null,
    onPrimary: (() -> Unit)? = null,
    secondaryLabel: String? = null,
    onSecondary: (() -> Unit)? = null,
) {
    Column(
        modifier = modifier.fillMaxWidth().padding(28.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Box(
            modifier = Modifier
                .size(56.dp)
                .clip(RoundedCornerShape(16.dp))
                .background(RiskHighWash),
            contentAlignment = Alignment.Center,
        ) {
            Icon(icon, contentDescription = null, tint = RiskHigh, modifier = Modifier.size(28.dp))
        }
        Spacer(Modifier.height(16.dp))
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            textAlign = TextAlign.Center,
        )
        Spacer(Modifier.height(8.dp))
        Text(
            text = message,
            style = MaterialTheme.typography.bodyMedium,
            color = InkSecondary,
            textAlign = TextAlign.Center,
        )
        if (onPrimary != null && primaryLabel != null) {
            Spacer(Modifier.height(20.dp))
            Button(onClick = onPrimary) {
                Icon(Icons.Default.Refresh, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(8.dp))
                Text(primaryLabel)
            }
        }
        if (onSecondary != null && secondaryLabel != null) {
            Spacer(Modifier.height(8.dp))
            OutlinedButton(onClick = onSecondary) { Text(secondaryLabel) }
        }
    }
}

/** Persistent offline banner. */
@Composable
fun OfflineBanner(queued: Int, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        color = RiskMediumWash,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                Icons.Default.CloudOff,
                contentDescription = null,
                tint = RiskMedium,
                modifier = Modifier.size(18.dp),
            )
            Spacer(Modifier.width(10.dp))
            Text(
                text = if (queued > 0)
                    "Offline · $queued assessment${if (queued == 1) "" else "s"} queued, will submit automatically"
                else
                    "Offline · assessments will be saved and submitted automatically",
                style = MaterialTheme.typography.bodySmall,
                color = RiskMedium,
                fontWeight = FontWeight.Medium,
            )
        }
    }
}

/** Small severity/status chip. */
@Composable
fun Pill(
    text: String,
    severity: String? = null,
    modifier: Modifier = Modifier,
    fg: Color? = null,
    bg: Color? = null,
) {
    val (foreground, background) = when {
        fg != null && bg != null -> fg to bg
        severity?.lowercase() == "high" -> RiskHigh to RiskHighWash
        severity?.lowercase() == "medium" -> RiskMedium to RiskMediumWash
        else -> RiskLow to RiskLowWash
    }
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(999.dp),
        color = background,
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.labelSmall,
            color = foreground,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
        )
    }
}

/** Label-over-value metric block used across results and home. */
@Composable
fun MetricTile(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
    valueColor: Color = MaterialTheme.colorScheme.onSurface,
    caption: String? = null,
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        color = MaterialTheme.colorScheme.surface,
        border = androidx.compose.foundation.BorderStroke(1.dp, HairLine),
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Text(
                text = label.uppercase(),
                style = MaterialTheme.typography.labelSmall,
                color = InkMuted,
            )
            Spacer(Modifier.height(6.dp))
            Text(
                text = value,
                style = MaterialTheme.typography.titleMedium,
                color = valueColor,
                fontWeight = FontWeight.Bold,
            )
            if (caption != null) {
                Spacer(Modifier.height(2.dp))
                Text(
                    text = caption,
                    style = MaterialTheme.typography.bodySmall,
                    color = InkMuted,
                )
            }
        }
    }
}
