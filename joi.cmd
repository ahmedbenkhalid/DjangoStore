@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ==========================================
:: JOI CLI - Batch Implementation
:: ==========================================
set "JOI_VERSION=0.2.0"
set "JOI_NAME=joi"
set "JOI_DESC=Project Development Tool"

:: ==========================================
:: Load Configuration
:: ==========================================
set "CFG_ADMIN_USER="
set "CFG_ADMIN_EMAIL="
set "CFG_ADMIN_PASS="
if exist ".joi.env" (
    for /f "usebackq tokens=1,* delims==" %%A in (".joi.env") do (
        set "KEY=%%A"
        set "VAL=%%B"
        if "!KEY!"=="ADMIN_USERNAME" set "CFG_ADMIN_USER=!VAL!"
        if "!KEY!"=="ADMIN_EMAIL" set "CFG_ADMIN_EMAIL=!VAL!"
        if "!KEY!"=="ADMIN_PASSWORD" set "CFG_ADMIN_PASS=!VAL!"
    )
)

:: ==========================================
:: Parse Global Arguments
:: ==========================================
set "COMMAND=%~1"
if "%COMMAND%"=="" goto :help

if /i "%COMMAND%"=="setup" (
    shift
    goto :parse_setup
)
if /i "%COMMAND%"=="install" (
    shift
    goto :cmd_install
)
if /i "%COMMAND%"=="migrate" (
    shift
    goto :cmd_migrate
)
if /i "%COMMAND%"=="seed" (
    shift
    goto :parse_seed
)
if /i "%COMMAND%"=="admin" (
    shift
    goto :parse_admin
)
if /i "%COMMAND%"=="server" (
    shift
    goto :parse_server
)
if /i "%COMMAND%"=="reset" (
    shift
    goto :cmd_reset
)
if /i "%COMMAND%"=="check" (
    shift
    goto :cmd_check
)
if /i "%COMMAND%"=="help" goto :help

:: If command not implemented
call :write_error "Command '%COMMAND%' is not recognized."
echo.
call :write_dim "Currently available commands: setup, install, migrate, seed, reset, check, admin, server, help"
exit /b 1


:: ==========================================
:: Command: Install
:: ==========================================
:cmd_install
call :write_header
call :write_step "Package manager"
where uv >nul 2>nul
if !errorlevel! neq 0 (
    call :write_error "uv is not installed"
    call :write_dim "Please install uv: https://docs.astral.sh/uv/"
    exit /b 1
)
call :write_step "Virtual environment"
if not exist ".venv" (
    uv venv
    if !errorlevel! neq 0 (
        call :write_error "Failed to create venv"
        exit /b 1
    )
)
call :write_step "Dependencies"
uv sync
if !errorlevel! neq 0 (
    call :write_error "Installation failed"
    exit /b 1
)
call :get_python
"!_PYTHON_EXE!" manage.py compilemessages >nul 2>&1
call :write_success "Installed packages"
exit /b 0


:: ==========================================
:: Command: Migrate
:: ==========================================
:cmd_migrate
call :write_header
call :get_python
if "!_PYTHON_EXE!"=="" exit /b 3
call :write_step "Running migrations"
"!_PYTHON_EXE!" manage.py makemigrations
if !errorlevel! neq 0 exit /b 1
"!_PYTHON_EXE!" manage.py migrate
if !errorlevel! neq 0 exit /b 1
call :write_success "Migrations applied"
exit /b 0


:: ==========================================
:: Command: Seed
:: ==========================================
:parse_seed
set "_CLEAR_SEED=0"
:seed_loop
if "%~1"=="" goto :cmd_seed
if /i "%~1"=="--clear" set "_CLEAR_SEED=1" & shift & goto :seed_loop
shift
goto :seed_loop

:cmd_seed
call :write_header
call :get_python
if "!_PYTHON_EXE!"=="" exit /b 3
if "!_CLEAR_SEED!"=="1" (
    call :write_warn "This will delete all existing data"
    set /p "ANS_CONT=Continue? (y/N): "
    if /i not "!ANS_CONT!"=="y" exit /b 0
    call :write_step "Clearing and Seeding database"
    "!_PYTHON_EXE!" manage.py load_data --clear
) else (
    call :write_step "Seeding database"
    "!_PYTHON_EXE!" manage.py load_data
)
if !errorlevel! neq 0 exit /b 1
call :write_success "Database seeded"
exit /b 0


:: ==========================================
:: Command: Reset
:: ==========================================
:cmd_reset
call :write_header
call :get_python
if "!_PYTHON_EXE!"=="" exit /b 3
call :write_warn "This will delete the database and all data"
set /p "ANS_RST=Continue? (y/N): "
if /i not "!ANS_RST!"=="y" exit /b 0

call :write_step "Resetting database"
if exist "db.sqlite3" (
    del /f /q "db.sqlite3"
    call :write_dim "  * Removed db.sqlite3"
)
call :write_dim "  * Running makemigrations"
"!_PYTHON_EXE!" manage.py makemigrations >nul 2>&1
call :write_dim "  * Running migrate"
"!_PYTHON_EXE!" manage.py migrate >nul 2>&1
call :write_success "Database reset"

if exist "fixtures" (
    set /p "ANS_SEED=Seed the database? (y/N): "
    if /i "!ANS_SEED!"=="y" (
        "!_PYTHON_EXE!" manage.py load_data
    )
)
exit /b 0


:: ==========================================
:: Command: Check
:: ==========================================
:cmd_check
call :write_header
where uv >nul 2>nul
if !errorlevel! equ 0 (
    for /f "tokens=*" %%i in ('uv --version') do call :write_success "%%i"
) else (
    call :write_error "uv not installed"
)
call :get_python
if not "!_PYTHON_EXE!"=="" (
    for /f "tokens=*" %%i in ('"!_PYTHON_EXE!" --version 2^>^&1') do call :write_success "%%i"
)
if exist "db.sqlite3" (
    call :write_success "Database found (db.sqlite3)"
) else (
    call :write_warn "Database not found"
)
exit /b 0


:: ==========================================
:: Command: Setup
:: ==========================================
:parse_setup
set "_SKIP_MIG=0"
set "_SEED_FLAG="
set "_ADMIN_FLAG="

:setup_loop
if "%~1"=="" goto :cmd_setup
if /i "%~1"=="--skip-migrations" set "_SKIP_MIG=1" & shift & goto :setup_loop
if /i "%~1"=="--seed" set "_SEED_FLAG=y" & shift & goto :setup_loop
if /i "%~1"=="--no-seed" set "_SEED_FLAG=n" & shift & goto :setup_loop
if /i "%~1"=="--admin" set "_ADMIN_FLAG=y" & shift & goto :setup_loop
if /i "%~1"=="--no-admin" set "_ADMIN_FLAG=n" & shift & goto :setup_loop
shift
goto :setup_loop

:cmd_setup
call :write_header
call :write_step "Package manager"
where uv >nul 2>nul
if !errorlevel! neq 0 (
    call :write_error "uv is not installed"
    exit /b 1
)
call :write_step "Virtual environment"
if not exist ".venv" (
    uv venv
)
call :write_step "Dependencies"
uv sync

if "!_SKIP_MIG!"=="0" (
    call :get_python
    call :write_step "Database Migrations"
    "!_PYTHON_EXE!" manage.py makemigrations >nul 2>&1
    "!_PYTHON_EXE!" manage.py migrate >nul 2>&1
    call :write_success "Migrations applied"
)

:: Admin
if "!_ADMIN_FLAG!"=="" (
    set /p "ANS_ADMIN=Create admin user? (y/N): "
    if /i "!ANS_ADMIN!"=="y" set "_ADMIN_FLAG=y"
)
if /i "!_ADMIN_FLAG!"=="y" (
    call :get_python
    if not "!CFG_ADMIN_USER!"=="" if not "!CFG_ADMIN_EMAIL!"=="" if not "!CFG_ADMIN_PASS!"=="" (
        set "DJANGO_SUPERUSER_USERNAME=!CFG_ADMIN_USER!"
        set "DJANGO_SUPERUSER_EMAIL=!CFG_ADMIN_EMAIL!"
        set "DJANGO_SUPERUSER_PASSWORD=!CFG_ADMIN_PASS!"
        "!_PYTHON_EXE!" manage.py createsuperuser --noinput >nul 2>&1
        if !errorlevel! equ 0 (
            call :write_success "Admin user created"
        ) else (
            call :write_error "Admin creation failed"
        )
        set "DJANGO_SUPERUSER_USERNAME="
        set "DJANGO_SUPERUSER_EMAIL="
        set "DJANGO_SUPERUSER_PASSWORD="
    ) else (
        call :write_step "Creating admin user (interactive)"
        "!_PYTHON_EXE!" manage.py createsuperuser
    )
)

:: Seed
if "!_SEED_FLAG!"=="" (
    set /p "ANS_SEED=Seed database with sample data? (y/N): "
    if /i "!ANS_SEED!"=="y" set "_SEED_FLAG=y"
)
if /i "!_SEED_FLAG!"=="y" (
    call :get_python
    call :write_step "Seed data"
    "!_PYTHON_EXE!" manage.py load_data >nul 2>&1
    if !errorlevel! equ 0 (
        call :write_success "Database seeded"
    ) else (
        call :write_error "Seeding failed"
    )
)

call :write_success "Setup complete!"
exit /b 0


:: ==========================================
:: Command: Server
:: ==========================================
:parse_server
set "_PORT=8000"
:server_loop
if "%~1"=="" goto :cmd_server
if /i "%~1"=="--port" set "_PORT=%~2" & shift & shift & goto :server_loop
shift
goto :server_loop

:cmd_server
  call :write_header
  call :get_python
  if "!_PYTHON_EXE!"=="" exit /b 3
  
  call :write_success "Starting server on http://127.0.0.1:!_PORT!"
  call :write_dim "Press Ctrl+C to stop"
  echo.
  "!_PYTHON_EXE!" manage.py runserver "127.0.0.1:!_PORT!"
  exit /b !errorlevel!


:: ==========================================
:: Command: Admin (Parse Args)
:: ==========================================
:parse_admin
set "_NOINPUT=0"
set "_ADMIN_USER="
set "_ADMIN_EMAIL="
set "_ADMIN_PASS="

:admin_loop
if "%~1"=="" goto :cmd_admin
if /i "%~1"=="--no-input" set "_NOINPUT=1" & shift & goto :admin_loop
if /i "%~1"=="-u" set "_ADMIN_USER=%~2" & shift & shift & goto :admin_loop
if /i "%~1"=="--username" set "_ADMIN_USER=%~2" & shift & shift & goto :admin_loop
if /i "%~1"=="-e" set "_ADMIN_EMAIL=%~2" & shift & shift & goto :admin_loop
if /i "%~1"=="--email" set "_ADMIN_EMAIL=%~2" & shift & shift & goto :admin_loop
if /i "%~1"=="-p" set "_ADMIN_PASS=%~2" & shift & shift & goto :admin_loop
if /i "%~1"=="--password" set "_ADMIN_PASS=%~2" & shift & shift & goto :admin_loop
shift
goto :admin_loop

:: ==========================================
:: Command: Admin (Execution)
:: ==========================================
:cmd_admin
  call :write_header
  call :get_python
  if "!_PYTHON_EXE!"=="" exit /b 3

  :: جلب القيم من flags أو config
  set "_AU=!_ADMIN_USER!"
  set "_AE=!_ADMIN_EMAIL!"
  set "_AP=!_ADMIN_PASS!"
  if "!_AU!"=="" if not "!CFG_ADMIN_USER!"==""  set "_AU=!CFG_ADMIN_USER!"
  if "!_AE!"=="" if not "!CFG_ADMIN_EMAIL!"=="" set "_AE=!CFG_ADMIN_EMAIL!"
  if "!_AP!"=="" if not "!CFG_ADMIN_PASS!"==""  set "_AP=!CFG_ADMIN_PASS!"

  :: حالة --no-input: لازم كل البيانات تكون موجودة
  if "!_NOINPUT!"=="1" (
    if "!_AU!"=="" (
      call :write_error "Username required when using --no-input. Use -u or set ADMIN_USERNAME in .joi.env"
      exit /b 1
    )
    if "!_AE!"=="" (
      call :write_error "Email required when using --no-input. Use -e or set ADMIN_EMAIL in .joi.env"
      exit /b 1
    )
    if "!_AP!"=="" (
      call :write_error "Password required when using --no-input. Use -p or set ADMIN_PASSWORD in .joi.env"
      exit /b 1
    )
    call :write_step "Creating admin user (non-interactive): !_AU!"
    set "DJANGO_SUPERUSER_USERNAME=!_AU!"
    set "DJANGO_SUPERUSER_EMAIL=!_AE!"
    set "DJANGO_SUPERUSER_PASSWORD=!_AP!"
    "!_PYTHON_EXE!" manage.py createsuperuser --noinput
    set _RC=!errorlevel!
    set "DJANGO_SUPERUSER_USERNAME="
    set "DJANGO_SUPERUSER_EMAIL="
    set "DJANGO_SUPERUSER_PASSWORD="
    if "!_RC!"=="0" (
      echo.
      call :write_success "Admin user created"
      echo.
      exit /b 0
    ) else (
      echo.
      call :write_error "Failed to create admin user"
      exit /b 1
    )
  )

  call :write_step "Creating admin user (interactive)"
  echo.
  call :write_dim "Press Ctrl+C to cancel, or enter details below"
  echo.
  "!_PYTHON_EXE!" manage.py createsuperuser
  if "!errorlevel!"=="0" (
    echo.
    call :write_success "Admin user created"
  ) else (
    echo.
    call :write_warn "Admin creation cancelled or failed"
  )
  echo.
  exit /b 0


:: ==========================================
:: Helper Functions
:: ==========================================
:get_python
set "_PYTHON_EXE="
if exist ".venv\Scripts\python.exe" (
    set "_PYTHON_EXE=.venv\Scripts\python.exe"
) else if exist ".venv\bin\python.exe" (
    set "_PYTHON_EXE=.venv\bin\python.exe"
) else if exist ".venv\bin\python" (
    set "_PYTHON_EXE=.venv\bin\python"
) else (
    call :write_error "Python not found in .venv"
)
exit /b 0

:write_header
echo.
echo      _       _ 
echo     (_) ___ (_)
echo     ^| ^|/ _ \^| ^|
echo     ^| ^| (_) ^| ^|
echo    _/ ^|\___/^|_^|
echo   ^|__/          
echo.
echo   !JOI_VERSION! - !JOI_DESC!
exit /b 0

:write_step
echo.
echo ^> %~1
exit /b 0

:write_success
echo [SUCCESS] %~1
exit /b 0

:write_error
echo [ERROR] %~1
exit /b 0

:write_warn
echo [WARN] %~1
exit /b 0

:write_dim
echo %~1
exit /b 0

:help
call :write_header
echo.
echo USAGE
echo   joi.cmd ^<command^> [options]
echo.
echo COMMANDS
echo   setup        Full project setup (install + migrate + seed)
echo   install      Install dependencies
echo   migrate      Run database migrations
echo   seed         Seed database with fixtures
echo   reset        Reset database
echo   check        Check environment status
echo   admin        Create admin user
echo   server       Start development server
echo   help         Show this help
echo.
echo ADMIN OPTIONS
echo   -u, --username    Admin username
echo   -e, --email       Admin email
echo   -p, --password    Admin password
echo   --no-input        Use env vars or prompts
echo.
echo SERVER OPTIONS
echo   --port            Server port (default 8000)
echo.
exit /b 0