# Hearthvale Project Audit Prompt

You are auditing the local Hearthvale project.

Project root:

`C:\Users\donny\Desktop\hearthvale`

Goal: inspect the current repository and produce a concise, evidence-based audit report of what should be improved. This is read-only. Do not fix code, data, tests, docs, saves, launcher files, generated files, or reports unless the user explicitly gives a separate implementation request.

## Hard Rules

* Do not modify, create, delete, format, migrate, regenerate, normalize, reset, checkout, stash, commit, or revert anything.
* Treat every modified or untracked file as user work.
* Do not run remediation.
* Do not install dependencies.
* Do not run formatters.
* Do not run commands likely to write saves, logs, caches, bytecode, build output, or generated artifacts.
* Do not paste large source files or full command output.
* Evidence must be concise: path plus line, function, class, config key, or test name when useful.
* Code/docs mentioning a feature is not proof it is playable.
* Do not recommend protected clone content. Translate classic grindable RPG feel into original Hearthvale-safe systems, names, lore, items, quests, UI, progression, visuals, and audio.

## Project Facts To Verify

Expected stack:

* Python 3.11
* Panda3D
* pytest

Expected entry points:

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
* Save/account/auth: `game/engine/save.py`, `game/engine/auth.py`, `game/settings.py`, local `users.db`, `saves/<username>.json`, legacy `savegame.json`
* Launcher/build: `launcher/`, `Hearthvale.spec`, `build/`, `dist/`
* Docs: `README.md`, `AGENTS.md`, `docs/`, `GRAPHICS_ANIMATION_NOTE.md`
* Tests: `tests/`

Protected/generated/user-data areas:

* Do not inspect binary/cache/build output unless directly relevant: `.venv/`, `.pytest_cache/`, `build/`, `dist/`, logs, `*.pyc`, `__pycache__/`
* Do not read or modify real local account/save contents unless the user explicitly asks: `users.db`, `saves/`, `savegame.json`

## Required Local Verification

1. Enter the repo and verify location:

```powershell
cd C:\Users\donny\Desktop\hearthvale
pwd
git rev-parse --show-toplevel
git status --short
```

If the path or repo root is wrong, stop and report.

2. List top-level files and folders read-only:

```powershell
Get-ChildItem -Force | Select-Object Mode,Length,LastWriteTime,Name
```

3. Read targeted files only:

* `AGENTS.md`
* `README.md`
* `requirements.txt`
* existing audit/planning docs only if relevant
* `game/settings.py`
* `game/tools/validate_data.py`
* targeted source files under `game/`
* targeted data files under `game/data/`
* targeted tests under `tests/`
* launcher/build files only when auditing launcher/build risk

4. Search for implementation status and risk signals:

```powershell
rg -n "TODO|FIXME|pass|NotImplemented|stub|animation|sprite|tileset|audio|music|settings|save|schema|migration|inventory|equipment|bank|shop|combat|skill|XP|level|quest|dialogue|npc|trade|market|economy|auth|account|launcher|build" AGENTS.md README.md requirements.txt docs launcher game tests -g "!*.pyc" -g "!__pycache__/**"
```

Also search for protected-content drift terms from `AGENTS.md`, including:

```powershell
rg -n "RuneScape|OSRS|Stardew|rune|runite" AGENTS.md README.md docs launcher game tests -g "!*.pyc" -g "!__pycache__/**"
```

Report hits as concise evidence. Distinguish intentional legacy migration/test coverage from new unsafe naming drift.

## Safe Checks

Before running validation, inspect `game/tools/validate_data.py` and confirm it is read-only. If safe:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -m game.tools.validate_data
```

Run tests only if they appear safe/read-only. Prefer the narrowest useful tests first, or run the full suite only if warranted:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -m pytest -p no:cacheprovider
```

Do not run the game or launcher unless feasible, safe, and specifically useful. If manual verification is needed, list steps instead of launching.

After any checks, run:

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

Use this distinction:

* `fully implemented`: code, data, UI/reachability, persistence if relevant, and tests/manual evidence all support it.
* `partially implemented`: core logic exists, but important behavior or coverage is incomplete.
* `partially wired`: logic/data exists but gameplay/UI reachability is incomplete or unclear.
* `present but unused`: module/data exists but no reachable caller or entry point was found.
* `stub/TODO`: placeholder, `pass`, TODO, or non-functional shell.
* `missing`: no meaningful implementation found.
* `manually unverified`: likely present, but requires running the game or visual/manual interaction to confirm.

## Systems To Audit

Audit the implemented state, playability, tests, risks, and highest-yield improvements for:

* Core loop: gather, process/craft, sell/use, level up, unlock better content.
* Skills and progression: XP curves, levels, unlocks, rewards, milestones, grind quality.
* Gathering and resource nodes: depletion, respawn, tiers, required tools, feedback.
* Inventory, equipment, item definitions, item categories, stackability, requirements.
* Crafting/processing: smithing, cooking, recipes, inputs/outputs, timing, XP, unlocks.
* Combat: mobs, attacks, damage, death, drops, combat training styles, ranged/magic support, equipment stats.
* Economy: coins, shops, buy/sell behavior, item value, resource dependency, scarcity.
* Banking/storage: deposit/withdraw, persistence, UI reachability.
* NPCs, dialogue, quests, rewards, quest state, objective tracking, memorable original activity design.
* World and interaction: map size, pathfinding, object reachability, context actions, blocked tiles/scenery.
* UI/HUD/input: action feedback, event log, tabs, login flow, settings, accessibility/low friction.
* Visuals/animation/style/assets: placeholder geometry, procedural renderer hooks, animations, icon/asset policy, audio/music gaps.
* Time/persistence/daily routine support: in-game time, save/load, account-specific saves.
* Save/account/auth: local-only security posture, username sanitization, migrations, legacy compatibility, user-data risks.
* Data/schema validation: shipped JSON data, validation coverage, schema drift, cross-file references.
* Tests: coverage, failing/skipped tests, behavior gaps, missing manual checks.
* Launcher/build/docs: README commands, launcher behavior, build docs, generated output boundaries.
* Originality/IP safety: protected-term drift, protected-like formulas, names, maps, icons, music, dialogue, quests, or recommendations.

## Target Game Feel

Evaluate whether current systems support an original single-player grindable RPG with:

* long-term account-building progression
* meaningful skilling as a main playstyle
* multiple valid goals and sandbox freedom
* useful gathering, processing, crafting, selling, banking, and equipment loops
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

A scoped implementation prompt ready to paste. It must ask for one small, testable improvement and must repeat: do not copy protected content, preserve user work, and do not commit.
