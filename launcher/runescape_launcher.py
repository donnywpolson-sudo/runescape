from __future__ import annotations

import ctypes
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(r"C:\Users\donny\Desktop\runescape")
GAME_ENTRYPOINT = PROJECT_ROOT / "game" / "main.py"
LOG_PATH = PROJECT_ROOT / "logs" / "launcher.log"
LAUNCHER_TITLE = "Hearthvale Launcher"


def append_log(message: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")


def show_error(title: str, message: str) -> None:
    append_log(f"{title}: {message}")
    ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)


def candidate_python_paths() -> list[str]:
    return [
        str(PROJECT_ROOT / ".venv" / "Scripts" / "pythonw.exe"),
        str(PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"),
        "python",
    ]


def resolve_python() -> str:
    for python_path in candidate_python_paths():
        if python_path == "python" or Path(python_path).exists():
            return python_path
    return "python"


def main() -> int:
    if not PROJECT_ROOT.exists():
        show_error(
            LAUNCHER_TITLE,
            f"Project folder was not found:\n{PROJECT_ROOT}\n\nMove it back or rebuild the launcher.",
        )
        return 1

    if not GAME_ENTRYPOINT.exists():
        show_error(
            LAUNCHER_TITLE,
            f"Game entry point was not found:\n{GAME_ENTRYPOINT}",
        )
        return 1

    python_exe = resolve_python()
    command = [python_exe, "-m", "game.main"]
    append_log(f"Launching from {PROJECT_ROOT} with: {' '.join(command)}")

    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        show_error(
            LAUNCHER_TITLE,
            f"Failed to start Python:\n{exc}\n\nInstall Python or rebuild the project virtual environment.",
        )
        return 1

    if completed.stdout:
        append_log(completed.stdout.rstrip())

    if completed.returncode != 0:
        show_error(
            LAUNCHER_TITLE,
            f"Game exited with code {completed.returncode}.\n\nDetails were written to:\n{LOG_PATH}",
        )
        return completed.returncode

    append_log("Game exited normally.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
