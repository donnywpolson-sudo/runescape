# META_AUDIT.md

You are reviewing the current `AUDIT.md` prompt against the actual local Hearthvale repository and rewriting `AUDIT.md` in place.

The user workflow should become:

1. Paste `META_AUDIT.md` into Codex to refresh `AUDIT.md`.
2. Paste `AUDIT.md` into Codex to audit the project and end with a paste-ready implementation prompt.

Project root:

`C:\Users\donny\Desktop\hearthvale`

## Goal

Improve `AUDIT.md` so the next audit run is:

* read-only for the project itself
* evidence-based and concise
* strong about dirty worktree and user-work protection
* strong about save/data/schema/originality risks
* strong about playable behavior, not just code presence
* guaranteed to end with one copy-paste-ready `Next Codex Prompt`

## Hard Rules

* Do not modify any file except `AUDIT.md`.
* Do not create reports, reports artifacts, or other files unless the user explicitly asks for them.
* Do not delete, reset, normalize, migrate, regenerate, or commit anything.
* Treat every existing modified or untracked file as user work.
* Record `git status --short` before and after checks.
* Do not install dependencies or run commands likely to write project files, caches, build output, or generated artifacts.
* Do not paste large source files.
* Do not run formatters.

## What to inspect

Read only the targeted context needed to improve the prompt:

* `AGENTS.md`
* `README.md`
* `requirements.txt`
* `CODEX_HANDOFF.md` if present
* `reports\audit\AUDIT_CURRENT.md`, `reports\audit\AUDIT_REPORT_LATEST.md`, and `reports\audit\NEXT_REMEDIATION_PROMPT.md` if present
* representative source, data, and tests under `game/` and `tests/` as needed to judge prompt coverage and repo reality
* the current `AUDIT.md`

## What the rewritten `AUDIT.md` must do

Make sure the revised prompt:

* verifies the local path and repo root before deeper inspection
* protects the dirty worktree and user work
* stays read-only for the project itself
* requires concise, evidence-backed findings
* distinguishes:
  * fully implemented
  * partially implemented
  * partially wired
  * present but unused
  * stub/TODO
  * missing
  * manually unverified
* checks game feel, grind quality, economy loops, graphics/audio/UI feedback, save and schema safety, and originality/IP safety
* avoids clone-like recommendations and over-inspection
* ends with a single copy-paste-ready `Next Codex Prompt`
* makes that next prompt self-contained, scoped, and ready to paste into a fresh Codex run
* keeps the final prompt as the last thing the user sees, with no commentary after it

## Rewrite Requirement

Rewrite `AUDIT.md` in place. If the existing prompt is already close, tighten it rather than replacing good coverage with something weaker.

Do not touch `reports\audit\` files.
