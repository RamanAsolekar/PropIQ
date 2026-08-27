package com.propiq.field.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.graphics.toArgb
import androidx.core.view.WindowCompat

private val LightScheme = lightColorScheme(
    primary = TealDeep,
    onPrimary = PaperSurface,
    primaryContainer = TealWash,
    onPrimaryContainer = TealDeep,
    secondary = PurpleBrand,
    onSecondary = PaperSurface,
    secondaryContainer = PurpleWash,
    onSecondaryContainer = PurpleBrand,
    tertiary = NavyInk,
    onTertiary = PaperSurface,
    background = PaperBg,
    onBackground = InkPrimary,
    surface = PaperSurface,
    onSurface = InkPrimary,
    surfaceVariant = PaperBg,
    onSurfaceVariant = InkSecondary,
    outline = HairLine,
    error = RiskHigh,
    onError = PaperSurface,
    errorContainer = RiskHighWash,
    onErrorContainer = RiskHigh,
)

private val DarkScheme = darkColorScheme(
    primary = TealPrimary,
    onPrimary = NavyDeep,
    primaryContainer = TealDeep,
    onPrimaryContainer = TealWash,
    secondary = PurpleBrand,
    onSecondary = PaperSurface,
    tertiary = TealPrimary,
    background = NavyDeep,
    onBackground = PaperSurface,
    surface = NavyInk,
    onSurface = PaperSurface,
    surfaceVariant = NavySlate,
    onSurfaceVariant = OnDarkMuted,
    outline = NavyLine,
    error = ErrorOnDark,
    onError = NavyDeep,
)

@Composable
fun PropIQTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val scheme = if (darkTheme) DarkScheme else LightScheme
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = NavyInk.toArgb()
            WindowCompat.getInsetsController(window, view)
                .isAppearanceLightStatusBars = false
        }
    }
    MaterialTheme(
        colorScheme = scheme,
        typography = PropIQTypography,
        content = content,
    )
}
