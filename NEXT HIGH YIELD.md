You are working locally in C:\Users\donny\Desktop\runescape.

Goal: inspect the current repo state, classify implemented/partial/unused/stub/missing systems, identify highest-yield next work, and write a concise planning report. Read-only only. Do not fix anything unless the user explicitly asks for implementation. Do not modify files, format, clean, delete, revert, checkout, stash, commit, install dependencies, run migrations, run the game, or run build/launcher scripts.

First read AGENTS.md; it is authoritative.

Required verification:
1. Run and report: pwd; git rev-parse --show-toplevel; git status --short.
2. Confirm pwd and repo root are C:\Users\donny\Desktop\runescape. If not, stop.
3. Treat every modified/untracked file as user work; read only.
4. List top-level files/folders and run rg --files.
5. Note generated/local paths only by presence: .venv/, .pytest_cache/, build/, dist/, logs/, saves/, users.db, savegame.json. Do not open personal saves/logs.

Targeted inspection, no huge pasted files:
- AGENTS.md, README.md, requirements.txt, .gitignore
- planning docs: NEXT HIGH YIELD.md, META AUDIT.md if relevant
- game/main.py, game/settings.py, game/engine/app.py
- game/engine/save.py, auth.py, validation.py, game/tools/validate_data.py
- game/world/map.py, visuals.py, animation.py, objects.py
- game/entities/player.py, game/style.py, game/ui/, game/systems/
- game/data/*.json, with counts for items, skills, recipes, quests, resource nodes, mobs, NPCs, decorations, shop stock
- game/assets/ presence/count only
- tests/
- launcher/, *.spec, build/dist presence only; do not run build commands

Search for:
TODO, FIXME, pass, stub, NotImplemented
RuneScape, OSRS, Stardew, rune, runite
animation, visuals, style, audio, sound, music, settings
quest, dialogue, save, migration, validation, schema
inventory, equipment, bank, shop, combat, skill, XP, level

Safe checks:
- Before tests, inspect whether commands are likely to write project files.
- Prefer: $env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider
- Inspect game/tools/validate_data.py before running validation.
- If read-only, run: $env:PYTHONDONTWRITEBYTECODE='1'; python -m game.tools.validate_data
- If any check is skipped, report exact reason.
- After checks, run git status --short again and state whether the worktree changed.

Evaluation rules:
- Separate fully implemented, partially implemented, partially wired, present but unused, stub/TODO, missing, and manually unverified.
- Treat test-helper pass separately from real stubs.
- Distinguish code existence from playable behavior.
- Do not claim visual/gameplay behavior is verified unless covered by tests or a manual run.
- Explicitly check visuals/animation/audio/settings, including procedural renderers, asset hook, world tint, player poses, scene effects, and tests.
- Explicitly check save/data/schema compatibility: SAVE_VERSION, migrations, account paths, item/world/quest IDs, validation, and tests.
- Explicitly check originality drift in source, data, docs, launcher/spec/build names, and tests. Distinguish legacy migration aliases from new protected content.
- Check README/build/launcher consistency and generated-artifact risks.
- Recommend small, testable work only. Do not recommend protected clone-like content or broad rewrites.
- For each recommendation, cite reusable files/systems, likely tests, and one manual check.
- Do not use web search unless explicitly requested.

Output exactly the original planning-report structure:

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

Rank 5-8 candidate additions.

# Plan
Phase | Goal | Steps | Acceptance Criteria | Tests

# Next Codex Prompt
Write one scoped implementation prompt for rank 1. It must be small, testable, protect dirty user work, include exact tests/manual checks, and say: "do not fix unrelated issues."