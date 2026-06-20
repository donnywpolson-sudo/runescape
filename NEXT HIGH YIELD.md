You are working in my RuneScape-style game project.

Goal: inspect the current repo state, identify what is already implemented, find the highest-yield next work, and write the most efficient implementation plan. Do not modify files. Produce a planning report only.

First, read `AGENTS.md` and follow its project rules and output format.

Safety and repo hygiene:

* Run `git status --short` early.
* Treat all modified and untracked files as pre-existing user work.
* Do not revert, delete, format, overwrite, or clean up dirty-worktree changes.
* Do not run destructive commands.
* Do not install dependencies unless clearly necessary for inspection.
* Keep evidence concise with path references; do not paste large source files.

Targeted inspection:

* Run basic discovery: `pwd`, `git status --short`, top-level files/folders, README/docs/TODOs/config files.
* Identify stack, entry points, run commands, test commands, asset/data folders, save/data formats, and main gameplay systems.
* Inspect only the relevant source/data/test files needed to classify current systems accurately.
* Search for implemented, partial, unused, stubbed, TODO, and missing systems.
* Run safe existing checks if available, especially examples like:
  * `python -m pytest`
  * `python -m game.tools.validate_data`
* Report exact check commands and results. If checks fail, prioritize fixing those failures before new gameplay additions unless they are clearly unrelated.

Evaluate the game as an original RuneScape-inspired progression game:

* Identify systems such as movement, camera, map/world, NPCs, dialogue, quests, combat, enemies, loot, skills, gathering, crafting/processing, inventory, equipment, banking, shops, economy, XP/levels/unlocks, UI feedback, save/load, areas, audio, settings, and testing.
* Clearly separate:
  1. Fully implemented
  2. Partially implemented
  3. Present but unused
  4. Stub/TODO
  5. Missing but high-value
* Do not claim implementation without repo evidence.
* Do not recommend copying RuneScape/OSRS proprietary assets, names, dialogue, quests, maps, icons, music, or copyrighted content.

External research:

* Use web search only if available and useful for high-retention progression-loop context.
* Keep it secondary to repo evidence.
* Limit external citations to 2-3 high-quality links.
* If web search is unavailable, say so and rely on codebase analysis plus general design reasoning.

Prioritize additions by:

* Player value / fun added
* Reuse of existing code/assets
* Low implementation risk
* Progression depth
* Replayability
* Testability
* Minimal refactor required
* Fit with current architecture
* Ability to ship incrementally

Output a concise planning report using exactly this structure:

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

Rank 5-8 candidate additions. If tests or validation are failing, include a fix-first item at rank 1 unless clearly unrelated.

# Plan
Phase | Goal | Steps | Acceptance Criteria | Tests

Include phases for:

* Any safety/fix-first work needed
* First playable improvement
* Second playable improvement
* Third playable improvement, only if justified
* Polish/tests/balancing

# Next Codex Prompt
Write one scoped implementation prompt ready to paste for the highest-priority next task. It must be small, testable, avoid broad rewrites, protect dirty user work, and include exact tests/manual checks.

Constraints:

* Do not change files in this run.
* Do not invent implemented features.
* Prefer incremental additions over rewrites.
* Preserve current architecture unless there is a clear reason not to.
* Be blunt about weak spots, missing systems, failing checks, and technical debt.
* Keep the report practical, concise, and action-oriented.
