$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Iscc = Get-Command iscc -ErrorAction SilentlyContinue

if (-not $Iscc) {
    throw "Inno Setup Compiler (iscc) non trovato. Installa Inno Setup e riprova."
}

Push-Location $ProjectRoot
try {
    if (-not (Test-Path ".\dist\Summerizer\Summerizer.exe")) {
        throw "Build applicazione mancante. Esegui prima .\build.ps1"
    }

    & $Iscc.Source ".\installer.iss"

    Write-Host ""
    Write-Host "Installer creato in:"
    Write-Host "  $(Join-Path $ProjectRoot 'dist_installer')"
} finally {
    Pop-Location
}
