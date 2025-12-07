# Task: Implement Pattern Review System

## Context
I'm working on the tac-webbuilder project. The pattern detection system (Session 1.5) identifies automation patterns from hook events, but there's no way to review and approve these patterns before they're used to generate automated workflows. This session implements a CLI-based pattern review tool with manual approval/rejection, database tracking, and GitHub integration.

## Objective
Create a pattern review system with CLI interface, approval tracking database, and safety layer to prevent automation of incorrect/dangerous patterns before workflow generation (Sessions 12+).

## Background Information
- **Pattern Detection:** Already implemented (Session 1.5) - identifies tool sequences
- **Current Gap:** No review mechanism before automation
- **Safety Threshold:** 95% confidence + 100+ occurrences + $1000+ savings
- **Review Workflow:** Detect patterns → **Review & approve** → Generate workflows

---

## Implementation Steps

### Step 1: Database Migration (30 min)

**Create:** `app/server/db/migrations/016_add_pattern_approvals.sql`

**Template:** See `.claude/templates/DATABASE_MIGRATION.md`

**Tables:**

**pattern_approvals:**
- Columns: `pattern_id TEXT UNIQUE`, `status TEXT CHECK(...)`, `reviewed_by TEXT`, `reviewed_at TIMESTAMP`, `approval_notes TEXT`, `confidence_score REAL`, `occurrence_count INTEGER`, `estimated_savings_usd REAL`, `tool_sequence TEXT`, `pattern_context TEXT`, `example_sessions TEXT` (JSON array)
- Indexes: `idx_pattern_approvals_status`, `idx_pattern_approvals_reviewed_at`, `idx_pattern_approvals_confidence`
- Status values: `'pending', 'approved', 'rejected', 'auto-approved', 'auto-rejected'`

**pattern_review_history** (audit trail):
- Columns: `pattern_id TEXT`, `action TEXT CHECK(...)`, `reviewer TEXT`, `notes TEXT`
- Index: `idx_pattern_review_history_pattern`
- Action values: `'approved', 'rejected', 'flagged', 'commented'`

**Run migration:**
```bash
cd app/server
sqlite3 db/workflow_history.db < db/migrations/016_add_pattern_approvals.sql
```

---

### Step 2: Service Layer (60 min)

**Create:** `app/server/services/pattern_review_service.py` (~200 lines)

**Template:** See `.claude/templates/SERVICE_LAYER.md`

**Data Model:**
```python
@dataclass
class PatternReviewItem:
    pattern_id: str
    tool_sequence: str
    status: str
    confidence_score: float
    occurrence_count: int
    estimated_savings_usd: float
    pattern_context: Optional[str]
    example_sessions: List[str]  # Parsed from JSON
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    approval_notes: Optional[str] = None
```

**Service Methods:**
- `get_pending_patterns(limit=20)` - Fetch patterns pending review, ordered by impact score
- `approve_pattern(pattern_id, reviewer, notes)` - Set status='approved', add to history
- `reject_pattern(pattern_id, reviewer, reason)` - Set status='rejected', add to history
- `get_pattern_details(pattern_id)` - Get single pattern with all metadata
- `get_review_statistics()` - Return counts by status (pending, approved, rejected, etc.)

**Impact Score Formula:**
```python
ORDER BY (confidence_score * occurrence_count * estimated_savings_usd) DESC
```

**Reference similar patterns:**
- `app/server/services/workflow_service.py` for database operations
- Use `json.loads()` for `example_sessions` field

---

### Step 3: CLI Tool (90 min)

**Create:** `scripts/review_patterns.py` (~400 lines)

**Template:** See `.claude/templates/CLI_TOOL.md`

**Class Structure:**
```python
class PatternReviewCLI:
    def __init__(self, reviewer_name='cli-reviewer'):
        self.service = PatternReviewService()
        self.reviewer_name = reviewer_name

    def show_statistics(self):
        # Display counts by status

    def display_pattern(self, pattern):
        # Show pattern details with metrics, context, examples

    def review_pattern_interactive(self, pattern):
        # Prompt: [a]pprove, [r]eject, [s]kip, [d]etails, [q]uit
        # Handle each action

    def review_all_pending(self, limit=20):
        # Loop through pending patterns

    def review_single_pattern(self, pattern_id):
        # Review specific pattern
```

**Interactive Actions:**
- `a` - Approve (optional notes)
- `r` - Reject (mandatory reason)
- `s` - Skip to next
- `d` - Show full JSON details
- `q` - Exit session

**Arguments:**
```python
--stats              Show statistics only
--pattern-id <id>    Review specific pattern
--limit N            Max patterns to review (default: 20)
--reviewer "Name"    Reviewer attribution (default: cli-reviewer)
```

**Make executable:**
```bash
chmod +x scripts/review_patterns.py
```

---

### Step 4: Tests (45 min)

**Create:** `scripts/tests/test_pattern_review.py` (~150 lines)

**Template:** See `.claude/templates/PYTEST_TESTS.md`

**Test Cases:**
1. `test_get_pending_patterns_empty` - Empty database
2. `test_get_pending_patterns` - With test data
3. `test_approve_pattern` - Approval updates status and creates history entry
4. `test_reject_pattern` - Rejection updates status and creates history entry
5. `test_get_review_statistics` - Counts by status

**Test Data Setup:**
```python
# Insert sample pattern in fixture
cursor.execute("""
    INSERT INTO pattern_approvals
        (pattern_id, status, tool_sequence, confidence_score,
         occurrence_count, estimated_savings_usd, example_sessions)
    VALUES (?, 'pending', 'Read→Edit→Write', 0.95, 150, 1200.50, ?)
""", ('test-pattern-1', json.dumps(['session-1', 'session-2'])))
```

**Run tests:**
```bash
cd /Users/Warmonger0/tac/tac-webbuilder
python -m pytest scripts/tests/test_pattern_review.py -v
```

---

### Step 5: Manual Testing (30 min)

**Insert sample patterns:**
```bash
cd app/server
sqlite3 db/workflow_history.db <<EOF
INSERT INTO pattern_approvals
    (pattern_id, status, tool_sequence, confidence_score, occurrence_count,
     estimated_savings_usd, pattern_context, example_sessions)
VALUES
    ('test-retry-pattern', 'pending', 'Test→Analyze→Fix→Test', 0.98, 250, 2500.0,
     'Automated test-fix-retry loop', '["session-1", "session-2", "session-3"]'),
    ('test-refactor-pattern', 'pending', 'Read→Edit→Lint→Test→Write', 0.92, 120, 1800.0,
     'Safe refactoring pattern', '["session-4", "session-5"]'),
    ('test-dangerous-pattern', 'pending', 'Delete→Delete→Delete', 0.65, 15, 50.0,
     'Cascading deletes - potentially dangerous', '["session-6"]');
EOF
```

**Test CLI:**
```bash
cd ../..
python scripts/review_patterns.py --stats
python scripts/review_patterns.py --pattern-id test-retry-pattern
python scripts/review_patterns.py  # Interactive review session
```

---

### Step 6: Documentation (20 min)

**Update:** `docs/features/observability-and-logging.md`

**Add section:**
```markdown
## Pattern Review Workflow

Before detected patterns are automated, they go through manual review.

**Review Criteria:**
- **Auto-Approve (>99%):** Well-known patterns, 200+ occurrences, $5000+ savings
- **Manual Review (95-99%):** Novel patterns, 100-200 occurrences, $1000-5000 savings
- **Auto-Reject (<95%):** Suspicious patterns, destructive operations

**CLI Usage:**
```bash
python scripts/review_patterns.py --stats
python scripts/review_patterns.py --interactive
python scripts/review_patterns.py --pattern-id <id>
```

**Review Actions:**
- Approve: Pattern will be automated (requires notes)
- Reject: Pattern blocked (requires reason)
- Skip: Review later

**Integration:** Approved patterns feed into Sessions 12-13 (Closed-loop learning, workflow generation)
```

---

## Success Criteria

- ✅ pattern_approvals and pattern_review_history tables created
- ✅ PatternReviewService implements all methods (5+)
- ✅ CLI tool provides interactive review interface
- ✅ All 5 tests passing
- ✅ Manual test confirms approve/reject/skip actions work
- ✅ Review history tracked correctly
- ✅ Documentation updated

---

## Files Expected to Change

**Created (4):**
- `app/server/db/migrations/016_add_pattern_approvals.sql` (~80 lines)
- `app/server/services/pattern_review_service.py` (~200 lines)
- `scripts/review_patterns.py` (~400 lines)
- `scripts/tests/test_pattern_review.py` (~150 lines)

**Modified (2):**
- `app/server/core/pattern_detector.py` (check approval status before automation)
- `docs/features/observability-and-logging.md` (add Pattern Review section)

---

## Quick Reference

**Templates Used:**
- `DATABASE_MIGRATION.md` - SQL structure, indexes, triggers
- `SERVICE_LAYER.md` - Repository pattern, CRUD operations
- `CLI_TOOL.md` - Interactive CLI with argparse
- `PYTEST_TESTS.md` - Fixtures, mocks, assertions

**Run Tests:**
```bash
python -m pytest scripts/tests/test_pattern_review.py -v
```

**CLI Examples:**
```bash
python scripts/review_patterns.py --stats
python scripts/review_patterns.py --interactive --limit 10
python scripts/review_patterns.py --pattern-id test-retry-pattern --reviewer "Your Name"
```

---

## Estimated Time

- Step 1 (Migration): 30 min
- Step 2 (Service): 60 min
- Step 3 (CLI): 90 min
- Step 4 (Tests): 45 min
- Step 5 (Manual test): 30 min
- Step 6 (Docs): 20 min

**Total: 3-4 hours**

---

## Troubleshooting

**Migration fails:**
```bash
sqlite3 app/server/db/workflow_history.db "DROP TABLE IF EXISTS pattern_approvals"
# Re-run migration
```

**Import errors:**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python scripts/review_patterns.py
```

**No patterns to review:**
```bash
# Insert test data (see Step 5)
```

---

## Session Completion

When done, provide summary:

```markdown
## ✅ Session 6 Complete - Pattern Review System

**Duration:** ~X hours
**Status:** Complete ✅
**Next:** Ready for Session 7 (Daily Pattern Analysis)

### What Was Done
1. Pattern approvals database (2 tables, indexes, audit trail)
2. PatternReviewService (~200 lines, 5 methods)
3. CLI review tool (~400 lines, interactive interface)
4. Tests (5/5 passing)
5. Documentation updated

### Key Results
- ✅ Manual approval system for patterns
- ✅ Safety layer before automation
- ✅ Audit trail for all decisions
- ✅ CLI for efficient review

### Files Changed
**Created (4):** migrations/016, pattern_review_service.py, review_patterns.py, tests
**Modified (2):** pattern_detector.py, observability docs

### Test Results
```
5/5 passed
```
```
