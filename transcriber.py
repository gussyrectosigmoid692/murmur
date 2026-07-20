"""Background faster-whisper transcription: submit WAV paths, get text via callback."""

import os
import queue
import sys
import threading
from pathlib import Path

import cleanup
import config
import vocabulary

DEVICE = "cuda"  # falls back to CPU automatically if CUDA is unavailable
GPU_COMPUTE_TYPE = "int8_float16"
CPU_COMPUTE_TYPE = "int8"

_RELOAD = object()  # queue sentinel: reload the model with current config


def _register_cuda_dll_dirs():
    """Make the pip-installed cuBLAS/cuDNN DLLs findable by ctranslate2."""
    nvidia = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia"
    for bin_dir in nvidia.glob("*/bin"):
        # ctranslate2 loads these with plain LoadLibrary, which searches PATH
        # but ignores add_dll_directory; set both to be safe
        os.add_dll_directory(str(bin_dir))
        os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")


class Transcriber:
    def __init__(self, on_result):
        """on_result(text, wav_path) is called from the worker thread per job."""
        self.on_result = on_result
        self._jobs = queue.Queue()
        self._ready = threading.Event()
        threading.Thread(target=self._worker, daemon=True).start()

    def submit(self, wav_path):
        self._jobs.put(str(wav_path))

    def reload(self):
        """Swap to the currently configured model (runs after queued jobs)."""
        self._jobs.put(_RELOAD)

    def _load_model(self):
        from faster_whisper import WhisperModel  # deferred: import alone takes ~1s

        import numpy as np

        model_size = config.get("model")
        if DEVICE == "cuda":
            _register_cuda_dll_dirs()
            try:
                model = WhisperModel(
                    model_size, device="cuda", compute_type=GPU_COMPUTE_TYPE
                )
                # CUDA initializes lazily; run a dummy transcribe now so failures
                # surface here (triggering fallback) and the first real job is fast
                list(model.transcribe(np.zeros(16000, np.float32), language="en")[0])
                print(f"whisper model '{model_size}' loaded on GPU")
                return model
            except Exception as e:
                print(f"CUDA unavailable ({e}); falling back to CPU")
        model = WhisperModel(model_size, device="cpu", compute_type=CPU_COMPUTE_TYPE)
        print(f"whisper model '{model_size}' loaded on CPU")
        return model

    def _worker(self):
        import gc

        model = self._load_model()
        self._ready.set()
        while True:
            job = self._jobs.get()
            if job is _RELOAD:
                model = None
                gc.collect()  # free the old model's VRAM before loading the new one
                model = self._load_model()
                continue
            try:
                prompt, replacements = vocabulary.load()
                segments, _info = model.transcribe(
                    job,
                    language=config.get("language") or None,
                    vad_filter=True,
                    initial_prompt=prompt,
                )
                text = " ".join(s.text.strip() for s in segments).strip()
                text = vocabulary.apply_replacements(text, replacements)
                if config.get("cleanup"):
                    text = cleanup.clean(text)
            except Exception as e:
                print(f"transcription failed: {e}")
                continue
            self.on_result(text, job)
