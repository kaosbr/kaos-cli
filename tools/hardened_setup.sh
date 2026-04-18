#!/usr/bin/env bash
# KAOS CLI - Hardened Setup Template
# This script applies security hardening and sets up a secure workspace for KAOS CLI.

set -euo pipefail
IFS=$'\n\t'

# Color definitions for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[x]${NC} $1"; exit 1; }

# 1. Privilege Check
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root (or with sudo)."
fi

# 2. Trap for temporary file cleanup
TMP_DIR=$(mktemp -d)
trap 'log "Cleaning up temporary files..."; rm -rf "$TMP_DIR"' EXIT

log "Starting KAOS Hardened Setup..."

# 3. Dependency Verification
log "Verifying critical dependencies..."
DEPS=("curl" "jq" "ufw" "fail2ban" "apparmor")
MISSING_DEPS=()
for tool in "${DEPS[@]}"; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        MISSING_DEPS+=("$tool")
    fi
done

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    warn "Missing dependencies: ${MISSING_DEPS[*]}. Installing..."
    apt-get update -yqq && apt-get install -yqq "${MISSING_DEPS[@]}" || error "Failed to install dependencies."
fi

# 4. Directory Permissions Setup
log "Setting up secure KAOS data directories..."
KAOS_DIR="/opt/kaos-cli"
mkdir -p "$KAOS_DIR"
chown -R root:root "$KAOS_DIR"
chmod 750 "$KAOS_DIR"

# 5. Basic Firewall Configuration
log "Configuring basic firewall rules (UFW/AppArmor)..."
if command -v ufw >/dev/null 2>&1; then
    ufw default deny incoming >/dev/null
    ufw default allow outgoing >/dev/null
    ufw allow ssh >/dev/null
    ufw --force enable >/dev/null
    log "UFW configured and enabled."
else
    warn "UFW not found, skipping firewall setup."
fi

# 6. Secure Environment Variables
log "Applying secure environment variable profile..."
SECURE_PROFILE="/etc/profile.d/kaos_secure.sh"
cat << 'EOF' > "$SECURE_PROFILE"
# KAOS Secure Profile
export TMOUT=900
export HISTCONTROL=ignoreboth
export HISTSIZE=1000
export HISTFILESIZE=2000
readonly TMOUT HISTCONTROL HISTSIZE HISTFILESIZE
EOF
chmod 644 "$SECURE_PROFILE"

log "Hardened setup complete! System is ready for KAOS CLI operations."