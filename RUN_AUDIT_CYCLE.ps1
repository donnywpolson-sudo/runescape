$ErrorActionPreference = "Stop"

$RepoRoot = "C:\Users\donny\Desktop\hearthvale"
Set-Location -LiteralPath $RepoRoot

$ExpectedRepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$ActualRepoRoot = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) {
    throw "Failed to resolve git repo root from $RepoRoot"
}
$ActualRepoRoot = (Resolve-Path -LiteralPath $ActualRepoRoot).Path
if ($ActualRepoRoot -ne $ExpectedRepoRoot) {
    throw "Wrong repo root. Expected $ExpectedRepoRoot but got $ActualRepoRoot"
}

$MetaAuditPath = ".codex\META_AUDIT.md"
$CanonicalAuditPath = ".codex\AUDIT.md"
$AuditOutputDir = "reports\audit"
$CurrentAuditPath = Join-Path $AuditOutputDir "AUDIT_CURRENT.md"
$LatestReportPath = Join-Path $AuditOutputDir "AUDIT_REPORT_LATEST.md"
$NextPromptPath = Join-Path $AuditOutputDir "NEXT_REMEDIATION_PROMPT.md"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportPath = Join-Path $AuditOutputDir "AUDIT_REPORT_$Timestamp.md"

$dirty = @(git status --porcelain)
$blockingDirty = @()
foreach ($line in $dirty) {
    $path = $line.Substring(3).Trim()
    $allowed = (
        $path -eq "RUN_AUDIT_CYCLE.ps1" -or
        $path -eq "CODEX_HANDOFF.md" -or
        $path -eq "README.md" -or
        $path -eq "GRAPHICS_ANIMATION_NOTE.md" -or
        $path -like "reports/audit/*"
    )
    if (-not $allowed) {
        $blockingDirty += $line
    }
}
if ($blockingDirty) {
    Write-Host "Repo has non-audit changes. Stop and review git status first:" -ForegroundColor Red
    $blockingDirty | ForEach-Object { Write-Host $_ }
    exit 1
}
if ($dirty) {
    Write-Host "Continuing with existing audit-infrastructure changes:" -ForegroundColor Yellow
    git status --short
}

New-Item -ItemType Directory -Force -Path $AuditOutputDir | Out-Null

$MetaAuditStatus = if (Test-Path $MetaAuditPath) { "available at $MetaAuditPath" } else { "not available" }
$CanonicalAuditStatus = if (Test-Path $CanonicalAuditPath) { "available at $CanonicalAuditPath" } else { "not available" }

$prompt = @"
Run one audit cycle.

Step 1:
Use the meta-audit prompt if available ($MetaAuditStatus) and the canonical audit prompt if available ($CanonicalAuditStatus) to inspect the current repo and update $CurrentAuditPath.
$CanonicalAuditPath is an optional read-only canonical prompt location. Read it if available, but do not write to .codex and do not fail if .codex is read-only or unavailable.
$CurrentAuditPath should become the best reusable project-specific audit prompt for this repo.

Step 2:
Using the updated $CurrentAuditPath, audit the repo and create one new timestamped audit report at $ReportPath.
The audit report should identify what to improve.
Do not fix code during the audit step.

Step 3:
Read the new audit report and select only the next smallest safe actionable remediation batch.
Do not fix the selected batch.
Do not modify gameplay code, save migrations, protected-term policy, content data, visuals, audio, routines, or tests.
Do not delete user work.
Do not commit.

Audit-only contract:
- Audit-only: yes
- Remediation applied: no
- Do not apply remediation.
- Do not run full pytest automatically.
- Do not run launcher, game, build, or manual smoke automatically.
- Any remediation or expensive validation must be a separate explicit Codex goal or separate approved command.

Rules:
- Read files directly by path. Do not ask me to paste reports or logs.
- Keep changes minimal.
- Prefer targeted audit checks only when needed to produce the report.
- If full pytest, launcher/game/build smoke, or remediation validation is needed, recommend it in the selected-batch summary instead of running it.
- The audit report and CODEX_HANDOFF.md must clearly include:
  - Audit-only: yes
  - Remediation applied: no
  - Selected batch: <name>
  - Selected batch severity: <Low/Medium/Severe>
  - Likely files: <paths>
  - Suggested commands: <validation/tests/manual smoke>
  - Next action: run a separate approved remediation goal
- Include a copyable selected-batch summary with:
  - problem statement
  - scope boundaries
  - likely files
  - acceptance criteria
  - suggested focused tests
  - explicit stop condition
- Update or create CODEX_HANDOFF.md with:
  - audit report path
  - latest report pointer path
  - files changed
  - remediation batch selected
  - audit-only and remediation-applied status
  - selected batch severity
  - likely files
  - suggested commands
  - tests/checks run
  - remaining findings
  - next recommended step

Expected allowed changes:
- $CurrentAuditPath
- $ReportPath
- $LatestReportPath
- CODEX_HANDOFF.md
- no remediation/source/test/data/gameplay files

Return only Changed, Notes/blockers, Selected batch, Next, Metrics.
"@

$prompt | codex exec --cd "$RepoRoot" --sandbox workspace-write -

if (-not (Test-Path $ReportPath)) {
    throw "Audit report was not created at $ReportPath"
}

$ReportText = Get-Content -Raw -LiteralPath $ReportPath
$SelectedBatchSectionMatch = [regex]::Match(
    $ReportText,
    '(?ms)^# Selected Remediation Batch\r?\n(?<body>.*?)(?:\r?\n# |\z)'
)
$NextPromptSectionMatch = [regex]::Match(
    $ReportText,
    '(?ms)^# Next Codex Prompt\r?\n(?<body>.*)\s*$'
)

$SelectedBatch = ""
$SelectedBatchSeverity = ""
if ($SelectedBatchSectionMatch.Success) {
    $SelectedBatchSection = $SelectedBatchSectionMatch.Groups["body"].Value.Trim()
    $SelectedBatchMatch = [regex]::Match($SelectedBatchSection, '(?m)^\* Selected batch:\s*(.+)$')
    $SelectedBatchSeverityMatch = [regex]::Match($SelectedBatchSection, '(?m)^\* Selected batch severity:\s*(.+)$')
    $SelectedBatch = $SelectedBatchMatch.Groups[1].Value.Trim()
    $SelectedBatchSeverity = $SelectedBatchSeverityMatch.Groups[1].Value.Trim()
}

$NextPromptBody = if ($NextPromptSectionMatch.Success) {
    $NextPromptSectionMatch.Groups["body"].Value.Trim()
} elseif ($SelectedBatchSectionMatch.Success) {
    @"
Selected remediation batch:
$SelectedBatchSection

The report did not include a ready-to-paste next prompt section.
Use the selected remediation batch above to craft a separate Codex implementation run.
"@.Trim()
} else {
    @"
The report did not include a selected remediation batch or next prompt section.
Review $ReportPath and craft a separate Codex implementation run from the report findings.
"@.Trim()
}

@"
# Latest Audit Report

Path: $ReportPath
Generated: $Timestamp
Audit-only: yes
Remediation applied: no
Selected batch prompt path: $NextPromptPath
Next action: paste the generated prompt into a separate approved remediation goal
"@ | Set-Content -Path $LatestReportPath -Encoding UTF8

$NextPrompt = @"
# Next Remediation Prompt

Source report: $ReportPath
Latest report pointer: $LatestReportPath
Selected batch prompt path: $NextPromptPath
Selected batch: $SelectedBatch
Severity: $SelectedBatchSeverity

$NextPromptBody
"@

Set-Content -LiteralPath $NextPromptPath -Value $NextPrompt -Encoding UTF8

Write-Host ""
Write-Host "Next remediation prompt:" -ForegroundColor Cyan
Get-Content -Raw -LiteralPath $NextPromptPath

Write-Host ""
Write-Host "Final git status:" -ForegroundColor Cyan
git status --short
