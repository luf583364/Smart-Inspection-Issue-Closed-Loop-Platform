param(
    [string]$OutputDir,
    [string]$PackageName = "inspection-system-offline.zip"
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
if (-not $OutputDir) {
    $OutputDir = Join-Path $RepoRoot "offline-package"
}

$StageRoot = Join-Path $OutputDir "inspection-system"
$ZipPath = Join-Path $OutputDir $PackageName

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

if (Test-Path $StageRoot) {
    Remove-Item -Recurse -Force -LiteralPath $StageRoot
}
New-Item -ItemType Directory -Force -Path $StageRoot | Out-Null

$ExcludeDirs = @(
    ".git", ".github", ".claude", ".codex", ".idea", ".vscode",
    "offline-package", "data",
    "node_modules", "dist", ".vite",
    ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "logs", "uploads", "reports"
)

$ExcludeFiles = @(
    ".env",
    "*.log", "*.db", "*.db-*", "*.sqlite", "*.sqlite3", "*.pyc", "*.pyo",
    "_*.py", "_*.ps1"
)

Write-Host "Copying project files to $StageRoot ..."
& robocopy $RepoRoot $StageRoot /MIR /XD $ExcludeDirs /XF $ExcludeFiles /NFL /NDL /NP
$RoboCode = $LASTEXITCODE
if ($RoboCode -gt 7) {
    throw "robocopy failed with exit code $RoboCode"
}
$global:LASTEXITCODE = 0

$SourceImageDir = Join-Path $OutputDir "docker-images"
if (Test-Path $SourceImageDir) {
    $TarFiles = Get-ChildItem $SourceImageDir -Filter "*.tar" -File
    if ($TarFiles.Count -gt 0) {
        $TargetImageDir = Join-Path $StageRoot "docker-images"
        New-Item -ItemType Directory -Force -Path $TargetImageDir | Out-Null
        foreach ($Tar in $TarFiles) {
            Copy-Item -LiteralPath $Tar.FullName -Destination $TargetImageDir -Force
        }
        Write-Host "Included Docker image tar files."
    }
    else {
        Write-Host "No Docker image tar files found under $SourceImageDir."
    }
}
else {
    Write-Host "No docker-images directory found. Package will contain source/scripts only."
}

if (Test-Path $ZipPath) {
    Remove-Item -Force -LiteralPath $ZipPath
}

Write-Host "Creating zip package $ZipPath ..."
Compress-Archive -Path $StageRoot -DestinationPath $ZipPath -Force

Write-Host "Package created:"
Get-Item $ZipPath | Select-Object FullName, Length | Format-List | Out-Host
