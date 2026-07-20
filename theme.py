"""Shared dark-theme palette and window helpers for the app's dialogs."""

import ctypes

BG = "#1c1c22"
FIELD = "#27272f"
FIELD_HOVER = "#2e2e38"
BORDER = "#3a3a44"
TEXT = "#e8e8ec"
MUTED = "#9a9aa6"
ACCENT = "#6ee7a8"
ACCENT_HOVER = "#8bedb9"
ACCENT_TEXT = "#0f2418"


def dark_titlebar(win):
    """Ask DWM for a dark title bar (Windows 10 1809+); harmless if unsupported."""
    try:
        win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
        )
    except Exception:
        pass
