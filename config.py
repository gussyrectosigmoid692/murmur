"""App settings persisted to settings.json next to the code."""

import json
from pathlib import Path

FILE = Path(__file__).parent / "settings.json"

DEFAULTS = {
    "hotkey": "right alt",
    "input_device": "",  # "" = system default; otherwise exact device name
    "model": "large-v3-turbo",
    "language": "",  # "" = auto-detect
    "delivery": "paste",  # "paste" = clipboard + Ctrl+V; "type" = simulate keystrokes
    "cleanup": True,  # strip filler words and stutters before delivery
}

_settings = dict(DEFAULTS)


def load():
    if FILE.exists():
        try:
            stored = json.loads(FILE.read_text(encoding="utf-8"))
            _settings.update({k: stored[k] for k in DEFAULTS if k in stored})
        except (json.JSONDecodeError, OSError) as e:
            print(f"could not read {FILE.name} ({e}); using defaults")


def save():
    FILE.write_text(json.dumps(_settings, indent=2), encoding="utf-8")


def get(key):
    return _settings[key]


def set(key, value):
    _settings[key] = value


load()
