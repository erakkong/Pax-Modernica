#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ ! -d ".venv" ]; then
    echo "Erstelle Python Virtual Environment..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

export PYTHONPATH="$DIR"
echo "=========================================================="
echo "  PAX MODERNICA - HISTORISCHE GRAND-STRATEGY-SIMULATION   "
echo "  Server-Authoritative Engine (1700–1930 / Jahr 0 System) "
echo "=========================================================="
echo "Startet Server auf http://localhost:8000 ..."
exec .venv/bin/python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
