# AGENTS.md

## Project Vision

This project is an original game inspired by the feel of classic grindable RPGs: simple controls, progression, skilling, combat, gathering, crafting, inventory management, NPC interaction, quests, shops, banking, economy, and long-term account growth.

Do not copy RuneScape/OSRS/Stardew proprietary assets, names, dialogue, maps, quests, icons, music, formulas, or copyrighted content. Do not add new branded or near-branded terms such as RuneScape, OSRS, Stardew, rune, runite, or direct equivalents. Use those games only as design inspiration for progression structure and game feel.

Some existing files may still contain prototype names or formulas inherited from earlier work. When touching nearby code or data, flag that drift and prefer original names, original progression curves, and original world/lore content.

## Working Rules

- Minimize tokens, reads, edits, commands, and output.
- Implement directly when the task is clear.
- Plan only for broad or risky work, and keep the plan under 120 words.
- Ask only when needed to avoid wrong or destructive changes.
- Read targeted files only; search before opening many files.
- Skip generated, vendor, cache, build, data, log, and binary files unless they are relevant.
- Read files directly by path instead of asking the user to paste large files, reports, logs, or full test output.
- Use short summaries instead of long copied output; ask for full logs only when a short summary is not enough.

## Repository Rules

For all tasks:

- Check `git status --short`.
- Inspect `README.md`, `requirements.txt`, and the specific source, data, or test files relevant to the request.
- Identify affected entry points, run/test commands, data files, save formats, and tests before editing those areas.
- Reuse existing patterns.
- Avoid rewrites, unrelated changes, speculative future work, and new dependencies unless clearly justified.
- Preserve behavior and APIs unless the task requires changing them.
- Do not overwrite user work.
- Do not perform destructive commands.
- Do not modify secrets, credentials, lockfiles, migrations, generated artifacts, or delete user work unless required or explicitly requested.
- Ask before any destructive operation.
- Do not commit unless explicitly asked.

For audits, "what should I do next?" requests, or broad planning reports:

- Inspect README, docs, package/config files, source folders, tests, and TODOs.
- Inventory implemented, partial, unused, stubbed, and missing systems.
- Identify the tech stack, entry points, run commands, test commands, asset folders, and save/data formats.

## Multi-step Work

- Use `CODEX_HANDOFF.md` for tasks that need multiple prompts.
- Read `CODEX_HANDOFF.md` first if it exists.
- Update `CODEX_HANDOFF.md` at the end of each run with what changed, files changed, commands run, test results, remaining work, and the next recommended step.
- Do not create or update `CODEX_HANDOFF.md` for simple one-shot tasks.

## Project Facts

* Stack: Python 3.11, Panda3D, pytest.
* Setup: `py -3.11 -m venv .venv`, `.venv\Scripts\Activate.ps1`, then `python -m pip install -r requirements.txt`.
* Run command: `python -m game.main`.
* Launcher build (if needed): `.\launcher\build_launcher.ps1`.
* Test commands: `python -m pytest` and `python -m game.tools.validate_data`.
* Main source: `game/`.
* Tests: `tests/`.
* Data files: `game/data/items.json`, `game/data/skills.json`, `game/data/world.json`, and `game/data/recipes.json`.
* Save/account files: local `users.db`, `saves/<username>.json`, and legacy `savegame.json`.
* Save/versioning code: `game/engine/save.py`; data validation code: `game/engine/validation.py`.
* `AGENTS.md` is the authoritative repo instruction file. Older planning prompts such as `NEXT HIGH_YIELD.txt` are secondary references only.

## Core Design Goals

Prioritize features that make the game feel more playable, grindable, and complete:

1. Core loop: gather -> process/craft -> sell/use -> level up -> unlock better content.
2. Skill progression with XP, levels, unlocks, and meaningful rewards.
3. Simple but satisfying combat.
4. Inventory, equipment, drops, shops, and banking.
5. NPCs, dialogue, quests, and world interaction.
6. Clear UI feedback for actions, XP, levels, loot, errors, and unlocks.
7. Incremental content additions over large rewrites.

## Implementation Rules

Prefer:

- Small, shippable increments.
- Reusing existing systems.
- Minimal architecture disruption.
- Data-driven content where practical.
- Clear separation between game logic, rendering/UI, assets, and persistence.
- Simple systems that can be expanded later.

Avoid:

- Big-bang rewrites.
- Unused abstractions.
- Premature optimization.
- Hardcoded one-off content when a small data structure would work.
- Adding dependencies unless clearly justified.
- Breaking existing saves unless migration is included.

Data/save rules:

- Keep gameplay content data-driven in `game/data/*.json` when practical.
- When changing data schemas or adding data files, update `game/engine/validation.py` and run `python -m game.tools.validate_data`.
- When changing save shape, update migration logic in `game/engine/save.py`, bump or respect `SAVE_VERSION` as appropriate, and preserve old save compatibility.
- Add or update focused tests for validation, save migration, and any system that consumes changed data.

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

- XP/leveling/unlocks.
- Inventory improvements.
- Gathering nodes and respawns.
- Crafting/processing.
- Combat polish.
- Loot tables.
- Shops/economy.
- Banking/storage.
- Equipment stats.
- NPC dialogue.
- Simple quests.
- Save/load reliability.
- UI feedback and tooltips.
- Content balancing.

## Testing Rules

- Run the smallest relevant test first.
- Then run broader tests or builds if needed.
- If no tests exist, add lightweight tests where practical.
- Always provide manual test steps when behavior changes.
- Report the exact commands run and the meaningful result.

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

- Keep changes focused.
- Do not mix unrelated refactors with feature work.
- Mention any untracked or pre-existing modified files.

## Default Behavior

When asked what to do next:

1. Inspect the repo.
2. Inventory what exists.
3. Identify the highest-yield missing systems.
4. Recommend the smallest playable improvement.
5. Produce a scoped implementation plan.
6. Wait for approval before editing after a planning-only request or before broad, risky, or destructive changes; implement directly when the user clearly asks for a narrow safe change.

## Final output

This section overrides any earlier Output Format, Tests, Validation, Manual Check, Added/Removed/Modified, or reporting sections in this file.

Final output only, using exactly these sections in this order:

### Done

* One very simple bullet point stating what was done, or `None`.

### Problems

List only unresolved problems. Do not list completed work, confirmations, or normal caveats unless they affect the next step.

Low

* Minor follow-up only.
* No correctness, safety, validation, data, or goal impact.
* Work can continue.
* If none, write `None`.

Medium

* Real caveat, incomplete verification, or non-blocking risk.
* Result is usable, but should be verified before merge, cleanup, promotion, or broader execution.
* If none, write `None`.

Severe

* Blocking issue.
* Result is unsafe, invalid, misleading, incomplete, or not ready.
* Requires a fix, rerun, rollback, or user decision before continuing.
* If none, write `None`.

Rules:

* Do not include generic notes.
* Do not list completed work here.
* Do not call something Severe unless it prevents safe continuation.
* Use concrete evidence where applicable: command output, failed test name, file path, metric, row count, or report path.
* End with exactly one proceed line: `Proceed status: yes / yes with medium problems / no`.

### Next Step(s)

The `Next Step(s)` section must contain a copy-paste-ready Codex prompt for the next run.

Rules:

* Make it usable in a fresh Codex thread.
* Include exact scope, files, commands, stop conditions, and forbidden actions.
* Prefer one row, one approved batch, or one explicit user decision.
* If any Severe problem exists, the prompt must focus only on clearing that problem.
* If no Severe problems exist but Medium problems exist, the prompt must focus on verification, caveat approval, or risk reduction.
* If no Medium or Severe problems exist, the prompt must name the next forward-progress task.
* Do not include optional polish unless explicitly requested.
* Do not write vague items like "continue improving," "investigate further," or "clean things up."
* If no next work exists, write `None`.

Preferred prompt format:

```text
Continue from CODEX_HANDOFF.md.

Next selected scope: <one row, one approved batch, or one decision>.

Rules:
- <forbidden actions>
- <scope limits>
- <validation requirements>

Task:
- <exact action 1>
- <exact action 2>
- <exact action 3>

Stop when:
- <clear acceptance condition>
```

### Metrics

Elapsed time: <duration>
Token usage: <tokens>

Do not estimate or fabricate elapsed time or token usage.
If metrics are unavailable, write `not available to agent`.

## Final output restrictions

* Do not include a `Changed` section.
* Do not write `Notes/blockers`; write only `Problems`.
* Do not include a `Tests` section unless explicitly requested.
* Do not include any top-level section except `Done`, `Problems`, `Next Step(s)`, and `Metrics`.
* Project/local `AGENTS.md` files may add task-specific rules, but final responses must still include only `Done`, `Problems`, `Next Step(s)`, and `Metrics`.
