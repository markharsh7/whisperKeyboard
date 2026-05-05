"""
Whisper Keyboard — Windows Entry Point.
Starts the system tray application with push-to-talk voice typing.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import load_config, get_whisper_config, get_hotkey_config, get_audio_config
from windows.tray_app import TrayApp
from windows.audio_recorder import AudioRecorder


def main():
    """Main entry point for the Windows Whisper Keyboard app."""
    print("Whisper Keyboard — Windows")
    print("Starting system tray app...")

    # Load configuration
    try:
        config = load_config()
        whisper_cfg = get_whisper_config(config)
        hotkey_cfg = get_hotkey_config(config)
        audio_cfg = get_audio_config(config)
    except Exception:
        whisper_cfg = {"model_size": "small"}
        hotkey_cfg = {"key": "cmd+alt"}
        audio_cfg = {}

    model_size = whisper_cfg.get("model_size", "small")
    hotkey = hotkey_cfg.get("key", "cmd+alt")
    input_device = audio_cfg.get("input_device", None)
    initial_prompt = whisper_cfg.get("initial_prompt", "") or None

    # Auto-detect best mic if not configured
    if input_device is None:
        best = AudioRecorder.find_best_mic()
        if best is not None:
            name = AudioRecorder.get_device_name(best)
            print(f"Auto-selected mic: {name} (ID {best})")
            input_device = best

    # Start tray application
    app = TrayApp(
        model_size=model_size,
        language="auto",
        hotkey=hotkey,
        compute_type="auto",
        device="cpu",
        input_device=input_device,
        initial_prompt=initial_prompt,
    )

    try:
        app.run()
    except KeyboardInterrupt:
        print("\nExiting.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
