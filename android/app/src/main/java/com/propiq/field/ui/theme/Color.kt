package com.propiq.field.ui.theme

import androidx.compose.ui.graphics.Color

/**
 * PropIQ Field palette.
 *
 * The brief asked for "navy/teal/white". The existing web dashboard's real
 * identity (frontend/src/styles/global.css) is purple #534AB7 + teal #0F6E56 on
 * warm grey — not navy. Rather than pick one and drift from the other, this
 * palette keeps the web app's exact teal and purple as the accent/data colours
 * and introduces navy as the *surface* colour, which is what actually produces
 * the "Bloomberg terminal" read on a phone in daylight.
 */

// Surfaces
val NavyInk = Color(0xFF0B1E33)
val NavyDeep = Color(0xFF071523)
val NavySlate = Color(0xFF16324F)
val NavyLine = Color(0xFF24455F)

// Accents — carried over from the web app so both surfaces read as one product
val TealPrimary = Color(0xFF12B39A)
val TealDeep = Color(0xFF0F6E56)
val TealWash = Color(0xFFE1F5EE)
val PurpleBrand = Color(0xFF534AB7)
val PurpleWash = Color(0xFFEEEDFE)

// Light chrome
val PaperBg = Color(0xFFF5F7FA)
val PaperSurface = Color(0xFFFFFFFF)
val InkPrimary = Color(0xFF10213A)
val InkSecondary = Color(0xFF5C6B7F)
val InkMuted = Color(0xFF8A97A8)
val HairLine = Color(0x1A10213A)

// Semantic — risk / status
val RiskHigh = Color(0xFFA32D2D)
val RiskHighWash = Color(0xFFFCEBEB)
val RiskMedium = Color(0xFFBA7517)
val RiskMediumWash = Color(0xFFFAEEDA)
val RiskLow = Color(0xFF0F6E56)
val RiskLowWash = Color(0xFFE1F5EE)

// LTV zone colours mirror the backend's ltv_zone green/amber/red contract
val ZoneGreen = Color(0xFF0F6E56)
val ZoneAmber = Color(0xFFBA7517)
val ZoneRed = Color(0xFFA32D2D)

// Dark-scheme support tones
val OnDarkMuted = Color(0xFFA9BACB)
val ErrorOnDark = Color(0xFFFF6B6B)
