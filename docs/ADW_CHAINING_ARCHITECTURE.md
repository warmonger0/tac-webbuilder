# ADW Chaining Architecture for External Tools

## Core Principle

External tools (test runner, build checker, test generator) are **independent ADW workflows** that are **chained via subprocess calls**, not directly invoked as functions.

## Why Chaining Instead of Direct Invocation?

### ❌ Bad: Direct Tool Invocation
```python
# adw_test_iso.py
from adw_modules.tool_registry import ToolRegistry

registry = ToolRegistry()
result = registry.invoke_tool("run_test_workflow", {...})  # ❌ Breaks isolation
```

**Problems:**
- Breaks ADW isolation model
- Doesn't use state management
- No worktree context
- Hard to debug/trace
- Doesn't follow existing patterns

### ✅ Good: ADW Workflow Chaining
```python
# adw_test_iso.py
import subprocess

# Chain to external test ADW
test_cmd = [
    "uv", "run",
    "adws/adw_test_external.py",
    issue_number,
    adw_id
]
result = subprocess.run(test_cmd)
```

**Benefits:**
- Maintains ADW isolation
- Uses state management (adw_state.json)
- Runs in correct worktree context
- Follows existing SDLC pattern
- Each tool is a complete, traceable ADW

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                  adw_sdlc_iso.py                         │
│                  (Main Orchestrator)                      │
└────────┬─────────────────────────────────────────────────┘
         │
         │ Chains ADW workflows via subprocess.run()
         │
    ┌────┴────┬──────────┬──────────┬──────────┬──────────┐
    │         │          │          │          │          │
    ▼         ▼          ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌─────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
│  Plan  │ │ Build  │ │  Test   │ │ Review │ │ Document │ │   Ship   │
│  ADW   │ │  ADW   │ │  ADW    │ │  ADW   │ │   ADW    │ │   ADW    │
└────────┘ └───┬────┘ └────┬────┘ └────────┘ └──────────┘ └──────────┘
               │           │
               │ Chains    │ Chains
               ▼           ▼
       ┌────────────┐  ┌────────────┐
       │Build Check │  │ Test Runner│
       │  ADW       │  │    ADW     │
       │(External)  │  │ (External) │
       └────────────┘  └────────────┘
           │               │
           │ Executes      │ Executes
           ▼               ▼
       ┌────────────┐  ┌────────────┐
       │    tsc     │  │   pytest   │
       │   vite     │  │   vitest   │
       └────────────┘  └────────────┘
           │               │
           │ Returns       │ Returns
           ▼               ▼
       Compact JSON    Compact JSON
       (errors only)   (failures only)
           │               │
           │ Saved to      │ Saved to
           ▼               ▼
       adw_state.json  adw_state.json
```

## State Management Flow

All ADW workflows share state via `agents/{adw_id}/adw_state.json`:

```python
# Example state after test ADW completes
{
  "adw_id": "adw-abc123",
  "issue_number": "42",
  "worktree_path": "trees/adw-abc123",
  "test_results": {
    "success": false,
    "summary": {
      "total": 45,
      "passed": 42,
      "failed": 3
    },
    "failures": [
      {
        "test_name": "test_analytics",
        "file": "app/server/tests/test_analytics.py",
        "line": 67,
        "error": "AssertionError"
      }
    ]
  }
}
```

## Refactored External Tool Workflows

### 1. Test Runner ADW (`adw_test_external.py`)

**Signature**: `uv run adw_test_external.py <issue-number> <adw-id>`

**Responsibilities:**
1. Load state from `agents/{adw_id}/adw_state.json`
2. Get worktree_path from state
3. Execute pytest/vitest in that worktree
4. Parse output to compact JSON (failures only)
5. Save results to state under `test_results` key
6. Exit with 0 (success) or 1 (failure)

**Called from**: `adw_test_iso.py` via subprocess chaining

### 2. Build Checker ADW (`adw_build_external.py`)

**Signature**: `uv run adw_build_external.py <issue-number> <adw-id>`

**Responsibilities:**
1. Load state
2. Get worktree_path
3. Execute tsc/vite build in worktree
4. Parse errors to compact JSON
5. Save to state under `build_results` key
6. Exit with code

**Called from**: `adw_build_iso.py` via subprocess chaining

### 3. Test Generator ADW (`adw_test_gen_external.py`)

**Signature**: `uv run adw_test_gen_external.py <issue-number> <adw-id> --target-path=<path>`

**Responsibilities:**
1. Load state
2. Get worktree_path
3. Analyze target file in worktree
4. Generate tests using templates
5. Save to state under `test_gen_results` key
6. Exit with code

**Called from**: `adw_test_iso.py` or standalone

## Integration Pattern

### Before (Direct Invocation - Wrong)
```python
# adw_test_iso.py - OLD APPROACH ❌
def main():
    registry = ToolRegistry()
    result = registry.invoke_tool("run_test_workflow", {
        "test_type": "all"
    })
```

### After (ADW Chaining - Correct)
```python
# adw_test_iso.py - NEW APPROACH ✅
def main():
    issue_number = sys.argv[1]
    adw_id = sys.argv[2]

    # Load state
    state = ADWState(adw_id)
    state.load()

    # Chain to external test ADW
    script_dir = os.path.dirname(os.path.abspath(__file__))
    test_cmd = [
        "uv", "run",
        os.path.join(script_dir, "adw_test_external.py"),
        issue_number,
        adw_id
    ]

    result = subprocess.run(test_cmd)

    # Reload state to get test results
    state.load()
    test_results = state.get("test_results", {})

    if test_results.get("success"):
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(test_results.get('failures', []))} test(s) failed")
        for failure in test_results.get("failures", []):
            print(f"  - {failure['file']}:{failure['line']} - {failure['error']}")

    return result.returncode
```

## Tool Registry Role

The Tool Registry is **metadata/discovery only**, not execution:

```python
# Tool Registry Usage (Discovery)
registry = ToolRegistry()

# Get tool metadata
tools = registry.get_all_tools()
for tool in tools:
    print(f"{tool.tool_name}: {tool.description}")
    print(f"  Script: {tool.script_path}")
    print(f"  Status: {tool.status}")

# Search for tools
matches = registry.search_tools("run tests")
# Returns: [run_test_workflow tool metadata]

# Invoke tool - ONLY FOR METADATA, NOT EXECUTION
# The actual ADW chaining is done via subprocess as shown above
```

## Migration Path

1. ✅ **Keep existing tool workflow scripts** (adw_test_workflow.py, etc.)
   - These work standalone for manual testing
   - They output compact JSON

2. ✅ **Create ADW wrapper scripts** (adw_test_external.py, etc.)
   - Follow ADW pattern (accept issue_number, adw_id)
   - Load/save state
   - Call underlying tool workflow
   - Store results in state

3. ✅ **Update main ADW workflows** (adw_test_iso.py, adw_build_iso.py)
   - Chain to external ADW wrappers via subprocess
   - Read results from state
   - Continue SDLC flow

## Benefits of This Architecture

1. **Isolation**: Each external tool runs as independent ADW
2. **State Management**: All workflows share state properly
3. **Traceability**: Full execution trace via ADW state files
4. **Testability**: Each ADW can be tested independently
5. **Composability**: Can chain tools in any order
6. **Consistency**: Follows existing ADW patterns
7. **Context Minimization**: Still achieves 70-95% token savings
8. **Error Handling**: Standard ADW error handling applies

## Example: Complete Test Flow

```bash
# 1. User triggers test
uv run adw_test_iso.py 42 adw-abc123

# 2. adw_test_iso.py chains to adw_test_external.py
subprocess.run(["uv", "run", "adw_test_external.py", "42", "adw-abc123"])

# 3. adw_test_external.py:
#    - Loads state from agents/adw-abc123/adw_state.json
#    - Gets worktree: trees/adw-abc123
#    - Calls adw_test_workflow.py with --json-input
#    - Receives compact JSON (failures only)
#    - Saves to state["test_results"]
#    - Exits with code 0/1

# 4. adw_test_iso.py:
#    - Reloads state
#    - Reads state["test_results"]
#    - Reports to user
#    - Continues SDLC
```

---

**Document Status**: Architecture v2.0 - ADW Chaining Model
**Date**: 2025-01-16
**Next Step**: Implement ADW wrapper scripts (adw_test_external.py, etc.)
