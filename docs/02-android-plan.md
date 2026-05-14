# Android App — Development Plan

Last updated: 2026-05-15 | [Master Checklist](00-master-checklist.md)

Current state: **Scaffold** — recording works, transcription is a placeholder, no on-device whisper.

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

- [ ] Create `android/app/src/main/cpp/CMakeLists.txt`
  - Target: whisper.cpp library + JNI bridge
  - ABI filters: `arm64-v8a` (primary for OnePlus 13R), `armeabi-v7a`, `x86_64` (emulator)
  - C++17 standard
  - Link against whisper.cpp + ggml
- [ ] Create JNI bridge files:
  - `android/app/src/main/cpp/whisper_jni.h` — Function declarations
  - `android/app/src/main/cpp/whisper_jni.cpp` — Implementation
    - `Java_com_whisperkeyboard_WhisperEngine_nativeInit(modelPath)` — Load model
    - `Java_com_whisperkeyboard_WhisperEngine_nativeTranscribe(audioPath)` — Transcribe
    - `Java_com_whisperkeyboard_WhisperEngine_nativeDestroy()` — Cleanup

### 5.2 — Integrate whisper.cpp

- [ ] Add whisper.cpp as git submodule: `android/app/src/main/cpp/whisper.cpp/`
- [ ] Configure CMake to build whisper.cpp + ggml
- [ ] Choose model: `ggml-small.bin` (~484 MB) or `ggml-tiny.bin` (~150 MB) for mobile
- [ ] Model storage strategy:
  - Option A: Bundle in APK assets (inflates APK size)
  - Option B: Download on first run from HuggingFace to app internal storage **(recommended)**

### 5.3 — Create Kotlin WhisperEngine Wrapper

- [ ] Create `WhisperEngine.kt`:
  ```kotlin
  class WhisperEngine(context: Context) {
      external fun nativeInit(modelPath: String): Boolean
      external fun nativeTranscribe(audioPath: String, language: String?): String
      external fun nativeDestroy()
      
      fun ensureModel(): File // Download if not present
      fun transcribe(audioFile: File, language: String?): String
  }
  ```
- [ ] Load native library via `System.loadLibrary("whisper_jni")`
- [ ] Handle model download with progress notification

### 5.4 — Wire into WhisperIME.kt

- [ ] Initialize `WhisperEngine` in `onCreate()` (lazy-load model after download)
- [ ] Replace `commitText("[Transcription placeholder]")` in `stopRecordingAndTranscribe()` with:
  ```kotlin
  val result = whisperEngine.transcribe(audioFile!!, language = null)
  commitText(result)
  ```
- [ ] Handle audio format: MediaRecorder records AAC → convert to 16kHz PCM WAV before passing to whisper
- [ ] Show "Transcribing..." toast/progress while processing

### 5.5 — Build & Test

- [ ] Verify CMake builds successfully with `gradlew assembleDebug`
- [ ] Test on OnePlus 13R (Snapdragon 8 Gen 3, arm64-v8a)
- [ ] Measure transcription latency (target: <1s for short utterances with tiny model)
- [ ] Test with Hinglish speech samples

---

## Phase 6: Command Processing + Text Injection

**Goal:** Port core Python command processor and post-processing to Kotlin, enable real text injection.

### 6.1 — CommandProcessor in Kotlin

- [ ] Create `CommandProcessor.kt`:
  - Parse `commands.yaml` at runtime (using a YAML library like `snakeyaml` or hardcode commands in Kotlin)
  - Index commands by phrase + aliases (same logic as `core/commands.py`)
  - `processText(raw: String): Pair<String, List<String>>` — returns cleaned text + action list
  - Support: text-type commands (punctuation, emoji), key-type commands (backspace, enter, undo)

### 6.2 — Text Post-Processing in Kotlin

- [ ] Create `TextPostProcessor.kt`:
  - Port `core/text_post.py` logic:
    - Devanagari transliteration (full ITRANS scheme with schwa deletion)
    - Hinglish word corrections
    - `i` → `I` fix
    - Sentence capitalization
    - Spacing normalization

### 6.3 — Text Injection Implementation

- [ ] Implement action execution in `WhisperIME.kt`:
  - `commitText()` for plain text + emoji insertion
  - `deleteSurroundingText()` for backspace/delete-word
  - `sendKeyEvent()` for enter, tab, ctrl combos
  - Handle action ordering: key commands first, then text

### 6.4 — End-to-End Wire-up

- [ ] In `stopRecordingAndTranscribe()`:
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

- [ ] Model selection (tiny/small/base) dropdown
- [ ] Language selection (auto/en/hi)
- [ ] Toggle: push-to-talk vs tap-to-talk
- [ ] Mic sensitivity / silence threshold
- [ ] Persist settings with `SharedPreferences`

### 7.2 — UX Polish

- [ ] Haptic feedback (`Vibrator` service) on mic tap
- [ ] Animated recording indicator (pulsing mic or waveform)
- [ ] "Listening..." / "Processing..." / "Done" status text
- [ ] Error toasts for failed recording/transcription
- [ ] Keyboard height adjustment

### 7.3 — Release Readiness

- [ ] ProGuard/R8 rules for whisper.cpp native libs
- [ ] App icon + branding
- [ ] Signed release build configuration
- [ ] Google Play / sideload distribution plan
