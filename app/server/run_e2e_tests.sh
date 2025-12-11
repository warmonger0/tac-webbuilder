#!/bin/bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=tac_webbuilder
export POSTGRES_USER=tac_user
export POSTGRES_PASSWORD=changeme
export DB_TYPE=postgresql

.venv/bin/pytest tests/e2e/test_workflow_journey.py -v --tb=short 2>&1
