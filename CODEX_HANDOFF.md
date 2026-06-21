# CODEX_HANDOFF

## Current task

Implemented only the selected audit batch: Launcher build dependency install guard.

## Files changed

* `launcher\build_launcher.ps1`: added explicit `-InstallBuildDependencies` opt-in and default fail-fast behavior when PyInstaller is missing.
* `README.md`: documented that PyInstaller must be installed explicitly, or the build script must be run with `-InstallBuildDependencies`.
* `tests\test_launcher.py`: added a focused test proving the build script requires an explicit dependency-install flag before `pip install pyinstaller`.
* `CODEX_HANDOFF.md`: recorded this remediation, checks, and remaining blockers.

Pre-existing audit/process artifacts remain dirty/staged and were preserved:

* `RUN_AUDIT_CYCLE.ps1`
* `reports\audit\AUDIT_CURRENT.md`
* `reports\audit\AUDIT_REPORT_LATEST.md`
* `reports\audit\AUDIT_REPORT_20260621_151336.md`
* `reports\audit\AUDIT_REPORT_20260621_153137.md`
* `reports\audit\AUDIT_REPORT_20260621_153903.md`

## Exact guard behavior added

* Default build behavior no longer installs PyInstaller when it is missing.
* If PyInstaller is missing and `-InstallBuildDependencies` is not supplied, the script throws a clear message:
  * PyInstaller is not installed.
  * No dependencies were installed.
  * Install explicitly with `"<project>\.venv\Scripts\python.exe" -m pip install pyinstaller`, or rerun with `-InstallBuildDependencies`.
* If PyInstaller is already installed, the existing build path is preserved.
* If `-InstallBuildDependencies` is supplied and PyInstaller is missing, the script may run `python -m pip install pyinstaller` explicitly.

## Commands/results

* `git status --short`: showed pre-existing audit/process changes before this batch.
* Read `CODEX_HANDOFF.md`, `README.md`, `requirements.txt`, `launcher\build_launcher.ps1`, and `tests\test_launcher.py`.
* `rg -n "pip install|python -m pip|PyInstaller|throw|InstallBuildDependencies|No dependencies were installed" launcher\build_launcher.ps1 README.md tests\test_launcher.py`: confirmed the install command is behind `-InstallBuildDependencies` and the docs mention explicit install.
* `python -B -m pytest -p no:cacheprovider tests\test_launcher.py`: 8 passed.
* `git diff --check`: passed.
* `git diff --cached --check`: passed.

## Dependency installation attempted

No. The PyInstaller build script was not run, and no dependency installation was attempted.

## Remaining blockers

Low

* Pre-existing audit/process artifacts remain dirty/staged in the worktree.
* Manual `.\launcher\build_launcher.ps1` smoke was not run because it can write generated `build\` and `dist\` output and was not explicitly approved.

Medium

* None for this launcher build dependency guard batch.

Severe

* None.

## Final git status

* `MM CODEX_HANDOFF.md`
* `M README.md`
* `M RUN_AUDIT_CYCLE.ps1`
* `M launcher\build_launcher.ps1`
* `MM reports\audit\AUDIT_CURRENT.md`
* `A reports\audit\AUDIT_REPORT_20260621_151336.md`
* `MM reports\audit\AUDIT_REPORT_LATEST.md`
* `M tests\test_launcher.py`
* `?? reports\audit\AUDIT_REPORT_20260621_153137.md`
* `?? reports\audit\AUDIT_REPORT_20260621_153903.md`

## Next action

Stop after this batch. Run manual launcher build smoke only if explicitly approved because it writes generated build output.
