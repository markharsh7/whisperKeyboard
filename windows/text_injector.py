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
        """Type a string character by character."""
        for char in text:
            self.keyboard.press(char)
            self.keyboard.release(char)
            time.sleep(self.typing_delay)

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
        Execute processed commands and type the remaining text.
        
        Actions from commands.py are applied in-place as we type:
        - For edit commands (backspace, delete word, undo): send key events before typing
        - For formatting commands (new line, tab, caps): insert text equivalents
        - For text commands (emoji, punctuation): type their values
        
        Since commands were already extracted from text by CommandProcessor,
        we just need to type the final text with any needed key events.
        """
        # For simplicity: type the processed final text directly
        # Editing commands like backspace are handled by sending key events
        # before the text is committed
        
        if not final_text and not actions:
            return

        # For editing commands (backspace, delete word, undo, redo, select all):
        # these modify the text field but don't produce visible text
        edit_actions = {
            "backspace": lambda c=1: self.send_backspace(c),
            "delete word": lambda c=1: self.send_delete_word(c),
            "undo": lambda: self.combo(Key.ctrl, "z"),
            "redo": lambda: self.combo(Key.ctrl, "y"),
            "select all": lambda: self.combo(Key.ctrl, "a"),
        }

        # Send edit actions first
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

        # Type the final text (includes emoji, punctuation, newlines already embedded)
        if final_text:
            self.type_text(final_text)
