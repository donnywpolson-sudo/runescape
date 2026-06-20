You are working locally in:

C:\Users\donny\Desktop\runescape

Goal: inspect the current repo state, identify implemented/partial/missing systems, find the highest-yield next work, and write a concise planning report. This is read-only. Do not modify files, format, clean, delete, revert, commit, install dependencies, or run build scripts unless explicitly asked.

First read AGENTS.md and follow it. Treat AGENTS.md as authoritative over older prompt files.

Safety and discovery:

1. Run and report:
   - pwd
   - git status --short
   - top-level file/folder listing
2. Treat every modified or untracked file as user work. Do not touch it except read-only inspection.
3. Inspect, using targeted reads/searches rather than pasting huge files:
   - AGENTS.md
   - README.md
   - requirements.txt
   - .gitignore
   - docs/TODO/planning files such as NEXT HIGH YIELD.md if present
   - game/main.py, game/settings.py, game/engine/app.py
   - game/engine/save.py, auth.py, validation.py
   - game/world/map.py, visuals.py, animation.py, objects.py, style.py
   - game/systems/
   - game/ui/
   - game/data/
   - tests/
   - launcher/ and any *.spec/build/dist presence, without running launcher/build commands
4. Search for:
   - TODO, FIXME, pass, stub, NotImplemented
   - RuneScape, OSRS, Stardew, rune, runite
   - animation, visuals, style, audio, settings
   - quest, dialogue, save, migration, validation
5. Run safe checks if feasible:
   - python -m pytest
   - python -m game.tools.validate_data
   If skipped or failed, report exact command, result, and relevance. Do not fix failures in this run.

Evaluation rules:

- Separate implemented, partially wired, present-but-unused, stub/TODO, missing, and manually-unverified systems.
- Do not claim visual/gameplay behavior is verified unless tests or manual run evidence supports it.
- Explicitly call out save/data compatibility risks for schema, item ID, quest, world, or progression changes.
- Explicitly call out originality drift and protected-name drift. Do not recommend copying RuneScape/OSRS/Stardew assets, names, maps, quests, dialogue, icons, music, formulas, or direct equivalents.
- Prefer small, shippable, data-driven improvements that reuse existing systems.
- Keep evidence concise with file/path references and function/file names.
- Do not use web search unless the user explicitly requests external design research; repo evidence is primary.

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

Rank 5-8 candidate additions. If tests or validation fail, include a fix-first item at rank 1 unless clearly unrelated.

# Plan
Phase | Goal | Steps | Acceptance Criteria | Tests

# Next Codex Prompt
Write one scoped implementation prompt for rank 1. It must be small, testable, read/write scope-aware, protect dirty user work, include exact tests and manual checks, and say “do not fix unrelated issues.”