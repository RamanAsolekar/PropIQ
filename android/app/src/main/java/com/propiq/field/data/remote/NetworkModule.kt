package com.propiq.field.data.remote

import com.propiq.field.BuildConfig
import com.propiq.field.core.AppSettings
import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Builds the API client.
 *
 * Two things here are deliberate rather than boilerplate:
 *
 * 1. The base URL and API key are read from [AppSettings] *per request* via
 *    interceptors, not baked into the Retrofit instance. That lets Settings
 *    re-point the app at a different backend without rebuilding the client
 *    graph or restarting the process.
 *
 * 2. The read timeout is 120s. The backend's own README warns that a cold
 *    Render free-tier instance spends time in ML init, and the web client sets
 *    300s for the same reason. 120s is the compromise: long enough for a cold
 *    VLM round trip, short enough that a field officer in dead signal falls
 *    through to the offline queue instead of staring at a spinner.
 */
object NetworkModule {

    fun create(settings: AppSettings): PropIQApi {
        val client = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(120, TimeUnit.SECONDS)
            .writeTimeout(120, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .addInterceptor(baseUrlInterceptor(settings))
            .addInterceptor(authInterceptor(settings))
            .apply {
                if (BuildConfig.DEBUG) {
                    addInterceptor(
                        HttpLoggingInterceptor().apply {
                            level = HttpLoggingInterceptor.Level.BASIC
                        }
                    )
                }
            }
            .build()

        return Retrofit.Builder()
            // Placeholder host — every request is rewritten by the interceptor
            // below. Retrofit only needs *a* valid URL at construction time.
            .baseUrl("http://localhost/")
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(PropIQApi::class.java)
    }

    /** Rewrites scheme/host/port on every call from the live settings value. */
    private fun baseUrlInterceptor(settings: AppSettings) = Interceptor { chain ->
        val configured = settings.baseUrl.value.toHttpUrlOrNullSafe()
        val request = chain.request()
        if (configured == null) return@Interceptor chain.proceed(request)

        val newUrl = request.url.newBuilder()
            .scheme(configured.scheme)
            .host(configured.host)
            .port(configured.port)
            .build()
        chain.proceed(request.newBuilder().url(newUrl).build())
    }

    private fun authInterceptor(settings: AppSettings) = Interceptor { chain ->
        chain.proceed(
            chain.request().newBuilder()
                .addHeader("X-API-Key", settings.apiKey.value)
                .addHeader("Accept", "application/json")
                .build()
        )
    }

    private fun String.toHttpUrlOrNullSafe(): HttpUrl? =
        runCatching { this.toHttpUrlOrNull() }.getOrNull()
}
