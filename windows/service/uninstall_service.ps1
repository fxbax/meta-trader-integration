# windows/service/uninstall_service.ps1
# Requires Administrator privileges
$ErrorActionPreference = "SilentlyContinue"

$ServiceName = "MetaTraderIntegration"

Write-Host "Stopping service '$ServiceName'..." -ForegroundColor Yellow
Stop-Service -Name $ServiceName -Force
Start-Sleep -Seconds 2

Write-Host "Deleting service '$ServiceName'..." -ForegroundColor Yellow
sc.exe delete $ServiceName | Out-Null

Write-Host "Removing Windows Firewall rule..." -ForegroundColor Yellow
netsh advfirewall firewall delete rule name="MetaTrader Integration" | Out-Null

Write-Host "Service and Firewall rules removed cleanly." -ForegroundColor Green
