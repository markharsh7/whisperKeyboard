# Windows App — Component Status

Last updated: 2026-05-15 | [Master Checklist](00-master-checklist.md)

Current state: **Fully functional** — push-to-talk voice typing with commands and post-processing.

---

## Component Status

### `windows/main.py` ✅
Entry point. Loads config, auto-detects microphone, creates TrayApp.

### `windows/tray_app.py` ✅
System tray lifecycle manager. Creates icon (purple idle / red dot recording), builds right-click menu (toggle listening, cycle language auto/en/hi, settings, exit). Hotkey handlers start/stop recording. Background transcription thread types results into active window.

### `windows/pipeline.py` ✅
Orchestrator connecting recorder → whisper engine → command processor → post-processing. `record_and_transcribe()` with optional silence auto-stop.

### `windows/audio_recorder.py` ✅
`sounddevice` InputStream for low-latency recording. Real-time RMS level callback. `SilenceDetector` for auto-stop. Auto-detects best mic (filters out Stereo Mix). Mic level check with warnings.

### `windows/whisper_engine.py` ✅
`faster-whisper` wrapper. Auto-download models to `core/models/`. Supports all sizes (tiny→turbo), VAD filtering, beam search, initial_prompt for Hinglish biasing.

### `windows/hotkey_listener.py` ✅
Global `pynput` hotkey (default: Win+Alt). Push-to-talk mode. Windows key suppression (prevents Start menu opening). 300ms debounce.

### `windows/text_injector.py` ✅
`pynput.keyboard.Controller` types text, sends key combos (Ctrl+Z/Y/A), backspace, delete-word, enter, tab. 300ms focus-settle delay before typing.

### `windows/settings_window.py` ✅
tkinter settings dialog: model dropdown (tiny/base/small/medium/turbo), language radio (auto/en/Hinglish), hotkey capture button, microphone dropdown from device list.

### `windows/test_pipeline.py` ✅
Interactive test: Enter to start/stop recording, displays raw + final text with language and commands. Also supports file transcription via CLI arg.

### `windows/requirements.txt` ✅
8 packages: faster-whisper, pynput, pystray, Pillow, PyYAML, sounddevice, numpy, scipy.

---

## Remaining / Possible Improvements

- [ ] Package as standalone .exe (PyInstaller / Nuitka) for easier distribution
- [ ] Auto-start with Windows option
- [ ] Visual waveform indicator during recording
- [ ] Toggle mode (tap to start/stop) as alternative to hold mode
- [ ] Keyboard shortcut to type last transcription again
- [ ] Per-app language profiles
