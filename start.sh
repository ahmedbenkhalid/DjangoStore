#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# ── Color codes ──
RESET='\033[0m'
BOLD='\033[1m'
RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
CYAN='\033[36m'
BCYAN='\033[1;36m'
MAGENTA='\033[1;35m'
WHITE='\033[1;37m'

# ── Helper functions ──
print_header() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${CYAN}║${RESET}                                                          ${CYAN}║${RESET}"
    echo -e "${CYAN}║${RESET}   ${MAGENTA}★  Django E-Commerce Platform  ★${RESET}                       ${CYAN}║${RESET}"
    echo -e "${CYAN}║${RESET}      Automated Setup & Configuration                      ${CYAN}║${RESET}"
    echo -e "${CYAN}║${RESET}                                                          ${CYAN}║${RESET}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${RESET}"
    echo ""
}

print_step() {
    echo -e "${BCYAN}──────────────────────────────────────────────────────────────${RESET}"
    echo -e "  ${YELLOW}[$1/$2]${RESET}  ${WHITE}$3${RESET}"
    echo -e "${BCYAN}──────────────────────────────────────────────────────────────${RESET}"
}

print_success() {
    echo -e "  ${GREEN}✔${RESET}  $1"
}

print_info() {
    echo -e "  ${CYAN}ℹ${RESET}  $1"
}

print_warning() {
    echo -e "  ${YELLOW}⚠${RESET}  $1"
}

print_error() {
    echo -e "  ${RED}✘${RESET}  $1"
}

print_server_start() {
    echo ""
    echo -e "${MAGENTA}┌──────────────────────────────────────────────────────────┐${RESET}"
    echo -e "${MAGENTA}│          🚀  Launching Development Server...            │${RESET}"
    echo -e "${MAGENTA}│          Press Ctrl+C to stop the server                │${RESET}"
    echo -e "${MAGENTA}└──────────────────────────────────────────────────────────┘${RESET}"
    echo ""
}

# ═══════════════════════════════════════════════════════
#  Main script
# ═══════════════════════════════════════════════════════

print_header

# ── Step 1: uv package manager ──
print_step 1 7 "Checking for uv package manager"
if ! command -v uv &> /dev/null; then
    print_warning "uv is not installed. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    print_success "uv installed successfully"
else
    print_success "uv is already installed"
fi

# ── Step 2: Virtual environment ──
echo ""
print_step 2 7 "Checking virtual environment"
if [ ! -d ".venv" ]; then
    print_info "Creating virtual environment (.venv)..."
    uv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# ── Step 3: Dependencies ──
echo ""
print_step 3 7 "Installing dependencies"
print_info "Running uv sync..."
uv sync
print_success "Dependencies installed"

PYTHON=".venv/bin/python"

# ── Step 4: Database migrations ──
echo ""
print_step 4 7 "Applying database migrations"
print_info "Running makemigrations..."
$PYTHON manage.py makemigrations
print_info "Running migrate..."
$PYTHON manage.py migrate
print_success "Database migrations applied"

# ── Step 5: Admin user ──
echo ""
print_step 5 7 "Admin user creation"
echo ""
read -rp "$(echo -e "  ${YELLOW}?${RESET}  Do you want to create an admin user? ${WHITE}(y/n)${RESET}: ")" CREATE_ADMIN
if [ "$CREATE_ADMIN" = "y" ] || [ "$CREATE_ADMIN" = "Y" ]; then
    echo ""
    $PYTHON manage.py createsuperuser
    print_success "Admin user created"
else
    print_info "Skipped admin user creation"
fi

# ── Step 6: Fake data seeding ──
echo ""
print_step 6 7 "Fake data seeding"
echo ""
read -rp "$(echo -e "  ${YELLOW}?${RESET}  Do you want to seed fake data into the database? ${WHITE}(y/n)${RESET}: ")" SEED_DATA
if [ "$SEED_DATA" = "y" ] || [ "$SEED_DATA" = "Y" ]; then
    if [ -f "data_seeding.sql" ]; then
        print_info "Loading data_seeding.sql..."
        if $PYTHON seed_db.py; then
            print_success "Fake data loaded successfully"
        else
            print_error "Seeding failed — check output above"
        fi
    else
        print_error "data_seeding.sql not found"
    fi
else
    print_info "Skipped data seeding"
fi

# ── Step 7: Start server ──
echo ""
print_step 7 7 "Starting Django development server"
print_server_start
$PYTHON manage.py runserver
