"""
Settings window for Whisper Keyboard.
Simple tkinter GUI for configuring model, language, hotkey, and audio device.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, List, Dict
from pynput import keyboard as pynput_keyboard

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from windows.audio_recorder import AudioRecorder


class SettingsWindow:
    """Settings dialog for Whisper Keyboard configuration."""

    def __init__(
        self,
        current_model: str = "small",
        current_language: str = "auto",
        current_hotkey: str = "cmd+alt",
        current_input_device: Optional[int] = None,
        on_save: Optional[Callable[[str, str, str, int], None]] = None,
    ):
        self.current_model = current_model
        self.current_language = current_language
        self.current_hotkey = current_hotkey
        self.current_input_device = current_input_device
        self.on_save = on_save

        self._capturing_hotkey = False
        self._hotkey_keys = set()

        # Load device list
        self._devices: List[Dict] = AudioRecorder.list_devices()
        self._device_map = {"System Default (auto-detect)": None}
        for d in self._devices:
            label = f"{d['name']} [{d['id']}]"
            self._device_map[label] = d["id"]

        self._build_window()

    def _build_window(self) -> None:
        self.root = tk.Tk()
        self.root.title("Whisper Keyboard Settings")
        self.root.geometry("400x400")
        self.root.resizable(False, False)

        # Center on screen
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Model selector
        ttk.Label(frame, text="Whisper Model:", font=("", 10, "bold")).pack(anchor=tk.W)
        self.model_var = tk.StringVar(value=self.current_model)
        model_menu = ttk.Combobox(
            frame, textvariable=self.model_var,
            values=["tiny", "base", "small", "medium", "turbo"],
            state="readonly", width=25,
        )
        model_menu.pack(anchor=tk.W, pady=(2, 12))

        # Language selector
        ttk.Label(frame, text="Language:", font=("", 10, "bold")).pack(anchor=tk.W)
        self.lang_var = tk.StringVar(value=self.current_language)
        lang_frame = ttk.Frame(frame)
        lang_frame.pack(anchor=tk.W, pady=(2, 12))
        ttk.Radiobutton(lang_frame, text="Auto-detect", variable=self.lang_var, value="auto").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(lang_frame, text="English", variable=self.lang_var, value="en").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(lang_frame, text="Hinglish", variable=self.lang_var, value="hi").pack(side=tk.LEFT)

        # Hotkey
        ttk.Label(frame, text="Push-to-Talk Hotkey:", font=("", 10, "bold")).pack(anchor=tk.W)
        self.hotkey_btn = ttk.Button(
            frame, text=self.current_hotkey.upper().replace("+", " + "),
            command=self._start_hotkey_capture, width=25,
        )
        self.hotkey_btn.pack(anchor=tk.W, pady=(2, 12))

        # Audio input device
        ttk.Label(frame, text="Microphone:", font=("", 10, "bold")).pack(anchor=tk.W)
        self.device_var = tk.StringVar()
        device_names = list(self._device_map.keys())
        # Set current selection
        for label, dev_id in self._device_map.items():
            if dev_id == self.current_input_device:
                self.device_var.set(label)
                break
        if not self.device_var.get():
            self.device_var.set(device_names[0])  # "System Default"

        device_menu = ttk.Combobox(
            frame, textvariable=self.device_var,
            values=device_names,
            state="readonly", width=45,
        )
        device_menu.pack(anchor=tk.W, pady=(2, 20))

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT)

        self.root.protocol("WM_DELETE_WINDOW", self._cancel)

    def _start_hotkey_capture(self) -> None:
        """Start capturing a new hotkey combination."""
        self._capturing_hotkey = True
        self._hotkey_keys = set()
        self.hotkey_btn.config(text="Press keys...", state="disabled")

        # Use pynput to capture the next key combo
        self._capture_listener = pynput_keyboard.Listener(
            on_press=self._on_capture_press,
        )
        self._capture_listener.start()

    def _on_capture_press(self, key) -> None:
        """Capture key presses for hotkey binding."""
        if not self._capturing_hotkey:
            return

        try:
            if hasattr(key, "name") and key.name in ("ctrl", "ctrl_l", "ctrl_r", "shift", "shift_l", "shift_r", "alt", "alt_l", "alt_r", "cmd", "cmd_l", "cmd_r"):
                self._hotkey_keys.add(key.name.replace("_l", "").replace("_r", ""))
            elif hasattr(key, "char") and key.char:
                self._hotkey_keys.add(key.char.lower())

            # Display current captured keys
            display = " + ".join(sorted(self._hotkey_keys)).upper()
            self.hotkey_btn.config(text=display)

            # If we have at least one modifier and one character key, finalize
            has_modifier = any(k in self._hotkey_keys for k in ("ctrl", "shift", "alt", "cmd"))
            has_char = any(len(k) == 1 for k in self._hotkey_keys)
            if has_modifier and has_char:
                self._finish_hotkey_capture()

        except Exception:
            pass

    def _finish_hotkey_capture(self) -> None:
        """Finalize the hotkey capture."""
        if self._capture_listener:
            self._capture_listener.stop()

        self._capturing_hotkey = False
        self.current_hotkey = "+".join(sorted(self._hotkey_keys))

        display = self.current_hotkey.upper().replace("+", " + ")
        self.hotkey_btn.config(text=display, state="normal")

    def _save(self) -> None:
        """Save settings and close."""
        # Resolve selected device
        selected_label = self.device_var.get()
        selected_device = self._device_map.get(selected_label, None)

        if self.on_save:
            self.on_save(
                self.model_var.get(),
                self.lang_var.get(),
                self.current_hotkey,
                selected_device,
            )
        self.root.destroy()

    def _cancel(self) -> None:
        """Close without saving."""
        if self._capturing_hotkey and self._capture_listener:
            self._capture_listener.stop()
        self.root.destroy()


def open_settings(
    current_model: str = "small",
    current_language: str = "auto",
    current_hotkey: str = "cmd+alt",
    current_input_device: Optional[int] = None,
    on_save: Optional[Callable[[str, str, str, int], None]] = None,
) -> None:
    """Open the settings window (standalone or from tray app)."""
    app = SettingsWindow(
        current_model=current_model,
        current_language=current_language,
        current_hotkey=current_hotkey,
        current_input_device=current_input_device,
        on_save=on_save,
    )
    app.root.mainloop()
