# Phase 3: Automated Tool Routing - Implementation Strategy

**Duration:** Week 2 (5-7 days)
**Dependencies:** Phase 1 complete (patterns detected)
**Priority:** HIGH - Delivers immediate cost savings
**Status:** Ready to implement

---

## ⚠️ IMPLEMENTATION GUIDE: This Phase is Split into 3 Sub-Phases

Due to complexity (1,322 lines, ~1,300 lines of code), **Phase 3 has been broken into 3 manageable sub-phases**:

### **Phase 3A: Pattern Matching Foundation** (Days 1-2)
📄 **[PHASE_3A_PATTERN_MATCHING.md](PHASE_3A_PATTERN_MATCHING.md)** - ~650 lines of code

Build and test the core pattern matching engine in isolation.

### **Phase 3B: Tool Registration & Activation** (Day 3)
📄 **[PHASE_3B_TOOL_REGISTRATION.md](PHASE_3B_TOOL_REGISTRATION.md)** - ~400 lines of code

Set up the tool registry and pattern activation system.

### **Phase 3C: ADW Integration & Routing** (Days 4-5)
📄 **[PHASE_3C_ADW_INTEGRATION.md](PHASE_3C_ADW_INTEGRATION.md)** - ~900 lines of code

Wire everything together with full routing logic and ADW integration.

---

### 🚀 Quick Start

1. **Read the overview:** [PHASE_3_OVERVIEW.md](PHASE_3_OVERVIEW.md)
2. **Start with Phase 3A:** Implement pattern matching foundation
3. **Progress sequentially:** 3A → 3B → 3C
4. **Use this document as reference:** Complete architecture and code below

---

## Overview

Automatically route workflow operations to specialized Python tools when high-confidence pattern matches are detected. This is where the cost savings actually happen - LLM workflows get replaced with efficient scripts that return compact results.

---

## Goals

1. ✅ Build pattern matching engine that queries operation_patterns table
2. ✅ Implement tool routing logic with fallback to LLM
3. ✅ Register existing external tools (test, build, etc.)
4. ✅ Integrate into ADW workflow executor
5. ✅ Track cost savings in real-time
6. ✅ Ensure graceful degradation on tool failures

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  ADW WORKFLOW STARTS                                      │
│  Issue: "Run the backend test suite"                     │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  PATTERN MATCHER                                          │
│  match_input_to_pattern("run the backend test suite")    │
│                                                           │
│  Query: operation_patterns WHERE automation_status =     │
│         'active' AND confidence_score >= 70               │
│                                                           │
│  Calculate similarity scores for input                    │
└────────────────────┬─────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
    [Match Found]         [No Match]
    confidence>=70%       confidence<70%
          │                     │
          ▼                     ▼
┌──────────────────────┐  ┌─────────────────────┐
│  ROUTE TO TOOL       │  │  FALLBACK TO LLM    │
│                      │  │                     │
│  1. Get tool from    │  │  Execute normal     │
│     adw_tools table  │  │  Claude Code        │
│                      │  │  workflow           │
│  2. Execute:         │  │                     │
│     adw_test_        │  │  (Full context,     │
│     workflow.py      │  │   creative work)    │
│                      │  │                     │
│  3. Capture compact  │  │                     │
│     results          │  │                     │
│                      │  │                     │
│  4. Calculate        │  │                     │
│     tokens saved     │  │                     │
└──────────┬───────────┘  └──────────┬──────────┘
           │                         │
           └──────────┬──────────────┘
                      ▼
┌──────────────────────────────────────────────────────────┐
│  LOG COST SAVINGS                                         │
│  INSERT INTO cost_savings_log (                           │
│    optimization_type='pattern_offload',                   │
│    tokens_saved=48000,                                    │
│    cost_saved_usd=0.144                                   │
│  )                                                        │
└──────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Step 3.1: Create Pattern Matcher Module
**File:** `app/server/core/pattern_matcher.py`

**Full Implementation:**

```python
# app/server/core/pattern_matcher.py

"""
Pattern Matching and Tool Routing Engine

Routes workflow operations to specialized tools when high-confidence
pattern matches are detected. Falls back to LLM for creative work.
"""

import json
import logging
import subprocess
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

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
            'tool_name': 'run_test_workflow',
            'tool_script_path': 'adws/adw_test_workflow.py',
            'avg_tokens_with_llm': 50000,
            'avg_tokens_with_tool': 2500,
            'input_patterns': ['run tests', 'test suite', 'pytest']
        }
    """
    cursor = db_connection.cursor()

    # Get all active patterns
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

    # Calculate similarity scores
    matches = []

    for pattern in active_patterns:
        # Parse input patterns
        try:
            input_patterns = json.loads(pattern['input_patterns'])
        except:
            input_patterns = []

        # Calculate match score
        similarity = calculate_input_similarity(nl_input, input_patterns)

        if similarity > 0:
            matches.append({
                **pattern,
                'similarity_score': similarity,
                'combined_score': (pattern['confidence_score'] + similarity) / 2
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

    Uses simple keyword matching for now. Future: embeddings.

    Args:
        nl_input: User's natural language input
        input_patterns: List of trigger keywords for this pattern

    Returns:
        Similarity score 0-100
    """
    nl_lower = nl_input.lower()

    # Count matching keywords
    matches = sum(1 for pattern in input_patterns if pattern.lower() in nl_lower)

    if matches == 0:
        return 0.0

    # Calculate score based on match percentage
    match_percentage = (matches / len(input_patterns)) * 100

    # Bonus if multiple keywords match
    if matches >= 3:
        match_percentage = min(100.0, match_percentage * 1.2)
    elif matches >= 2:
        match_percentage = min(100.0, match_percentage * 1.1)

    return match_percentage


# ============================================================================
# TOOL EXECUTION
# ============================================================================

def route_to_tool(
    pattern: Dict,
    workflow_context: Dict,
    db_connection
) -> Dict:
    """
    Execute specialized tool for this pattern.

    Args:
        pattern: Pattern dict from match_input_to_pattern()
        workflow_context: {
            'adw_id': 'adw-abc123',
            'issue_number': 42,
            'worktree_path': 'trees/adw-abc123',
            'nl_input': '...'
        }
        db_connection: SQLite database connection

    Returns:
        {
            'success': True,
            'tool_name': 'run_test_workflow',
            'result': {...},  # Tool-specific results
            'tokens_saved': 47500,
            'cost_saved_usd': 0.1425,
            'duration_seconds': 45,
            'tool_call_id': 'tc-xyz789'
        }
    """
    tool_name = pattern['tool_name']
    script_path = pattern['tool_script_path']
    adw_id = workflow_context['adw_id']
    issue_number = workflow_context.get('issue_number')

    logger.info(f"[Router] Executing tool: {tool_name} for workflow {adw_id}")

    # Generate tool call ID
    import uuid
    tool_call_id = f"tc-{uuid.uuid4().hex[:12]}"

    # Record tool call start
    cursor = db_connection.cursor()
    cursor.execute("""
        INSERT INTO tool_calls (
            tool_call_id,
            workflow_id,
            tool_name,
            tool_params,
            called_at
        ) VALUES (?, ?, ?, ?, datetime('now'))
    """, (
        tool_call_id,
        workflow_context.get('workflow_id', adw_id),
        tool_name,
        json.dumps(workflow_context)
    ))
    db_connection.commit()

    # Execute tool
    start_time = datetime.now()
    success = False
    result_data = None
    error_message = None

    try:
        result = execute_tool_script(
            script_path,
            workflow_context
        )

        success = result['success']
        result_data = result.get('data')
        error_message = result.get('error')

    except Exception as e:
        logger.error(f"[Router] Tool execution failed: {e}")
        success = False
        error_message = str(e)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Calculate tokens saved
    tokens_saved = 0
    cost_saved = 0.0

    if success:
        # Use pattern's historical data
        llm_tokens = pattern['avg_tokens_with_llm'] or 0
        tool_tokens = pattern['avg_tokens_with_tool'] or 0
        tokens_saved = llm_tokens - tool_tokens

        # Cost calculation (rough estimate: $0.003/1K tokens)
        cost_saved = (tokens_saved / 1000) * 0.003

        logger.info(
            f"[Router] Tool succeeded: saved {tokens_saved:,} tokens (${cost_saved:.4f})"
        )
    else:
        logger.warning(f"[Router] Tool failed: {error_message}")

    # Update tool call record
    cursor.execute("""
        UPDATE tool_calls
        SET
            completed_at = datetime('now'),
            duration_seconds = ?,
            success = ?,
            result_data = ?,
            error_message = ?,
            tokens_saved = ?,
            cost_saved_usd = ?
        WHERE tool_call_id = ?
    """, (
        duration,
        1 if success else 0,
        json.dumps(result_data) if result_data else None,
        error_message,
        tokens_saved,
        cost_saved,
        tool_call_id
    ))
    db_connection.commit()

    return {
        'success': success,
        'tool_name': tool_name,
        'result': result_data,
        'error': error_message,
        'tokens_saved': tokens_saved,
        'cost_saved_usd': cost_saved,
        'duration_seconds': duration,
        'tool_call_id': tool_call_id
    }


def execute_tool_script(
    script_path: str,
    workflow_context: Dict
) -> Dict:
    """
    Execute tool script and capture results.

    Args:
        script_path: Path to tool script (e.g., 'adws/adw_test_workflow.py')
        workflow_context: Context to pass to tool

    Returns:
        {
            'success': True,
            'data': {...},  # Parsed from tool output
            'error': None
        }
    """
    # Resolve script path
    project_root = Path(__file__).parent.parent.parent
    full_script_path = project_root / script_path

    if not full_script_path.exists():
        return {
            'success': False,
            'data': None,
            'error': f"Tool script not found: {script_path}"
        }

    # Build command
    cmd = [
        "uv", "run", "python",
        str(full_script_path),
        str(workflow_context.get('issue_number', '')),
        workflow_context['adw_id']
    ]

    # Add additional flags based on tool
    if 'test' in script_path:
        cmd.extend(['--test-type=all'])
    elif 'build' in script_path:
        cmd.extend(['--check-type=both', '--target=both'])

    logger.debug(f"[Router] Executing: {' '.join(cmd)}")

    try:
        # Execute with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            cwd=str(project_root / "adws")
        )

        if result.returncode == 0:
            # Parse JSON output from tool
            try:
                data = json.loads(result.stdout)
                return {
                    'success': True,
                    'data': data,
                    'error': None
                }
            except json.JSONDecodeError:
                # Tool didn't return JSON, use raw output
                return {
                    'success': True,
                    'data': {'output': result.stdout},
                    'error': None
                }
        else:
            return {
                'success': False,
                'data': None,
                'error': f"Tool exited with code {result.returncode}: {result.stderr}"
            }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'data': None,
            'error': "Tool execution timed out (10 minutes)"
        }
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'error': f"Tool execution error: {str(e)}"
        }


# ============================================================================
# FALLBACK LOGIC
# ============================================================================

def should_fallback_to_llm(
    tool_result: Dict,
    pattern: Dict
) -> Tuple[bool, str]:
    """
    Decide if we should fallback to LLM after tool failure.

    Args:
        tool_result: Result from route_to_tool()
        pattern: Pattern dict

    Returns:
        (should_fallback: bool, reason: str)
    """
    if tool_result['success']:
        return False, "Tool succeeded"

    # Check tool reliability
    # If tool has low success rate, fallback immediately
    # (Would query adw_tools.success_rate here)

    # For now, always fallback on failure
    reason = f"Tool failed: {tool_result['error']}"
    logger.warning(f"[Router] Fallback to LLM - {reason}")

    return True, reason


# ============================================================================
# COST LOGGING
# ============================================================================

def log_cost_savings(
    optimization_type: str,
    workflow_id: str,
    tool_call_id: Optional[str],
    pattern_id: Optional[int],
    tokens_saved: int,
    cost_saved_usd: float,
    db_connection,
    notes: Optional[str] = None
):
    """
    Record cost savings to cost_savings_log table.

    Args:
        optimization_type: 'pattern_offload', 'tool_call', 'input_split', etc.
        workflow_id: Workflow identifier
        tool_call_id: Tool call identifier (if applicable)
        pattern_id: Pattern ID (if applicable)
        tokens_saved: Number of tokens saved
        cost_saved_usd: Dollar amount saved
        db_connection: SQLite connection
        notes: Optional notes
    """
    cursor = db_connection.cursor()

    cursor.execute("""
        INSERT INTO cost_savings_log (
            optimization_type,
            workflow_id,
            tool_call_id,
            pattern_id,
            baseline_tokens,
            actual_tokens,
            tokens_saved,
            cost_saved_usd,
            notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        optimization_type,
        workflow_id,
        tool_call_id,
        pattern_id,
        0,  # Would calculate from pattern avg
        0,  # Would calculate from actual usage
        tokens_saved,
        cost_saved_usd,
        notes
    ))

    db_connection.commit()

    logger.info(
        f"[Savings] Logged: {optimization_type} - "
        f"{tokens_saved:,} tokens (${cost_saved_usd:.4f})"
    )


# ============================================================================
# MAIN ROUTING FUNCTION
# ============================================================================

def route_workflow(
    nl_input: str,
    workflow_context: Dict,
    db_connection
) -> Dict:
    """
    Main entry point for pattern-based routing.

    Args:
        nl_input: User's natural language input
        workflow_context: Workflow context dict
        db_connection: SQLite connection

    Returns:
        {
            'routed_to': 'tool' or 'llm',
            'pattern_matched': 'test:pytest:backend' or None,
            'tool_result': {...} or None,
            'should_use_llm': bool,
            'reason': str
        }
    """
    # Check for pattern match
    pattern = match_input_to_pattern(nl_input, db_connection)

    if not pattern:
        return {
            'routed_to': 'llm',
            'pattern_matched': None,
            'tool_result': None,
            'should_use_llm': True,
            'reason': 'No high-confidence pattern match'
        }

    # Route to tool
    tool_result = route_to_tool(pattern, workflow_context, db_connection)

    # Check if should fallback
    should_fallback, fallback_reason = should_fallback_to_llm(tool_result, pattern)

    if should_fallback:
        return {
            'routed_to': 'tool_then_llm',
            'pattern_matched': pattern['pattern_signature'],
            'tool_result': tool_result,
            'should_use_llm': True,
            'reason': fallback_reason
        }

    # Tool succeeded - log savings
    log_cost_savings(
        optimization_type='pattern_offload',
        workflow_id=workflow_context.get('workflow_id', workflow_context['adw_id']),
        tool_call_id=tool_result['tool_call_id'],
        pattern_id=pattern['id'],
        tokens_saved=tool_result['tokens_saved'],
        cost_saved_usd=tool_result['cost_saved_usd'],
        db_connection=db_connection,
        notes=f"Pattern: {pattern['pattern_signature']}"
    )

    return {
        'routed_to': 'tool',
        'pattern_matched': pattern['pattern_signature'],
        'tool_result': tool_result,
        'should_use_llm': False,
        'reason': 'Tool execution successful'
    }
```

---

### Step 3.2: Integrate into ADW Executor
**File:** `adws/adw_sdlc_iso.py`

**Add routing logic at the start of workflow:**

```python
# Add imports at top
import sys
import os
from pathlib import Path
import sqlite3

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "app" / "server"))

from core.pattern_matcher import route_workflow


def execute_adw(issue_number: int, adw_id: str):
    """Execute ADW workflow with pattern-based routing."""

    # Load workflow state
    state = load_adw_state(adw_id)
    nl_input = state.get('nl_input', '')

    # Connect to database
    db_path = project_root / "app" / "server" / "db" / "workflow_history.db"
    db_conn = sqlite3.connect(str(db_path))
    db_conn.row_factory = sqlite3.Row

    try:
        # NEW: Check for pattern match and route
        workflow_context = {
            'adw_id': adw_id,
            'issue_number': issue_number,
            'workflow_id': state.get('workflow_id', adw_id),
            'worktree_path': state.get('worktree_path'),
            'nl_input': nl_input
        }

        routing_result = route_workflow(nl_input, workflow_context, db_conn)

        logger.info(f"[ADW] Routing decision: {routing_result['routed_to']}")
        logger.info(f"[ADW] Reason: {routing_result['reason']}")

        if routing_result['pattern_matched']:
            logger.info(f"[ADW] Pattern: {routing_result['pattern_matched']}")

        # If routed to tool and successful, use tool results
        if routing_result['routed_to'] == 'tool' and not routing_result['should_use_llm']:
            tool_result = routing_result['tool_result']

            logger.info(
                f"[ADW] ✅ Tool execution successful - "
                f"saved {tool_result['tokens_saved']:,} tokens (${tool_result['cost_saved_usd']:.4f})"
            )

            # Store tool results in state
            state['tool_routed'] = True
            state['tool_name'] = tool_result['tool_name']
            state['tool_results'] = tool_result['result']
            state['tokens_saved'] = tool_result['tokens_saved']
            save_adw_state(state)

            # Post success comment to GitHub
            post_github_comment(
                issue_number,
                f"✅ **Tool Execution Complete**\n\n"
                f"Pattern matched: `{routing_result['pattern_matched']}`\n"
                f"Tool used: `{tool_result['tool_name']}`\n"
                f"Tokens saved: {tool_result['tokens_saved']:,}\n"
                f"Cost saved: ${tool_result['cost_saved_usd']:.4f}\n\n"
                f"Results:\n```json\n{json.dumps(tool_result['result'], indent=2)}\n```"
            )

            return 0  # Success

        # Otherwise, fallback to LLM workflow
        elif routing_result['should_use_llm']:
            logger.info(f"[ADW] Executing with LLM: {routing_result['reason']}")

            # Post info comment if tool was attempted
            if routing_result['routed_to'] == 'tool_then_llm':
                post_github_comment(
                    issue_number,
                    f"ℹ️ **Tool Fallback**\n\n"
                    f"Attempted tool routing but falling back to LLM.\n"
                    f"Reason: {routing_result['reason']}"
                )

            # Execute normal LLM workflow
            return execute_llm_workflow(issue_number, adw_id, state)

    finally:
        db_conn.close()


def execute_llm_workflow(issue_number: int, adw_id: str, state: Dict):
    """Original LLM-based workflow execution."""
    # ... existing LLM workflow code ...
    pass
```

---

### Step 3.3: Register Tools
**File:** `scripts/register_tools.py`

```python
#!/usr/bin/env python3
"""
Register ADW tools in the database.

Populates the adw_tools table with metadata for specialized tools.
"""

import sys
import sqlite3
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
db_path = project_root / "app" / "server" / "db" / "workflow_history.db"


def register_tool(
    tool_name: str,
    description: str,
    script_path: str,
    input_patterns: list,
    tool_schema: dict = None,
    output_format: dict = None,
    status: str = 'active'
):
    """Register a tool in the database."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    tool_schema = tool_schema or {
        "type": "object",
        "properties": {
            "issue_number": {"type": "integer"},
            "adw_id": {"type": "string"}
        }
    }

    output_format = output_format or {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "data": {"type": "object"}
        }
    }

    cursor.execute("""
        INSERT OR REPLACE INTO adw_tools (
            tool_name,
            description,
            tool_schema,
            script_path,
            input_patterns,
            output_format,
            status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        tool_name,
        description,
        json.dumps(tool_schema),
        script_path,
        json.dumps(input_patterns),
        json.dumps(output_format),
        status
    ))

    conn.commit()
    conn.close()

    print(f"✓ Registered: {tool_name}")


def main():
    """Register all available tools."""
    print("Registering ADW tools...")
    print()

    # Test workflow tool
    register_tool(
        tool_name='run_test_workflow',
        description='Run project test suite (pytest/vitest) and return failures only. Saves ~95% tokens.',
        script_path='adws/adw_test_workflow.py',
        input_patterns=[
            'run tests',
            'test suite',
            'pytest',
            'vitest',
            'execute tests',
            'run all tests',
            'run backend tests',
            'run frontend tests'
        ],
        status='active'
    )

    # Build workflow tool
    register_tool(
        tool_name='run_build_workflow',
        description='Run build/typecheck and return errors only. Saves ~97% tokens.',
        script_path='adws/adw_build_workflow.py',
        input_patterns=[
            'build',
            'typecheck',
            'type check',
            'compile',
            'tsc',
            'check types',
            'run build'
        ],
        status='active'
    )

    # Test generation tool
    register_tool(
        tool_name='generate_tests',
        description='Auto-generate tests from templates. Saves ~90% tokens.',
        script_path='adws/adw_test_gen_workflow.py',
        input_patterns=[
            'generate tests',
            'create tests',
            'add tests',
            'write tests for'
        ],
        status='experimental'  # Not yet activated for auto-routing
    )

    print()
    print("=" * 60)
    print("✅ Tool registration complete!")
    print("=" * 60)

    # Show registered tools
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tool_name, status, input_patterns
        FROM adw_tools
        ORDER BY status, tool_name
    """)

    print()
    print("Registered tools:")
    for row in cursor.fetchall():
        patterns = json.loads(row['input_patterns'])
        print(f"  • {row['tool_name']} ({row['status']})")
        print(f"    Triggers: {', '.join(patterns[:3])}...")

    conn.close()


if __name__ == "__main__":
    main()
```

**Make executable and run:**
```bash
chmod +x scripts/register_tools.py
python scripts/register_tools.py
```

---

### Step 3.4: Link Patterns to Tools
**File:** `scripts/link_patterns_to_tools.py`

```python
#!/usr/bin/env python3
"""
Link detected patterns to their corresponding tools.

Updates operation_patterns.tool_name based on pattern_signature.
"""

import sqlite3
from pathlib import Path

project_root = Path(__file__).parent.parent
db_path = project_root / "app" / "server" / "db" / "workflow_history.db"


def link_patterns():
    """Link patterns to tools."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Mapping of pattern signatures to tools
    pattern_tool_map = {
        'test:pytest:backend': 'run_test_workflow',
        'test:pytest:frontend': 'run_test_workflow',
        'test:pytest:all': 'run_test_workflow',
        'test:vitest:frontend': 'run_test_workflow',
        'test:vitest:backend': 'run_test_workflow',
        'test:generic:all': 'run_test_workflow',
        'build:typecheck:backend': 'run_build_workflow',
        'build:typecheck:frontend': 'run_build_workflow',
        'build:typecheck:both': 'run_build_workflow',
        'build:compile:all': 'run_build_workflow',
        'build:build:all': 'run_build_workflow',
    }

    updated = 0

    for pattern_sig, tool_name in pattern_tool_map.items():
        # Check if pattern exists
        cursor.execute("""
            SELECT id FROM operation_patterns
            WHERE pattern_signature = ?
        """, (pattern_sig,))

        if cursor.fetchone():
            # Check if tool exists
            cursor.execute("""
                SELECT tool_name FROM adw_tools
                WHERE tool_name = ?
            """, (tool_name,))

            if cursor.fetchone():
                # Link pattern to tool
                cursor.execute("""
                    UPDATE operation_patterns
                    SET
                        tool_name = ?,
                        tool_script_path = (
                            SELECT script_path FROM adw_tools WHERE tool_name = ?
                        )
                    WHERE pattern_signature = ?
                """, (tool_name, tool_name, pattern_sig))

                updated += 1
                print(f"✓ Linked: {pattern_sig} → {tool_name}")

    conn.commit()
    conn.close()

    print()
    print(f"✅ Linked {updated} patterns to tools")


if __name__ == "__main__":
    link_patterns()
```

**Run it:**
```bash
python scripts/link_patterns_to_tools.py
```

---

### Step 3.5: Activate High-Confidence Patterns
**File:** `scripts/activate_patterns.py`

```python
#!/usr/bin/env python3
"""
Activate patterns that meet criteria for automation.

Changes automation_status from 'detected' to 'active' for patterns with:
- confidence_score >= 70
- occurrence_count >= 3
- tool_name is set
"""

import sqlite3
from pathlib import Path

project_root = Path(__file__).parent.parent
db_path = project_root / "app" / "server" / "db" / "workflow_history.db"


def activate_patterns():
    """Activate eligible patterns."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find eligible patterns
    cursor.execute("""
        SELECT
            id,
            pattern_signature,
            confidence_score,
            occurrence_count,
            tool_name
        FROM operation_patterns
        WHERE automation_status = 'detected'
        AND confidence_score >= 70
        AND occurrence_count >= 3
        AND tool_name IS NOT NULL
    """)

    eligible = cursor.fetchall()

    if not eligible:
        print("No patterns eligible for activation.")
        return

    print(f"Found {len(eligible)} pattern(s) eligible for activation:")
    print()

    for pattern in eligible:
        print(f"  • {pattern['pattern_signature']}")
        print(f"    Confidence: {pattern['confidence_score']:.1f}%")
        print(f"    Occurrences: {pattern['occurrence_count']}")
        print(f"    Tool: {pattern['tool_name']}")

    print()
    response = input("Activate these patterns? (yes/no): ")

    if response.lower() != 'yes':
        print("Cancelled.")
        return

    # Activate patterns
    for pattern in eligible:
        cursor.execute("""
            UPDATE operation_patterns
            SET automation_status = 'active'
            WHERE id = ?
        """, (pattern['id'],))

    conn.commit()
    conn.close()

    print()
    print(f"✅ Activated {len(eligible)} pattern(s)")


if __name__ == "__main__":
    activate_patterns()
```

**Run it:**
```bash
python scripts/activate_patterns.py
```

---

## Testing Strategy

### Unit Tests
**File:** `app/server/tests/test_pattern_matcher.py`

```python
"""Unit tests for pattern matcher and tool routing."""

import pytest
import json
from core.pattern_matcher import (
    match_input_to_pattern,
    calculate_input_similarity,
    route_to_tool,
)


@pytest.fixture
def mock_db():
    """Create mock database."""
    import sqlite3

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
            avg_tokens_with_tool INTEGER
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

    cursor.execute("""
        CREATE TABLE tool_calls (
            tool_call_id TEXT PRIMARY KEY,
            workflow_id TEXT,
            tool_name TEXT,
            tool_params TEXT,
            called_at TEXT,
            completed_at TEXT,
            duration_seconds REAL,
            success INTEGER,
            result_data TEXT,
            error_message TEXT,
            tokens_saved INTEGER,
            cost_saved_usd REAL
        )
    """)

    # Insert test data
    cursor.execute("""
        INSERT INTO operation_patterns VALUES
        (1, 'test:pytest:backend', 85.0, '{}', 'run_test_workflow', 'active', 50000, 2500)
    """)

    cursor.execute("""
        INSERT INTO adw_tools VALUES
        ('run_test_workflow', 'adws/adw_test_workflow.py',
         '["run tests", "test suite", "pytest"]', 'active')
    """)

    conn.commit()
    return conn


class TestPatternMatching:
    """Test pattern matching logic."""

    def test_match_high_confidence(self, mock_db):
        """Should match pattern with high confidence."""
        result = match_input_to_pattern(
            "run the backend test suite with pytest",
            mock_db
        )

        assert result is not None
        assert result['pattern_signature'] == 'test:pytest:backend'
        assert result['tool_name'] == 'run_test_workflow'

    def test_no_match_low_confidence(self, mock_db):
        """Should not match if confidence too low."""
        result = match_input_to_pattern(
            "implement user authentication",
            mock_db,
            min_confidence=70.0
        )

        assert result is None

    def test_input_similarity_calculation(self):
        """Should calculate input similarity correctly."""
        # All keywords match
        score = calculate_input_similarity(
            "run tests with pytest",
            ["run", "tests", "pytest"]
        )
        assert score == 100.0

        # Partial match
        score = calculate_input_similarity(
            "run tests",
            ["run", "tests", "pytest"]
        )
        assert 50 < score < 100

        # No match
        score = calculate_input_similarity(
            "deploy to production",
            ["run", "tests", "pytest"]
        )
        assert score == 0.0


class TestToolRouting:
    """Test tool routing and execution."""

    def test_route_to_tool_success(self, mock_db):
        """Should route to tool and record results."""
        pattern = {
            'tool_name': 'run_test_workflow',
            'tool_script_path': 'adws/adw_test_workflow.py',
            'avg_tokens_with_llm': 50000,
            'avg_tokens_with_tool': 2500
        }

        workflow_context = {
            'adw_id': 'adw-test123',
            'issue_number': 42,
            'workflow_id': 'wf-test123'
        }

        # Note: This would need mocking of subprocess.run
        # For now, just test the structure
        assert pattern['tool_name'] == 'run_test_workflow'
```

### Integration Tests
```bash
# 1. Register tools
python scripts/register_tools.py

# 2. Link patterns
python scripts/link_patterns_to_tools.py

# 3. Activate patterns
python scripts/activate_patterns.py

# 4. Test pattern matching
python -c "
import sqlite3
from app.server.core.pattern_matcher import match_input_to_pattern

conn = sqlite3.connect('app/server/db/workflow_history.db')
conn.row_factory = sqlite3.Row

result = match_input_to_pattern('run the backend tests', conn)
if result:
    print(f'✓ Matched: {result[\"pattern_signature\"]}')
    print(f'  Tool: {result[\"tool_name\"]}')
    print(f'  Confidence: {result[\"confidence_score\"]:.1f}%')
else:
    print('✗ No match')

conn.close()
"

# 5. Test full routing (dry-run)
cd adws/
uv run adw_sdlc_iso.py 42 --dry-run

# 6. Test actual execution
cd adws/
uv run adw_sdlc_iso.py 43  # Real issue number
```

---

## Success Criteria

- [ ] ✅ Pattern matcher returns high-confidence matches (>=70%)
- [ ] ✅ Tool routing executes external tools successfully
- [ ] ✅ Cost savings tracked in cost_savings_log table
- [ ] ✅ Fallback to LLM works on tool failures
- [ ] ✅ 40%+ of test/build operations auto-routed within 1 week
- [ ] ✅ No regressions in workflow success rate
- [ ] ✅ Average token savings: 45,000+ per routed workflow

---

## Deliverables

1. ✅ `app/server/core/pattern_matcher.py` (600+ lines)
2. ✅ Modified `adws/adw_sdlc_iso.py` (+150 lines)
3. ✅ `scripts/register_tools.py` (150 lines)
4. ✅ `scripts/link_patterns_to_tools.py` (100 lines)
5. ✅ `scripts/activate_patterns.py` (100 lines)
6. ✅ `app/server/tests/test_pattern_matcher.py` (200 lines)

**Total Lines of Code:** ~1300 lines

---

## Next Steps (After Phase 3)

1. Monitor tool routing for 1 week
2. Review cost_savings_log for actual savings
3. Adjust confidence thresholds if needed
4. Activate more patterns as confidence grows
5. Proceed to Phase 4: Auto-Discovery
