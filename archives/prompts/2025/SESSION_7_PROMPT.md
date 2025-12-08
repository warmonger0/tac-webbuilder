# Task: Implement Daily Pattern Analysis System

## Context
I'm working on the tac-webbuilder project. The pattern review system (Session 6) provides a manual approval workflow for patterns, but patterns must be discovered and populated manually. This session implements a daily batch analysis script that automatically discovers new patterns from hook_events, calculates metrics using statistical analysis, and populates the pattern_approvals table for review.

## Objective
Create an automated daily batch analysis system that discovers patterns from hook events, calculates confidence scores and savings estimates, auto-classifies patterns based on thresholds, and notifies reviewers of new patterns requiring approval.

## Background Information
- **Pattern Review System:** Already implemented (Session 6) - provides CLI and web UI for approval
- **Current Gap:** No automated pattern discovery from hook events
- **Analysis Window:** Last 24 hours of hook_events
- **Auto-Classification Rules:**
  - Auto-approve: >99% confidence + 200+ occurrences + $5000+ savings
  - Auto-reject: <95% confidence OR destructive operations
  - Pending review: 95-99% confidence (requires manual review via Panel 8 or CLI)

---

## Implementation Steps

### Step 1: Pattern Discovery Algorithm (90 min)

**Create:** `scripts/analyze_daily_patterns.py` (~400-500 lines)

**Template:** See `.claude/templates/CLI_TOOL.md` for CLI structure

**Class Structure:**
```python
class DailyPatternAnalyzer:
    def __init__(self, window_hours=24):
        self.window_hours = window_hours
        self.service = PatternReviewService()

    def analyze_patterns(self) -> Dict[str, Any]:
        """Main analysis entry point."""
        # 1. Extract tool sequences from hook_events
        # 2. Find repeated patterns
        # 3. Calculate metrics
        # 4. Deduplicate against existing patterns
        # 5. Auto-classify
        # 6. Save to pattern_approvals

    def extract_tool_sequences(self) -> List[ToolSequence]:
        """Extract tool sequences from hook_events grouped by session_id."""

    def find_repeated_patterns(self, sequences) -> List[Pattern]:
        """Identify patterns that repeat across multiple sessions."""

    def calculate_metrics(self, pattern) -> PatternMetrics:
        """Calculate confidence, occurrences, and estimated savings."""

    def auto_classify(self, pattern) -> str:
        """Return 'auto-approved', 'pending', or 'auto-rejected'."""

    def deduplicate_pattern(self, pattern) -> bool:
        """Check if pattern already exists, update if so."""
```

**Pattern Discovery SQL:**
```python
def extract_tool_sequences(self):
    """Extract tool sequences from last 24 hours."""
    query = """
        SELECT
            session_id,
            GROUP_CONCAT(tool_name, '→') as tool_sequence,
            COUNT(*) as event_count,
            MIN(timestamp) as first_seen,
            MAX(timestamp) as last_seen
        FROM hook_events
        WHERE timestamp >= datetime('now', '-{} hours')
        AND event_type = 'tool_use'
        GROUP BY session_id
        ORDER BY session_id, timestamp
    """.format(self.window_hours)

    # Execute and return results
```

**Pattern Grouping:**
```python
def find_repeated_patterns(self, sequences):
    """Group identical tool sequences and count occurrences."""
    from collections import Counter

    # Group by tool_sequence
    pattern_counts = Counter([seq.tool_sequence for seq in sequences])

    # Filter patterns that appear 2+ times
    repeated = {seq: count for seq, count in pattern_counts.items() if count >= 2}

    return repeated
```

**Confidence Score Calculation:**
```python
def calculate_confidence(self, occurrences, total_sessions):
    """Statistical confidence score (0.0 to 1.0)."""
    # Simple frequency-based confidence
    # More sophisticated: chi-square, z-score, etc.

    frequency = occurrences / total_sessions

    # Boost confidence for high occurrence counts
    if occurrences >= 100:
        confidence = min(0.99, frequency * 1.2)
    elif occurrences >= 50:
        confidence = min(0.95, frequency * 1.1)
    else:
        confidence = frequency

    return round(confidence, 4)
```

**Estimated Savings Calculation:**
```python
def estimate_savings(self, pattern, occurrences):
    """Estimate cost savings if pattern is automated."""
    # Average time per tool execution
    avg_time_per_tool = 30  # seconds

    # Parse tool sequence
    tools = pattern.split('→')
    pattern_time_seconds = len(tools) * avg_time_per_tool

    # Assume $100/hour AI cost (conservative)
    cost_per_second = 100.0 / 3600.0

    # Savings if automated
    savings_per_occurrence = pattern_time_seconds * cost_per_second
    total_savings = savings_per_occurrence * occurrences

    return round(total_savings, 2)
```

**Auto-Classification Logic:**
```python
def auto_classify(self, pattern, confidence, occurrences, savings):
    """Determine pattern status based on thresholds."""
    # Check for destructive operations
    destructive_tools = ['Delete', 'Remove', 'Drop', 'Truncate', 'ForceDelete']
    if any(tool in pattern for tool in destructive_tools):
        return 'auto-rejected'

    # Auto-approve high-confidence, high-value patterns
    if confidence > 0.99 and occurrences > 200 and savings > 5000:
        return 'auto-approved'

    # Auto-reject low-confidence patterns
    if confidence < 0.95:
        return 'auto-rejected'

    # Everything else requires manual review
    return 'pending'
```

**Deduplication:**
```python
def deduplicate_pattern(self, pattern_id):
    """Check if pattern already exists in pattern_approvals."""
    existing = self.service.get_pattern_details(pattern_id)

    if existing:
        # Update occurrence count
        new_count = existing.occurrence_count + 1
        self.service.update_occurrence_count(pattern_id, new_count)
        return True  # Already exists

    return False  # New pattern
```

**Reference implementations:**
- `app/server/services/pattern_review_service.py` for database interactions
- `scripts/review_patterns.py` for CLI structure

---

### Step 2: Database Integration (30 min)

**Modify:** `app/server/services/pattern_review_service.py`

**Add methods:**
```python
def create_pattern(self, pattern_data: Dict[str, Any]) -> str:
    """Insert new pattern into pattern_approvals."""
    pattern_id = hashlib.sha256(
        pattern_data['tool_sequence'].encode()
    ).hexdigest()[:16]

    cursor.execute("""
        INSERT INTO pattern_approvals
            (pattern_id, status, tool_sequence, confidence_score,
             occurrence_count, estimated_savings_usd, pattern_context,
             example_sessions)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        pattern_id,
        pattern_data['status'],
        pattern_data['tool_sequence'],
        pattern_data['confidence_score'],
        pattern_data['occurrence_count'],
        pattern_data['estimated_savings_usd'],
        pattern_data['pattern_context'],
        json.dumps(pattern_data['example_sessions'])
    ))

    return pattern_id

def update_occurrence_count(self, pattern_id: str, new_count: int):
    """Update occurrence count for existing pattern."""
    cursor.execute("""
        UPDATE pattern_approvals
        SET occurrence_count = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE pattern_id = ?
    """, (new_count, pattern_id))
```

**No template needed** - simple method additions to existing service.

---

### Step 3: CLI Interface (45 min)

**Arguments for `scripts/analyze_daily_patterns.py`:**
```python
parser.add_argument(
    '--hours',
    type=int,
    default=24,
    help='Analysis window in hours (default: 24)'
)
parser.add_argument(
    '--min-occurrences',
    type=int,
    default=2,
    help='Minimum pattern occurrences to consider (default: 2)'
)
parser.add_argument(
    '--dry-run',
    action='store_true',
    help='Analyze but do not save to database'
)
parser.add_argument(
    '--report',
    action='store_true',
    help='Generate analysis report (markdown)'
)
parser.add_argument(
    '--notify',
    action='store_true',
    help='Send notifications for new pending patterns'
)
parser.add_argument(
    '--verbose',
    action='store_true',
    help='Enable verbose output'
)
```

**Output Format:**
```python
def print_analysis_summary(self, results):
    """Print summary of analysis."""
    print("\n" + "="*80)
    print("DAILY PATTERN ANALYSIS SUMMARY")
    print("="*80)
    print(f"Analysis Window: {self.window_hours} hours")
    print(f"Total Sessions Analyzed: {results['total_sessions']}")
    print(f"Patterns Discovered: {results['patterns_found']}")
    print(f"  - New Patterns: {results['new_patterns']}")
    print(f"  - Updated Patterns: {results['updated_patterns']}")
    print(f"\nClassification:")
    print(f"  - Auto-Approved: {results['auto_approved']}")
    print(f"  - Pending Review: {results['pending']}")
    print(f"  - Auto-Rejected: {results['auto_rejected']}")
    print(f"\nEstimated Total Savings: ${results['total_savings']:,.2f}")
    print("="*80 + "\n")
```

---

### Step 4: Cron Wrapper Script (20 min)

**Create:** `scripts/cron/daily_pattern_analysis.sh` (~50 lines)

```bash
#!/bin/bash
# Daily Pattern Analysis - Cron Wrapper
# Runs daily at 2 AM to analyze patterns from last 24 hours

set -e

# Configuration
PROJECT_ROOT="/path/to/tac-webbuilder"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/pattern_analysis_$(date +%Y%m%d).log"
NOTIFY_EMAIL="admin@example.com"  # Optional

# Create log directory
mkdir -p "$LOG_DIR"

# Navigate to project
cd "$PROJECT_ROOT"

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

    # Optional: Send error notification
    # echo "Pattern analysis failed. Check logs: $LOG_FILE" | \
    #     mail -s "Pattern Analysis Failed" "$NOTIFY_EMAIL"
fi

# Cleanup old logs (keep last 30 days)
find "$LOG_DIR" -name "pattern_analysis_*.log" -mtime +30 -delete

exit $EXIT_CODE
```

**Make executable:**
```bash
chmod +x scripts/cron/daily_pattern_analysis.sh
```

**Crontab entry:**
```bash
# Run daily at 2:00 AM
0 2 * * * /path/to/tac-webbuilder/scripts/cron/daily_pattern_analysis.sh
```

---

### Step 5: Notification System (30 min)

**Add to `scripts/analyze_daily_patterns.py`:**

```python
def send_notifications(self, new_pending_patterns):
    """Send notifications for new pending patterns."""
    if not new_pending_patterns:
        return

    # Generate notification message
    message = self._format_notification(new_pending_patterns)

    # Send via configured channel
    # Option 1: Email (requires SMTP configuration)
    # self._send_email(message)

    # Option 2: Slack webhook (if configured)
    # self._send_slack(message)

    # Option 3: Log to file for now
    self._log_notification(message)

def _format_notification(self, patterns):
    """Format notification message."""
    msg = f"""
New Patterns Requiring Review
==============================

{len(patterns)} new patterns discovered that require manual approval.

"""
    for pattern in patterns[:5]:  # Show top 5
        msg += f"""
Pattern: {pattern.tool_sequence}
Confidence: {pattern.confidence_score:.1%}
Occurrences: {pattern.occurrence_count}
Estimated Savings: ${pattern.estimated_savings_usd:,.2f}
---
"""

    msg += f"\nReview via CLI: python scripts/review_patterns.py"
    msg += f"\nReview via Web UI: http://localhost:5173 (Panel 8)"

    return msg

def _log_notification(self, message):
    """Log notification to file."""
    log_file = Path("logs/pattern_notifications.log")
    log_file.parent.mkdir(exist_ok=True)

    with open(log_file, 'a') as f:
        f.write(f"\n[{datetime.now().isoformat()}]\n")
        f.write(message)
        f.write("\n")
```

---

### Step 6: Tests (45 min)

**Create:** `scripts/tests/test_daily_pattern_analysis.py` (~150 lines)

**Template:** See `.claude/templates/PYTEST_TESTS.md`

**Test Cases:**
1. `test_extract_tool_sequences` - Verify SQL extraction logic
2. `test_find_repeated_patterns` - Pattern grouping and counting
3. `test_calculate_confidence` - Confidence score formula
4. `test_estimate_savings` - Savings calculation
5. `test_auto_classify_approved` - High-confidence auto-approval
6. `test_auto_classify_rejected` - Low-confidence auto-rejection
7. `test_auto_classify_destructive` - Destructive operations rejected
8. `test_deduplicate_new_pattern` - New pattern insertion
9. `test_deduplicate_existing_pattern` - Occurrence count update
10. `test_full_analysis_workflow` - End-to-end test

**Fixture Setup:**
```python
@pytest.fixture
def setup_test_hook_events(db_connection):
    """Insert test hook events for analysis."""
    cursor = db_connection.cursor()

    # Session 1: Read→Edit→Write (appears 5 times)
    for i in range(5):
        session_id = f"test-session-{i}"
        for tool in ['Read', 'Edit', 'Write']:
            cursor.execute("""
                INSERT INTO hook_events
                    (session_id, event_type, tool_name, timestamp)
                VALUES (?, 'tool_use', ?, datetime('now', '-1 hour'))
            """, (session_id, tool))

    # Session 2: Test→Fix→Test (appears 3 times)
    for i in range(5, 8):
        session_id = f"test-session-{i}"
        for tool in ['Test', 'Fix', 'Test']:
            cursor.execute("""
                INSERT INTO hook_events
                    (session_id, event_type, tool_name, timestamp)
                VALUES (?, 'tool_use', ?, datetime('now', '-2 hours'))
            """, (session_id, tool))

    db_connection.commit()
```

**Test Example:**
```python
def test_calculate_confidence(analyzer):
    """Test confidence score calculation."""
    # Test with 100 occurrences out of 1000 sessions
    confidence = analyzer.calculate_confidence(
        occurrences=100,
        total_sessions=1000
    )

    assert 0.0 <= confidence <= 1.0
    assert confidence > 0.10  # At least 10% frequency

def test_auto_classify_destructive(analyzer):
    """Test that destructive patterns are auto-rejected."""
    status = analyzer.auto_classify(
        pattern='Read→Delete→Delete',
        confidence=0.99,
        occurrences=500,
        savings=10000
    )

    assert status == 'auto-rejected'
```

**Run tests:**
```bash
cd /Users/Warmonger0/tac/tac-webbuilder
python -m pytest scripts/tests/test_daily_pattern_analysis.py -v
```

---

### Step 7: Documentation (20 min)

**Modify:** `docs/features/observability-and-logging.md`

**Add section:**
```markdown
## Daily Pattern Analysis

### Overview
The daily pattern analysis system automatically discovers automation patterns from hook events, calculates metrics, and populates the pattern review system for approval.

### How It Works
1. **Extraction**: Query `hook_events` table for last 24 hours
2. **Pattern Discovery**: Group tool sequences by session, identify repeated patterns
3. **Metrics Calculation**: Calculate confidence scores, occurrence counts, estimated savings
4. **Auto-Classification**:
   - Auto-approve: >99% confidence + 200+ occurrences + $5000+ savings
   - Auto-reject: <95% confidence OR destructive operations
   - Pending: 95-99% confidence (manual review required)
5. **Deduplication**: Check existing patterns, update occurrence counts
6. **Notification**: Alert reviewers of new pending patterns

### Usage

**Manual Execution:**
```bash
# Analyze last 24 hours
python scripts/analyze_daily_patterns.py

# Analyze last 48 hours
python scripts/analyze_daily_patterns.py --hours 48

# Dry run (no database changes)
python scripts/analyze_daily_patterns.py --dry-run --verbose

# Generate report
python scripts/analyze_daily_patterns.py --report
```

**Automated Execution:**
```bash
# Install cron job (runs daily at 2 AM)
crontab -e
# Add: 0 2 * * * /path/to/tac-webbuilder/scripts/cron/daily_pattern_analysis.sh
```

### Configuration

**Thresholds** (in `analyze_daily_patterns.py`):
- Minimum occurrences: 2 (configurable via `--min-occurrences`)
- Auto-approve: confidence > 99%, occurrences > 200, savings > $5000
- Auto-reject: confidence < 95% OR destructive operations
- Pending review: 95-99% confidence

**Destructive Operations:**
Operations flagged as potentially dangerous and auto-rejected:
- Delete, Remove, Drop, Truncate, ForceDelete

### Output

**Console Output:**
```
================================================================================
DAILY PATTERN ANALYSIS SUMMARY
================================================================================
Analysis Window: 24 hours
Total Sessions Analyzed: 145
Patterns Discovered: 12
  - New Patterns: 8
  - Updated Patterns: 4

Classification:
  - Auto-Approved: 2
  - Pending Review: 7
  - Auto-Rejected: 3

Estimated Total Savings: $12,450.00
================================================================================
```

**Database Updates:**
- New patterns added to `pattern_approvals` table
- Existing patterns updated with new occurrence counts
- Ready for review via Panel 8 or CLI

### Review Workflow

After daily analysis discovers new patterns:

1. **CLI Review:**
   ```bash
   python scripts/review_patterns.py --stats
   python scripts/review_patterns.py  # Interactive review
   ```

2. **Web UI Review:**
   - Navigate to Panel 8 (Review Panel)
   - Review pending patterns
   - Approve/reject with notes

3. **Automated Workflows:**
   - Auto-approved patterns ready for workflow generation (Session 12+)
   - Pending patterns require manual review
   - Auto-rejected patterns logged for audit
```

---

## Success Criteria

- ✅ Script analyzes hook_events from configurable time window (default 24 hours)
- ✅ Discovers repeated patterns across multiple sessions
- ✅ Calculates confidence scores using statistical analysis
- ✅ Calculates estimated cost savings for each pattern
- ✅ Auto-classifies patterns (auto-approved, pending, auto-rejected)
- ✅ Deduplicates against existing patterns in pattern_approvals table
- ✅ Updates occurrence counts for existing patterns
- ✅ Logs notifications for new pending patterns
- ✅ Supports dry-run mode for testing
- ✅ Can run as cron job or on-demand
- ✅ All tests passing (10/10)
- ✅ Documentation updated in observability-and-logging.md

---

## Files Expected to Change

**Created (4):**
- `scripts/analyze_daily_patterns.py` (~450 lines) - Main analysis script
- `scripts/tests/test_daily_pattern_analysis.py` (~150 lines) - Tests
- `scripts/cron/daily_pattern_analysis.sh` (~50 lines) - Cron wrapper
- `logs/pattern_notifications.log` (auto-created) - Notification log

**Modified (2):**
- `app/server/services/pattern_review_service.py` (add `create_pattern` and `update_occurrence_count` methods)
- `docs/features/observability-and-logging.md` (add Daily Pattern Analysis section)

---

## Quick Reference

**Templates used:**
- CLI_TOOL.md - Script structure and argument parsing
- PYTEST_TESTS.md - Test fixtures and assertions

**Run analysis:**
```bash
# Standard daily run
python scripts/analyze_daily_patterns.py

# Dry run with verbose output
python scripts/analyze_daily_patterns.py --dry-run --verbose

# Custom time window
python scripts/analyze_daily_patterns.py --hours 48

# With report generation
python scripts/analyze_daily_patterns.py --report
```

**Run tests:**
```bash
pytest scripts/tests/test_daily_pattern_analysis.py -v
```

**Install cron job:**
```bash
chmod +x scripts/cron/daily_pattern_analysis.sh
crontab -e
# Add: 0 2 * * * /path/to/tac-webbuilder/scripts/cron/daily_pattern_analysis.sh
```

**Review discovered patterns:**
```bash
# Via CLI
python scripts/review_patterns.py

# Via Web UI
# Navigate to Panel 8 at http://localhost:5173
```

---

## Estimated Time

- Step 1 (Pattern Discovery): 90 min
- Step 2 (Database Integration): 30 min
- Step 3 (CLI Interface): 45 min
- Step 4 (Cron Wrapper): 20 min
- Step 5 (Notifications): 30 min
- Step 6 (Tests): 45 min
- Step 7 (Documentation): 20 min

**Total: 3-4 hours**

---

## Session Completion Template

When done, provide summary in this format:

```markdown
## ✅ Session 7 Complete - Daily Pattern Analysis

**Duration:** ~X hours
**Status:** Complete ✅
**Next:** Ready for Session 8 (Plans Panel Database Migration)

### What Was Done
- Implemented daily batch analysis script for pattern discovery
- Statistical analysis of hook_events with confidence scoring
- Auto-classification system (auto-approve, pending, auto-reject)
- Deduplication logic to update existing patterns
- Cron wrapper for automated daily execution
- Comprehensive test suite (10 tests)
- Documentation in observability-and-logging.md

### Key Results
- Pattern discovery from hook_events operational
- Auto-classification thresholds: >99% + 200+ occurrences + $5000 = auto-approve
- Destructive operations automatically rejected
- Notifications logged for new pending patterns
- Ready for cron scheduling

### Files Changed
**Created (4):**
- scripts/analyze_daily_patterns.py
- scripts/tests/test_daily_pattern_analysis.py
- scripts/cron/daily_pattern_analysis.sh
- logs/pattern_notifications.log

**Modified (2):**
- app/server/services/pattern_review_service.py
- docs/features/observability-and-logging.md

### Test Results
```
pytest scripts/tests/test_daily_pattern_analysis.py -v
======================== 10 passed in X.XXs ========================
```

### Next Session
Session 8: Plans Panel Database Migration (4-5 hours)
- Migrate hardcoded PlansPanel.tsx to database-driven system
- Create planned_features table
- API endpoints for CRUD operations
- Frontend refactor to consume API
```
