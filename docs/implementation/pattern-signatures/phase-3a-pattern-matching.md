# Phase 3A: Pattern Matching Foundation

**Duration:** 1-2 days
**Dependencies:** Phase 1 complete (patterns detected in database)
**Priority:** HIGH - Foundation for all routing logic
**Status:** Ready to implement

---

## Overview

Build and test the core pattern matching engine in isolation. This module is responsible for:
1. Querying active patterns from the database
2. Calculating similarity between user input and pattern triggers
3. Returning high-confidence matches for tool routing

**This phase does NOT include:**
- Tool execution (that's Phase 3C)
- Tool registration (that's Phase 3B)
- ADW integration (that's Phase 3C)

**Why separate this?** We can thoroughly test the matching logic before integrating with the complex ADW workflow system.

---

## Goals

- ✅ Build pattern matching module with query logic
- ✅ Implement similarity scoring algorithm
- ✅ Create standalone testing capabilities
- ✅ Write comprehensive unit tests
- ✅ Validate matching accuracy before integration

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  INPUT: "run the backend test suite"                     │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  match_input_to_pattern()                                │
│                                                           │
│  1. Query active patterns from database                  │
│     WHERE automation_status = 'active'                   │
│     AND confidence_score >= min_confidence               │
│                                                           │
│  2. For each pattern:                                    │
│     - Parse input_patterns JSON                          │
│     - Calculate similarity to user input                 │
│     - Combine with confidence score                      │
│                                                           │
│  3. Return best match if combined_score >= threshold     │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  OUTPUT: Pattern match with metadata                     │
│  {                                                        │
│    'pattern_signature': 'test:pytest:backend',           │
│    'confidence_score': 85.0,                             │
│    'similarity_score': 90.0,                             │
│    'combined_score': 87.5,                               │
│    'tool_name': 'run_test_workflow',                     │
│    'input_patterns': ['run tests', 'pytest', ...]        │
│  }                                                        │
└──────────────────────────────────────────────────────────┘
```

---

## Implementation

### File: `app/server/core/pattern_matcher.py`

Create this file with the pattern matching functions only:

```python
# app/server/core/pattern_matcher.py

"""
Pattern Matching Engine

Matches user input to known operation patterns for tool routing.
This module handles ONLY pattern matching - tool execution is separate.
"""

import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# PATTERN MATCHING
# ============================================================================

def match_input_to_pattern(
    nl_input: str,
    db_connection,
    min_confidence: float = 70.0
) -> Optional[Dict]:
    """
    Check if input matches a known active pattern.

    Args:
        nl_input: Natural language input from user
        db_connection: SQLite database connection
        min_confidence: Minimum confidence score required (default 70%)

    Returns:
        Pattern dict if match found, None otherwise
        {
            'id': 5,
            'pattern_signature': 'test:pytest:backend',
            'confidence_score': 85.0,
            'similarity_score': 90.0,
            'combined_score': 87.5,
            'tool_name': 'run_test_workflow',
            'tool_script_path': 'adws/adw_test_workflow.py',
            'avg_tokens_with_llm': 50000,
            'avg_tokens_with_tool': 2500,
            'input_patterns': ['run tests', 'test suite', 'pytest']
        }

    Example:
        >>> pattern = match_input_to_pattern(
        ...     "run the backend tests",
        ...     db_conn
        ... )
        >>> if pattern:
        ...     print(f"Matched: {pattern['pattern_signature']}")
    """
    cursor = db_connection.cursor()

    # Get all active patterns with their associated tools
    cursor.execute("""
        SELECT
            p.id,
            p.pattern_signature,
            p.confidence_score,
            p.typical_input_pattern,
            t.tool_name,
            t.script_path as tool_script_path,
            t.input_patterns,
            p.avg_tokens_with_llm,
            p.avg_tokens_with_tool
        FROM operation_patterns p
        LEFT JOIN adw_tools t ON t.tool_name = p.tool_name
        WHERE p.automation_status = 'active'
        AND p.confidence_score >= ?
        AND t.status = 'active'
    """, (min_confidence,))

    active_patterns = [dict(row) for row in cursor.fetchall()]

    if not active_patterns:
        logger.debug("[Matcher] No active patterns available")
        return None

    # Calculate similarity scores for each pattern
    matches = []

    for pattern in active_patterns:
        # Parse input patterns from JSON
        try:
            input_patterns = json.loads(pattern['input_patterns'])
        except (json.JSONDecodeError, TypeError):
            logger.warning(
                f"[Matcher] Invalid input_patterns for {pattern['pattern_signature']}"
            )
            input_patterns = []

        # Calculate how similar the user's input is to this pattern
        similarity = calculate_input_similarity(nl_input, input_patterns)

        if similarity > 0:
            # Combine pattern confidence with input similarity
            combined_score = (pattern['confidence_score'] + similarity) / 2

            matches.append({
                **pattern,
                'similarity_score': similarity,
                'combined_score': combined_score,
                'input_patterns': input_patterns  # Store parsed version
            })

    if not matches:
        logger.debug(f"[Matcher] No pattern matches for input: {nl_input[:50]}...")
        return None

    # Sort by combined score (confidence + similarity)
    matches.sort(key=lambda x: x['combined_score'], reverse=True)
    best_match = matches[0]

    # Only return if combined score meets threshold
    if best_match['combined_score'] >= min_confidence:
        logger.info(
            f"[Matcher] Pattern matched: {best_match['pattern_signature']} "
            f"(confidence: {best_match['confidence_score']:.1f}%, "
            f"similarity: {best_match['similarity_score']:.1f}%, "
            f"combined: {best_match['combined_score']:.1f}%)"
        )
        return best_match
    else:
        logger.debug(
            f"[Matcher] Best match {best_match['pattern_signature']} "
            f"below threshold ({best_match['combined_score']:.1f}% < {min_confidence}%)"
        )
        return None


def calculate_input_similarity(nl_input: str, input_patterns: List[str]) -> float:
    """
    Calculate similarity between input and pattern triggers.

    Uses simple keyword matching for now. Future enhancement: embeddings.

    Args:
        nl_input: User's natural language input
        input_patterns: List of trigger keywords for this pattern

    Returns:
        Similarity score 0-100

    Example:
        >>> calculate_input_similarity(
        ...     "run tests with pytest",
        ...     ["run", "tests", "pytest"]
        ... )
        100.0

        >>> calculate_input_similarity(
        ...     "run tests",
        ...     ["run", "tests", "pytest"]
        ... )
        66.7  # 2 out of 3 keywords matched
    """
    if not input_patterns:
        return 0.0

    nl_lower = nl_input.lower()

    # Count matching keywords
    matches = sum(1 for pattern in input_patterns if pattern.lower() in nl_lower)

    if matches == 0:
        return 0.0

    # Calculate score based on match percentage
    match_percentage = (matches / len(input_patterns)) * 100

    # Bonus if multiple keywords match (higher confidence)
    if matches >= 3:
        match_percentage = min(100.0, match_percentage * 1.2)
    elif matches >= 2:
        match_percentage = min(100.0, match_percentage * 1.1)

    return match_percentage


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_active_patterns(db_connection, min_confidence: float = 0.0) -> List[Dict]:
    """
    Get all active patterns from database.

    Useful for debugging and testing.

    Args:
        db_connection: SQLite database connection
        min_confidence: Optional minimum confidence filter

    Returns:
        List of pattern dicts
    """
    cursor = db_connection.cursor()

    cursor.execute("""
        SELECT
            p.id,
            p.pattern_signature,
            p.confidence_score,
            p.occurrence_count,
            p.automation_status,
            p.tool_name,
            t.input_patterns
        FROM operation_patterns p
        LEFT JOIN adw_tools t ON t.tool_name = p.tool_name
        WHERE p.automation_status = 'active'
        AND p.confidence_score >= ?
        ORDER BY p.confidence_score DESC, p.occurrence_count DESC
    """, (min_confidence,))

    patterns = []
    for row in cursor.fetchall():
        pattern = dict(row)
        # Parse input_patterns
        try:
            pattern['input_patterns'] = json.loads(pattern['input_patterns'] or '[]')
        except (json.JSONDecodeError, TypeError):
            pattern['input_patterns'] = []
        patterns.append(pattern)

    return patterns


def test_pattern_matching(db_connection, test_inputs: List[str]):
    """
    Test pattern matching against multiple inputs.

    Useful for validation and debugging.

    Args:
        db_connection: SQLite database connection
        test_inputs: List of test input strings

    Prints results to stdout.
    """
    print("=" * 60)
    print("PATTERN MATCHING TEST")
    print("=" * 60)
    print()

    for test_input in test_inputs:
        print(f"Input: '{test_input}'")

        result = match_input_to_pattern(test_input, db_connection)

        if result:
            print(f"  ✓ MATCH: {result['pattern_signature']}")
            print(f"    Confidence: {result['confidence_score']:.1f}%")
            print(f"    Similarity: {result['similarity_score']:.1f}%")
            print(f"    Combined: {result['combined_score']:.1f}%")
            print(f"    Tool: {result['tool_name']}")
        else:
            print("  ✗ NO MATCH")

        print()

    print("=" * 60)
```

---

## Testing Strategy

### Unit Tests

Create comprehensive unit tests for the pattern matching logic.

**File:** `app/server/tests/test_pattern_matcher.py`

```python
"""Unit tests for pattern matcher."""

import pytest
import json
import sqlite3
from core.pattern_matcher import (
    match_input_to_pattern,
    calculate_input_similarity,
    get_active_patterns,
)


@pytest.fixture
def mock_db():
    """Create mock database with test data."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE operation_patterns (
            id INTEGER PRIMARY KEY,
            pattern_signature TEXT,
            confidence_score REAL,
            typical_input_pattern TEXT,
            tool_name TEXT,
            automation_status TEXT,
            avg_tokens_with_llm INTEGER,
            avg_tokens_with_tool INTEGER,
            occurrence_count INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE adw_tools (
            tool_name TEXT PRIMARY KEY,
            script_path TEXT,
            input_patterns TEXT,
            status TEXT
        )
    """)

    # Insert test patterns
    cursor.execute("""
        INSERT INTO operation_patterns VALUES
        (1, 'test:pytest:backend', 85.0, '{}', 'run_test_workflow', 'active', 50000, 2500, 10),
        (2, 'build:typecheck:both', 90.0, '{}', 'run_build_workflow', 'active', 45000, 2000, 15),
        (3, 'test:vitest:frontend', 75.0, '{}', 'run_test_workflow', 'active', 48000, 2400, 8),
        (4, 'deploy:staging:all', 60.0, '{}', 'deploy_workflow', 'detected', 60000, 3000, 5)
    """)

    # Insert test tools
    cursor.execute("""
        INSERT INTO adw_tools VALUES
        ('run_test_workflow', 'adws/adw_test_workflow.py',
         '["run tests", "test suite", "pytest", "vitest", "execute tests"]', 'active'),
        ('run_build_workflow', 'adws/adw_build_workflow.py',
         '["build", "typecheck", "type check", "compile", "tsc"]', 'active'),
        ('deploy_workflow', 'adws/adw_deploy_workflow.py',
         '["deploy", "deployment", "staging"]', 'inactive')
    """)

    conn.commit()
    return conn


class TestInputSimilarity:
    """Test similarity calculation."""

    def test_exact_match_all_keywords(self):
        """Should return 100% for all keywords matching."""
        score = calculate_input_similarity(
            "run tests with pytest",
            ["run", "tests", "pytest"]
        )
        assert score == 100.0

    def test_partial_match(self):
        """Should return partial score for some keywords matching."""
        score = calculate_input_similarity(
            "run tests",
            ["run", "tests", "pytest"]
        )
        # 2/3 keywords = 66.7%, with bonus = ~73%
        assert 65 < score < 75

    def test_no_match(self):
        """Should return 0% for no keywords matching."""
        score = calculate_input_similarity(
            "deploy to production",
            ["run", "tests", "pytest"]
        )
        assert score == 0.0

    def test_case_insensitive(self):
        """Should match regardless of case."""
        score = calculate_input_similarity(
            "RUN TESTS WITH PYTEST",
            ["run", "tests", "pytest"]
        )
        assert score == 100.0

    def test_empty_patterns(self):
        """Should return 0% for empty pattern list."""
        score = calculate_input_similarity("anything", [])
        assert score == 0.0

    def test_bonus_for_multiple_matches(self):
        """Should give bonus for 3+ keyword matches."""
        score_2_matches = calculate_input_similarity(
            "run tests",
            ["run", "tests"]
        )
        score_3_matches = calculate_input_similarity(
            "run all tests with pytest",
            ["run", "tests", "pytest"]
        )
        # 3+ matches should get larger bonus
        assert score_3_matches > score_2_matches


class TestPatternMatching:
    """Test pattern matching logic."""

    def test_match_high_confidence_pattern(self, mock_db):
        """Should match pattern with high confidence."""
        result = match_input_to_pattern(
            "run the backend test suite with pytest",
            mock_db
        )

        assert result is not None
        assert result['pattern_signature'] == 'test:pytest:backend'
        assert result['tool_name'] == 'run_test_workflow'
        assert result['confidence_score'] == 85.0
        assert result['similarity_score'] > 0
        assert result['combined_score'] >= 70.0

    def test_match_build_pattern(self, mock_db):
        """Should match build/typecheck patterns."""
        result = match_input_to_pattern(
            "run typecheck on both frontend and backend",
            mock_db
        )

        assert result is not None
        assert result['pattern_signature'] == 'build:typecheck:both'
        assert result['tool_name'] == 'run_build_workflow'

    def test_no_match_low_confidence(self, mock_db):
        """Should not match if combined score below threshold."""
        result = match_input_to_pattern(
            "implement user authentication",
            mock_db,
            min_confidence=70.0
        )

        assert result is None

    def test_no_match_inactive_pattern(self, mock_db):
        """Should not match patterns with 'detected' status."""
        result = match_input_to_pattern(
            "deploy to staging",
            mock_db
        )

        # deploy:staging:all is 'detected', not 'active'
        assert result is None

    def test_respects_min_confidence_threshold(self, mock_db):
        """Should respect minimum confidence parameter."""
        # Lower threshold to 60%
        result = match_input_to_pattern(
            "run tests",
            mock_db,
            min_confidence=60.0
        )
        assert result is not None

        # Raise threshold to 95%
        result = match_input_to_pattern(
            "run tests",
            mock_db,
            min_confidence=95.0
        )
        assert result is None

    def test_returns_best_match(self, mock_db):
        """Should return highest scoring match."""
        result = match_input_to_pattern(
            "build and typecheck everything",
            mock_db
        )

        # Should match build pattern (90% confidence) over test (85%)
        assert result is not None
        assert result['pattern_signature'] == 'build:typecheck:both'
        assert result['confidence_score'] == 90.0


class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_active_patterns(self, mock_db):
        """Should return all active patterns."""
        patterns = get_active_patterns(mock_db)

        # Should return 3 active patterns (not the 'detected' one)
        assert len(patterns) == 3

        # Should be sorted by confidence score DESC
        assert patterns[0]['confidence_score'] >= patterns[1]['confidence_score']

        # Should have parsed input_patterns
        for pattern in patterns:
            assert isinstance(pattern['input_patterns'], list)

    def test_get_active_patterns_with_min_confidence(self, mock_db):
        """Should filter by minimum confidence."""
        patterns = get_active_patterns(mock_db, min_confidence=80.0)

        # Only 2 patterns have confidence >= 80%
        assert len(patterns) == 2
        assert all(p['confidence_score'] >= 80.0 for p in patterns)
```

### Standalone Test Script

Create a script to test pattern matching without full system integration.

**File:** `scripts/test_pattern_matching.py`

```python
#!/usr/bin/env python3
"""
Standalone test script for pattern matching.

Usage:
    python scripts/test_pattern_matching.py
"""

import sys
import sqlite3
from pathlib import Path

# Add app/server to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "app" / "server"))

from core.pattern_matcher import (
    match_input_to_pattern,
    get_active_patterns,
    test_pattern_matching,
)


def main():
    """Run pattern matching tests."""
    db_path = project_root / "app" / "server" / "db" / "workflow_history.db"

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    print("Pattern Matching Test Suite")
    print()

    # Show active patterns
    print("=" * 60)
    print("ACTIVE PATTERNS")
    print("=" * 60)
    print()

    patterns = get_active_patterns(conn)

    if not patterns:
        print("⚠️  No active patterns found!")
        print("   Run scripts/activate_patterns.py first")
        return 1

    for p in patterns:
        print(f"  • {p['pattern_signature']}")
        print(f"    Confidence: {p['confidence_score']:.1f}%")
        print(f"    Occurrences: {p['occurrence_count']}")
        print(f"    Tool: {p['tool_name']}")
        print(f"    Triggers: {', '.join(p['input_patterns'][:3])}...")
        print()

    # Test various inputs
    test_inputs = [
        "run the backend test suite",
        "execute all tests with pytest",
        "run frontend tests",
        "build and typecheck everything",
        "check types in backend",
        "run vitest for frontend",
        "implement user authentication",  # Should not match
        "deploy to staging",  # Should not match (inactive)
    ]

    test_pattern_matching(conn, test_inputs)

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Make executable:**
```bash
chmod +x scripts/test_pattern_matching.py
```

---

## Success Criteria

- [ ] ✅ `pattern_matcher.py` module created with matching functions
- [ ] ✅ Unit tests pass with 100% coverage of matching logic
- [ ] ✅ Standalone test script runs successfully
- [ ] ✅ Pattern matching returns correct results for test inputs:
  - "run tests" → matches test pattern
  - "typecheck" → matches build pattern
  - "implement feature" → no match (creative work)
- [ ] ✅ Similarity scoring validated:
  - All keywords match → 100%
  - Partial match → 50-90%
  - No match → 0%
- [ ] ✅ Combined scoring works (confidence + similarity)
- [ ] ✅ Min confidence threshold respected

---

## Testing Instructions

### 1. Run Unit Tests

```bash
cd app/server
uv run pytest tests/test_pattern_matcher.py -v
```

Expected output:
```
test_pattern_matcher.py::TestInputSimilarity::test_exact_match_all_keywords PASSED
test_pattern_matcher.py::TestInputSimilarity::test_partial_match PASSED
test_pattern_matcher.py::TestInputSimilarity::test_no_match PASSED
test_pattern_matcher.py::TestPatternMatching::test_match_high_confidence_pattern PASSED
test_pattern_matcher.py::TestPatternMatching::test_match_build_pattern PASSED
...

===================== 15 passed in 0.5s =====================
```

### 2. Run Standalone Test

```bash
python scripts/test_pattern_matching.py
```

Expected output:
```
Pattern Matching Test Suite

============================================================
ACTIVE PATTERNS
============================================================

  • test:pytest:backend
    Confidence: 85.0%
    Occurrences: 10
    Tool: run_test_workflow
    Triggers: run tests, test suite, pytest...

============================================================
PATTERN MATCHING TEST
============================================================

Input: 'run the backend test suite'
  ✓ MATCH: test:pytest:backend
    Confidence: 85.0%
    Similarity: 90.0%
    Combined: 87.5%
    Tool: run_test_workflow

Input: 'implement user authentication'
  ✗ NO MATCH

============================================================
```

### 3. Interactive Testing

```python
# Test in Python REPL
import sqlite3
from pathlib import Path
import sys

project_root = Path.cwd()
sys.path.insert(0, str(project_root / "app" / "server"))

from core.pattern_matcher import match_input_to_pattern

conn = sqlite3.connect("app/server/db/workflow_history.db")
conn.row_factory = sqlite3.Row

# Test matching
result = match_input_to_pattern("run all the tests", conn)
if result:
    print(f"Matched: {result['pattern_signature']}")
    print(f"Combined score: {result['combined_score']:.1f}%")

conn.close()
```

---

## Troubleshooting

### No Active Patterns Found

**Problem:** Test script shows "No active patterns found"

**Solution:**
```bash
# First ensure Phase 1 is complete
sqlite3 app/server/db/workflow_history.db "
SELECT COUNT(*) FROM operation_patterns;
"

# If 0, run Phase 1 backfill first
python scripts/backfill_pattern_learning.py

# Then activate patterns (Phase 3B)
python scripts/activate_patterns.py
```

### Low Similarity Scores

**Problem:** Patterns exist but similarity scores are low

**Solution:**
- Check input_patterns in adw_tools table
- Add more trigger keywords to patterns
- Verify keywords are present in test inputs

### Pattern Match But Tool is NULL

**Problem:** Pattern matches but tool_name is NULL

**Solution:**
```bash
# Link patterns to tools (Phase 3B)
python scripts/link_patterns_to_tools.py
```

---

## Next Steps

After completing Phase 3A:

1. **Verify matching accuracy** - Run all tests
2. **Review active patterns** - Ensure they're correctly linked
3. **Proceed to Phase 3B** - Tool registration and activation
4. **Note any issues** - Document edge cases found during testing

---

## Deliverables Checklist

- [ ] `app/server/core/pattern_matcher.py` created (~350 lines)
- [ ] `app/server/tests/test_pattern_matcher.py` created (~200 lines)
- [ ] `scripts/test_pattern_matching.py` created (~100 lines)
- [ ] All unit tests passing
- [ ] Standalone test script working
- [ ] Pattern matching validated with real data
- [ ] Documentation updated if edge cases found

**Total Lines of Code:** ~650 lines

---

## Dependencies for Next Phase

Phase 3B will need:
- ✅ This module working correctly
- ✅ Database with operation_patterns populated
- ❌ Tool registration scripts (created in 3B)
- ❌ Pattern activation logic (created in 3B)

Once Phase 3A is complete and tested, proceed to Phase 3B for tool registration.
