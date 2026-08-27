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
ondevice/      LOCAL inference — the on-device half of the pipeline
  PhotoGate    blur variance + ML Kit scene labelling (bundled in APK)
  LocalLlm     Gemma-class LLM on the GPU/NPU via MediaPipe (side-loaded)
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
| **GPU / NPU** | **MediaPipe LLM Inference — Gemma 3 1B, quantised** | `ondevice/LocalLlm.kt` |
| GPS | `FusedLocationProviderClient` | `location/LocationProvider.kt` |
| Microphone | `SpeechRecognizer` (on-device on API 31+), English / हिन्दी / मराठी | `speech/VoiceCapture.kt` |

Two models run locally, and they do different jobs: `PhotoGate` screens frames
before upload, `LocalLlm` turns speech into structured fields with no network.

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

## On-device LLM

The voice-to-fields step runs a quantised open-weights model (Gemma 3 1B class)
on the phone's GPU/NPU through MediaPipe's LLM Inference API. It is the second
on-device model in the app, alongside the ML Kit labeller in `PhotoGate`.

**Why it is not a gimmick:** the offline queue already let an officer *submit*
without signal, but until now they still had to type the property in by hand,
because parsing the spoken description round-tripped to `/api/v1/chat`. In a
basement that step was dead — the exact scenario the queue exists for. The local
model closes that loop.

`interpret()` is two-stage: on-device first (no round trip, works with the radio
off), cloud extractor as fallback. The capture screen tells the officer which
one ran rather than leaving them to guess whether their data left the handset.

### Installing the model

The model is **not in the APK and not in this repo** — it is 0.5-1.3 GB and
licence-gated.

```bash
# once per device; survives app reinstalls
./scripts/push-model.sh ~/Downloads/Gemma3-1B-IT_multi-prefill-seq_q4_ekv2048.task
```

Get the file by accepting the Gemma licence at
`huggingface.co/litert-community/Gemma3-1B-IT` and downloading a `.task` build.
Do this **before the event or during Green Light** — it is a slow download and a
slow USB push.

`LocalLlm.MODEL_SEARCH_PATHS` lists where the app looks, in priority order.

### It cannot break the demo

Every failure — absent file, truncated push, OOM, unsupported backend, slow
inference — degrades silently to `LlmState.Unavailable` and the cloud path. The
app is fully functional with no model present. Nothing requires it.

Confirm it loaded: the voice card shows **LLM ON-DEVICE**. Debug with
`adb logcat -s LocalLlm:*`.

---

## Red Light / Green Light plan

The event splits build time 55% **Red Light (phone only, no laptop)** / 45%
**Green Light (phone + laptop via Office Kit)**. 30 hours gives ~16.5h Red,
~13.5h Green.

### The honest constraint

**You cannot realistically run Gradle Android builds on the phone.** AGP needs
aapt2/d8 native binaries; Termux builds exist but are fragile, and burning Red
Light hours fighting a toolchain produces nothing demoable. AIDE does not
support Kotlin 2.0 or Compose.

So this plan does not depend on compiling during Red Light. **Red Light does not
require compiling — it requires the work to happen on the phone**, and there is
a lot of real work that is genuinely phone-native:

| Phase | Tooling on the phone | What actually gets done |
|---|---|---|
| Red | Acode / Squircle IDE, or Termux + `nvim` | Writing Kotlin and Compose source, editing copy, palette and layout values |
| Red | Termux + `git` | Branching, committing, pushing — full history from the handset |
| Red | The app itself | **All device testing.** Camera framing, GPS drift indoors, Marathi recognition accuracy, on-device LLM latency, blur-threshold tuning against real walls |
| Red | Termux + `curl` | Hitting the deployed backend directly to verify contracts |
| Green | Laptop | Compiling, dependency surgery, `adb push` of the model, install cycles, PDF layout checks |

Device testing is the part worth protecting. It **can only be done on the
phone**, it is what tunes `PhotoGate` thresholds and the LLM prompt to reality,
and it generates exactly the telemetry criterion 3 measures.

### Hour-by-hour

| Hours | Light | Work |
|---|---|---|
| 0-1 | Green | Check in. Clone, `./gradlew assembleDebug`, `installDebug`, `push-model.sh`. Get a working APK on the loaner **before** Red Light starts. |
| 1-3 | Red | Device-test everything already built. Camera in real light, GPS indoors, voice in all three languages. Write findings straight into the repo as notes. |
| 3-6 | Red | Tune on-device thresholds from what you just measured: `BLUR_REJECT` / `BLUR_WARN`, the LLM prompt, locality snapping. Source edits on-phone. |
| 6-8 | Green | Compile the tuned values, reinstall, re-measure. First Office Kit file hops. |
| 8-12 | Red | Build out UI and copy on-phone: results polish, empty states, error copy, the fraud banner wording. All source-level, no compile needed. |
| 12-15 | Green | Compile everything from 8-12. Fix what broke. Run `./gradlew testDebugUnitTest`. Export a PDF and pull it across via Office Kit. |
| 15-19 | Red | **Sleep window** for a 3-person team, or on-phone rehearsal. Run the demo end-to-end on the handset repeatedly. Time it. |
| 19-22 | Green | Final integration. Clean build, install from scratch, verify with no history present. |
| 22-25 | Red | Rehearse on the phone. Airplane-mode drill. Fraud-scenario drill. Get it under 4 minutes reliably. |
| 25-28 | Green | Buffer for whatever broke. Re-export artefacts to the laptop for the slide deck via Office Kit. |
| 28-30 | Red | Final phone-only rehearsal. Charge. Do not touch the code. |

**Two rules that matter more than the schedule:**

1. **Get a working APK on the loaner in hour 0-1.** Everything else is optional;
   an app that will not install at hour 29 is a zero.
2. **Freeze code at hour 28.** The last two hours are rehearsal, not building.

### Office Kit (criterion 5, 10%, telemetry-scored)

Scored on **actual bridge usage during the 30 hours**, not on code. Natural
reasons to use it, spread across the event rather than once at the end:

- Every Green Light compile sends an APK across to the phone
- The model push
- PDF/JSON exports pulled back for the slide deck
- Clipboard sync for logcat traces while debugging on-phone
- Screen mirror while rehearsing, so a teammate sees what you tap

---

## Rehearsed demo script — 4 minutes, live on the loaner iQOO 15

Setup before you walk up: Demo Mode **on**, model pushed, app on Home, phone
mirrored to the projector via Office Kit, airplane mode **off**.

| Time | You tap / say | Criterion hit |
|---|---|---|
| **0:00-0:25** | Home screen on the projector. *"Loan Against Property is a nine-lakh-crore-rupee market in India. Every one of those loans needs its collateral valued — and today that takes two to three weeks and a physical visit from a panel valuer. We collapse it to under a minute, on the phone the officer already carried to the site."* | Novelty 20% |
| **0:25-0:45** | Tap **Start field assessment**. GPS chip fills itself in; locality auto-selects Baner. Type `LAP-2026-04417`. *"Location is captured the second the screen opens — the officer never types it. It also lets our server skip geocoding, so the answer comes back faster. And it is filed against a real loan number, because an officer does six of these a day."* | Phone use 15% · Product 30% |
| **0:45-1:15** | Tap **मराठी**, then **Speak**. Say the property in Marathi. Watch the fields fill. Point at the **LLM ON-DEVICE** pill. *"That was Marathi — our officers are in Pune, they do not dictate in English. And here is the part to notice: that parsing just ran on this phone's NPU. A one-billion-parameter Gemma model, quantised, running locally. No network."* | **Phone use 15% + local-model bonus** |
| **1:15-1:45** | **Open camera.** Deliberately capture a blurred frame, get the red on-device rejection. Then a sharp exterior and interior. *"Every frame is screened on-device before anything uploads — blur variance plus a scene classifier, about two hundred milliseconds. A bad photo never costs a thirty-second round trip to a vision model that would only tell us it is a bad photo."* | Phone use 15% · Depth 15% |
| **1:45-2:15** | Tap **Run the fraud-detection scenario**. Results screen lands. *"One point nine four crore. Confidence eighty-seven percent. But look at the red banner."* | Product 30% |
| **2:15-2:55** | Point at the fraud banner, then scroll to LTV. *"The borrower declared a three-BHK apartment. The vision model looked at the photographs and saw an industrial warehouse — roller shutter, roof trusses, pallet racking. Two high-severity flags. And the LTV engine has already cut the sanction from seventy percent to forty, pending physical re-verification. That is caught before disbursal, not during recovery two years later."* | **Novelty 20% · Product 30%** |
| **2:55-3:20** | Turn on **airplane mode**. Run another assessment — it queues. Turn it off — it submits itself. *"A field officer in basement parking is the normal case, not an edge case. Nothing is ever lost — and because the model is on-device, they can still fill the form by voice down there."* | Product 30% · Depth 15% |
| **3:20-3:40** | Tap **Export assessment**. Drag the PDF to the laptop over Office Kit, open it on the projector. *"Straight to the credit team as a one-page memo."* | **Office Kit 10%** |
| **3:40-4:00** | Back to Home. *"Two to three weeks, down to under a minute. Fraud caught before the money goes out. Running on the officer's own phone, offline, in their own language. That is PropIQ Field."* | Presentation 10% |

### Contingencies — rehearse these too

| If | Then |
|---|---|
| Venue wifi dies | Nothing happens. Demo Mode never touches the network. |
| Model did not load | The pill reads SPEECH ON-DEVICE instead. Skip the NPU line; do not draw attention to it. Everything else is identical. |
| Voice mis-hears in Marathi | Tap **Use sample** and carry on — *"I will type it, in the interest of time."* |
| Camera will not bind | The error state offers **Back to form**; Demo Mode submits without photos. |
| Projector or mirror drops | Keep talking to the phone in your hand. The pitch does not depend on the mirror. |

See [PITCH.md](PITCH.md) for the full narrative version.

---

## Testing

```bash
./gradlew testDebugUnitTest
```

33 unit tests over the logic where a bug is silent rather than loud — Indian
digit grouping, form bounds mirrored from the backend's Pydantic Fields, retry
routing, fraud-flag detection, and locality-table drift.

---

## What I would build next

- Room migrations (currently `fallbackToDestructiveMigration`, fine pre-1.0)
- Instrumented tests for the queue → sync → history path
- The backend's `/api/v1/rag/query` returns cited RBI policy snippets; a field
  officer arguing an LTV cap with a branch manager would want that on the phone
- Signed release build + R8 (debug APK is ~60 MB, mostly the ML Kit model)
