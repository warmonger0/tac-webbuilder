# External Tool Schemas

## Overview

This document defines the exact input/output schemas for all external ADW tools, integration points, and data flow specifications.

## Tool Registration in Database

All tools are registered in the `adw_tools` table with the following structure:

```sql
CREATE TABLE adw_tools (
    tool_name TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    tool_schema TEXT NOT NULL,  -- JSON schema for parameters
    script_path TEXT NOT NULL,
    input_patterns TEXT,  -- JSON array of trigger keywords
    output_format TEXT,  -- JSON schema for output
    status TEXT DEFAULT 'active',  -- active|deprecated|experimental
    avg_duration_seconds REAL DEFAULT 0.0,
    avg_tokens_consumed INTEGER DEFAULT 0,
    avg_cost_usd REAL DEFAULT 0.0,
    success_rate REAL DEFAULT 1.0,
    total_invocations INTEGER DEFAULT 0
)
```

## Tool 1: Test Runner (`run_test_workflow`)

### Purpose
Execute project test suites (pytest/vitest) and return only failures with precise error locations.

### Registration Data
```python
{
    "tool_name": "run_test_workflow",
    "description": "Run the project test suite and return failures only. Dramatically reduces context by not loading test files.",
    "script_path": "adws/adw_test_workflow.py",
    "status": "experimental",
    "input_patterns": [
        "run tests", "test suite", "pytest", "vitest",
        "execute tests", "run all tests", "check tests"
    ]
}
```

### Input Schema (JSON Schema Format)
```json
{
    "type": "object",
    "properties": {
        "test_path": {
            "type": "string",
            "description": "Optional path to specific tests (e.g., 'app/server/tests/test_analytics.py'). If omitted, runs all tests.",
            "default": null
        },
        "test_type": {
            "type": "string",
            "enum": ["pytest", "vitest", "all"],
            "description": "Which test framework to use",
            "default": "all"
        },
        "coverage_threshold": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "description": "Minimum coverage percentage required (fails if below)",
            "default": 80
        },
        "fail_fast": {
            "type": "boolean",
            "description": "Stop on first failure",
            "default": false
        },
        "verbose": {
            "type": "boolean",
            "description": "Include verbose output for failures",
            "default": true
        }
    },
    "required": []
}
```

### Output Schema (JSON Schema Format)
```json
{
    "type": "object",
    "properties": {
        "success": {
            "type": "boolean",
            "description": "Overall test success (true if all tests passed)"
        },
        "summary": {
            "type": "object",
            "properties": {
                "total": {"type": "integer"},
                "passed": {"type": "integer"},
                "failed": {"type": "integer"},
                "skipped": {"type": "integer"},
                "duration_seconds": {"type": "number"}
            },
            "required": ["total", "passed", "failed", "duration_seconds"]
        },
        "failures": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "test_name": {"type": "string"},
                    "file": {"type": "string"},
                    "line": {"type": "integer"},
                    "error_type": {"type": "string"},
                    "error_message": {"type": "string"},
                    "stack_trace": {"type": "string"}
                },
                "required": ["test_name", "file", "line", "error_message"]
            }
        },
        "coverage": {
            "type": "object",
            "properties": {
                "percentage": {"type": "number"},
                "lines_covered": {"type": "integer"},
                "lines_total": {"type": "integer"},
                "missing_files": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "next_steps": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Suggested actions to fix failures"
        }
    },
    "required": ["success", "summary", "failures", "next_steps"]
}
```

### Example Output
```json
{
    "success": false,
    "summary": {
        "total": 45,
        "passed": 42,
        "failed": 3,
        "skipped": 0,
        "duration_seconds": 12.4
    },
    "failures": [
        {
            "test_name": "test_workflow_analytics::test_calculate_clarity_score",
            "file": "app/server/tests/test_workflow_analytics.py",
            "line": 67,
            "error_type": "AssertionError",
            "error_message": "Expected 0.85, got 0.72",
            "stack_trace": "  File \"test_workflow_analytics.py\", line 67, in test_calculate_clarity_score\n    assert result == 0.85\nAssertionError: Expected 0.85, got 0.72"
        }
    ],
    "coverage": {
        "percentage": 82.5,
        "lines_covered": 1650,
        "lines_total": 2000,
        "missing_files": ["app/server/core/new_module.py"]
    },
    "next_steps": [
        "Fix assertion in app/server/tests/test_workflow_analytics.py:67",
        "Add coverage for app/server/core/new_module.py (currently 0%)"
    ]
}
```

### Integration Point
**Called from**: `adw_test_iso.py` during test phase

**Python invocation**:
```python
from adw_modules.tool_registry import ToolRegistry

registry = ToolRegistry()
result = registry.invoke_tool("run_test_workflow", {
    "test_type": "all",
    "coverage_threshold": 80
})

if not result["success"]:
    for failure in result["failures"]:
        print(f"❌ {failure['file']}:{failure['line']} - {failure['error_message']}")
```

---

## Tool 2: Build Checker (`run_build_workflow`)

### Purpose
Run typecheck and build processes, returning only errors with precise locations.

### Registration Data
```python
{
    "tool_name": "run_build_workflow",
    "description": "Run typecheck/build and return errors only. Dramatically reduces context during build validation.",
    "script_path": "adws/adw_build_workflow.py",
    "status": "planned",
    "input_patterns": [
        "build", "typecheck", "check types", "run build",
        "compile", "type errors", "tsc", "typescript check"
    ]
}
```

### Input Schema
```json
{
    "type": "object",
    "properties": {
        "check_type": {
            "type": "string",
            "enum": ["typecheck", "build", "both"],
            "description": "What to check",
            "default": "both"
        },
        "target": {
            "type": "string",
            "enum": ["frontend", "backend", "both"],
            "description": "Which codebase to check",
            "default": "both"
        },
        "strict_mode": {
            "type": "boolean",
            "description": "Enable strict TypeScript checking",
            "default": true
        }
    },
    "required": []
}
```

### Output Schema
```json
{
    "type": "object",
    "properties": {
        "success": {
            "type": "boolean",
            "description": "True if no errors found"
        },
        "summary": {
            "type": "object",
            "properties": {
                "total_errors": {"type": "integer"},
                "type_errors": {"type": "integer"},
                "build_errors": {"type": "integer"},
                "warnings": {"type": "integer"},
                "duration_seconds": {"type": "number"}
            }
        },
        "errors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "line": {"type": "integer"},
                    "column": {"type": "integer"},
                    "error_type": {"type": "string"},
                    "severity": {
                        "type": "string",
                        "enum": ["error", "warning"]
                    },
                    "message": {"type": "string"},
                    "code_snippet": {"type": "string"}
                }
            }
        },
        "next_steps": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["success", "summary", "errors", "next_steps"]
}
```

### Example Output
```json
{
    "success": false,
    "summary": {
        "total_errors": 5,
        "type_errors": 3,
        "build_errors": 2,
        "warnings": 0,
        "duration_seconds": 8.2
    },
    "errors": [
        {
            "file": "app/client/src/components/RequestForm.tsx",
            "line": 142,
            "column": 23,
            "error_type": "TS2345",
            "severity": "error",
            "message": "Type 'string' is not assignable to type 'number'",
            "code_snippet": "const port: number = '8000';"
        }
    ],
    "next_steps": [
        "Fix type error in app/client/src/components/RequestForm.tsx:142 (TS2345)"
    ]
}
```

### Integration Point
**Called from**: `adw_build_iso.py` during build phase

---

## Tool 3: Test Generator (`generate_tests_workflow`)

### Purpose
Auto-generate tests using libraries (pynguin, hypothesis, templates), only involving LLM for complex cases.

### Registration Data
```python
{
    "tool_name": "generate_tests_workflow",
    "description": "Auto-generate tests using libraries/templates. Only involves LLM for complex edge cases.",
    "script_path": "adws/adw_test_gen_workflow.py",
    "status": "planned",
    "input_patterns": [
        "generate tests", "create tests", "write tests",
        "test generation", "auto test", "test coverage"
    ]
}
```

### Input Schema
```json
{
    "type": "object",
    "properties": {
        "target_path": {
            "type": "string",
            "description": "Path to file/directory to generate tests for",
            "examples": ["app/server/core/new_feature.py"]
        },
        "test_type": {
            "type": "string",
            "enum": ["unit", "integration", "e2e", "all"],
            "default": "unit"
        },
        "coverage_goal": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "default": 85
        },
        "generation_strategy": {
            "type": "string",
            "enum": ["pynguin", "hypothesis", "template", "hybrid", "llm"],
            "description": "Which generation approach to use",
            "default": "hybrid"
        },
        "max_llm_budget": {
            "type": "number",
            "description": "Max tokens to spend on LLM-generated tests",
            "default": 10000
        }
    },
    "required": ["target_path"]
}
```

### Output Schema
```json
{
    "type": "object",
    "properties": {
        "success": {
            "type": "boolean"
        },
        "auto_generated": {
            "type": "object",
            "properties": {
                "count": {"type": "integer"},
                "files": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "coverage_achieved": {"type": "number"},
                "generation_method": {
                    "type": "object",
                    "properties": {
                        "pynguin": {"type": "integer"},
                        "hypothesis": {"type": "integer"},
                        "template": {"type": "integer"},
                        "llm": {"type": "integer"}
                    }
                }
            }
        },
        "needs_llm_review": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "function": {"type": "string"},
                    "file": {"type": "string"},
                    "line": {"type": "integer"},
                    "reason": {"type": "string"},
                    "context": {"type": "string"},
                    "complexity_score": {"type": "number"}
                }
            }
        },
        "coverage_gap": {
            "type": "object",
            "properties": {
                "percentage_needed": {"type": "number"},
                "uncovered_lines": {
                    "type": "array",
                    "items": {"type": "integer"}
                }
            }
        },
        "tokens_used": {
            "type": "integer",
            "description": "Tokens consumed for LLM generation (if any)"
        },
        "next_steps": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["success", "auto_generated", "needs_llm_review", "next_steps"]
}
```

### Example Output
```json
{
    "success": true,
    "auto_generated": {
        "count": 23,
        "files": [
            "app/server/tests/test_new_feature.py"
        ],
        "coverage_achieved": 78.5,
        "generation_method": {
            "pynguin": 15,
            "hypothesis": 3,
            "template": 5,
            "llm": 0
        }
    },
    "needs_llm_review": [
        {
            "function": "handle_edge_case",
            "file": "app/server/core/new_feature.py",
            "line": 89,
            "reason": "Complex async logic with external dependencies",
            "context": "async def handle_edge_case(config: Dict, api_client: APIClient) -> Result:\n    # Complex branching logic with API calls",
            "complexity_score": 8.5
        }
    ],
    "coverage_gap": {
        "percentage_needed": 6.5,
        "uncovered_lines": [89, 90, 134, 135]
    },
    "tokens_used": 0,
    "next_steps": [
        "Review 23 auto-generated tests in app/server/tests/test_new_feature.py",
        "Manually write test for handle_edge_case (complexity: 8.5/10)",
        "Run test suite to verify 78.5% coverage"
    ]
}
```

### Integration Point
**Called from**: `adw_test_iso.py` or standalone via `uv run adw_test_gen_workflow.py`

---

## Integration Architecture

### How Main Workflows Call External Tools

```python
# In adw_test_iso.py (modified)
from adw_modules.tool_registry import ToolRegistry
import json

def run_tests(adw_id: str, issue_number: str):
    """Run tests using external test workflow."""
    registry = ToolRegistry()

    # Invoke external tool
    result = registry.invoke_tool("run_test_workflow", {
        "test_type": "all",
        "coverage_threshold": 80
    })

    # Log invocation
    registry.log_invocation(
        workflow_id=adw_id,
        tool_name="run_test_workflow",
        result=result,
        tokens_saved=45000  # Estimated context savings
    )

    # Handle result
    if result["success"]:
        print(f"✅ All {result['summary']['total']} tests passed!")
        return True
    else:
        print(f"❌ {result['summary']['failed']} test(s) failed:")
        for failure in result["failures"]:
            print(f"  - {failure['file']}:{failure['line']} - {failure['error_message']}")
        return False
```

### Tool Invocation Flow

```
┌──────────────────────────────────────────┐
│  Main ADW (adw_sdlc_iso.py)              │
│  Current Phase: TEST                      │
└──────────────┬───────────────────────────┘
               │
               │ 1. Request tool invocation
               ▼
┌──────────────────────────────────────────┐
│  ToolRegistry.invoke_tool()              │
│  - Validates input against schema        │
│  - Spawns subprocess for tool script     │
│  - Tracks start time, metrics            │
└──────────────┬───────────────────────────┘
               │
               │ 2. Execute external script
               ▼
┌──────────────────────────────────────────┐
│  adw_test_workflow.py                    │
│  - Runs pytest/vitest                    │
│  - Parses output                         │
│  - Extracts failures only                │
│  - Returns compact JSON                  │
└──────────────┬───────────────────────────┘
               │
               │ 3. Return compact result
               ▼
┌──────────────────────────────────────────┐
│  ToolRegistry.invoke_tool()              │
│  - Validates output against schema       │
│  - Updates tool metrics in DB            │
│  - Returns result to caller              │
└──────────────┬───────────────────────────┘
               │
               │ 4. Process result
               ▼
┌──────────────────────────────────────────┐
│  Main ADW (adw_sdlc_iso.py)              │
│  - Displays failures to user             │
│  - Decides next action                   │
│  - Continues SDLC or fixes errors        │
└──────────────────────────────────────────┘
```

### Database Tracking

Every tool invocation is logged to `tool_calls` table:

```sql
INSERT INTO tool_calls (
    tool_call_id, workflow_id, tool_name,
    tool_params, success, result_data,
    tokens_saved, duration_seconds
) VALUES (
    'tc-abc123', 'adw-def456', 'run_test_workflow',
    '{"test_type": "all"}', 1, '{"success": true, ...}',
    45000, 12.4
);
```

### Cost Tracking

Before/after comparison stored in `tool_calls` table:

- `tokens_saved`: Context tokens not loaded (45K for passing tests)
- `cost_before`: Estimated cost without external tool ($0.30)
- `cost_after`: Actual cost with external tool ($0.05)
- `savings_percentage`: 83.3%

---

## Command-Line Interface

All tools can be invoked standalone for testing:

```bash
# Test Runner
cd adws/
uv run adw_test_workflow.py --test-type=pytest --coverage-threshold=80

# Build Checker
uv run adw_build_workflow.py --check-type=both --target=frontend

# Test Generator
uv run adw_test_gen_workflow.py \
  --target-path=app/server/core/new_feature.py \
  --coverage-goal=85 \
  --generation-strategy=hybrid
```

---

## Error Handling

All tools follow consistent error handling:

```json
{
    "success": false,
    "error": {
        "type": "ExecutionError",
        "message": "pytest command failed with exit code 2",
        "details": "No tests found in specified path",
        "file": null,
        "line": null
    },
    "next_steps": [
        "Verify test path exists: app/server/tests/",
        "Check pytest is installed: uv pip list | grep pytest"
    ]
}
```

---

**Document Status**: Draft - v1.0
**Date**: 2025-01-16
**Next Steps**: Implement tool scripts based on these schemas
