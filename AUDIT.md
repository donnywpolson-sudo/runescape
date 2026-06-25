# Hearthvale Project Audit Prompt

You are auditing the local Hearthvale project at:

`C:\Users\donny\Desktop\hearthvale`

Goal: inspect the current repository and produce one concise, evidence-based audit report of what should be improved. This audit is read-only. Do not fix code, data, tests, docs, saves, launcher files, generated files, or reports unless the user explicitly gives a separate implementation request after the audit.

This is the second stage of the workflow: first use `META_AUDIT.md` to refresh this prompt, then use this prompt to audit the project and finish with a paste-ready implementation prompt.

## Hard Rules

* Verify the local path and repo root before inspecting anything else. Stop if they are wrong.
* Record `git status --short` before and after checks.
* Treat every modified or untracked file as user work.
* Do not modify, create, delete, format, migrate, regenerate, normalize, reset, checkout, stash, commit, or revert anything, except for the single timestamped report file if the user explicitly requested one.
* Do not install dependencies, run formatters, run the game, or run launcher/build commands during the audit.
* Do not run commands likely to write saves, logs, caches, bytecode, build output, or generated artifacts.
* Do not inspect real local account/save contents unless the user explicitly asks: `users.db`, `saves/`, `savegame.json`.
* Do not paste large source files or full command output.
* Evidence must be concise: path plus line, function, class, config key, command, or test name when useful.
* Code/docs mentioning a feature is not proof it is playable; require player-reachable UI or gameplay-flow evidence, or mark it manually unverified.
* Do not recommend protected clone content. Translate classic grindable RPG feel into original Hearthvale-safe mechanics, names, lore, items, quests, UI, progression, visuals, and audio.

## Project Facts To Verify

Expected stack:

* Python 3.11
* Panda3D
* pytest

Expected commands:

* Game: `python -m game.main`
* Data validation: `python -m game.tools.validate_data`
* Tests: `python -m pytest`
* Launcher build: `.\launcher\build_launcher.ps1`
* Built launcher: `.\dist\Hearthvale.exe`

Important repo areas:

* Source: `game/`
* Systems: `game/systems/`
* Engine: `game/engine/`
* World/rendering: `game/world/`
* UI: `game/ui/`
* Data: `game/data/items.json`, `skills.json`, `world.json`, `recipes.json`, `quests.json`
* Validation: `game/engine/validation.py`, `game/tools/validate_data.py`
* Save/account/auth: `game/engine/save.py`, `game/engine/auth.py`, `game/settings.py`
* User data boundaries: `users.db`, `saves/<username>.json`, legacy `savegame.json`
* Launcher/build docs: `launcher/`, `Hearthvale.spec`, `build/`, `dist/`, `README.md`
* Planning/docs: `AGENTS.md`, `docs/`, `GRAPHICS_ANIMATION_NOTE.md`
* Audit workflow drift: `reports\audit\AUDIT_CURRENT.md`, `reports\audit\AUDIT_REPORT_LATEST.md`, `reports\audit\NEXT_REMEDIATION_PROMPT.md`
* Tests: `tests/`

Protected/generated areas:

* Skip `.venv/`, `.pytest_cache/`, `build/`, `dist/`, `logs/`, `*.pyc`, `__pycache__/`, binary files, and real save/account files unless directly relevant and explicitly allowed.

## Required Local Verification

Run from PowerShell:

```powershell
cd C:\Users\donny\Desktop\hearthvale
pwd
git rev-parse --show-toplevel
git status --short
Get-ChildItem -Force | Select-Object Mode,Length,LastWriteTime,Name
```

If `pwd` or `git rev-parse --show-toplevel` does not point at this repo, stop and report.

## Targeted Inspection

Read targeted files only:

* `AGENTS.md`
* `README.md`
* `requirements.txt`
* `game/settings.py`
* `game/style.py`
* `game/tools/validate_data.py`
* `docs/icon_asset_options.md`
* targeted source under `game/`
* targeted data under `game/data/`
* targeted tests under `tests/`, especially `tests/test_validation.py`, `tests/test_save.py`, `tests/test_time.py`, `tests/test_auth.py`, `tests/test_login.py`, `tests/test_hud.py`, `tests/test_world_rendering.py`, and `tests/test_app_audio.py`
* launcher/build files only when auditing launcher/build risk
* docs/planning files only when they affect current behavior or recommendations
* `reports\audit\AUDIT_CURRENT.md`, `reports\audit\AUDIT_REPORT_LATEST.md`, and `reports\audit\NEXT_REMEDIATION_PROMPT.md` when comparing prompt/report drift or an audit cycle is explicitly requested

Search implementation and risk signals:

```powershell
rg -n "TODO|FIXME|pass|NotImplemented|stub|animation|sprite|tileset|palette|style|icon|license|audio|music|sound|sfx|volume|mute|settings|save|schema|migration|inventory|equipment|bank|shop|combat|skill|XP|level|quest|dialogue|npc|trade|market|economy|auth|account|launcher|build" AGENTS.md README.md requirements.txt docs launcher game tests -g "!*.pyc" -g "!__pycache__/**"
```

Search protected-content drift terms from `AGENTS.md`:

```powershell
rg -n "RuneScape|OSRS|Stardew|runite|\brune\b" AGENTS.md README.md docs launcher game tests -g "!*.pyc" -g "!__pycache__/**"
```

Report hits as concise evidence. Distinguish allowed policy text, legacy compatibility/migration coverage, and unsafe gameplay/content drift.

## Safe Checks

Before validation, inspect `game/tools/validate_data.py` and confirm it is read-only. If safe:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -m game.tools.validate_data
```

Run only targeted pytest checks that are useful for audit evidence and appear read-only, especially `tests/test_validation.py`, `tests/test_save.py`, `tests/test_time.py`, `tests/test_auth.py`, `tests/test_login.py`, `tests/test_hud.py`, `tests/test_world_rendering.py`, and `tests/test_app_audio.py`. Do not run full pytest unless the user explicitly asks for it; recommend the user run it when needed.

After checks:

```powershell
git status --short
```

If the worktree changed, report it immediately and do not clean it up.

## Classification Required

For each audited system, classify it as exactly one of:

* fully implemented
* partially implemented
* partially wired
* present but unused
* stub/TODO
* missing
* manually unverified

Definitions:

* `fully implemented`: code, data, UI/reachability, persistence if relevant, and tests/manual evidence all support it.
* `partially implemented`: core logic exists, but important behavior or coverage is incomplete.
* `partially wired`: logic/data exists but gameplay/UI reachability is incomplete or unclear.
* `present but unused`: module/data exists but no reachable caller or entry point was found.
* `stub/TODO`: placeholder, `pass`, TODO, or non-functional shell.
* `missing`: no meaningful implementation found.
* `manually unverified`: likely present, but requires running the game or visual/manual interaction to confirm.

## Systems To Audit

Audit implemented state, playability, tests, risks, and highest-yield improvements for:

* Core loop: gather, process/craft, sell/use, level up, unlock better content.
* Skills/progression: XP curves, levels, unlocks, rewards, milestones, grind quality.
* Gathering/resource nodes: depletion, respawn, tiers, required tools, feedback.
* Inventory/equipment/items: definitions, categories, stackability, requirements.
* Crafting/processing: smithing, cooking, recipes, inputs/outputs, timing, XP, unlocks.
* Combat: mobs, attacks, damage, death, drops, combat training styles, ranged/magic support, equipment stats.
* Economy: coins, shops, buy/sell behavior, item value, dependency, scarcity.
* Banking/storage: deposit/withdraw, persistence, UI reachability.
* NPCs/dialogue/quests: state, objective tracking, rewards, original activity design.
* World/interaction: map size, pathfinding, object reachability, context actions, blocked tiles/scenery.
* UI/HUD/input: feedback, event log, tabs, login flow, settings, accessibility/low friction.
* Visuals/animation/assets/audio/style: placeholder geometry, procedural renderer hooks, animations, icons, audio/music gaps, settings.
* Time/persistence/routines: in-game time, save/load, account-specific saves.
* Save/account/auth: local-only posture, username safety, migrations, legacy compatibility, user-data risks.
* Data/schema validation: JSON data, validation coverage, schema drift, cross-file references.
* Tests: coverage, failing/skipped tests, behavior gaps, manual checks.
* Launcher/build/docs: README commands, launcher behavior, generated output boundaries.
* Originality/IP safety: protected-term drift, protected-like formulas, names, maps, icons, music, dialogue, quests, or recommendations.

## Target Game Feel

Evaluate whether current systems support an original single-player grindable RPG with:

* long-term account-building progression
* meaningful skilling as a main playstyle
* multiple valid goals and sandbox freedom
* gathering, processing, crafting, selling, banking, and equipment loops
* scarcity, rarity, risk, achievement weight, and visible milestones
* simple but sticky combat that does not crowd out non-combat goals
* memorable original NPC/quest/activity content
* clear UI feedback for XP, levels, loot, errors, unlocks, and persistence
* low mechanical friction and readable controls
* original nostalgic texture through safe names, lore, visuals, and audio

If social/community, market, trading, multiplayer, or online-account goals are discussed, verify implemented support or label them missing/manual verification needed.

## Prioritization Rules

Rank recommendations by:

1. Failing validation/tests or save/data compatibility risk.
2. Player value and fun.
3. Improvements to the gather-process-sell/use-level-unlock loop.
4. Low implementation risk and small scope.
5. Reuse of existing systems.
6. Testability.
7. Originality/IP safety.

Avoid broad rewrites, new dependencies, speculative architecture, and clone-like feature requests.

## Required Report Format

Output exactly:

# Snapshot

* Local path:
* Repo root:
* Git status before:
* Git status after:
* Stack:
* Entry points:
* Run command:
* Test command:
* Data files:
* Save/account files:
* Checks run:
* Checks result:
* Worktree changed after checks:

# System Inventory

System | Status | Evidence | Notes

# Findings

Severity | Finding | Evidence | Why it matters | Recommended next step

# Game-Feel Assessment

Area | Status | Evidence | Gap | Safe recommendation

# Originality/IP Safety

Risk | Evidence | Classification | Recommendation

# Tests And Validation

Check | Result | Evidence | Notes

# Manual Verification Needed

Manual check | Why | Steps

# Recommended Next Work

Rank | Feature/Fix | Why | Complexity | Risk | Files likely touched | Acceptance criteria | Suggested tests

# Next Codex Prompt

A single paste-ready implementation prompt in a fenced text block, with no commentary after it. It must include exact scope, files, commands, stop conditions, and forbidden actions. It must ask for one small, testable improvement and must repeat: do not copy protected content, preserve user work, and do not commit.
