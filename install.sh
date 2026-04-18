#!/usr/bin/env bash
set -euo pipefail

APP_NAME="kaos-cli"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
CONFIG_DIR="${HOME}/.config/${APP_NAME}"
DATA_DIR="${HOME}/.local/share/${APP_NAME}"
BIN_PATH="${BIN_DIR}/${APP_NAME}"
PYTHON_BIN="${PYTHON:-python3}"
MANAGED_BLOCK_START="# >>> kaos-cli >>>"
MANAGED_BLOCK_END="# <<< kaos-cli <<<"

mkdir -p "$BIN_DIR" "$CONFIG_DIR" "$DATA_DIR"
install -m 0755 "$SCRIPT_DIR/kaos-cli" "$BIN_PATH"
install -m 0755 "$SCRIPT_DIR/kaos-cli" "$DATA_DIR/kaos-cli"
install -m 0644 "$SCRIPT_DIR/README.md" "$DATA_DIR/README.md"

if [ ! -f "$CONFIG_DIR/config.env" ]; then
  install -m 0600 "$SCRIPT_DIR/config.env.example" "$CONFIG_DIR/config.env"
fi

"$PYTHON_BIN" -m py_compile "$BIN_PATH"

add_path_block() {
  local rc_file="$1"
  [ -f "$rc_file" ] || touch "$rc_file"
  if ! grep -Fq "$MANAGED_BLOCK_START" "$rc_file"; then
    {
      echo
      echo "$MANAGED_BLOCK_START"
      echo 'export PATH="$HOME/.local/bin:$PATH"'
      echo "$MANAGED_BLOCK_END"
    } >> "$rc_file"
  fi
}

add_path_block "$HOME/.bashrc"
add_path_block "$HOME/.zshrc"

cat <<EOF
[OK] Instalado em:
  - Binario: $BIN_PATH
  - Config : $CONFIG_DIR/config.env
  - Dados  : $DATA_DIR

Para usar agora nesta sessao:
  export PATH="$HOME/.local/bin:$PATH"
  hash -r

Exemplos:
  kaos-cli analise este projeto
  kaos-cli --models
  kaos-cli --doctor
  kaos-cli --project . revise a seguranca
  cat prompt.txt | kaos-cli

Se ainda nao tiver modelo local, rode por exemplo:
  ollama pull qwen2.5-coder
EOF
