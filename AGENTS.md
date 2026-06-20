# AGENTS.md

## Project Vision

This project is an original game inspired by the feel of classic grindable RPGs: simple controls, progression, skilling, combat, gathering, crafting, inventory management, NPC interaction, quests, shops, banking, economy, and long-term account growth.

Do not copy RuneScape/OSRS/Stardew proprietary assets, names, dialogue, maps, quests, icons, music, formulas, or copyrighted content. Do not add new branded or near-branded terms such as RuneScape, OSRS, Stardew, rune, runite, or direct equivalents. Use those games only as design inspiration for progression structure and game feel.

Some existing files may still contain prototype names or formulas inherited from earlier work. When touching nearby code/data, flag that drift and prefer original names, original progression curves, and original world/lore content.

## Project Facts

* Stack: Python 3.11, Panda3D, pytest.
* Setup: `py -3.11 -m venv .venv`, `.venv\Scripts\Activate.ps1`, then `python -m pip install -r requirements.txt`.
* Run command: `python -m game.main`.
* Test commands: `python -m pytest` and `python -m game.tools.validate_data`.
* Main source: `game/`.
* Tests: `tests/`.
* Data files: `game/data/items.json`, `game/data/skills.json`, `game/data/world.json`, and `game/data/recipes.json`.
* Save/account files: local `users.db`, `saves/<username>.json`, and legacy `savegame.json`.
* Save/versioning code: `game/engine/save.py`; data validation code: `game/engine/validation.py`.
* `AGENTS.md` is the authoritative repo instruction file. Older planning prompts such as `NEXT HIGH YIELD.txt` are secondary references only.

## Core Design Goals

Prioritize features that make the game feel more playable, grindable, and complete:

1. Core loop: gather → process/craft → sell/use → level up → unlock better content.
2. Skill progression with XP, levels, unlocks, and meaningful rewards.
3. Simple but satisfying combat.
4. Inventory, equipment, drops, shops, and banking.
5. NPCs, dialogue, quests, and world interaction.
6. Clear UI feedback for actions, XP, levels, loot, errors, and unlocks.
7. Incremental content additions over large rewrites.

## Working Style

Be extremely token efficient.

Input handling:

* Read only what is needed.
* Prefer targeted file inspection before broad summaries.
* Avoid pasting large files unless required.
* Use path/file references instead of copying code when possible.

Output handling:

* Be concise.
* Prefer bullets, tables, and changed hunks.
* Do not include filler, praise, or generic advice.
* Do not explain obvious steps.
* Do not repeat the user’s request.
* For code changes, show only changed files and important diffs unless asked otherwise.

Reasoning:

* Keep reasoning compact.
* Do not output long chain-of-thought.
* Provide only brief rationale, tradeoffs, and decisions.
* When uncertain, state the uncertainty directly and inspect the repo instead of guessing.

## Repository Rules

For all tasks:

* Check `git status --short`.
* Inspect `README.md`, `requirements.txt`, and the specific source/data/test files relevant to the request.
* Identify affected entry points, run/test commands, data files, save formats, and tests before editing those areas.
* Do not overwrite user work.
* Do not perform destructive commands.
* Do not make broad rewrites unless explicitly requested.

For audits, "what should I do next?" requests, or broad planning reports:

* Inspect `README`, docs, package/config files, source folders, tests, and TODOs.
* Inventory implemented, partial, unused, stubbed, and missing systems.
* Identify the tech stack, entry points, run commands, test commands, asset folders, and save/data formats.

## Implementation Rules

Prefer:

* Small, shippable increments.
* Reusing existing systems.
* Minimal architecture disruption.
* Data-driven content where practical.
* Clear separation between game logic, rendering/UI, assets, and persistence.
* Simple systems that can be expanded later.

Avoid:

* Big-bang rewrites.
* Unused abstractions.
* Premature optimization.
* Hardcoded one-off content when a small data structure would work.
* Adding dependencies unless clearly justified.
* Breaking existing saves unless migration is included.

Data/save rules:

* Keep gameplay content data-driven in `game/data/*.json` when practical.
* When changing data schemas or adding data files, update `game/engine/validation.py` and run `python -m game.tools.validate_data`.
* When changing save shape, update migration logic in `game/engine/save.py`, bump or respect `SAVE_VERSION` as appropriate, and preserve old save compatibility.
* Add or update focused tests for validation, save migration, and any system that consumes changed data.

## Feature Priority

When choosing next work, rank features by:

1. Player value / fun added.
2. Reuse of existing code.
3. Low implementation risk.
4. Improves the core grind/progression loop.
5. Adds replayability or long-term goals.
6. Easy to test manually or automatically.
7. Minimal refactor required.

High-yield feature categories:

* XP/leveling/unlocks.
* Inventory improvements.
* Gathering nodes and respawns.
* Crafting/processing.
* Combat polish.
* Loot tables.
* Shops/economy.
* Banking/storage.
* Equipment stats.
* NPC dialogue.
* Simple quests.
* Save/load reliability.
* UI feedback and tooltips.
* Content balancing.

## Testing Rules

When changing code:

* Run the smallest relevant test first.
* Then run broader tests/build if available.
* If no tests exist, add lightweight tests where practical.
* Always provide manual test steps.
* Report exact commands run and results.

## Output Format For Plans

Use this structure by default unless the user, review mode, or higher-priority system/developer instructions require another format:

```md
# Snapshot
- Stack:
- Entry points:
- Run command:
- Test command:
- Current status:

# Findings
System | Status | Evidence | Notes

# Recommended Next Work
Rank | Feature | Why | Complexity | Risk | Files likely touched

# Plan
Phase | Goal | Steps | Acceptance Criteria | Tests

# Next Codex Prompt
A scoped implementation prompt ready to paste.
```

## Output Format For Code Changes

Use this structure by default unless the user, review mode, or higher-priority system/developer instructions require another format:

```md
# Changed
- `path/file.ext`: what changed

# Why
- Brief rationale

# Tests
- Command: result

# Manual Check
- Steps to verify in-game

# Notes
- Risks or follow-ups
```

## Git Hygiene

* Keep changes focused.
* Do not mix unrelated refactors with feature work.
* Mention any untracked or pre-existing modified files.
* Do not commit unless explicitly asked.
* Do not add generated artifacts unless required.

## Default Behavior

When asked what to do next:

1. Inspect the repo.
2. Inventory what exists.
3. Identify the highest-yield missing systems.
4. Recommend the smallest playable improvement.
5. Produce a scoped implementation plan.
6. Wait for approval before editing unless explicitly told to implement.
