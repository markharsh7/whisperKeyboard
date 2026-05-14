# Master Project Checklist

Last updated: 2026-05-15 | [agents.md](../agents.md)

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

## Phase 5: Android On-Device Whisper Engine ⬜

- [ ] Set up `CMakeLists.txt` for whisper.cpp cross-compilation
- [ ] Create JNI bridge (`whisper_jni.cpp`, `whisper_jni.h`)
- [ ] Integrate whisper.cpp source as submodule or vendored dependency
- [ ] Bundle/download model on first run (small model for mobile)
- [ ] Link JNI with WhisperIME.kt → real transcription instead of placeholder
- [ ] Handle audio format conversion (AAC → 16kHz PCM for whisper)
- [ ] Test on OnePlus 13R device

**Status: TODO** — See `docs/02-android-plan.md` for detailed breakdown.

---

## Phase 6: Android Command Processing + Text Injection ⬜

- [ ] Port `core/commands.yaml` parsing to Kotlin
- [ ] Implement `CommandProcessor` in Kotlin (match phrases, extract actions)
- [ ] Port `core/text_post.py` logic (Hinglish corrections, capitalization) to Kotlin
- [ ] Implement real text injection via `InputConnection.commitText()`
- [ ] Implement key-event commands (backspace, enter, undo, etc.)
- [ ] Proper error handling and user feedback (toasts)

**Status: TODO** — See `docs/02-android-plan.md` for detailed breakdown.

---

## Phase 7: Android Settings + Polish ⬜

- [ ] Real settings activity (model selection, language, recording config)
- [ ] Haptic feedback on mic button press
- [ ] Recording duration limit and silence auto-stop
- [ ] Visual recording indicator (animate mic button / waveform)
- [ ] ProGuard/R8 configuration for release builds
- [ ] App icon and store metadata

**Status: TODO** — See `docs/02-android-plan.md` for detailed breakdown.

---

## Phase 8: Cross-Platform Sync (Future) ⬜

- [ ] Unify config files between platforms
- [ ] Share commands.yaml between platforms
- [ ] Sync model files between platforms
- [ ] Consistent post-processing behavior across platforms
