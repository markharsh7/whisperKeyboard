"""
System tray application for Whisper Keyboard.
Provides tray icon, right-click menu, and recording state indicator.
"""

import os
import sys
import threading
import time
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pystray
from PIL import Image, ImageDraw, ImageFont

from core.commands import CommandProcessor
from windows.pipeline import Pipeline
from windows.hotkey_listener import HotkeyListener
from windows.text_injector import TextInjector


def _create_icon(color: str = "#6200EE", recording: bool = False) -> Image.Image:
    """Generate a simple mic/sound icon for the system tray."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if recording:
        # Red pulsing dot when recording
        draw.ellipse([16, 16, 48, 48], fill="#E53935")
    else:
        # Purple mic shape
        # Mic body
        draw.rounded_rectangle([24, 10, 40, 36], radius=6, fill=color)
        # Mic base
        draw.rounded_rectangle([18, 32, 46, 46], radius=4, fill=color)
        # Mic cable
        draw.rectangle([30, 46, 34, 56], fill=color)

    return img


class TrayApp:
    """Manages the system tray icon and application lifecycle."""

    def __init__(
        self,
        model_size: str = "small",
        language: str = "auto",
        hotkey: str = "cmd+alt",
        compute_type: str = "auto",
        device: str = "cpu",
    ):
        self.model_size = model_size
        self.language = language
        self.hotkey_str = hotkey
        self.compute_type = compute_type
        self.device = device

        # Core components
        self.pipeline: Pipeline = None
        self.hotkey: HotkeyListener = None
        self.injector = TextInjector()
        self.command_processor = CommandProcessor()

        # State
        self.is_recording = False
        self.is_listening = False
        self.tray_icon: pystray.Icon = None
        self._status_text = "Ready"

        # Recording coordination
        self._recording_event = threading.Event()
        self._recording_thread: threading.Thread = None

    def setup(self) -> None:
        """Initialize pipeline and hotkey listener (without starting tray event loop)."""
        self._update_status("Loading Whisper model...")
        self.pipeline = Pipeline(
            model_size=self.model_size,
            language=self.language,
            compute_type=self.compute_type,
            device=self.device,
            enable_commands=True,
            enable_post_processing=True,
            on_status=self._update_status,
        )
        self.pipeline.ensure_loaded()

        self.hotkey = HotkeyListener(
            hotkey=self.hotkey_str,
            on_press=self._on_hotkey_press,
            on_release=self._on_hotkey_release,
            on_status=self._update_status,
        )

    def run(self) -> None:
        """Start the tray application (blocks until exit)."""
        idle_icon = _create_icon(color="#6200EE", recording=False)
        self._recording_icon = _create_icon(color="#E53935", recording=True)

        self.tray_icon = pystray.Icon(
            "whisper_keyboard",
            idle_icon,
            "Whisper Keyboard - Starting...",
            menu=self._build_menu(),
        )
        print("[Whisper Keyboard] Tray icon created — check system tray / overflow (^)")

        # Load model in background so tray appears immediately
        threading.Thread(target=self._load_in_background, daemon=True).start()

        self.tray_icon.run()

    def _load_in_background(self):
        """Load Whisper model in background thread, then start hotkey."""
        try:
            self._update_status("Loading Whisper model...")
            self.setup()
            self._update_status("Ready")
            print("[Whisper Keyboard] Ready — hold Win+Alt to speak")
            self.is_listening = True
            self.hotkey.start()
        except Exception as e:
            self._update_status(f"Startup error: {e}")
            print(f"[Whisper Keyboard] Startup failed: {e}")

    def _build_menu(self) -> pystray.Menu:
        """Build the right-click context menu."""
        return pystray.Menu(
            pystray.MenuItem(
                "Listening: ON",
                self._toggle_listening,
                checked=lambda item: self.is_listening,
            ),
            pystray.MenuItem(
                "Language: Auto",
                self._cycle_language,
            ),
            pystray.MenuItem(
                "Settings",
                self._open_settings,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Exit",
                self._exit_app,
            ),
        )

    def _toggle_listening(self, icon, item) -> None:
        """Toggle hotkey listening on/off."""
        if self.is_listening:
            self.hotkey.stop()
            self.is_listening = False
        else:
            self.hotkey.start()
            self.is_listening = True

    def _cycle_language(self, icon, item) -> None:
        """Cycle through language modes."""
        languages = ["auto", "en", "hi"]
        current = self.language
        idx = languages.index(current)
        self.language = languages[(idx + 1) % len(languages)]
        self.pipeline.language = self.language

    def _open_settings(self, icon, item) -> None:
        """Open the settings window."""
        # Import locally to avoid circular dependency
        from windows.settings_window import open_settings
        open_settings(
            current_model=self.model_size,
            current_language=self.language,
            current_hotkey=self.hotkey_str,
            on_save=self._on_settings_saved,
        )

    def _on_settings_saved(self, model: str, language: str, hotkey: str) -> None:
        """Handle settings changes."""
        changed = False
        if model != self.model_size:
            self.model_size = model
            changed = True
        if language != self.language:
            self.language = language
            self.pipeline.language = language
        if hotkey != self.hotkey_str:
            self.hotkey.stop()
            self.hotkey_str = hotkey
            self.hotkey = HotkeyListener(
                hotkey=hotkey,
                on_press=self._on_hotkey_press,
                on_release=self._on_hotkey_release,
                on_status=self._update_status,
            )
            self.hotkey.start()
        if changed:
            self._reload_pipeline()

    def _reload_pipeline(self) -> None:
        """Reload pipeline with new model settings."""
        self.pipeline = Pipeline(
            model_size=self.model_size,
            language=self.language,
            compute_type=self.compute_type,
            device=self.device,
            enable_commands=True,
            enable_post_processing=True,
            on_status=self._update_status,
        )
        self.pipeline.ensure_loaded()

    def _on_hotkey_press(self) -> None:
        """Hotkey pressed: start recording."""
        if self.is_recording:
            return

        self.is_recording = True
        self._update_tray_icon(recording=True)

        # Start recording in a thread
        self._recording_event.clear()
        self.pipeline.recorder.start_recording()

    def _on_hotkey_release(self) -> None:
        """Hotkey released: stop recording and transcribe."""
        if not self.is_recording:
            return

        self.is_recording = False
        self._update_tray_icon(recording=False)

        # Stop recording
        audio_path = self.pipeline.recorder.stop_recording()
        if audio_path is None:
            self._update_status("No audio captured")
            return

        # Transcribe in background to not block hotkey
        threading.Thread(
            target=self._transcribe_and_type,
            args=(audio_path,),
            daemon=True,
        ).start()

    def _transcribe_and_type(self, audio_path: str) -> None:
        """Transcribe audio and type result into active window."""
        try:
            self._update_status("Transcribing...")

            result = self.pipeline.engine.transcribe(
                audio_path,
                language=None if self.language == "auto" else self.language,
            )

            raw_text = result["text"]
            processed_text, actions = self.command_processor.process_text(raw_text)

            from core.text_post import post_process
            final_text = post_process(processed_text, self.language)

            if final_text or actions:
                self._update_status("Done")
                print(f"[Whisper] {final_text!r}" + (f"  cmds={actions}" if actions else ""))
                time.sleep(0.1)
                self.injector.execute_actions(final_text, actions, self.command_processor)
            else:
                self._update_status("No speech detected")

            # Clean up temp file
            try:
                os.remove(audio_path)
            except OSError:
                pass

        except Exception as e:
            self._update_status(f"Error: {e}")

    def _update_tray_icon(self, recording: bool) -> None:
        """Update tray icon to reflect recording state."""
        if self.tray_icon:
            self.tray_icon.icon = self._recording_icon if recording else _create_icon()

    def _update_status(self, msg: str) -> None:
        """Update status text (shown in tray tooltip)."""
        self._status_text = msg
        if self.tray_icon:
            self.tray_icon.title = f"Whisper Keyboard - {msg}"

    def _exit_app(self, icon, item) -> None:
        """Clean exit."""
        if self.hotkey:
            self.hotkey.stop()
        if self.tray_icon:
            self.tray_icon.stop()
