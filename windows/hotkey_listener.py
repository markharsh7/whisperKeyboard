"""
Global hotkey listener for push-to-talk.
Detects press-and-hold (start recording) and release (stop + transcribe).
"""

import threading
import time
from typing import Callable, Optional
from pynput import keyboard


class HotkeyListener:
    """Listens for a global hotkey with press-to-start, release-to-stop."""

    def __init__(
        self,
        hotkey: str = "ctrl+shift+v",
        on_press: Optional[Callable[[], None]] = None,
        on_release: Optional[Callable[[], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize hotkey listener.
        
        Args:
            hotkey: Key combination like "ctrl+shift+v" or "alt+r".
            on_press: Called when hotkey is pressed (start recording).
            on_release: Called when hotkey is released (stop + transcribe).
            on_status: Called with status messages.
        """
        self.hotkey_str = hotkey
        self.on_press = on_press
        self.on_release = on_release
        self.on_status = on_status

        self._keys = self._parse_hotkey(hotkey)
        self._pressed_keys = set()
        self._hotkey_held = False
        self._listener: Optional[keyboard.Listener] = None
        self._running = False
        self._debounce_time = 0
        self._debounce_delay = 0.3  # seconds

    def _parse_hotkey(self, hotkey: str) -> set:
        """Parse a hotkey string like 'ctrl+shift+v' into a set of key enum values."""
        parts = hotkey.lower().strip().split("+")
        keys = set()

        for part in parts:
            part = part.strip()
            if part == "ctrl" or part == "control":
                keys.add(keyboard.Key.ctrl_l)
            elif part == "shift":
                keys.add(keyboard.Key.shift)
            elif part == "alt":
                keys.add(keyboard.Key.alt_l)
            elif part == "cmd" or part == "win":
                keys.add(keyboard.Key.cmd)
            elif len(part) == 1:
                # Single character key
                keys.add(part)
            else:
                # Function keys, etc.
                keys.add(part)

        return keys

    def start(self) -> None:
        """Start listening for the hotkey in a background thread."""
        if self._running:
            return

        self._running = True
        self._listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._listener.daemon = True
        self._listener.start()
        self._status(f"Hotkey listener started ({self.hotkey_str})")

    def stop(self) -> None:
        """Stop the hotkey listener."""
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._status("Hotkey listener stopped")

    def _on_key_press(self, key):
        """Called when any key is pressed."""
        if not self._running:
            return

        try:
            # Normalize the key
            k = self._normalize_key(key)
            self._pressed_keys.add(k)

            # Check if the full hotkey combination is held
            if self._keys.issubset(self._pressed_keys) and not self._hotkey_held:
                # Debounce: prevent triggering again within debounce window
                now = time.time()
                if now - self._debounce_time > self._debounce_delay:
                    self._hotkey_held = True
                    self._status("Recording...")
                    if self.on_press:
                        self.on_press()
        except Exception as e:
            self._status(f"Hotkey error: {e}")

    def _on_key_release(self, key):
        """Called when any key is released."""
        if not self._running:
            return

        try:
            k = self._normalize_key(key)
            self._pressed_keys.discard(k)

            # If hotkey was held and a required key was released, trigger stop
            if self._hotkey_held and not self._keys.issubset(self._pressed_keys):
                self._hotkey_held = False
                self._debounce_time = time.time()
                self._status("Processing...")
                if self.on_release:
                    self.on_release()
        except Exception as e:
            self._status(f"Hotkey error: {e}")

    def _normalize_key(self, key):
        """Normalize pynput key objects to consistent identifiers."""
        if hasattr(key, "char") and key.char:
            return key.char.lower()
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            return keyboard.Key.ctrl_l
        if key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            return keyboard.Key.shift
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            return keyboard.Key.alt_l
        return key

    def _status(self, msg: str) -> None:
        if self.on_status:
            self.on_status(msg)
