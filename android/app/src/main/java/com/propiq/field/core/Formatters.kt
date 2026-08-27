package com.propiq.field.core

import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.math.abs
import kotlin.math.roundToLong

/**
 * Indian-format currency. Valuations here run from a few lakh to tens of crore,
 * so the jury-facing hero number must read as "₹1.94 Cr", not "₹19,400,000".
 */
object Money {

    fun compact(amount: Number?): String {
        if (amount == null) return "—"
        val v = amount.toDouble()
        if (v == 0.0) return "₹0"
        val sign = if (v < 0) "-" else ""
        val a = abs(v)
        return when {
            a >= 1_00_00_000 -> "$sign₹${trim(a / 1_00_00_000)} Cr"
            a >= 1_00_000 -> "$sign₹${trim(a / 1_00_000)} L"
            a >= 1_000 -> "$sign₹${trim(a / 1_000)} K"
            else -> "$sign₹${a.roundToLong()}"
        }
    }

    /** Full grouped figure, Indian digit grouping (##,##,###). */
    fun full(amount: Number?): String {
        if (amount == null) return "—"
        val n = amount.toDouble().roundToLong()
        val sign = if (n < 0) "-" else ""
        val digits = abs(n).toString()
        if (digits.length <= 3) return "$sign₹$digits"
        val last3 = digits.takeLast(3)
        var rest = digits.dropLast(3)
        val parts = mutableListOf<String>()
        while (rest.length > 2) {
            parts.add(0, rest.takeLast(2))
            rest = rest.dropLast(2)
        }
        if (rest.isNotEmpty()) parts.add(0, rest)
        return "$sign₹${parts.joinToString(",")},$last3"
    }

    fun range(range: List<Number>?): String {
        if (range == null || range.size < 2) return "—"
        return "${compact(range[0])} – ${compact(range[1])}"
    }

    private fun trim(value: Double): String {
        val r = (value * 100).roundToLong() / 100.0
        return if (r % 1.0 == 0.0) r.toLong().toString()
        else String.format(Locale.US, "%.2f", r).trimEnd('0').trimEnd('.')
    }
}

object Fmt {
    private val stamp = SimpleDateFormat("dd MMM, HH:mm", Locale.getDefault())
    private val fileStamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US)

    fun timestamp(millis: Long): String = stamp.format(Date(millis))
    fun fileTimestamp(millis: Long = System.currentTimeMillis()): String =
        fileStamp.format(Date(millis))

    fun relative(millis: Long): String {
        val delta = System.currentTimeMillis() - millis
        return when {
            delta < 60_000 -> "just now"
            delta < 3_600_000 -> "${delta / 60_000}m ago"
            delta < 86_400_000 -> "${delta / 3_600_000}h ago"
            else -> "${delta / 86_400_000}d ago"
        }
    }

    /** "3bhk_apartment" -> "3BHK Apartment" */
    fun propType(raw: String?): String {
        if (raw.isNullOrBlank()) return "—"
        return raw.split("_").joinToString(" ") { word ->
            if (word.length <= 4 && word.any { it.isDigit() }) word.uppercase()
            else word.replaceFirstChar { it.uppercase() }
        }
    }

    /** "cv_property_type_mismatch" -> "CV Property Type Mismatch" */
    fun flagLabel(raw: String?): String {
        if (raw.isNullOrBlank()) return "Risk flag"
        return raw.split("_").joinToString(" ") { w ->
            if (w.lowercase() in setOf("cv", "ltv", "rbi", "vlm")) w.uppercase()
            else w.replaceFirstChar { it.uppercase() }
        }
    }

    fun days(range: List<Int>?): String {
        if (range == null || range.size < 2) return "—"
        return "${range[0]}–${range[1]} days"
    }
}
