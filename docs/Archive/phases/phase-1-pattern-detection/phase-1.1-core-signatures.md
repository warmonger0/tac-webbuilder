# Phase 1.1: Core Pattern Signatures - Implementation Guide

**Parent:** Phase 1 - Pattern Detection Engine
**Duration:** 1-2 days
**Priority:** HIGH - Foundation for pattern detection
**Status:** Ready to implement

---

## Overview

Build the core pattern signature generation system that uniquely identifies operation types from workflow data. This is the foundation that enables pattern detection and automation.

---

## Goals

1. ✅ Generate unique signatures for common operations (test, build, format, git, etc.)
2. ✅ Classify operations by category, subcategory, and target
3. ✅ Extract operation context from natural language input
4. ✅ Handle edge cases and ambiguous inputs
5. ✅ Achieve >90% accuracy on test suite

---

## Signature Format

```
{category}:{subcategory}:{target}

Examples:
  - "test:pytest:backend"
  - "test:vitest:frontend"
  - "build:typecheck:both"
  - "format:prettier:all"
  - "git:diff:summary"
  - "deps:npm:update"
```

**Why this format?**
- **Category** - High-level operation type (test, build, format, etc.)
- **Subcategory** - Specific tool or variant (pytest, vitest, typecheck, etc.)
- **Target** - Scope of operation (backend, frontend, both, all)

This hierarchical structure allows for:
- Pattern matching at different granularities
- Tool-agnostic automation (e.g., all `test:*:backend` patterns)
- Clear automation opportunities

---

## Supported Categories

### 1. Testing Operations
**Category:** `test`
**Subcategories:** pytest, vitest, jest, mocha, generic
**Targets:** backend, frontend, both, all

**Examples:**
```
"Run backend tests with pytest" → "test:pytest:backend"
"Test the frontend with vitest" → "test:vitest:frontend"
"Run all tests" → "test:generic:all"
```

### 2. Build Operations
**Category:** `build`
**Subcategories:** typecheck, compile, bundle, build
**Targets:** backend, frontend, both, all

**Examples:**
```
"Run typecheck on backend" → "build:typecheck:backend"
"Build the frontend" → "build:bundle:frontend"
"Compile everything" → "build:compile:both"
```

### 3. Formatting Operations
**Category:** `format`
**Subcategories:** prettier, black, eslint, ruff, generic
**Targets:** all (formatting typically applies to all code)

**Examples:**
```
"Format code with prettier" → "format:prettier:all"
"Run black formatter" → "format:black:all"
"Lint with eslint" → "format:eslint:all"
```

### 4. Git Operations
**Category:** `git`
**Subcategories:** diff, status, log, generic
**Targets:** summary (git operations analyze the repo)

**Examples:**
```
"Show git diff" → "git:diff:summary"
"Check git status" → "git:status:summary"
"View git log" → "git:log:summary"
```

### 5. Dependency Operations
**Category:** `deps`
**Subcategories:** npm, pip, bun, yarn, generic
**Targets:** update (dependency operations modify packages)

**Examples:**
```
"Update npm dependencies" → "deps:npm:update"
"Install Python packages" → "deps:pip:update"
"Update all dependencies" → "deps:generic:update"
```

### 6. Documentation Operations
**Category:** `docs`
**Subcategories:** generate
**Targets:** all

**Examples:**
```
"Generate documentation" → "docs:generate:all"
"Update README" → "docs:generate:all"
```

---

## Implementation

### File: `app/server/core/pattern_signatures.py`

Create a new module focused purely on signature generation:

```python
"""
Pattern Signature Generation for Out-Loop Coding

Generates unique signatures for workflow operations to enable pattern detection.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# SIGNATURE GENERATION
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


# ============================================================================
# SUBCATEGORY DETECTORS
# ============================================================================

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
# TARGET DETECTION
# ============================================================================

def _detect_target(nl_input: str, workflow: Dict) -> str:
    """
    Detect target of operation (backend, frontend, both).

    Priority:
    1. Explicit keywords in nl_input
    2. Inferred from workflow template
    3. Default to 'all'
    """
    # Check explicit keywords
    if "backend" in nl_input or "server" in nl_input or "api" in nl_input:
        return "backend"
    elif "frontend" in nl_input or "client" in nl_input or "ui" in nl_input:
        return "frontend"
    elif "both" in nl_input or "all" in nl_input:
        return "both"

    # Try to infer from workflow template
    template = (workflow.get("workflow_template") or "").lower()
    if "server" in template or "backend" in template:
        return "backend"
    elif "client" in template or "frontend" in template:
        return "frontend"

    # Default
    return "all"


# ============================================================================
# VALIDATION
# ============================================================================

def validate_signature(signature: str) -> bool:
    """
    Validate that a signature follows the correct format.

    Format: {category}:{subcategory}:{target}

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature:
        return False

    parts = signature.split(":")
    if len(parts) != 3:
        return False

    category, subcategory, target = parts

    # Validate category
    valid_categories = {"test", "build", "format", "git", "deps", "docs"}
    if category not in valid_categories:
        return False

    # Validate non-empty subcategory and target
    if not subcategory or not target:
        return False

    return True


def normalize_signature(signature: str) -> str:
    """
    Normalize a signature to ensure consistency.

    - Convert to lowercase
    - Trim whitespace
    - Validate format

    Returns:
        Normalized signature

    Raises:
        ValueError: If signature is invalid
    """
    normalized = signature.strip().lower()

    if not validate_signature(normalized):
        raise ValueError(f"Invalid signature format: {signature}")

    return normalized
```

---

## Unit Tests

### File: `app/server/tests/test_pattern_signatures.py`

```python
"""
Unit tests for pattern signature generation.
"""

import pytest
from core.pattern_signatures import (
    extract_operation_signature,
    validate_signature,
    normalize_signature,
)


class TestTestOperations:
    """Test signature generation for testing operations."""

    def test_pytest_backend(self):
        workflow = {
            "nl_input": "Run the backend test suite with pytest",
            "workflow_template": "adw_test_iso"
        }
        sig = extract_operation_signature(workflow)
        assert sig == "test:pytest:backend"

    def test_pytest_explicit(self):
        workflow = {
            "nl_input": "Run pytest on server code",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "test:pytest:backend"

    def test_vitest_frontend(self):
        workflow = {
            "nl_input": "Run frontend tests using vitest",
            "workflow_template": "adw_test_iso"
        }
        sig = extract_operation_signature(workflow)
        assert sig == "test:vitest:frontend"

    def test_jest_ui(self):
        workflow = {
            "nl_input": "Test UI components with jest",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "test:jest:frontend"

    def test_generic_all(self):
        workflow = {
            "nl_input": "Run all tests",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "test:generic:all"


class TestBuildOperations:
    """Test signature generation for build operations."""

    def test_typecheck_backend(self):
        workflow = {
            "nl_input": "Run typecheck on backend",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "build:typecheck:backend"

    def test_typecheck_all(self):
        workflow = {
            "nl_input": "Run typecheck on entire project",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "build:typecheck:all"

    def test_compile_backend(self):
        workflow = {
            "nl_input": "Compile the backend code",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "build:compile:backend"

    def test_bundle_frontend(self):
        workflow = {
            "nl_input": "Bundle frontend with vite",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "build:bundle:frontend"


class TestFormatOperations:
    """Test signature generation for formatting operations."""

    def test_prettier(self):
        workflow = {
            "nl_input": "Format code with prettier",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "format:prettier:all"

    def test_black(self):
        workflow = {
            "nl_input": "Run black formatter on Python files",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "format:black:all"

    def test_eslint(self):
        workflow = {
            "nl_input": "Lint with eslint",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "format:eslint:all"


class TestGitOperations:
    """Test signature generation for git operations."""

    def test_git_diff(self):
        workflow = {
            "nl_input": "Show me the git diff",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "git:diff:summary"

    def test_git_status(self):
        workflow = {
            "nl_input": "Check git status",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "git:status:summary"

    def test_git_log(self):
        workflow = {
            "nl_input": "View git log",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "git:log:summary"


class TestDependencyOperations:
    """Test signature generation for dependency operations."""

    def test_npm_update(self):
        workflow = {
            "nl_input": "Update npm dependencies",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "deps:npm:update"

    def test_pip_install(self):
        workflow = {
            "nl_input": "Install Python packages with pip",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "deps:pip:update"


class TestDocumentationOperations:
    """Test signature generation for documentation operations."""

    def test_generate_docs(self):
        workflow = {
            "nl_input": "Generate documentation",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "docs:generate:all"

    def test_update_readme(self):
        workflow = {
            "nl_input": "Update the README file",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "docs:generate:all"


class TestNonPatterns:
    """Test that complex tasks don't generate signatures."""

    def test_feature_implementation(self):
        workflow = {
            "nl_input": "Implement user authentication with JWT",
            "workflow_template": "adw_plan_iso"
        }
        sig = extract_operation_signature(workflow)
        assert sig is None

    def test_bug_fix(self):
        workflow = {
            "nl_input": "Fix the login bug in the authentication system",
            "workflow_template": "adw_sdlc_iso"
        }
        sig = extract_operation_signature(workflow)
        assert sig is None

    def test_planning(self):
        workflow = {
            "nl_input": "Plan the implementation of the new feature",
            "workflow_template": "adw_plan_iso"
        }
        sig = extract_operation_signature(workflow)
        assert sig is None


class TestSignatureValidation:
    """Test signature validation and normalization."""

    def test_valid_signature(self):
        assert validate_signature("test:pytest:backend") is True
        assert validate_signature("build:typecheck:frontend") is True
        assert validate_signature("format:prettier:all") is True

    def test_invalid_format(self):
        assert validate_signature("test:pytest") is False  # Missing target
        assert validate_signature("test") is False  # Missing parts
        assert validate_signature("") is False  # Empty
        assert validate_signature("test:pytest:backend:extra") is False  # Too many parts

    def test_invalid_category(self):
        assert validate_signature("invalid:pytest:backend") is False

    def test_normalize_signature(self):
        assert normalize_signature("TEST:PYTEST:BACKEND") == "test:pytest:backend"
        assert normalize_signature("  test:pytest:backend  ") == "test:pytest:backend"

    def test_normalize_invalid(self):
        with pytest.raises(ValueError):
            normalize_signature("invalid")


class TestTargetDetection:
    """Test target detection logic."""

    def test_explicit_backend(self):
        workflow = {
            "nl_input": "Run tests on the backend server",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert "backend" in sig

    def test_explicit_frontend(self):
        workflow = {
            "nl_input": "Run tests on the frontend UI",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert "frontend" in sig

    def test_explicit_both(self):
        workflow = {
            "nl_input": "Run tests on both frontend and backend",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert "both" in sig

    def test_infer_from_template(self):
        workflow = {
            "nl_input": "Run tests",
            "workflow_template": "adw_test_backend"
        }
        sig = extract_operation_signature(workflow)
        assert "backend" in sig

    def test_default_all(self):
        workflow = {
            "nl_input": "Run tests",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert "all" in sig
```

---

## Testing Strategy

### Run Unit Tests

```bash
cd app/server
pytest tests/test_pattern_signatures.py -v
```

**Expected output:**
```
tests/test_pattern_signatures.py::TestTestOperations::test_pytest_backend PASSED
tests/test_pattern_signatures.py::TestTestOperations::test_vitest_frontend PASSED
tests/test_pattern_signatures.py::TestBuildOperations::test_typecheck_backend PASSED
...
======================== 25 passed in 0.5s ========================
```

### Manual Testing

```python
# Test in Python REPL
from app.server.core.pattern_signatures import extract_operation_signature

# Test various inputs
workflows = [
    {"nl_input": "Run backend tests with pytest", "workflow_template": None},
    {"nl_input": "Build the frontend", "workflow_template": None},
    {"nl_input": "Format code with prettier", "workflow_template": None},
]

for wf in workflows:
    sig = extract_operation_signature(wf)
    print(f"{wf['nl_input']:40} → {sig}")
```

---

## Success Criteria

- [ ] ✅ **All unit tests pass** - 25+ tests green
- [ ] ✅ **Signature coverage** - All 6 categories supported
- [ ] ✅ **Target detection works** - Backend/frontend/both/all correctly identified
- [ ] ✅ **Edge cases handled** - Complex tasks return None
- [ ] ✅ **Validation works** - Invalid signatures rejected
- [ ] ✅ **Code documented** - Docstrings on all functions

---

## Deliverables

1. ✅ `app/server/core/pattern_signatures.py` (~250 lines)
2. ✅ `app/server/tests/test_pattern_signatures.py` (~300 lines)

**Total Lines of Code:** ~550 lines

---

## Next Steps

After completing Phase 1.1:

1. Run all unit tests to verify correctness
2. Test manually with real workflow examples
3. **Proceed to Phase 1.2: Pattern Detection & Characteristics**

---

## Notes

- This module is **stateless** - no database operations
- Focus is on **pure functions** - easy to test
- Signatures are **deterministic** - same input = same output
- Design is **extensible** - easy to add new categories
