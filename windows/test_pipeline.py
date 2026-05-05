"""
Interactive test for the Whisper Keyboard Windows pipeline.
Modes:
  - Interactive: Press Enter to start, speak, press Enter to stop
  - Batch: Record 5s with silence auto-stop
  - File: Transcribe a WAV file
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from windows.whisper_engine import WhisperEngine
from windows.audio_recorder import AudioRecorder
from core.commands import CommandProcessor
from core.text_post import post_process


def test_file(filepath: str):
    """Transcribe a pre-recorded audio file."""
    engine = WhisperEngine(model_size="small", compute_type="auto", device="cpu")
    cp = CommandProcessor()

    print(f"Loading model...")
    engine.load_model()

    print(f"Transcribing: {filepath}")
    result = engine.transcribe(filepath)

    raw = result["text"]
    processed, actions = cp.process_text(raw)
    final = post_process(processed, "auto")

    print(f"\n  Raw:      {raw!r}")
    print(f"  Final:    {final!r}")
    print(f"  Language: {result['language']}")
    if actions:
        print(f"  Commands: {actions}")


def test_interactive():
    """Interactive push-to-talk: Enter to start, speak, Enter to stop."""
    engine = WhisperEngine(model_size="small", compute_type="auto", device="cpu")
    recorder = AudioRecorder()
    cp = CommandProcessor()

    print("=" * 60)
    print("Whisper Keyboard - Interactive Pipeline Test")
    print("=" * 60)

    print("\nLoading model (first run downloads ~75MB)...")
    engine.load_model()
    print("Model ready.\n")

    while True:
        print("-" * 40)
        print("1. Press Enter to start recording")
        print("2. Speak your text (include commands like 'full stop')")
        print("3. Press Enter to stop and transcribe")
        print("   Type 'q' to quit, 'f <path>' to transcribe a file\n")

        cmd = input("> ").strip()

        if cmd.lower() == "q":
            print("Exiting.")
            break

        if cmd.lower().startswith("f "):
            filepath = cmd[2:].strip()
            if not os.path.exists(filepath):
                print(f"File not found: {filepath}")
                continue
            result = engine.transcribe(filepath)
            raw = result["text"]
            processed, actions = cp.process_text(raw)
            final = post_process(processed, "auto")
            print(f"\n  Raw:      {raw!r}")
            print(f"  Final:    {final!r}")
            print(f"  Language: {result['language']}")
            if actions:
                print(f"  Commands: {actions}")
            continue

        # Start recording
        recorder.start_recording()
        print("\n  RECORDING... speak now. Press Enter to stop.")

        input()

        # Stop recording
        audio_path = recorder.stop_recording()
        if audio_path is None:
            print("  No audio captured.")
            continue

        print("  Transcribing...")
        result = engine.transcribe(audio_path)
        raw = result["text"]
        processed, actions = cp.process_text(raw)
        final = post_process(processed, "auto")

        print(f"\n  Raw:      {raw!r}")
        print(f"  Final:    {final!r}")
        print(f"  Language: {result['language']}")
        if actions:
            print(f"  Commands: {actions}")
        print()

        # Clean up
        try:
            os.remove(audio_path)
        except OSError:
            pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if os.path.isfile(arg):
            test_file(arg)
        else:
            print(f"Usage: python test_pipeline.py [wav_file_path]")
            print(f"File not found: {arg}")
    else:
        test_interactive()
