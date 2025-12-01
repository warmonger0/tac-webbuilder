#!/bin/bash
# Diagnostic script for frontend issues

echo "🔍 TAC WebBuilder Frontend Diagnostics"
echo "======================================"
echo ""

echo "1. Backend API Status"
echo "---------------------"
echo "Active workflows:"
curl -s "http://localhost:8000/api/v1/workflows" | jq 'length'
echo ""
echo "Workflow history (latest 3):"
curl -s "http://localhost:8000/api/v1/workflow-history?limit=3" | jq '.workflows[0:3] | .[] | {id, issue_number, status, updated_at}'
echo ""

echo "2. ADW Monitor Status"
echo "--------------------"
curl -s "http://localhost:8000/api/v1/adw-monitor" | jq '{active_count: .active_workflows | length, queued_count: .queued_workflows | length, active: .active_workflows, queued: .queued_workflows}'
echo ""

echo "3. Frontend Proxy"
echo "-----------------"
echo "Can frontend reach backend?"
curl -s "http://localhost:5173/api/v1/system-status" | jq '{status, uptime_seconds, services_running}'
echo ""

echo "4. WebSocket Endpoints"
echo "---------------------"
echo "Registered WebSocket routes:"
curl -s "http://localhost:8000/api/v1/routes" | jq '.routes[] | select(.path | contains("/ws"))'
echo ""

echo "5. Background Sync Status"
echo "------------------------"
echo "Checking recent sync activity (check server logs for:"
echo "  [WORKFLOW_SERVICE] Background sync"
echo "  [WORKFLOW_SERVICE] Initial sync complete"
echo ""

echo "6. Database Status"
echo "-----------------"
sqlite3 app/server/db/workflow_history.db "SELECT status, COUNT(*) FROM workflow_history GROUP BY status;"
echo ""

echo "7. Frontend Build"
echo "----------------"
ls -lh app/client/dist/assets/*.js 2>/dev/null | tail -2
echo ""

echo "✅ Diagnostic complete!"
echo ""
echo "Common Issues & Fixes:"
echo "  - Stale browser cache: Hard refresh (Cmd+Shift+R)"
echo "  - WebSocket not connecting: Check browser console"
echo "  - Wrong data: Check which API endpoint component uses"
echo "  - Animation issues: Check CSS/Tailwind classes"
