package com.propiq.field

import android.app.Application
import android.content.Context
import com.google.gson.Gson
import com.propiq.field.core.AppSettings
import com.propiq.field.core.Connectivity
import com.propiq.field.data.local.AppDatabase
import com.propiq.field.data.remote.NetworkModule
import com.propiq.field.data.remote.PropIQApi
import com.propiq.field.data.repo.AssessmentRepository
import com.propiq.field.export.AssessmentExporter
import com.propiq.field.location.LocationProvider
import com.propiq.field.ondevice.PhotoGate
import com.propiq.field.speech.VoiceCapture
import com.propiq.field.sync.SyncWorker

class PropIQApp : Application() {

    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
        // Anything stranded by a previous process death gets picked up as soon
        // as the device has a network again.
        SyncWorker.schedule(this)
    }
}

/**
 * Hand-rolled dependency container.
 *
 * Deliberately not Hilt: the graph is small and fully known at startup, and
 * avoiding an annotation processor keeps `./gradlew assembleDebug` fast and
 * free of KSP/Kotlin version coupling. The boundaries that matter for the
 * architecture — remote, local, on-device, repository — are enforced by package
 * structure and constructor injection either way.
 */
class AppContainer(context: Context) {

    private val appContext = context.applicationContext

    val settings: AppSettings = AppSettings(appContext)
    val connectivity: Connectivity = Connectivity(appContext)
    val database: AppDatabase = AppDatabase.get(appContext)
    val gson: Gson = Gson()

    val api: PropIQApi = NetworkModule.create(settings)

    val repository: AssessmentRepository = AssessmentRepository(
        api = api,
        queueDao = database.queueDao(),
        historyDao = database.historyDao(),
        connectivity = connectivity,
        settings = settings,
        gson = gson,
    )

    val locationProvider: LocationProvider = LocationProvider(appContext)
    val voiceCapture: VoiceCapture = VoiceCapture(appContext)
    val photoGate: PhotoGate = PhotoGate()
    val exporter: AssessmentExporter = AssessmentExporter(appContext)
}
