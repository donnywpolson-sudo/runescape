You are working locally in `C:\Users\donny\Desktop\runescape`.

Goal: inspect the current repo state, classify implemented/partial/unused/stub/missing systems, identify the highest-yield next work, and write a concise planning report. Read-only only. Do not modify files, format, clean, delete, revert, checkout, commit, install dependencies, run migrations, run the game, or run build/launcher scripts unless explicitly asked.

First read `AGENTS.md`; it is authoritative.

Required discovery:
1. Run and report:
   - `pwd`
   - `git status --short`
   - top-level file/folder listing
   - `rg --files`
2. Confirm `pwd` is exactly `C:\Users\donny\Desktop\runescape`; if not, stop and report the mismatch.
3. Treat every modified/untracked file as user work.
4. Note ignored/generated/local paths only by presence unless explicitly asked: `.venv/`, `.pytest_cache/`, `build/`, `dist/`, `logs/`, `saves/`, `users.db`, `savegame.json`. Do not open personal account/save/log contents.

Targeted inspection:
- `AGENTS.md`, `README.md`, `requirements.txt`, `.gitignore`
- planning docs such as `NEXT HIGH YIELD.md` and `META AUDIT.md`
- `game/main.py`, `game/settings.py`, `game/engine/app.py`
- `game/engine/save.py`, `auth.py`, `validation.py`
- `game/world/map.py`, `visuals.py`, `animation.py`, `objects.py`
- `game/entities/player.py`, `game/style.py`, `game/ui/`, `game/systems/`
- `game/data/*.json`, with counts for items, skills, recipes, quests, world nodes/mobs/NPCs
- `game/assets/` presence/count only, plus renderer hook/tests
- `tests/`
- `launcher/`, `*.spec`, and `build/`/`dist/` presence only; do not run build commands

Search for:
- `TODO`, `FIXME`, `pass`, `stub`, `NotImplemented`
- `RuneScape`, `OSRS`, `Stardew`, `rune`, `runite`
- `animation`, `visuals`, `style`, `audio`, `sound`, `music`, `settings`
- `quest`, `dialogue`, `save`, `migration`, `validation`

Run safe checks if feasible:
- `python -m pytest`
- `python -m game.tools.validate_data`

If checks fail, report exact command, failure summary, and relevance. Do not fix anything in this run. Recommend fix-first work at rank 1 unless clearly unrelated.

Evaluation rules:
- Separate implemented, partially wired, present-but-unused, stub/TODO, missing, and manually-unverified systems.
- Treat test-helper `pass` separately from real stubs.
- Do not claim visual/gameplay behavior is verified unless covered by tests or an actual manual run.
- Explicitly check visuals/animation: procedural renderers, asset hook, world tint, player poses, scene effects, and tests.
- Explicitly check save/data compatibility: `SAVE_VERSION`, migrations, account paths, item/world/quest IDs, validation, and tests.
- Explicitly check originality drift in source, data, docs, launcher/spec/build names, and tests. Distinguish legacy migration aliases from new protected content.
- Check docs/build consistency, especially README run/build commands, launcher behavior, generated artifacts, and hardcoded paths.
- For each recommendation, cite existing reusable systems/files, likely tests, and one manual check.
- Do not use web search unless explicitly requested.

Output exactly:

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