package com.propiq.field.core

import android.content.Context
import androidx.core.content.edit
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import com.propiq.field.BuildConfig

/**
 * Runtime-editable configuration. The base URL ships from BuildConfig (see
 * app/build.gradle.kts) but must be changeable on-device: at the venue the
 * backend moves from a laptop on the LAN to a deployed URL, and reflashing an
 * APK mid-event is not an option.
 */
class AppSettings(context: Context) {

    private val prefs = context.getSharedPreferences("propiq_settings", Context.MODE_PRIVATE)

    private val _baseUrl = MutableStateFlow(
        prefs.getString(KEY_BASE_URL, null) ?: BuildConfig.DEFAULT_BASE_URL
    )
    val baseUrl: StateFlow<String> = _baseUrl

    private val _apiKey = MutableStateFlow(
        prefs.getString(KEY_API_KEY, null) ?: BuildConfig.DEFAULT_API_KEY
    )
    val apiKey: StateFlow<String> = _apiKey

    private val _demoMode = MutableStateFlow(prefs.getBoolean(KEY_DEMO, false))
    val demoMode: StateFlow<Boolean> = _demoMode

    fun setBaseUrl(value: String) {
        val cleaned = normalize(value)
        prefs.edit { putString(KEY_BASE_URL, cleaned) }
        _baseUrl.value = cleaned
    }

    fun setApiKey(value: String) {
        val cleaned = value.trim()
        prefs.edit { putString(KEY_API_KEY, cleaned) }
        _apiKey.value = cleaned
    }

    fun setDemoMode(enabled: Boolean) {
        prefs.edit { putBoolean(KEY_DEMO, enabled) }
        _demoMode.value = enabled
    }

    /** Retrofit demands a trailing slash; officers will not type one. */
    private fun normalize(raw: String): String {
        var s = raw.trim()
        if (s.isEmpty()) return BuildConfig.DEFAULT_BASE_URL
        if (!s.startsWith("http://") && !s.startsWith("https://")) s = "http://$s"
        return s.trimEnd('/')
    }

    companion object {
        private const val KEY_BASE_URL = "base_url"
        private const val KEY_API_KEY = "api_key"
        private const val KEY_DEMO = "demo_mode"
    }
}
