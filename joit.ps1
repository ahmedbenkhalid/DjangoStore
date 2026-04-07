#!/usr/bin/env pwsh
# =============================================================================
# joit.ps1 - Install joi to system PATH (Windows)
# =============================================================================

param(
    [switch]$Uninstall,
    [switch]$Force
)

$JOI_VERSION = "0.2.0"
$JOI_SCRIPT = "joi.ps1"

function Get-JoiInstallPath {
    return Join-Path $env:LOCALAPPDATA "joi"
}

function Get-JoiBinPath {
    return Join-Path (Get-JoiInstallPath) $JOI_SCRIPT
}

function Test-InPath {
    $pathLower = $env:PATH.ToLower()
    $installPath = (Get-JoiInstallPath).ToLower()
    return $pathLower.Contains($installPath)
}

function Add-ToPath {
    $installPath = Get-JoiInstallPath
    
    Write-Host ""
    Write-Host "Adding to PATH: $installPath"
    
    try {
        $currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        if ($currentPath -and $currentPath.ToLower().Contains($installPath.ToLower())) {
            Write-Host "  Already in PATH" -ForegroundColor Yellow
            return $true
        }
        
        $newPath = if ($currentPath) { "$currentPath;$installPath" } else { $installPath }
        [System.Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        
        Write-Host "  Added to User PATH" -ForegroundColor Green
        return $true
    } catch {
        Write-Host ""
        Write-Host "Failed to update PATH automatically:" -ForegroundColor Red
        Write-Host "  $_" -ForegroundColor Red
        return $false
    }
}

function Show-ManualInstructions {
    param([string]$InstallPath)
    
    Write-Host ""
    Write-Host "Manual installation required:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. Open PowerShell as Administrator"
    Write-Host ""
    Write-Host "  2. Run this command to add to System PATH:"
    Write-Host ""
    Write-Host "     [Environment]::SetEnvironmentVariable("
    Write-Host '       "Path",'
    Write-Host "       [Environment]::GetEnvironmentVariable('Path','User') + ';$InstallPath',"
    Write-Host '       "User"'
    Write-Host "     )"
    Write-Host ""
    Write-Host "  OR add to your User PATH manually:"
    Write-Host "     Settings > System > Environment Variables > User PATH"
    Write-Host ""
    Write-Host "  3. Restart your terminal and run: joi check"
    Write-Host ""
}

# =============================================================================
# Uninstall
# =============================================================================
if ($Uninstall) {
    $installPath = Get-JoiInstallPath
    $binPath = Get-JoiBinPath
    
    if (-not (Test-Path $installPath)) {
        Write-Host "joi is not installed" -ForegroundColor Yellow
        exit 0
    }
    
    Write-Host "Uninstalling joi..."
    Write-Host ""
    
    Remove-Item $installPath -Recurse -Force -ErrorAction SilentlyContinue
    
    $currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -and $currentPath.ToLower().Contains($installPath.ToLower())) {
        $newPath = ($currentPath -split ';' | Where-Object { 
            $_ -and $_.ToLower() -ne $installPath.ToLower() 
        }) -join ';'
        [System.Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Host "Removed from PATH" -ForegroundColor Green
    }
    
    Write-Host "joi uninstalled successfully"
    Write-Host "Restart your terminal to complete removal"
    exit 0
}

# =============================================================================
# Install
# =============================================================================
Write-Host ""
Write-Host "joit - Install joi to PATH"
Write-Host "========================="
Write-Host ""

# Check if already installed
if (Test-InPath -and -not $Force) {
    $installedPath = Get-JoiBinPath
    Write-Host "joi is already installed at:" -ForegroundColor Green
    Write-Host "  $installedPath"
    Write-Host ""
    Write-Host "Run: $C_CYAN`joi check$C_RESET" -NoNewline
    Write-Host " to verify"
    Write-Host ""
    Write-Host "To reinstall, run: $C_CYAN`joit install --force$C_RESET"
    exit 0
}

# Find source script
$scriptDir = $PSScriptRoot
$sourceScript = Join-Path $scriptDir $JOI_SCRIPT

if (-not (Test-Path $sourceScript)) {
    $sourceScript = Join-Path $scriptDir "..\$JOI_SCRIPT"
}

if (-not (Test-Path $sourceScript)) {
    Write-Host "Error: $JOI_SCRIPT not found in:" -ForegroundColor Red
    Write-Host "  $scriptDir"
    Write-Host ""
    Write-Host "Make sure you're running joit.ps1 from the joi project directory"
    exit 1
}

$installPath = Get-JoiInstallPath
$binPath = Get-JoiBinPath

Write-Host "Installing joi v$JOI_VERSION..."
Write-Host ""

# Create install directory
try {
    New-Item -ItemType Directory -Path $installPath -Force | Out-Null
    Write-Host "  Created: $installPath"
} catch {
    Write-Host ""
    Write-Host "Failed to create directory: $installPath" -ForegroundColor Red
    Show-ManualInstructions -InstallPath $installPath
    exit 1
}

# Copy script
try {
    Copy-Item $sourceScript -Destination $binPath -Force
    Write-Host "  Copied: joi.ps1"
} catch {
    Write-Host ""
    Write-Host "Failed to copy script" -ForegroundColor Red
    exit 1
}

# Add to PATH
$pathAdded = Add-ToPath

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "joi installed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

if ($pathAdded) {
    Write-Host "IMPORTANT: Restart your terminal for PATH changes to take effect"
    Write-Host ""
    Write-Host "Then run:" -ForegroundColor Cyan
    Write-Host "  joi check"
} else {
    Show-ManualInstructions -InstallPath $installPath
}

Write-Host ""
