"""
Template-based routing for common request patterns.

This module provides fast, deterministic routing for common request types
using keyword/pattern matching. Falls back to structured prompts for novel requests.

Cost: $0 (template matching)
Latency: <100ms
"""

from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class TemplateMatch:
    """Result of template matching."""
    matched: bool
    workflow: Optional[str] = None
    model_set: Optional[str] = None
    classification: Optional[str] = None
    confidence: float = 0.0
    pattern_name: Optional[str] = None


# Lightweight patterns ($0.20-0.50)
LIGHTWEIGHT_PATTERNS = [
    # UI/Styling changes
    {
        "name": "ui_styling",
        "keywords_any_of": ["styling", "css", "style", "color", "margin", "padding", "layout"],
        "keywords_action": ["fix", "update", "change", "adjust"],
        "classification": "feature",
        "confidence": 0.9,
    },
    {
        "name": "ui_component_text",
        "keywords_any_of": ["text", "label", "title", "heading", "button text"],
        "keywords_action": ["change", "update", "fix"],
        "classification": "chore",
        "confidence": 0.9,
    },
    {
        "name": "ui_display",
        "keywords_any_of": ["display", "show", "hide", "tab", "column"],
        "keywords_action": ["fix", "change", "update"],
        "classification": "feature",
        "confidence": 0.85,
    },
    # Documentation
    {
        "name": "docs_update",
        "keywords_any_of": ["documentation", "readme", "docs", "comment", "docstring"],
        "keywords_action": ["update", "add", "fix", "write"],
        "classification": "chore",
        "confidence": 0.95,
    },
    {
        "name": "typo_fix",
        "keywords_any_of": ["typo", "spelling", "grammar"],
        "classification": "chore",
        "confidence": 1.0,
    },
    # Simple fixes
    {
        "name": "import_fix",
        "keywords_any_of": ["import", "import statement"],
        "keywords_action": ["fix", "add", "update"],
        "classification": "bug",
        "confidence": 0.9,
    },
]

# Standard SDLC patterns ($3-5)
STANDARD_PATTERNS = [
    # Features requiring testing
    {
        "name": "api_endpoint",
        "keywords_any_of": ["api", "endpoint", "route"],
        "keywords_action": ["add", "create", "implement", "new"],
        "classification": "feature",
        "confidence": 0.9,
    },
    {
        "name": "database_changes",
        "keywords_any_of": ["database", "table", "schema", "migration"],
        "classification": "feature",
        "confidence": 0.95,
    },
    {
        "name": "authentication",
        "keywords_any_of": ["auth", "login", "signup", "session", "jwt", "token"],
        "classification": "feature",
        "confidence": 0.9,
    },
]

# Bug patterns
BUG_PATTERNS = [
    {
        "name": "error_fix",
        "keywords_any_of": ["error", "crash", "exception", "failing", "broken"],
        "classification": "bug",
        "confidence": 0.95,
    },
    {
        "name": "bug_report",
        "keywords_any_of": ["bug", "issue", "problem"],
        "keywords_action": ["fix", "resolve", "solve"],
        "classification": "bug",
        "confidence": 0.9,
    },
]


def normalize_text(text: str) -> str:
    """Normalize text for pattern matching."""
    return text.lower().strip()


def matches_pattern(text: str, pattern: Dict) -> bool:
    """
    Check if text matches a pattern.

    Pattern structure:
    - keywords_any_of: At least ONE of these keywords must be present
    - keywords_action: At least ONE of these action words must be present (optional)
    - keywords_all_of: ALL of these keywords must be present (optional)
    """
    normalized = normalize_text(text)

    # Check keywords_any_of (at least one must be present)
    if "keywords_any_of" in pattern:
        keywords = pattern["keywords_any_of"]
        if not any(kw.lower() in normalized for kw in keywords):
            return False

    # Check keywords_action (at least one must be present)
    if "keywords_action" in pattern:
        keywords_action = pattern["keywords_action"]
        if not any(kw.lower() in normalized for kw in keywords_action):
            return False

    # Check keywords_all_of (all must be present)
    if "keywords_all_of" in pattern:
        keywords_all = pattern["keywords_all_of"]
        if not all(kw.lower() in normalized for kw in keywords_all):
            return False

    return True


def match_lightweight(text: str) -> Optional[TemplateMatch]:
    """
    Check if request matches lightweight workflow patterns.

    Returns:
        TemplateMatch if matched, None otherwise
    """
    for pattern in LIGHTWEIGHT_PATTERNS:
        if matches_pattern(text, pattern):
            return TemplateMatch(
                matched=True,
                workflow="adw_lightweight_iso",
                model_set="base",
                classification=pattern["classification"],
                confidence=pattern["confidence"],
                pattern_name=pattern["name"],
            )
    return None


def match_standard(text: str) -> Optional[TemplateMatch]:
    """
    Check if request matches standard SDLC patterns.

    Returns:
        TemplateMatch if matched, None otherwise
    """
    for pattern in STANDARD_PATTERNS:
        if matches_pattern(text, pattern):
            return TemplateMatch(
                matched=True,
                workflow="adw_sdlc_iso",
                model_set="base",
                classification=pattern["classification"],
                confidence=pattern["confidence"],
                pattern_name=pattern["name"],
            )
    return None


def match_bug(text: str) -> Optional[TemplateMatch]:
    """
    Check if request matches bug fix patterns.

    Returns:
        TemplateMatch if matched, None otherwise
    """
    for pattern in BUG_PATTERNS:
        if matches_pattern(text, pattern):
            return TemplateMatch(
                matched=True,
                workflow="adw_plan_build_test_iso",
                model_set="base",
                classification="bug",
                confidence=pattern["confidence"],
                pattern_name=pattern["name"],
            )
    return None


def route_by_template(nl_input: str) -> TemplateMatch:
    """
    Main template routing function.

    Tries to match request against known patterns in priority order:
    1. Bugs (highest priority - need testing)
    2. Lightweight (cost optimization)
    3. Standard SDLC (fallback for known patterns)
    4. No match (return unmatched)

    Args:
        nl_input: Natural language request

    Returns:
        TemplateMatch object with routing decision
    """
    # Priority 1: Bug patterns (need thorough testing)
    bug_match = match_bug(nl_input)
    if bug_match:
        return bug_match

    # Priority 2: Lightweight patterns (cost optimization)
    lightweight_match = match_lightweight(nl_input)
    if lightweight_match:
        return lightweight_match

    # Priority 3: Standard patterns
    standard_match = match_standard(nl_input)
    if standard_match:
        return standard_match

    # No match - defer to structured prompts
    return TemplateMatch(matched=False)


def detect_characteristics(nl_input: str) -> Dict[str, any]:
    """
    Detect request characteristics for workflow routing.

    This is used when template matching fails, to help the structured
    prompt system make better routing decisions.

    Returns:
        Dictionary with characteristics:
        - ui_only: bool
        - backend_changes: bool
        - testing_needed: bool
        - docs_only: bool
        - file_count_estimate: int (1=single, 2=few, 3=many)
    """
    normalized = normalize_text(nl_input)

    characteristics = {
        "ui_only": False,
        "backend_changes": False,
        "testing_needed": False,
        "docs_only": False,
        "file_count_estimate": 2,  # Default: assume few files
    }

    # UI-only indicators
    ui_keywords = ["component", "styling", "css", "ui", "display", "show", "hide", "tab", "button", "color"]
    if any(kw in normalized for kw in ui_keywords):
        characteristics["ui_only"] = True
        characteristics["file_count_estimate"] = 1

    # Backend indicators
    backend_keywords = ["api", "database", "server", "endpoint", "backend", "sql", "query"]
    if any(kw in normalized for kw in backend_keywords):
        characteristics["backend_changes"] = True
        characteristics["ui_only"] = False
        characteristics["file_count_estimate"] = 3

    # Testing indicators
    test_keywords = ["test", "testing", "validation", "auth", "security"]
    if any(kw in normalized for kw in test_keywords):
        characteristics["testing_needed"] = True

    # Docs-only indicators
    docs_keywords = ["documentation", "readme", "docs", "comment"]
    if any(kw in normalized for kw in docs_keywords):
        characteristics["docs_only"] = True
        characteristics["file_count_estimate"] = 1

    # Single-file indicators
    single_file_keywords = ["single", "one file", "typo", "fix button"]
    if any(kw in normalized for kw in single_file_keywords):
        characteristics["file_count_estimate"] = 1

    return characteristics
