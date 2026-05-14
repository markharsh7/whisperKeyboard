# Whisper Keyboard — Agent Guide

## Project Overview

Cross-platform voice-typing keyboard app. Speak via hotkey/mic button → transcribed locally via Whisper → text typed into active field. Targets **Windows desktop** (Python) and **Android IME** (Kotlin + C++).

**Hardware targets:**
- Laptop: Intel i5 11th-gen, Iris Xe (CPU inference via `int8` quantized)
- Phone: OnePlus 13R (Snapdragon 8 Gen 3, on-device C++ inference)

## Tech Stack

| Layer | Tech |
|-------|------|
| Speech-to-text | `faster-whisper` (Python) / `whisper.cpp` (C++ for Android) |
| Audio capture | `sounddevice` (Win) / `MediaRecorder` (Android) |
| Text injection | `pynput` (Win) / `InputConnection` (Android IME) |
| Voice commands | YAML-defined (`core/commands.yaml`) |
| Text post-processing | Python (`core/text_post.py`) — Hinglish, transliteration, capitalization |
| Windows GUI | System tray (`pystray`) + settings (`tkinter`) |
| Android native | JNI bridge (CMake), Kotlin IME service |

## Architecture

```
core/           Shared logic: config, voice commands, text post-processing
windows/        Windows desktop app (Python) — push-to-talk via system tray
android/        Android keyboard IME (Kotlin) — tap-to-talk, on-device whisper
docs/           Project plans and checklists
```

**Data flow (both platforms):**
```
Audio capture → Whisper transcription → CommandProcessor → Text post-processing → Type into active field
```

## Agent Instructions

### Rule 1: Update Docs After Every Action
After **every** code change, feature addition, or bug fix, update the relevant file in `docs/`:
- `docs/00-master-checklist.md` — Toggle checkboxes, update phase status
- `docs/01-windows-status.md` — Update Windows component status
- `docs/02-android-plan.md` — Update Android phase progress

### Rule 2: Track Progress in Checklist Format
All docs use `- [x]` / `- [ ]` checklist format. Mark items complete immediately after finishing them.

### Rule 3: Read Before Edit
Always read a file before editing it. Follow existing code conventions, naming, and structure.

### Rule 4: Verify Changes
After making code changes, verify with available tests or linting. The Windows app test script is at `windows/test_pipeline.py`. Android builds with `./android/gradlew assembleDebug`.

### Rule 5: Commit Only When Asked
Never commit changes unless the user explicitly requests it.

## Quick Reference

| Action | Command |
|--------|---------|
| Run Windows app | `python windows/main.py` |
| Test Windows pipeline | `python windows/test_pipeline.py` |
| Build Android debug APK | `./android/gradlew assembleDebug` |
| Lint Python | `ruff check .` |
