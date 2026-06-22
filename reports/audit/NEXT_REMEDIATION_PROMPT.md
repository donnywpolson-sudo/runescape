# Next Remediation Prompt

Source report: reports\audit\AUDIT_REPORT_20260621_203330.md
Latest report pointer: reports\audit\AUDIT_REPORT_LATEST.md
Selected batch prompt path: reports\audit\NEXT_REMEDIATION_PROMPT.md
Selected batch: Docs-only time and routine disclosure
Severity: Low

Paste this into a separate Codex remediation run.
Implement only the selected batch below.
Use the scope boundaries, likely files, acceptance criteria, tests, and stop condition exactly.
Do not modify anything outside the stated scope.
Do not commit.

Problem statement:
The slice keeps time fixed at noon and does not implement daily routines, but the reusable docs should say that plainly so future audits and readers do not infer a missing clock or routine loop from gameplay wording.

Scope boundaries:
Documentation only. Do not touch gameplay code, save migrations, protected-term policy, content data, visuals, audio, routines, or tests. Do not run full pytest, the game, launcher, build, or manual smoke for this batch. Do not commit.

Likely files:
* `README.md`
* `GRAPHICS_ANIMATION_NOTE.md`

Acceptance criteria:
* Docs explicitly state that time does not advance, the HUD does not surface a clock, and daily routines are not implemented yet.
* Wording stays original and does not mention or recommend protected clone content.
* No implementation claims are added.

Suggested focused tests:
* `git diff --check README.md GRAPHICS_ANIMATION_NOTE.md`
* `rg -n "time|day|routine|clock" README.md GRAPHICS_ANIMATION_NOTE.md`

Explicit stop condition:
Stop after docs are updated and focused docs checks are reported; do not implement time progression or HUD changes.
