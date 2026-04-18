#!/usr/bin/env bash
# =============================================================================
# joi - Project Development Tool (Optimized)
# =============================================================================
set -euo pipefail

# Disable color output if not in terminal
if [[ ! -t 1 ]]; then
  NO_COLOR=1
fi

# =============================================================================
# Auto-install completion (if running as root or with sudo)
# =============================================================================
if [[ "${1:-}" == "install-completion" ]]; then
  target="/etc/bash_completion.d/joi.bash"
  if [[ -w "$(dirname "${target}" 2>/dev/null || echo "")" ]] || [[ $EUID -eq 0 ]]; then
    cat > "${target}" << 'COMPLETION'
#!/usr/bin/env bash

_joi() {
    local cur prev words cword
    _init_completion || return

    local commands="setup install migrate seed admin server check reset update help version"
    local options="--help --version --yes --no-color --verbose --quiet --debug --port --clear --seed --no-seed --admin --no-admin --skip-migrations"

    if [[ ${cword} -eq 1 ]]; then
        COMPREPLY=($(compgen -W "${commands}" -- "${cur}"))
        return
    fi

    case "${words[1]}" in
        server) COMPREPLY=($(compgen -W "${options} --port" -- "${cur}")) ;;
        seed) COMPREPLY=($(compgen -W "${options} --clear" -- "${cur}")) ;;
        setup) COMPREPLY=($(compgen -W "${options} --seed --no-seed --admin --no-admin --skip-migrations" -- "${cur}")) ;;
    esac
}

complete -F _joi joi
COMPLETION
    echo "Installed bash completion to ${target}"
    echo "Restart shell or run: source ${target}"
    exit 0
  else
    echo "Cannot install to ${target} - need sudo"
    exit 1
  fi
fi

# =============================================================================
# Constants
# =============================================================================
readonly JOI_VERSION="0.2.0"
readonly JOI_NAME="joi"
readonly JOI_DESC="Project Development Tool"

# Paths
readonly JOI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly JOI_LOCK_FILE="${JOI_ROOT}/.joi.lock"
readonly JOI_ENV_FILE="${JOI_ROOT}/.joi.env"
readonly JOI_ENV_EXAMPLE="${JOI_ROOT}/.joi.env.example"

# Exit codes
readonly EXIT_SUCCESS=0
readonly EXIT_ERROR=1
readonly EXIT_USAGE=2
readonly EXIT_DEP=3

# =============================================================================
# Project Detection
# =============================================================================
is_project_dir() {
  [[ -f "${JOI_ROOT}/manage.py" ]] || \
  [[ -f "${JOI_ROOT}/joi.ps1" ]] || \
  [[ -f "${JOI_ROOT}/joi" ]] || \
  [[ -f "${JOI_ROOT}/.joi.env" ]]
}

# =============================================================================
# Color support
# =============================================================================
if [[ "${NO_COLOR:-}" == "1" ]]; then
  BOLD="" CYAN="" GREEN="" YELLOW="" RED="" DIM="" RESET=""
else
  BOLD=$(tput bold 2>/dev/null || echo "")
  CYAN=$(tput setaf 6 2>/dev/null || echo "")
  GREEN=$(tput setaf 2 2>/dev/null || echo "")
  YELLOW=$(tput setaf 3 2>/dev/null || echo "")
  RED=$(tput setaf 1 2>/dev/null || echo "")
  DIM=$(tput dim 2>/dev/null || echo "")
  RESET=$(tput sgr0 2>/dev/null || echo "")
fi

# =============================================================================
# Timing utilities
# =============================================================================
_start_time=0
start_timer() { _start_time=$(date +%s%3N); }

get_elapsed() {
  local end_time=$(date +%s%3N)
  local elapsed=$((end_time - _start_time))
  
  if [[ ${elapsed} -lt 1000 ]]; then
    echo "${elapsed}ms"
  else
    local seconds=$((elapsed / 1000))
    local ms=$((elapsed % 1000))
    if [[ ${seconds} -lt 60 ]]; then
      echo "${seconds}.${ms:0:1}s"
    else
      local minutes=$((seconds / 60))
      seconds=$((seconds % 60))
      echo "${minutes}m ${seconds}s"
    fi
  fi
}

# =============================================================================
# Logging functions
# =============================================================================
log_success() { echo "${GREEN}✓${RESET} $*"; }
log_info()    { echo "${CYAN}i${RESET} $*"; }
log_warn()    { echo "${YELLOW}!${RESET} $*"; }
log_error()   { echo "${RED}✗${RESET} $*" >&2; }

log_header() {
  echo ""
  echo "${CYAN}     _       _ ${RESET}"
  echo "${CYAN}    (_) ___ (_)${RESET}"
  echo "${CYAN}    | |/ _ \\| |${RESET}"
  echo "${CYAN}    | | (_) | |${RESET}"
  echo "${CYAN}   _/ |\\___/|_|${RESET}"
  echo "${CYAN}  |__/          ${RESET}"
  echo ""
  echo "  ${DIM}v${JOI_VERSION} - Project Development Tool${RESET}"
  echo ""
}

log_step()    { echo ""; echo "${CYAN}>${RESET} ${BOLD}$1${RESET}"; }
log_item()    { echo "  ${DIM}*${RESET} $*"; }
log_dim()     { echo "${DIM}$*${RESET}"; }

# =============================================================================
# Progress indicator
# =============================================================================
show_progress() {
  local msg="$1"; shift
  
  if [[ "${JOI_QUIET}" == "1" ]]; then "$@" >/dev/null 2>&1; return $?; fi
  if [[ "${JOI_VERBOSE}" == "1" ]]; then
    echo -e "${DIM}....${RESET} ${msg}"
    "$@"
    return $?
  fi

  "$@" >/dev/null 2>&1 &
  local pid=$!
  local frames=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
  local i=0
  echo -ne "${CYAN}${frames[0]}${RESET} ${msg}"
  
  while kill -0 "$pid" 2>/dev/null; do
    echo -ne "\r${CYAN}${frames[i]}${RESET} ${msg}"
    i=$(((i + 1) % ${#frames[@]}))
    sleep 0.08
  done
  
  echo -ne "\r"
  wait "$pid"
  return $?
}

# =============================================================================
# Confirmation prompt
# =============================================================================
confirm() {
  local prompt="$1"
  local default="${2:-n}"

  if [[ "${JOI_YES}" == "1" ]]; then return 0; fi

  local yn_hint="y/n"
  [[ "${default}" == "y" ]] && yn_hint="Y/n"
  [[ "${default}" == "n" ]] && yn_hint="y/N"

  echo -ne "${YELLOW}?${RESET} ${prompt} ${DIM}(${yn_hint})${RESET} "
  read -r answer
  answer="${answer:-${default}}"
  [[ "${answer}" =~ ^[Yy]$ ]]
}

# =============================================================================
# Lock file management
# =============================================================================
acquire_lock() {
  if [[ -f "${JOI_LOCK_FILE}" ]]; then
    local pid=$(cat "${JOI_LOCK_FILE}" 2>/dev/null || echo "")
    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
      log_error "Another instance is running (PID ${pid})"
      log_dim "  If stuck, delete ${JOI_LOCK_FILE}"
      exit "${EXIT_ERROR}"
    fi
    rm -f "${JOI_LOCK_FILE}"
  fi
  echo $$ >"${JOI_LOCK_FILE}"
}

release_lock() { rm -f "${JOI_LOCK_FILE}" 2>/dev/null || true; }

cleanup() {
  local exit_code=$?
  release_lock
  if [[ ${exit_code} -eq 130 ]]; then echo ""; log_warn "Interrupted"; fi
  exit "${exit_code}"
}
trap cleanup EXIT INT TERM

# =============================================================================
# Config loading
# =============================================================================
load_config() {
  JOI_SEED_DATA="${JOI_SEED_DATA:-}"
  JOI_CREATE_ADMIN="${JOI_CREATE_ADMIN:-}"
  JOI_PORT="${JOI_PORT:-}"
  JOI_PYTHON="${JOI_PYTHON:-}"

  if [[ -f "${JOI_ENV_FILE}" ]]; then
    while IFS='=' read -r key value; do
      [[ "${key}" =~ ^#.*$ || -z "${key}" ]] && continue
      key=$(echo "${key}" | xargs)
      value=$(echo "${value}" | xargs | sed 's/^["'\'']\(.*\)["'\'']$/\1/')
      case "${key}" in
        SEED_DATA) JOI_SEED_DATA="${JOI_SEED_DATA:-${value}}" ;;
        CREATE_ADMIN) JOI_CREATE_ADMIN="${JOI_CREATE_ADMIN:-${value}}" ;;
        PORT) JOI_PORT="${JOI_PORT:-${value}}" ;;
        PYTHON) JOI_PYTHON="${JOI_PYTHON:-${value}}" ;;
      esac
    done <"${JOI_ENV_FILE}"
  fi

  JOI_SEED_DATA="${JOI_SEED_DATA:-y}"
  JOI_CREATE_ADMIN="${JOI_CREATE_ADMIN:-n}"
  JOI_PORT="${JOI_PORT:-8000}"
}

# =============================================================================
# Dependency checks
# =============================================================================
setup_uv_env() {
  if [[ "$(uname -s)" == "Linux" ]]; then
    if [[ "${JOI_ROOT}" == /mnt/* || "${JOI_ROOT}" == /media/* ]]; then
      if [[ -z "${UV_LINK_MODE:-}" ]]; then
        log_dim "  * Detected Linux on mounted drive, setting UV_LINK_MODE=copy"
        export UV_LINK_MODE=copy
      fi
    fi
  fi
}

check_uv() {
  if ! command -v uv &>/dev/null; then
    log_warn "uv is not installed"
    if confirm "Install uv now?" "y"; then
      start_timer
      if show_progress "Installing uv" curl -LsSf https://astral.sh/uv/install.sh | sh; then
        export PATH="${HOME}/.local/bin:${PATH}"
        log_success "Installed uv in $(get_elapsed)"
      else
        log_error "Failed to install uv"
        return 1
      fi
    else
      log_error "uv is required"
      log_dim "  Install: ${CYAN}https://docs.astral.sh/uv/${RESET}"
      return 1
    fi
  fi
}

check_venv() {
  local python_exec
  if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    python_exec="${JOI_ROOT}/.venv/Scripts/python.exe"
  else
    python_exec="${JOI_ROOT}/.venv/bin/python"
  fi

  if [[ -d "${JOI_ROOT}/.venv" && ! -f "${python_exec}" ]]; then
    log_warn "Existing .venv directory is invalid for this platform"
    if confirm "Recreate it?" "y"; then
      local backup=".venv_$(date +%Y%m%d_%H%M%S)"
      mv "${JOI_ROOT}/.venv" "${JOI_ROOT}/${backup}"
      log_info "Moved invalid .venv to ${backup}"
    else
      log_error "Invalid virtual environment. Setup may fail."
    fi
  fi

  if [[ ! -d "${JOI_ROOT}/.venv" ]]; then
    start_timer
    if show_progress "Creating virtual environment" uv venv; then
      log_success "Created .venv in $(get_elapsed)"
    else
      log_error "Failed to create virtual environment"
      return 1
    fi
  fi
}

get_python() {
  if [[ -n "${JOI_PYTHON}" ]]; then
    echo "${JOI_PYTHON}"
  elif [[ -f "${JOI_ROOT}/.venv/bin/python" ]]; then
    echo "${JOI_ROOT}/.venv/bin/python"
  elif [[ -f "${JOI_ROOT}/.venv/Scripts/python.exe" ]]; then
    echo "${JOI_ROOT}/.venv/Scripts/python.exe"
  else
    log_error "Python not found in .venv"
    return 1
  fi
}

# Private helper to install dependencies
_install_deps() {
  log_step "Package manager"
  check_uv || return $?
  setup_uv_env
  check_venv || return $?

  # Clean up Windows-created venv artifacts on Unix (skip on Windows)
  if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "cygwin" ]]; then
    [[ -L "${JOI_ROOT}/.venv/lib64" ]] && rm -f "${JOI_ROOT}/.venv/lib64"
  fi
  
  log_step "Dependencies"
  start_timer
  if show_progress "Running uv sync" uv sync; then
    local elapsed=$(get_elapsed)
    local python; python=$(get_python)
    local count
    if command -v uv &>/dev/null; then
      count=$(uv pip list 2>/dev/null | tail -n +3 | wc -l)
    else
      count=$("${python}" -m pip list 2>/dev/null | tail -n +3 | wc -l || echo "0")
    fi
    echo ""
    log_success "Installed ${BOLD}${count}${RESET} packages in ${DIM}${elapsed}${RESET}"
    cmd_compile
  else
    echo ""
    log_error "Installation failed"
    return "${EXIT_ERROR}"
  fi
  echo ""
}

# =============================================================================
# Commands
# =============================================================================
cmd_check() {
  log_header; echo ""
  
  if command -v uv &>/dev/null; then
    local uv_version; uv_version=$(uv --version 2>/dev/null | head -1 | awk '{print $2}')
    log_success "uv ${DIM}${uv_version}${RESET}"
  else
    log_error "uv not installed"; log_dim "  Run: ${CYAN}joi install${RESET}"
  fi

  if [[ -d "${JOI_ROOT}/.venv" ]]; then
    if local python=$(get_python); then
      local py_version; py_version=$("${python}" --version 2>&1 | awk '{print $2}')
      log_success "Python ${DIM}${py_version}${RESET}"
      local pkg_count
      if command -v uv &>/dev/null; then
        pkg_count=$(uv pip list 2>/dev/null | tail -n +3 | wc -l)
      else
        pkg_count=$("${python}" -m pip list 2>/dev/null | tail -n +3 | wc -l || echo "0")
      fi
      log_item "${pkg_count} packages installed"
    else
      log_warn "Virtual environment exists but Python not found"
    fi
  else
    log_error "Virtual environment not found"; log_dim "  Run: ${CYAN}joi install${RESET}"
  fi

  echo ""
  if [[ -f "${JOI_ROOT}/db.sqlite3" ]]; then
    local size; size=$(du -h "${JOI_ROOT}/db.sqlite3" 2>/dev/null | cut -f1)
    log_success "Database ${DIM}${size}${RESET}"
  else
    log_warn "Database not found"; log_dim "  Run: ${CYAN}joi migrate${RESET}"
  fi

  if [[ -d "${JOI_ROOT}/fixtures" ]]; then
    local count; count=$(ls "${JOI_ROOT}/fixtures"/*.json 2>/dev/null | wc -l)
    log_item "${count} fixture files"
  elif [[ -f "${JOI_ROOT}/data_seeding.sql" ]]; then
    log_item "data_seeding.sql available"
  else
    log_warn "No seed data found"
  fi

  echo ""
  if [[ -f "${JOI_ENV_FILE}" ]]; then
    log_success "Configuration loaded"; log_dim "  ${JOI_ENV_FILE}"
  else
    log_info "Using default configuration"; log_dim "  Copy ${JOI_ENV_EXAMPLE} → ${JOI_ENV_FILE} to customize"
  fi
  echo ""
}

cmd_compile() {
  local python; python="$(get_python)" || return 0
  log_dim "  * Compiling translations..."
  if "${python}" manage.py compilemessages >/dev/null 2>&1; then
    log_success "Translations compiled"
  else
    log_warn "Failed to compile translations (is gettext installed?)"
  fi
}

cmd_install() {
  log_header
  _install_deps
}

cmd_migrate() {
  log_header
  local python; python="$(get_python)" || return "${EXIT_DEP}"
  log_step "Running migrations"
  start_timer; echo ""
  
  if "${python}" manage.py makemigrations; then
    if "${python}" manage.py migrate; then
      echo ""; log_success "Migrations applied in $(get_elapsed)"
    else
      echo ""; log_error "Migration failed"; return "${EXIT_ERROR}"
    fi
  else
    echo ""; log_error "makemigrations failed"; return "${EXIT_ERROR}"
  fi
  echo ""
}

cmd_seed() {
  log_header
  local python; python="$(get_python)" || return "${EXIT_DEP}"
  local clear="${JOI_CLEAR:-0}"
  while [[ $# -gt 0 ]]; do
    case "$1" in --clear) clear=1; shift ;; *) shift ;; esac
  done

  if [[ "${clear}" -eq 1 ]]; then
    log_warn "This will delete all existing data"
    if confirm "Continue?" "n"; then
      start_timer; echo ""
      if "${python}" manage.py load_data --clear; then
        echo ""; log_success "Database cleared and reseeded in $(get_elapsed)"
      else
        echo ""; log_error "Seeding failed"; return "${EXIT_ERROR}"
      fi
    else
      log_info "Cancelled"
    fi
    echo ""; return 0
  fi

  log_step "Seeding database"
  start_timer; echo ""
  
  if [[ -d "${JOI_ROOT}/fixtures" ]]; then
    if "${python}" manage.py load_data; then
      echo ""; log_success "Database seeded in $(get_elapsed)"
    else
      echo ""; log_error "Seeding failed"; return "${EXIT_ERROR}"
    fi
  elif [[ -f "${JOI_ROOT}/data_seeding.sql" ]]; then
    log_warn "Using legacy data_seeding.sql"
    if "${python}" seed_db.py; then
      echo ""; log_success "Database seeded in $(get_elapsed)"
    else
      echo ""; log_error "Seeding failed"; return "${EXIT_ERROR}"
    fi
  else
    log_error "No seed data found"
    log_dim "  Expected: fixtures/ or data_seeding.sql"
    return "${EXIT_ERROR}"
  fi
  echo ""
}

cmd_admin() {
  log_header
  local python; python="$(get_python)" || return "${EXIT_DEP}"
  log_step "Creating admin user"; echo ""
  "${python}" manage.py createsuperuser
  echo ""; log_success "Admin user created"; echo ""
}

cmd_server() {
  log_header
  local python; python="$(get_python)" || return "${EXIT_DEP}"
  cmd_compile

  local port="${JOI_PORT}"
  while [[ $# -gt 0 ]]; do
    case "$1" in --port) port="$2"; shift 2 ;; --port=*) port="${1#*=}"; shift ;; -*) shift ;; *) port="$1"; shift ;; esac
  done

  echo ""; log_success "Starting server on ${CYAN}http://127.0.0.1:${port}${RESET}"; log_dim "  Press Ctrl+C to stop"; echo ""
  "${python}" manage.py runserver "127.0.0.1:${port}"
}

cmd_reset() {
  log_header
  local python; python="$(get_python)" || return "${EXIT_DEP}"

  log_warn "This will delete the database and all data"
  if ! confirm "Continue?" "n"; then log_info "Cancelled"; return 0; fi

  log_step "Resetting database"; echo ""; start_timer
  
  [[ -f "${JOI_ROOT}/db.sqlite3" ]] && rm -f "${JOI_ROOT}/db.sqlite3" && log_dim "  * Removed db.sqlite3"
  
  log_dim "  * Running makemigrations"; "${python}" manage.py makemigrations >/dev/null 2>&1
  log_dim "  * Running migrate"; "${python}" manage.py migrate >/dev/null 2>&1
  echo ""; log_success "Database reset in $(get_elapsed)"

  if [[ -d "${JOI_ROOT}/fixtures" ]] || [[ -f "${JOI_ROOT}/data_seeding.sql" ]]; then
    if confirm "Seed the database?" "y"; then JOI_YES=1 cmd_seed; fi
  fi
  echo ""
}

# Helper to handle user prompts based on flags/config
_handle_user_prompt() {
  local flag="$1"
  local config="$2"
  local prompt_text="$3"
  local action_func="$4"
  local step_name="$5"

  local should_run="n"
  
  # Determine if we should run
  if [[ "${flag}" == "y" ]]; then
    should_run="y"
  elif [[ "${flag}" == "n" ]]; then
    should_run="n"
  elif [[ "${config}" == "y" ]]; then
    should_run="y"
  elif [[ "${JOI_YES}" == "1" ]]; then
    # If JOI_YES is set (auto-yes) and no explicit no-flag, usually we default to config or skip.
    # Let's default to skipping if forced auto and no explicit yes.
    should_run="n"
  fi
  
  # If not decided and no explicit flag, ask user
  if [[ "${flag}" == "" ]]; then
    if confirm "${prompt_text}" "${should_run}"; then
      should_run="y"
    else
      should_run="n"
    fi
  fi

  if [[ "${should_run}" == "y" ]]; then
    log_step "${step_name}"; echo ""
    ${action_func}
    echo ""; log_success "${step_name} completed"
  fi
}

cmd_setup() {
  local flag_seed="${JOI_SEED_FLAG:-}" 
  local flag_admin="${JOI_ADMIN_FLAG:-}" 
  local flag_migrations="${JOI_SKIP_MIGRATIONS:-0}"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --seed) flag_seed="y"; shift ;;
      --no-seed) flag_seed="n"; shift ;;
      --admin) flag_admin="y"; shift ;;
      --no-admin) flag_admin="n"; shift ;;
      --skip-migrations) flag_migrations="1"; shift ;;
      *) shift ;;
    esac
  done

  log_header; echo ""
  local setup_start=$(date +%s%3N)

  # Step 1-3: Dependencies (Reusing logic)
  if ! _install_deps; then return $?; fi

  local python; python="$(get_python)" || return "${EXIT_DEP}"

  # Step 4: Migrations
  if [[ "${flag_migrations}" == "0" ]]; then
    log_step "Database"
    start_timer; echo ""
    log_dim "  * makemigrations"; "${python}" manage.py makemigrations >/dev/null 2>&1
    log_dim "  * migrate"; "${python}" manage.py migrate >/dev/null 2>&1
    echo ""; log_success "Migrations applied in $(get_elapsed)"
  fi

  # Step 5: Admin User
  _handle_user_prompt "${flag_admin}" "${JOI_CREATE_ADMIN}" "Create admin user?" "\"${python}\" manage.py createsuperuser" "Admin user"

  # Step 6: Seed Data
  if [[ "${flag_seed}" == "y" ]] || ([[ "${flag_seed}" == "" ]] && [[ "${JOI_SEED_DATA}" == "y" ]]); then
     # Simplified seed logic if yes
     log_step "Seed data"
     start_timer; echo ""
     [[ -d "${JOI_ROOT}/fixtures" ]] && "${python}" manage.py load_data >/dev/null 2>&1
     echo ""; log_success "Database seeded in $(get_elapsed)"
  elif [[ "${flag_seed}" == "" ]]; then
     # Prompt
     _handle_user_prompt "${flag_seed}" "n" "Seed database with sample data?" "\"${python}\" manage.py load_data" "Database seeded"
  fi

  # Summary
  local setup_end=$(date +%s%3N)
  local total_time=$((setup_end - setup_start))
  local total_seconds=$((total_time / 1000))
  local total_ms=$((total_time % 1000))
  echo ""
  echo -e "${GREEN}${S_SUCCESS}${RESET} ${BOLD}Setup complete!${RESET} ${DIM}${total_seconds}.${total_ms:0:1}s${RESET}"
  echo ""
  echo -e "  \033[30;42m READY \033[0m ${DIM}Your project is configured and ready to go${RESET}"
  echo ""
  log_dim "Next steps:"
  echo -e "  ${CYAN}joi server${RESET}  Start development server"
  echo -e "  ${CYAN}joi admin${RESET}   Create admin user"
  echo ""
}

cmd_help() {
  log_header
  echo "${DIM}USAGE${RESET}"
  echo "  ${CYAN}joi${RESET} ${DIM}<command> [options]${RESET}"
  echo ""
  echo "${DIM}COMMANDS${RESET}"
  echo "  ${CYAN}setup${RESET}       Full project setup (install + migrate + seed)"
  echo "  ${CYAN}install${RESET}     Install dependencies"
  echo "  ${CYAN}migrate${RESET}     Run database migrations"
  echo "  ${CYAN}seed${RESET}        Seed database with fixtures"
  echo "  ${CYAN}admin${RESET}       Create admin user"
  echo "  ${CYAN}server${RESET}      Start development server"
  echo "  ${CYAN}check${RESET}       Check environment status"
  echo "  ${CYAN}reset${RESET}       Reset database"
  echo "  ${CYAN}install-completion${RESET} Install bash tab completion"
  echo "  ${CYAN}help${RESET}        Show this help"
  echo ""
  echo "${DIM}OPTIONS${RESET}"
  echo "  -h, --help        Show help"
  echo "  -v, --version     Show version"
  echo "  -y, --yes         Skip confirmations"
  echo "  --no-color        Disable colors"
  echo "  --verbose         Detailed output"
  echo "  --quiet           Minimal output"
  echo ""
  echo "${DIM}EXAMPLES${RESET}"
  echo "  ${CYAN}joi setup${RESET}                 ${DIM}# Interactive setup${RESET}"
  echo "  ${CYAN}joi setup -y --no-seed${RESET}    ${DIM}# Auto-setup, skip seeding${RESET}"
  echo "  ${CYAN}joi seed --clear${RESET}          ${DIM}# Reset and reseed data${RESET}"
  echo "  ${CYAN}joi server --port 8080${RESET}    ${DIM}# Custom port${RESET}"
  echo "  ${CYAN}joi check${RESET}                 ${DIM}# Check environment${RESET}"
  echo ""
  echo "${DIM}CONFIGURATION${RESET}"
  echo "  Copy ${CYAN}.joi.env.example${RESET} to ${CYAN}.joi.env${RESET} to set defaults"
  echo "  See documentation for all options"
  echo ""
}

cmd_update() {
  log_header
  log_step "Checking for updates..."; echo ""
  log_dim "  Current version: ${BOLD}${JOI_VERSION}${RESET}"
  log_dim "  Latest version:  ${BOLD}${JOI_VERSION}${RESET} (check GitHub for updates)"
  echo ""; log_info "To update manually:"
  echo "    1. Download latest joi script"
  echo "    2. Replace this file"
  echo ""
}

cmd_version() { log_header; echo "  ${DIM}version${RESET} ${BOLD}${JOI_VERSION}${RESET}"; echo ""; }

# =============================================================================
# Main
# =============================================================================
main() {
  load_config

  if [[ $# -eq 0 ]]; then cmd_help; exit "${EXIT_SUCCESS}"; fi

  # Parse global flags
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help) cmd_help; exit "${EXIT_SUCCESS}" ;;
      -v|--version) cmd_version; exit "${EXIT_SUCCESS}" ;;
      -y|--yes) JOI_YES=1; shift ;;
      --no-color) NO_COLOR=1; BOLD=""; CYAN=""; GREEN=""; YELLOW=""; RED=""; DIM=""; RESET=""; shift ;;
      --verbose) JOI_VERBOSE=1; shift ;;
      --quiet) JOI_QUIET=1; shift ;;
      --debug) JOI_DEBUG=1; set -x; shift ;;
      --port) JOI_PORT="$2"; shift 2 ;;
      --port=*) JOI_PORT="${1#*=}"; shift ;;
      --clear) JOI_CLEAR=1; shift ;;
      --seed) JOI_SEED_FLAG="y"; shift ;;
      --no-seed) JOI_SEED_FLAG="n"; shift ;;
      --admin) JOI_ADMIN_FLAG="y"; shift ;;
      --no-admin) JOI_ADMIN_FLAG="n"; shift ;;
      --skip-migrations) JOI_SKIP_MIGRATIONS=1; shift ;;
      -*) log_error "Unknown option: $1"; echo "  Run 'joi --help' for usage"; exit "${EXIT_USAGE}" ;;
      *) break ;;
    esac
  done

  local command="${1:-}"; shift || true

  if [[ -z "${command}" ]]; then cmd_help; exit "${EXIT_SUCCESS}"; fi

  if ! is_project_dir; then
    case "${command}" in
      update) ;;
      *) log_error "Not a joi project directory"; echo "  Run 'joi' from a project folder"; exit "${EXIT_ERROR}" ;;
    esac
  fi

  case "${command}" in
    setup|install|migrate|seed|admin|reset) acquire_lock ;;
  esac

  case "${command}" in
    setup) cmd_setup "$@" ;;
    install) cmd_install "$@" ;;
    migrate) cmd_migrate "$@" ;;
    seed) cmd_seed "$@" ;;
    admin) cmd_admin "$@" ;;
    server) cmd_server "$@" ;;
    check) cmd_check "$@" ;;
    reset) cmd_reset "$@" ;;
    update) cmd_update "$@" ;;
    help) cmd_help ;;
    version) cmd_version ;;
    *) log_error "Unknown command: ${command}"; echo "  Run 'joi --help' for usage"; exit "${EXIT_USAGE}" ;;
  esac
}

main "$@"