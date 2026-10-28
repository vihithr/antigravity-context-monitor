# Antigravity Context Monitor - PowerShell Installer
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Write-Host "=== Antigravity Context Monitor Installer ===" -ForegroundColor Cyan

$PluginDir = Join-Path $HOME ".gemini\config\plugins\context-monitor"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($ScriptDir -and (Test-Path (Join-Path $ScriptDir "plugin.json"))) {
    Write-Host "[*] Installing from local repository: $ScriptDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $PluginDir | Out-Null
    Copy-Item -Path "$ScriptDir\*" -Destination $PluginDir -Recurse -Force
} else {
    Write-Host "[*] Downloading latest release from GitHub..." -ForegroundColor Yellow
    $ZipUrl = "https://github.com/vihithr/antigravity-context-monitor/archive/refs/heads/main.zip"
    $TempZip = Join-Path $env:TEMP "antigravity-context-monitor.zip"
    $TempExtract = Join-Path $env:TEMP "antigravity-context-monitor-extract"

    Invoke-WebRequest -Uri $ZipUrl -OutFile $TempZip -UseBasicParsing
    if (Test-Path $TempExtract) { Remove-Item -Recurse -Force $TempExtract }
    Expand-Archive -Path $TempZip -DestinationPath $TempExtract -Force
    
    New-Item -ItemType Directory -Force -Path $PluginDir | Out-Null
    Copy-Item -Path "$TempExtract\antigravity-context-monitor-main\*" -Destination $PluginDir -Recurse -Force

    Remove-Item -Force $TempZip -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $TempExtract -ErrorAction SilentlyContinue
}

if (Test-Path (Join-Path $PluginDir "plugin.json")) {
    Write-Host "[+] Successfully installed context-monitor to:" -ForegroundColor Green
    Write-Host "    $PluginDir" -ForegroundColor Gray
    Write-Host ""
    Write-Host "[i] Restart Antigravity or Antigravity IDE to activate the plugin." -ForegroundColor Cyan
    Write-Host "[i] Verification:" -ForegroundColor Cyan
    Write-Host "    python `"$PluginDir\scripts\monitor.py`"" -ForegroundColor White
} else {
    Write-Host "[-] Installation failed: plugin.json not found." -ForegroundColor Red
}
