# Phase 3C: ADW Integration & Routing

**Duration:** 2-3 days
**Dependencies:** Phase 3A (pattern matcher) + Phase 3B (tools registered) complete
**Priority:** HIGH - Delivers actual cost savings
**Status:** Ready to implement

---

## Overview

Wire everything together to enable automatic tool routing in ADW workflows. This phase implements:
1. Tool execution logic (calling external Python scripts)
2. Full routing workflow (pattern match → execute tool → handle results)
3. Fallback to LLM on tool failures
4. Cost savings tracking
5. Integration with ADW executor

**This is the final phase** that brings all components together and delivers measurable token savings.

---

## Goals

- ✅ Complete pattern_matcher.py with execution functions
- ✅ Integrate routing logic into ADW executor
- ✅ Implement tool execution with timeout and error handling
- ✅ Add fallback to LLM when tools fail
- ✅ Track cost savings in database
- ✅ Test end-to-end workflow routing

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  ADW WORKFLOW STARTS                                      │
│  Issue #42: "Run the backend test suite"                 │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  route_workflow() - Main Entry Point                     │
│                                                           │
│  1. Call match_input_to_pattern()                        │
│     → Returns pattern or None                            │
└────────────────────┬─────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
    [Match Found]         [No Match]
    confidence>=70%
          │                     │
          ▼                     ▼
┌──────────────────────┐  ┌─────────────────────┐
│  route_to_tool()     │  │  FALLBACK TO LLM    │
│                      │  │                     │
│  1. Record tool call │  │  Return:            │
│  2. Execute script   │  │  should_use_llm=True│
│  3. Capture results  │  │                     │
│  4. Calculate savings│  │                     │
└──────────┬───────────┘  └──────────┬──────────┘
           │                         │
    [Tool Success]  [Tool Failure]   │
           │              │          │
           ▼              └──────────┤
┌──────────────────────┐             │
│  log_cost_savings()  │             │
│                      │             │
│  Return:             │             ▼
│  should_use_llm=False│  ┌──────────────────────┐
└──────────────────────┘  │  should_fallback_    │
                          │  to_llm()            │
                          │                      │
                          │  → Yes: Use LLM      │
                          │  → Post GitHub       │
                          │    comment           │
                          └──────────────────────┘
```

---

## Implementation Part 1: Tool Execution Logic

Add these functions to `app/server/core/pattern_matcher.py`:

```python
# Add to existing pattern_matcher.py file

import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Tuple


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
        llm_tokens = pattern.get('avg_tokens_with_llm') or 0
        tool_tokens = pattern.get('avg_tokens_with_tool') or 0
        tokens_saved = llm_tokens - tool_tokens

        # Cost calculation (Sonnet 4: $3/M input, $15/M output, avg ~$0.003/1K)
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

    # Add tool-specific flags
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
            cwd=str(project_root)
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

    # For now, always fallback on failure
    # Future enhancement: check tool success_rate in database
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
        optimization_type: 'pattern_offload', 'tool_call', etc.
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

## Implementation Part 2: ADW Executor Integration

Modify `adws/adw_sdlc_iso.py` to integrate routing:

```python
# Add to adws/adw_sdlc_iso.py

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

    logger.info(f"[ADW] Starting workflow: {adw_id} for issue #{issue_number}")

    # Load workflow state
    state = load_adw_state(adw_id)
    nl_input = state.get('nl_input', '')

    if not nl_input:
        logger.error("[ADW] No nl_input in state - cannot route")
        return execute_llm_workflow(issue_number, adw_id, state)

    # Connect to database
    db_path = project_root / "app" / "server" / "db" / "workflow_history.db"

    if not db_path.exists():
        logger.warning(f"[ADW] Database not found: {db_path} - using LLM workflow")
        return execute_llm_workflow(issue_number, adw_id, state)

    db_conn = sqlite3.connect(str(db_path))
    db_conn.row_factory = sqlite3.Row

    try:
        # ====================================================================
        # PATTERN-BASED ROUTING
        # ====================================================================
        workflow_context = {
            'adw_id': adw_id,
            'issue_number': issue_number,
            'workflow_id': state.get('workflow_id', adw_id),
            'worktree_path': state.get('worktree_path'),
            'nl_input': nl_input
        }

        logger.info(f"[ADW] Checking for pattern match: '{nl_input[:60]}...'")

        routing_result = route_workflow(nl_input, workflow_context, db_conn)

        logger.info(f"[ADW] Routing decision: {routing_result['routed_to']}")
        logger.info(f"[ADW] Reason: {routing_result['reason']}")

        if routing_result['pattern_matched']:
            logger.info(f"[ADW] Pattern: {routing_result['pattern_matched']}")

        # ====================================================================
        # TOOL EXECUTION SUCCESS PATH
        # ====================================================================
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
            state['status'] = 'completed'
            save_adw_state(state)

            # Post success comment to GitHub
            post_github_comment(
                issue_number,
                f"✅ **Tool Execution Complete**\\n\\n"
                f"Pattern matched: `{routing_result['pattern_matched']}`\\n"
                f"Tool used: `{tool_result['tool_name']}`\\n"
                f"Tokens saved: {tool_result['tokens_saved']:,}\\n"
                f"Cost saved: ${tool_result['cost_saved_usd']:.4f}\\n\\n"
                f"**Results:**\\n```json\\n{json.dumps(tool_result['result'], indent=2)}\\n```\\n\\n"
                f"Duration: {tool_result['duration_seconds']:.1f}s"
            )

            return 0  # Success

        # ====================================================================
        # FALLBACK TO LLM PATH
        # ====================================================================
        elif routing_result['should_use_llm']:
            logger.info(f"[ADW] Executing with LLM: {routing_result['reason']}")

            # Post info comment if tool was attempted
            if routing_result['routed_to'] == 'tool_then_llm':
                post_github_comment(
                    issue_number,
                    f"ℹ️ **Tool Fallback**\\n\\n"
                    f"Attempted tool routing but falling back to LLM.\\n"
                    f"Pattern: `{routing_result['pattern_matched']}`\\n"
                    f"Reason: {routing_result['reason']}"
                )

            # Execute normal LLM workflow
            return execute_llm_workflow(issue_number, adw_id, state)

    finally:
        db_conn.close()


def execute_llm_workflow(issue_number: int, adw_id: str, state: Dict):
    """
    Original LLM-based workflow execution.

    This is the existing workflow logic - unchanged.
    """
    # ... existing LLM workflow code ...
    logger.info("[ADW] Executing LLM workflow")

    # Your existing claude code execution logic here
    # This should remain unchanged

    pass
```

---

## Testing Strategy

### Integration Test Script

**File:** `scripts/test_tool_routing.py`

```python
#!/usr/bin/env python3
"""
Integration test for tool routing.

Usage:
    python scripts/test_tool_routing.py
"""

import sys
import sqlite3
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "app" / "server"))

from core.pattern_matcher import route_workflow


def test_routing():
    """Test full routing workflow."""
    db_path = project_root / "app" / "server" / "db" / "workflow_history.db"

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    test_cases = [
        {
            'input': 'run the backend test suite',
            'expect': 'tool',
            'description': 'Should route to test tool'
        },
        {
            'input': 'typecheck the entire codebase',
            'expect': 'tool',
            'description': 'Should route to build tool'
        },
        {
            'input': 'implement user authentication',
            'expect': 'llm',
            'description': 'Should fallback to LLM (creative work)'
        },
    ]

    print("=" * 60)
    print("TOOL ROUTING INTEGRATION TEST")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['description']}")
        print(f"  Input: '{test['input']}'")

        workflow_context = {
            'adw_id': f'test-{i}',
            'issue_number': 999,
            'workflow_id': f'wf-test-{i}',
            'nl_input': test['input']
        }

        result = route_workflow(test['input'], workflow_context, conn)

        expected_routing = test['expect']
        actual_routing = 'llm' if result['should_use_llm'] else 'tool'

        if actual_routing == expected_routing:
            print(f"  ✓ PASS: Routed to {result['routed_to']}")
            if result['pattern_matched']:
                print(f"    Pattern: {result['pattern_matched']}")
            passed += 1
        else:
            print(f"  ✗ FAIL: Expected {expected_routing}, got {actual_routing}")
            print(f"    Reason: {result['reason']}")
            failed += 1

        print()

    conn.close()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(test_routing())
```

---

## Success Criteria

- [ ] ✅ `pattern_matcher.py` complete with all routing functions
- [ ] ✅ `adw_sdlc_iso.py` integrated with routing logic
- [ ] ✅ Tool execution works with subprocess
- [ ] ✅ Fallback to LLM on tool failures
- [ ] ✅ Cost savings tracked in database
- [ ] ✅ Integration test passes
- [ ] ✅ End-to-end workflow test successful
- [ ] ✅ GitHub comments posted correctly

---

## End-to-End Testing

### Test 1: Create Test Issue

```bash
# Create test issue
gh issue create \
  --title "Test: Run backend tests" \
  --body "Run the backend test suite with pytest" \
  --label "test"

# Note the issue number (e.g., 123)
```

### Test 2: Trigger ADW Workflow

```bash
# Run ADW for test issue
cd adws
uv run python adw_sdlc_iso.py 123
```

### Expected Behavior:

1. **Pattern Matching:**
   - Should match `test:pytest:backend` pattern
   - Log should show: "Pattern matched: test:pytest:backend"

2. **Tool Execution:**
   - Should execute `adws/adw_test_workflow.py`
   - Should complete in < 60 seconds
   - Should return test results

3. **Cost Tracking:**
   - Should log tokens saved to database
   - Should show savings in GitHub comment

4. **GitHub Comment:**
   ```
   ✅ Tool Execution Complete

   Pattern matched: `test:pytest:backend`
   Tool used: `run_test_workflow`
   Tokens saved: 47,500
   Cost saved: $0.1425

   Results:
   ```json
   {
     "tests_run": 42,
     "failures": 0,
     "duration": 12.3
   }
   ```

   Duration: 45.2s
   ```

### Test 3: Verify Cost Savings

```bash
sqlite3 app/server/db/workflow_history.db "
SELECT
    optimization_type,
    tokens_saved,
    cost_saved_usd,
    notes
FROM cost_savings_log
ORDER BY logged_at DESC
LIMIT 5;
"
```

---

## Troubleshooting

### Tool Execution Fails

**Problem:** subprocess returns non-zero exit code

**Solution:**
- Test tool script manually: `uv run python adws/adw_test_workflow.py 123 test-adw`
- Check script permissions: `chmod +x adws/adw_test_workflow.py`
- Review stderr output in error message

### Pattern Matches But No Tool Execution

**Problem:** Pattern matched but still uses LLM

**Solution:**
```bash
# Check tool is registered and active
sqlite3 app/server/db/workflow_history.db "
SELECT tool_name, status FROM adw_tools WHERE tool_name = 'run_test_workflow';
"

# Check pattern is linked to tool
sqlite3 app/server/db/workflow_history.db "
SELECT pattern_signature, tool_name, automation_status
FROM operation_patterns
WHERE pattern_signature = 'test:pytest:backend';
"
```

### Database Connection Errors

**Problem:** `db_path` not found or connection fails

**Solution:**
```python
# Add debug logging
logger.debug(f"[ADW] DB path: {db_path}")
logger.debug(f"[ADW] DB exists: {db_path.exists()}")
```

---

## Deliverables Checklist

- [ ] `app/server/core/pattern_matcher.py` completed (~650 additional lines)
- [ ] `adws/adw_sdlc_iso.py` modified (+150 lines)
- [ ] `scripts/test_tool_routing.py` created (~100 lines)
- [ ] Integration tests passing
- [ ] End-to-end workflow tested
- [ ] Cost savings verified in database
- [ ] GitHub comments working

**Total Lines of Code:** ~900 lines

---

## Phase 3 Complete!

After finishing Phase 3C, you will have:

- ✅ **Phase 3A:** Pattern matching engine
- ✅ **Phase 3B:** Tool registration system
- ✅ **Phase 3C:** Full ADW integration

**Next Steps:**
1. Monitor tool routing for 1 week
2. Review cost_savings_log for actual savings
3. Adjust confidence thresholds if needed
4. Proceed to **Phase 4: Auto-Discovery** for continuous improvement

---

## Success Metrics (After 1 Week)

Expected results after Phase 3 is fully operational:

- **Routing Rate:** 40%+ of test/build operations auto-routed
- **Token Savings:** 45,000+ tokens per routed workflow
- **Cost Savings:** $0.10-0.15 per routed workflow
- **Success Rate:** 95%+ tool executions successful
- **Fallback Rate:** < 5% requiring LLM fallback

Track progress:
```sql
-- Routing statistics
SELECT
    COUNT(*) FILTER (WHERE routed_to = 'tool') as tool_routed,
    COUNT(*) FILTER (WHERE routed_to = 'llm') as llm_only,
    SUM(tokens_saved) as total_tokens_saved,
    SUM(cost_saved_usd) as total_cost_saved
FROM cost_savings_log
WHERE logged_at >= date('now', '-7 days');
```
