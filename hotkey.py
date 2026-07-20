"""Global push-to-talk / tap-to-toggle detection on a configurable key, with Esc to cancel."""

import time

import keyboard

import config

CANCEL_KEY = "esc"
HOLD_THRESHOLD = 0.35  # seconds; shorter presses toggle instead of push-to-talk


class Hotkey:
    def __init__(self, on_start, on_stop, on_cancel):
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_cancel = on_cancel
        self._recording = False
        self._toggled = False  # recording continues after a short tap
        self._key_down = False
        self._pressed_at = 0.0

    def install(self):
        keyboard.hook(self._handle)

    def uninstall(self):
        keyboard.unhook(self._handle)

    def _handle(self, event):
        if event.name == config.get("hotkey"):
            if event.event_type == keyboard.KEY_DOWN:
                if self._key_down:  # OS key-repeat while held
                    return
                self._key_down = True
                if not self._recording:
                    self._recording = True
                    self._toggled = False
                    self._pressed_at = time.monotonic()
                    self.on_start()
                elif self._toggled:  # second tap ends a toggled recording
                    self._recording = False
                    self.on_stop()
            else:
                self._key_down = False
                if self._recording and not self._toggled:
                    if time.monotonic() - self._pressed_at >= HOLD_THRESHOLD:
                        self._recording = False  # it was a hold: release ends it
                        self.on_stop()
                    else:
                        self._toggled = True  # short tap: keep recording
        elif (
            event.name == CANCEL_KEY
            and event.event_type == keyboard.KEY_DOWN
            and self._recording
        ):
            self._recording = False
            self._toggled = False
            self.on_cancel()
