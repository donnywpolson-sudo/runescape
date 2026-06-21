param(
    [switch]$InstallBuildDependencies
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$LauncherScript = Join-Path $ProjectRoot "launcher\hearthvale_launcher.py"
$IconPath = Join-Path $ProjectRoot "launcher\hearthvale.ico"
$OutputExe = Join-Path $ProjectRoot "dist\Hearthvale.exe"

function Test-PyInstaller {
    $PreviousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $PythonExe -m PyInstaller --version *> $null
        return $LASTEXITCODE -eq 0
    }
    finally {
        $ErrorActionPreference = $PreviousErrorActionPreference
    }
}

if (-not (Test-Path $PythonExe)) {
    throw "Project virtual environment Python was not found: $PythonExe"
}

if (-not (Test-Path $LauncherScript)) {
    throw "Launcher script was not found: $LauncherScript"
}

if (-not (Test-Path $IconPath)) {
    throw "Launcher icon was not found: $IconPath"
}

Push-Location $ProjectRoot
try {
    if (-not (Test-PyInstaller)) {
        if (-not $InstallBuildDependencies) {
            throw "PyInstaller is not installed in the project virtual environment. No dependencies were installed. Install it explicitly with `"$PythonExe`" -m pip install pyinstaller, or rerun this script with -InstallBuildDependencies to allow this build script to install it."
        }

        Write-Host "Installing PyInstaller because -InstallBuildDependencies was provided." -ForegroundColor Yellow
        & $PythonExe -m pip install pyinstaller
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install PyInstaller with exit code $LASTEXITCODE"
        }
        if (-not (Test-PyInstaller)) {
            throw "PyInstaller installed but could not be imported"
        }
    }

    & $PythonExe -m PyInstaller --clean --noconfirm --onefile --windowed --icon $IconPath --name Hearthvale $LauncherScript
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE"
    }

    if (-not (Test-Path $OutputExe)) {
        throw "Expected launcher exe was not created: $OutputExe"
    }

    Write-Host "Built launcher: $OutputExe"
}
finally {
    Pop-Location
}
