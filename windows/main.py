"""
Whisper Keyboard — Windows Entry Point.
Starts the system tray application with push-to-talk voice typing.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import load_config, get_whisper_config, get_hotkey_config
from windows.tray_app import TrayApp


def main():
    """Main entry point for the Windows Whisper Keyboard app."""
    print("Whisper Keyboard — Windows")
    print("Starting system tray app...")

    # Load configuration
    try:
        config = load_config()
        whisper_cfg = get_whisper_config(config)
        hotkey_cfg = get_hotkey_config(config)
    except Exception:
        whisper_cfg = {"model_size": "small"}
        hotkey_cfg = {"key": "cmd+alt"}

    model_size = whisper_cfg.get("model_size", "small")
    hotkey = hotkey_cfg.get("key", "ctrl+shift+v")

    # Start tray application
    app = TrayApp(
        model_size=model_size,
        language="auto",
        hotkey=hotkey,
        compute_type="auto",
        device="cpu",
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
