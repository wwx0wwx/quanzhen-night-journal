#!/usr/bin/env bash
set -euo pipefail

# Load environment variables from .env in the engine root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ -f "${ENGINE_ROOT}/.env" ]; then
    export $(grep -v '^#' "${ENGINE_ROOT}/.env" | xargs)
fi

# Set default values if not in .env
export ENGINE_ROOT="${ENGINE_ROOT:-${ENGINE_ROOT}}"
export BLOG_OUTPUT_DIR="${BLOG_OUTPUT_DIR:-/var/www/shetop.ru}"
export LOG_DIR="${LOG_DIR:-${ENGINE_ROOT}/logs}"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Run the generator
python3 "${ENGINE_ROOT}/scripts/generate_night_journal.py" >> "${LOG_DIR}/night-journal.log" 2>&1
