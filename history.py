"""Transcript log: one JSON object per line in transcripts.jsonl."""

import json
import time
from pathlib import Path

FILE = Path(__file__).parent / "transcripts.jsonl"


def append(text, wav_path, model):
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wav": str(wav_path),
        "model": model,
        "text": text,
    }
    with FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def recent(n=100):
    """Latest n records, newest first."""
    if not FILE.exists():
        return []
    records = []
    for line in FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records[-n:][::-1]


def last():
    entries = recent(1)
    return entries[0] if entries else None
