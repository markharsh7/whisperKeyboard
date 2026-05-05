"""
Voice command parser and processor.
Loads command definitions from commands.yaml and provides lookup/execution.
"""

import os
import yaml
from typing import Dict, List, Optional, Tuple


class Command:
    """Represents a single voice command."""
    def __init__(self, data: dict):
        self.phrase: str = data["phrase"]
        self.action: str = data["action"]  # text, key, key_combo, caps
        self.value: str = data["value"]
        self.count: int = data.get("count", 1)
        self.description: str = data.get("description", "")

    def __repr__(self):
        return f"Command(phrase={self.phrase!r}, action={self.action!r}, value={self.value!r})"


class CommandProcessor:
    """
    Detects and processes voice commands within transcribed text.
    Commands are triggered by exact phrase match (case-insensitive).
    """

    def __init__(self, config_path: Optional[str] = None):
        self.commands: Dict[str, Command] = {}
        self._load_commands(config_path)

    def _load_commands(self, config_path: Optional[str] = None):
        """Load command definitions from YAML."""
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "commands.yaml"
            )

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Commands config not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for item in data["commands"]:
            cmd = Command(item)
            self.commands[cmd.phrase.lower()] = cmd

    def find_command(self, word_sequence: List[str]) -> Optional[Command]:
        """
        Find the longest matching command from a sequence of words.
        Checks progressively shorter suffixes to match multi-word commands.
        """
        text = " ".join(word_sequence).lower().strip()
        
        # Try full sequence first, then progressively shorter
        words = text.split()
        for length in range(len(words), 0, -1):
            candidate = " ".join(words[-length:])
            if candidate in self.commands:
                return self.commands[candidate]
        return None

    def process_text(self, text: str) -> Tuple[str, List[str]]:
        """
        Process transcribed text, extracting and executing commands.
        
        Returns:
            (output_text, list_of_actions_performed)
        """
        if not text.strip():
            return text, []

        words = text.split()
        output_parts = []
        actions = []
        i = 0

        while i < len(words):
            # Try to match a command starting at position i
            matched = False
            for j in range(len(words), i, -1):
                candidate = " ".join(words[i:j]).lower()
                if candidate in self.commands:
                    cmd = self.commands[candidate]
                    actions.append(cmd.phrase)
                    i = j
                    matched = True
                    break
            
            if not matched:
                output_parts.append(words[i])
                i += 1

        result = " ".join(output_parts)
        return result, actions

    def get_command(self, phrase: str) -> Optional[Command]:
        """Get a single command by exact phrase match."""
        return self.commands.get(phrase.lower().strip())

    def get_all_commands(self) -> Dict[str, Command]:
        """Return all loaded commands."""
        return dict(self.commands)

    def list_commands(self) -> List[str]:
        """Return sorted list of all command phrases."""
        return sorted(self.commands.keys())


if __name__ == "__main__":
    # Test the command processor
    cp = CommandProcessor()
    print(f"Loaded {len(cp.commands)} commands:")
    for phrase in cp.list_commands():
        cmd = cp.commands[phrase]
        print(f"  '{phrase}' -> {cmd.action}:{cmd.value}")
