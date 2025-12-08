# Task: Implement Pattern Review System

## Context
I'm working on the tac-webbuilder project. The pattern detection system (completed in Session 1.5) identifies automation patterns from hook events, but there's currently no way to review and approve these patterns before they're used to generate automated workflows. This session implements a CLI-based pattern review tool that allows manual approval/rejection of detected patterns, ensuring quality and preventing automation of incorrect patterns.

## Objective
Create a pattern review system that:
- Displays detected patterns with context (frequency, cost savings, examples)
- Allows manual approval/rejection via CLI interface
- Stores approval decisions in database
- Integrates with GitHub for collaborative review
- Provides filtering and search capabilities
- Sets foundation for semi-automatic workflow generation

## Background Information
- **Pattern Detection:** Already implemented (Session 1.5) - identifies tool sequences
- **Current Gap:** No review mechanism before automation
- **Safety Layer:** Manual approval prevents bad automation (e.g., infinite loops, destructive patterns)
- **Workflow:** Detect patterns → **Review & approve** → Generate automated workflows
- **Threshold:** 95% confidence + 100+ occurrences + $1000+ savings before automation eligible

- **Review Categories:**
  1. **Auto-Approve:** High confidence (>99%), well-known patterns (Test-Fix-Retry)
  2. **Manual Review:** Medium confidence (95-99%), novel patterns
  3. **Auto-Reject:** Low confidence (<95%), suspicious patterns (destructive, infinite loops)

- **Files to Create:**
  - `scripts/review_patterns.py` (~400-500 lines) - CLI review tool
  - `app/server/db/migrations/016_add_pattern_approvals.sql` - Approval tracking table
  - `app/server/services/pattern_review_service.py` (~200 lines) - Business logic
  - `scripts/tests/test_pattern_review.py` (~150 lines) - Tests

- **Files to Modify:**
  - `app/server/core/pattern_detector.py` - Add approval status checks
  - `docs/features/observability-and-logging.md` - Document review workflow

---

## Step-by-Step Instructions

### Step 1: Understand Pattern Detection Output (20 min)

Review the existing pattern detection system to understand what data is available:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder
```

**Read these files:**
1. `app/server/core/pattern_detector.py` - Pattern detection logic (Session 1.5)
2. `app/server/db/migrations/` - Find pattern-related tables
3. Look for pattern_occurrences, patterns tables

**Check current patterns:**
```bash
cd app/server
DB_TYPE=sqlite python3 -c "
import sqlite3
conn = sqlite3.connect('db/workflow_history.db')
cursor = conn.cursor()

# Show pattern tables
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%pattern%'\")
print('Pattern tables:', cursor.fetchall())

# Show sample patterns
cursor.execute('SELECT DISTINCT pattern_id FROM pattern_occurrences LIMIT 10')
print('Sample pattern IDs:', cursor.fetchall())

# Show pattern occurrence count
cursor.execute('SELECT pattern_id, COUNT(*) as count FROM pattern_occurrences GROUP BY pattern_id ORDER BY count DESC LIMIT 5')
print('Top patterns by occurrence:', cursor.fetchall())
"
```

**Document:**
- Pattern data structure (pattern_id, tool_sequence, confidence, etc.)
- How patterns are stored
- What metadata is available (frequency, cost, timestamps)
- Current approval status (if any)

### Step 2: Create Pattern Approvals Database Migration (30 min)

Create new file: `app/server/db/migrations/016_add_pattern_approvals.sql`

```sql
-- Migration 016: Add pattern approval tracking
-- Created: 2025-12-06
-- Purpose: Track manual approval/rejection of detected patterns for automation

-- Pattern approvals table
CREATE TABLE IF NOT EXISTS pattern_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'rejected', 'auto-approved', 'auto-rejected')),
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    approval_notes TEXT,
    confidence_score REAL,
    occurrence_count INTEGER,
    estimated_savings_usd REAL,
    -- Pattern details (denormalized for review UI)
    tool_sequence TEXT NOT NULL,
    pattern_context TEXT,
    example_sessions TEXT,  -- JSON array of session IDs
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_pattern_approvals_status ON pattern_approvals(status);
CREATE INDEX IF NOT EXISTS idx_pattern_approvals_reviewed_at ON pattern_approvals(reviewed_at);
CREATE INDEX IF NOT EXISTS idx_pattern_approvals_confidence ON pattern_approvals(confidence_score);

-- Trigger to update updated_at
CREATE TRIGGER IF NOT EXISTS update_pattern_approvals_timestamp
AFTER UPDATE ON pattern_approvals
BEGIN
    UPDATE pattern_approvals SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Pattern review history (audit trail)
CREATE TABLE IF NOT EXISTS pattern_review_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('approved', 'rejected', 'flagged', 'commented')),
    reviewer TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pattern_id) REFERENCES pattern_approvals(pattern_id)
);

CREATE INDEX IF NOT EXISTS idx_pattern_review_history_pattern ON pattern_review_history(pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_review_history_created ON pattern_review_history(created_at);
```

**Run migration:**
```bash
cd app/server

# SQLite
sqlite3 db/workflow_history.db < db/migrations/016_add_pattern_approvals.sql

# PostgreSQL (if using)
PGPASSWORD=changeme psql -h 127.0.0.1 -U tac_user -d tac_webbuilder -f db/migrations/016_add_pattern_approvals.sql
```

**Verify:**
```bash
sqlite3 db/workflow_history.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%approval%'"
# Should show: pattern_approvals, pattern_review_history
```

### Step 3: Create Pattern Review Service (60 min)

Create new file: `app/server/services/pattern_review_service.py`

```python
#!/usr/bin/env python3
"""
Pattern Review Service

Business logic for reviewing and approving detected patterns before automation.

Responsibilities:
- Fetch patterns pending review
- Calculate pattern metrics (frequency, savings, confidence)
- Update approval status
- Track review history
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from app.server.db.database import get_connection

logger = logging.getLogger(__name__)


@dataclass
class PatternReviewItem:
    """Pattern pending review with all metadata."""
    pattern_id: str
    tool_sequence: str
    status: str
    confidence_score: float
    occurrence_count: int
    estimated_savings_usd: float
    pattern_context: Optional[str]
    example_sessions: List[str]
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    approval_notes: Optional[str] = None
    created_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)


class PatternReviewService:
    """Service for pattern review operations."""

    def get_pending_patterns(self, limit: int = 20) -> List[PatternReviewItem]:
        """
        Get patterns pending review, ordered by potential impact.

        Args:
            limit: Maximum number of patterns to return

        Returns:
            List of PatternReviewItem objects
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            # Get pending patterns with calculated metrics
            cursor.execute("""
                SELECT
                    pattern_id,
                    tool_sequence,
                    status,
                    confidence_score,
                    occurrence_count,
                    estimated_savings_usd,
                    pattern_context,
                    example_sessions,
                    reviewed_by,
                    reviewed_at,
                    approval_notes,
                    created_at
                FROM pattern_approvals
                WHERE status = 'pending'
                ORDER BY
                    (confidence_score * occurrence_count * estimated_savings_usd) DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            patterns = []

            for row in rows:
                # Parse example_sessions JSON
                example_sessions = json.loads(row[7]) if row[7] else []

                pattern = PatternReviewItem(
                    pattern_id=row[0],
                    tool_sequence=row[1],
                    status=row[2],
                    confidence_score=row[3],
                    occurrence_count=row[4],
                    estimated_savings_usd=row[5],
                    pattern_context=row[6],
                    example_sessions=example_sessions,
                    reviewed_by=row[8],
                    reviewed_at=row[9],
                    approval_notes=row[10],
                    created_at=row[11]
                )
                patterns.append(pattern)

            logger.info(f"[PatternReview] Found {len(patterns)} pending patterns")
            return patterns

    def approve_pattern(
        self,
        pattern_id: str,
        reviewer: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Approve a pattern for automation.

        Args:
            pattern_id: Pattern identifier
            reviewer: Name/ID of reviewer
            notes: Optional approval notes

        Returns:
            True if approved successfully
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            # Update approval status
            cursor.execute("""
                UPDATE pattern_approvals
                SET
                    status = 'approved',
                    reviewed_by = ?,
                    reviewed_at = ?,
                    approval_notes = ?
                WHERE pattern_id = ?
            """, (reviewer, datetime.now().isoformat(), notes, pattern_id))

            # Add to review history
            cursor.execute("""
                INSERT INTO pattern_review_history
                    (pattern_id, action, reviewer, notes)
                VALUES (?, 'approved', ?, ?)
            """, (pattern_id, reviewer, notes))

            conn.commit()

            logger.info(f"[PatternReview] Pattern {pattern_id} approved by {reviewer}")
            return True

    def reject_pattern(
        self,
        pattern_id: str,
        reviewer: str,
        reason: str
    ) -> bool:
        """
        Reject a pattern (will not be automated).

        Args:
            pattern_id: Pattern identifier
            reviewer: Name/ID of reviewer
            reason: Reason for rejection

        Returns:
            True if rejected successfully
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            # Update approval status
            cursor.execute("""
                UPDATE pattern_approvals
                SET
                    status = 'rejected',
                    reviewed_by = ?,
                    reviewed_at = ?,
                    approval_notes = ?
                WHERE pattern_id = ?
            """, (reviewer, datetime.now().isoformat(), reason, pattern_id))

            # Add to review history
            cursor.execute("""
                INSERT INTO pattern_review_history
                    (pattern_id, action, reviewer, notes)
                VALUES (?, 'rejected', ?, ?)
            """, (pattern_id, reviewer, reason))

            conn.commit()

            logger.info(f"[PatternReview] Pattern {pattern_id} rejected by {reviewer}")
            return True

    def get_pattern_details(self, pattern_id: str) -> Optional[PatternReviewItem]:
        """
        Get detailed information about a specific pattern.

        Args:
            pattern_id: Pattern identifier

        Returns:
            PatternReviewItem or None if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    pattern_id, tool_sequence, status, confidence_score,
                    occurrence_count, estimated_savings_usd, pattern_context,
                    example_sessions, reviewed_by, reviewed_at, approval_notes,
                    created_at
                FROM pattern_approvals
                WHERE pattern_id = ?
            """, (pattern_id,))

            row = cursor.fetchone()
            if not row:
                return None

            example_sessions = json.loads(row[7]) if row[7] else []

            return PatternReviewItem(
                pattern_id=row[0],
                tool_sequence=row[1],
                status=row[2],
                confidence_score=row[3],
                occurrence_count=row[4],
                estimated_savings_usd=row[5],
                pattern_context=row[6],
                example_sessions=example_sessions,
                reviewed_by=row[8],
                reviewed_at=row[9],
                approval_notes=row[10],
                created_at=row[11]
            )

    def get_review_statistics(self) -> Dict:
        """
        Get pattern review statistics.

        Returns:
            Dict with approval statistics
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    status,
                    COUNT(*) as count
                FROM pattern_approvals
                GROUP BY status
            """)

            stats = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                'pending': stats.get('pending', 0),
                'approved': stats.get('approved', 0),
                'rejected': stats.get('rejected', 0),
                'auto_approved': stats.get('auto-approved', 0),
                'auto_rejected': stats.get('auto-rejected', 0),
                'total': sum(stats.values())
            }
```

### Step 4: Create CLI Review Tool (90-120 min)

Create new file: `scripts/review_patterns.py`

```python
#!/usr/bin/env python3
"""
Pattern Review CLI Tool

Interactive command-line tool for reviewing detected automation patterns.

Usage:
    python scripts/review_patterns.py
    python scripts/review_patterns.py --pattern-id <id>
    python scripts/review_patterns.py --stats
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.server.services.pattern_review_service import (
    PatternReviewService,
    PatternReviewItem
)


class PatternReviewCLI:
    """Interactive CLI for pattern review."""

    def __init__(self, reviewer_name: str = "cli-reviewer"):
        self.service = PatternReviewService()
        self.reviewer_name = reviewer_name

    def show_statistics(self):
        """Display pattern review statistics."""
        stats = self.service.get_review_statistics()

        print("\n" + "="*80)
        print("PATTERN REVIEW STATISTICS")
        print("="*80)
        print(f"Total Patterns: {stats['total']}")
        print(f"  ⏳ Pending Review: {stats['pending']}")
        print(f"  ✅ Approved: {stats['approved']}")
        print(f"  ❌ Rejected: {stats['rejected']}")
        print(f"  🤖 Auto-Approved: {stats['auto_approved']}")
        print(f"  🚫 Auto-Rejected: {stats['auto_rejected']}")
        print("="*80 + "\n")

    def display_pattern(self, pattern: PatternReviewItem):
        """Display pattern details in readable format."""
        print("\n" + "="*80)
        print(f"PATTERN: {pattern.pattern_id}")
        print("="*80)
        print(f"Tool Sequence: {pattern.tool_sequence}")
        print(f"Status: {pattern.status}")
        print(f"")
        print(f"📊 METRICS:")
        print(f"  Confidence: {pattern.confidence_score:.2%}")
        print(f"  Occurrences: {pattern.occurrence_count}")
        print(f"  Est. Savings: ${pattern.estimated_savings_usd:.2f}")
        print(f"")
        if pattern.pattern_context:
            print(f"📝 CONTEXT:")
            print(f"  {pattern.pattern_context}")
            print(f"")
        if pattern.example_sessions:
            print(f"🔍 EXAMPLE SESSIONS:")
            for session_id in pattern.example_sessions[:5]:
                print(f"  - {session_id}")
            if len(pattern.example_sessions) > 5:
                print(f"  ... and {len(pattern.example_sessions) - 5} more")
            print(f"")
        print("="*80)

    def review_pattern_interactive(self, pattern: PatternReviewItem):
        """
        Interactively review a single pattern.

        Returns:
            True if reviewed, False if skipped
        """
        self.display_pattern(pattern)

        print("\nACTIONS:")
        print("  [a] Approve - Pattern is safe and useful")
        print("  [r] Reject - Pattern is dangerous or incorrect")
        print("  [s] Skip - Review later")
        print("  [d] Details - Show more information")
        print("  [q] Quit review session")

        while True:
            choice = input("\nYour choice: ").lower().strip()

            if choice == 'a':
                notes = input("Approval notes (optional): ").strip()
                self.service.approve_pattern(
                    pattern.pattern_id,
                    self.reviewer_name,
                    notes if notes else None
                )
                print(f"✅ Pattern {pattern.pattern_id} APPROVED")
                return True

            elif choice == 'r':
                reason = input("Rejection reason (required): ").strip()
                if not reason:
                    print("❌ Rejection reason is required")
                    continue

                self.service.reject_pattern(
                    pattern.pattern_id,
                    self.reviewer_name,
                    reason
                )
                print(f"❌ Pattern {pattern.pattern_id} REJECTED")
                return True

            elif choice == 's':
                print("⏭️  Skipped")
                return False

            elif choice == 'd':
                # Show additional details
                print(f"\nFull Pattern Data:")
                print(json.dumps(pattern.to_dict(), indent=2))
                continue

            elif choice == 'q':
                print("Exiting review session")
                sys.exit(0)

            else:
                print("Invalid choice. Please select a, r, s, d, or q.")

    def review_all_pending(self, limit: int = 20):
        """Review all pending patterns interactively."""
        patterns = self.service.get_pending_patterns(limit=limit)

        if not patterns:
            print("\n✅ No patterns pending review!")
            return

        print(f"\n📋 Found {len(patterns)} patterns pending review\n")

        reviewed = 0
        for i, pattern in enumerate(patterns, 1):
            print(f"\n--- Pattern {i}/{len(patterns)} ---")

            if self.review_pattern_interactive(pattern):
                reviewed += 1

        print(f"\n✅ Review session complete! Reviewed {reviewed}/{len(patterns)} patterns")

    def review_single_pattern(self, pattern_id: str):
        """Review a specific pattern by ID."""
        pattern = self.service.get_pattern_details(pattern_id)

        if not pattern:
            print(f"❌ Pattern {pattern_id} not found")
            sys.exit(1)

        self.review_pattern_interactive(pattern)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Interactive pattern review tool'
    )
    parser.add_argument(
        '--pattern-id',
        type=str,
        help='Review specific pattern by ID'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show review statistics only'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Maximum patterns to review (default: 20)'
    )
    parser.add_argument(
        '--reviewer',
        type=str,
        default='cli-reviewer',
        help='Reviewer name/ID (default: cli-reviewer)'
    )

    args = parser.parse_args()

    cli = PatternReviewCLI(reviewer_name=args.reviewer)

    if args.stats:
        cli.show_statistics()
    elif args.pattern_id:
        cli.review_single_pattern(args.pattern_id)
    else:
        cli.show_statistics()
        cli.review_all_pending(limit=args.limit)


if __name__ == '__main__':
    main()
```

Make executable:
```bash
chmod +x scripts/review_patterns.py
```

### Step 5: Create Tests (45 min)

Create new file: `scripts/tests/test_pattern_review.py`

```python
#!/usr/bin/env python3
"""
Tests for Pattern Review Service

Run with:
    cd /Users/Warmonger0/tac/tac-webbuilder
    python -m pytest scripts/tests/test_pattern_review.py -v
"""

import pytest
import json
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.server.services.pattern_review_service import (
    PatternReviewService,
    PatternReviewItem
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_path = temp_file.name
    temp_file.close()

    # Create schema
    conn = sqlite3.connect(temp_path)
    cursor = conn.cursor()

    # Pattern approvals table
    cursor.execute("""
        CREATE TABLE pattern_approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL,
            reviewed_by TEXT,
            reviewed_at TIMESTAMP,
            approval_notes TEXT,
            confidence_score REAL,
            occurrence_count INTEGER,
            estimated_savings_usd REAL,
            tool_sequence TEXT NOT NULL,
            pattern_context TEXT,
            example_sessions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Pattern review history table
    cursor.execute("""
        CREATE TABLE pattern_review_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id TEXT NOT NULL,
            action TEXT NOT NULL,
            reviewer TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    yield temp_path

    # Cleanup
    Path(temp_path).unlink()


@pytest.fixture
def service(temp_db, monkeypatch):
    """Create PatternReviewService with temp database."""
    def mock_get_connection():
        return sqlite3.connect(temp_db)

    monkeypatch.setattr(
        'app.server.services.pattern_review_service.get_connection',
        mock_get_connection
    )

    return PatternReviewService()


def test_get_pending_patterns_empty(service):
    """Test getting pending patterns when none exist."""
    patterns = service.get_pending_patterns()
    assert len(patterns) == 0


def test_get_pending_patterns(service, temp_db):
    """Test getting pending patterns."""
    # Insert test pattern
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pattern_approvals
            (pattern_id, status, tool_sequence, confidence_score,
             occurrence_count, estimated_savings_usd, example_sessions)
        VALUES (?, 'pending', ?, 0.95, 150, 1200.50, ?)
    """, (
        'test-pattern-1',
        'Read→Edit→Write',
        json.dumps(['session-1', 'session-2'])
    ))

    conn.commit()
    conn.close()

    # Get patterns
    patterns = service.get_pending_patterns()

    assert len(patterns) == 1
    assert patterns[0].pattern_id == 'test-pattern-1'
    assert patterns[0].status == 'pending'
    assert patterns[0].confidence_score == 0.95
    assert patterns[0].occurrence_count == 150
    assert len(patterns[0].example_sessions) == 2


def test_approve_pattern(service, temp_db):
    """Test approving a pattern."""
    # Insert test pattern
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pattern_approvals
            (pattern_id, status, tool_sequence, confidence_score,
             occurrence_count, estimated_savings_usd)
        VALUES ('test-pattern-1', 'pending', 'Read→Edit', 0.98, 200, 5000.0)
    """)

    conn.commit()
    conn.close()

    # Approve pattern
    result = service.approve_pattern(
        'test-pattern-1',
        'test-reviewer',
        'Looks good'
    )

    assert result is True

    # Verify status updated
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT status, reviewed_by, approval_notes FROM pattern_approvals WHERE pattern_id = ?",
        ('test-pattern-1',)
    )
    row = cursor.fetchone()

    assert row[0] == 'approved'
    assert row[1] == 'test-reviewer'
    assert row[2] == 'Looks good'

    # Verify history entry
    cursor.execute(
        "SELECT action, reviewer FROM pattern_review_history WHERE pattern_id = ?",
        ('test-pattern-1',)
    )
    history = cursor.fetchone()

    assert history[0] == 'approved'
    assert history[1] == 'test-reviewer'

    conn.close()


def test_reject_pattern(service, temp_db):
    """Test rejecting a pattern."""
    # Insert test pattern
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pattern_approvals
            (pattern_id, status, tool_sequence, confidence_score,
             occurrence_count, estimated_savings_usd)
        VALUES ('test-pattern-1', 'pending', 'Delete→Delete→Delete', 0.75, 50, 100.0)
    """)

    conn.commit()
    conn.close()

    # Reject pattern
    result = service.reject_pattern(
        'test-pattern-1',
        'test-reviewer',
        'Dangerous pattern - cascading deletes'
    )

    assert result is True

    # Verify status updated
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT status, reviewed_by, approval_notes FROM pattern_approvals WHERE pattern_id = ?",
        ('test-pattern-1',)
    )
    row = cursor.fetchone()

    assert row[0] == 'rejected'
    assert row[1] == 'test-reviewer'
    assert 'Dangerous pattern' in row[2]

    conn.close()


def test_get_review_statistics(service, temp_db):
    """Test getting review statistics."""
    # Insert test patterns with different statuses
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    patterns = [
        ('pattern-1', 'pending'),
        ('pattern-2', 'pending'),
        ('pattern-3', 'approved'),
        ('pattern-4', 'rejected'),
    ]

    for pattern_id, status in patterns:
        cursor.execute("""
            INSERT INTO pattern_approvals
                (pattern_id, status, tool_sequence, confidence_score,
                 occurrence_count, estimated_savings_usd)
            VALUES (?, ?, 'Test', 0.9, 100, 1000.0)
        """, (pattern_id, status))

    conn.commit()
    conn.close()

    # Get statistics
    stats = service.get_review_statistics()

    assert stats['total'] == 4
    assert stats['pending'] == 2
    assert stats['approved'] == 1
    assert stats['rejected'] == 1
```

### Step 6: Run Tests (15 min)

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Install pytest if needed
cd app/server && uv add --dev pytest

# Run tests
python -m pytest scripts/tests/test_pattern_review.py -v

# Expected output:
# test_get_pending_patterns_empty PASSED
# test_get_pending_patterns PASSED
# test_approve_pattern PASSED
# test_reject_pattern PASSED
# test_get_review_statistics PASSED
# ================== 5 passed ==================
```

### Step 7: Manual Integration Test (30 min)

Test the CLI tool with sample data:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Insert sample patterns for testing
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

# Test 1: Show statistics
cd ../..
python scripts/review_patterns.py --stats

# Expected output:
# PATTERN REVIEW STATISTICS
# Total Patterns: 3
#   ⏳ Pending Review: 3
#   ...

# Test 2: Review specific pattern
python scripts/review_patterns.py --pattern-id test-retry-pattern

# Should display pattern details and prompt for action

# Test 3: Interactive review session
python scripts/review_patterns.py

# Should show statistics, then interactively review each pattern
```

**Manual test checklist:**
- ✅ Statistics display correctly
- ✅ Pattern details are readable
- ✅ Approve action updates database
- ✅ Reject action updates database
- ✅ Skip action works
- ✅ Review history is tracked

### Step 8: Update Documentation (20 min)

**Update `docs/features/observability-and-logging.md`:**

Add section about Pattern Review:

```markdown
## Pattern Review Workflow

### Overview

Before detected patterns are automated, they go through a manual review process to ensure quality and safety.

**Review Workflow:**
1. **Pattern Detection** - System detects recurring tool sequences (Session 1.5)
2. **Automatic Classification** - High confidence patterns → auto-approve, Low confidence → auto-reject
3. **Manual Review** - Medium confidence patterns (95-99%) require human approval
4. **Automation** - Approved patterns generate automated workflows (Session 12+)

### Review Criteria

**Auto-Approve (>99% confidence):**
- Well-known patterns (Test-Fix-Retry)
- 200+ occurrences
- $5000+ estimated savings
- No destructive operations

**Manual Review Required (95-99% confidence):**
- Novel patterns
- 100-200 occurrences
- $1000-5000 estimated savings
- Mixed tool sequences

**Auto-Reject (<95% confidence):**
- Suspicious patterns (infinite loops, cascading deletes)
- <100 occurrences
- <$1000 estimated savings
- Destructive operations without validation

### Using the Review Tool

**Show statistics:**
```bash
python scripts/review_patterns.py --stats
```

**Review all pending patterns:**
```bash
python scripts/review_patterns.py
```

**Review specific pattern:**
```bash
python scripts/review_patterns.py --pattern-id <pattern-id>
```

**Review as specific user:**
```bash
python scripts/review_patterns.py --reviewer "Your Name"
```

### Review Actions

**Approve:**
- Pattern will be used to generate automated workflows
- Requires optional approval notes
- Tracks reviewer and timestamp

**Reject:**
- Pattern will NOT be automated
- Requires rejection reason (mandatory)
- Useful for dangerous patterns

**Skip:**
- Review later
- Pattern remains in pending queue

### Review History

All review actions are tracked in `pattern_review_history` table:
- Audit trail of all approvals/rejections
- Reviewer attribution
- Timestamp tracking
- Review notes preserved

### Integration with Automation

Approved patterns feed into:
- **Session 12:** Closed-loop ROI tracking
- **Session 13:** Confidence updating based on results
- **Future:** Automatic workflow generation from approved patterns
```

---

## Success Criteria

- ✅ pattern_approvals and pattern_review_history tables created
- ✅ PatternReviewService implements approve/reject/get_pending methods
- ✅ CLI tool provides interactive review interface
- ✅ All 5 tests passing
- ✅ Manual test confirms approve/reject/skip actions work
- ✅ Review history is tracked correctly
- ✅ Documentation updated with review workflow
- ✅ Statistics display correctly (pending, approved, rejected counts)

---

## Files Expected to Change

**Created (4):**
- `app/server/db/migrations/016_add_pattern_approvals.sql` (~80 lines)
- `app/server/services/pattern_review_service.py` (~200 lines)
- `scripts/review_patterns.py` (~400 lines)
- `scripts/tests/test_pattern_review.py` (~150 lines)

**Modified (2):**
- `app/server/core/pattern_detector.py` (add approval status checks, ~10 lines)
- `docs/features/observability-and-logging.md` (add Pattern Review section)

---

## Troubleshooting

### Migration Fails

```bash
# Check if tables already exist
sqlite3 app/server/db/workflow_history.db ".schema pattern_approvals"

# If exists, drop and recreate
sqlite3 app/server/db/workflow_history.db "DROP TABLE IF EXISTS pattern_approvals; DROP TABLE IF EXISTS pattern_review_history;"

# Re-run migration
sqlite3 app/server/db/workflow_history.db < app/server/db/migrations/016_add_pattern_approvals.sql
```

### Import Errors

```bash
# If "ModuleNotFoundError: No module named 'app'"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python scripts/review_patterns.py --stats
```

### Database Connection Issues

```bash
# Verify database exists
ls -lh app/server/db/workflow_history.db

# Check DB_TYPE environment variable
echo $DB_TYPE  # Should be "sqlite" or "postgresql"
```

### No Patterns to Review

```bash
# Check if patterns exist
sqlite3 app/server/db/workflow_history.db "SELECT COUNT(*) FROM pattern_approvals WHERE status='pending'"

# If 0, insert test patterns (see Step 7)
```

### CLI Tool Hangs

This usually indicates:
- Input prompt waiting (press Enter)
- Database connection issue (check file permissions)
- Missing table (run migration)

---

## Estimated Time

- Step 1 (Understand pattern detection): 20 min
- Step 2 (Create migration): 30 min
- Step 3 (Create service): 60 min
- Step 4 (Create CLI tool): 90-120 min
- Step 5 (Create tests): 45 min
- Step 6 (Run tests): 15 min
- Step 7 (Manual test): 30 min
- Step 8 (Documentation): 20 min

**Total: 3-4 hours**

---

## Session Completion Instructions

When you finish this session, provide a completion summary in this **EXACT FORMAT:**

```markdown
## ✅ Session 6 Complete - Pattern Review System

**Duration:** ~X hours
**Status:** Complete ✅
**Next:** Ready for Session 7 (Daily Pattern Analysis)

### What Was Done

1. **Pattern Approvals Database**
   - Created migration 016_add_pattern_approvals.sql
   - Tables: pattern_approvals, pattern_review_history
   - Indexes for efficient querying
   - Audit trail for all review actions

2. **Pattern Review Service**
   - Created pattern_review_service.py (~200 lines)
   - Methods: get_pending_patterns, approve_pattern, reject_pattern
   - PatternReviewItem dataclass for type safety
   - Review statistics and metrics

3. **CLI Review Tool**
   - Created review_patterns.py (~400 lines)
   - Interactive pattern review interface
   - Actions: approve, reject, skip, details, quit
   - Statistics display
   - Single pattern review mode

4. **Comprehensive Tests**
   - Created test_pattern_review.py (5 tests)
   - All tests passing ✅
   - Coverage: pending patterns, approve, reject, statistics

5. **Documentation Updated**
   - Added Pattern Review Workflow section to observability docs
   - Documented review criteria (auto-approve, manual review, auto-reject)
   - CLI usage examples and review actions

### Key Results

- ✅ Manual approval system for detected patterns
- ✅ Safety layer before automation (prevents bad patterns)
- ✅ Audit trail for all review decisions
- ✅ CLI tool for efficient batch review
- ✅ Statistics and metrics for review queue
- ✅ Foundation for semi-automatic workflow generation (Sessions 12-13)

### Files Changed

**Created (4):**
- app/server/db/migrations/016_add_pattern_approvals.sql
- app/server/services/pattern_review_service.py
- scripts/review_patterns.py
- scripts/tests/test_pattern_review.py

**Modified (2):**
- app/server/core/pattern_detector.py
- docs/features/observability-and-logging.md

### Test Results

```
python -m pytest scripts/tests/test_pattern_review.py -v
================== 5 passed ==================
```

### Example Usage

Review all pending patterns:
```bash
python scripts/review_patterns.py
```

Show statistics:
```bash
python scripts/review_patterns.py --stats
# PATTERN REVIEW STATISTICS
# Total Patterns: 15
#   ⏳ Pending Review: 8
#   ✅ Approved: 5
#   ❌ Rejected: 2
```

Review specific pattern:
```bash
python scripts/review_patterns.py --pattern-id test-retry-pattern
```

### Next Session

Session 7: Daily Pattern Analysis (2-3 hours)
- Batch script to analyze patterns daily
- Identify new patterns from hook events
- Auto-populate pattern_approvals table
- Email/Slack notifications for new patterns requiring review
```

---

## Next Session Prompt Instructions

After providing the completion summary above, create the prompt for **Session 7: Daily Pattern Analysis** using this template:

### Template for SESSION_7_PROMPT.md

```markdown
# Task: Implement Daily Pattern Analysis

## Context
I'm working on the tac-webbuilder project. The pattern detection system (Session 1.5) and pattern review system (Session 6) are in place, but there's no automated process to regularly analyze hook events and populate the review queue. This session implements a daily batch script that discovers new patterns, calculates metrics, and notifies reviewers of patterns requiring approval.

## Objective
Create a daily pattern analysis system that:
- Analyzes hook events from the last 24 hours
- Discovers new patterns using statistical analysis
- Calculates pattern metrics (confidence, frequency, savings)
- Auto-populates pattern_approvals table
- Sends notifications for patterns requiring review
- Runs as scheduled cron job or on-demand

[... continue with full session structure ...]
```

**Save this prompt as:** `/Users/Warmonger0/tac/tac-webbuilder/SESSION_7_PROMPT.md`

---

**Ready to copy into a new chat!**

Run `/prime` first, then paste this entire prompt.
