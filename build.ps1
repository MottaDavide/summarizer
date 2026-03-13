$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$SpecFile = Join-Path $ProjectRoot "Summerizer.spec"

if (-not (Test-Path $VenvPython)) {
    throw "Python del virtualenv non trovato: $VenvPython"
}

Push-Location $ProjectRoot
try {
    & $VenvPython -m pip install --upgrade pip pyinstaller
    & $VenvPython -m PyInstaller --noconfirm --clean $SpecFile

    $DistDir = Join-Path $ProjectRoot "dist\Summerizer"
    if (-not (Test-Path $DistDir)) {
        throw "Build completata ma cartella non trovata: $DistDir"
    }

    $ReadmePath = Join-Path $DistDir "LEGGIMI.txt"
    $ReadmeContent = @"
Summerizer - avvio rapido

1. Se manca, crea/modifica il file .env nella stessa cartella con:
   GEMINI_API_KEY=la_tua_chiave

2. Se ffmpeg non e' incluso, copia ffmpeg.exe e ffprobe.exe in questa cartella
   oppure in .\ffmpeg\bin\

3. Avvia Summerizer.exe con doppio click.
"@
    Set-Content -Path $ReadmePath -Value $ReadmeContent -Encoding UTF8

    Write-Host ""
    Write-Host "Build completata:"
    Write-Host "  $DistDir"
} finally {
    Pop-Location
}
