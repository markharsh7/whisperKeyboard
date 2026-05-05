"""
Audio recording module using sounddevice.
Captures microphone input, saves to WAV, with optional silence detection.
"""

import os
import tempfile
import wave
import threading
import time
from typing import Optional, Callable

import numpy as np
import sounddevice as sd


class AudioRecorder:
    """Records audio from the default microphone."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        dtype: str = "int16",
        device: Optional[int] = None,
    ):
        """
        Initialize audio recorder.
        
        Args:
            sample_rate: Sample rate in Hz (16000 for Whisper).
            channels: Number of audio channels (1 = mono).
            dtype: Sample format (int16 = 16-bit PCM).
            device: Input device ID or None for default.
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.device = device

        self._recording = False
        self._audio_data: list = []
        self._stream: Optional[sd.InputStream] = None
        self._thread: Optional[threading.Thread] = None
        self._on_level: Optional[Callable[[float], None]] = None

    def start_recording(self, on_level: Optional[Callable[[float], None]] = None) -> None:
        """
        Start recording audio.
        
        Args:
            on_level: Optional callback receiving RMS level (0.0-1.0) for visual feedback.
        """
        if self._recording:
            return

        self._audio_data = []
        self._recording = True
        self._on_level = on_level

        def callback(indata, frames, time_info, status):
            if status:
                print(f"[Audio] Warning: {status}")
            if self._recording:
                self._audio_data.append(indata.copy())
                if self._on_level:
                    rms = np.sqrt(np.mean(indata.astype(np.float64) ** 2))
                    level = min(rms / 32768.0, 1.0)
                    self._on_level(level)

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            device=self.device,
            callback=callback,
        )
        self._stream.start()

    def stop_recording(self) -> str:
        """
        Stop recording and save audio to a WAV file.
        
        Returns:
            Path to the saved WAV file.
        """
        if not self._recording:
            return None

        self._recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        # Concatenate all audio chunks
        if not self._audio_data:
            return None

        audio_array = np.concatenate(self._audio_data, axis=0)

        # Save to temp WAV file
        temp_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "temp_audio"
        )
        os.makedirs(temp_dir, exist_ok=True)

        filepath = os.path.join(temp_dir, f"recording_{int(time.time() * 1000)}.wav")
        self._save_wav(filepath, audio_array)
        return filepath

    def record(
        self,
        duration: Optional[float] = None,
        on_level: Optional[Callable[[float], None]] = None,
    ) -> str:
        """
        Record for a fixed duration or until stop_recording() is called.
        
        Args:
            duration: Record for this many seconds, or None for manual stop.
            on_level: Optional callback receiving RMS level for visual feedback.
        
        Returns:
            Path to the saved WAV file.
        """
        self.start_recording(on_level=on_level)

        if duration is not None:
            time.sleep(duration)
            return self.stop_recording()

        return None  # Caller must call stop_recording() manually

    def _save_wav(self, filepath: str, audio_data: np.ndarray) -> None:
        """Save numpy audio array as WAV file."""
        with wave.open(filepath, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit = 2 bytes
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())

    @staticmethod
    def list_devices() -> list:
        """List available audio input devices."""
        devices = []
        for i, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0:
                devices.append({
                    "id": i,
                    "name": dev["name"],
                    "channels": dev["max_input_channels"],
                    "default_samplerate": dev["default_samplerate"],
                })
        return devices


class SilenceDetector:
    """Monitors audio levels and triggers callback when silence is detected."""

    def __init__(
        self,
        threshold: float = 0.02,
        silence_duration: float = 1.5,
        on_silence: Optional[Callable[[], None]] = None,
    ):
        self.threshold = threshold
        self.silence_duration = silence_duration
        self.on_silence = on_silence
        self._silence_start: Optional[float] = None
        self._last_level_time: float = 0

    def process_level(self, level: float) -> bool:
        """
        Process an audio level reading.
        
        Returns:
            True if silence threshold has been exceeded (triggered callback).
        """
        now = time.time()

        if level < self.threshold:
            if self._silence_start is None:
                self._silence_start = now
            elif now - self._silence_start >= self.silence_duration:
                if self.on_silence:
                    self.on_silence()
                return True
        else:
            self._silence_start = None

        self._last_level_time = now
        return False
