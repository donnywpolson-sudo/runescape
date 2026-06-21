from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ENV_PROJECT_ROOT = "HEARTHVALE_PROJECT_ROOT"
LAUNCHER_TITLE = "Hearthvale Launcher"
DESKTOP_PROJECT_FOLDER_NAMES = ("hearthvale", "Hearthvale")


def append_log(message: str, project_root: Path | None = None) -> None:
    log_path = _log_path(project_root)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")


def show_error(title: str, message: str, project_root: Path | None = None) -> None:
    append_log(f"{title}: {message}", project_root)
    ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)


def project_root_candidates(
    *,
    environ: dict[str, str] | os._Environ[str] = os.environ,
    executable_path: str | Path | None = None,
    source_file: str | Path | None = None,
    cwd: str | Path | None = None,
    frozen: bool | None = None,
) -> list[Path]:
    candidates: list[Path] = []
    env_project_root = environ.get(ENV_PROJECT_ROOT, "").strip()
    if env_project_root:
        candidates.append(Path(env_project_root))

    if frozen is None:
        frozen = bool(getattr(sys, "frozen", False))
    if frozen:
        executable = Path(executable_path or sys.executable)
        executable_dir = executable.resolve().parent
        candidates.append(executable_dir.parent)
        for folder_name in DESKTOP_PROJECT_FOLDER_NAMES:
            candidates.append(executable_dir / folder_name)

    source = Path(source_file or __file__)
    candidates.append(source.resolve().parent.parent)
    candidates.append(Path(cwd or Path.cwd()).resolve())
    return _unique_paths(candidates)


def resolve_project_root(
    *,
    environ: dict[str, str] | os._Environ[str] = os.environ,
    executable_path: str | Path | None = None,
    source_file: str | Path | None = None,
    cwd: str | Path | None = None,
    frozen: bool | None = None,
) -> Path | None:
    for candidate in project_root_candidates(
        environ=environ,
        executable_path=executable_path,
        source_file=source_file,
        cwd=cwd,
        frozen=frozen,
    ):
        if _is_project_root(candidate):
            return candidate
    return None


def candidate_python_paths(project_root: Path) -> list[str]:
    return [
        str(project_root / ".venv" / "Scripts" / "pythonw.exe"),
        str(project_root / ".venv" / "Scripts" / "python.exe"),
        "python",
    ]


def resolve_python(project_root: Path) -> str:
    for python_path in candidate_python_paths(project_root):
        if python_path == "python" or Path(python_path).exists():
            return python_path
    return "python"


def build_command(project_root: Path) -> list[str]:
    return [resolve_python(project_root), "-m", "game.main"]


def main() -> int:
    project_root = resolve_project_root()
    if project_root is None:
        show_error(
            LAUNCHER_TITLE,
            "Project folder was not found.\n\n"
            f"Set {ENV_PROJECT_ROOT} to the project folder, or run the launcher "
            "from this repo's dist folder. A Desktop launcher also checks for "
            "hearthvale or Hearthvale folders next to it.",
        )
        return 1

    game_entrypoint = project_root / "game" / "main.py"
    if not game_entrypoint.exists():
        show_error(
            LAUNCHER_TITLE,
            f"Game entry point was not found:\n{game_entrypoint}",
            project_root,
        )
        return 1

    command = build_command(project_root)
    append_log(f"Launching from {project_root} with: {' '.join(command)}", project_root)

    try:
        completed = subprocess.run(
            command,
            cwd=project_root,
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
            project_root,
        )
        return 1

    if completed.stdout:
        append_log(completed.stdout.rstrip(), project_root)

    if completed.returncode != 0:
        log_path = _log_path(project_root)
        show_error(
            LAUNCHER_TITLE,
            f"Game exited with code {completed.returncode}.\n\nDetails were written to:\n{log_path}",
            project_root,
        )
        return completed.returncode

    append_log("Game exited normally.", project_root)
    return 0


def _is_project_root(path: Path) -> bool:
    return path.is_dir() and (path / "game" / "main.py").is_file()


def _log_path(project_root: Path | None = None) -> Path:
    root = project_root or Path.cwd()
    return root / "logs" / "launcher.log"


def _unique_paths(paths: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        normalized = str(path.resolve()).lower()
        if normalized in seen:
            continue
        unique.append(path.resolve())
        seen.add(normalized)
    return unique


if __name__ == "__main__":
    sys.exit(main())
