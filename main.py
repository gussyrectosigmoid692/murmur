"""Hold or tap Right Ctrl to dictate; audio is saved to recordings/ and the
transcript is pasted into the focused window."""

import queue
import socket
import sys
import tkinter as tk
from pathlib import Path

import keyboard

import config
import history
import history_ui
import settings_ui
from hotkey import Hotkey
from overlay import Overlay
from recorder import Recorder
from transcriber import Transcriber
from tray import Tray

LOCK_PORT = 52731  # arbitrary localhost port used as a single-instance lock


def acquire_single_instance_lock():
    lock = socket.socket()
    try:
        lock.bind(("127.0.0.1", LOCK_PORT))
    except OSError:
        print("Murmur is already running — close the other instance first.")
        sys.exit(1)
    return lock


def main():
    lock = acquire_single_instance_lock()  # held for process lifetime  # noqa: F841
    root = tk.Tk()
    root.withdraw()

    recorder = Recorder()
    try:
        recorder.open()  # mic stays open for the app's lifetime (instant start + pre-roll)
    except Exception as e:
        print(f"could not open microphone: {e}")
        sys.exit(1)
    overlay = Overlay(root, lambda: recorder.levels)
    events = queue.Queue()
    recording = False

    hotkey = Hotkey(
        on_start=lambda: events.put(("start",)),
        on_stop=lambda: events.put(("stop",)),
        on_cancel=lambda: events.put(("cancel",)),
    )
    hotkey.install()
    transcriber = Transcriber(
        on_result=lambda text, wav: events.put(("text", text, wav))
    )

    recordings_dir = Path(__file__).resolve().parent / "recordings"
    recordings_dir.mkdir(exist_ok=True)
    tray = Tray(
        on_settings=lambda: events.put(("settings",)),
        on_history=lambda: events.put(("history",)),
        on_copy_last=lambda: events.put(("copy_last",)),
        on_quit=lambda: events.put(("quit",)),
        recordings_dir=recordings_dir,
    )
    tray.run_detached()

    def deliver(text):
        if config.get("delivery") == "type":
            keyboard.write(text)
            return
        try:
            previous = root.clipboard_get()
        except tk.TclError:
            previous = None  # empty or non-text clipboard; nothing to restore
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        keyboard.send("ctrl+v")
        if previous is not None:
            def restore():
                root.clipboard_clear()
                root.clipboard_append(previous)
            root.after(800, restore)

    def poll():
        nonlocal recording
        try:
            while True:
                ev = events.get_nowait()
                if ev[0] == "start":
                    try:
                        recorder.start()
                        overlay.show()
                        recording = True
                    except Exception as e:
                        print(f"could not start recording: {e}")
                        overlay.flash_error()
                elif ev[0] == "stop":
                    recording = False
                    try:
                        path = recorder.stop()
                    except Exception as e:
                        print(f"error saving recording: {e}")
                        overlay.hide()
                        continue
                    if path is not None:
                        print(f"saved {path}, transcribing...")
                        overlay.show_transcribing()
                        transcriber.submit(path)
                    else:
                        print("recording too short, discarded")
                        overlay.hide()
                elif ev[0] == "cancel":
                    recording = False
                    recorder.cancel()
                    overlay.hide()
                    print("recording cancelled")
                elif ev[0] == "settings":
                    settings_ui.show(
                        root,
                        on_device_change=recorder.reopen,
                        on_model_change=transcriber.reload,
                    )
                elif ev[0] == "history":
                    history_ui.show(root)
                elif ev[0] == "copy_last":
                    entry = history.last()
                    if entry:
                        root.clipboard_clear()
                        root.clipboard_append(entry["text"])
                        root.update()
                        print(f"copied last transcript: {entry['text'][:60]}")
                    else:
                        print("no transcripts yet")
                elif ev[0] == "quit":
                    root.quit()
                    return
                elif ev[0] == "text":
                    text, wav = ev[1], ev[2]
                    if text:
                        print(f"transcript: {text}")
                        history.append(text, wav, config.get("model"))
                        deliver(text)
                        if not recording:
                            overlay.flash_done()
                    else:
                        print("transcript: (no speech detected)")
                        if not recording:
                            overlay.flash_error("no speech")
        except queue.Empty:
            pass
        root.after(30, poll)

    poll()
    print(
        f"Hold {config.get('hotkey').title()} to record (release to finish), "
        "or tap it to toggle.\n"
        "Esc cancels a recording. Quit from the tray icon (or Ctrl+C here)."
    )
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        tray.stop()
        hotkey.uninstall()
        recorder.stop()
        recorder.close()


if __name__ == "__main__":
    main()
