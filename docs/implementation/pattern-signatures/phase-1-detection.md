# Phase 1: Pattern Detection Engine - Implementation Strategy

**Duration:** Week 1 (5-7 days)
**Priority:** HIGH - Foundation for all other phases
**Status:** Ready to implement

---

## 🎯 Quick Start

This phase has been **broken down into 4 sequential implementation guides** for easier execution:

1. **[Phase 1.1: Core Pattern Signatures](PHASE_1.1_CORE_PATTERN_SIGNATURES.md)** (1-2 days)
   - Pattern signature generation
   - Operation classification
   - Foundation for detection

2. **[Phase 1.2: Pattern Detection & Characteristics](PHASE_1.2_PATTERN_DETECTION.md)** (1-2 days)
   - Multi-pattern detection from workflows
   - Characteristic extraction
   - Confidence scoring logic

3. **[Phase 1.3: Database Integration](PHASE_1.3_DATABASE_INTEGRATION.md)** (1-2 days)
   - Database persistence
   - Statistics updates
   - Workflow sync integration

4. **[Phase 1.4: Backfill & Validation](PHASE_1.4_BACKFILL_AND_VALIDATION.md)** (1 day)
   - Historical data backfill
   - Validation tools
   - Pattern analysis utilities

**Start with Phase 1.1 and proceed sequentially.**

---

## Overview

Build the pattern detection engine that automatically identifies repetitive operations in workflows and tracks them in the `operation_patterns` table. This is the foundation of the learning loop.

---

## Goals

1. ✅ Detect and classify operation patterns from workflow data
2. ✅ Generate unique signatures for each pattern type
3. ✅ Track pattern occurrences in database
4. ✅ Calculate confidence scores and statistics
5. ✅ Backfill historical workflows to seed the system

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  WORKFLOW COMPLETES                                       │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  sync_workflow_history()                                  │
│  (existing function in workflow_history.py)               │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  NEW: Pattern Detection Pass                             │
│  for each workflow:                                       │
│    patterns = detect_patterns_in_workflow(workflow)       │
│    for pattern in patterns:                               │
│      record_pattern_occurrence(pattern, workflow_id)      │
└────────────────────┬─────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
┌──────────────────┐  ┌─────────────────────┐
│ operation_       │  │ pattern_            │
│ patterns         │  │ occurrences         │
│                  │  │                     │
│ • pattern_sig    │  │ • pattern_id        │
│ • occurrence_    │  │ • workflow_id       │
│   count++        │  │ • similarity_score  │
│ • avg_tokens     │  │                     │
│ • confidence     │  │                     │
└──────────────────┘  └─────────────────────┘
```

---

## Implementation Overview

This document provides a high-level overview. **For detailed implementation instructions, refer to the phase-specific documents above.**

The implementation has been modularized into focused components:

### Components

1. **pattern_signatures.py** (Phase 1.1)
   - Signature generation
   - Category/subcategory/target detection
   - Validation logic

2. **pattern_detector.py** (Phase 1.2)
   - Pattern detection from workflows
   - Characteristic extraction
   - Confidence score calculation

3. **pattern_persistence.py** (Phase 1.3)
   - Database operations
   - Pattern recording
   - Statistics updates

4. **Backfill & Analysis Tools** (Phase 1.4)
   - Historical data processing
   - Pattern analysis scripts
   - Validation utilities

---

## Quick Reference: Original Implementation Details

The sections below contain the original monolithic implementation for reference.
**For actual implementation, use the phase-specific documents linked above.**

---

### Original Step 1.1: Create Pattern Detector Module
**File:** `app/server/core/pattern_detector.py`

**Note:** This has been split into:
- `pattern_signatures.py` (Phase 1.1)
- `pattern_detector.py` (Phase 1.2)

**Dependencies:**
```python
import hashlib
import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)
```

**Implementation:**

```python
# app/server/core/pattern_detector.py

"""
Pattern Detection Engine for Out-Loop Coding

Automatically identifies repetitive operations in workflows and tracks them
for automation opportunities.
"""

import hashlib
import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# PATTERN SIGNATURE GENERATION
# ============================================================================

def extract_operation_signature(workflow: Dict) -> Optional[str]:
    """
    Generate unique signature for a workflow's primary operation.

    Signature format: "{category}:{subcategory}:{target}"

    Examples:
        - "test:pytest:backend"
        - "test:vitest:frontend"
        - "build:typecheck:both"
        - "build:compile:backend"
        - "format:prettier:all"
        - "git:diff:summary"

    Args:
        workflow: Workflow dictionary with nl_input, workflow_template, etc.

    Returns:
        Pattern signature string, or None if no clear pattern
    """
    nl_input = (workflow.get("nl_input") or "").lower()
    template = (workflow.get("workflow_template") or "").lower()

    # Category 1: Testing operations
    if any(kw in nl_input for kw in ["test", "pytest", "vitest", "jest", "run tests"]):
        subcategory = _detect_test_framework(nl_input)
        target = _detect_target(nl_input, workflow)
        return f"test:{subcategory}:{target}"

    # Category 2: Build operations
    if any(kw in nl_input for kw in ["build", "compile", "typecheck", "tsc"]):
        subcategory = _detect_build_type(nl_input)
        target = _detect_target(nl_input, workflow)
        return f"build:{subcategory}:{target}"

    # Category 3: Formatting
    if any(kw in nl_input for kw in ["format", "prettier", "black", "lint"]):
        subcategory = _detect_formatter(nl_input)
        return f"format:{subcategory}:all"

    # Category 4: Git operations
    if any(kw in nl_input for kw in ["git diff", "git status", "git log"]):
        subcategory = _detect_git_operation(nl_input)
        return f"git:{subcategory}:summary"

    # Category 5: Dependency operations
    if any(kw in nl_input for kw in ["update dependencies", "npm update", "pip install"]):
        subcategory = _detect_package_manager(nl_input)
        return f"deps:{subcategory}:update"

    # Category 6: Documentation
    if any(kw in nl_input for kw in ["generate docs", "update readme", "documentation"]):
        return "docs:generate:all"

    # No clear pattern detected
    return None


def _detect_test_framework(nl_input: str) -> str:
    """Detect which test framework is being used."""
    if "pytest" in nl_input or "py.test" in nl_input:
        return "pytest"
    elif "vitest" in nl_input:
        return "vitest"
    elif "jest" in nl_input:
        return "jest"
    elif "mocha" in nl_input:
        return "mocha"
    else:
        return "generic"


def _detect_build_type(nl_input: str) -> str:
    """Detect type of build operation."""
    if "typecheck" in nl_input or "tsc" in nl_input or "type check" in nl_input:
        return "typecheck"
    elif "compile" in nl_input:
        return "compile"
    elif "bundle" in nl_input or "webpack" in nl_input or "vite" in nl_input:
        return "bundle"
    else:
        return "build"


def _detect_target(nl_input: str, workflow: Dict) -> str:
    """Detect target of operation (backend, frontend, both)."""
    if "backend" in nl_input or "server" in nl_input or "api" in nl_input:
        return "backend"
    elif "frontend" in nl_input or "client" in nl_input or "ui" in nl_input:
        return "frontend"
    elif "both" in nl_input or "all" in nl_input:
        return "both"
    else:
        # Try to infer from workflow template
        template = (workflow.get("workflow_template") or "").lower()
        if "server" in template or "backend" in template:
            return "backend"
        elif "client" in template or "frontend" in template:
            return "frontend"
        else:
            return "all"


def _detect_formatter(nl_input: str) -> str:
    """Detect code formatter being used."""
    if "prettier" in nl_input:
        return "prettier"
    elif "black" in nl_input:
        return "black"
    elif "eslint" in nl_input:
        return "eslint"
    elif "ruff" in nl_input:
        return "ruff"
    else:
        return "generic"


def _detect_git_operation(nl_input: str) -> str:
    """Detect git operation type."""
    if "diff" in nl_input:
        return "diff"
    elif "status" in nl_input:
        return "status"
    elif "log" in nl_input:
        return "log"
    else:
        return "generic"


def _detect_package_manager(nl_input: str) -> str:
    """Detect package manager."""
    if "npm" in nl_input:
        return "npm"
    elif "pip" in nl_input or "python" in nl_input:
        return "pip"
    elif "bun" in nl_input:
        return "bun"
    elif "yarn" in nl_input:
        return "yarn"
    else:
        return "generic"


# ============================================================================
# PATTERN DETECTION FROM WORKFLOWS
# ============================================================================

def detect_patterns_in_workflow(workflow: Dict) -> List[str]:
    """
    Analyze a workflow and extract all operation patterns.

    Args:
        workflow: Complete workflow dictionary from workflow_history table

    Returns:
        List of pattern signatures found in this workflow
    """
    patterns = []

    # Primary pattern from nl_input
    primary = extract_operation_signature(workflow)
    if primary:
        patterns.append(primary)

    # Secondary patterns from error messages (indicates what was attempted)
    error_msg = workflow.get("error_message", "")
    if error_msg:
        error_patterns = _extract_patterns_from_errors(error_msg)
        patterns.extend(error_patterns)

    # Patterns from workflow template
    template_pattern = _extract_pattern_from_template(workflow.get("workflow_template"))
    if template_pattern and template_pattern not in patterns:
        patterns.append(template_pattern)

    return list(set(patterns))  # Remove duplicates


def _extract_patterns_from_errors(error_message: str) -> List[str]:
    """Extract operation patterns from error messages."""
    patterns = []
    error_lower = error_message.lower()

    # Test failures indicate test operation
    if "test failed" in error_lower or "pytest" in error_lower:
        patterns.append("test:pytest:backend")

    # Build failures indicate build operation
    if "type error" in error_lower or "typecheck" in error_lower:
        patterns.append("build:typecheck:backend")

    return patterns


def _extract_pattern_from_template(template: Optional[str]) -> Optional[str]:
    """Extract pattern from workflow template name."""
    if not template:
        return None

    template_lower = template.lower()

    if "test" in template_lower:
        return "test:generic:all"
    elif "build" in template_lower:
        return "build:generic:all"
    elif "plan" in template_lower:
        return None  # Planning workflows don't have automation potential

    return None


# ============================================================================
# PATTERN CHARACTERISTICS EXTRACTION
# ============================================================================

def extract_pattern_characteristics(workflow: Dict) -> Dict:
    """
    Extract characteristics that help identify patterns.

    Returns:
        {
            'input_length': 150,
            'keywords': ['test', 'pytest', 'backend'],
            'files_mentioned': ['tests/', 'app/server/'],
            'duration_range': 'medium',  # short, medium, long
            'complexity': 'simple'  # simple, medium, complex
        }
    """
    nl_input = workflow.get("nl_input", "")
    duration = workflow.get("duration_seconds", 0)
    error_count = workflow.get("error_count", 0)

    # Extract keywords
    keywords = _extract_keywords(nl_input)

    # Extract file paths mentioned
    files_mentioned = _extract_file_paths(nl_input)

    # Categorize duration
    if duration < 180:
        duration_range = "short"
    elif duration < 600:
        duration_range = "medium"
    else:
        duration_range = "long"

    # Determine complexity
    word_count = len(nl_input.split())
    if word_count < 50 and error_count < 3:
        complexity = "simple"
    elif word_count > 200 or error_count > 5:
        complexity = "complex"
    else:
        complexity = "medium"

    return {
        "input_length": len(nl_input),
        "keywords": keywords,
        "files_mentioned": files_mentioned,
        "duration_range": duration_range,
        "complexity": complexity,
        "error_count": error_count
    }


def _extract_keywords(text: str) -> List[str]:
    """Extract significant keywords from text."""
    # Common operation keywords
    operation_keywords = [
        "test", "pytest", "vitest", "build", "typecheck", "compile",
        "format", "lint", "update", "install", "deploy", "run"
    ]

    # Target keywords
    target_keywords = [
        "backend", "frontend", "server", "client", "api", "ui"
    ]

    found = []
    text_lower = text.lower()

    for keyword in operation_keywords + target_keywords:
        if keyword in text_lower:
            found.append(keyword)

    return found


def _extract_file_paths(text: str) -> List[str]:
    """Extract file paths or glob patterns from text."""
    # Look for common path patterns
    patterns = [
        r'(app/\w+/[\w/]*)',  # app/server/..., app/client/...
        r'(tests?/[\w/]*)',   # tests/..., test/...
        r'(src/[\w/]*)',      # src/...
        r'(\w+\.py)',         # *.py files
        r'(\w+\.ts)',         # *.ts files
    ]

    paths = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        paths.extend(matches)

    return list(set(paths))


# ============================================================================
# CONFIDENCE SCORE CALCULATION
# ============================================================================

def calculate_confidence_score(pattern_id: int, db_connection) -> float:
    """
    Calculate confidence score for a pattern based on:
    - Occurrence count (more occurrences = higher confidence)
    - Consistency of characteristics (similar workflows = higher confidence)
    - Success rate (fewer errors = higher confidence)

    Returns:
        Confidence score from 0.0 to 100.0
    """
    cursor = db_connection.cursor()

    # Get pattern and its occurrences
    cursor.execute("""
        SELECT
            p.occurrence_count,
            p.pattern_type,
            (SELECT COUNT(*) FROM pattern_occurrences WHERE pattern_id = p.id) as linked_count
        FROM operation_patterns p
        WHERE p.id = ?
    """, (pattern_id,))

    pattern_data = cursor.fetchone()
    if not pattern_data:
        return 0.0

    occurrence_count = pattern_data[0]
    linked_count = pattern_data[2]

    # Get characteristics of workflows with this pattern
    cursor.execute("""
        SELECT w.error_count, w.duration_seconds, w.retry_count
        FROM workflow_history w
        JOIN pattern_occurrences po ON po.workflow_id = w.workflow_id
        WHERE po.pattern_id = ?
    """, (pattern_id,))

    workflows = cursor.fetchall()
    if not workflows:
        return 10.0  # Base score for new patterns

    # Component 1: Occurrence frequency (0-40 points)
    # 1-2 occurrences = 10 points
    # 3-4 occurrences = 20 points
    # 5-9 occurrences = 30 points
    # 10+ occurrences = 40 points
    if occurrence_count >= 10:
        frequency_score = 40.0
    elif occurrence_count >= 5:
        frequency_score = 30.0
    elif occurrence_count >= 3:
        frequency_score = 20.0
    else:
        frequency_score = 10.0

    # Component 2: Consistency (0-30 points)
    # Calculate variance in duration and error rates
    durations = [w[1] for w in workflows if w[1]]
    error_counts = [w[0] for w in workflows if w[0] is not None]

    if durations:
        avg_duration = sum(durations) / len(durations)
        duration_variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations)
        # Low variance = high consistency
        if duration_variance < 100:  # Very consistent
            consistency_score = 30.0
        elif duration_variance < 1000:  # Moderately consistent
            consistency_score = 20.0
        else:  # High variance
            consistency_score = 10.0
    else:
        consistency_score = 15.0  # Default

    # Component 3: Success rate (0-30 points)
    # Patterns with low error rates are more reliable for automation
    avg_errors = sum(error_counts) / len(error_counts) if error_counts else 0
    avg_retries = sum(w[2] or 0 for w in workflows) / len(workflows)

    if avg_errors == 0 and avg_retries == 0:
        success_score = 30.0
    elif avg_errors < 1 and avg_retries < 2:
        success_score = 20.0
    elif avg_errors < 3:
        success_score = 10.0
    else:
        success_score = 5.0

    # Total confidence score
    total_score = frequency_score + consistency_score + success_score

    return min(100.0, max(0.0, total_score))


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def record_pattern_occurrence(
    pattern_signature: str,
    workflow: Dict,
    db_connection
) -> Tuple[int, bool]:
    """
    Record that we observed a pattern in a workflow.

    Creates or updates operation_patterns entry.
    Creates pattern_occurrences link.

    Args:
        pattern_signature: Pattern signature string
        workflow: Workflow dictionary
        db_connection: SQLite connection

    Returns:
        Tuple of (pattern_id, is_new_pattern)
    """
    cursor = db_connection.cursor()
    workflow_id = workflow.get("workflow_id")

    if not workflow_id:
        logger.warning(f"[Pattern] Workflow missing workflow_id, cannot record pattern")
        return None, False

    # Check if pattern exists
    cursor.execute("""
        SELECT id, occurrence_count, automation_status
        FROM operation_patterns
        WHERE pattern_signature = ?
    """, (pattern_signature,))

    existing = cursor.fetchone()

    if existing:
        pattern_id = existing[0]
        occurrence_count = existing[1]
        is_new = False

        # Update existing pattern
        cursor.execute("""
            UPDATE operation_patterns
            SET
                occurrence_count = occurrence_count + 1,
                last_seen = datetime('now')
            WHERE id = ?
        """, (pattern_id,))

        logger.debug(f"[Pattern] Updated pattern {pattern_signature} (count: {occurrence_count + 1})")

    else:
        # Create new pattern
        pattern_type = pattern_signature.split(":")[0]  # Extract category
        characteristics = extract_pattern_characteristics(workflow)

        cursor.execute("""
            INSERT INTO operation_patterns (
                pattern_signature,
                pattern_type,
                typical_input_pattern,
                occurrence_count,
                automation_status,
                confidence_score
            ) VALUES (?, ?, ?, 1, 'detected', 10.0)
        """, (
            pattern_signature,
            pattern_type,
            json.dumps(characteristics)
        ))

        pattern_id = cursor.lastrowid
        is_new = True

        logger.info(f"[Pattern] New pattern detected: {pattern_signature}")

    # Create pattern occurrence link
    cursor.execute("""
        INSERT OR IGNORE INTO pattern_occurrences (
            pattern_id,
            workflow_id,
            similarity_score,
            matched_characteristics
        ) VALUES (?, ?, ?, ?)
    """, (
        pattern_id,
        workflow_id,
        100.0,  # Perfect match since it came from this workflow
        json.dumps(extract_pattern_characteristics(workflow))
    ))

    db_connection.commit()

    # Update statistics
    update_pattern_statistics(pattern_id, workflow, db_connection)

    return pattern_id, is_new


def update_pattern_statistics(
    pattern_id: int,
    workflow: Dict,
    db_connection
):
    """
    Update pattern statistics based on new workflow data.

    Updates:
    - avg_tokens_with_llm (running average)
    - avg_cost_with_llm (running average)
    - confidence_score (recalculated)
    - potential_monthly_savings (estimated)
    """
    cursor = db_connection.cursor()

    # Get current statistics
    cursor.execute("""
        SELECT
            occurrence_count,
            avg_tokens_with_llm,
            avg_cost_with_llm
        FROM operation_patterns
        WHERE id = ?
    """, (pattern_id,))

    current = cursor.fetchone()
    if not current:
        return

    count = current[0]
    current_avg_tokens = current[1] or 0
    current_avg_cost = current[2] or 0.0

    # Get new workflow metrics
    new_tokens = workflow.get("total_tokens", 0)
    new_cost = workflow.get("actual_cost_total", 0.0)

    # Calculate running average
    if count == 1:
        # First occurrence, use as-is
        avg_tokens = new_tokens
        avg_cost = new_cost
    else:
        # Update running average
        avg_tokens = int((current_avg_tokens * (count - 1) + new_tokens) / count)
        avg_cost = (current_avg_cost * (count - 1) + new_cost) / count

    # Estimate tool cost (typically 95-97% reduction)
    estimated_tool_tokens = int(avg_tokens * 0.05)  # 5% of LLM tokens
    estimated_tool_cost = avg_cost * 0.05

    # Calculate potential monthly savings
    # Assume current frequency continues
    workflows_per_month = count  # Extrapolate based on observation period
    savings_per_use = avg_cost - estimated_tool_cost
    potential_monthly_savings = savings_per_use * workflows_per_month

    # Recalculate confidence score
    confidence = calculate_confidence_score(pattern_id, db_connection)

    # Update pattern
    cursor.execute("""
        UPDATE operation_patterns
        SET
            avg_tokens_with_llm = ?,
            avg_cost_with_llm = ?,
            avg_tokens_with_tool = ?,
            avg_cost_with_tool = ?,
            potential_monthly_savings = ?,
            confidence_score = ?
        WHERE id = ?
    """, (
        avg_tokens,
        avg_cost,
        estimated_tool_tokens,
        estimated_tool_cost,
        potential_monthly_savings,
        confidence,
        pattern_id
    ))

    db_connection.commit()

    logger.debug(f"[Pattern] Updated statistics for pattern {pattern_id}: "
                f"avg_cost=${avg_cost:.4f}, savings=${potential_monthly_savings:.2f}/mo, "
                f"confidence={confidence:.1f}%")


# ============================================================================
# MAIN DETECTION FUNCTION
# ============================================================================

def process_workflow_for_patterns(workflow: Dict, db_connection) -> Dict:
    """
    Main entry point for pattern detection on a single workflow.

    Args:
        workflow: Complete workflow dictionary
        db_connection: SQLite database connection

    Returns:
        {
            'patterns_detected': 2,
            'new_patterns': 1,
            'pattern_ids': [1, 5]
        }
    """
    patterns = detect_patterns_in_workflow(workflow)

    result = {
        "patterns_detected": len(patterns),
        "new_patterns": 0,
        "pattern_ids": []
    }

    for pattern_sig in patterns:
        pattern_id, is_new = record_pattern_occurrence(
            pattern_sig,
            workflow,
            db_connection
        )

        if pattern_id:
            result["pattern_ids"].append(pattern_id)
            if is_new:
                result["new_patterns"] += 1

    return result
```

---

### Step 1.2: Integrate into Workflow Sync
**File:** `app/server/core/workflow_history.py`

**Modify the `sync_workflow_history()` function:**

```python
# Add import at top of file
from .pattern_detector import process_workflow_for_patterns

# In sync_workflow_history() function, add after existing sync logic:

def sync_workflow_history() -> int:
    # ... existing code ...

    # Phase 3E: Second pass - Calculate similar workflows
    # ... existing similar workflow code ...

    # NEW: Pattern Learning Pass
    logger.info("[SYNC] Phase: Pattern Learning")
    try:
        from .pattern_detector import process_workflow_for_patterns

        patterns_detected = 0
        new_patterns = 0

        with get_db_connection() as conn:
            for workflow in all_workflows:
                try:
                    result = process_workflow_for_patterns(workflow, conn)
                    patterns_detected += result['patterns_detected']
                    new_patterns += result['new_patterns']

                    if result['patterns_detected'] > 0:
                        logger.debug(
                            f"[SYNC] Workflow {workflow['adw_id']}: "
                            f"detected {result['patterns_detected']} pattern(s)"
                        )

                except Exception as e:
                    logger.warning(
                        f"[SYNC] Failed to process patterns for {workflow['adw_id']}: {e}"
                    )

        logger.info(
            f"[SYNC] Pattern learning complete: "
            f"{patterns_detected} patterns detected, {new_patterns} new"
        )

    except Exception as e:
        logger.error(f"[SYNC] Pattern learning failed: {e}")
        # Don't fail entire sync if pattern learning fails

    return synced_count
```

---

### Step 1.3: Create Backfill Script
**File:** `scripts/backfill_pattern_learning.py`

```python
#!/usr/bin/env python3
"""
Backfill pattern learning with historical workflow data.

This script analyzes all existing workflows in the database and
populates the operation_patterns table.
"""

import sys
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "app" / "server"))

from core.pattern_detector import process_workflow_for_patterns


def backfill_patterns():
    """Analyze all historical workflows for patterns."""
    db_path = project_root / "app" / "server" / "db" / "workflow_history.db"

    print(f"📚 Backfilling pattern learning from: {db_path}")
    print()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all workflows
    cursor.execute("""
        SELECT * FROM workflow_history
        WHERE status IN ('completed', 'failed')
        ORDER BY created_at ASC
    """)

    workflows = [dict(row) for row in cursor.fetchall()]
    total = len(workflows)

    print(f"Found {total} workflows to analyze")
    print()

    patterns_detected = 0
    new_patterns = 0
    processed = 0

    for i, workflow in enumerate(workflows, 1):
        # Parse JSON fields
        if workflow.get('cost_breakdown'):
            import json
            try:
                workflow['cost_breakdown'] = json.loads(workflow['cost_breakdown'])
            except:
                pass

        try:
            result = process_workflow_for_patterns(workflow, conn)
            patterns_detected += result['patterns_detected']
            new_patterns += result['new_patterns']
            processed += 1

            if result['patterns_detected'] > 0:
                print(
                    f"[{i}/{total}] {workflow['adw_id']}: "
                    f"✓ {result['patterns_detected']} pattern(s)"
                )

        except Exception as e:
            print(f"[{i}/{total}] {workflow['adw_id']}: ✗ Error: {e}")

    conn.close()

    print()
    print("=" * 60)
    print(f"✅ Backfill complete!")
    print(f"   Workflows processed: {processed}/{total}")
    print(f"   Patterns detected: {patterns_detected}")
    print(f"   New patterns created: {new_patterns}")
    print("=" * 60)

    # Show top patterns
    print()
    print("Top 10 patterns by occurrence:")
    print()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            pattern_signature,
            occurrence_count,
            confidence_score,
            avg_cost_with_llm,
            potential_monthly_savings,
            automation_status
        FROM operation_patterns
        ORDER BY occurrence_count DESC
        LIMIT 10
    """)

    for i, row in enumerate(cursor.fetchall(), 1):
        print(
            f"{i:2}. {row['pattern_signature']:30} "
            f"| Count: {row['occurrence_count']:3} "
            f"| Confidence: {row['confidence_score']:5.1f}% "
            f"| Savings: ${row['potential_monthly_savings']:6.2f}/mo "
            f"| Status: {row['automation_status']}"
        )

    conn.close()


if __name__ == "__main__":
    backfill_patterns()
```

**Make executable:**
```bash
chmod +x scripts/backfill_pattern_learning.py
```

---

### Step 1.4: Create Unit Tests
**File:** `app/server/tests/test_pattern_detector.py`

```python
"""
Unit tests for pattern detection engine.
"""

import pytest
from core.pattern_detector import (
    extract_operation_signature,
    detect_patterns_in_workflow,
    extract_pattern_characteristics,
    calculate_confidence_score,
)


class TestOperationSignatureExtraction:
    """Test pattern signature generation."""

    def test_test_operation_pytest_backend(self):
        workflow = {
            "nl_input": "Run the backend test suite with pytest",
            "workflow_template": "adw_test_iso"
        }
        sig = extract_operation_signature(workflow)
        assert sig == "test:pytest:backend"

    def test_test_operation_vitest_frontend(self):
        workflow = {
            "nl_input": "Run frontend tests using vitest",
            "workflow_template": "adw_test_iso"
        }
        sig = extract_operation_signature(workflow)
        assert sig == "test:vitest:frontend"

    def test_build_operation_typecheck(self):
        workflow = {
            "nl_input": "Run typecheck on the entire project",
            "workflow_template": "adw_build_iso"
        }
        sig = extract_operation_signature(workflow)
        assert sig == "build:typecheck:all"

    def test_format_operation(self):
        workflow = {
            "nl_input": "Format all code with prettier",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "format:prettier:all"

    def test_no_clear_pattern(self):
        workflow = {
            "nl_input": "Implement user authentication with JWT",
            "workflow_template": "adw_plan_iso"
        }
        sig = extract_operation_signature(workflow)
        assert sig is None  # Complex implementation, not a simple operation


class TestPatternDetection:
    """Test multi-pattern detection from workflows."""

    def test_detect_multiple_patterns(self):
        workflow = {
            "nl_input": "Run tests and build",
            "workflow_template": "adw_sdlc_iso",
            "error_message": None
        }
        patterns = detect_patterns_in_workflow(workflow)
        assert "test:generic:all" in patterns

    def test_detect_from_error_message(self):
        workflow = {
            "nl_input": "Deploy to production",
            "workflow_template": "adw_deploy",
            "error_message": "pytest failed: 3 tests failed in test_api.py"
        }
        patterns = detect_patterns_in_workflow(workflow)
        assert "test:pytest:backend" in patterns


class TestCharacteristicExtraction:
    """Test extraction of pattern characteristics."""

    def test_extract_simple_characteristics(self):
        workflow = {
            "nl_input": "Run pytest tests",
            "duration_seconds": 120,
            "error_count": 0
        }
        chars = extract_pattern_characteristics(workflow)

        assert chars["complexity"] == "simple"
        assert chars["duration_range"] == "short"
        assert "test" in chars["keywords"]
        assert "pytest" in chars["keywords"]

    def test_extract_complex_characteristics(self):
        workflow = {
            "nl_input": "Implement comprehensive authentication system with JWT tokens, refresh tokens, role-based access control, and multi-factor authentication. Create database migrations, API endpoints, frontend UI components, integration tests, and documentation.",
            "duration_seconds": 1200,
            "error_count": 8
        }
        chars = extract_pattern_characteristics(workflow)

        assert chars["complexity"] == "complex"
        assert chars["duration_range"] == "long"
        assert chars["input_length"] > 200


@pytest.fixture
def mock_db():
    """Create in-memory SQLite database for testing."""
    import sqlite3

    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE operation_patterns (
            id INTEGER PRIMARY KEY,
            pattern_signature TEXT UNIQUE,
            pattern_type TEXT,
            occurrence_count INTEGER DEFAULT 1,
            avg_tokens_with_llm INTEGER DEFAULT 0,
            avg_cost_with_llm REAL DEFAULT 0.0,
            typical_input_pattern TEXT,
            automation_status TEXT DEFAULT 'detected',
            confidence_score REAL DEFAULT 10.0
        )
    """)

    cursor.execute("""
        CREATE TABLE pattern_occurrences (
            id INTEGER PRIMARY KEY,
            pattern_id INTEGER,
            workflow_id TEXT,
            similarity_score REAL,
            matched_characteristics TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE workflow_history (
            workflow_id TEXT PRIMARY KEY,
            error_count INTEGER,
            duration_seconds INTEGER,
            retry_count INTEGER
        )
    """)

    conn.commit()
    return conn


class TestConfidenceScore:
    """Test confidence score calculation."""

    def test_new_pattern_low_confidence(self, mock_db):
        cursor = mock_db.cursor()

        # Create pattern with 1 occurrence
        cursor.execute("""
            INSERT INTO operation_patterns (id, pattern_signature, occurrence_count)
            VALUES (1, 'test:pytest:backend', 1)
        """)
        mock_db.commit()

        score = calculate_confidence_score(1, mock_db)
        assert 10 <= score <= 30  # Low confidence for new patterns

    def test_frequent_pattern_high_confidence(self, mock_db):
        cursor = mock_db.cursor()

        # Create pattern with 10 occurrences
        cursor.execute("""
            INSERT INTO operation_patterns (id, pattern_signature, occurrence_count)
            VALUES (1, 'test:pytest:backend', 10)
        """)

        # Create pattern occurrences with consistent metrics
        cursor.execute("""
            INSERT INTO workflow_history (workflow_id, error_count, duration_seconds, retry_count)
            VALUES
                ('wf-1', 0, 120, 0),
                ('wf-2', 0, 125, 0),
                ('wf-3', 0, 118, 0),
                ('wf-4', 1, 130, 0),
                ('wf-5', 0, 122, 0)
        """)

        for i in range(1, 6):
            cursor.execute("""
                INSERT INTO pattern_occurrences (pattern_id, workflow_id)
                VALUES (1, ?)
            """, (f'wf-{i}',))

        mock_db.commit()

        score = calculate_confidence_score(1, mock_db)
        assert score >= 70  # High confidence for frequent, consistent patterns
```

---

## Testing Strategy

### Unit Tests
```bash
cd app/server
pytest tests/test_pattern_detector.py -v
```

### Integration Test
```bash
# 1. Run backfill on existing data
python scripts/backfill_pattern_learning.py

# 2. Verify patterns created
sqlite3 app/server/db/workflow_history.db "
SELECT
    pattern_signature,
    occurrence_count,
    confidence_score,
    automation_status
FROM operation_patterns
ORDER BY occurrence_count DESC;
"

# 3. Check pattern occurrences
sqlite3 app/server/db/workflow_history.db "
SELECT COUNT(*) as total_occurrences
FROM pattern_occurrences;
"

# 4. Test sync integration
python -c "
from app.server.core.workflow_history import sync_workflow_history
sync_workflow_history()
"
```

### Manual Verification
```bash
# Check top patterns
sqlite3 app/server/db/workflow_history.db "
SELECT * FROM v_high_value_patterns LIMIT 10;
"

# Verify pattern characteristics
sqlite3 app/server/db/workflow_history.db "
SELECT
    pattern_signature,
    typical_input_pattern
FROM operation_patterns
WHERE pattern_signature = 'test:pytest:backend';
"
```

---

## Success Criteria

- [ ] ✅ **Unit tests pass** - All test_pattern_detector.py tests green
- [ ] ✅ **Backfill succeeds** - Historical workflows analyzed without errors
- [ ] ✅ **Patterns created** - At least 5 distinct patterns in database
- [ ] ✅ **Confidence scores calculated** - Scores range from 10-100
- [ ] ✅ **Sync integration works** - New workflows automatically tracked
- [ ] ✅ **No performance impact** - Sync time increase <10%

---

## Deliverables

1. ✅ `app/server/core/pattern_detector.py` (500+ lines)
2. ✅ Modified `app/server/core/workflow_history.py` (~50 lines added)
3. ✅ `scripts/backfill_pattern_learning.py` (150+ lines)
4. ✅ `app/server/tests/test_pattern_detector.py` (200+ lines)
5. ✅ Documentation updates

**Total Lines of Code:** ~900 lines

---

## Next Steps (After Completion)

1. Run backfill script to seed database
2. Monitor pattern detection for 1 week
3. Review top patterns for accuracy
4. Adjust signature detection heuristics if needed
5. Proceed to Phase 2: Context Efficiency Analysis

---

## Troubleshooting

**Issue:** No patterns detected
- Check that workflows have `nl_input` field populated
- Review `extract_operation_signature()` keywords
- Run with debug logging enabled

**Issue:** Duplicate patterns
- Check `pattern_signature` uniqueness constraint
- Verify pattern signature format is consistent

**Issue:** Low confidence scores
- Need more occurrences (wait for more workflows)
- Check if workflows have consistent characteristics

**Issue:** Backfill script slow
- Normal for large databases (>100 workflows)
- Consider batching commits (currently commits per workflow)
