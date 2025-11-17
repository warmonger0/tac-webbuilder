"""
Pattern Signature Generation System.

This module provides functionality to generate unique signatures for workflow operations
based on natural language input. Pattern signatures enable automatic workflow categorization,
intelligent routing, pattern detection, and cost optimization.

Signature Format:
    category:subcategory:target

Examples:
    - "test:pytest:backend" - Run pytest tests on backend code
    - "test:vitest:frontend" - Run vitest tests on frontend code
    - "build:typecheck:both" - Type-check both frontend and backend
    - "format:prettier:all" - Format all code with prettier
    - "git:diff:summary" - Show git diff summary
    - "deps:npm:update" - Update npm dependencies

Usage:
    >>> from app.server.core.pattern_signatures import generate_signature
    >>>
    >>> # Generate signature from natural language
    >>> sig = generate_signature("run pytest tests on backend")
    >>> print(sig)
    'test:pytest:backend'
    >>>
    >>> # Validate a signature
    >>> from app.server.core.pattern_signatures import validate_signature
    >>> is_valid = validate_signature("test:pytest:backend")
    >>> print(is_valid)
    True
    >>>
    >>> # Parse signature into components
    >>> from app.server.core.pattern_signatures import parse_signature
    >>> components = parse_signature("test:pytest:backend")
    >>> print(components)
    {'category': 'test', 'subcategory': 'pytest', 'target': 'backend'}

Integration Points:
    - pattern_matcher.py: Uses signatures to match operations to handlers
    - workflow_analytics.py: Uses signatures to group similar workflows
    - workflow_history.py: Stores signatures with workflow records for analytics
"""

import re
import logging
from typing import Optional, Dict

from core.constants import (
    VALID_CATEGORIES,
    VALID_SUBCATEGORIES,
    VALID_TARGETS,
    SIGNATURE_FORMAT_REGEX,
)

# Module-level logger
logger = logging.getLogger(__name__)


# Type aliases for signature components
Category = str
Subcategory = str
Target = str


def detect_category(nl_input: str) -> Optional[Category]:
    """
    Detect the category from natural language input.

    Uses keyword matching to identify the operation category. Categories represent
    high-level operation types: test, build, format, git, deps, docs.

    Args:
        nl_input: Natural language description of the operation

    Returns:
        Category string if detected, None otherwise

    Examples:
        >>> detect_category("run pytest tests")
        'test'
        >>> detect_category("build the project")
        'build'
        >>> detect_category("format code with prettier")
        'format'
        >>> detect_category("fix the authentication bug")
        None
    """
    if not nl_input or not isinstance(nl_input, str):
        return None

    # Normalize input to lowercase for matching
    nl_lower = nl_input.lower()

    # Test category keywords
    if any(keyword in nl_lower for keyword in [
        "test", "pytest", "vitest", "jest", "unittest", "mocha", "cypress",
        "test suite", "run tests", "testing"
    ]):
        return "test"

    # Build category keywords
    if any(keyword in nl_lower for keyword in [
        "build", "compile", "typecheck", "type check", "webpack", "vite",
        "bundl", "tsc", "transpile"
    ]):
        return "build"

    # Format category keywords
    if any(keyword in nl_lower for keyword in [
        "format", "lint", "prettier", "eslint", "black", "ruff", "rustfmt",
        "style", "formatting", "linting"
    ]):
        return "format"

    # Git category keywords
    if any(keyword in nl_lower for keyword in [
        "git diff", "git commit", "git status", "git add", "git push",
        "git pull", "git log", "commit", "diff"
    ]):
        return "git"

    # Deps category keywords
    if any(keyword in nl_lower for keyword in [
        "npm install", "pip install", "cargo", "dependencies", "packages",
        "update packages", "install", "yarn", "pnpm", "deps"
    ]):
        return "deps"

    # Docs category keywords
    if any(keyword in nl_lower for keyword in [
        "documentation", "docs", "readme", "docstring", "api doc",
        "guide", "changelog", "document"
    ]):
        return "docs"

    return None


def detect_subcategory(nl_input: str, category: Category) -> Optional[Subcategory]:
    """
    Detect the subcategory from natural language input based on the category.

    Subcategories identify the specific tool or operation within a category.
    Returns category-specific default if no specific tool is detected.

    Args:
        nl_input: Natural language description of the operation
        category: The detected category (test, build, format, git, deps, docs)

    Returns:
        Subcategory string if detected, "generic" as default

    Examples:
        >>> detect_subcategory("run pytest tests", "test")
        'pytest'
        >>> detect_subcategory("run tests", "test")
        'generic'
        >>> detect_subcategory("format with prettier", "format")
        'prettier'
    """
    if not nl_input or not isinstance(nl_input, str) or not category:
        return "generic"

    nl_lower = nl_input.lower()

    if category == "test":
        if "pytest" in nl_lower:
            return "pytest"
        elif "vitest" in nl_lower:
            return "vitest"
        elif "jest" in nl_lower:
            return "jest"
        elif "unittest" in nl_lower:
            return "unittest"
        elif "mocha" in nl_lower:
            return "mocha"
        elif "cypress" in nl_lower:
            return "cypress"
        return "generic"

    elif category == "build":
        if "typecheck" in nl_lower or "type check" in nl_lower or "tsc" in nl_lower:
            return "typecheck"
        elif "compile" in nl_lower:
            return "compile"
        elif "webpack" in nl_lower:
            return "webpack"
        elif "vite" in nl_lower:
            return "vite"
        elif "npm" in nl_lower:
            return "npm"
        elif "pip" in nl_lower:
            return "pip"
        elif "cargo" in nl_lower:
            return "cargo"
        return "generic"

    elif category == "format":
        if "prettier" in nl_lower:
            return "prettier"
        elif "eslint" in nl_lower:
            return "eslint"
        elif "black" in nl_lower:
            return "black"
        elif "ruff" in nl_lower:
            return "ruff"
        elif "rustfmt" in nl_lower:
            return "rustfmt"
        return "generic"

    elif category == "git":
        if "diff" in nl_lower:
            return "diff"
        elif "commit" in nl_lower:
            return "commit"
        elif "status" in nl_lower:
            return "status"
        elif "add" in nl_lower:
            return "add"
        elif "push" in nl_lower:
            return "push"
        elif "pull" in nl_lower:
            return "pull"
        elif "log" in nl_lower:
            return "log"
        return "generic"

    elif category == "deps":
        if "npm" in nl_lower:
            return "npm"
        elif "pip" in nl_lower:
            return "pip"
        elif "cargo" in nl_lower:
            return "cargo"
        elif "yarn" in nl_lower:
            return "yarn"
        elif "pnpm" in nl_lower:
            return "pnpm"
        elif "update" in nl_lower:
            return "update"
        elif "install" in nl_lower:
            return "install"
        return "generic"

    elif category == "docs":
        if "readme" in nl_lower:
            return "readme"
        elif "api" in nl_lower:
            return "api"
        elif "guide" in nl_lower:
            return "guide"
        elif "changelog" in nl_lower:
            return "changelog"
        elif "docstring" in nl_lower:
            return "docstring"
        return "generic"

    return "generic"


def detect_target(nl_input: str) -> Target:
    """
    Detect the target from natural language input.

    Target indicates what part of the codebase the operation applies to:
    backend, frontend, both, or all. Defaults to "all" if not specified.

    Args:
        nl_input: Natural language description of the operation

    Returns:
        Target string (backend, frontend, both, or all)

    Examples:
        >>> detect_target("run backend tests")
        'backend'
        >>> detect_target("format frontend code")
        'frontend'
        >>> detect_target("type check both frontend and backend")
        'both'
        >>> detect_target("run tests")
        'all'
    """
    if not nl_input or not isinstance(nl_input, str):
        return "all"

    nl_lower = nl_input.lower()

    # Check for "both" keywords first
    if any(keyword in nl_lower for keyword in ["both", "frontend and backend", "backend and frontend"]):
        return "both"

    # Check for backend keywords
    has_backend = any(keyword in nl_lower for keyword in [
        "backend", "server", "api", "python", "fastapi", "django"
    ])

    # Check for frontend keywords
    has_frontend = any(keyword in nl_lower for keyword in [
        "frontend", "client", "ui", "react", "vue", "angular", "typescript", "jsx", "tsx"
    ])

    # If both detected, return "both"
    if has_backend and has_frontend:
        return "both"

    # If only one detected, return that one
    if has_backend:
        return "backend"
    if has_frontend:
        return "frontend"

    # Default to "all"
    return "all"


def generate_signature(nl_input: str) -> Optional[str]:
    """
    Generate a pattern signature from natural language input.

    Parses natural language to detect category, subcategory, and target,
    then formats them into a standardized signature string.

    Returns None for complex multi-step tasks that don't fit pattern matching.

    Args:
        nl_input: Natural language description of the operation

    Returns:
        Formatted signature string (category:subcategory:target) or None

    Examples:
        >>> generate_signature("run pytest tests on backend")
        'test:pytest:backend'
        >>> generate_signature("format code with prettier")
        'format:prettier:all'
        >>> generate_signature("implement authentication with JWT and add tests")
        None
    """
    if not nl_input or not isinstance(nl_input, str):
        return None

    # Strip whitespace
    nl_input = nl_input.strip()
    if not nl_input:
        return None

    # Check for complex multi-step tasks (should return None)
    # Look for multiple verbs or conjunctions indicating multiple operations
    complexity_indicators = [
        " and then ", " after ", " before ",
        "implement", "refactor", "redesign", "architecture",
        "entire", "whole", "complete overhaul"
    ]

    nl_lower = nl_input.lower()

    # Count operation verbs
    operation_verbs = ["run", "test", "build", "format", "lint", "compile", "install", "update", "commit"]
    verb_count = sum(1 for verb in operation_verbs if verb in nl_lower)

    # If multiple conjunctions or complex indicators, return None
    if any(indicator in nl_lower for indicator in complexity_indicators):
        return None

    # If multiple distinct operations mentioned, return None
    if " and " in nl_lower and verb_count > 1:
        return None

    # Detect category
    category = detect_category(nl_input)
    if not category:
        return None

    # Detect subcategory
    subcategory = detect_subcategory(nl_input, category)
    if not subcategory:
        subcategory = "generic"

    # Detect target
    target = detect_target(nl_input)

    # Format signature
    signature = f"{category}:{subcategory}:{target}"

    return signature


def validate_signature(signature: str) -> bool:
    """
    Validate a pattern signature format and components.

    Checks that the signature:
    1. Matches the format pattern (category:subcategory:target)
    2. Contains valid category, subcategory, and target values

    Args:
        signature: Signature string to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_signature("test:pytest:backend")
        True
        >>> validate_signature("test:pytest")
        False
        >>> validate_signature("invalid:foo:bar")
        False
    """
    if not signature or not isinstance(signature, str):
        return False

    # Check format with regex
    if not re.match(SIGNATURE_FORMAT_REGEX, signature):
        return False

    # Parse components
    parts = signature.split(":")
    if len(parts) != 3:
        return False

    category, subcategory, target = parts

    # Validate category
    if category not in VALID_CATEGORIES:
        return False

    # Validate subcategory for the category
    if category not in VALID_SUBCATEGORIES:
        return False
    if subcategory not in VALID_SUBCATEGORIES[category]:
        return False

    # Validate target
    if target not in VALID_TARGETS:
        return False

    return True


def normalize_signature(signature: str) -> Optional[str]:
    """
    Normalize a signature to standard format.

    Converts to lowercase, trims whitespace, and validates the result.

    Args:
        signature: Signature string to normalize

    Returns:
        Normalized signature if valid, None otherwise

    Examples:
        >>> normalize_signature("Test:Pytest:Backend")
        'test:pytest:backend'
        >>> normalize_signature("  test:pytest:backend  ")
        'test:pytest:backend'
        >>> normalize_signature("invalid:foo:bar")
        None
    """
    if not signature or not isinstance(signature, str):
        return None

    # Convert to lowercase and trim
    normalized = signature.lower().strip()

    # Validate normalized signature
    if validate_signature(normalized):
        return normalized

    return None


def parse_signature(signature: str) -> Optional[Dict[str, str]]:
    """
    Parse a signature into its components.

    Splits the signature and returns a dictionary with category, subcategory,
    and target keys. Returns None if the signature is invalid.

    Args:
        signature: Signature string to parse

    Returns:
        Dict with category, subcategory, target keys, or None if invalid

    Examples:
        >>> parse_signature("test:pytest:backend")
        {'category': 'test', 'subcategory': 'pytest', 'target': 'backend'}
        >>> parse_signature("invalid")
        None
    """
    if not signature or not isinstance(signature, str):
        return None

    # Validate first
    if not validate_signature(signature):
        return None

    # Split into components
    parts = signature.split(":")
    if len(parts) != 3:
        return None

    return {
        "category": parts[0],
        "subcategory": parts[1],
        "target": parts[2],
    }
