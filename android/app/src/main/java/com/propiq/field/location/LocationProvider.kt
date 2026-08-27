package com.propiq.field.location

import android.annotation.SuppressLint
import android.content.Context
import android.location.Geocoder
import com.google.android.gms.location.CurrentLocationRequest
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import java.util.Locale
import kotlin.coroutines.resume

/**
 * GPS capture via FusedLocationProviderClient.
 *
 * This matters more than a convenience: `PropertyInput.geo_lat/geo_lon` are
 * optional on the backend, but supplying them makes `enrich_property` skip its
 * geocoding step entirely (see the "Gap 6 fix" comment in
 * backend/app/main.py `_run_assessment`). Auto-capturing coordinates on screen
 * open therefore removes a network hop from the server's own critical path,
 * and pins the valuation to where the officer is physically standing rather
 * than to a locality centroid.
 */
class LocationProvider(private val context: Context) {

    private val client by lazy { LocationServices.getFusedLocationProviderClient(context) }

    /**
     * Returns null rather than throwing when permission is absent or no fix
     * arrives — the caller degrades to locality-only assessment, which the
     * backend fully supports.
     */
    @SuppressLint("MissingPermission")
    suspend fun currentFix(timeoutMs: Long = 12_000): GeoFix? = withTimeoutOrNull(timeoutMs) {
        val location = suspendCancellableCoroutine<android.location.Location?> { cont ->
            val request = CurrentLocationRequest.Builder()
                .setPriority(Priority.PRIORITY_HIGH_ACCURACY)
                .setMaxUpdateAgeMillis(60_000)
                .setDurationMillis(timeoutMs)
                .build()
            runCatching {
                client.getCurrentLocation(request, null)
                    .addOnSuccessListener { cont.resume(it) }
                    .addOnFailureListener { cont.resume(null) }
            }.onFailure { cont.resume(null) }
        } ?: return@withTimeoutOrNull null

        GeoFix(
            lat = location.latitude,
            lon = location.longitude,
            accuracyMeters = if (location.hasAccuracy()) location.accuracy else null,
            areaName = reverseGeocode(location.latitude, location.longitude),
        )
    }

    /**
     * Best-effort locality name for the "you are here" line. Never blocks the
     * assessment — the backend resolves locality from the picker value, not
     * from this string.
     */
    private suspend fun reverseGeocode(lat: Double, lon: Double): String? =
        withContext(Dispatchers.IO) {
            if (!Geocoder.isPresent()) return@withContext null
            runCatching {
                @Suppress("DEPRECATION")
                val results = Geocoder(context, Locale.getDefault())
                    .getFromLocation(lat, lon, 1)
                results?.firstOrNull()?.let { a ->
                    a.subLocality ?: a.locality ?: a.subAdminArea
                }
            }.getOrNull()
        }
}

data class GeoFix(
    val lat: Double,
    val lon: Double,
    val accuracyMeters: Float? = null,
    val areaName: String? = null,
) {
    val display: String
        get() = String.format(Locale.US, "%.5f, %.5f", lat, lon)

    val accuracyLabel: String
        get() = accuracyMeters?.let { "±${it.toInt()} m" } ?: "accuracy unknown"

    /**
     * Nearest supported locality by great-circle distance, used to pre-select
     * the picker. Coordinates come from backend/app/data/india_circle_rates.py.
     */
    fun nearestLocality(candidates: Map<String, Pair<Double, Double>>): String? {
        if (candidates.isEmpty()) return null
        return candidates.minByOrNull { (_, coords) ->
            val dLat = coords.first - lat
            val dLon = coords.second - lon
            dLat * dLat + dLon * dLon
        }?.key
    }
}
