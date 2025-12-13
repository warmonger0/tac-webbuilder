#!/bin/bash
# Shell wrapper for generate_prompt.py
# Automatically sets PostgreSQL environment variables and executes the generator

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

export POSTGRES_HOST=localhost POSTGRES_PORT=5432
export POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user
export POSTGRES_PASSWORD=changeme DB_TYPE=postgresql

app/server/.venv/bin/python3 scripts/generate_prompt.py "$@"
