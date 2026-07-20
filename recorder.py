"""Persistent microphone stream writing to WAV on demand, with pre-roll.

The input stream stays open for the app's lifetime so recording start is
instant (no device-activation latency). A rolling ring buffer keeps the last
~300 ms of audio, which is prepended to each recording to catch speech that
began just before the hotkey was pressed.
"""

import collections
import threading
import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

import config

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCKSIZE = SAMPLE_RATE // 30  # ~33 ms per callback
MIN_DURATION = 0.3  # seconds; shorter recordings are discarded as accidental taps
PRE_ROLL = 0.3  # seconds of audio kept from before recording starts


class Recorder:
    def __init__(self, out_dir="recordings"):
        self.out_dir = Path(out_dir)
        self.levels = collections.deque([0.0] * 24, maxlen=24)
        self._pre_roll = collections.deque(
            maxlen=max(1, round(PRE_ROLL * SAMPLE_RATE / BLOCKSIZE))
        )
        self._lock = threading.Lock()  # guards _wav and _pre_roll across threads
        self._stream = None
        self._wav = None
        self._path = None
        self._started_at = None

    def open(self):
        """Open the persistent input stream. Call once at startup."""
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=BLOCKSIZE,
            device=self._resolve_device(config.get("input_device")),
            callback=self._callback,
        )
        self._stream.start()

    def reopen(self):
        """Switch to the currently configured input device."""
        self.cancel()  # drop any in-flight recording tied to the old device
        self.close()
        self._pre_roll.clear()
        self.open()

    @staticmethod
    def _resolve_device(name):
        if not name:
            return None  # system default
        for i, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0 and dev["name"] == name:
                return i
        print(f"input device '{name}' not found; using system default")
        return None

    def close(self):
        """Release the microphone. Call once at shutdown."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def start(self):
        if self._stream is None:
            raise RuntimeError("microphone stream is not open")
        with self._lock:
            if self._wav is not None:
                return
            self.out_dir.mkdir(parents=True, exist_ok=True)
            self._path = self.out_dir / time.strftime("rec_%Y%m%d_%H%M%S.wav")
            self._wav = wave.open(str(self._path), "wb")
            self._wav.setnchannels(CHANNELS)
            self._wav.setsampwidth(2)
            self._wav.setframerate(SAMPLE_RATE)
            for block in self._pre_roll:
                self._wav.writeframes(block.tobytes())
            self._started_at = time.monotonic()

    def stop(self):
        """Finish the recording. Returns the saved path, or None if discarded."""
        path = self._close_wav()
        if path is None:
            return None
        if time.monotonic() - self._started_at < MIN_DURATION:
            path.unlink(missing_ok=True)
            return None
        return path

    def cancel(self):
        """Finish the recording and delete the file."""
        path = self._close_wav()
        if path is not None:
            path.unlink(missing_ok=True)

    def _close_wav(self):
        with self._lock:
            if self._wav is None:
                return None
            self._wav.close()
            self._wav = None
            path, self._path = self._path, None
            return path

    def _callback(self, indata, frames, time_info, status):
        if status:
            print(f"audio status: {status}")
        block = indata.copy()
        with self._lock:
            self._pre_roll.append(block)
            if self._wav is not None:
                self._wav.writeframes(block.tobytes())
        rms = np.sqrt(np.mean((block.astype(np.float32) / 32768.0) ** 2))
        self.levels.append(min(1.0, float(rms) * 6.0))
