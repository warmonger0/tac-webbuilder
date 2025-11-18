# Phase 4: Validate Working Directory Propagation

**Status:** Planned
**Priority:** Low
**Estimated Effort:** 1 hour
**Impact:** Consistent tool availability

## Problem

MCP config detection only happens when `working_dir` is provided to `execute_template()`. If not passed, agents in worktrees might not get MCP tools (Playwright, etc.).

## Current Code

**File:** `adw_modules/agent.py:332-335`

```python
# Check for MCP config in working directory
if request.working_dir:
    mcp_config_path = os.path.join(request.working_dir, ".mcp.json")
    if os.path.exists(mcp_config_path):
        cmd.extend(["--mcp-config", mcp_config_path])
```

**Issue:** If `working_dir` is None, MCP config is never loaded, even if the agent is running in a worktree.

## Solution

### 1. Audit All `execute_template()` Calls

Find all calls and ensure `working_dir` is passed in worktree workflows:

```bash
cd adws
grep -n "execute_template" *.py adw_modules/*.py
```

**Expected locations:**
- `adw_plan_iso.py` - Should pass `worktree_path`
- `adw_build_iso.py` - Should pass `worktree_path`
- `adw_test_iso.py` - Should pass `worktree_path`
- `adw_review_iso.py` - Should pass `worktree_path`
- `adw_document_iso.py` - Should pass `worktree_path`
- `adw_patch_iso.py` - Should pass `worktree_path`

### 2. Add Validation

**File:** `adw_modules/agent.py`

```python
def execute_template(request: AgentTemplateRequest) -> AgentPromptResponse:
    """Execute a Claude Code template with slash command and arguments."""

    # Get the appropriate model for this request
    mapped_model = get_model_for_slash_command(request)
    request = request.model_copy(update={"model": mapped_model})

    # Validate MCP config for worktree workflows
    if request.working_dir:
        mcp_config_path = os.path.join(request.working_dir, ".mcp.json")
        if os.path.exists(mcp_config_path):
            # Log that MCP tools will be available
            logging.debug(f"MCP config found: {mcp_config_path}")
        else:
            # Warn if expected but not found
            if "trees/" in request.working_dir:
                logging.warning(f"Worktree detected but no MCP config at {mcp_config_path}")

    # ... rest of function
```

### 3. Create Validation Script

**File:** `adws/scripts/validate_working_dir.py`

```python
#!/usr/bin/env python3
"""Validate that all execute_template calls in worktree workflows pass working_dir."""

import re
import sys
from pathlib import Path

def check_file(filepath):
    """Check if file has execute_template calls without working_dir."""
    content = filepath.read_text()

    # Find all execute_template calls
    pattern = r'execute_template\((.*?)\)'
    issues = []

    for match in re.finditer(pattern, content, re.DOTALL):
        call = match.group(1)
        # Check if this file works with worktrees
        if 'worktree' in filepath.name or '_iso.py' in filepath.name:
            # Should have working_dir parameter
            if 'working_dir=' not in call:
                line_num = content[:match.start()].count('\n') + 1
                issues.append((filepath.name, line_num, match.group(0)))

    return issues

def main():
    adws_dir = Path(__file__).parent.parent
    issues = []

    # Check all workflow files
    for py_file in adws_dir.glob("adw_*.py"):
        file_issues = check_file(py_file)
        issues.extend(file_issues)

    if issues:
        print("❌ Found execute_template calls without working_dir:")
        for filename, line_num, call in issues:
            print(f"  {filename}:{line_num} - {call[:60]}...")
        sys.exit(1)
    else:
        print("✅ All worktree workflows properly pass working_dir")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

## Implementation Steps

1. Create validation script
2. Run validation to find issues
3. Fix any execute_template calls missing working_dir
4. Add logging to agent.py for MCP config detection
5. Test review workflow to ensure MCP tools available

## Expected Benefits

- **Consistent tool availability:** All worktree agents get MCP tools
- **Better debugging:** Logs show when MCP config is loaded
- **Catch regressions:** Validation script prevents future issues

## Validation

```bash
# Run validation script
python adws/scripts/validate_working_dir.py

# Expected output:
# ✅ All worktree workflows properly pass working_dir
```

## Completion Criteria

- [ ] Validation script created
- [ ] All worktree workflows pass validation
- [ ] MCP config logging added to agent.py
- [ ] Test confirms MCP tools available in review phase
