"""Bottom-center recording indicator: mic icon with circular waves, drawn with tkinter.

States: recording (ripples), transcribing (spinner), done (checkmark flash),
error (red badge flash). Every state change cancels the previous one's timer.
"""

import tkinter as tk

CHROMA = "#010203"  # transparent-color key; anything painted this color is see-through
ICON_COLOR = "#6ee7a8"
DIM_ICON_COLOR = "#5a6a62"
ERROR_BG = "#7f1d1d"
# ring shades from bright to dim as ripples expand (no per-item alpha in tkinter)
RING_COLORS = ["#6ee7a8", "#55b986", "#3d8a64", "#285c43", "#183a2a"]

SIZE = 110
RING_START = 20
MAX_R = SIZE // 2 - 4
FPS_MS = 33
SILENCE_THRESHOLD = 0.08  # below this level no new ripples spawn


class Overlay:
    def __init__(self, root, get_levels):
        self.get_levels = get_levels
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", CHROMA)
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f"{SIZE}x{SIZE}+{(sw - SIZE) // 2}+{sh - SIZE - 70}")
        self.canvas = tk.Canvas(
            self.win, width=SIZE, height=SIZE, bg=CHROMA, highlightthickness=0
        )
        self.canvas.pack()
        self._after_id = None
        self._ripples = []
        self._spawn_cooldown = 0
        self._level = 0.0
        self._spin_angle = 0
        self.win.withdraw()

    # -- states ------------------------------------------------------------

    def show(self):
        """Recording: mic with sound-reactive ripples."""
        self._enter_state()
        self._ripples = []
        self._spawn_cooldown = 0
        self._level = 0.0
        self._animate_recording()

    def show_transcribing(self):
        """Dimmed mic with a spinner arc while whisper runs."""
        self._enter_state()
        self._spin_angle = 0
        self._animate_spinner()

    def flash_done(self):
        """Brief checkmark, then hide."""
        self._enter_state()
        self.canvas.delete("all")
        c = SIZE // 2
        self.canvas.create_oval(
            c - RING_START, c - RING_START, c + RING_START, c + RING_START,
            outline=ICON_COLOR, width=2
        )
        self.canvas.create_line(
            c - 8, c + 1, c - 2, c + 7, c + 9, c - 7,
            fill=ICON_COLOR, width=3, capstyle=tk.ROUND, joinstyle=tk.ROUND
        )
        self._after_id = self.win.after(700, self.hide)

    def flash_error(self, text="mic error"):
        self._enter_state()
        self.canvas.delete("all")
        c = SIZE // 2
        r = RING_START + 2
        self.canvas.create_oval(c - r, c - r, c + r, c + r, fill=ERROR_BG, outline="")
        self._draw_mic(c, c, "white")
        self.canvas.create_text(
            c, c + r + 12, text=text, fill="white", font=("Segoe UI", 9)
        )
        self._after_id = self.win.after(1200, self.hide)

    def hide(self):
        self._cancel_pending()
        self.win.withdraw()

    # -- internals ---------------------------------------------------------

    def _enter_state(self):
        self._cancel_pending()
        self.win.deiconify()
        self.win.attributes("-topmost", True)

    def _cancel_pending(self):
        if self._after_id is not None:
            self.win.after_cancel(self._after_id)
            self._after_id = None

    def _draw_mic(self, cx, cy, color):
        # capsule body
        self.canvas.create_oval(cx - 4, cy - 13, cx + 4, cy - 5, fill=color, outline="")
        self.canvas.create_oval(cx - 4, cy - 7, cx + 4, cy + 1, fill=color, outline="")
        self.canvas.create_rectangle(cx - 4, cy - 9, cx + 4, cy - 3, fill=color, outline="")
        # U-shaped holder
        self.canvas.create_arc(
            cx - 8, cy - 10, cx + 8, cy + 6,
            start=180, extent=180, style=tk.ARC, outline=color, width=2
        )
        # stem and base
        self.canvas.create_line(cx, cy + 6, cx, cy + 11, fill=color, width=2)
        self.canvas.create_line(cx - 5, cy + 11, cx + 5, cy + 11, fill=color, width=2)

    def _animate_recording(self):
        levels = self.get_levels()
        latest = levels[-1] if levels else 0.0
        self._level = max(latest, self._level * 0.9)  # fast attack, slow decay

        if self._level > SILENCE_THRESHOLD and self._spawn_cooldown <= 0:
            self._ripples.append({"r": float(RING_START)})
            self._spawn_cooldown = max(4, int(14 - self._level * 10))
        self._spawn_cooldown -= 1

        speed = 1.0 + self._level * 2.0
        for rip in self._ripples:
            rip["r"] += speed
        self._ripples = [r for r in self._ripples if r["r"] <= MAX_R]

        self.canvas.delete("all")
        c = SIZE // 2
        for rip in self._ripples:
            p = (rip["r"] - RING_START) / (MAX_R - RING_START)
            color = RING_COLORS[min(len(RING_COLORS) - 1, int(p * len(RING_COLORS)))]
            r = rip["r"]
            self.canvas.create_oval(
                c - r, c - r, c + r, c + r,
                outline=color, width=max(1, 2 - int(p * 1.5))
            )
        self._draw_mic(c, c, ICON_COLOR)
        self._after_id = self.win.after(FPS_MS, self._animate_recording)

    def _animate_spinner(self):
        self.canvas.delete("all")
        c = SIZE // 2
        self._draw_mic(c, c, DIM_ICON_COLOR)
        r = RING_START
        self.canvas.create_arc(
            c - r, c - r, c + r, c + r,
            start=self._spin_angle, extent=100, style=tk.ARC,
            outline=ICON_COLOR, width=2
        )
        self._spin_angle = (self._spin_angle - 24) % 360
        self._after_id = self.win.after(FPS_MS, self._animate_spinner)
