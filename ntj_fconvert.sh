#!/bin/bash
echo "Launcher Python Script $1"

# ----- Configurazione -----
PYTHON="python3"

# ----- Ricava nome script python con PATH completo -----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}" .sh).py"
SCRIPT="${SCRIPT_DIR}/${SCRIPT_NAME}"

# ----- Esecuzione -----
echo "Sintassi fileini.ini"
call "${PYTHON}" "${SCRIPT}" "$@"