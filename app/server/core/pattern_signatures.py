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
    # Safely extract and normalize inputs
    nl_input_raw = workflow.get("nl_input")
    template_raw = workflow.get("workflow_template")

    nl_input = (nl_input_raw if nl_input_raw is not None else "").lower()
    template = (template_raw if template_raw is not None else "").lower()

    # Category 1: Testing operations
    if any(kw in nl_input for kw in ["test", "pytest", "vitest", "jest", "run tests"]):
        subcategory = _detect_test_framework(nl_input)
        target = _detect_target(nl_input, workflow)
        return f"test:{subcategory}:{target}"

    # Category 2: Build operations
    if any(kw in nl_input for kw in ["build", "compile", "typecheck", "tsc", "bundle"]):
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
    if any(kw in nl_input for kw in ["update dependencies", "npm update", "npm", "pip install", "pip", "install python", "update npm"]):
        subcategory = _detect_package_manager(nl_input)
        return f"deps:{subcategory}:update"

    # Category 6: Documentation
    if any(kw in nl_input for kw in ["generate docs", "update readme", "documentation", "readme"]):
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
    # Check for "both" first before checking individual targets
    if "both" in nl_input:
        return "both"

    # Check for "all" in specific contexts (e.g., "run all tests")
    # Look for "all" as a standalone word or followed by common keywords
    import re
    if re.search(r'\ball\b', nl_input):
        # Check if it's "all tests", "all code", etc.
        if any(word in nl_input for word in ["tests", "code", "files"]):
            return "all"

    # Check explicit target keywords
    if "backend" in nl_input or "server" in nl_input or "api" in nl_input:
        return "backend"
    elif "frontend" in nl_input or "client" in nl_input or "ui" in nl_input:
        return "frontend"

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
    valid_categories = {"test", "build", "format", "git", "deps", "docs", "sdlc", "patch", "deploy", "review"}
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
