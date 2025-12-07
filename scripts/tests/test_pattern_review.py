#!/usr/bin/env python3
"""
Tests for Pattern Review Service

Run with:
    cd /Users/Warmonger0/tac/tac-webbuilder
    python -m pytest scripts/tests/test_pattern_review.py -v
    python -m pytest scripts/tests/test_pattern_review.py -v -k "test_approve"
"""

import json
import os
import sqlite3
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "app" / "server"))

from services.pattern_review_service import (
    PatternReviewItem,
    PatternReviewService,
)


@pytest.fixture
def temp_db():
    """Create temporary database with pattern_approvals schema."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_path = temp_file.name
    temp_file.close()

    # Create schema
    conn = sqlite3.connect(temp_path)
    cursor = conn.cursor()

    # Create pattern_approvals table
    cursor.execute("""
        CREATE TABLE pattern_approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'rejected', 'auto-approved', 'auto-rejected')),
            reviewed_by TEXT,
            reviewed_at TIMESTAMP,
            approval_notes TEXT,
            confidence_score REAL NOT NULL,
            occurrence_count INTEGER NOT NULL,
            estimated_savings_usd REAL NOT NULL,
            tool_sequence TEXT NOT NULL,
            pattern_context TEXT,
            example_sessions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create pattern_review_history table
    cursor.execute("""
        CREATE TABLE pattern_review_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id TEXT NOT NULL,
            action TEXT NOT NULL CHECK(action IN ('approved', 'rejected', 'flagged', 'commented')),
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
def mock_adapter(temp_db):
    """Create mock database adapter."""

    @contextmanager
    def get_connection():
        conn = sqlite3.connect(temp_db)
        try:
            yield conn
        finally:
            conn.close()

    adapter = MagicMock()
    adapter.get_connection = get_connection
    return adapter


@pytest.fixture
def service(mock_adapter):
    """Create service instance with mocked database."""
    with patch("services.pattern_review_service.get_database_adapter", return_value=mock_adapter):
        return PatternReviewService()


def test_get_pending_patterns_empty(service):
    """Test get_pending_patterns with empty database."""
    patterns = service.get_pending_patterns(limit=20)
    assert len(patterns) == 0


def test_get_pending_patterns(service, temp_db):
    """Test get_pending_patterns with test data."""
    # Insert test data
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO pattern_approvals
            (pattern_id, status, tool_sequence, confidence_score,
             occurrence_count, estimated_savings_usd, pattern_context, example_sessions)
        VALUES (?, 'pending', 'Read→Edit→Write', 0.95, 150, 1200.50, 'Test pattern 1', ?)
    """,
        ("test-pattern-1", json.dumps(["session-1", "session-2"])),
    )

    cursor.execute(
        """
        INSERT INTO pattern_approvals
            (pattern_id, status, tool_sequence, confidence_score,
             occurrence_count, estimated_savings_usd, pattern_context, example_sessions)
        VALUES (?, 'pending', 'Test→Fix→Test', 0.98, 200, 2500.0, 'Test pattern 2', ?)
    """,
        ("test-pattern-2", json.dumps(["session-3", "session-4"])),
    )

    cursor.execute(
        """
        INSERT INTO pattern_approvals
            (pattern_id, status, tool_sequence, confidence_score,
             occurrence_count, estimated_savings_usd, pattern_context, example_sessions)
        VALUES (?, 'approved', 'Lint→Fix→Commit', 0.92, 100, 800.0, 'Approved pattern', ?)
    """,
        ("test-pattern-3", json.dumps(["session-5"])),
    )

    conn.commit()
    conn.close()

    # Test
    patterns = service.get_pending_patterns(limit=20)

    assert len(patterns) == 2  # Only pending patterns

    # Verify ordering by impact score (confidence * occurrence * savings)
    # Pattern 2: 0.98 * 200 * 2500 = 490,000
    # Pattern 1: 0.95 * 150 * 1200.50 = 171,071.25
    assert patterns[0].pattern_id == "test-pattern-2"
    assert patterns[1].pattern_id == "test-pattern-1"

    # Verify data
    assert patterns[0].confidence_score == 0.98
    assert patterns[0].occurrence_count == 200
    assert patterns[0].estimated_savings_usd == 2500.0
    assert patterns[0].example_sessions == ["session-3", "session-4"]


def test_approve_pattern(service, temp_db):
    """Test approve_pattern updates status and creates history entry."""
    # Insert test pattern
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO pattern_approvals
            (pattern_id, status, tool_sequence, confidence_score,
             occurrence_count, estimated_savings_usd, example_sessions)
        VALUES (?, 'pending', 'Read→Edit→Write', 0.95, 150, 1200.50, ?)
    """,
        ("test-pattern-1", json.dumps(["session-1", "session-2"])),
    )
    conn.commit()
    conn.close()

    # Approve pattern
    result = service.approve_pattern(
        "test-pattern-1", "test-reviewer", "Looks good"
    )

    assert result is not None
    assert result.status == "approved"
    assert result.reviewed_by == "test-reviewer"
    assert result.approval_notes == "Looks good"
    assert result.reviewed_at is not None

    # Verify history entry
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM pattern_review_history WHERE pattern_id = ?",
        ("test-pattern-1",),
    )
    history = cursor.fetchone()
    conn.close()

    assert history is not None
    assert history[2] == "approved"  # action
    assert history[3] == "test-reviewer"  # reviewer
    assert history[4] == "Looks good"  # notes


def test_reject_pattern(service, temp_db):
    """Test reject_pattern updates status and creates history entry."""
    # Insert test pattern
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO pattern_approvals
            (pattern_id, status, tool_sequence, confidence_score,
             occurrence_count, estimated_savings_usd, example_sessions)
        VALUES (?, 'pending', 'Delete→Delete→Delete', 0.65, 15, 50.0, ?)
    """,
        ("test-dangerous-pattern", json.dumps(["session-6"])),
    )
    conn.commit()
    conn.close()

    # Reject pattern
    result = service.reject_pattern(
        "test-dangerous-pattern", "test-reviewer", "Too dangerous"
    )

    assert result is not None
    assert result.status == "rejected"
    assert result.reviewed_by == "test-reviewer"
    assert result.approval_notes == "REJECTED: Too dangerous"
    assert result.reviewed_at is not None

    # Verify history entry
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM pattern_review_history WHERE pattern_id = ?",
        ("test-dangerous-pattern",),
    )
    history = cursor.fetchone()
    conn.close()

    assert history is not None
    assert history[2] == "rejected"  # action
    assert history[3] == "test-reviewer"  # reviewer
    assert history[4] == "Too dangerous"  # notes


def test_get_review_statistics(service, temp_db):
    """Test get_review_statistics returns counts by status."""
    # Insert test data with various statuses
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # 3 pending
    for i in range(3):
        cursor.execute(
            """
            INSERT INTO pattern_approvals
                (pattern_id, status, tool_sequence, confidence_score,
                 occurrence_count, estimated_savings_usd, example_sessions)
            VALUES (?, 'pending', 'Test', 0.95, 100, 1000.0, ?)
        """,
            (f"pending-{i}", json.dumps(["session-1"])),
        )

    # 5 approved
    for i in range(5):
        cursor.execute(
            """
            INSERT INTO pattern_approvals
                (pattern_id, status, tool_sequence, confidence_score,
                 occurrence_count, estimated_savings_usd, example_sessions)
            VALUES (?, 'approved', 'Test', 0.95, 100, 1000.0, ?)
        """,
            (f"approved-{i}", json.dumps(["session-1"])),
        )

    # 2 rejected
    for i in range(2):
        cursor.execute(
            """
            INSERT INTO pattern_approvals
                (pattern_id, status, tool_sequence, confidence_score,
                 occurrence_count, estimated_savings_usd, example_sessions)
            VALUES (?, 'rejected', 'Test', 0.65, 50, 500.0, ?)
        """,
            (f"rejected-{i}", json.dumps(["session-1"])),
        )

    conn.commit()
    conn.close()

    # Test
    stats = service.get_review_statistics()

    assert stats["pending"] == 3
    assert stats["approved"] == 5
    assert stats["rejected"] == 2


def test_get_pattern_details(service, temp_db):
    """Test get_pattern_details retrieves specific pattern."""
    # Insert test pattern
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO pattern_approvals
            (pattern_id, status, tool_sequence, confidence_score,
             occurrence_count, estimated_savings_usd, pattern_context, example_sessions)
        VALUES (?, 'pending', 'Read→Edit→Write', 0.95, 150, 1200.50, 'Test context', ?)
    """,
        ("test-pattern-1", json.dumps(["session-1", "session-2"])),
    )
    conn.commit()
    conn.close()

    # Test
    pattern = service.get_pattern_details("test-pattern-1")

    assert pattern is not None
    assert pattern.pattern_id == "test-pattern-1"
    assert pattern.status == "pending"
    assert pattern.tool_sequence == "Read→Edit→Write"
    assert pattern.confidence_score == 0.95
    assert pattern.occurrence_count == 150
    assert pattern.estimated_savings_usd == 1200.50
    assert pattern.pattern_context == "Test context"
    assert pattern.example_sessions == ["session-1", "session-2"]


def test_get_pattern_details_not_found(service):
    """Test get_pattern_details returns None for non-existent pattern."""
    pattern = service.get_pattern_details("non-existent-pattern")
    assert pattern is None


def test_approve_pattern_not_found(service):
    """Test approve_pattern returns None for non-existent pattern."""
    result = service.approve_pattern("non-existent-pattern", "test-reviewer", "Notes")
    assert result is None


def test_reject_pattern_not_found(service):
    """Test reject_pattern returns None for non-existent pattern."""
    result = service.reject_pattern("non-existent-pattern", "test-reviewer", "Reason")
    assert result is None


def test_impact_score_calculation(service, temp_db):
    """Test impact score calculation property."""
    # Insert test pattern
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO pattern_approvals
            (pattern_id, status, tool_sequence, confidence_score,
             occurrence_count, estimated_savings_usd, example_sessions)
        VALUES (?, 'pending', 'Test', 0.95, 150, 1200.50, ?)
    """,
        ("test-pattern-1", json.dumps(["session-1"])),
    )
    conn.commit()
    conn.close()

    # Test
    pattern = service.get_pattern_details("test-pattern-1")
    expected_impact = 0.95 * 150 * 1200.50  # 171,071.25

    assert pattern.impact_score == pytest.approx(expected_impact, rel=1e-9)
