#!/bin/bash
# Daily confidence score updates based on ROI performance
# Runs daily at 3:00 AM (after pattern analysis at 2:00 AM)
#
# Crontab entry:
# 0 3 * * * /path/to/tac-webbuilder/scripts/cron/update_confidence.sh
#
# Purpose: Automatically adjust pattern confidence scores based on actual
# performance data, creating a self-improving pattern system

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/confidence_update_$(date +%Y%m%d).log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Change to project root
cd "$PROJECT_ROOT"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Starting daily confidence score updates"
log "=========================================="

# Check if Python script exists
if [ ! -f "$PROJECT_ROOT/scripts/update_confidence_scores.py" ]; then
    log "ERROR: Confidence update script not found: $PROJECT_ROOT/scripts/update_confidence_scores.py"
    exit 1
fi

# Check if virtual environment exists (optional)
if [ -d "$PROJECT_ROOT/app/server/.venv" ]; then
    log "Using virtual environment: $PROJECT_ROOT/app/server/.venv"
    PYTHON_CMD="$PROJECT_ROOT/app/server/.venv/bin/python3"
else
    log "Using system Python"
    PYTHON_CMD="python3"
fi

# Run confidence update (all patterns)
log "Updating confidence scores for all patterns..."
if $PYTHON_CMD "$PROJECT_ROOT/scripts/update_confidence_scores.py" --update-all >> "$LOG_FILE" 2>&1; then
    log "✓ Confidence scores updated successfully"
else
    EXIT_CODE=$?
    log "✗ Confidence update failed with exit code $EXIT_CODE"

    # Send alert (optional - configure based on your alert system)
    # echo "Confidence update failed" | mail -s "TAC Webbuilder Alert" admin@example.com

    exit $EXIT_CODE
fi

# Generate recommendations report
log "Generating status change recommendations..."
if $PYTHON_CMD "$PROJECT_ROOT/scripts/update_confidence_scores.py" --recommendations >> "$LOG_FILE" 2>&1; then
    log "✓ Recommendations generated successfully"
else
    log "✗ Failed to generate recommendations (non-fatal)"
fi

# Cleanup old logs (keep last 30 days)
log "Cleaning up old log files..."
find "$LOG_DIR" -name "confidence_update_*.log" -type f -mtime +30 -delete
log "✓ Log cleanup complete"

log "=========================================="
log "Daily confidence score updates completed"
log "=========================================="

exit 0
