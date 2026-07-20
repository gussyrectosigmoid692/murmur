"""Filler-word and stutter cleanup applied to transcripts before delivery."""

import re

# um/umm, uh/uhh, erm, mhm — with any stretched spelling
_FILLER = r"(?:u+m+|u+h+|e+r+m+|m+h+m+)"


def clean(text):
    text = re.sub(rf"\b{_FILLER}\b[,.!?]*\s*", "", text, flags=re.IGNORECASE)
    # collapse immediate word repeats ("the the the" -> "the")
    text = re.sub(r"\b(\w+)(?:\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)
    # tidy artifacts left behind
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    text = re.sub(r"([,.!?;:])(?:\s*,)+", r"\1", text)
    text = re.sub(r"^[\s,.;:]+", "", text).strip()
    # a removed leading filler ("Um, so...") leaves a lowercase start
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text
