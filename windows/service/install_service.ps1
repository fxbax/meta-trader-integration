# windows/service/install_service.ps1
# Requires Administrator privileges
param (
    [int]$Port = 5000,
    [string]$AuthToken = "",
    [string]$HostBinding = "0.0.0.0"
)

$ErrorActionPreference = "Stop"

# Ensure script is running with elevated permissions
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script must be executed as Administrator. Please run PowerShell as Administrator."
    exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir
$ExePath = Join-Path $BaseDir "fxbax-mt.exe"

# If fxbax-mt.exe is not in parent, check script dir or current dir
if (-not (Test-Path $ExePath)) {
    $ExePath = Join-Path $ScriptDir "fxbax-mt.exe"
}

if (-not (Test-Path $ExePath)) {
    Write-Warning "Executable fxbax-mt.exe not found at standard path. Ensure you run this inside the extracted distribution."
}

# Prompt for AuthToken if not provided
if ([string]::IsNullOrWhiteSpace($AuthToken)) {
    $AuthToken = Read-Host "Enter secret API Access Token (AUTH_TOKEN)"
    if ([string]::IsNullOrWhiteSpace($AuthToken)) {
        Write-Error "AuthToken cannot be empty."
        exit 1
    }
}

# 1. Generate config file
$ConfigFile = Join-Path $BaseDir ".env"
$ConfigContent = @"
PORT=$Port
HOST=$HostBinding
AUTH_TOKEN=$AuthToken
LOG_LEVEL=INFO
LOG_DIR=logs
"@
Set-Content -Path $ConfigFile -Value $ConfigContent -Encoding UTF8
Write-Host "Created configuration at $ConfigFile (Port: $Port)" -ForegroundColor Green

# 2. Add Windows Firewall Rule
Write-Host "Configuring Windows Firewall for port $Port..." -ForegroundColor Cyan
try {
    netsh advfirewall firewall delete rule name="MetaTrader Integration" 2>$null | Out-Null
    netsh advfirewall firewall add rule name="MetaTrader Integration" dir=in action=allow protocol=TCP localport=$Port | Out-Null
    Write-Host "Firewall rule created successfully." -ForegroundColor Green
} catch {
    Write-Warning "Could not add firewall rule automatically. Please ensure port $Port is allowed inbound."
}

# 3. Register and Start Windows Service using sc.exe
$ServiceName = "MetaTraderIntegration"
$DisplayName = "MetaTrader 5 Integration Service"

Write-Host "Registering Windows Service '$ServiceName'..." -ForegroundColor Cyan
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "Service already exists. Stopping and removing old instance..."
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    sc.exe delete $ServiceName | Out-Null
    Start-Sleep -Seconds 2
}

$binPath = "`"$ExePath`""
sc.exe create $ServiceName binPath= $binPath start= auto DisplayName= $DisplayName | Out-Null
sc.exe description $ServiceName "High-performance REST API gateway connecting external applications to MetaTrader 5." | Out-Null

Write-Host "Starting service..." -ForegroundColor Cyan
Start-Service -Name $ServiceName
Start-Sleep -Seconds 2

$status = (Get-Service -Name $ServiceName).Status
Write-Host "Service $ServiceName is now $status on port $Port." -ForegroundColor Green
Write-Host "Test connection: curl -X POST http://127.0.0.1:$Port/account-info -H `"token: $AuthToken`""
