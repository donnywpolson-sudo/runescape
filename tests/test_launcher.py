from __future__ import annotations

from pathlib import Path

from launcher import hearthvale_launcher as launcher


def test_resolve_project_root_uses_source_checkout(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path, "source_project")
    source_file = project_root / "launcher" / "hearthvale_launcher.py"

    resolved = launcher.resolve_project_root(
        environ={},
        source_file=source_file,
        cwd=tmp_path,
        frozen=False,
    )

    assert resolved == project_root.resolve()


def test_env_project_root_takes_precedence(tmp_path: Path) -> None:
    env_root = _project_root(tmp_path, "env_project")
    source_root = _project_root(tmp_path, "source_project")

    resolved = launcher.resolve_project_root(
        environ={launcher.ENV_PROJECT_ROOT: str(env_root)},
        source_file=source_root / "launcher" / "hearthvale_launcher.py",
        cwd=source_root,
        frozen=False,
    )

    assert resolved == env_root.resolve()


def test_frozen_launcher_resolves_project_root_from_dist_exe(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path, "frozen_project")
    executable_path = project_root / "dist" / "Hearthvale.exe"

    resolved = launcher.resolve_project_root(
        environ={},
        executable_path=executable_path,
        source_file=tmp_path / "missing" / "launcher" / "hearthvale_launcher.py",
        cwd=tmp_path,
        frozen=True,
    )

    assert resolved == project_root.resolve()


def test_frozen_desktop_launcher_resolves_hearthvale_folder(tmp_path: Path) -> None:
    desktop = tmp_path / "Desktop"
    project_root = _project_root(desktop, "hearthvale")
    executable_path = desktop / "Hearthvale.exe"

    resolved = launcher.resolve_project_root(
        environ={},
        executable_path=executable_path,
        source_file=tmp_path / "missing" / "launcher" / "hearthvale_launcher.py",
        cwd=tmp_path,
        frozen=True,
    )

    assert resolved == project_root.resolve()


def test_frozen_desktop_launcher_resolves_capitalized_project_folder(tmp_path: Path) -> None:
    desktop = tmp_path / "Desktop"
    project_root = _project_root(desktop, "Hearthvale")
    executable_path = desktop / "Hearthvale.exe"

    resolved = launcher.resolve_project_root(
        environ={},
        executable_path=executable_path,
        source_file=tmp_path / "missing" / "launcher" / "hearthvale_launcher.py",
        cwd=tmp_path,
        frozen=True,
    )

    assert resolved == project_root.resolve()


def test_candidate_python_paths_prefer_venv_pythonw_then_python(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path, "project")

    assert launcher.candidate_python_paths(project_root) == [
        str(project_root / ".venv" / "Scripts" / "pythonw.exe"),
        str(project_root / ".venv" / "Scripts" / "python.exe"),
        "python",
    ]


def test_build_command_uses_resolved_python(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path, "project")
    pythonw = project_root / ".venv" / "Scripts" / "pythonw.exe"
    pythonw.parent.mkdir(parents=True)
    pythonw.touch()

    assert launcher.resolve_python(project_root) == str(pythonw)
    assert launcher.build_command(project_root) == [str(pythonw), "-m", "game.main"]


def test_build_launcher_requires_explicit_dependency_install_flag() -> None:
    script_path = Path(__file__).resolve().parents[1] / "launcher" / "build_launcher.ps1"
    script = script_path.read_text(encoding="utf-8")

    assert "[switch]$InstallBuildDependencies" in script
    assert "No dependencies were installed" in script
    assert "if (-not $InstallBuildDependencies)" in script
    assert script.index("-m pip install pyinstaller") > script.index("if (-not $InstallBuildDependencies)")


def _project_root(tmp_path: Path, name: str) -> Path:
    project_root = tmp_path / name
    game_dir = project_root / "game"
    game_dir.mkdir(parents=True)
    (game_dir / "main.py").touch()
    return project_root
