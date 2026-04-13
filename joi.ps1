#!/usr/bin/env pwsh
# =============================================================================
# joi.ps1 - Project Development Tool (PowerShell version)
# =============================================================================

param(
    [switch]$Help,
    [switch]$Version,
    [switch]$Yes,
    [switch]$NoColor,
    [switch]$Verbose,
    [switch]$Quiet,
    [switch]$Debug
)

# =============================================================================
# Constants
# =============================================================================
$JOI_VERSION = "0.2.0"
$JOI_NAME = "joi"
$JOI_DESC = "Project Development Tool"
$JOI_ROOT = $PSScriptRoot
$JOI_LOCK_FILE = Join-Path $JOI_ROOT ".joi.lock"
$JOI_ENV_FILE = Join-Path $JOI_ROOT ".joi.env"
$JOI_ENV_EXAMPLE = Join-Path $JOI_ROOT ".joi.env.example"

$EXIT_SUCCESS = 0
$EXIT_ERROR = 1
$EXIT_USAGE = 2
$EXIT_DEP = 3

# Global flags
$script:JOI_YES = $Yes
$script:JOI_VERBOSE = $Verbose
$script:JOI_QUIET = $Quiet
$script:JOI_NO_COLOR = $NoColor

# =============================================================================
# Color support
# =============================================================================
if ($NoColor -or $env:JOI_NO_COLOR -eq '1') {
    $C_RESET = $C_BOLD = $C_RED = $C_GREEN = $C_YELLOW = $C_BLUE = $C_CYAN = $C_WHITE = $C_DIM = $C_BRIGHT_GREEN = $C_BRIGHT_CYAN = ""
}
else {
    $C_RESET = "`e[0m"
    $C_BOLD = "`e[1m"
    $C_RED = "`e[31m"
    $C_GREEN = "`e[32m"
    $C_YELLOW = "`e[33m"
    $C_BLUE = "`e[34m"
    $C_CYAN = "`e[36m"
    $C_WHITE = "`e[37m"
    $C_DIM = "`e[2m"
    $C_BRIGHT_GREEN = "`e[1;32m"
    $C_BRIGHT_CYAN = "`e[1;36m"
}

# Symbols (ASCII-safe fallback)
if ($NoColor) {
    $S_SUCCESS = "+"; $S_ERROR = "x"; $S_WARN = "!"; $S_INFO = "i";
    $S_BULLET = "*"; $S_POINTER = ">"
}
else {
    $S_SUCCESS = "√"; $S_ERROR = "✗"; $S_WARN = "!"; $S_INFO = "i";
    $S_BULLET = "•"; $S_POINTER = "▸"
}

# =============================================================================
# Timing
# =============================================================================
$script:_startTime = 0

function Start-Timer {
    $script:_startTime = [DateTimeOffset]::Now.ToUnixTimeMilliseconds()
}

function Get-Elapsed {
    $endTime = [DateTimeOffset]::Now.ToUnixTimeMilliseconds()
    $elapsed = $endTime - $script:_startTime
    if ($elapsed -lt 1000) { return "${elapsed}ms" }
    $seconds = [math]::Floor($elapsed / 1000)
    $ms = $elapsed % 1000
    if ($seconds -lt 60) { return "${seconds}.$([math]::Floor($ms / 100))s" }
    $minutes = [math]::Floor($seconds / 60)
    $seconds = $seconds % 60
    return "${minutes}m ${seconds}s"
}

# =============================================================================
# Logging functions
# =============================================================================
function Write-Success {
    if ($script:JOI_QUIET) { return }
    Write-Host "$($C_GREEN)$S_SUCCESS$($C_RESET) $args"
}

function Write-Info {
    if ($script:JOI_QUIET) { return }
    Write-Host "$($C_CYAN)$S_INFO$($C_RESET) $args"
}

function Write-Warn {
    if ($script:JOI_QUIET) { return }
    Write-Host "$($C_YELLOW)$S_WARN$($C_RESET) $args"
}

function Write-ErrorMsg {
    Write-Host "$($C_RED)$S_ERROR$($C_RESET) $args" 2>&1
}

function Write-Dim {
    if ($script:JOI_QUIET) { return }
    Write-Host "$($C_DIM)$args$($C_RESET)"
}

function Write-Step {
    if ($script:JOI_QUIET) { return }
    Write-Host ""
    Write-Host "$($C_BRIGHT_CYAN)$S_POINTER$($C_RESET) $($C_BOLD)$args$($C_RESET)"
}

function Write-Item {
    if ($script:JOI_QUIET) { return }
    Write-Host "  $($C_DIM)$S_BULLET$($C_RESET) $args"
}

function Write-Header {
    if ($script:JOI_QUIET) { return }
    Write-Host ""
    Write-Host "$($C_BRIGHT_CYAN)     _       _ $($C_RESET)"
    Write-Host "$($C_BRIGHT_CYAN)    (_) ___ (_)$($C_RESET)"
    Write-Host "$($C_BRIGHT_CYAN)    | |/ _ \| |$($C_RESET)"
    Write-Host "$($C_BRIGHT_CYAN)    | | (_) | |$($C_RESET)"
    Write-Host "$($C_BRIGHT_CYAN)   _/ |\___/|_|$($C_RESET)"
    Write-Host "$($C_BRIGHT_CYAN)  |__/          $($C_RESET)"
    Write-Host ""
    Write-Host "  $($C_DIM)$JOI_VERSION - $JOI_DESC$($C_RESET)"
}

# =============================================================================
# Progress indicator (spinner)
# =============================================================================
function Invoke-WithProgress {
    param(
        [string]$Message,
        [scriptblock]$ScriptBlock
    )
    if ($script:JOI_QUIET) {
        & $ScriptBlock | Out-Default
        return $LASTEXITCODE
    }
    if ($script:JOI_VERBOSE) {
        Write-Dim "... $Message"
        & $ScriptBlock
        return $LASTEXITCODE
    }
    $spinner = @('⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏')
    $job = Start-Job -ScriptBlock $ScriptBlock
    $i = 0
    while ($job.State -eq 'Running') {
        Write-Host -NoNewline "`r$($C_CYAN)$($spinner[$i])$($C_RESET) $Message"
        $i = ($i + 1) % $spinner.Length
        Start-Sleep -Milliseconds 80
    }
    Write-Host -NoNewline "`r"
    Receive-Job $job -Wait -AutoRemoveJob | Out-Default
    return $job.ExitCode
}

# =============================================================================
# Confirmation prompt
# =============================================================================
function Confirm-Action {
    param([string]$Prompt, [string]$Default = "n")
    if ($script:JOI_YES) { return $true }
    $hint = if ($Default -eq 'y') { 'Y/n' } else { 'y/N' }
    $answer = Read-Host "$($C_YELLOW)?$($C_RESET) $Prompt $($C_DIM)($hint)$($C_RESET) "
    if ([string]::IsNullOrEmpty($answer)) { $answer = $Default }
    return $answer -match '^[Yy]$'
}

# =============================================================================
# Lock file management
# =============================================================================
$script:LockAcquired = $false
function Acquire-Lock {
    if (Test-Path $JOI_LOCK_FILE) {
        $pidContent = Get-Content $JOI_LOCK_FILE -ErrorAction SilentlyContinue
        if ($pidContent -and (Get-Process -Id $pidContent -ErrorAction SilentlyContinue)) {
            Write-ErrorMsg "Another instance is running (PID $pidContent)"
            Write-Dim "  If stuck, delete $JOI_LOCK_FILE"
            exit $EXIT_ERROR
        }
        Remove-Item $JOI_LOCK_FILE -Force -ErrorAction SilentlyContinue
    }
    $script:LockAcquired = $true
    Set-Content $JOI_LOCK_FILE -Value $PID -Force
}

function Release-Lock {
    if ($script:LockAcquired -and (Test-Path $JOI_LOCK_FILE)) {
        Remove-Item $JOI_LOCK_FILE -Force -ErrorAction SilentlyContinue
        $script:LockAcquired = $false
    }
}

# Cleanup on exit
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Release-Lock }
trap {
    Release-Lock
    if ($_.Exception.Message -match 'Ctrl\+C') { Write-Warn "Interrupted" }
    exit $EXIT_ERROR
}

# =============================================================================
# Config loading
# =============================================================================
function Load-Config {
    $script:JOI_SEED_DATA = $env:JOI_SEED_DATA
    $script:JOI_CREATE_ADMIN = $env:JOI_CREATE_ADMIN
    $script:JOI_PORT = $env:JOI_PORT
    $script:JOI_PYTHON = $env:JOI_PYTHON

    if (Test-Path $JOI_ENV_FILE) {
        Get-Content $JOI_ENV_FILE | ForEach-Object {
            if ($_ -match '^([^#][^=]*)=(.*)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim() -replace '^["'']?(.*)["'']?$', '$1'
                switch ($key) {
                    'SEED_DATA' { if (-not $script:JOI_SEED_DATA) { $script:JOI_SEED_DATA = $value } }
                    'CREATE_ADMIN' { if (-not $script:JOI_CREATE_ADMIN) { $script:JOI_CREATE_ADMIN = $value } }
                    'PORT' { if (-not $script:JOI_PORT) { $script:JOI_PORT = $value } }
                    'PYTHON' { if (-not $script:JOI_PYTHON) { $script:JOI_PYTHON = $value } }
                }
            }
        }
    }
    if (-not $script:JOI_SEED_DATA) { $script:JOI_SEED_DATA = 'y' }
    if (-not $script:JOI_CREATE_ADMIN) { $script:JOI_CREATE_ADMIN = 'n' }
    if (-not $script:JOI_PORT) { $script:JOI_PORT = '8000' }
}

# =============================================================================
# Python & dependency helpers
# =============================================================================
function Get-PythonPath {
    if ($script:JOI_PYTHON) { return $script:JOI_PYTHON }
    $venvPy = Join-Path $JOI_ROOT ".venv\Scripts\python.exe"
    if (Test-Path $venvPy) { return $venvPy }
    $venvPy = Join-Path $JOI_ROOT ".venv\bin\python"
    if (Test-Path $venvPy) { return $venvPy }
    Write-ErrorMsg "Python not found in .venv"
    return $null
}

function Test-Uv {
    if (Get-Command uv -ErrorAction SilentlyContinue) { return $true }
    Write-Warn "uv is not installed"
    if (Confirm-Action "Install uv now?" "y") {
        Write-Info "Installing uv..."
        try {
            $result = Invoke-WithProgress "Installing uv" {
                iex "& { $(irm https://astral.sh/uv/install.ps1) }" | Out-Default
            }
            if ($LASTEXITCODE -eq 0) {
                $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + $env:Path
                Write-Success "uv installed"
                return $true
            }
            throw "Installation failed"
        }
        catch {
            Write-ErrorMsg "Failed to install uv"
            return $false
        }
    }
    Write-ErrorMsg "uv is required (https://docs.astral.sh/uv/)"
    return $false
}

function Test-Venv {
    $venvPath = Join-Path $JOI_ROOT ".venv"
    if (-not (Test-Path $venvPath)) {
        Write-Info "Creating virtual environment..."
        $result = Invoke-WithProgress "Creating virtual environment" { uv venv }
        if ($LASTEXITCODE -ne 0) {
            Write-ErrorMsg "Failed to create virtual environment"
            return $false
        }
        Write-Success "Created .venv"
    }
    return $true
}

# =============================================================================
# Command implementations
# =============================================================================
function Invoke-Check {
    Write-Header
    Write-Host ""

    # uv
    $uvVer = & uv --version 2>$null
    if ($uvVer -match '(\d+\.\d+\.\d+)') {
        Write-Success "uv $($C_DIM)$($Matches[1])$($C_RESET)"
    }
    else {
        Write-ErrorMsg "uv not installed"
        Write-Dim "  Run: $($C_CYAN)joi install$($C_RESET)"
    }

    # venv / python
    if (Test-Path (Join-Path $JOI_ROOT ".venv")) {
        $python = Get-PythonPath
        if ($python) {
            $pyVer = & $python --version 2>&1
            if ($pyVer -match '(\d+\.\d+\.\d+)') {
                Write-Success "Python $($C_DIM)$($Matches[1])$($C_RESET)"
            }
            $pkgCount = if (Get-Command uv -ErrorAction SilentlyContinue) {
                (& uv pip list 2>$null | Measure-Object | Select-Object -ExpandProperty Count) - 2
            } else {
                & $python -m pip list 2>$null | Measure-Object | Select-Object -ExpandProperty Count
            }
            if ($pkgCount -lt 0) { $pkgCount = 0 }
            Write-Item "$pkgCount packages installed"
        }
        else {
            Write-Warn "Virtual environment exists but Python not found"
        }
    }
    else {
        Write-ErrorMsg "Virtual environment not found"
        Write-Dim "  Run: $($C_CYAN)joi install$($C_RESET)"
    }

    # database
    Write-Host ""
    $dbPath = Join-Path $JOI_ROOT "db.sqlite3"
    if (Test-Path $dbPath) {
        $size = [math]::Round((Get-Item $dbPath).Length / 1KB, 1)
        Write-Success "Database $($C_DIM)${size}KB$($C_RESET)"
    }
    else {
        Write-Warn "Database not found"
        Write-Dim "  Run: $($C_CYAN)joi migrate$($C_RESET)"
    }

    # fixtures
    $fixtures = Join-Path $JOI_ROOT "fixtures"
    if (Test-Path $fixtures) {
        $count = (Get-ChildItem "$fixtures\*.json" -ErrorAction SilentlyContinue | Measure-Object).Count
        Write-Item "$count fixture files"
    }
    elseif (Test-Path (Join-Path $JOI_ROOT "data_seeding.sql")) {
        Write-Item "data_seeding.sql available"
    }
    else {
        Write-Warn "No seed data found"
    }

    # config
    Write-Host ""
    if (Test-Path $JOI_ENV_FILE) {
        Write-Success "Configuration loaded"
        Write-Dim "  $JOI_ENV_FILE"
    }
    else {
        Write-Info "Using default configuration"
        Write-Dim "  Copy $JOI_ENV_EXAMPLE → $JOI_ENV_FILE to customize"
    }
    Write-Host ""
}

function Invoke-CompileMessages {
    $python = Get-PythonPath
    if (-not $python) { return }
    Write-Dim "  $S_BULLET Compiling translations..."
    & $python manage.py compilemessages >$null 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Translations compiled"
    }
}

function Invoke-Install {
    Write-Header
    Write-Step "Installing dependencies"
    if (-not (Test-Uv)) { return $EXIT_ERROR }
    if (-not (Test-Venv)) { return $EXIT_ERROR }

    # Clean Windows‑created symlink on Unix
    $lib64 = Join-Path $JOI_ROOT ".venv\lib64"
    if (Test-Path $lib64) {
        $item = Get-Item $lib64 -ErrorAction SilentlyContinue
        if ($item -and $item.LinkType -eq 'Junction') {
            Remove-Item $lib64 -Force
        }
    }

    Start-Timer
    $result = Invoke-WithProgress "Running uv sync" { uv sync }
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""; Write-ErrorMsg "Installation failed"; return $EXIT_ERROR
    }
    $python = Get-PythonPath
    $pkgCount = if (Get-Command uv -ErrorAction SilentlyContinue) {
        (& uv pip list 2>$null | Measure-Object | Select-Object -ExpandProperty Count) - 2
    } else {
        & $python -m pip list 2>$null | Measure-Object | Select-Object -ExpandProperty Count
    }
    if ($pkgCount -lt 0) { $pkgCount = 0 }
    $elapsed = Get-Elapsed
    Write-Host ""; Write-Success "Installed $($C_BOLD)$pkgCount$($C_RESET) packages in $($C_DIM)$elapsed$($C_RESET)"
    
    Invoke-CompileMessages
    Write-Host ""
    return $EXIT_SUCCESS
}

function Invoke-Migrate {
    Write-Header
    $python = Get-PythonPath
    if (-not $python) { return $EXIT_DEP }
    Write-Step "Running migrations"
    Write-Host ""
    Write-Dim "  makemigrations"
    & $python manage.py makemigrations
    if ($LASTEXITCODE -ne 0) { Write-Host ""; Write-ErrorMsg "makemigrations failed"; return $EXIT_ERROR }
    Write-Dim "  migrate"
    & $python manage.py migrate
    if ($LASTEXITCODE -ne 0) { Write-Host ""; Write-ErrorMsg "Migration failed"; return $EXIT_ERROR }
    Write-Host ""; Write-Success "Migrations applied"
    Write-Host ""
    return $EXIT_SUCCESS
}

function Invoke-Seed {
    param([switch]$Clear)
    Write-Header
    $python = Get-PythonPath
    if (-not $python) { return $EXIT_DEP }

    $shouldClear = $Clear -or $script:JOI_CLEAR

    if ($shouldClear) {
        Write-Warn "This will delete all existing data"
        if (-not (Confirm-Action "Continue?" "n")) {
            Write-Info "Cancelled"; return $EXIT_SUCCESS
        }
        Write-Host ""
        & $python manage.py load_data --clear
        if ($LASTEXITCODE -ne 0) { Write-Host ""; Write-ErrorMsg "Seeding failed"; return $EXIT_ERROR }
        Write-Host ""; Write-Success "Database cleared and reseeded"
        return $EXIT_SUCCESS
    }

    Write-Step "Seeding database"
    Write-Host ""
    $fixtures = Join-Path $JOI_ROOT "fixtures"
    if (Test-Path $fixtures) {
        & $python manage.py load_data
        if ($LASTEXITCODE -ne 0) { Write-Host ""; Write-ErrorMsg "Seeding failed"; return $EXIT_ERROR }
        Write-Host ""; Write-Success "Database seeded"
    }
    elseif (Test-Path (Join-Path $JOI_ROOT "data_seeding.sql")) {
        Write-Warn "Using legacy data_seeding.sql"
        & $python seed_db.py
        if ($LASTEXITCODE -ne 0) { Write-Host ""; Write-ErrorMsg "Seeding failed"; return $EXIT_ERROR }
        Write-Host ""; Write-Success "Database seeded"
    }
    else {
        Write-ErrorMsg "No seed data found (fixtures/ or data_seeding.sql)"
        return $EXIT_ERROR
    }
    Write-Host ""
    return $EXIT_SUCCESS
}

function Invoke-Admin {
    Write-Header
    $python = Get-PythonPath
    if (-not $python) { return $EXIT_DEP }
    Write-Step "Creating admin user"
    Write-Host ""
    & $python manage.py createsuperuser
    Write-Host ""; Write-Success "Admin user created"
    Write-Host ""
    return $EXIT_SUCCESS
}

function Invoke-Server {
    param([string]$Port)
    Write-Header
    $python = Get-PythonPath
    if (-not $python) { return $EXIT_DEP }
    
    Invoke-CompileMessages

    $port = if ($Port) { $Port } else { $script:JOI_PORT }
    Write-Host ""; Write-Success "Starting server on ${C_CYAN}http://127.0.0.1:$port$C_RESET"
    Write-Dim "  Press Ctrl+C to stop"; Write-Host ""
    & $python manage.py runserver "127.0.0.1:$port"
    return $LASTEXITCODE
}

function Invoke-Reset {
    Write-Header
    $python = Get-PythonPath
    if (-not $python) { return $EXIT_DEP }
    Write-Warn "This will delete the database and all data"
    if (-not (Confirm-Action "Continue?" "n")) {
        Write-Info "Cancelled"; return $EXIT_SUCCESS
    }
    Write-Step "Resetting database"
    Write-Host ""
    $dbPath = Join-Path $JOI_ROOT "db.sqlite3"
    if (Test-Path $dbPath) {
        Remove-Item $dbPath -Force
        Write-Dim "  $S_BULLET Removed db.sqlite3"
    }
    Write-Dim "  $S_BULLET Running makemigrations"
    & $python manage.py makemigrations >$null 2>&1
    Write-Dim "  $S_BULLET Running migrate"
    & $python manage.py migrate >$null 2>&1
    Write-Host ""; Write-Success "Database reset"
    if (Test-Path (Join-Path $JOI_ROOT "fixtures")) {
        if (Confirm-Action "Seed the database?" "y") {
            $global:JOI_YES = $true
            Invoke-Seed
        }
    }
    Write-Host ""
    return $EXIT_SUCCESS
}

function Invoke-Setup {
    param(
        [string]$SeedFlag,
        [string]$AdminFlag,
        [switch]$SkipMigrations
    )
    Write-Header
    Write-Host ""
    $setupStart = Get-Date

    Write-Step "Package manager"
    if (-not (Test-Uv)) { return $EXIT_ERROR }
    Write-Step "Virtual environment"
    if (-not (Test-Venv)) { return $EXIT_ERROR }
    Write-Step "Dependencies"
    Start-Timer
    $result = Invoke-WithProgress "Running uv sync" { uv sync }
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""; Write-ErrorMsg "Installation failed"; return $EXIT_ERROR
    }
    $python = Get-PythonPath
    if (-not $python) { return $EXIT_DEP }
    $pkgCount = if (Get-Command uv -ErrorAction SilentlyContinue) {
        (& uv pip list 2>$null | Measure-Object | Select-Object -ExpandProperty Count) - 2
    } else {
        & $python -m pip list 2>$null | Measure-Object | Select-Object -ExpandProperty Count
    }
    if ($pkgCount -lt 0) { $pkgCount = 0 }
    $elapsed = Get-Elapsed
    Write-Host ""; Write-Success "Installed $($C_BOLD)$pkgCount$($C_RESET) packages in $($C_DIM)$elapsed$($C_RESET)"

    $shouldSkipMig = $SkipMigrations -or $script:JOI_SKIP_MIGRATIONS
    if (-not $shouldSkipMig) {
        Write-Step "Database"
        Write-Host ""
        Write-Dim "  $S_BULLET makemigrations"
        & $python manage.py makemigrations >$null 2>&1
        Write-Dim "  $S_BULLET migrate"
        & $python manage.py migrate >$null 2>&1
        Write-Host ""; Write-Success "Migrations applied"
    }

    $createAdmin = if ($AdminFlag) { $AdminFlag } elseif ($script:JOI_ADMIN_FLAG) { $script:JOI_ADMIN_FLAG } else { $script:JOI_CREATE_ADMIN }
    if ($createAdmin -eq 'y' -or ($script:JOI_YES -and -not $AdminFlag -and -not $script:JOI_ADMIN_FLAG)) {
        Write-Step "Admin user"; Write-Host ""
        & $python manage.py createsuperuser
        Write-Host ""; Write-Success "Admin user created"
    }
    elseif (-not $AdminFlag -and -not $script:JOI_ADMIN_FLAG) {
        if (Confirm-Action "Create admin user?" "n") {
            Write-Step "Admin user"; Write-Host ""
            & $python manage.py createsuperuser
            Write-Host ""; Write-Success "Admin user created"
        }
    }

    $seed = if ($SeedFlag) { $SeedFlag } elseif ($script:JOI_SEED_FLAG) { $script:JOI_SEED_FLAG } else { $script:JOI_SEED_DATA }
    $fixtures = Join-Path $JOI_ROOT "fixtures"
    if ($seed -eq 'y') {
        if (Test-Path $fixtures) {
            Write-Step "Seed data"; Write-Host ""
            & $python manage.py load_data >$null 2>&1
            Write-Host ""; Write-Success "Database seeded"
        }
    }
    elseif (-not $SeedFlag -and -not $script:JOI_SEED_FLAG) {
        if (Confirm-Action "Seed database with sample data?" "n") {
            if (Test-Path $fixtures) {
                Write-Step "Seed data"; Write-Host ""
                & $python manage.py load_data >$null 2>&1
                Write-Host ""; Write-Success "Database seeded"
            }
        }
    }

    Invoke-CompileMessages

    $elapsed = [math]::Round(((Get-Date) - $setupStart).TotalSeconds, 1)
    Write-Host ""; Write-Success "Setup complete! $($C_DIM)${elapsed}s$($C_RESET)"
    Write-Host ""; Write-Dim "Next steps:"
    Write-Host "  $($C_CYAN)joi server$($C_RESET)  Start development server"
    Write-Host "  $($C_CYAN)joi admin$($C_RESET)   Create admin user"
    Write-Host ""
    return $EXIT_SUCCESS
}

function Invoke-Update {
    Write-Header
    Write-Host ""
    Write-Step "Checking for updates..."
    Write-Host ""
    Write-Dim "  Current version: $($C_BOLD)$JOI_VERSION$($C_RESET)"
    Write-Dim "  Latest version:  $($C_BOLD)$JOI_VERSION$($C_RESET) (check GitHub for updates)"
    Write-Host ""
    Write-Info "To update manually:"
    Write-Host "    1. Download latest joi.ps1"
    Write-Host "    2. Replace this file"
    Write-Host ""
    Write-Info "To reinstall from project:"
    Write-Host "    $($C_CYAN)joi install$($C_RESET)"
    Write-Host ""
}

function Show-Help {
    Write-Host ""
    Write-Host "$($C_BRIGHT_CYAN)     _       _ $($C_RESET)"
    Write-Host "$($C_BRIGHT_CYAN)    (_) ___ (_)$($C_RESET)"
    Write-Host "$($C_BRIGHT_CYAN)    | |/ _ \| |$($C_RESET)"
    Write-Host "$($C_BRIGHT_CYAN)    | | (_) | |$($C_RESET)"
    Write-Host "$($C_BRIGHT_CYAN)   _/ |\___/|_|$($C_RESET)"
    Write-Host "$($C_BRIGHT_CYAN)  |__/          $($C_RESET)"
    Write-Host ""
    Write-Host "  $($C_DIM)$JOI_VERSION - $JOI_DESC$($C_RESET)"
    Write-Host ""
    Write-Host "$($C_DIM) USAGE$($C_RESET)"
    Write-Host "  $($C_WHITE)joi$($C_RESET) $($C_DIM)<command> [options]$($C_RESET)"
    Write-Host ""
    Write-Host "$($C_DIM) COMMANDS$($C_RESET)"
    Write-Host "  $($C_CYAN)setup$($C_RESET)       Full project setup (install + migrate + seed)"
    Write-Host "  $($C_CYAN)install$($C_RESET)     Install dependencies"
    Write-Host "  $($C_CYAN)migrate$($C_RESET)     Run database migrations"
    Write-Host "  $($C_CYAN)seed$($C_RESET)         Seed database with fixtures"
    Write-Host "  $($C_CYAN)admin$($C_RESET)        Create admin user"
    Write-Host "  $($C_CYAN)server$($C_RESET)       Start development server"
    Write-Host "  $($C_CYAN)check$($C_RESET)        Check environment status"
    Write-Host "  $($C_CYAN)reset$($C_RESET)        Reset database"
    Write-Host "  $($C_CYAN)update$($C_RESET)       Update joi to latest version"
    Write-Host "  $($C_CYAN)help$($C_RESET)          Show this help"
    Write-Host ""
    Write-Host "$($C_DIM) OPTIONS$($C_RESET)"
    Write-Host "  -h, --help        Show help"
    Write-Host "  -v, --version     Show version"
    Write-Host "  -y, --yes         Skip confirmations"
    Write-Host "  --no-color        Disable colors"
    Write-Host "  --verbose         Detailed output"
    Write-Host "  --quiet           Minimal output"
    Write-Host ""
    Write-Host "$($C_DIM) EXAMPLES$($C_RESET)"
    Write-Host "  $($C_WHITE)joi setup$($C_RESET)              $($C_DIM)# Interactive setup$($C_RESET)"
    Write-Host "  $($C_WHITE)joi setup -y --no-seed$($C_RESET)  $($C_DIM)# Auto-setup, skip seeding$($C_RESET)"
    Write-Host "  $($C_WHITE)joi seed --clear$($C_RESET)       $($C_DIM)# Reset and reseed data$($C_RESET)"
    Write-Host "  $($C_WHITE)joi server --port 8080$($C_RESET) $($C_DIM)# Custom port$($C_RESET)"
    Write-Host "  $($C_WHITE)joi check$($C_RESET)              $($C_DIM)# Check environment$($C_RESET)"
    Write-Host ""
}

function Show-Version {
    Write-Host ""
    Write-Host "$($C_BRIGHT_CYAN)     _       _ $($C_RESET)"
    Write-Host "$($C_BRIGHT_CYAN)    (_) ___ (_)$($C_RESET)"
    Write-Host "$($C_BRIGHT_CYAN)    | |/ _ \| |$($C_RESET)"
    Write-Host "$($C_BRIGHT_CYAN)    | | (_) | |$($C_RESET)"
    Write-Host "$($C_BRIGHT_CYAN)   _/ |\___/|_|$($C_RESET)"
    Write-Host "$($C_BRIGHT_CYAN)  |__/          $($C_RESET)"
    Write-Host ""
    Write-Host "  $($C_DIM)version$($C_RESET) $($C_BOLD)$JOI_VERSION$($C_RESET)"
    Write-Host ""
}

# =============================================================================
# Main entry point
# =============================================================================
function Main {
    Load-Config

    # Parse global flags that may appear before command
    $remainingArgs = @()
    $i = 0
    while ($i -lt $args.Count) {
        $arg = $args[$i]
        switch -Wildcard ($arg) {
            '-h' { Show-Help; exit $EXIT_SUCCESS }
            '--help' { Show-Help; exit $EXIT_SUCCESS }
            '-v' { Show-Version; exit $EXIT_SUCCESS }
            '--version' { Show-Version; exit $EXIT_SUCCESS }
            '-y' { $script:JOI_YES = $true }
            '--yes' { $script:JOI_YES = $true }
            '--no-color' { $script:JOI_NO_COLOR = $true; $C_RESET = $C_BOLD = $C_RED = $C_GREEN = $C_YELLOW = $C_BLUE = $C_CYAN = $C_WHITE = $C_DIM = $C_BRIGHT_GREEN = $C_BRIGHT_CYAN = "" }
            '--verbose' { $script:JOI_VERBOSE = $true }
            '--quiet' { $script:JOI_QUIET = $true }
            '--debug' { $script:JOI_DEBUG = $true; Set-PSDebug -Trace 1 }
            '--port' {
                $i++
                if ($i -lt $args.Count) { $script:JOI_PORT = $args[$i] }
            }
            '--clear' { $script:JOI_CLEAR = $true }
            '--seed' { $script:JOI_SEED_FLAG = "y" }
            '--no-seed' { $script:JOI_SEED_FLAG = "n" }
            '--admin' { $script:JOI_ADMIN_FLAG = "y" }
            '--no-admin' { $script:JOI_ADMIN_FLAG = "n" }
            '--skip-migrations' { $script:JOI_SKIP_MIGRATIONS = $true }
            default { $remainingArgs += $arg }
        }
        $i++
    }

    if ($remainingArgs.Count -eq 0) {
        Show-Help
        exit $EXIT_SUCCESS
    }

    $command = $remainingArgs[0]
    $commandArgs = $remainingArgs[1..$remainingArgs.Count]

    # Check project directory (allow update from anywhere)
    $isProject = (Test-Path (Join-Path $JOI_ROOT "manage.py")) -or
    (Test-Path (Join-Path $JOI_ROOT "joi.ps1")) -or
    (Test-Path $JOI_ENV_FILE)
    if (-not $isProject -and $command -ne 'update') {
        Write-ErrorMsg "Not a joi project directory"
        Write-Host "  Run 'joi' from a project folder containing manage.py or joi.ps1"
        exit $EXIT_ERROR
    }

    # Acquire lock for mutating commands
    $mutatingCommands = @('setup', 'install', 'migrate', 'seed', 'admin', 'reset')
    if ($command -in $mutatingCommands) {
        Acquire-Lock
    }

    # Dispatch
    switch ($command) {
        'setup' { exit (Invoke-Setup @commandArgs) }
        'install' { exit (Invoke-Install @commandArgs) }
        'migrate' { exit (Invoke-Migrate @commandArgs) }
        'seed' { exit (Invoke-Seed @commandArgs) }
        'admin' { exit (Invoke-Admin @commandArgs) }
        'server' { exit (Invoke-Server @commandArgs) }
        'check' { Invoke-Check; exit $EXIT_SUCCESS }
        'reset' { exit (Invoke-Reset @commandArgs) }
        'update' { Invoke-Update; exit $EXIT_SUCCESS }
        'help' { Show-Help; exit $EXIT_SUCCESS }
        'version' { Show-Version; exit $EXIT_SUCCESS }
        default {
            Write-ErrorMsg "Unknown command: $command"
            Write-Host "  Run '$($C_CYAN)joi --help$($C_RESET)' for usage"
            exit $EXIT_USAGE
        }
    }
}

# Run main
Main @args