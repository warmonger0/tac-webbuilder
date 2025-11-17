"""
Constants for JSONL file processing and field flattening.

This module defines the delimiter constants used for flattening nested JSON objects
and arrays into flat column names suitable for SQLite tables.

Delimiter System:
- NESTED_DELIMITER: Used to separate nested object keys (e.g., "user__profile__name")
- LIST_INDEX_DELIMITER: Used to separate list indices (e.g., "items_0", "items_1")

Examples:
- Nested object {"user": {"profile": {"name": "John"}}} becomes "user__profile__name"
- Array field {"items": ["a", "b"]} becomes "items_0" and "items_1"
- Complex structure {"tags": [{"name": "tag1"}, {"name": "tag2"}]} becomes "tags_0__name", "tags_1__name"
"""

# Delimiter for nested object fields
NESTED_DELIMITER = "__"

# Delimiter for list/array indices
LIST_INDEX_DELIMITER = "_"

# Pattern Signature Constants
# Used by the pattern signature generation system to classify workflow operations

# Valid categories for pattern signatures
# Each category represents a high-level operation type
VALID_CATEGORIES = ["test", "build", "format", "git", "deps", "docs"]

# Valid subcategories mapped to each category
# Subcategories identify the specific tool or operation within a category
VALID_SUBCATEGORIES = {
    "test": ["pytest", "vitest", "jest", "unittest", "mocha", "cypress", "generic"],
    "build": ["typecheck", "compile", "webpack", "vite", "npm", "pip", "cargo", "generic"],
    "format": ["prettier", "eslint", "black", "ruff", "rustfmt", "generic"],
    "git": ["diff", "commit", "status", "add", "push", "pull", "log", "generic"],
    "deps": ["npm", "pip", "cargo", "yarn", "pnpm", "update", "install", "generic"],
    "docs": ["readme", "api", "guide", "changelog", "docstring", "generic"],
}

# Valid targets for pattern signatures
# Target indicates what part of the codebase the operation applies to
VALID_TARGETS = ["backend", "frontend", "both", "all"]

# Regex pattern for validating signature format: category:subcategory:target
SIGNATURE_FORMAT_REGEX = r"^[a-z]+:[a-z]+:[a-z]+$"