"""Transcript history window: click an entry to copy it to the clipboard."""

import time
import tkinter as tk
from tkinter import ttk

import history
import theme
from theme import ACCENT, ACCENT_TEXT, BG, BORDER, FIELD, MUTED, TEXT

_open_window = None


def show(root):
    global _open_window
    if _open_window is not None and _open_window.top.winfo_exists():
        _open_window.top.lift()
        _open_window.top.focus_force()
        return
    _open_window = _Window(root)


class _Window:
    def __init__(self, root):
        top = self.top = tk.Toplevel(root)
        top.title("Murmur History")
        top.configure(bg=BG)
        top.resizable(False, False)
        top.attributes("-topmost", True)
        theme.dark_titlebar(top)

        style = ttk.Style(top)
        style.theme_use("clam")
        style.configure("WF.TFrame", background=BG)
        style.configure(
            "WFTitle.TLabel", background=BG, foreground=TEXT,
            font=("Segoe UI Semibold", 14),
        )
        style.configure(
            "WFSub.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9)
        )

        frame = ttk.Frame(top, style="WF.TFrame", padding=(20, 14, 20, 16))
        frame.grid()

        ttk.Label(frame, text="History", style="WFTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            frame, text="Click an entry to copy it", style="WFSub.TLabel"
        ).grid(row=1, column=0, sticky="w", pady=(0, 8))

        self.entries = history.recent(100)
        self.listbox = tk.Listbox(
            frame, width=72, height=12, activestyle="none", cursor="hand2",
            bg=FIELD, fg=TEXT, selectbackground=ACCENT, selectforeground=ACCENT_TEXT,
            highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT,
            relief="flat", font=("Segoe UI", 9),
        )
        self.listbox.grid(row=2, column=0, sticky="ew")
        for e in self.entries:
            stamp = time.strftime("%b %d %H:%M", time.strptime(e["ts"], "%Y-%m-%dT%H:%M:%S"))
            snippet = e["text"][:70] + ("…" if len(e["text"]) > 70 else "")
            self.listbox.insert("end", f" {stamp}   {snippet}")
        if not self.entries:
            self.listbox.insert("end", "  no transcripts yet")

        self.preview = tk.Text(
            frame, width=72, height=4, wrap="word", state="disabled",
            bg=FIELD, fg=TEXT, insertbackground=TEXT,
            highlightthickness=1, highlightbackground=BORDER, relief="flat",
            font=("Segoe UI", 9), padx=8, pady=6,
        )
        self.preview.grid(row=3, column=0, sticky="ew", pady=(8, 0))

        self.status = ttk.Label(frame, text="", style="WFSub.TLabel")
        self.status.grid(row=4, column=0, sticky="w", pady=(6, 0))

        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        top.bind("<Escape>", lambda e: top.destroy())

    def _on_select(self, _event):
        selection = self.listbox.curselection()
        if not selection or not self.entries:
            return
        entry = self.entries[selection[0]]
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", entry["text"])
        self.preview.configure(state="disabled")
        self.top.clipboard_clear()
        self.top.clipboard_append(entry["text"])
        self.status.configure(text="Copied to clipboard")
