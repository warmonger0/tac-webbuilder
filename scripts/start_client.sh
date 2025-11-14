#!/bin/bash
cd "$(dirname "$0")/../app/client"

echo "🚀 Starting tac-webbuilder frontend on http://localhost:5174"

# Install deps if needed
[ ! -d "node_modules" ] && npm install

npm run dev
