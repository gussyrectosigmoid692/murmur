"""System tray icon with Settings / Open recordings / Quit."""

import os
import threading

import pystray
from PIL import Image, ImageDraw

_DARK = (28, 28, 34, 255)
_GREEN = (110, 231, 168, 255)


def _icon_image():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 62, 62], fill=_DARK)
    d.rounded_rectangle([26, 12, 38, 34], radius=6, fill=_GREEN)
    d.arc([18, 16, 46, 44], start=0, end=180, fill=_GREEN, width=3)
    d.line([32, 44, 32, 50], fill=_GREEN, width=3)
    d.line([24, 50, 40, 50], fill=_GREEN, width=3)
    return img


class Tray:
    def __init__(self, on_settings, on_history, on_copy_last, on_quit, recordings_dir):
        menu = pystray.Menu(
            pystray.MenuItem("Settings…", lambda icon, item: on_settings(), default=True),
            pystray.MenuItem("History…", lambda icon, item: on_history()),
            pystray.MenuItem("Copy last transcript", lambda icon, item: on_copy_last()),
            pystray.MenuItem(
                "Open recordings",
                lambda icon, item: os.startfile(str(recordings_dir)),
            ),
            pystray.MenuItem("Quit", lambda icon, item: on_quit()),
        )
        self.icon = pystray.Icon("murmur", _icon_image(), "Murmur", menu)

    def run_detached(self):
        threading.Thread(target=self.icon.run, daemon=True).start()

    def stop(self):
        self.icon.stop()
