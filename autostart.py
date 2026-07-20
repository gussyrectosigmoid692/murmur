"""Launch-at-login via a shortcut in the user's Startup folder."""

import os
import subprocess
import sys
from pathlib import Path

SHORTCUT = (
    Path(os.environ["APPDATA"])
    / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    / "Murmur.lnk"
)


def is_enabled():
    return SHORTCUT.exists()


def enable():
    project = Path(__file__).resolve().parent
    # pythonw.exe: no console window at login
    pythonw = Path(sys.executable).parent / "pythonw.exe"
    cmd = (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut('{SHORTCUT}'); "
        f"$s.TargetPath = '{pythonw}'; "
        f"$s.Arguments = '\"{project / 'main.py'}\"'; "
        f"$s.WorkingDirectory = '{project}'; "
        "$s.Save()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd],
        check=True, capture_output=True,
    )


def disable():
    SHORTCUT.unlink(missing_ok=True)
