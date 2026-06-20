You are working locally in `C:\Users\donny\Desktop\runescape`.

Goal: inspect the current repo state, classify implemented/partial/missing systems, identify the highest-yield next work, and write a concise planning report. This is read-only. Do not modify files, format, clean, delete, revert, checkout, commit, install dependencies, run migrations, or run build/launcher scripts unless explicitly asked.

First read `AGENTS.md`; it is authoritative over older planning files.

Required discovery:
1. Run and report:
   - `pwd`
   - `git status --short`
   - top-level file/folder listing
2. Confirm `pwd` is exactly `C:\Users\donny\Desktop\runescape`; if not, stop and report the mismatch.
3. Treat every modified/untracked file as user work. Read only; do not touch dirty files except inspection.
4. Inspect with targeted reads/searches, not pasted large files:
   - `AGENTS.md`, `README.md`, `requirements.txt`, `.gitignore`
   - planning docs such as `NEXT HIGH YIELD.md` and `META AUDIT.md` if present
   - `game/main.py`, `game/settings.py`, `game/engine/app.py`
   - `game/engine/save.py`, `auth.py`, `validation.py`
   - `game/world/map.py`, `visuals.py`, `animation.py`, `objects.py`
   - `game/entities/player.py`, `game/style.py`, `game/ui/`, `game/systems/`
   - `game/data/*.json`, `game/assets/`, `tests/`
   - `launcher/`, `*.spec`, and presence of `build/` or `dist/` without running build commands
5. Search for:
   - `TODO`, `FIXME`, `pass`, `stub`, `NotImplemented`
   - `RuneScape`, `OSRS`, `Stardew`, `rune`, `runite`
   - `animation`, `visuals`, `style`, `audio`, `sound`, `music`, `settings`
   - `quest`, `dialogue`, `save`, `migration`, `validation`
6. Run safe checks if feasible:
   - `python -m pytest`
   - `python -m game.tools.validate_data`
   If skipped or failed, report exact command, result, and relevance. Do not fix anything in this run.

Evaluation rules:
- Separate implemented, partially wired, present-but-unused, stub/TODO, missing, and manually-unverified systems.
- Do not claim visual/gameplay behavior is verified unless covered by tests or a manual run; otherwise label it static/manual-unverified.
- Explicitly check recent visuals/animation: procedural renderers, asset hook, world tint, player action poses, scene effects, and their tests.
- Explicitly check save/data compatibility: `SAVE_VERSION`, migrations, item/world/quest IDs, validation, and tests.
- Explicitly check originality drift in source, data, docs, launcher/spec/build names, and tests. Do not recommend copying protected assets, names, maps, quests, dialogue, icons, music, formulas, or direct equivalents.
- Check docs/build consistency, especially README run commands vs actual `dist/`, launcher scripts, and hardcoded paths.
- Prefer small, shippable, data-driven improvements that reuse existing systems.
- Keep evidence concise with path references and line/function names.
- Do not use web search unless the user explicitly requests external design research.

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

Rank 5-8 candidate additions. If tests or validation fail, include a fix-first recommendation at rank 1 unless clearly unrelated.

# Plan
Phase | Goal | Steps | Acceptance Criteria | Tests

# Next Codex Prompt
Write one scoped implementation prompt for rank 1. It must be small, testable, protect dirty user work, include exact tests/manual checks, and say: "do not fix unrelated issues."
