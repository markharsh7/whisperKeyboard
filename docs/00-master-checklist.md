# Master Project Checklist

Last updated: 2026-05-15 | [agents.md](../agents.md)

**Progress:** Phases 1-4 complete ✅ | Phase 8 CI/CD ✅ | Android phases 5-7 deferred ⏸️

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

## Phase 5: Android — Deferred ⏸️

Android implementation (whisper.cpp JNI, IME service, settings) is deferred. Code remains in the `android/` directory for future use.

## Phase 6: Android Commands — Deferred ⏸️

## Phase 7: Android Settings — Deferred ⏸️


---

## Phase 8: CI/CD ✅

- [x] GitHub Actions workflow for auto-build on push to master
- [x] Windows .exe build with PyInstaller
- [x] Auto-upload artifacts to GitHub Releases
