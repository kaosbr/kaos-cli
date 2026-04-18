#!/usr/bin/env bash
set -euo pipefail

APP_NAME="kaos-cli"
BIN_PATH="${HOME}/.local/bin/${APP_NAME}"
DATA_DIR="${HOME}/.local/share/${APP_NAME}"
CONFIG_DIR="${HOME}/.config/${APP_NAME}"
MANAGED_BLOCK_START="# >>> kaos-cli >>>"
MANAGED_BLOCK_END="# <<< kaos-cli <<<"

remove_path_block() {
  local rc_file="$1"
  [ -f "$rc_file" ] || return 0
  python3 - "$rc_file" "$MANAGED_BLOCK_START" "$MANAGED_BLOCK_END" <<'PY'
import sys
from pathlib import Path
path = Path(sys.argv[1])
start = sys.argv[2]
end = sys.argv[3]
text = path.read_text(encoding='utf-8', errors='replace')
lines = text.splitlines()
out = []
skip = False
for line in lines:
    if line.strip() == start:
        skip = True
        continue
    if skip and line.strip() == end:
        skip = False
        continue
    if not skip:
        out.append(line)
new_text = "\n".join(out).rstrip() + ("\n" if out else "")
path.write_text(new_text, encoding='utf-8')
PY
}

rm -f "$BIN_PATH"
rm -rf "$DATA_DIR"
remove_path_block "$HOME/.bashrc"
remove_path_block "$HOME/.zshrc"

cat <<EOF
[OK] Removido:
  - $BIN_PATH
  - $DATA_DIR

Configuracao preservada em:
  - $CONFIG_DIR

Se quiser apagar tudo manualmente:
  rm -rf "$CONFIG_DIR"
EOF
