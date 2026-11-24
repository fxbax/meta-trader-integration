# windows/service/manage_service.ps1
param (
    [ValidateSet("status", "start", "stop", "restart", "logs")]
    [string]$Action = "status"
)

$ServiceName = "MetaTraderIntegration"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir
$LogFile = Join-Path $BaseDir "logs\service.log"

switch ($Action) {
    "status" {
        $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($svc) {
            Write-Host "Service '$ServiceName': " -NoNewline
            Write-Host "$($svc.Status)" -ForegroundColor ($svc.Status -eq 'Running' ? 'Green' : 'Red')
        } else {
            Write-Host "Service '$ServiceName' is not installed." -ForegroundColor Yellow
        }
    }
    "start" {
        Write-Host "Starting '$ServiceName'..." -ForegroundColor Cyan
        Start-Service -Name $ServiceName
        Get-Service -Name $ServiceName
    }
    "stop" {
        Write-Host "Stopping '$ServiceName'..." -ForegroundColor Yellow
        Stop-Service -Name $ServiceName -Force
        Get-Service -Name $ServiceName
    }
    "restart" {
        Write-Host "Restarting '$ServiceName'..." -ForegroundColor Cyan
        Restart-Service -Name $ServiceName -Force
        Get-Service -Name $ServiceName
    }
    "logs" {
        if (Test-Path $LogFile) {
            Get-Content -Path $LogFile -Tail 50 -Wait
        } else {
            Write-Warning "Log file not found at $LogFile"
        }
    }
}
