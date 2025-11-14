#!/bin/bash
# ZTE Hopper - Automated Pipeline Queue System
# Processes GitHub issues sequentially through ZTE workflows with validation
# Usage: ./scripts/zte_hopper.sh [--work|--status|--stop|--kill]

set -euo pipefail

#############################################################################
# Configuration
#############################################################################

HOPPER_DIR="zte-hopper"
QUEUE_DIR="$HOPPER_DIR/queue"
COMPLETED_DIR="$HOPPER_DIR/completed"
FAILED_DIR="$HOPPER_DIR/failed"
LOGS_DIR="$HOPPER_DIR/logs"
STATE_FILE="$HOPPER_DIR/.hopper_state"
PID_FILE="$HOPPER_DIR/.hopper.pid"
STOP_FILE="$HOPPER_DIR/.stop"
LOG_FILE=""

# Timeouts and intervals
POLL_INTERVAL=30  # seconds between status checks
TIMEOUT_SECONDS=$((2 * 60 * 60))  # 2 hours
MAX_POLLS=$((TIMEOUT_SECONDS / POLL_INTERVAL))

#############################################################################
# Logging Functions
#############################################################################

init_logging() {
    local timestamp=$(date +%Y%m%d-%H%M%S)
    LOG_FILE="$LOGS_DIR/hopper-$timestamp.log"

    # Create log file
    touch "$LOG_FILE"

    log "INFO" "ZTE Hopper starting - Log file: $LOG_FILE"

    # Rotate logs - keep last 10
    local log_count=$(find "$LOGS_DIR" -name "hopper-*.log" -type f | wc -l | tr -d ' ')
    if [ "$log_count" -gt 10 ]; then
        find "$LOGS_DIR" -name "hopper-*.log" -type f | sort | head -n -10 | xargs rm -f
        log "INFO" "Rotated old log files, kept last 10"
    fi
}

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_line="[$timestamp] [$level] $message"

    # Write to log file if initialized
    if [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
        echo "$log_line" >> "$LOG_FILE"
    fi

    # Also output to stderr for real-time monitoring (not stdout to avoid contaminating command substitution)
    echo "$log_line" >&2
}

#############################################################################
# State Management Functions
#############################################################################

init_state() {
    log "INFO" "Initializing state"
    cat > "$STATE_FILE" << EOF
STATE="IDLE"
ISSUE_NUMBER=""
ISSUE_FILE=""
TIMESTAMP="$(date +%s)"
EOF
}

save_state() {
    local state="$1"
    local issue_number="${2:-}"
    local issue_file="${3:-}"
    local timestamp=$(date +%s)

    log "DEBUG" "Saving state: $state, issue: $issue_number, file: $issue_file"

    cat > "$STATE_FILE" << EOF
STATE="$state"
ISSUE_NUMBER="$issue_number"
ISSUE_FILE="$issue_file"
TIMESTAMP="$timestamp"
EOF
}

load_state() {
    if [ ! -f "$STATE_FILE" ]; then
        log "WARN" "State file not found, initializing"
        init_state
    fi

    # Source the state file to load variables
    # shellcheck disable=SC1090
    source "$STATE_FILE"

    log "DEBUG" "Loaded state: STATE=$STATE, ISSUE_NUMBER=$ISSUE_NUMBER"
}

#############################################################################
# Process Management Functions
#############################################################################

check_single_instance() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log "ERROR" "Another hopper instance is already running (PID: $pid)"
            echo "Error: ZTE Hopper is already running (PID: $pid)"
            echo "Use './scripts/zte_hopper.sh --kill' to stop it"
            exit 1
        else
            log "WARN" "Stale PID file found, removing"
            rm -f "$PID_FILE"
        fi
    fi
}

write_pid_file() {
    echo $$ > "$PID_FILE"
    log "INFO" "PID file created: $PID_FILE (PID: $$)"
}

remove_pid_file() {
    if [ -f "$PID_FILE" ]; then
        rm -f "$PID_FILE"
        log "INFO" "PID file removed"
    fi
}

cleanup() {
    log "INFO" "Cleanup called, shutting down gracefully"
    save_state "STOPPED" "${ISSUE_NUMBER:-}" "${ISSUE_FILE:-}"
    remove_pid_file
    log "INFO" "ZTE Hopper stopped"
    exit 0
}

check_stop_signal() {
    if [ -f "$STOP_FILE" ]; then
        log "INFO" "Stop signal detected"
        return 0
    fi
    return 1
}

#############################################################################
# Queue Processing Functions
#############################################################################

get_next_issue() {
    # Get oldest file in queue (FIFO by creation time)
    # Works on both Linux (with -printf) and macOS (falls back to stat)
    local oldest_file=""

    if find "$QUEUE_DIR" -type f -name "*.md" -printf '%T@ %p\n' 2>/dev/null | head -1 | grep -q .; then
        # GNU find (Linux)
        oldest_file=$(find "$QUEUE_DIR" -type f -name "*.md" -printf '%T@ %p\n' 2>/dev/null | sort -n | head -1 | cut -d' ' -f2-)
    else
        # BSD find (macOS) - use stat instead
        oldest_file=$(find "$QUEUE_DIR" -type f -name "*.md" -exec stat -f '%m %N' {} \; 2>/dev/null | sort -n | head -1 | cut -d' ' -f2-)
    fi

    if [ -z "$oldest_file" ]; then
        log "DEBUG" "No files in queue"
        return 1
    fi

    echo "$oldest_file"
    return 0
}

extract_title() {
    local file="$1"

    # Extract first # heading
    local title=$(grep -m 1 "^# " "$file" | sed 's/^# //')

    if [ -z "$title" ]; then
        log "ERROR" "Could not extract title from $file"
        return 1
    fi

    echo "$title"
    return 0
}

move_to_completed() {
    local file="$1"
    local basename=$(basename "$file")
    local dest="$COMPLETED_DIR/$basename"

    log "INFO" "Moving to completed: $basename"
    mv "$file" "$dest"
}

move_to_failed() {
    local file="$1"
    local basename=$(basename "$file")
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local dest="$FAILED_DIR/${timestamp}-${basename}"

    log "ERROR" "Moving to failed: $basename"
    mv "$file" "$dest"
}

count_queue_files() {
    find "$QUEUE_DIR" -type f -name "*.md" 2>/dev/null | wc -l | tr -d ' '
}

#############################################################################
# Git Operations
#############################################################################

preflight_checks() {
    log "INFO" "Running pre-flight checks"

    # Check git worktree - allow frontend changes, block backend/infrastructure changes
    local git_status=$(git status --porcelain)
    local modified=$(echo "$git_status" | grep -E "^(M|A|D|R|C)" || true)

    if [ -n "$modified" ]; then
        log "INFO" "Found uncommitted changes, checking if they're frontend-only"

        # Define frontend patterns (can be modified in parallel with hopper)
        local frontend_patterns=(
            "app/client/"
            "app/webbuilder/"
            ".*/client/"
            ".*/frontend/"
            ".*\.(tsx|jsx|css|scss|html)$"
            ".*vite\.config\.*"
            ".*tailwind\.config\.*"
            ".*postcss\.config\.*"
        )

        # Define backend/critical patterns (must be committed before hopper runs)
        local backend_patterns=(
            "app/server/"
            ".*/server/"
            ".*/backend/"
            ".*\.py$"
            ".*pyproject\.toml$"
            ".*requirements.*\.txt$"
            ".*\.sh$"
            "adws/"
            "scripts/"
            "zte-hopper/"
        )

        # Check each modified file
        local backend_changes=""
        while IFS= read -r line; do
            # Extract filename (skip status prefix)
            local file=$(echo "$line" | awk '{print $2}')

            # Check if it matches frontend patterns
            local is_frontend=false
            for pattern in "${frontend_patterns[@]}"; do
                if echo "$file" | grep -qE "$pattern"; then
                    is_frontend=true
                    break
                fi
            done

            # Check if it matches backend patterns
            local is_backend=false
            for pattern in "${backend_patterns[@]}"; do
                if echo "$file" | grep -qE "$pattern"; then
                    is_backend=true
                    break
                fi
            done

            # If it's backend but not frontend, this is a blocking change
            if [ "$is_backend" = true ] && [ "$is_frontend" = false ]; then
                backend_changes="${backend_changes}${line}\n"
            fi
        done <<< "$modified"

        if [ -n "$backend_changes" ]; then
            log "ERROR" "Git worktree has uncommitted backend/infrastructure changes:"
            echo -e "$backend_changes" | while read -r line; do
                log "ERROR" "  $line"
            done
            log "ERROR" "Commit or stash backend changes before running hopper"
            log "INFO" "Frontend changes are allowed and will not block hopper"
            return 1
        else
            log "INFO" "✓ Only frontend changes detected - safe to proceed"
        fi
    else
        log "INFO" "✓ Git worktree is clean (no uncommitted changes to tracked files)"
    fi

    # Pull latest from origin/main
    log "INFO" "Pulling latest from origin/main"
    if ! git pull origin main; then
        log "ERROR" "Failed to pull from origin/main"
        return 1
    fi

    log "INFO" "✓ Pre-flight checks passed"
    return 0
}

check_git_clean() {
    local git_status=$(git status --porcelain)

    # Filter out expected directories (trees/, agents/, logs/)
    local unexpected=$(echo "$git_status" | grep -v "^?? trees/" | grep -v "^?? agents/" | grep -v "^?? logs/" | grep -v "^?? zte-hopper/logs/" | grep -v "^?? zte-hopper/.hopper")

    if [ -n "$unexpected" ]; then
        log "ERROR" "Unexpected changes in git worktree:"
        log "ERROR" "$unexpected"
        return 1
    fi

    return 0
}

#############################################################################
# GitHub Issue Operations
#############################################################################

create_issue() {
    local title="$1"
    local file="$2"

    log "INFO" "Creating GitHub issue: $title"

    # Use the gi script to create issue
    local output=$(./scripts/gi --title "$title" --body-file "$file" 2>&1)
    local exit_code=$?

    if [ $exit_code -ne 0 ]; then
        log "ERROR" "Failed to create GitHub issue"
        log "ERROR" "$output"
        return 1
    fi

    # Extract issue number from output
    local issue_number=$(echo "$output" | grep -oE '#[0-9]+' | head -1 | tr -d '#')

    if [ -z "$issue_number" ]; then
        log "ERROR" "Could not extract issue number from output"
        log "ERROR" "$output"
        return 1
    fi

    log "INFO" "✓ Issue created: #$issue_number"
    echo "$issue_number"
    return 0
}

check_issue_status() {
    local issue_number="$1"

    # Get issue state using gh CLI
    local state=$(gh issue view "$issue_number" --json state --jq '.state' 2>/dev/null)

    echo "$state"
}

validate_completion() {
    local issue_number="$1"

    log "INFO" "Validating issue #$issue_number completion"

    # Check 1: Issue is closed
    local state=$(check_issue_status "$issue_number")
    if [ "$state" != "CLOSED" ]; then
        log "ERROR" "Issue is not closed (state: $state)"
        return 1
    fi
    log "INFO" "✓ Issue is closed"

    # Check 2: Has ZTE completion marker
    local comments=$(gh issue view "$issue_number" --json comments --jq '.comments[].body' 2>/dev/null)

    if ! echo "$comments" | grep -q "Zero Touch Execution Complete\|Code has been shipped"; then
        log "ERROR" "Missing ZTE completion marker"
        log "ERROR" "Expected 'Zero Touch Execution Complete' or 'Code has been shipped'"
        return 1
    fi
    log "INFO" "✓ Has ZTE completion marker"

    # Check 3: All SDLC phases present
    local missing_phases=""
    for phase in plan build test review document ship; do
        if ! echo "$comments" | grep -qi "$phase"; then
            missing_phases="$missing_phases $phase"
        fi
    done

    if [ -n "$missing_phases" ]; then
        log "ERROR" "Missing SDLC phases:$missing_phases"
        return 1
    fi
    log "INFO" "✓ All SDLC phases present (plan, build, test, review, document, ship)"

    # Check 4: Git worktree is clean
    if ! check_git_clean; then
        log "ERROR" "Git worktree is not clean after issue completion"
        return 1
    fi
    log "INFO" "✓ Git worktree is clean"

    log "INFO" "✓ All validation checks passed for issue #$issue_number"
    return 0
}

wait_for_completion() {
    local issue_number="$1"
    local poll_count=0
    local start_time=$(date +%s)

    log "INFO" "Waiting for issue #$issue_number to complete (max $TIMEOUT_SECONDS seconds)"
    log "INFO" "Polling every $POLL_INTERVAL seconds..."

    while [ $poll_count -lt $MAX_POLLS ]; do
        # Check for stop signal
        if check_stop_signal; then
            log "INFO" "Stop signal detected, will stop after current issue completes"
            # Don't return error, let the issue finish
        fi

        # Check issue status
        local state=$(check_issue_status "$issue_number")

        if [ "$state" = "CLOSED" ]; then
            local elapsed=$(($(date +%s) - start_time))
            log "INFO" "Issue #$issue_number closed after $elapsed seconds"
            return 0
        fi

        # Log progress every 5 minutes
        if [ $((poll_count % 10)) -eq 0 ] && [ $poll_count -gt 0 ]; then
            local elapsed=$(($(date +%s) - start_time))
            log "INFO" "Still waiting... ($elapsed seconds elapsed, issue state: $state)"
        fi

        sleep $POLL_INTERVAL
        poll_count=$((poll_count + 1))
    done

    # Timeout reached
    log "ERROR" "Timeout waiting for issue #$issue_number to complete"
    return 1
}

#############################################################################
# Main Processing Loop
#############################################################################

process_queue() {
    log "INFO" "Starting queue processing"

    # Remove stale stop signal file
    if [ -f "$STOP_FILE" ]; then
        log "INFO" "Removing stale stop signal file"
        rm -f "$STOP_FILE"
    fi

    while true; do
        # Check for stop signal at start of loop
        if check_stop_signal; then
            log "INFO" "Stop signal detected, exiting"
            save_state "STOPPED" "" ""
            return 0
        fi

        # Get next issue from queue
        local issue_file
        if ! issue_file=$(get_next_issue); then
            log "INFO" "Queue is empty, processing complete"
            save_state "IDLE" "" ""
            return 0
        fi

        log "INFO" "Processing: $(basename "$issue_file")"

        # Extract title
        local title
        if ! title=$(extract_title "$issue_file"); then
            log "ERROR" "Failed to extract title, skipping file"
            move_to_failed "$issue_file"
            save_state "FAILED" "" "$issue_file"
            return 1
        fi

        log "INFO" "Issue title: $title"

        # Run pre-flight checks
        if ! preflight_checks; then
            log "ERROR" "Pre-flight checks failed"
            move_to_failed "$issue_file"
            save_state "FAILED" "" "$issue_file"
            return 1
        fi

        # Create GitHub issue
        local issue_number
        if ! issue_number=$(create_issue "$title" "$issue_file"); then
            log "ERROR" "Failed to create issue"
            move_to_failed "$issue_file"
            save_state "FAILED" "" "$issue_file"
            return 1
        fi

        # Update state to processing
        save_state "RUNNING" "$issue_number" "$issue_file"

        # Wait for issue to complete
        if ! wait_for_completion "$issue_number"; then
            log "ERROR" "Issue #$issue_number did not complete in time"
            move_to_failed "$issue_file"
            save_state "FAILED" "$issue_number" "$issue_file"
            return 1
        fi

        # Validate completion
        if ! validate_completion "$issue_number"; then
            log "ERROR" "Issue #$issue_number failed validation"
            move_to_failed "$issue_file"
            save_state "FAILED" "$issue_number" "$issue_file"
            return 1
        fi

        # Success - move to completed
        move_to_completed "$issue_file"
        log "INFO" "✅ Issue #$issue_number completed successfully"

        # Continue to next issue
        save_state "RUNNING" "" ""
    done
}

#############################################################################
# Command Implementations
#############################################################################

cmd_work() {
    log "INFO" "Command: --work"

    # Check single instance
    check_single_instance

    # Write PID file
    write_pid_file

    # Set up signal handlers
    trap cleanup EXIT INT TERM

    # Initialize state
    init_state

    # Process queue
    if process_queue; then
        log "INFO" "Queue processing completed successfully"
        exit 0
    else
        log "ERROR" "Queue processing failed"
        exit 1
    fi
}

cmd_status() {
    echo "ZTE Hopper Status"
    echo "================="
    echo ""

    # Check if running
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "Status: RUNNING (PID: $pid)"
        else
            echo "Status: STOPPED (stale PID file)"
        fi
    else
        echo "Status: STOPPED"
    fi

    echo ""

    # Load and display state
    if [ -f "$STATE_FILE" ]; then
        load_state
        echo "State: $STATE"
        if [ -n "$ISSUE_NUMBER" ]; then
            echo "Current Issue: #$ISSUE_NUMBER"
        fi
        if [ -n "$ISSUE_FILE" ]; then
            echo "Current File: $(basename "$ISSUE_FILE")"
        fi
        if [ -n "$TIMESTAMP" ]; then
            local elapsed=$(($(date +%s) - TIMESTAMP))
            echo "Time Elapsed: ${elapsed}s"
        fi
    else
        echo "State: UNINITIALIZED"
    fi

    echo ""

    # Queue statistics
    local queue_count=$(count_queue_files)
    local completed_count=$(find "$COMPLETED_DIR" -type f -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
    local failed_count=$(find "$FAILED_DIR" -type f -name "*.md" 2>/dev/null | wc -l | tr -d ' ')

    echo "Queue: $queue_count files"
    echo "Completed: $completed_count files"
    echo "Failed: $failed_count files"

    echo ""

    # Recent log file
    if [ -n "$(ls -t "$LOGS_DIR"/hopper-*.log 2>/dev/null | head -1)" ]; then
        local latest_log=$(ls -t "$LOGS_DIR"/hopper-*.log | head -1)
        echo "Latest Log: $latest_log"
    fi
}

cmd_stop() {
    echo "Sending stop signal to ZTE Hopper..."

    if [ ! -f "$PID_FILE" ]; then
        echo "Error: ZTE Hopper is not running"
        exit 1
    fi

    # Create stop signal file
    touch "$STOP_FILE"

    echo "Stop signal sent. Hopper will stop after completing current issue."
    echo "Use './scripts/zte_hopper.sh --status' to monitor progress"
}

cmd_kill() {
    echo "Killing ZTE Hopper..."

    if [ ! -f "$PID_FILE" ]; then
        echo "Error: ZTE Hopper is not running (no PID file found)"
        exit 1
    fi

    local pid=$(cat "$PID_FILE")

    if ! ps -p "$pid" > /dev/null 2>&1; then
        echo "Error: Process $pid is not running (stale PID file)"
        rm -f "$PID_FILE"
        exit 1
    fi

    echo "Sending SIGTERM to process $pid..."
    kill -TERM "$pid"

    # Wait for process to exit
    local wait_count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $wait_count -lt 10 ]; do
        sleep 1
        wait_count=$((wait_count + 1))
    done

    if ps -p "$pid" > /dev/null 2>&1; then
        echo "Process did not exit gracefully, sending SIGKILL..."
        kill -KILL "$pid"
    fi

    # Clean up PID file
    rm -f "$PID_FILE"

    echo "ZTE Hopper stopped"
}

#############################################################################
# Main Entry Point
#############################################################################

show_usage() {
    cat << EOF
ZTE Hopper - Automated Pipeline Queue System

Usage: $0 [COMMAND]

Commands:
    --work      Start processing queue (processes all files in queue/)
    --status    Show queue status and current progress
    --stop      Stop after current issue completes
    --kill      Kill immediately (graceful shutdown)

Queue Management:
    To add issues to queue:  cp issue.md zte-hopper/queue/
    Issues are processed FIFO by file creation time

Examples:
    # Start processing queue
    $0 --work

    # Monitor progress
    $0 --status

    # Stop after current issue
    $0 --stop

    # Emergency stop
    $0 --kill

For more information, see zte-hopper/README.md
EOF
}

main() {
    # Ensure we're in repository root or worktree
    if [ ! -e ".git" ] || [ ! -d "adws" ]; then
        echo "Error: Must run from repository root directory"
        exit 1
    fi

    # Create directories if they don't exist
    mkdir -p "$QUEUE_DIR" "$COMPLETED_DIR" "$FAILED_DIR" "$LOGS_DIR"

    # Initialize logging for --work command
    if [ "${1:-}" = "--work" ]; then
        init_logging
    fi

    # Parse command
    case "${1:-}" in
        --work)
            cmd_work
            ;;
        --status)
            cmd_status
            ;;
        --stop)
            cmd_stop
            ;;
        --kill)
            cmd_kill
            ;;
        --help|-h|help)
            show_usage
            exit 0
            ;;
        *)
            echo "Error: Unknown command '${1:-}'"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main
main "$@"
