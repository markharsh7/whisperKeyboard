"""
Text post-processing for Whisper Keyboard.
Handles English and Hinglish (Hindi in Roman script) transcription output.
"""

import re

# Common Hinglish corrections: word pairs that Whisper frequently
# transliterates inconsistently
HINGLISH_CORRECTIONS = {
    # Common Hindi words Whisper might mangle
    "mein": "main",
    "hein": "hain",
    "he": "hai",
    "theek": "theek",
    "acha": "accha",
    "aacha": "accha",
    "bahut": "bahut",
    "bohot": "bahut",
    "kyun": "kyun",
    "kyu": "kyun",
    "sch": "sh",
}

# Words that should always be lowercase in English (conjunctions, articles, prepositions)
# unless they start a sentence
LOWERCASE_WORDS = {
    "a", "an", "the", "and", "but", "or", "for", "nor", "on", "at",
    "to", "by", "in", "of", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "shall", "should", "may", "might", "must", "can", "could", "it",
    "its", "so", "as", "if", "than", "that", "this", "with", "from",
}

# Words that should always be capitalized
ALWAYS_CAPITALIZE = {
    "i", "i'm", "i'll", "i've", "i'd",
}


def apply_hinglish_corrections(text: str) -> str:
    """Apply common Hinglish word corrections."""
    words = text.split()
    corrected = []
    for word in words:
        lower = word.lower()
        if lower in HINGLISH_CORRECTIONS:
            corrected.append(HINGLISH_CORRECTIONS[lower])
        else:
            corrected.append(word)
    return " ".join(corrected)


def capitalize_sentences(text: str) -> str:
    """Capitalize the first letter of each sentence."""
    # Split on sentence boundaries: . ! ? followed by space
    sentences = re.split(r'([.!?]\s+)', text)
    result = []
    for i, part in enumerate(sentences):
        if i % 2 == 0 and part:  # Sentence content (not the separator)
            part = part[0].upper() + part[1:] if part[0].isalpha() else part
        result.append(part)
    return "".join(result)


def capitalize_i(text: str) -> str:
    """Ensure standalone 'i' is always capitalized as 'I'."""
    words = text.split()
    result = []
    for word in words:
        stripped = word.strip(".,!?;:'\"")
        lower = stripped.lower()
        if lower in ALWAYS_CAPITALIZE:
            word = word.replace(stripped, stripped.capitalize())
        result.append(word)
    return " ".join(result)


def fix_spacing_after_punctuation(text: str) -> str:
    """Ensure proper spacing after punctuation marks."""
    # Remove space before punctuation
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    # Add space after punctuation if missing
    text = re.sub(r'([.,!?;:])([^\s\d])', r'\1 \2', text)
    return text


def remove_leading_trailing_space(text: str) -> str:
    """Clean up whitespace."""
    return text.strip()


def post_process(text: str, language: str = "auto") -> str:
    """
    Post-process transcribed text.
    
    Args:
        text: Raw transcribed text from Whisper.
        language: 'en', 'hi', or 'auto'.
    
    Returns:
        Cleaned and formatted text.
    """
    text = text.strip()
    
    if not text:
        return ""
    
    # Apply corrections
    if language in ("hi", "auto"):
        text = apply_hinglish_corrections(text)
    
    # Capitalize first letter
    text = remove_leading_trailing_space(text)
    if text and text[0].isalpha():
        text = text[0].upper() + text[1:]
    
    # Capitalize 'i' as 'I'
    text = capitalize_i(text)
    
    # Fix spacing
    text = fix_spacing_after_punctuation(text)
    
    # Sentence capitalization
    text = capitalize_sentences(text)
    
    return text
