# CODEX_HANDOFF

## Current task

Clean only the ignored local generated `Hearthvale.spec` protected-path drift.

## Hearthvale.spec status

* `Hearthvale.spec` was untracked: `git ls-files -- Hearthvale.spec` returned no tracked path.
* `Hearthvale.spec` was ignored: `git check-ignore -v Hearthvale.spec` reported `.gitignore:15:*.spec`.
* `Hearthvale.spec` was generated/local: `.gitignore` ignores `*.spec`, and `launcher\build_launcher.ps1` invokes PyInstaller with `--name Hearthvale`.

## Action taken

Deleted the ignored local `Hearthvale.spec`.

Reason: the only documented regeneration path is the launcher build command, which runs PyInstaller, may install PyInstaller, and creates `build\` and `dist\` artifacts. There is no documented spec-only regeneration command, so deleting the ignored generated stale spec was the smallest scoped cleanup.

## Files changed

* `CODEX_HANDOFF.md`: recorded the ignored spec cleanup, commands, checks, and remaining protected-term hits.

Pre-existing modified files from the completed launcher/docs remediation batch remain:

* `GRAPHICS_ANIMATION_NOTE.md`
* `README.md`
* `launcher\hearthvale_launcher.py`
* `tests\test_launcher.py`

## Exact commands run

* `git status --short --ignored`
* `git ls-files -- Hearthvale.spec`
* `git check-ignore -v Hearthvale.spec`
* `Get-Content -Raw .gitignore`
* `Get-Content -Raw README.md`
* `Get-Content -Raw requirements.txt`
* `Get-Content -Raw launcher\build_launcher.ps1`
* `Get-Content -Raw Hearthvale.spec`
* `rg -n "pyinstaller|spec|Hearthvale.spec|build_launcher|--name|--onefile" README.md launcher . -g "!*.pyc" -g "!__pycache__/**" -g "!.venv/**" -g "!.pytest_cache/**" -g "!build/**" -g "!dist/**"`
* `Remove-Item -LiteralPath <resolved repo>\Hearthvale.spec`
* `Test-Path .\Hearthvale.spec`
* `git status --short --ignored`
* `rg -ni "RuneScape|OSRS|Stardew|runite|\brune\b" AGENTS.md README.md GRAPHICS_ANIMATION_NOTE.md docs launcher game tests -g "!*.pyc" -g "!__pycache__/**"`
* `Select-String -Path Hearthvale.spec -Pattern 'RuneScape|OSRS|Stardew|runite|\brune\b' -CaseSensitive:$false`

## Check results

* `Test-Path .\Hearthvale.spec`: `False`.
* `git status --short --ignored`: no `!! Hearthvale.spec` entry after deletion.
* Explicit spec protected-term check: `Hearthvale.spec not present`.
* No validation or pytest was run for this task because no gameplay, launcher code, data, validation policy, or tests were changed in this task; only the ignored generated spec was deleted and this handoff was updated.

## Remaining protected-term hits

The tracked-path protected-term search now reports only intentional references:

* `AGENTS.md`: protected-term policy text.
* `game\engine\validation.py`: protected-term validator guard list.
* `tests\test_validation.py`: validator guard test fixture/assertions.
* `game\engine\save.py` and `tests\test_save.py`: legacy save migration compatibility aliases/tests.

## Remaining blockers

None for the ignored local generated spec cleanup.

## Final git status

* `M CODEX_HANDOFF.md`
* `M GRAPHICS_ANIMATION_NOTE.md`
* `M README.md`
* `M launcher\hearthvale_launcher.py`
* `M tests\test_launcher.py`

## Next recommended step

None for this cleanup. Do not start another audit remediation batch without a new scoped request.
