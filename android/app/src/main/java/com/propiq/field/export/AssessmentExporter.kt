package com.propiq.field.export

import android.content.ContentValues
import android.content.Context
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
import android.graphics.pdf.PdfDocument
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import com.propiq.field.core.Fmt
import com.propiq.field.core.Money
import com.propiq.field.data.remote.AssessmentResponse
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.OutputStream

/**
 * Writes a finished assessment to the shared Downloads folder as PDF and JSON.
 *
 * Downloads is chosen deliberately: it is the folder iQOO's Office Kit surfaces
 * for phone-to-laptop file transfer, so "export here, drag across on stage" is
 * a natural motion rather than a staged one. Nothing about Office Kit is coded
 * against — the bridge is an OS feature; this just puts the artefact where the
 * bridge already looks.
 *
 * On API 29+ the file goes through MediaStore (no storage permission needed);
 * below that it writes to the public Downloads directory directly.
 */
class AssessmentExporter(private val context: Context) {

    suspend fun export(result: AssessmentResponse, json: String): ExportResult =
        withContext(Dispatchers.IO) {
            val stamp = Fmt.fileTimestamp()
            val id = result.requestId ?: "assessment"
            val baseName = "PropIQ_${id}_$stamp"

            val pdf = runCatching { writePdf(result, "$baseName.pdf") }.getOrNull()
            val jsonFile = runCatching { writeText(json, "$baseName.json", "application/json") }
                .getOrNull()

            ExportResult(
                pdfName = pdf,
                jsonName = jsonFile,
                folder = "Downloads",
                success = pdf != null || jsonFile != null,
            )
        }

    // ── PDF ───────────────────────────────────────────────────────────────

    private fun writePdf(r: AssessmentResponse, fileName: String): String {
        val doc = PdfDocument()
        val pageInfo = PdfDocument.PageInfo.Builder(PAGE_W, PAGE_H, 1).create()
        val page = doc.startPage(pageInfo)
        val c = page.canvas

        val navy = Color.rgb(11, 30, 51)
        val teal = Color.rgb(15, 110, 86)
        val ink = Color.rgb(16, 33, 58)
        val muted = Color.rgb(92, 107, 127)

        val h1 = Paint().apply {
            color = Color.WHITE; textSize = 22f; isAntiAlias = true
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
        }
        val small = Paint().apply { color = Color.rgb(169, 186, 203); textSize = 9f; isAntiAlias = true }
        val label = Paint().apply { color = muted; textSize = 8.5f; isAntiAlias = true }
        val body = Paint().apply { color = ink; textSize = 10f; isAntiAlias = true }
        val bodyBold = Paint().apply {
            color = ink; textSize = 11f; isAntiAlias = true
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
        }
        val hero = Paint().apply {
            color = navy; textSize = 30f; isAntiAlias = true
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
        }
        val rule = Paint().apply { color = Color.rgb(220, 226, 233); strokeWidth = 0.8f }

        // Header band
        c.drawRect(0f, 0f, PAGE_W.toFloat(), 74f, Paint().apply { color = navy })
        c.drawText("PropIQ — Collateral Valuation", MARGIN, 32f, h1)
        c.drawText(
            "Field assessment · ${r.requestId ?: "—"} · ${Fmt.timestamp(System.currentTimeMillis())}",
            MARGIN, 50f, small,
        )
        c.drawText(
            "AI-assisted appraisal for LAP underwriting · Model MAPE ${r.resolvedMape}%",
            MARGIN, 64f, small,
        )

        var y = 108f

        // Subject
        c.drawText("SUBJECT PROPERTY", MARGIN, y, label); y += 15f
        c.drawText(
            "${Fmt.propType(r.propType)} · ${r.locality ?: "—"}, ${r.city ?: "—"}",
            MARGIN, y, bodyBold,
        ); y += 14f
        c.drawText(
            "${r.sizeSqft?.toInt() ?: "—"} sqft · ${r.ageYears?.toInt() ?: "—"} yrs old · " +
                "floor ${r.floorNum ?: "—"} · zone ${r.enrichment?.zoneTier ?: "—"}",
            MARGIN, y, body,
        ); y += 22f

        c.drawLine(MARGIN, y, PAGE_W - MARGIN, y, rule); y += 24f

        // Hero value
        c.drawText("ASSESSED MARKET VALUE", MARGIN, y, label); y += 34f
        c.drawText(Money.compact(r.marketValueMid), MARGIN, y, hero)
        c.drawText(Money.full(r.marketValueMid), MARGIN + 190f, y, body); y += 16f
        c.drawText(
            "Range ${Money.range(r.marketValueRange)} · ${Money.full(r.pricePerSqft)}/sqft · " +
                "confidence ${((r.confidenceScore ?: 0.0) * 100).toInt()}%",
            MARGIN, y, body,
        ); y += 26f

        // Metric row
        val cols = listOf(
            "Resale Potential Index" to String.format("%.1f", r.resalePotentialIndex ?: 0.0),
            "Time to sell" to Fmt.days(r.resolvedTimeToSell),
            "Distress (90d)" to Money.compact(r.distressValue90d ?: r.distressValueRange?.firstOrNull()),
        )
        cols.forEachIndexed { i, (k, v) ->
            val x = MARGIN + i * 165f
            c.drawText(k.uppercase(), x, y, label)
            c.drawText(v, x, y + 16f, bodyBold)
        }
        y += 38f
        c.drawLine(MARGIN, y, PAGE_W - MARGIN, y, rule); y += 22f

        // LTV
        r.ltvAnalysis?.let { ltv ->
            c.drawText("RECOMMENDED LTV (RBI-ALIGNED)", MARGIN, y, label); y += 17f
            c.drawText(
                "${ltv.recommendedLtvPct ?: "—"}%  ·  max loan ${Money.compact(ltv.maxLoanAmount)}  " +
                    "·  zone ${ltv.ltvZone?.uppercase() ?: "—"}",
                MARGIN, y, bodyBold,
            ); y += 15f
            ltv.pflRationale?.let { y = wrap(c, it, MARGIN, y, body, 92) }
            y += 12f
            c.drawLine(MARGIN, y, PAGE_W - MARGIN, y, rule); y += 22f
        }

        // Risk flags
        c.drawText("RISK FLAGS", MARGIN, y, label); y += 16f
        val flags = r.rankedFlags
        if (flags.isEmpty()) {
            c.drawText("None raised.", MARGIN, y, body); y += 16f
        } else {
            flags.take(5).forEach { f ->
                val sev = f.severity?.uppercase() ?: "—"
                c.drawText(
                    "[$sev] ${Fmt.flagLabel(f.flag)}",
                    MARGIN, y,
                    Paint(bodyBold).apply {
                        color = when (f.severity?.lowercase()) {
                            "high" -> Color.rgb(163, 45, 45)
                            "medium" -> Color.rgb(186, 117, 23)
                            else -> teal
                        }
                    },
                ); y += 13f
                f.detail?.let { y = wrap(c, it, MARGIN + 8f, y, body, 90) }
                y += 8f
                if (y > PAGE_H - 130f) return@forEach
            }
        }

        // CV block
        r.cvAssessment?.let { cv ->
            if (y < PAGE_H - 150f) {
                y += 6f
                c.drawLine(MARGIN, y, PAGE_W - MARGIN, y, rule); y += 22f
                c.drawText("VISUAL CONDITION (VLM)", MARGIN, y, label); y += 16f
                c.drawText(
                    "${cv.condition?.uppercase() ?: "—"} · quality ${cv.qualityScore ?: "—"}/100 · " +
                        "${cv.imagesCount ?: 0} image(s) · adjustment ×${cv.adjustmentFactor ?: 1.0}",
                    MARGIN, y, body,
                ); y += 14f
                cv.perImage?.firstOrNull()?.vlmAnalysis?.description?.let {
                    y = wrap(c, it, MARGIN, y, body, 92)
                }
            }
        }

        // Footer
        val footer = Paint().apply { color = muted; textSize = 7.5f; isAntiAlias = true }
        c.drawText(
            "Generated by PropIQ Field on-device. AI-assisted estimate — not a substitute for a " +
                "registered valuer's certificate.",
            MARGIN, PAGE_H - 30f, footer,
        )
        c.drawText(
            r.ltvAnalysis?.disclaimer?.take(120) ?: "",
            MARGIN, PAGE_H - 19f, footer,
        )

        doc.finishPage(page)

        writeStream(fileName, "application/pdf") { out -> doc.writeTo(out) }
        doc.close()
        return fileName
    }

    /** Naive width-based wrapping — adequate for a one-page field summary. */
    private fun wrap(
        c: android.graphics.Canvas,
        text: String,
        x: Float,
        startY: Float,
        paint: Paint,
        charsPerLine: Int,
    ): Float {
        var y = startY
        val words = text.replace("\n", " ").split(" ")
        val line = StringBuilder()
        for (w in words) {
            if (line.length + w.length + 1 > charsPerLine) {
                c.drawText(line.toString(), x, y, paint)
                y += 12f
                line.clear()
            }
            if (line.isNotEmpty()) line.append(' ')
            line.append(w)
        }
        if (line.isNotEmpty()) {
            c.drawText(line.toString(), x, y, paint)
            y += 12f
        }
        return y
    }

    // ── Shared writing ────────────────────────────────────────────────────

    private fun writeText(content: String, fileName: String, mime: String): String {
        writeStream(fileName, mime) { out -> out.write(content.toByteArray()) }
        return fileName
    }

    private fun writeStream(fileName: String, mime: String, block: (OutputStream) -> Unit) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val values = ContentValues().apply {
                put(MediaStore.Downloads.DISPLAY_NAME, fileName)
                put(MediaStore.Downloads.MIME_TYPE, mime)
                put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)
                put(MediaStore.Downloads.IS_PENDING, 1)
            }
            val resolver = context.contentResolver
            val uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
                ?: throw IllegalStateException("Could not create $fileName in Downloads")
            resolver.openOutputStream(uri)?.use(block)
                ?: throw IllegalStateException("Could not open $fileName for writing")
            values.clear()
            values.put(MediaStore.Downloads.IS_PENDING, 0)
            resolver.update(uri, values, null, null)
        } else {
            @Suppress("DEPRECATION")
            val dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
            if (!dir.exists()) dir.mkdirs()
            File(dir, fileName).outputStream().use(block)
        }
    }

    companion object {
        // A4 at 72dpi
        private const val PAGE_W = 595
        private const val PAGE_H = 842
        private const val MARGIN = 40f
    }
}

data class ExportResult(
    val pdfName: String?,
    val jsonName: String?,
    val folder: String,
    val success: Boolean,
) {
    val summary: String
        get() = when {
            !success -> "Export failed."
            pdfName != null && jsonName != null ->
                "Saved PDF + JSON to $folder — ready to pull across via Office Kit."
            pdfName != null -> "Saved $pdfName to $folder."
            else -> "Saved $jsonName to $folder."
        }
}
