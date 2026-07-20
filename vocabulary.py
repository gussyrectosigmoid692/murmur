"""User vocabulary: bias transcription toward known terms and fix mis-hearings.

Reads vocabulary.txt next to this file. Format:

    # plain lines are glossary terms fed to whisper as an initial prompt
    Murmur
    ctranslate2

    [replace]
    # wrong => right, applied to the transcript (case-insensitive, whole words)
    murmer => Murmur
"""

import re
from pathlib import Path

VOCAB_FILE = Path(__file__).parent / "vocabulary.txt"


def load():
    """Returns (initial_prompt or None, list of (wrong, right) replacements)."""
    terms = []
    replacements = []
    section = "terms"
    if VOCAB_FILE.exists():
        for line in VOCAB_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower() == "[replace]":
                section = "replace"
                continue
            if section == "terms":
                terms.append(line)
            elif "=>" in line:
                wrong, right = (part.strip() for part in line.split("=>", 1))
                if wrong:
                    replacements.append((wrong, right))
    prompt = f"Glossary: {', '.join(terms)}." if terms else None
    return prompt, replacements


def apply_replacements(text, replacements):
    for wrong, right in replacements:
        text = re.sub(rf"\b{re.escape(wrong)}\b", right, text, flags=re.IGNORECASE)
    return text
