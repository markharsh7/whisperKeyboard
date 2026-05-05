"""
Whisper speech recognition engine using faster-whisper.
Handles model loading, transcription, and language detection.
"""

import os
from typing import Optional
from faster_whisper import WhisperModel


class WhisperEngine:
    """Wraps faster-whisper model for speech-to-text transcription."""

    def __init__(
        self,
        model_size: str = "small",
        model_type: str = "multilingual",
        compute_type: str = "auto",
        device: str = "cpu",
        cpu_threads: int = 4,
        model_path: Optional[str] = None,
    ):
        """
        Initialize the Whisper engine.

        Args:
            model_size: Model size - tiny, base, small, medium, large, turbo, etc.
            model_type: "multilingual" or "english-only" (appends .en to size).
            compute_type: auto, float16, int8, int8_float16.
            device: cpu or cuda.
            cpu_threads: Number of CPU threads for inference.
            model_path: Custom directory to store/download model files.
        """
        self.model_size = model_size
        self.model_type = model_type
        self.compute_type = compute_type
        self.device = device
        self.cpu_threads = cpu_threads
        self.model_path = model_path

        # Construct model size identifier for faster-whisper
        if model_type == "english-only":
            self._model_id = model_size if model_size.endswith(".en") else f"{model_size}.en"
        else:
            self._model_id = model_size

        self._model: Optional[WhisperModel] = None

    def load_model(self) -> None:
        """Load the Whisper model into memory (downloads on first run)."""
        if self._model is not None:
            return

        download_root = self.model_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "core", "models"
        )

        self._model = WhisperModel(
            model_size_or_path=self._model_id,
            device=self.device,
            compute_type=self.compute_type,
            cpu_threads=self.cpu_threads,
            download_root=download_root,
            local_files_only=False,
        )
        print(f"[Whisper] {self._model_id} loaded")

    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._model is not None

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        beam_size: int = 5,
        vad_filter: bool = True,
        vad_parameters: Optional[dict] = None,
        temperature: float = 0.0,
    ) -> dict:
        """
        Transcribe an audio file to text.

        Args:
            audio_path: Path to WAV file.
            language: Language code (en, hi) or None for auto-detect.
            beam_size: Beam size for decoding.
            vad_filter: Enable voice activity detection.
            vad_parameters: VAD configuration dict.
            temperature: Sampling temperature (0 = greedy).

        Returns:
            dict with keys: text, language, segments, duration
        """
        if not self._model:
            self.load_model()

        result = {
            "text": "",
            "language": "",
            "segments": [],
            "duration": 0.0,
        }

        segments, info = self._model.transcribe(
            audio_path,
            language=language,
            beam_size=beam_size,
            vad_filter=vad_filter,
            vad_parameters=vad_parameters,
            temperature=temperature,
        )

        result["language"] = info.language
        result["duration"] = info.duration

        full_text = []
        for segment in segments:
            full_text.append(segment.text)
            result["segments"].append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
            })

        result["text"] = " ".join(full_text).strip()
        return result

    def unload(self) -> None:
        """Unload the model to free memory."""
        self._model = None
