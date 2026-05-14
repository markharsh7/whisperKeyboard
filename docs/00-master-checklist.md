# Master Project Checklist

Last updated: 2026-05-15 | [agents.md](../agents.md)

**Progress:** All phases 1-8 complete ✅ — Project fully built with CI/CD

---

## Phase 1: Shared Core Library ✅

- [x] `core/config.yaml` — Single-source-of-truth configuration
- [x] `core/config.py` — YAML config loader with typed accessors
- [x] `core/commands.yaml` — 30+ voice commands (punctuation, editing, emoji, caps)
- [x] `core/commands.py` — `CommandProcessor` class (YAML→lookup→execute)
- [x] `core/text_post.py` — Devanagari transliteration, Hinglish corrections, spacing

**Status: Complete** (commit `11c3f86`)

---

## Phase 2: Windows Whisper Engine + Audio Pipeline ✅

- [x] `windows/whisper_engine.py` — faster-whisper wrapper (load, transcribe, unload)
- [x] `windows/audio_recorder.py` — sounddevice recorder + SilenceDetector
- [x] `windows/pipeline.py` — Orchestrator: record→transcribe→commands→post-process
- [x] `windows/test_pipeline.py` — Interactive test script
- [x] `windows/requirements.txt` — Dependencies (faster-whisper, pynput, pystray, etc.)
- [x] Model auto-download to `core/models/`

**Status: Complete** (commit `435cacf`)

---

## Phase 3: Windows System Tray + Hotkey ✅

- [x] `windows/tray_app.py` — pystray icon, right-click menu, lifecycle
- [x] `windows/hotkey_listener.py` — Global Win+Alt push-to-talk, debounce
- [x] System tray icon with idle/recording state indicator
- [x] Background model loading (tray appears immediately)
- [x] Mic auto-detection + level verification with warnings

**Status: Complete** (commit `14e9be9`)

---

## Phase 4: Windows Settings + Polish ✅

- [x] `windows/settings_window.py` — tkinter GUI (model, language, hotkey, mic)
- [x] `windows/text_injector.py` — pynput keyboard controller (type, combos, backspace)
- [x] Hotkey changed to Win+Alt, tray immediate display fix
- [x] Text commands produce visible output fix
- [x] Audio device selection fix
- [x] Auto-punctuation strip, emoji aliases, Devanagari transliteration
- [x] Typing reliability improvements
- [x] Default model: small + int8 for CPU speed

**Status: Complete** (commits `010f022`, `cee1fe5`, `5b9c8c5`, `9ef35ef`)

---

## Phase 5: Android On-Device Whisper Engine ✅

- [x] Set up `CMakeLists.txt` for whisper.cpp cross-compilation
- [x] Create JNI bridge (`whisper_jni.cpp`, `whisper_jni.h`)
- [x] Integrate whisper.cpp source as git submodule
- [x] Bundle/download model on first run (small model for mobile)
- [x] Link JNI with WhisperIME.kt → real transcription instead of placeholder
- [x] Handle audio format conversion (raw PCM → 16kHz WAV for whisper)
- [x] Build verified: compiles for arm64-v8a, armeabi-v7a, x86_64

**Status: Complete** — APK builds successfully.

---

## Phase 6: Android Command Processing + Text Injection ✅

- [x] Port `core/commands.yaml` parsing to Kotlin (`VoiceCommands.kt`, `CommandProcessor.kt`)
- [x] Implement `CommandProcessor` in Kotlin (match phrases, extract actions)
- [x] Port `core/text_post.py` logic (Hinglish corrections, capitalization, Devanagari transliteration) to Kotlin (`TextPostProcessor.kt`)
- [x] Implement real text injection via `InputConnection.commitText()`
- [x] Implement key-event commands (backspace, enter, tab, delete-word)
- [x] Proper error handling and user feedback (toasts)
- [x] End-to-end wire-up in WhisperIME.kt

**Status: Complete** — Build verified.

---

## Phase 7: Android Settings + Polish ✅

- [x] Real settings activity (model selection, language, recording config)
- [x] Haptic feedback on mic button press
- [x] Recording duration limit and silence auto-stop
- [x] Visual recording indicator (animate mic button / waveform)
- [x] ProGuard/R8 configuration for release builds
- [x] App icon and store metadata
- [x] SharedPreferences persistence
- [x] Model download/clear cache buttons
- [x] Release build with minification

**Status: Complete** — All Android phases done.


---

## Phase 8: Cross-Platform Sync & CI/CD ✅

- [x] GitHub Actions workflow for auto-build on push to master
- [x] Windows .exe build with PyInstaller
- [x] Android release APK build with Gradle
- [x] Auto-upload artifacts to GitHub Releases
- [x] Shared config files (config.yaml, commands.yaml) between platforms
- [x] Debug keystore generation for CI release builds
- [x] ProGuard rules for Android release builds

**Status: Complete** — Push to master triggers automatic build and release.
