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

# Devanagari Unicode range
_DEVANAGARI_START = 0x0900
_DEVANAGARI_END = 0x097F

# Independent vowels (stand alone)
_INDEPENDENT_VOWELS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
    'ऋ': 'ri',
}

# Vowel signs (matras) — replace the inherent 'a' of a consonant
_VOWEL_SIGNS = {
    'ा': 'aa', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
    'ृ': 'ri',
}

# Consonants — base form includes inherent 'a'
_CONSONANTS = {
    'क': 'ka', 'ख': 'kha', 'ग': 'ga', 'घ': 'gha', 'ङ': 'nga',
    'च': 'cha', 'छ': 'chha', 'ज': 'ja', 'झ': 'jha', 'ञ': 'nya',
    'ट': 'ta', 'ठ': 'tha', 'ड': 'da', 'ढ': 'dha', 'ण': 'na',
    'त': 'ta', 'थ': 'tha', 'द': 'da', 'ध': 'dha', 'न': 'na',
    'प': 'pa', 'फ': 'pha', 'ब': 'ba', 'भ': 'bha', 'म': 'ma',
    'य': 'ya', 'र': 'ra', 'ल': 'la', 'व': 'va',
    'श': 'sha', 'ष': 'sha', 'स': 'sa', 'ह': 'ha',
    'क्ष': 'ksha', 'त्र': 'tra', 'ज्ञ': 'gya', 'श्र': 'shra',
    # Nukta variants
    'क़': 'qa', 'ख़': 'kha', 'ग़': 'gha', 'ज़': 'za', 'ड़': 'da', 'ढ़': 'dha',
    'फ़': 'fa', 'य़': 'ya',
}

# Special modifiers
_NASAL = {'ं': 'n', 'ँ': 'n'}
_VISARGA = 'ः'  # 'h'
_HALANT = '्'   # suppresses inherent vowel

# Digits
_DIGITS = {
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
}


def _has_devanagari(text: str) -> bool:
    """Check if text contains Devanagari characters."""
    return any(_DEVANAGARI_START <= ord(c) <= _DEVANAGARI_END for c in text)


def transliterate_devanagari(text: str) -> str:
    """
    Convert Devanagari (Hindi script) to Latin/Roman script using ITRANS scheme.
    Properly handles consonant + vowel sign combinations (e.g., मै = mai not maai).
    """
    if not _has_devanagari(text):
        return text

    result = []
    i = 0
    while i < len(text):
        c = text[i]
        codepoint = ord(c)

        if not (_DEVANAGARI_START <= codepoint <= _DEVANAGARI_END):
            result.append(c)
            i += 1
            continue

        if c in _INDEPENDENT_VOWELS:
            result.append(_INDEPENDENT_VOWELS[c])
            i += 1
            continue

        if c in _CONSONANTS:
            base = _CONSONANTS[c]
            i += 1

            if i < len(text):
                next_c = text[i]

                if next_c in _VOWEL_SIGNS:
                    vowel = _VOWEL_SIGNS[next_c]
                    if base.endswith('a'):
                        base = base[:-1] + vowel
                    else:
                        base += vowel
                    i += 1

                elif next_c == _HALANT:
                    base = base[:-1]
                    i += 1

                if i < len(text) and text[i] in _NASAL:
                    base += _NASAL[text[i]]
                    i += 1

                if i < len(text) and text[i] == _VISARGA:
                    base += 'h'
                    i += 1

            result.append(base)
            continue

        if c in _VOWEL_SIGNS:
            result.append(_VOWEL_SIGNS[c])
            i += 1
            continue

        if c in _NASAL:
            result.append(_NASAL[c])
            i += 1
            continue

        if c == _VISARGA:
            result.append('h')
            i += 1
            continue

        if c == _HALANT:
            i += 1
            continue

        if c in _DIGITS:
            result.append(_DIGITS[c])
            i += 1
            continue

        i += 1

    transliterated = "".join(result)
    return _apply_schwa_deletion(transliterated)


def _apply_schwa_deletion(text: str) -> str:
    """
    Apply Hindi schwa deletion and vowel length normalization.
    - Drop trailing 'a' on word-final consonants (e.g., 'theeka' -> 'theek')
    - Collapse trailing 'aa' after conjunct consonants (e.g., 'kyaa' -> 'kya')
    """
    words = text.split()
    result = []
    for word in words:
        # Collapse final 'aa' to 'a' if word has > 3 chars or contains a conjunct
        # (heuristic: if there are more consonants than vowels, it's a conjunct word)
        consonants = sum(1 for c in word if c in 'bcdfghjklmnpqrstvwxyz')
        vowels = sum(1 for c in word if c in 'aeiou')
        if word.endswith('aa') and consonants >= vowels:
            word = word[:-2] + 'a'
        # Schwa deletion: remove trailing 'a' from consonant-ending words
        elif len(word) > 1 and word.endswith('a') and word[-2] not in 'aeiou':
            word = word[:-1]
        result.append(word)
    return " ".join(result)


def strip_auto_punctuation(text: str) -> str:
    """
    Strip ALL punctuation that Whisper auto-inserts.
    Preserves only letters, digits, spaces, and apostrophes (for contractions).
    Voice commands re-insert explicit punctuation afterward.
    """
    # Strip everything except: word chars, spaces, digits, apostrophes, and
    # characters needed for command detection (preserved via word boundary)
    # Also keep existing emoji that might have been inserted by commands
    text = re.sub(r"[^\w\s'\-]", '', text)  # strip all punctuation/symbols
    text = re.sub(r'\s{2,}', ' ', text)      # collapse multi-spaces
    return text.strip()


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


def post_process(text: str, language: str = "auto", detected_language: str = None) -> str:
    """
    Post-process transcribed text.
    
    Args:
        text: Processed text (after command extraction).
        language: 'en', 'hi', or 'auto'.
        detected_language: Language that Whisper detected (for transliteration).
    
    Returns:
        Cleaned and formatted text.
    """
    text = text.strip()
    
    if not text:
        return ""

    # Transliterate Devanagari to Latin if Hindi was detected
    if detected_language == "hi" or (language == "hi" and _has_devanagari(text)):
        text = transliterate_devanagari(text)
    elif _has_devanagari(text):
        # Auto-detect: always transliterate any devanagari found
        text = transliterate_devanagari(text)
    
    # Apply Hinglish corrections
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


def pre_process_for_commands(text: str) -> str:
    """
    Pre-process raw Whisper output before command detection.
    Strips auto-inserted punctuation so only explicit voice commands
    produce punctuation.
    """
    return strip_auto_punctuation(text)
