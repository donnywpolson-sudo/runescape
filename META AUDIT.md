You are working locally in:

`C:\Users\donny\Desktop\runescape`

Goal: perform a **meta-audit** of the audit prompt below against the actual local RuneScape-style game project.

This is **not** an implementation task. This is an audit-of-the-audit.

You must produce a report only.

Hard rules:

* Do not modify files.
* Do not create files.
* Do not write a report file.
* Do not run formatters.
* Do not install dependencies.
* Do not run cleanup commands.
* Do not delete generated files.
* Do not revert, checkout, reset, stash, or commit anything.
* Treat every modified or untracked file as pre-existing user work.
* If the repo is dirty, inspect by reading only. Do not touch dirty files except to read them.
* Do not run commands that are likely to generate, overwrite, migrate, or normalize project files.
* Keep evidence concise with path references and line/function names where useful.
* Do not paste large source files.

Original audit prompt to evaluate:

```text
[PASTE ORIGINAL AUDIT PROMPT HERE]
```

## Target Game Feel: Old School RuneScape-Like

Audit this project against the feel of Old School RuneScape, not by copying its IP, quests, UI, or exact mechanics, but by capturing the core emotional and gameplay loop.

The game should aim for:

* **Grindy but meaningful progression**: long-term goals, slow skill growth, visible milestones, and a satisfying sense of account permanence.
* **Skilling as a core pillar**: gathering, crafting, production, economy, and non-combat skills should matter as much as combat.
* **Player-driven economy**: items, resources, crafting, trading, and markets should create reasons for players to interact.
* **Sandbox freedom**: players should not feel forced down one linear path; they should be able to choose between skilling, combat, quests, money-making, exploration, collection, and social goals.
* **Questing with personality**: quests should feel memorable, weird, funny, puzzle-like, or handcrafted rather than generic fetch-task filler.
* **Simple but sticky combat**: combat can be mechanically simple on the surface, but should support gear choices, risk, progression, bosses, preparation, and mastery.
* **Community feel**: the world should encourage seeing other players, trading, chatting, competing, helping, flexing achievements, and forming social routines.
* **Risk/reward tension**: PvP, dangerous zones, rare drops, long grinds, or resource loss should create stakes where appropriate.
* **Low-friction accessibility**: the game should be easy to understand, run on modest systems, and not require high mechanical skill just to participate.
* **Nostalgic old-school MMO texture**: the experience should feel grounded, persistent, slightly grindy, social, and systems-driven rather than overly cinematic or theme-park-like.

When auditing, specifically ask:

1. Does this feel like a long-term account-building game?
2. Are non-combat skills meaningful enough to be a main playstyle?
3. Does the economy create real player dependency?
4. Are there multiple valid goals at any moment?
5. Would players form routines around logging in daily?
6. Is the grind satisfying rather than empty?
7. Does the world feel social, persistent, and alive?
8. Are quests or activities memorable instead of generic?
9. Is there enough risk, rarity, or scarcity to make achievements matter?
10. Does the game capture the OSRS-style feeling without directly cloning RuneScape?

Required local verification:

1. Change into the repo:

   ```powershell
   cd C:\Users\donny\Desktop\runescape
   ```

2. Verify location and repo root:

   ```powershell
   pwd
   git rev-parse --show-toplevel
   git status --short
   ```

3. List top-level files/folders without modifying anything.

4. Read, if present:

   * `AGENTS.md`
   * `README.md`
   * `requirements.txt`
   * `.gitignore`
   * docs/TODO files
   * launcher/build files
   * config files
   * schema/validation files
   * save/account/auth-related files
   * asset/style/animation/audio-related files
   * `game/`
   * `game/data/`
   * `tests/`

5. Search for evidence of implemented, partial, unused, stubbed, missing, or risky systems using targeted searches for:

   * `TODO`
   * `FIXME`
   * `pass`
   * `NotImplemented`
   * `stub`
   * `RuneScape`
   * `OSRS`
   * `Stardew`
   * `rune`
   * `runite`
   * `animation`
   * `sprite`
   * `tileset`
   * `audio`
   * `music`
   * `quest`
   * `dialogue`
   * `settings`
   * `save`
   * `schema`
   * `migration`
   * `inventory`
   * `equipment`
   * `bank`
   * `shop`
   * `combat`
   * `skill`
   * `XP`
   * `level`

6. Run safe checks only if they appear read-only.

   Prefer:

   ```powershell
   $env:PYTHONDONTWRITEBYTECODE='1'
   python -m pytest -p no:cacheprovider
   ```

   For data validation:

   ```powershell
   python -m game.tools.validate_data
   ```

   But first inspect whether the validation command writes, normalizes, migrates, or regenerates files. If it is not clearly read-only, do not run it. Report that it was skipped and why.

7. After any checks, run:

   ```powershell
   git status --short
   ```

   If the worktree changed, report it immediately. Do not clean it up.

Meta-audit tasks:

## 1. Prompt coverage audit

Evaluate whether the original audit prompt adequately covers:

* local path verification
* local vs remote repo confusion
* repo hygiene
* dirty worktree protection
* no-modification requirement
* no generated-file deletion
* exact command reporting
* evidence standards
* concise path/line/function evidence
* asset/copyright/originality constraints
* target game feel: long-term account growth, skilling, economy, sandbox freedom, quests, combat, community, risk/reward, accessibility, and old-school MMO texture
* current gameplay system classification
* visual, animation, sprite, tileset, style, audio, and settings systems
* save/load compatibility
* account/auth/save-data risks, if present
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
* risk of missing the intended grindy, social, systems-driven game feel while avoiding direct RuneScape/OSRS copying

## 2. Repo-reality check

Compare the original audit prompt against the actual local project.

Answer:

* Does it ask for every file/folder that matters?
* Does it miss generated/build/launcher paths?
* Does it miss assets, visuals, animations, audio, or style files?
* Does it miss save/account/auth files?
* Does it miss validation/schema files?
* Does it miss tests that reveal actual behavior?
* Does it ask for too much irrelevant inspection?
* Does it force enough evidence to prevent hallucinated features?
* Does it distinguish fully implemented from partially wired, present-but-unused, stubbed, and manually unverified systems?
* Does it distinguish code existence from playable behavior?
* Does it evaluate whether the current systems support long-term account growth, meaningful skilling, economy dependency, sandbox goals, memorable quests, sticky combat, community routines, risk/reward, accessibility, and old-school MMO texture?

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
* hardcoded copyrighted/protected naming drift
* protected RuneScape/OSRS-like names, quests, maps, icons, music, dialogue, or terminology
* hardcoded quest/dialogue content that is too clone-like
* recommendations that copy protected RuneScape/OSRS content instead of translating the desired feel into original mechanics, naming, worldbuilding, and progression
* grind that is long but not meaningful
* combat progression crowding out skilling, economy, quests, collection, exploration, or social goals
* economy, trading, or social systems that are described as goals but not supported by implemented multiplayer or market mechanics
* lack of rarity, scarcity, risk, or visible milestones to make achievements matter
* visual/animation gaps
* audio/settings gaps
* backend/UI mismatch, such as HUD slots unsupported by backend state
* systems present in code but not reachable in gameplay
* untested new systems
* present-but-unused modules
* manual checks required but not documented

## 4. Improvement-ideas policy

Improvement ideas are allowed, but only as report recommendations.

Separate them into:

1. **Audit-prompt improvements**
   Changes that make future Codex planning/audit runs safer, more evidence-based, or more useful.

2. **Project improvement candidates**
   Possible future game improvements discovered from repo evidence.

Rules for improvement ideas:

* Do not implement anything.
* Do not modify files.
* Do not invent features.
* Do not recommend broad rewrites.
* Do not recommend protected RuneScape/OSRS clone content.
* Translate the target old-school MMO feel into original systems, names, lore, items, quests, UI, and progression.
* Every idea must cite repo evidence or be labeled “manual verification needed.”
* Prefer small, testable, incremental work.
* Prefer fixes for failing tests/validation before new gameplay, unless clearly unrelated.

## 5. Improved audit prompt

Write an improved version of the original audit prompt.

Requirements for the improved prompt:

* Still read-only.
* Still concise.
* Still outputs the same planning-report structure as the original.
* Stronger about verifying the local path.
* Stronger about dirty worktree protection.
* Stronger about exact command reporting.
* Stronger about tests and validation.
* Stronger about checking recent visual/animation/audio/settings work.
* Stronger about originality drift and protected-content risk.
* Stronger about auditing against the target game feel without recommending direct RuneScape/OSRS clone content.
* Stronger about save/data/schema compatibility.
* Stronger about distinguishing:

  * fully implemented
  * partially implemented
  * partially wired
  * present but unused
  * stub/TODO
  * missing
  * manually unverified
* Avoids over-inspection.
* Avoids huge pasted files.
* Includes “do not fix” language unless the user explicitly asks for implementation.
* Includes manual-check recommendations but does not require running the game unless feasible and safe.

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
