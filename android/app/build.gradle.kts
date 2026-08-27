import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.ksp)
}

// ── Base URL configuration ────────────────────────────────────────────────
// Resolution order (first hit wins):
//   1. -PpropiqBaseUrl=... on the Gradle command line
//   2. propiq.baseUrl=...  in android/local.properties  (git-ignored)
//   3. the 10.0.2.2 emulator loopback default below
// At runtime this is only the *initial* value — Settings on the Home screen
// can override it and the override is persisted, so a demo can be re-pointed
// at a deployed backend without a rebuild.
val localProps = Properties().apply {
    val f = rootProject.file("local.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}
val configuredBaseUrl: String =
    (project.findProperty("propiqBaseUrl") as String?)
        ?: localProps.getProperty("propiq.baseUrl")
        ?: "http://10.0.2.2:8000"
val configuredApiKey: String =
    (project.findProperty("propiqApiKey") as String?)
        ?: localProps.getProperty("propiq.apiKey")
        ?: "propiq-demo-2026"

android {
    namespace = "com.propiq.field"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.propiq.field"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"

        buildConfigField("String", "DEFAULT_BASE_URL", "\"$configuredBaseUrl\"")
        buildConfigField("String", "DEFAULT_API_KEY", "\"$configuredApiKey\"")
    }

    buildTypes {
        debug {
            isMinifyEnabled = false
        }
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
    packaging {
        resources.excludes += "/META-INF/{AL2.0,LGPL2.1}"
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.activity.compose)
    implementation(libs.kotlinx.coroutines.android)

    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.material.icons)
    debugImplementation(libs.androidx.compose.ui.tooling)

    implementation(libs.androidx.navigation.compose)

    // Networking — cloud valuation engine
    implementation(libs.retrofit)
    implementation(libs.retrofit.gson)
    implementation(libs.okhttp)
    implementation(libs.okhttp.logging)
    implementation(libs.gson)

    // Offline queue
    implementation(libs.androidx.room.runtime)
    implementation(libs.androidx.room.ktx)
    ksp(libs.androidx.room.compiler)
    implementation(libs.androidx.work.runtime.ktx)

    // Camera
    implementation(libs.androidx.camera.core)
    implementation(libs.androidx.camera.camera2)
    implementation(libs.androidx.camera.lifecycle)
    implementation(libs.androidx.camera.view)

    // On-device AI + device data
    implementation(libs.mlkit.image.labeling)
    // On-device LLM (Gemma / Phi class) — model file is side-loaded, not bundled.
    implementation(libs.mediapipe.tasks.genai)
    implementation(libs.play.services.location)

    implementation(libs.coil.compose)

    testImplementation(libs.junit)
}
