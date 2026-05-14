# Android App — Development Plan

Last updated: 2026-05-15 | [Master Checklist](00-master-checklist.md)

Current state: **All phases complete** — on-device whisper, voice commands, text injection, settings, haptics, animations, release build all done.

---

## Current Implementation

| File | Status | Notes |
|------|--------|-------|
| `WhisperIME.kt` | Partial | IME service: onCreate, mic button, start/stop recording with `MediaRecorder`. Commits `"[Transcription placeholder]"` — 6 TODOs. |
| `SettingsActivity.kt` | Stub | Static text explaining how to enable keyboard. No real settings. |
| `keyboard.xml` | Done | Mic button (80dp, purple/red toggle) + "Tap to speak" label. |
| `method.xml` | Done | IME metadata (non-default, switchable, settings activity). |
| `build.gradle.kts` | Partial | References `CMakeLists.txt` that doesn't exist yet. Dependencies: AndroidX, Material. |
| `AndroidManifest.xml` | Done | IME service + launcher activity. Permissions: RECORD_AUDIO, INTERNET, VIBRATE. |

---

## Phase 5: On-Device Whisper Engine

**Goal:** Replace placeholder text with real transcription via whisper.cpp running natively.

### 5.1 — Set up Native Build System

- [x] Create `android/app/src/main/cpp/CMakeLists.txt`
- [x] Create JNI bridge files (`whisper_jni.h`, `whisper_jni.cpp`)

### 5.2 — Integrate whisper.cpp

- [x] Add whisper.cpp as git submodule
- [x] Configure CMake to build whisper.cpp + ggml
- [x] Model storage: download on first run to app internal storage

### 5.3 — Create Kotlin WhisperEngine Wrapper

- [x] Create `WhisperEngine.kt` with native method declarations
- [x] Load native library via `System.loadLibrary("whisper_jni")`
- [x] Handle model download with progress notification

### 5.4 — Wire into WhisperIME.kt

- [x] Initialize `WhisperEngine` in `onCreate()` (lazy-load model)
- [x] Switch from MediaRecorder to AudioRecord for raw PCM capture
- [x] Write WAV file from PCM data for whisper.cpp
- [x] Replace placeholder text with real transcription
- [x] Handle threading (background transcription, UI updates)

### 5.5 — Build & Test

- [x] CMake builds successfully for arm64-v8a, armeabi-v7a, x86_64
- [x] Kotlin compiles without errors
- [x] APK assembles successfully

---

## Phase 6: Command Processing + Text Injection

**Goal:** Port core Python command processor and post-processing to Kotlin, enable real text injection.

### 6.1 — CommandProcessor in Kotlin

- [x] Create `VoiceCommands.kt` — hardcoded command definitions (mirrors `core/commands.yaml`)
- [x] Create `CommandProcessor.kt` — phrase matching, action extraction, text/key command separation

### 6.2 — Text Post-Processing in Kotlin

- [x] Create `TextPostProcessor.kt`:
  - [x] Devanagari transliteration (full ITRANS scheme with schwa deletion)
  - [x] Hinglish word corrections
  - [x] `i` → `I` fix
  - [x] Sentence capitalization
  - [x] Spacing normalization

### 6.3 — Text Injection Implementation

- [x] Implement action execution in `WhisperIME.kt`:
  - [x] `commitText()` for plain text + emoji insertion
  - [x] `deleteSurroundingText()` for backspace/delete-word
  - [x] `sendKeyEvent()` for enter, tab
  - [x] Handle action ordering: key commands first, then text

### 6.4 — End-to-End Wire-up

- [x] In `stopRecordingAndTranscribe()`:
  ```kotlin
  val rawText = whisperEngine.transcribe(audioFile!!)
  val (processedText, actions) = commandProcessor.processText(rawText)
  val finalText = textPostProcessor.process(processedText)
  executeActions(actions)
  commitText(finalText)
  ```

---

## Phase 7: Settings, Polish & Release

### 7.1 — Settings Activity

- [x] Model selection (tiny/small/base) dropdown
- [x] Language selection (auto/en/hi)
- [x] Toggle: push-to-talk vs tap-to-talk
- [x] Haptics toggle
- [x] Persist settings with `SharedPreferences`
- [x] Model download button with progress
- [x] Clear model cache button

### 7.2 — UX Polish

- [x] Haptic feedback (`Vibrator` service) on mic tap
- [x] Animated recording indicator (pulsing mic button)
- [x] "Listening..." / "Processing..." / "Done" status text
- [x] Error toasts for failed recording/transcription
- [x] Keyboard height adjustment (minHeight 200dp)

### 7.3 — Release Readiness

- [x] ProGuard/R8 rules for whisper.cpp native libs
- [x] App icon (adaptive icon with mic foreground)
- [x] Release build configuration (minification, shrink resources)
- [x] Debug build with applicationIdSuffix

---

## Phase 8: CI/CD & Cross-Platform

### 8.1 — GitHub Actions Workflow

- [x] Create `.github/workflows/build.yml`
- [x] Trigger on push to master branch
- [x] Windows job: PyInstaller .exe build
- [x] Android job: Gradle release APK build
- [x] Auto-upload to GitHub Releases

### 8.2 — Windows Packaging

- [x] Create `windows/main.spec` for PyInstaller
- [x] Bundle core/ config files and commands.yaml
- [x] Include all Python dependencies

### 8.3 — Android Release Signing

- [x] Add signingConfigs to build.gradle.kts
- [x] CI generates debug keystore for release builds
- [x] Document how to add production keystore via secrets
