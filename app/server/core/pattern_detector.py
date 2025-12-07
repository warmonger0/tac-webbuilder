"""
Pattern Detection Engine for Out-Loop Coding

Analyzes complete workflows to identify patterns and extract characteristics.
"""

import logging
import re

from .pattern_signatures import extract_operation_signature

logger = logging.getLogger(__name__)


# ============================================================================
# PATTERN DETECTION FROM WORKFLOWS
# ============================================================================

def detect_patterns_in_workflow(workflow: dict) -> list[str]:
    """
    Analyze a workflow and extract all operation patterns.

    This function performs multi-level pattern detection:
    1. Primary pattern from nl_input (most reliable)
    2. Secondary patterns from error messages (what was attempted)
    3. Tertiary patterns from workflow template (backup)

    Args:
        workflow: Complete workflow dictionary from workflow_history table

    Returns:
        List of pattern signatures found in this workflow (de-duplicated)

    Example:
        >>> workflow = {
        ...     "nl_input": "Run backend tests with pytest",
        ...     "error_message": "typecheck failed",
        ...     "workflow_template": "adw_sdlc_iso"
        ... }
        >>> detect_patterns_in_workflow(workflow)
        ['test:pytest:backend', 'build:typecheck:backend']
    """
    patterns = []

    # Layer 1: Primary pattern from nl_input
    primary = extract_operation_signature(workflow)
    if primary:
        patterns.append(primary)
        logger.debug(f"[Pattern] Primary pattern detected: {primary}")

    # Layer 2: Secondary patterns from error messages
    error_msg = workflow.get("error_message", "")
    if error_msg:
        error_patterns = _extract_patterns_from_errors(error_msg)
        for ep in error_patterns:
            if ep not in patterns:
                patterns.append(ep)
                logger.debug(f"[Pattern] Error-based pattern detected: {ep}")

    # Layer 3: Tertiary pattern from workflow template
    template_pattern = _extract_pattern_from_template(workflow.get("workflow_template"))
    if template_pattern and template_pattern not in patterns:
        patterns.append(template_pattern)
        logger.debug(f"[Pattern] Template-based pattern detected: {template_pattern}")

    return patterns


def _extract_patterns_from_errors(error_message: str) -> list[str]:
    """
    Extract operation patterns from error messages.

    Error messages reveal what operations were attempted, even if they failed.
    This helps identify patterns that might not be obvious from nl_input alone.

    Args:
        error_message: Error message from workflow execution

    Returns:
        List of pattern signatures inferred from errors

    Example:
        >>> _extract_patterns_from_errors("pytest failed: 3 tests failed")
        ['test:pytest:backend']
    """
    patterns = []
    error_lower = error_message.lower()

    # Test failures indicate test operation
    if any(kw in error_lower for kw in ["test failed", "pytest", "tests failed"]):
        patterns.append("test:pytest:backend")

    # Vitest failures
    if "vitest" in error_lower:
        patterns.append("test:vitest:frontend")

    # Build failures indicate build operation
    if any(kw in error_lower for kw in ["type error", "typecheck", "tsc"]):
        patterns.append("build:typecheck:backend")

    # Compilation errors
    if "compilation" in error_lower or "compile error" in error_lower:
        patterns.append("build:compile:backend")

    # Linting errors
    if "eslint" in error_lower or "lint" in error_lower:
        patterns.append("format:eslint:all")

    return patterns


def _extract_pattern_from_template(template: str | None) -> str | None:
    """
    Extract pattern from workflow template name.

    Template names often indicate the type of operation (test, build, plan).
    This is a fallback when nl_input is ambiguous.

    Args:
        template: Workflow template name

    Returns:
        Pattern signature, or None if template doesn't indicate a pattern

    Example:
        >>> _extract_pattern_from_template("adw_test_iso")
        'test:generic:all'
        >>> _extract_pattern_from_template("sdlc")
        None  # SDLC workflows are orchestration flows, not patterns
    """
    if not template:
        return None

    template_lower = template.lower()

    # Specific template patterns
    # NOTE: Template-based patterns should only detect specific operations (test, build, format)
    # NOT entire orchestration flows. ADW workflows are not patterns - patterns exist WITHIN workflows
    if "test" in template_lower:
        return "test:generic:all"
    elif "build" in template_lower:
        return "build:generic:all"
    elif "plan" in template_lower:
        # Planning workflows don't have automation potential
        return None
    elif "sdlc" in template_lower or "zte" in template_lower:
        # SDLC and Zero-Touch workflows are full lifecycle orchestration
        # They are NOT patterns - patterns are deterministic tool sequences within these workflows
        return None
    elif "patch" in template_lower or "lightweight" in template_lower:
        # Patch workflows are orchestration flows, not patterns
        return None
    elif "ship" in template_lower:
        return "deploy:ship:all"
    elif "review" in template_lower:
        return "review:code:all"
    elif "cleanup" in template_lower:
        # Cleanup doesn't have automation potential
        return None

    return None


# ============================================================================
# PATTERN CHARACTERISTICS EXTRACTION
# ============================================================================

def extract_pattern_characteristics(workflow: dict) -> dict:
    """
    Extract characteristics that help identify and classify patterns.

    Characteristics are used to:
    - Calculate confidence scores
    - Match similar workflows
    - Estimate automation value
    - Filter patterns for specific use cases

    Args:
        workflow: Complete workflow dictionary

    Returns:
        Dictionary with extracted characteristics:
        {
            'input_length': 150,
            'keywords': ['test', 'pytest', 'backend'],
            'files_mentioned': ['tests/', 'app/server/'],
            'duration_range': 'medium',  # short, medium, long
            'complexity': 'simple',       # simple, medium, complex
            'error_count': 2
        }

    Example:
        >>> workflow = {
        ...     "nl_input": "Run backend tests with pytest",
        ...     "duration_seconds": 120,
        ...     "error_count": 0
        ... }
        >>> chars = extract_pattern_characteristics(workflow)
        >>> chars['complexity']
        'simple'
        >>> chars['duration_range']
        'short'
    """
    # Safely extract nl_input, handling None from database
    nl_input_raw = workflow.get("nl_input")
    nl_input = nl_input_raw if nl_input_raw is not None else ""

    # Safely extract numeric fields, handling None from database
    duration_raw = workflow.get("duration_seconds")
    duration = duration_raw if duration_raw is not None else 0

    error_count_raw = workflow.get("error_count")
    error_count = error_count_raw if error_count_raw is not None else 0

    # Extract keywords
    keywords = _extract_keywords(nl_input)

    # Extract file paths mentioned
    files_mentioned = _extract_file_paths(nl_input)

    # Categorize duration
    if duration < 180:  # < 3 minutes
        duration_range = "short"
    elif duration < 600:  # < 10 minutes
        duration_range = "medium"
    else:
        duration_range = "long"

    # Determine complexity
    word_count = len(nl_input.split())
    if word_count < 50 and error_count < 3:
        complexity = "simple"
    elif word_count > 200 or error_count > 5:
        complexity = "complex"
    else:
        complexity = "medium"

    return {
        "input_length": len(nl_input),
        "keywords": keywords,
        "files_mentioned": files_mentioned,
        "duration_range": duration_range,
        "complexity": complexity,
        "error_count": error_count
    }


def _extract_keywords(text: str) -> list[str]:
    """
    Extract significant keywords from text.

    Keywords help identify the type and scope of operations.

    Args:
        text: Natural language input text

    Returns:
        List of found keywords

    Example:
        >>> _extract_keywords("Run backend tests with pytest")
        ['test', 'pytest', 'backend']
    """
    # Handle None or empty text
    if not text:
        return []

    # Common operation keywords
    operation_keywords = [
        "test", "pytest", "vitest", "jest", "build", "typecheck", "compile",
        "format", "lint", "update", "install", "deploy", "run"
    ]

    # Target keywords
    target_keywords = [
        "backend", "frontend", "server", "client", "api", "ui"
    ]

    found = []
    text_lower = text.lower()

    for keyword in operation_keywords + target_keywords:
        if keyword in text_lower:
            found.append(keyword)

    return found


def _extract_file_paths(text: str) -> list[str]:
    """
    Extract file paths or glob patterns from text.

    File paths help identify the scope of operations and can be used
    to match patterns to specific parts of the codebase.

    Args:
        text: Natural language input text

    Returns:
        List of file paths/patterns found

    Example:
        >>> _extract_file_paths("Run tests in app/server/tests/")
        ['app/server/tests/']
    """
    # Handle None or empty text
    if not text:
        return []

    # Look for common path patterns
    patterns = [
        r'(app/\w+/[\w/]*)',  # app/server/..., app/client/...
        r'(tests?/[\w/]*)',   # tests/..., test/...
        r'(src/[\w/]*)',      # src/...
        r'(\w+\.py)',         # *.py files
        r'(\w+\.ts)',         # *.ts files
        r'(\w+\.js)',         # *.js files
    ]

    paths = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        paths.extend(matches)

    return list(set(paths))  # Remove duplicates


# ============================================================================
# CONFIDENCE SCORE CALCULATION
# ============================================================================

def calculate_confidence_score(pattern_data: dict, workflows: list[dict]) -> float:
    """
    Calculate confidence score for a pattern based on occurrence data.

    Confidence score is calculated from three components:
    1. **Frequency** (0-40 points) - How often the pattern occurs
    2. **Consistency** (0-30 points) - How similar workflows are
    3. **Success Rate** (0-30 points) - How often it succeeds without errors

    Args:
        pattern_data: Dictionary with pattern info (occurrence_count, pattern_type)
        workflows: List of workflow dictionaries that match this pattern

    Returns:
        Confidence score from 0.0 to 100.0

    Example:
        >>> pattern_data = {"occurrence_count": 10, "pattern_type": "test"}
        >>> workflows = [
        ...     {"error_count": 0, "duration_seconds": 120, "retry_count": 0},
        ...     {"error_count": 0, "duration_seconds": 125, "retry_count": 0},
        ...     {"error_count": 1, "duration_seconds": 130, "retry_count": 0}
        ... ]
        >>> calculate_confidence_score(pattern_data, workflows)
        85.0  # High frequency + high consistency + good success rate
    """
    if not workflows:
        return 10.0  # Base score for new patterns

    occurrence_count = pattern_data.get("occurrence_count", 0)

    # Component 1: Occurrence frequency (0-40 points)
    # More occurrences = higher confidence that this is a real pattern
    if occurrence_count >= 10:
        frequency_score = 40.0
    elif occurrence_count >= 5:
        frequency_score = 30.0
    elif occurrence_count >= 3:
        frequency_score = 20.0
    else:
        frequency_score = 10.0

    # Component 2: Consistency (0-30 points)
    # Calculate variance in duration and error rates
    durations = [w.get("duration_seconds", 0) for w in workflows if w.get("duration_seconds")]
    error_counts = [w.get("error_count", 0) for w in workflows if w.get("error_count") is not None]

    if durations and len(durations) > 1:
        avg_duration = sum(durations) / len(durations)
        duration_variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations)

        # Low variance = high consistency = good automation candidate
        if duration_variance < 100:  # Very consistent (within ~10 seconds)
            consistency_score = 30.0
        elif duration_variance < 1000:  # Moderately consistent
            consistency_score = 20.0
        else:  # High variance
            consistency_score = 10.0
    else:
        consistency_score = 15.0  # Default for insufficient data

    # Component 3: Success rate (0-30 points)
    # Patterns with low error rates are more reliable for automation
    avg_errors = sum(error_counts) / len(error_counts) if error_counts else 0
    avg_retries = sum(w.get("retry_count", 0) for w in workflows) / len(workflows) if workflows else 0

    if avg_errors == 0 and avg_retries == 0:
        success_score = 30.0  # Perfect success rate
    elif avg_errors < 1 and avg_retries < 2:
        success_score = 20.0  # Good success rate
    elif avg_errors < 3:
        success_score = 10.0  # Moderate success rate
    else:
        success_score = 5.0  # Poor success rate

    # Total confidence score
    total_score = frequency_score + consistency_score + success_score

    # Clamp to [0, 100]
    return min(100.0, max(0.0, total_score))


# ============================================================================
# BATCH PROCESSING
# ============================================================================

def process_workflow_for_patterns(workflow: dict) -> dict:
    """
    Main entry point for pattern detection on a single workflow.

    This is a pure function that doesn't interact with the database.
    It returns all detected information for the caller to persist.

    Args:
        workflow: Complete workflow dictionary

    Returns:
        Dictionary with detection results:
        {
            'patterns': ['test:pytest:backend', 'build:typecheck:backend'],
            'characteristics': {
                'input_length': 150,
                'keywords': ['test', 'pytest', 'backend'],
                ...
            }
        }

    Example:
        >>> workflow = {
        ...     "nl_input": "Run backend tests with pytest",
        ...     "duration_seconds": 120,
        ...     "error_count": 0
        ... }
        >>> result = process_workflow_for_patterns(workflow)
        >>> result['patterns']
        ['test:pytest:backend']
    """
    # Detect all patterns
    patterns = detect_patterns_in_workflow(workflow)

    # Extract characteristics
    characteristics = extract_pattern_characteristics(workflow)

    return {
        "patterns": patterns,
        "characteristics": characteristics
    }
