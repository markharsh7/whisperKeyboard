"""
Pipeline orchestrator for Whisper Keyboard on Windows.
Connects audio recording → whisper transcription → command processing → text output.
"""

import sys
import os
import time
import threading
from typing import Optional, Callable

# Add project root to path for core imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.commands import CommandProcessor
from core.text_post import post_process
from core.config import load_config
from windows.whisper_engine import WhisperEngine
from windows.audio_recorder import AudioRecorder, SilenceDetector


class Pipeline:
    """End-to-end pipeline: record → transcribe → process commands → return text."""

    def __init__(
        self,
        model_size: str = "small",
        language: str = "auto",
        compute_type: str = "auto",
        device: str = "cpu",
        enable_commands: bool = True,
        enable_post_processing: bool = True,
        on_status: Optional[Callable[[str], None]] = None,
    ):
        self.language = language
        self.enable_commands = enable_commands
        self.enable_post_processing = enable_post_processing
        self.on_status = on_status

        self._status("Initializing Whisper engine...")
        self.engine = WhisperEngine(
            model_size=model_size,
            compute_type=compute_type,
            device=device,
        )

        self.recorder = AudioRecorder()

        self.command_processor = CommandProcessor() if enable_commands else None

        self._is_loaded = False

    def _status(self, msg: str) -> None:
        """Report status via callback or print."""
        if self.on_status:
            self.on_status(msg)
        else:
            print(f"[Pipeline] {msg}")

    def ensure_loaded(self) -> None:
        """Load the Whisper model if not already loaded."""
        if not self._is_loaded:
            self.engine.load_model()
            self._is_loaded = True
            self._status("Whisper engine ready")

    def record_and_transcribe(
        self,
        on_level: Optional[Callable[[float], None]] = None,
        silence_threshold: Optional[float] = None,
        silence_duration: Optional[float] = None,
    ) -> dict:
        """
        Record audio until stopped, then transcribe.
        
        Designed for push-to-talk: call record_and_transcribe() which blocks
        until silence or manual stop.
        
        Returns:
            dict with keys: raw_text, final_text, language, duration, actions
        """
        self.ensure_loaded()

        # If silence detection is enabled, use it
        silence_det = None
        recording_done = threading.Event()

        if silence_threshold is not None and silence_duration is not None:
            def on_silence():
                recording_done.set()

            silence_det = SilenceDetector(
                threshold=silence_threshold,
                silence_duration=silence_duration,
                on_silence=on_silence,
            )

            def level_callback(level):
                if on_level:
                    on_level(level)
                silence_det.process_level(level)
        else:
            def level_callback(level):
                if on_level:
                    on_level(level)

        # Start recording
        self._status("Recording...")

        self.recorder.start_recording(on_level=level_callback)

        # Wait for stop signal (in push-to-talk, the hotkey listener calls stop)
        # For the test pipeline, we block until silence or timeout
        if silence_det is not None:
            try:
                recording_done.wait(timeout=30)  # Max 30 seconds
            except:
                pass

        audio_path = self.recorder.stop_recording()
        if audio_path is None:
            return {"raw_text": "", "final_text": "", "language": "", "duration": 0, "actions": []}

        self._status("Transcribing...")
        result = self.engine.transcribe(
            audio_path,
            language=None if self.language == "auto" else self.language,
        )

        raw_text = result["text"]

        # Process voice commands in the text
        actions = []
        if self.enable_commands and self.command_processor:
            processed_text, actions = self.command_processor.process_text(raw_text)
        else:
            processed_text = raw_text

        # Post-process (capitalization, spacing, Hinglish corrections)
        final_text = processed_text
        if self.enable_post_processing:
            final_text = post_process(processed_text, self.language)

        # Clean up temp audio
        try:
            os.remove(audio_path)
        except OSError:
            pass

        return {
            "raw_text": raw_text,
            "final_text": final_text,
            "language": result["language"],
            "duration": result["duration"],
            "actions": actions,
        }

    def stop_recording(self) -> Optional[str]:
        """Stop recording manually (for push-to-talk release)."""
        return self.recorder.stop_recording()

    def transcribe_file(self, audio_path: str) -> dict:
        """Transcribe an existing audio file (no recording)."""
        self.ensure_loaded()

        result = self.engine.transcribe(
            audio_path,
            language=None if self.language == "auto" else self.language,
        )

        raw_text = result["text"]

        actions = []
        if self.enable_commands and self.command_processor:
            processed_text, actions = self.command_processor.process_text(raw_text)
        else:
            processed_text = raw_text

        final_text = processed_text
        if self.enable_post_processing:
            final_text = post_process(processed_text, self.language)

        return {
            "raw_text": raw_text,
            "final_text": final_text,
            "language": result["language"],
            "duration": result["duration"],
            "actions": actions,
        }


if __name__ == "__main__":
    print("=" * 50)
    print("Whisper Keyboard - Pipeline Test")
    print("=" * 50)

    pipeline = Pipeline(model_size="small", language="auto")

    print("\nLoading Whisper model (first run may download)...")
    pipeline.ensure_loaded()

    print("\nRecording for 5 seconds. Speak now...")
    result = pipeline.record_and_transcribe(
        silence_threshold=0.02,
        silence_duration=1.5,
    )

    print(f"\n--- Results ---")
    print(f"Raw text:    {result['raw_text']!r}")
    print(f"Final text:  {result['final_text']!r}")
    print(f"Language:    {result['language']}")
    print(f"Duration:    {result['duration']:.2f}s")
    if result["actions"]:
        print(f"Commands:    {result['actions']}")
