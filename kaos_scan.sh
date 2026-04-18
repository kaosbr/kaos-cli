#!/usr/bin/env bash
# KAOS Project Scanner - Context Gathering & Security Audit Tool
# Usage: ./kaos_scan.sh > context.txt

set -euo pipefail

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() {
    # Output logs to stderr so they don't pollute the context file
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Ensure we're running in a directory
if [[ ! -d "$PWD" ]]; then
    error "Current working directory is invalid."
    exit 1
fi

log "Starting KAOS Project Scanner in $PWD"

echo "====================================================="
echo "=== KAOS-CLI PROJECT CONTEXT & SECURITY SCAN      ==="
echo "====================================================="
echo "Date: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "Path: $PWD"
echo -e "=====================================================\n"

echo "=== 1. DIRECTORY STRUCTURE (max depth 3) ==="
log "Scanning directory structure..."
find . -maxdepth 3 -not -path '*/.*' -not -path '*/node_modules*' -not -path '*/__pycache__*' -not -path '*/venv*' | sort || true

echo -e "\n=== 2. CRITICAL FILE PERMISSIONS ==="
log "Checking for globally writable files..."
# Find files that are 777 or world-writable, excluding .git
find . -type f -not -path '*/.*' -perm -002 -exec ls -la {} + 2>/dev/null || echo "No overly permissive files found."

echo -e "\n=== 3. HARDCODED SECRETS (Basic Heuristics) ==="
log "Scanning for hardcoded secrets..."
# Search for secrets, excluding common false positives
grep -rnEi "(password|passwd|api_key|apikey|token|secret|admin_pass)[_a-z0-9]*\s*(=|:|\s+)\s*['\"][^'\"]{6,}['\"]" . \
    --exclude="kaos_scan.sh" --exclude-dir=".git" --exclude-dir="node_modules" --exclude-dir="venv" 2>/dev/null || echo "No immediate hardcoded secrets found."

echo -e "\n=== 4. CONFIGURATION & CRITICAL FILES ==="
log "Reading configuration files..."
CONFIG_FILES=(
    "Dockerfile" "docker-compose.yml" "docker-compose.yaml"
    "requirements.txt" "Pipfile" "pyproject.toml"
    "package.json" "yarn.lock" "tsconfig.json"
    "Makefile" "pom.xml" "build.gradle" "cargo.toml"
    "go.mod" "go.sum"
)

for f in "${CONFIG_FILES[@]}"; do
    # Check if file exists in the root directory
    if [[ -f "$f" ]]; then
        echo -e "\n--- FILE: $f ---"
        cat "$f"
    fi
done

# Check for any .sh scripts
for f in *.sh; do
    if [[ -f "$f" && "$f" != "kaos_scan.sh" ]]; then
        echo -e "\n--- FILE: $f ---"
        cat "$f"
    fi
done

log "Scan complete."
echo -e "\n=== END OF REPORT ==="
