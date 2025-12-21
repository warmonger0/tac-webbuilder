#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR/app/client"

# Load port config
if [ -f "$PROJECT_DIR/.ports.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.ports.env" | xargs)
fi

FRONTEND_PORT=${FRONTEND_PORT:-5173}

echo "🚀 Starting tac-webbuilder frontend on http://localhost:${FRONTEND_PORT}"

# Install deps if needed
[ ! -d "node_modules" ] && npm install

bun run dev
