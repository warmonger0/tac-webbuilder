#!/usr/bin/env python3
"""
Tests for Daily Pattern Analysis System

Run with:
    cd /Users/Warmonger0/tac/tac-webbuilder
    POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=tac_dev_password_2024 DB_TYPE=postgresql python -m pytest scripts/tests/test_daily_pattern_analysis.py -v
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add paths for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "app" / "server"))
sys.path.insert(0, str(project_root / "scripts"))

from analyze_daily_patterns import (
    DailyPatternAnalyzer,
    PatternMetrics,
    ToolSequence,
)
from database import get_database_adapter


@pytest.fixture(scope="module")
def db_adapter():
    """Get database adapter for tests."""
    return get_database_adapter()


@pytest.fixture
def cleanup_test_patterns(db_adapter):
    """Clean up test patterns after each test."""
    yield

    # Cleanup: Remove test patterns
    with db_adapter.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM pattern_approvals WHERE pattern_id LIKE 'test-%'"
        )
        cursor.execute(
            "DELETE FROM hook_events WHERE session_id LIKE 'test-session-%'"
        )
        conn.commit()


@pytest.fixture
def analyzer():
    """Create DailyPatternAnalyzer instance for testing."""
    return DailyPatternAnalyzer(window_hours=24, min_occurrences=2)


@pytest.fixture
def setup_test_hook_events(db_adapter):
    """Insert test hook events for analysis."""
    with db_adapter.get_connection() as conn:
        cursor = conn.cursor()
        placeholder = db_adapter.placeholder()

        # Clear any existing test data
        cursor.execute("DELETE FROM hook_events WHERE session_id LIKE 'test-session-%'")

        # Session 1-5: Read→Edit→Write pattern (appears 5 times)
        for i in range(5):
            session_id = f"test-session-{i}"
            for idx, tool_name in enumerate(['Read', 'Edit', 'Write']):
                cursor.execute(
                    f"""
                    INSERT INTO hook_events
                        (event_id, event_type, tool_name, session_id, timestamp, payload)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder},
                            NOW() - INTERVAL '1 hour', {placeholder})
                """,
                    (
                        f"evt-{session_id}-{idx}-{tool_name}",
                        'PreToolUse',
                        tool_name,
                        session_id,
                        json.dumps({'tool': tool_name})
                    ),
                )

        # Session 6-8: Test→Fix→Test pattern (appears 3 times)
        for i in range(5, 8):
            session_id = f"test-session-{i}"
            for idx, tool_name in enumerate(['Test', 'Fix', 'Test']):
                cursor.execute(
                    f"""
                    INSERT INTO hook_events
                        (event_id, event_type, tool_name, session_id, timestamp, payload)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder},
                            NOW() - INTERVAL '2 hours', {placeholder})
                """,
                    (
                        f"evt-{session_id}-{idx}-{tool_name}",
                        'PreToolUse',
                        tool_name,
                        session_id,
                        json.dumps({'tool': tool_name})
                    ),
                )

        # Session 9: Single tool (should be filtered out - needs 2+ tools)
        cursor.execute(
            f"""
            INSERT INTO hook_events
                (event_id, event_type, tool_name, session_id, timestamp, payload)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder},
                    NOW() - INTERVAL '3 hours', {placeholder})
        """,
            (
                'evt-single-1',
                'PreToolUse',
                'Compile',
                'test-session-single',
                json.dumps({'tool': 'Compile'})
            ),
        )

        conn.commit()

    yield

    # Cleanup
    with db_adapter.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hook_events WHERE session_id LIKE 'test-session-%'")
        conn.commit()


def test_extract_tool_sequences(analyzer, setup_test_hook_events):
    """Test extraction of tool sequences from hook events."""
    sequences = analyzer.extract_tool_sequences()

    # Should have 8 valid sequences (sessions 0-7, excluding single-tool session)
    assert len(sequences) >= 8, f"Expected at least 8 sequences, got {len(sequences)}"

    # Check that sequences are properly formatted
    for seq in sequences:
        assert '→' in seq.tool_sequence
        assert len(seq.tool_names) >= 2  # Minimum 2 tools per sequence
        assert seq.session_id.startswith('test-session-')


def test_find_repeated_patterns(analyzer, setup_test_hook_events):
    """Test pattern grouping and repetition detection."""
    sequences = analyzer.extract_tool_sequences()
    patterns = analyzer.find_repeated_patterns(sequences)

    # Should find at least 2 patterns (Read→Edit→Write and Test→Fix→Test)
    assert len(patterns) >= 2, f"Expected at least 2 patterns, got {len(patterns)}"

    # Check that each pattern has minimum occurrences
    for pattern_seq, occurrences in patterns.items():
        assert len(occurrences) >= analyzer.min_occurrences


def test_calculate_confidence_high_occurrences(analyzer):
    """Test confidence score calculation with high occurrences."""
    # 100 occurrences out of 1000 sessions = 10% frequency
    confidence = analyzer.calculate_confidence(occurrences=100, total_sessions=1000)

    assert 0.0 <= confidence <= 1.0
    assert confidence >= 0.10  # At least 10% frequency
    # High occurrence boost should apply
    assert confidence > 0.10


def test_calculate_confidence_low_occurrences(analyzer):
    """Test confidence score calculation with low occurrences."""
    # 5 occurrences out of 100 sessions = 5% frequency
    confidence = analyzer.calculate_confidence(occurrences=5, total_sessions=100)

    assert 0.0 <= confidence <= 1.0
    assert confidence <= 0.10  # Should be close to 5%


def test_estimate_savings(analyzer):
    """Test cost savings estimation."""
    # Pattern with 3 tools, 10 occurrences
    savings = analyzer.estimate_savings(pattern='Read→Edit→Write', occurrences=10)

    # Should estimate some savings
    assert savings > 0.0
    assert isinstance(savings, float)

    # More occurrences should result in more savings
    savings_100 = analyzer.estimate_savings(pattern='Read→Edit→Write', occurrences=100)
    assert savings_100 > savings


def test_auto_classify_high_confidence(analyzer):
    """Test auto-classification for high-confidence, high-value patterns."""
    status = analyzer.auto_classify(
        pattern='Read→Edit→Write',
        confidence=0.995,  # >99%
        occurrences=250,   # >200
        savings=6000       # >$5000
    )

    assert status == 'auto-approved'


def test_auto_classify_low_confidence(analyzer):
    """Test auto-classification for low-confidence patterns."""
    status = analyzer.auto_classify(
        pattern='Read→Edit→Write',
        confidence=0.90,   # <95%
        occurrences=100,
        savings=1000
    )

    assert status == 'auto-rejected'


def test_auto_classify_pending(analyzer):
    """Test auto-classification for patterns requiring manual review."""
    status = analyzer.auto_classify(
        pattern='Read→Edit→Write',
        confidence=0.97,   # 95-99%
        occurrences=50,
        savings=1000
    )

    assert status == 'pending'


def test_auto_classify_destructive(analyzer):
    """Test that destructive patterns are auto-rejected."""
    status = analyzer.auto_classify(
        pattern='Read→Delete→Delete',
        confidence=0.99,   # High confidence
        occurrences=500,   # High occurrences
        savings=10000      # High savings
    )

    # Should be rejected due to destructive operation
    assert status == 'auto-rejected'


def test_full_analysis_workflow(analyzer, setup_test_hook_events, cleanup_test_patterns):
    """Test end-to-end analysis workflow."""
    # Run full analysis
    results = analyzer.analyze_patterns()

    # Should have processed some sessions and patterns
    assert results['total_sessions'] > 0
    assert results['patterns_found'] >= 0

    # Classification counts should sum to patterns_found
    total_classified = (
        results['auto_approved'] +
        results['pending'] +
        results['auto_rejected']
    )
    assert total_classified == results['patterns_found']

    # Should track new vs updated patterns
    assert results['new_patterns'] + results['updated_patterns'] == results['patterns_found']


def test_save_pattern_new(analyzer, cleanup_test_patterns):
    """Test saving a new pattern to database."""
    pattern = PatternMetrics(
        pattern_id='test-pattern-new-001',
        tool_sequence='Test→Build→Deploy',
        confidence_score=0.95,
        occurrence_count=10,
        estimated_savings_usd=500.0,
        pattern_context='Test pattern for unit testing',
        example_sessions=['session-1', 'session-2'],
        status='pending'
    )

    # Save pattern (should be new)
    is_new = analyzer.save_pattern(pattern)

    assert is_new is True

    # Verify pattern was saved
    saved = analyzer.service.get_pattern_details('test-pattern-new-001')
    assert saved is not None
    assert saved.tool_sequence == 'Test→Build→Deploy'
    assert saved.occurrence_count == 10


def test_save_pattern_update_existing(analyzer, cleanup_test_patterns):
    """Test updating an existing pattern's occurrence count."""
    # Create initial pattern
    pattern1 = PatternMetrics(
        pattern_id='test-pattern-update-001',
        tool_sequence='Read→Write',
        confidence_score=0.90,
        occurrence_count=5,
        estimated_savings_usd=100.0,
        pattern_context='Test pattern',
        example_sessions=['session-1'],
        status='pending'
    )

    # Save first time (should be new)
    is_new_first = analyzer.save_pattern(pattern1)
    assert is_new_first is True

    # Save again with more occurrences (should update)
    pattern2 = PatternMetrics(
        pattern_id='test-pattern-update-001',  # Same ID
        tool_sequence='Read→Write',
        confidence_score=0.92,
        occurrence_count=10,  # Additional occurrences
        estimated_savings_usd=200.0,
        pattern_context='Test pattern',
        example_sessions=['session-2'],
        status='pending'
    )

    is_new_second = analyzer.save_pattern(pattern2)
    assert is_new_second is False  # Should be update

    # Verify occurrence count was updated
    saved = analyzer.service.get_pattern_details('test-pattern-update-001')
    assert saved is not None
    assert saved.occurrence_count == 15  # 5 + 10


def test_calculate_metrics(analyzer):
    """Test metric calculation for a pattern."""
    # Create mock occurrences
    occurrences = [
        ToolSequence(
            session_id=f'session-{i}',
            tool_sequence='Read→Edit→Write',
            tool_names=['Read', 'Edit', 'Write'],
            event_count=3,
            first_seen='2025-01-01 10:00:00',
            last_seen='2025-01-01 10:05:00'
        )
        for i in range(10)
    ]

    all_sequences = occurrences + [
        ToolSequence(
            session_id='other-session',
            tool_sequence='Test→Deploy',
            tool_names=['Test', 'Deploy'],
            event_count=2,
            first_seen='2025-01-01 11:00:00',
            last_seen='2025-01-01 11:02:00'
        )
    ]

    metrics = analyzer.calculate_metrics(
        pattern_seq='Read→Edit→Write',
        occurrences=occurrences,
        all_sequences=all_sequences
    )

    # Verify metrics structure
    assert metrics.pattern_id is not None
    assert metrics.tool_sequence == 'Read→Edit→Write'
    assert 0.0 <= metrics.confidence_score <= 1.0
    assert metrics.occurrence_count == 10
    assert metrics.estimated_savings_usd > 0.0
    assert 'Read' in metrics.pattern_context
    assert len(metrics.example_sessions) <= 10  # Max 10 examples
    assert metrics.status in ['auto-approved', 'pending', 'auto-rejected']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
