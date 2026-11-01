#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

VENV="$ROOT/venv"

if [[ ! -d "$VENV" ]]; then
  echo "Virtual environment not found at $VENV"
  echo "Create it with: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# shellcheck source=/dev/null
source "$VENV/bin/activate"

exec uvicorn app.main:app --reload
