# Antigravity Context Monitor - PowerShell Uninstaller
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Write-Host "=== Antigravity Context Monitor Uninstaller ===" -ForegroundColor Yellow

$PluginDir = Join-Path $HOME ".gemini\config\plugins\context-monitor"

if (Test-Path $PluginDir) {
    Remove-Item -Path $PluginDir -Recurse -Force
    Write-Host "[+] Successfully removed context-monitor plugin from:" -ForegroundColor Green
    Write-Host "    $PluginDir" -ForegroundColor Gray
    Write-Host "[i] Restart Antigravity to finalize." -ForegroundColor Cyan
} else {
    Write-Host "[i] Plugin is not installed at $PluginDir." -ForegroundColor Gray
}
