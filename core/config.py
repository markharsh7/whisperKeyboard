"""
Configuration loader for Whisper Keyboard.
Reads core/config.yaml and provides typed access.
"""

import os
from typing import Any, Dict, Optional

import yaml


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the shared configuration from YAML.
    
    Args:
        config_path: Path to config.yaml. If None, uses core/config.yaml.
    
    Returns:
        Parsed config dictionary.
    """
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.yaml"
        )

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_whisper_config(config: Optional[Dict] = None) -> dict:
    """Extract whisper-specific config."""
    if config is None:
        config = load_config()
    return config.get("whisper", {})


def get_audio_config(config: Optional[Dict] = None) -> dict:
    """Extract audio-specific config."""
    if config is None:
        config = load_config()
    return config.get("audio", {})


def get_hotkey_config(config: Optional[Dict] = None) -> dict:
    """Extract hotkey-specific config."""
    if config is None:
        config = load_config()
    return config.get("hotkey", {})


def get_post_processing_config(config: Optional[Dict] = None) -> dict:
    """Extract post-processing config."""
    if config is None:
        config = load_config()
    return config.get("post_processing", {})
