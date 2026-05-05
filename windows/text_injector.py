"""
Text injector — types text and simulates key presses into the active window.
Handles plain text, special keys, key combinations, and emoji.
"""

import time
from typing import List
from pynput.keyboard import Controller, Key


class TextInjector:
    """Types text and keys into the currently focused application."""

    def __init__(self, typing_delay: float = 0.002):
        self.keyboard = Controller()
        self.typing_delay = typing_delay

    def type_text(self, text: str) -> None:
        """Type a string, using pynput's native type() for speed and reliability."""
        if not text:
            return
        # Small warmup tap to ensure keyboard controller is active
        time.sleep(0.05)
        self.keyboard.type(text)

    def tap_key(self, key) -> None:
        """Press and release a single key."""
        self.keyboard.press(key)
        self.keyboard.release(key)

    def combo(self, *keys) -> None:
        """Press a key combination (e.g., ctrl+c)."""
        for key in keys:
            self.keyboard.press(key)
        for key in reversed(keys):
            self.keyboard.release(key)

    def send_backspace(self, count: int = 1) -> None:
        """Send backspace key events."""
        for _ in range(count):
            self.tap_key(Key.backspace)
            time.sleep(0.01)

    def send_delete_word(self, count: int = 1) -> None:
        """Send Ctrl+Backspace to delete previous words."""
        for _ in range(count):
            self.combo(Key.ctrl, Key.backspace)
            time.sleep(0.01)

    def execute_actions(self, final_text: str, actions: List[str], command_processor) -> None:
        """
        Execute commands and type the remaining text into the active window.
        """
        if not final_text and not actions:
            return

        # Let focus settle after hotkey release
        time.sleep(0.3)

        # Execute key-based commands first
        for action_name in actions:
            cmd = command_processor.get_command(action_name)
            if cmd and cmd.action == "key":
                if cmd.value == "backspace":
                    self.send_backspace(cmd.count)
                elif cmd.value == "ctrl_backspace":
                    self.send_delete_word(cmd.count)
                elif cmd.value == "ctrl_z":
                    self.combo(Key.ctrl, "z")
                elif cmd.value == "ctrl_y":
                    self.combo(Key.ctrl, "y")
                elif cmd.value == "ctrl_a":
                    self.combo(Key.ctrl, "a")
                elif cmd.value == "enter":
                    self.tap_key(Key.enter)
                elif cmd.value == "tab":
                    self.tap_key(Key.tab)

        # Type the final text
        if final_text:
            self.type_text(final_text)
