You are auditing the local Hearthvale project.

Project root:

`C:\Users\donny\Desktop\hearthvale`

Goal: perform a read-only meta-audit of the audit prompt below against the actual local Hearthvale game project.

This is a report-only audit unless the user explicitly asks you to create a timestamped report file.

Hard rules:

* Do not modify source, data, tests, saves, lockfiles, generated output, build output, caches, or user work.
* Do not delete, clean, normalize, migrate, regenerate, reset, checkout, stash, commit, or revert anything.
* Treat every modified or untracked file as pre-existing user work unless you created it in this turn.
* Record `git status --short` before checks and after checks.
* If asked to create a report file, create exactly one timestamped audit report file and no other files.
* If not asked to create a report file, do not create files.
* Do not run formatters.
* Do not install dependencies.
* Do not run commands likely to generate, overwrite, migrate, cache, normalize, or rewrite project files.
* Do not paste large source files.
* Evidence must be concise: path + line/function/class/config key when useful.
* Do not implement fixes.
* Do not recommend protected clone content. Translate the desired classic grindable RPG feel into original Hearthvale-safe mechanics, names, lore, UI, items, quests, progression, visuals, and audio.

Original audit prompt to evaluate:

```text
[PASTE ORIGINAL AUDIT PROMPT HERE]
```

Target game feel: classic grindable RPG progression without copying protected IP.

Audit whether the original prompt properly evaluates this project for:

* long-term account-building progression
* meaningful skilling as a main playstyle
* single-player economy loops, shops, banking, and resource dependency
* sandbox freedom and multiple valid goals
* daily routines and persistence
* satisfying grind vs empty grind
* social/community feel only when supported by implemented code or explicitly labeled missing/manual verification needed
* memorable quest/activity design
* rarity, scarcity, risk, and achievement weight
* simple but sticky combat
* accessibility / low mechanical friction
* nostalgic old-school texture through original content
* originality and copyright/IP safety

Important distinction:

* Code/docs mentioning a system is not proof it is playable.
* Classify each system as one of:
  * fully implemented
  * partially implemented
  * partially wired
  * present but unused
  * stub/TODO
  * missing
  * manually unverified

Required local verification:

1. Enter repo:

```powershell
cd C:\Users\donny\Desktop\hearthvale
```

2. Verify exact location, repo root, and dirty worktree state:

```powershell
pwd
git rev-parse --show-toplevel
git status --short
```

If the path or repo root is wrong, stop and report.

3. List top-level files/folders read-only:

```powershell
Get-ChildItem -Force | Select-Object Mode,Length,LastWriteTime,Name
```

4. Read only if present and relevant:

* `AGENTS.md`
* `README.md`
* `.gitignore`
* `requirements.txt`
* docs/TODO/planning files
* launcher/build files
* config/settings files
* schema/validation files
* save/account/auth-related files
* asset/style/sprite/animation/audio/settings-related files
* targeted files under `game/`
* targeted files under `game/data/`
* targeted files under `tests/`

Use targeted reads, not giant dumps.

5. Search with concise evidence:

```powershell
rg -n "TODO|FIXME|pass|NotImplemented|stub|animation|sprite|tileset|audio|music|quest|dialogue|settings|save|schema|migration|inventory|equipment|bank|shop|combat|skill|XP|level|trade|market|economy|auth|account|launcher|build" AGENTS.md README.md .gitignore requirements.txt launcher game tests -g "!*.pyc" -g "!__pycache__/**"
```

Also search for protected-content drift terms from `AGENTS.md` and report any hits as concise evidence. If `rg` is unavailable, use a read-only PowerShell equivalent and report that fallback.

6. Safe checks only:

Before running validation, inspect the tool first:

```powershell
Get-Content .\game\tools\validate_data.py -TotalCount 220
```

Only run validation if clearly read-only:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -m game.tools.validate_data
```

Run tests only if they appear safe/read-only:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -m pytest -p no:cacheprovider
```

If tests or validation might write files, skip and explain why.

7. After any checks, run:

```powershell
git status --short
```

If worktree status changed, report it immediately. Do not clean it up.

Meta-audit tasks:

## 1. Prompt coverage audit

Evaluate whether the original audit prompt adequately covers:

* local path verification
* local vs remote repo confusion
* repo hygiene
* dirty worktree protection
* no-modification requirement
* generated-file protection
* exact command reporting
* evidence standards
* concise path/line/function evidence
* asset/copyright/originality constraints
* target game feel
* implemented vs partial vs unused vs stubbed vs missing systems
* playable behavior vs code presence
* visuals, animation, sprite, tileset, style, audio, and settings
* save/load compatibility
* account/auth/save-data risks
* data/schema/validation compatibility
* tests and validation
* launcher/build docs
* README/docs drift
* highest-yield prioritization
* Codex prompt output quality
* risk of broad rewrites
* risk of over-inspection
* risk of hallucinated implemented features
* risk of recommending protected clone-like content
* risk of missing the intended grindy, systems-driven feel

## 2. Repo-reality check

Compare the original audit prompt against the actual local project.

Answer:

* Does it ask for every file/folder that matters?
* Does it miss generated/build/launcher paths?
* Does it miss assets, visuals, animations, audio, style, or settings files?
* Does it miss save/account/auth files?
* Does it miss validation/schema files?
* Does it miss tests that reveal actual behavior?
* Does it ask for too much irrelevant inspection?
* Does it force enough evidence to prevent hallucinated features?
* Does it distinguish fully implemented, partially wired, present-but-unused, stubbed, missing, and manually unverified systems?
* Does it distinguish code existence from playable behavior?
* Does it evaluate whether current systems support the target feel through original Hearthvale-safe content?

## 3. Current-state risk check

Identify risks that the original audit prompt should force future Codex runs to catch:

* failing tests
* skipped tests
* validation failures
* dirty worktree
* broken launcher/build docs
* README/docs mismatch
* save migration risks
* data schema drift
* hardcoded protected naming drift
* protected-like names, quests, maps, icons, music, dialogue, formulas, or terminology
* recommendations that copy protected content instead of translating the desired feel into original design
* grind that is long but not meaningful
* combat crowding out skilling, economy, quests, collection, or exploration goals
* economy/trading/social goals not supported by implemented multiplayer or market mechanics
* lack of rarity, scarcity, risk, or visible milestones
* visual/animation gaps
* audio/settings gaps
* backend/UI mismatch
* systems present in code but unreachable in gameplay
* untested new systems
* present-but-unused modules
* manual checks required but undocumented

## 4. Improvement-ideas policy

Improvement ideas are allowed only as report recommendations.

Separate them into:

1. Audit-prompt improvements

   * Changes that make future audit/planning Codex runs safer, more evidence-based, or more useful.

2. Project improvement candidates

   * Possible future game improvements discovered from repo evidence.

Rules:

* Do not implement anything.
* Do not modify files unless explicitly asked to create the timestamped report.
* Do not invent features.
* Do not recommend broad rewrites.
* Do not recommend protected clone content.
* Translate classic grindable RPG feel into original systems, names, lore, items, quests, UI, progression, visuals, and audio.
* Every idea must cite repo evidence or be labeled `manual verification needed`.
* Prefer small, testable, incremental work.
* Prefer fixes for failing tests/validation before new gameplay unless clearly unrelated.

## 5. Improved audit prompt

Write an improved ready-to-paste replacement for the original audit prompt.

The improved prompt must:

* be read-only unless the user explicitly asks for a report file
* be concise
* preserve the same report-only purpose
* verify the local path strongly
* protect dirty worktree/user changes strongly
* require exact command reporting
* handle tests and validation safely
* check recent visual/animation/audio/settings work
* check originality drift and protected-content risk
* audit for target game feel without recommending direct clone content
* check save/data/schema compatibility
* distinguish:
  * fully implemented
  * partially implemented
  * partially wired
  * present but unused
  * stub/TODO
  * missing
  * manually unverified
* avoid over-inspection
* avoid pasted source dumps
* include "do not fix" language
* include manual-check recommendations
* not require running the game unless feasible and safe

Output exactly:

# Meta-Audit Snapshot

* Local path:
* Repo root:
* Git status:
* Checks run:
* Checks result:
* Worktree changed after checks:
* Prompt verdict:

# Audit Prompt Strengths

Issue | Why it helps | Evidence from prompt/repo

# Audit Prompt Weaknesses

Issue | Risk | Concrete improvement

# Repo-Reality Gaps The Prompt Should Catch

Gap | Evidence | Why it matters

# Current-State Risks Future Audits Should Force

Risk | Evidence | How the improved prompt should catch it

# Improvement Ideas Allowed?

* Prompt improvement ideas:
* Project improvement ideas:
* Boundaries:

# Improved Audit Prompt

A ready-to-paste replacement prompt.

# Recommended Use

* When to use original prompt:
* When to use improved prompt:
* When to split into smaller prompts:
* Highest-risk thing to verify before any implementation:
