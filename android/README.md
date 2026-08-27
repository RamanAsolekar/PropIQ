# PropIQ Field — Android companion

A native Android "field valuer" app for [PropIQ](../README.md), the AI collateral
valuation and risk engine for Loan Against Property (LAP) lending in India.

This is **not** a port of the React dashboard. It is a phone-native surface onto
the same intelligence engine: a loan officer stands inside a property, captures
it, and gets a valuation back in under a minute — instead of the 2-3 weeks a
manual site visit plus panel valuer takes today.

Built for **iQOO City Battles 2026, Pune leg.**

---

## Quick start

```bash
cd android
./gradlew assembleDebug
# APK: app/build/outputs/apk/debug/app-debug.apk
```

Requires **JDK 17+** and the **Android SDK** with `platforms;android-35` and
`build-tools;35.0.0`. Nothing else — no Android Studio step, no manual sync.

Install to a connected device:

```bash
./gradlew installDebug
# or
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

### If Gradle can't find the SDK

Create `android/local.properties` (git-ignored):

```properties
sdk.dir=C:/Users/<you>/AppData/Local/Android/Sdk
```

Use forward slashes even on Windows — the Java properties parser eats single
backslashes and you get a confusing `IOException: The filename, directory name,
or volume label syntax is incorrect`.

---

## Backend URL configuration

The app talks to the existing FastAPI backend. The base URL resolves in this
order — first hit wins:

| Priority | Source | Example |
|---|---|---|
| 1 | Gradle property | `./gradlew assembleDebug -PpropiqBaseUrl=https://propiq.onrender.com` |
| 2 | `local.properties` | `propiq.baseUrl=http://192.168.1.42:8000` |
| 3 | Built-in default | `http://10.0.2.2:8000` (emulator → host localhost) |

The same three-tier resolution applies to `propiq.apiKey` / `-PpropiqApiKey`,
defaulting to `propiq-demo-2026` (matches `PROPIQ_API_KEYS` in
`backend/app/core/security.py`).

**At runtime, Settings on the Home screen overrides both and persists the
change.** That is the one that matters at a venue: when the backend moves from
your laptop to a deployed URL an hour before the pitch, you re-point the app in
five seconds instead of rebuilding an APK.

### Reaching a local backend

```bash
# terminal 1
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- **Emulator** → `http://10.0.2.2:8000` (the default; `localhost` on the emulator
  is the emulator itself)
- **Physical phone on the same wifi** → `http://<laptop-LAN-IP>:8000`. Note the
  `--host 0.0.0.0` above; uvicorn's default `127.0.0.1` bind is not reachable
  from the phone.

Cleartext HTTP is permitted for local addresses only
(`res/xml/network_security_config.xml`); a public URL should be HTTPS.

CORS is irrelevant here — that's a browser policy, and a native OkHttp client
doesn't enforce it. The backend's `CORS_ORIGINS` allow-list does not need to
change for Android.

---

## Architecture

```
ui/            Compose screens + ViewModels        (no business logic in Composables)
  home/  capture/  results/  components/  theme/  nav/
ondevice/      PhotoGate — LOCAL inference          ← on-device half of the pipeline
data/
  remote/      Retrofit API + DTOs                  ← cloud half of the pipeline
  local/       Room: offline queue + history
  repo/        AssessmentRepository — owns online/offline/demo routing
  demo/        Stage fixtures + locality reference data
location/      FusedLocationProviderClient
speech/        SpeechRecognizer (on-device where supported)
export/        PDF + JSON writer → Downloads
sync/          WorkManager retry worker
core/          Outcome type, connectivity, settings, formatters
```

**Compose UI → ViewModel → Repository → {Retrofit | Room | PhotoGate}.**
Coroutines and Flow throughout; no callbacks above the platform-API boundary.
Dependencies are wired in `AppContainer` (hand-rolled — the graph is small and
fully known at startup, and skipping an annotation processor keeps the build
fast and free of KSP/Kotlin version coupling).

### The hybrid pipeline

This is the architecture story, and the package layout is meant to make it
obvious in a code walkthrough:

```
   shutter
      │
      ▼
┌──────────────────────┐   rejected (~200ms, no network)
│  ondevice/PhotoGate  │──────────────────────────────► "Too blurry — retake"
│  · Laplacian blur    │
│  · ML Kit labeller   │
└──────────┬───────────┘
           │ accepted
           ▼
┌──────────────────────┐   offline / timeout
│ data/repo/           │──────────────────────────────► Room queue → WorkManager
│  AssessmentRepository│                                 auto-retry on reconnect
└──────────┬───────────┘
           │ online
           ▼
   POST /api/v1/assess/image
   XGBoost + SHAP · Groq Llama-4-Scout VLM · RBI LTV engine
```

`PhotoGate` combines two independent on-device signals:

1. **Sharpness** — variance of the Laplacian over a downsampled luma plane. Pure
   arithmetic, sub-10ms, catches the most common field failure: a motion-blurred
   wall shot taken while walking.
2. **Scene class** — ML Kit's *bundled* image labeller (`com.google.mlkit:image-labeling`,
   not the Play-Services variant), so the model ships inside the APK and runs
   with the radio off. Labels are mapped onto EXTERIOR / INTERIOR / DOCUMENT.

**Why ML Kit and not a hand-rolled TFLite model:** a custom `.tflite` would need
a checked-in binary, a label file, NNAPI delegate wiring and its own
preprocessing — for a classifier still weaker than ML Kit's 400-label bundled
MobileNet. ML Kit gives the same on-device guarantee with a fraction of the
surface area and auto-delegates to the NPU where the device exposes one. The
payoff is real UX, not just a box ticked: rejecting a blurred frame costs ~200ms
locally instead of a 10-30s VLM round trip that returns a useless grade, and it
keeps junk off the backend entirely.

### Device data used

| Hardware | API | Where |
|---|---|---|
| Camera | CameraX (`ImageCapture`, live preview) | `ui/capture/CameraCapture.kt` |
| NPU / DSP | ML Kit bundled image labelling | `ondevice/PhotoGate.kt` |
| GPS | `FusedLocationProviderClient` | `location/LocationProvider.kt` |
| Microphone | `SpeechRecognizer`, on-device on API 31+ | `speech/VoiceCapture.kt` |

There is **no gallery picker anywhere in the app** — deliberately. A collateral
photo that could have been taken somewhere else at some other time is worthless
for fraud detection.

GPS is not decoration either: supplying `geo_lat`/`geo_lon` makes
`enrich_property` skip its geocoding step server-side (the "Gap 6 fix" in
`backend/app/main.py::_run_assessment`), so auto-capturing coordinates removes a
network hop from the server's own critical path.

---

## Offline behaviour

A field officer in basement parking is the normal case, not an edge case.

- **Radio already offline** → queued immediately. No 15s connect timeout first.
- **Timeout / 5xx / unreachable / 429** → queued and retried with exponential
  backoff.
- **400 or 403** → *not* queued. Bad property fields or a bad API key will fail
  identically forever; queueing them would just build a backlog of garbage.
- Retry is a `WorkManager` job with a `NetworkType.CONNECTED` constraint, so the
  OS wakes it when signal returns. No polling, no wake locks.
- Photos are stored as **file paths**, not blobs — a four-photo assessment is
  several MB and would blow past SQLite's CursorWindow limit.
- Queue state is visible and manageable from the Home screen ("Queued" tile).

Every failure mode has a real UI: permission denied, camera unavailable, backend
unreachable, photo unreadable, cache evicted before retry.

---

## Export (Office Kit)

The results screen has **Export assessment**, which writes a one-page PDF and the
raw JSON to the device's **Downloads** folder via `MediaStore` (no storage
permission needed on API 29+).

Downloads is the folder iQOO's Office Kit surfaces for phone-to-laptop transfer,
so dragging the credit memo across on stage is a natural motion rather than a
staged one. Nothing here codes *against* Office Kit — the bridge is an OS
feature; this just puts the artefact where the bridge already looks.

---

## Demo Mode

Toggle in Settings. When on, assessments return pre-seeded fixtures instantly
with **zero network calls** — including the voice step.

The fixtures are shaped exactly like a real `/api/v1/assess/image` response
(same field names, same nesting, same magnitudes), so the results screen renders
through the identical code path. Nothing on stage is a special case.

Two scenarios:
- **Run valuation** → the clean path: ₹1.94 Cr, RPI 82.4, green LTV zone.
- **Run the fraud-detection scenario** → claimed 3BHK, VLM sees a warehouse.

---

## 90-second demo script

Setup: Demo Mode **on**, app on the Home screen, laptop paired via Office Kit.

| Time | Do | Say | Criterion |
|---|---|---|---|
| **0:00–0:10** | Home screen. Point at the "2-3 weeks → < 60 seconds" panel. | "LAP collateral valuation in India takes two to three weeks and a physical site visit. We collapse it to under a minute, on the same phone that got the officer there." | Novelty & Impact (20%) |
| **0:10–0:20** | Tap **Start field assessment**. GPS chip fills in on its own; locality auto-selects. | "GPS is captured the moment the screen opens — the officer never types a location. It also lets our server skip geocoding, so the result comes back faster." | Phone use (15%) |
| **0:20–0:35** | Tap **Speak**. Say: *"Three BHK apartment in Baner, fourteen fifty square feet, eight years old, seventh floor."* Form fills. | "Speech-to-text runs on-device. Hands-free matters when you're holding a phone up to a wall with a torch in the other hand." | Phone use (15%) |
| **0:35–0:50** | **Open camera**. Deliberately capture one blurred frame → red on-device rejection appears. Then capture a sharp exterior + interior. | "Every frame is screened on the phone's own NPU before anything is uploaded. Blur detection and scene classification, about two hundred milliseconds. A bad photo never costs a round trip." | Phone use + Technical depth |
| **0:50–1:05** | Tap **Run the fraud-detection scenario**. Results screen lands. | "Valuation, one-nine-four crore. But look at the red banner." | End product (30%) |
| **1:05–1:20** | Point at the fraud banner, then the LTV panel. | "The borrower declared a 3BHK apartment. The vision model looked at the photos and saw an industrial warehouse — roller shutter, roof trusses, pallet racking. Two high-severity flags, and the LTV engine has already cut the sanction from 70% to 40%. Caught before disbursal, not during recovery." | Novelty & Impact (20%) |
| **1:20–1:30** | Tap **Export assessment**. Drag the PDF to the laptop via Office Kit. | "Exports to Downloads as PDF and JSON — straight across to the credit team's laptop." | Office Kit (10%) |

**Optional 15s add-on if the room is engaged** — turn on airplane mode, run
another assessment, show it queue; turn wifi back on, show it auto-submit.
That's the End Product criterion (30%) in one gesture.

### If something goes wrong on stage

- Backend unreachable → it's already Demo Mode; nothing hits the network.
- Camera won't bind → the error state offers "Back to form"; Demo Mode submits
  without photos.
- Fresh install with no history → the Home empty state is deliberate copy, not a
  blank screen.

---

## What I'd build next

- Room migrations (currently `fallbackToDestructiveMigration`, fine pre-1.0)
- Instrumented tests for the queue → sync → history path
- The backend's `/assess/full` comps and 24-month trend blocks are fetched but
  not yet surfaced on the phone; they'd fit as a fourth results panel
- Signed release build + R8 shrinking (the debug APK is ~60 MB, mostly the
  bundled ML Kit model)
