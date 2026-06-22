# Hearthvale Reusable Audit Prompt

You are auditing the local Hearthvale project at `C:\Users\donny\Desktop\hearthvale`.

Goal: inspect the repository and produce one concise, evidence-based audit report of what should improve. This is read-only unless the user explicitly asks you to create or update report files under `reports\audit`. Do not fix code, data, tests, saves, launcher files, or generated output during the audit.

## Hard Rules

- Verify `pwd`, `git rev-parse --show-toplevel`, and `git status --short` before deeper inspection. Stop if the path or repo root is wrong.
- Treat every modified or untracked file as user work. Do not clean, reset, checkout, stash, revert, delete, migrate, normalize, format, regenerate, commit, or install dependencies.
- Read `.codex\META_AUDIT.md` and `.codex\AUDIT.md` if present and readable, but never write to `.codex`.
- Read `CODEX_HANDOFF.md` first if present.
- Skip `.venv/`, caches, build/dist/logs, binary files, bytecode, and real user save/account data unless explicitly allowed.
- Do not run the game, launcher, build script, manual smoke, or full pytest during the audit.
- Do not paste large source files or full logs.
- Evidence must stay concise: path plus line/function/class/config key, command, or test name.
- Code/docs mentioning a feature are not proof it is playable.
- Do not recommend protected clone content; translate the desired grindy RPG feel into original Hearthvale-safe names, lore, items, quests, UI, visuals, and audio.

## Required Context

Read targeted files only:

- `AGENTS.md`, `CODEX_HANDOFF.md` if present, `README.md`, `requirements.txt`, `.gitignore`
- `.codex\META_AUDIT.md` and `.codex\AUDIT.md` if present
- `GRAPHICS_ANIMATION_NOTE.md` and `RUN_AUDIT_CYCLE.ps1` if present
- `game/settings.py`, `game/main.py`, `game/engine/app.py`, `game/world/time.py`
- `game/engine/save.py`, `game/engine/auth.py`, `game/engine/validation.py`, `game/tools/validate_data.py`
- targeted files under `game/systems/`, `game/world/`, `game/ui/`, `game/data/`, `tests/`
- `launcher/`, `Hearthvale.spec`, and `docs/` when relevant to launcher/build, visuals, audio, originality, or docs drift

## Required Searches

Use `rg` when available. Summarize results, do not dump them.

```powershell
rg -n "TODO|FIXME|pass|NotImplemented|stub|animation|sprite|tileset|audio|music|settings|options|time|day|night|routine|save|schema|migration|inventory|equipment|bank|shop|combat|skill|XP|level|quest|dialogue|npc|trade|market|economy|auth|account|launcher|build" AGENTS.md README.md requirements.txt docs launcher game tests -g "!*.pyc" -g "!__pycache__/**"
rg -ni "runescape|osrs|stardew|runite|\brune\b" AGENTS.md README.md docs launcher game tests -g "!*.pyc" -g "!__pycache__/**"
```

Classify hits as policy text, legacy compatibility, generated or ignored drift, or unsafe active content drift.

## Safe Checks

- Inspect `game/tools/validate_data.py` first. If it is read-only, run `python -B -m game.tools.validate_data` with `PYTHONDONTWRITEBYTECODE=1`.
- Run only targeted pytest slices that directly support findings and appear read-only. Never run full pytest unless the user explicitly asks.
- After checks, record `git status --short` again.

## Classification

For each audited system, classify it as exactly one of:

- `fully implemented`
- `partially implemented`
- `partially wired`
- `present but unused`
- `stub/TODO`
- `missing`
- `manually unverified`

## Systems To Audit

Audit implemented state, playability, tests, risks, and highest-yield improvements for:

- Core loop: gather, process/craft, sell/use, level up, unlock
- Skills/progression: XP curves, levels, unlocks, rewards, milestones, grind quality
- Gathering/resource nodes: depletion, respawn, tiers, tools, feedback
- Inventory/equipment/items: definitions, stackability, requirements, drops
- Crafting/processing: cooking, smithing, recipes, timing, XP, unlocks
- Combat: mobs, styles, damage, death, drops, equipment stats, ranged/magic
- Economy: coins, shops, buy/sell behavior, scarcity, resource dependency
- Banking/storage: UI reachability, deposit/withdraw, persistence
- NPCs/dialogue/quests: state, objective tracking, rewards, original activity design
- World/interaction: map size, pathfinding, object reachability, context actions, scenery
- UI/HUD/input: feedback, tabs, login, settings, accessibility, low friction
- Visuals/animation/assets/audio/style: placeholder geometry, procedural hooks, authored asset gaps, audio/music gaps
- Time/persistence/routines: fixed or advancing time, daily routine support, save/load, account boundaries
- Save/account/auth: local-only posture, username safety, migrations, legacy compatibility, user-data risk
- Data/schema validation: JSON coverage, cross-file references, originality guard, schema drift
- Tests: coverage, failing or skipped checks, manual checks
- Launcher/build/docs: launcher resolution, build script side effects, generated-output boundaries, README drift
- Originality/IP safety: active data, docs, tests, launcher, generated files, and recommendation wording

## Target Game Feel

Evaluate whether current systems support an original single-player grindable RPG with:

- long-term account growth
- meaningful skilling as a main playstyle
- multiple valid goals and sandbox freedom
- gather, process, craft, sell/use, bank, and equipment loops
- scarcity, rarity, risk, visible milestones, and achievement weight
- simple sticky combat that does not crowd out non-combat goals
- memorable original NPC, quest, and activity content
- clear feedback for XP, levels, loot, errors, unlocks, and persistence
- low mechanical friction and readable controls
- original nostalgic texture through safe names, lore, visuals, and audio

If social/community, trading, market, multiplayer, or daily routine goals are discussed, verify implemented support or label them `missing` or `manually unverified`.

## Prioritization

Rank recommendations by:

1. Failing validation or tests, or save/data/originality risk
2. Player value and core-loop impact
3. Small safe scope and reuse of existing systems
4. Testability
5. Minimal refactor and no new dependencies

Avoid broad rewrites, speculative architecture, generated-file churn, and clone-like feature requests.

## Audit-Cycle Rule

If the user asks for an audit cycle, write the report, then read it and select exactly one smallest safe actionable remediation batch. Do not fix the batch unless the user separately asks for implementation. If source, gameplay, data, save, or test remediation is forbidden, select only docs, process, or report work, or state that no safe batch is selectable.

Audit-cycle reports and handoffs must clearly state:

- Audit-only: yes
- Remediation applied: no
- Selected batch: `<name>`
- Selected batch severity: `<Low/Medium/Severe>`
- Likely files: `<paths>`
- Suggested commands: `<validation/tests/manual smoke>`
- Next action: run a separate approved remediation goal

The selected-batch summary must be copyable and include:

- Problem statement
- Scope boundaries
- Likely files
- Acceptance criteria
- Suggested focused tests
- Explicit stop condition

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
