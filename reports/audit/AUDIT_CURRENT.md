# Hearthvale Project Audit Prompt

You are auditing the local Hearthvale project at:

`C:\Users\donny\Desktop\hearthvale`

Goal: inspect the current repository and produce one concise, evidence-based audit report of what should improve. This audit is read-only. Do not fix code, data, tests, docs, saves, launcher files, generated output, or reports unless the user explicitly asks for a separate implementation step after the audit.

If the user explicitly asks for a report file, create exactly one timestamped audit report under `reports\audit\` and no other files. Otherwise, do not create files.

## Hard Rules

* Verify `pwd`, `git rev-parse --show-toplevel`, and `git status --short` before deeper inspection. Stop if the path or repo root is wrong.
* Record `git status --short` before and after checks.
* Treat every modified or untracked file as user work.
* Do not modify, create, delete, format, migrate, regenerate, normalize, reset, checkout, stash, commit, or revert anything except the single timestamped report file if explicitly requested.
* Do not install dependencies.
* Do not run the game, launcher, or build script unless a specific finding benefits from it and the check appears safe.
* Do not run full pytest unless the user explicitly asks.
* Do not run commands likely to write saves, logs, caches, bytecode, build output, or generated artifacts.
* Do not inspect real local account/save contents unless the user explicitly asks: `users.db`, `saves/`, `savegame.json`.
* Do not paste large source files or full command output.
* Stop once you have enough evidence; do not deep-dive unrelated modules.
* Evidence must be concise: path plus line, function, class, config key, command, or test name when useful.
* Code/docs mentioning a feature is not proof it is playable; require player-reachable UI or gameplay-flow evidence, or mark it manually unverified.
* Do not recommend protected clone content. Translate classic grindable RPG feel into original Hearthvale-safe mechanics, names, lore, items, quests, UI, progression, visuals, and audio.
* Flag protected-like naming drift, formulas, or content drift when it appears in player-facing content, docs, tests, or recommendations.

## Project Facts

* Stack: Python 3.11, Panda3D, pytest.
* Main entry point: `python -m game.main`
* Validation: `python -m game.tools.validate_data`
* Tests: `python -m pytest`
* Launcher build: `.\launcher\build_launcher.ps1`
* Built launcher: `.\dist\Hearthvale.exe`
* Source: `game\`
* Launcher: `launcher\`
* Tests: `tests\`
* Data files: `game\data\items.json`, `game\data\skills.json`, `game\data\world.json`, `game\data\recipes.json`, `game\data\quests.json`
* Save/account files: `users.db`, `saves\<username>.json`, `savegame.json`

## Repo-Specific Risk Themes

* `game\world\time.py` currently resets to fixed noon; verify whether static time is intentional or a missing routine system.
* `game\ui\hud.py` only exposes a compact HUD toggle in settings; verify any missing audio/options UI is intentional.
* `game\engine\save.py` still carries legacy `runite`/`rune` migration aliases; treat those as compatibility evidence unless they appear in new player-facing content.
* `game\world\visuals.py` is procedural-first with optional asset hooks; separate placeholder rendering from authored assets and check README/license guidance drift.
* `game\engine\validation.py` enforces protected-term checks; still search player-facing content, docs, tests, and recommendations for drift.

## Required Context

Read targeted files only:

* `AGENTS.md`
* `CODEX_HANDOFF.md` if present
* `README.md`
* `requirements.txt`
* `.gitignore`
* `.codex\META_AUDIT.md` and `.codex\AUDIT.md` if present and readable, but never write to `.codex`
* `docs\icon_asset_options.md` and `RUN_AUDIT_CYCLE.ps1` if present
* `launcher\hearthvale_launcher.py`
* `launcher\build_launcher.ps1`
* `game\main.py`
* `game\settings.py`
* `game\style.py`
* `game\engine\app.py`
* `game\engine\auth.py`
* `game\engine\save.py`
* `game\engine\validation.py`
* `game\tools\validate_data.py`
* `game\world\time.py`
* `game\world\animation.py`
* `game\world\visuals.py`
* `game\ui\hud.py`
* `game\ui\login.py`
* targeted source under `game\engine\`, `game\systems\`, `game\world\`, `game\ui\`, `game\entities\`, `game\data\`
* targeted tests under `tests\` when relevant, especially `tests\test_validation.py`, `tests\test_save.py`, `tests\test_time.py`, `tests\test_launcher.py`, `tests\test_hud.py`, and `tests\test_world_rendering.py`
* `reports\audit\AUDIT_CURRENT.md`, `reports\audit\AUDIT_REPORT_LATEST.md`, and `reports\audit\NEXT_REMEDIATION_PROMPT.md` only when comparing prompt/report drift or an audit cycle is explicitly requested

## Required Searches

Use `rg` when available. Summarize results, do not dump them.
If `rg` is unavailable, use a read-only PowerShell equivalent and report that fallback.

```powershell
rg -n "TODO|FIXME|pass|NotImplemented|stub|animation|sprite|tileset|audio|music|settings|options|time|day|night|routine|save|schema|migration|inventory|equipment|bank|shop|combat|skill|XP|level|quest|dialogue|npc|trade|market|economy|auth|account|launcher|build|asset|icon|license|style" AGENTS.md README.md requirements.txt .gitignore docs launcher game tests -g "!*.pyc" -g "!__pycache__/**"
rg -ni "RuneScape|OSRS|Stardew|runite|\brune\b" AGENTS.md README.md docs launcher game tests -g "!*.pyc" -g "!__pycache__/**"
```

Classify hits as policy text, legacy compatibility, generated or ignored drift, or unsafe active content drift.

Treat `runite` and `rune` hits in save migration code or tests as legacy compatibility unless they appear in new player-facing content, docs, or recommendations.
Treat `pass` hits in test doubles, helper fallbacks, or defensive `except` blocks as non-stub evidence unless they are in production code that should be doing work.

## Safe Checks

* Inspect `game\tools\validate_data.py` first. If it is read-only, run `python -B -m game.tools.validate_data` with `PYTHONDONTWRITEBYTECODE=1`.
* Run only targeted pytest slices that directly support findings and appear read-only. Prefer `python -B -m pytest -p no:cacheprovider` for those slices. Do not run full pytest unless the user explicitly asks for it.
* Do not require running the game, launcher, or build script. Only run them if a specific finding benefits from it and the check appears safe; otherwise document the manual step under `Manual Verification Needed`.
* If tests or validation might write files, skip them and explain why.
* After checks, record `git status --short` again. If the worktree changed, report it immediately and do not clean it up.

## Classification

For each audited system, classify it as exactly one of:

* `fully implemented`
* `partially implemented`
* `partially wired`
* `present but unused`
* `stub/TODO`
* `missing`
* `manually unverified`

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
* Gathering/resource nodes: depletion, respawn, tiers, tools, feedback.
* Inventory/equipment/items: definitions, categories, stackability, requirements, drops.
* Crafting/processing: cooking, smithing, recipes, inputs/outputs, timing, XP, unlocks.
* Combat: mobs, attacks, damage, death, drops, equipment stats, ranged/magic.
* Economy: coins, shops, buy/sell behavior, item value, scarcity, resource dependency.
* Banking/storage: UI reachability, deposit/withdraw, persistence.
* NPCs/dialogue/quests: state, objective tracking, rewards, original activity design.
* World/interaction: map size, pathfinding, reachability, context actions, scenery.
* UI/HUD/input: feedback, tabs, login, settings, accessibility, low friction.
* Visuals/animation/assets/audio/style: placeholder geometry, procedural renderer hooks, authored asset gaps, audio/music gaps, `game\world\animation.py`, `game\world\visuals.py`, `game\style.py`, `game\settings.py`.
* Time/persistence/routines: fixed or advancing time, daily routine support, save/load, account boundaries.
* Save/account/auth: local-only posture, username safety, migrations, legacy compatibility, user-data risk.
* Data/schema validation: JSON coverage, cross-file references, originality guard, schema drift.
* Tests: coverage, failing/skipped checks, manual checks.
* Launcher/build/docs: launcher resolution, build script side effects, generated-output boundaries, README drift.
* Originality/IP safety: active data, docs, tests, launcher, generated files, and recommendation wording.

## Target Game Feel

Evaluate whether current systems support an original single-player grindable RPG with:

* long-term account growth
* meaningful skilling as a main playstyle
* multiple valid goals and sandbox freedom
* gather, process, craft, sell/use, bank, and equipment loops
* scarcity, rarity, risk, visible milestones, and achievement weight
* simple sticky combat that does not crowd out non-combat goals
* memorable original NPC, quest, and activity content
* clear feedback for XP, levels, loot, errors, unlocks, and persistence
* low mechanical friction and readable controls
* original nostalgic texture through safe names, lore, visuals, and audio

If social/community, trading, market, multiplayer, or daily routine goals are discussed, verify implemented support or label them `missing` or `manually unverified`.

## Prioritization

Rank recommendations by:

1. Failing validation or tests, or save/data/originality risk.
2. Player value and core-loop impact.
3. Small safe scope and reuse of existing systems.
4. Testability.
5. Minimal refactor and no new dependencies.

Avoid broad rewrites, speculative architecture, generated-file churn, and clone-like feature requests.
Avoid over-inspection. Stop reading when the evidence is enough to support the report.

## Audit Cycle

If the user explicitly asks for an audit cycle, write the report, then read it and select exactly one smallest safe actionable remediation batch. Do not fix the batch unless the user separately asks for implementation.

Audit-cycle reports and handoffs must clearly state:

* Audit-only: yes
* Remediation applied: no
* Selected batch: `<name>`
* Selected batch severity: `<Low/Medium/Severe>`
* Likely files: `<paths>`
* Suggested commands: `<validation/tests/manual smoke>`
* Next action: run a separate approved remediation goal

The selected-batch summary must be copyable and include:

* Problem statement
* Scope boundaries
* Likely files
* Acceptance criteria
* Suggested focused tests
* Explicit stop condition

## Required Report Format

Output exactly:

```md
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

# Audit Contract

* Audit-only:
* Remediation applied:
* Selected batch:
* Selected batch severity:
* Likely files:
* Suggested commands:
* Next action:

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

# Selected Remediation Batch

* Selected batch:
* Selected batch severity:
* Problem statement:
* Scope boundaries:
* Likely files:
* Acceptance criteria:
* Suggested focused tests:
* Explicit stop condition:

# Next Codex Prompt

A scoped implementation prompt ready to paste. It must ask for one small, testable improvement and repeat: do not copy protected content, preserve user work, and do not commit.
```
