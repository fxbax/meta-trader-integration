# windows/build_release.ps1
# Automated build script for PyInstaller + Inno Setup installer
param (
    [string]$InnoSetupCompilerPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "=== Building MetaTrader 5 Integration Release ===" -ForegroundColor Cyan

# Step 1: Run PyInstaller
Write-Host "[1/2] Compiling standalone executable with PyInstaller..." -ForegroundColor Yellow
$SpecPath = Join-Path $ScriptDir "pyinstaller.spec"
Push-Location $ProjectRoot
try {
    pyinstaller --noconfirm --clean $SpecPath
    Write-Host "PyInstaller build completed in dist/fxbax-mt" -ForegroundColor Green
} finally {
    Pop-Location
}

# Step 2: Compile Inno Setup Installer (if ISCC.exe is available)
Write-Host "[2/2] Generating Windows Installer Setup.exe..." -ForegroundColor Yellow
$IssPath = Join-Path $ScriptDir "installer\setup_script.iss"

if (Test-Path $InnoSetupCompilerPath) {
    & $InnoSetupCompilerPath $IssPath
    Write-Host "Installer created successfully in windows/installer/Output/" -ForegroundColor Green
} else {
    Write-Warning "Inno Setup compiler not found at '$InnoSetupCompilerPath'."
    Write-Warning "To generate the Setup.exe installer, install Inno Setup 6 from https://jrsoftware.org/isdl.php"
    Write-Warning "Standalone binary distribution is ready in 'dist/fxbax-mt/'"
}

Write-Host "=== Build Completed ===" -ForegroundColor Cyan
