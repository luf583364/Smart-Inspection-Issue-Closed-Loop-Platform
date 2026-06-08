param(
    [switch]$PackageAfterBuild
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ComposeFile = Join-Path $RepoRoot "docker-compose.yml"
$ImageDir = Join-Path $RepoRoot "offline-package\docker-images"

New-Item -ItemType Directory -Force -Path $ImageDir | Out-Null

function Assert-LastCommandSucceeded {
    param([string]$Step)
    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE"
    }
}

Push-Location $RepoRoot
try {
    Write-Host "Checking Docker daemon ..."
    docker version | Out-Host
    Assert-LastCommandSucceeded "docker version"

    Write-Host "Building production images ..."
    docker compose -f $ComposeFile build
    Assert-LastCommandSucceeded "docker compose build"

    Write-Host "Saving images to $ImageDir ..."
    docker image inspect inspection-backend:latest inspection-frontend:latest | Out-Null
    Assert-LastCommandSucceeded "docker image inspect"
    docker save -o (Join-Path $ImageDir "inspection-backend_latest.tar") inspection-backend:latest
    Assert-LastCommandSucceeded "docker save inspection-backend"
    docker save -o (Join-Path $ImageDir "inspection-frontend_latest.tar") inspection-frontend:latest
    Assert-LastCommandSucceeded "docker save inspection-frontend"

    Write-Host "Saved:"
    Get-ChildItem $ImageDir -Filter "*.tar" | Select-Object FullName, Length | Format-Table | Out-Host

    if ($PackageAfterBuild) {
        & (Join-Path $PSScriptRoot "make-offline-package.ps1")
    }
}
finally {
    Pop-Location
}
