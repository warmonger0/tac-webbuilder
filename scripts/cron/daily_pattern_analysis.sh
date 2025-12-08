#!/bin/bash
# Daily Pattern Analysis - Cron Wrapper
# Runs daily at 2 AM to analyze patterns from last 24 hours
#
# Usage:
#   ./scripts/cron/daily_pattern_analysis.sh
#
# Crontab entry:
#   0 2 * * * /path/to/tac-webbuilder/scripts/cron/daily_pattern_analysis.sh

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/pattern_analysis_$(date +%Y%m%d).log"
NOTIFY_EMAIL=""  # Optional: Set email for notifications

# Create log directory
mkdir -p "$LOG_DIR"

# Navigate to project
cd "$PROJECT_ROOT"

# Activate virtual environment if using uv
if [ -d "app/server/.venv" ]; then
    export PATH="$PROJECT_ROOT/app/server/.venv/bin:$PATH"
fi

# Set database environment variables (PostgreSQL)
export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export POSTGRES_DB="${POSTGRES_DB:-tac_webbuilder}"
export POSTGRES_USER="${POSTGRES_USER:-tac_user}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-changeme}"
export DB_TYPE="${DB_TYPE:-postgresql}"

# Run analysis
echo "[$(date)] Starting daily pattern analysis..." >> "$LOG_FILE"

python scripts/analyze_daily_patterns.py \
    --hours 24 \
    --report \
    --notify \
    --verbose >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date)] Pattern analysis completed successfully" >> "$LOG_FILE"
else
    echo "[$(date)] Pattern analysis failed with exit code $EXIT_CODE" >> "$LOG_FILE"

    # Optional: Send error notification via email
    if [ -n "$NOTIFY_EMAIL" ]; then
        echo "Pattern analysis failed. Check logs: $LOG_FILE" | \
            mail -s "Pattern Analysis Failed" "$NOTIFY_EMAIL"
    fi
fi

# Cleanup old logs (keep last 30 days)
find "$LOG_DIR" -name "pattern_analysis_*.log" -mtime +30 -delete 2>/dev/null || true
find "$LOG_DIR" -name "pattern_analysis_*.md" -mtime +30 -delete 2>/dev/null || true

exit $EXIT_CODE
