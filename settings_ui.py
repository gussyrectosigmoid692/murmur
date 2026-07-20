"""Settings dialog: hotkey, microphone, model, language, delivery, autostart."""

import tkinter as tk
from tkinter import ttk

import sounddevice as sd

import autostart
import config
import theme
from theme import (
    ACCENT, ACCENT_HOVER, ACCENT_TEXT, BG, BORDER, FIELD, FIELD_HOVER, MUTED, TEXT,
)

HOTKEY_CHOICES = ["right alt", "right ctrl", "f8", "f9", "scroll lock", "pause"]
MODEL_CHOICES = [
    "tiny", "base", "small", "distil-small.en", "medium", "large-v3", "large-v3-turbo",
]
LANGUAGE_CHOICES = ["auto", "en", "ur", "hi", "ar", "es", "fr", "de", "zh"]
DEFAULT_DEVICE_LABEL = "System default"

_open_dialog = None


def input_device_names():
    """Full-fidelity input device names (prefers the WASAPI host API)."""
    try:
        apis = sd.query_hostapis()
        target = next((i for i, a in enumerate(apis) if "WASAPI" in a["name"]), 0)
        return [
            d["name"]
            for d in sd.query_devices()
            if d["max_input_channels"] > 0 and d["hostapi"] == target
        ]
    except Exception as e:
        print(f"could not list input devices: {e}")
        return []


def show(root, on_device_change, on_model_change):
    """Open the settings dialog (single instance)."""
    global _open_dialog
    if _open_dialog is not None and _open_dialog.top.winfo_exists():
        _open_dialog.top.lift()
        _open_dialog.top.focus_force()
        return
    _open_dialog = _Dialog(root, on_device_change, on_model_change)


def _apply_theme(top):
    style = ttk.Style(top)
    style.theme_use("clam")
    style.configure("WF.TFrame", background=BG)
    style.configure(
        "WFTitle.TLabel", background=BG, foreground=TEXT, font=("Segoe UI Semibold", 14)
    )
    style.configure(
        "WFSub.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9)
    )
    style.configure(
        "WFSection.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 8, "bold")
    )
    style.configure(
        "WF.TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10)
    )
    style.configure(
        "WF.TCombobox",
        fieldbackground=FIELD, background=FIELD, foreground=TEXT,
        arrowcolor=MUTED, bordercolor=BORDER, lightcolor=FIELD, darkcolor=FIELD,
        insertcolor=TEXT, padding=(8, 4), font=("Segoe UI", 10),
    )
    style.map(
        "WF.TCombobox",
        fieldbackground=[("readonly", FIELD)],
        bordercolor=[("focus", ACCENT)],
        arrowcolor=[("hover", TEXT)],
        selectbackground=[("readonly", FIELD)],
        selectforeground=[("readonly", TEXT)],
    )
    style.configure(
        "WF.TCheckbutton",
        background=BG, foreground=TEXT, font=("Segoe UI", 10),
        indicatorcolor=FIELD, indicatormargin=6,
    )
    style.map(
        "WF.TCheckbutton",
        background=[("active", BG)],
        indicatorcolor=[("selected", ACCENT), ("active", FIELD_HOVER)],
    )
    style.configure(
        "WFAccent.TButton",
        background=ACCENT, foreground=ACCENT_TEXT, bordercolor=ACCENT,
        lightcolor=ACCENT, darkcolor=ACCENT, focuscolor=ACCENT_TEXT,
        font=("Segoe UI Semibold", 10), padding=(18, 6),
    )
    style.map(
        "WFAccent.TButton",
        background=[("active", ACCENT_HOVER), ("pressed", ACCENT_HOVER)],
        lightcolor=[("active", ACCENT_HOVER)],
        darkcolor=[("active", ACCENT_HOVER)],
    )
    style.configure(
        "WFGhost.TButton",
        background=FIELD, foreground=TEXT, bordercolor=BORDER,
        lightcolor=FIELD, darkcolor=FIELD, focuscolor=MUTED,
        font=("Segoe UI", 10), padding=(18, 6),
    )
    style.map(
        "WFGhost.TButton",
        background=[("active", FIELD_HOVER), ("pressed", FIELD_HOVER)],
        lightcolor=[("active", FIELD_HOVER)],
        darkcolor=[("active", FIELD_HOVER)],
    )
    # dropdown list colors (plain tk Listbox inside the combobox popup)
    top.option_add("*TCombobox*Listbox.background", FIELD)
    top.option_add("*TCombobox*Listbox.foreground", TEXT)
    top.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    top.option_add("*TCombobox*Listbox.selectForeground", ACCENT_TEXT)
    top.option_add("*TCombobox*Listbox.font", "{Segoe UI} 10")


class _Dialog:
    def __init__(self, root, on_device_change, on_model_change):
        self.on_device_change = on_device_change
        self.on_model_change = on_model_change
        top = self.top = tk.Toplevel(root)
        top.title("Murmur Settings")
        top.configure(bg=BG)
        top.resizable(False, False)
        top.attributes("-topmost", True)
        _apply_theme(top)
        theme.dark_titlebar(top)

        frame = ttk.Frame(top, style="WF.TFrame", padding=(24, 18, 24, 20))
        frame.grid()
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Settings", style="WFTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            frame, text="Changes apply as soon as you save", style="WFSub.TLabel"
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 6))

        self._section(frame, 2, "INPUT")
        self.hotkey = self._combo(frame, 3, "Hotkey", HOTKEY_CHOICES, config.get("hotkey"))
        devices = [DEFAULT_DEVICE_LABEL] + input_device_names()
        current_dev = config.get("input_device") or DEFAULT_DEVICE_LABEL
        if current_dev not in devices:
            devices.append(current_dev)  # keep a now-unplugged device selectable
        self.device = self._combo(frame, 4, "Microphone", devices, current_dev, width=32)

        self._section(frame, 5, "TRANSCRIPTION")
        self.model = self._combo(frame, 6, "Model", MODEL_CHOICES, config.get("model"))
        self.language = self._combo(
            frame, 7, "Language", LANGUAGE_CHOICES,
            config.get("language") or "auto", readonly=False,
        )

        self._section(frame, 8, "OUTPUT")
        self.delivery = self._combo(
            frame, 9, "Delivery", ["paste", "type"], config.get("delivery")
        )
        self.cleanup_var = tk.BooleanVar(value=config.get("cleanup"))
        ttk.Checkbutton(
            frame, text="Remove filler words (um, uh, stutters)",
            variable=self.cleanup_var, style="WF.TCheckbutton", cursor="hand2",
        ).grid(row=10, column=1, sticky="w", pady=(6, 0))
        self.autostart_var = tk.BooleanVar(value=autostart.is_enabled())
        ttk.Checkbutton(
            frame, text="Start with Windows", variable=self.autostart_var,
            style="WF.TCheckbutton", cursor="hand2",
        ).grid(row=11, column=1, sticky="w", pady=(2, 0))

        buttons = ttk.Frame(frame, style="WF.TFrame")
        buttons.grid(row=12, column=0, columnspan=2, pady=(18, 0), sticky="e")
        ttk.Button(
            buttons, text="Cancel", style="WFGhost.TButton",
            command=top.destroy, cursor="hand2",
        ).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(
            buttons, text="Save", style="WFAccent.TButton",
            command=self._save, cursor="hand2",
        ).grid(row=0, column=1)

        top.bind("<Return>", lambda e: self._save())
        top.bind("<Escape>", lambda e: top.destroy())

    def _section(self, frame, row, label):
        holder = ttk.Frame(frame, style="WF.TFrame")
        holder.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(14, 6))
        holder.columnconfigure(1, weight=1)
        ttk.Label(holder, text=label, style="WFSection.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        tk.Frame(holder, height=1, bg=BORDER, bd=0).grid(
            row=0, column=1, sticky="ew", padx=(8, 0)
        )

    def _combo(self, frame, row, label, values, current, width=22, readonly=True):
        ttk.Label(frame, text=label, style="WF.TLabel").grid(
            row=row, column=0, sticky="w", padx=(0, 16), pady=4
        )
        var = tk.StringVar(value=current)
        ttk.Combobox(
            frame, textvariable=var, values=values, width=width,
            style="WF.TCombobox", cursor="hand2",
            state="readonly" if readonly else "normal",
        ).grid(row=row, column=1, sticky="ew", pady=4)
        return var

    def _save(self):
        device = self.device.get()
        device = "" if device == DEFAULT_DEVICE_LABEL else device
        language = self.language.get().strip()
        language = "" if language in ("", "auto") else language

        device_changed = device != config.get("input_device")
        model_changed = self.model.get() != config.get("model")

        config.set("hotkey", self.hotkey.get())
        config.set("input_device", device)
        config.set("model", self.model.get())
        config.set("language", language)
        config.set("delivery", self.delivery.get())
        config.set("cleanup", self.cleanup_var.get())
        config.save()

        try:
            if self.autostart_var.get() != autostart.is_enabled():
                autostart.enable() if self.autostart_var.get() else autostart.disable()
        except Exception as e:
            print(f"could not update autostart shortcut: {e}")

        if device_changed:
            self.on_device_change()
        if model_changed:
            self.on_model_change()
        self.top.destroy()
