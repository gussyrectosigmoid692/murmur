# Murmur

Local push-to-talk dictation for Windows, inspired by [Wispr Flow](https://wisprflow.ai). Hold a key, speak, release - your words are transcribed on your own GPU and pasted into whatever window has focus. No cloud, no subscription, no audio leaving your machine.

## How it works

- **Hold Right Alt** and speak; release to finish. Or **tap** it to toggle a hands-free recording and tap again to stop.
- A minimal overlay appears at the bottom of the screen: a mic icon with ripple rings that react to your voice, a spinner while transcribing, a checkmark when your text lands.
- **Esc** cancels a recording; nothing is saved or transcribed.
- The transcript is cleaned up (filler words, stutters) and delivered to the focused window via clipboard paste, with your previous clipboard restored afterward.

## Features

- **Instant capture with pre-roll** — the mic stream stays open, so recording starts with zero latency and includes the ~300 ms _before_ you pressed the key. Your first syllable survives.
- **Fast local transcription** — [faster-whisper](https://github.com/SYSTRAN/faster-whisper) on CUDA (`large-v3-turbo` by default), with automatic CPU fallback if CUDA is unavailable.
- **Custom vocabulary** — edit `vocabulary.txt` to prime the model with names and jargon, plus `wrong => right` correction rules applied to every transcript. Changes apply to the next recording, no restart.
- **Filler-word cleanup** — strips "um"/"uh"/stutters before delivery (toggleable in Settings).
- **Transcript history** — every transcription is logged to `transcripts.jsonl`; browse and re-copy from the tray's History window, or use _Copy last transcript_.
- **System tray app** — Settings, History, recordings folder, and Quit live in the tray. Optional autostart with Windows (no console window).
- **Settings UI** — hotkey, microphone, model, language, delivery mode, all applied live: mic changes reopen the stream, model changes hot-swap without a restart.
- **Audio archive** — every recording is also saved as a 16 kHz mono WAV in `recordings/`.

## Requirements

- Windows 10/11
- Python 3.12 (a virtual environment is recommended)
- NVIDIA GPU for fast transcription (optional — CPU fallback works, just slower)

## Setup

```powershell
git clone <this-repo>
cd <folder-name>
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# optional, for GPU inference (CUDA 12 runtime libraries, ~1 GB):
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

Then run:

```powershell
python main.py
```

The Whisper model downloads to the Hugging Face cache on first launch (~1.6 GB for `large-v3-turbo`); after that everything runs offline. Wait for `whisper model '...' loaded on GPU` in the terminal, then hold Right Alt and talk.

Enable **Start with Windows** in the tray Settings to run it headless at login.

## Configuration

Everything lives next to the code:

| File                | Purpose                                                                      |
| ------------------- | ---------------------------------------------------------------------------- |
| `settings.json`     | Hotkey, mic, model, language, delivery, cleanup — managed by the Settings UI |
| `vocabulary.txt`    | Glossary terms + transcript correction rules (hand-edited)                   |
| `transcripts.jsonl` | Transcript history log                                                       |
| `recordings/`       | Archived WAVs                                                                |

Useful `settings.json` values beyond the UI defaults: `model` accepts any faster-whisper size (`tiny` … `large-v3`, `distil-small.en`); `language` is a Whisper language code or empty for auto-detect; `delivery` is `paste` or `type` (simulated keystrokes for apps that fight clipboard paste).

## Notes

- The mic-in-use indicator stays on while the app runs — that's the persistent stream that makes capture instant; audio is discarded except while you're recording.
- Transcription runs entirely locally. The only network access is the one-time model download.
- The overlay, history, and settings windows are plain tkinter — no browser runtime involved.

## Acknowledgements

Murmur is built on [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT-licensed) by SYSTRAN, a fast reimplementation of [OpenAI Whisper](https://github.com/openai/whisper) using [CTranslate2](https://github.com/OpenNMT/CTranslate2). Model weights are downloaded from the [Hugging Face Hub](https://huggingface.co/) on first launch. Thanks to these projects for making fast, fully local speech recognition possible.

## Project layout

| Module                                                               | Role                                                                        |
| -------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `main.py`                                                            | Wires everything together; event loop, delivery, single-instance lock       |
| `hotkey.py`                                                          | Global hold/tap/cancel key detection                                        |
| `recorder.py`                                                        | Persistent mic stream, pre-roll ring buffer, WAV writing                    |
| `transcriber.py`                                                     | faster-whisper worker thread (GPU with CPU fallback, hot model swap)        |
| `overlay.py`                                                         | Bottom-center status overlay (ripples / spinner / checkmark)                |
| `vocabulary.py`, `cleanup.py`                                        | Transcript post-processing pipeline                                         |
| `history.py`, `history_ui.py`                                        | Transcript log and history window                                           |
| `tray.py`, `settings_ui.py`, `config.py`, `autostart.py`, `theme.py` | Tray icon, settings dialog, persistence, launch-at-login, shared dark theme |

## License

Released under the [MIT License](LICENSE).
