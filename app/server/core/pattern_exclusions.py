"""
Pattern Exclusions - Filter Out Normal Workflow Orchestration

Based on Session 1.5 analysis of 39,274 hook events, we identified 117 high-frequency
tool sequences that are ALL normal workflow orchestration (not wasteful patterns).

This module defines exclusion rules so the pattern detection system only flags
truly anomalous patterns worth investigating for automation.
"""


# ============================================================================
# NORMAL ORCHESTRATION PATTERNS (DO NOT FLAG AS AUTOMATION OPPORTUNITIES)
# ============================================================================

def is_normal_orchestration_pattern(tool_sequence: list[str]) -> tuple[bool, str]:
    """
    Check if a tool sequence is normal workflow orchestration.

    Returns:
        (is_normal, reason) - True if pattern should be excluded, with explanation

    Example:
        >>> is_normal_orchestration_pattern(['TodoWrite', 'Bash', 'Bash'])
        (True, "Normal task tracking: Update todo → run commands")
    """
    # Convert to tuple for easier pattern matching
    seq = tuple(tool_sequence)

    # Category 1: Task Tracking Patterns (TodoWrite sequences)
    # These are INTENDED behavior - we WANT the LLM to track progress
    if 'TodoWrite' in seq:
        if seq.count('TodoWrite') >= 1 and seq.count('Bash') >= 1:
            return True, "Normal task tracking: TodoWrite + Bash orchestration"

        if seq.count('TodoWrite') >= 1 and seq.count('Read') >= 1:
            return True, "Normal task tracking: TodoWrite + Read orchestration"

        if seq.count('TodoWrite') >= 1 and seq.count('Edit') >= 1:
            return True, "Normal task tracking: TodoWrite + Edit orchestration"

    # Category 2: Command → Inspect Patterns (Bash → Read)
    # LLM needs to inspect results after running commands
    if 'Bash' in seq and 'Read' in seq:
        # Allow up to 2 Bash, 2 Read in a sequence
        if seq.count('Bash') <= 2 and seq.count('Read') <= 2:
            return True, "Normal verification: Bash → Read inspection pattern"

    # Category 3: Multi-Read Patterns (Context Gathering)
    # Reading multiple files is normal when understanding codebase
    if seq.count('Read') >= 2 and len(set(seq)) == 1:  # Only Read tools
        return True, "Normal context gathering: Multiple Read operations"

    # Category 4: Multi-Edit Patterns (Batch Modifications)
    # Multiple edits in sequence are normal during refactoring
    if seq.count('Edit') >= 2 and len(set(seq)) <= 2:  # Mostly Edit
        return True, "Normal refactoring: Multiple Edit operations"

    # Category 5: Search → Read → Edit (Normal Code Modification)
    # Grep → Read → Edit is intelligent code modification, not wasteful
    if 'Grep' in seq and 'Read' in seq and 'Edit' in seq:
        return True, "Normal code modification: Search → Read → Edit pattern"

    # Category 6: Read → Edit → Bash (Standard Change Workflow)
    # Read file → modify → verify is proper workflow
    if seq.count('Read') >= 1 and seq.count('Edit') >= 1 and seq.count('Bash') >= 1:
        return True, "Normal change workflow: Read → Edit → Verify pattern"

    # Not a normal pattern - might be worth investigating
    return False, ""


def should_flag_for_automation(tool_sequence: list[str], occurrence_count: int) -> tuple[bool, str]:
    """
    Determine if a pattern should be flagged as automation opportunity.

    Criteria:
    1. NOT a normal orchestration pattern
    2. High frequency (50+ occurrences)
    3. Contains mixed tools (at least 2 different types)
    4. Has potential for determinism

    Returns:
        (should_flag, reason)
    """
    # Check if it's normal orchestration
    is_normal, normal_reason = is_normal_orchestration_pattern(tool_sequence)
    if is_normal:
        return False, f"Excluded: {normal_reason}"

    # Check frequency
    if occurrence_count < 50:
        return False, "Excluded: Low frequency (< 50 occurrences)"

    # Check for mixed tools
    if len(set(tool_sequence)) < 2:
        return False, "Excluded: Single tool type (not mixed orchestration)"

    # Check for automation-worthy patterns
    # Must have Bash (indicates command execution)
    if 'Bash' not in tool_sequence:
        return False, "Excluded: No Bash commands (unlikely to have automation value)"

    # At this point, it's worth investigating
    return True, "Potential automation candidate: Review manually"


# ============================================================================
# KNOWN VALUABLE PATTERN TYPES (WOULD FLAG IF FOUND)
# ============================================================================

VALUABLE_PATTERN_SIGNATURES = {
    # Error → Fix → Retry patterns
    'bash_error_read_edit_bash_success': {
        'description': 'Command fails → read file → edit → command succeeds',
        'automation_potential': 'High - if error type is deterministic',
        'example': 'pytest import error → add import → pytest success'
    },

    # Type error auto-fix
    'bash_tsc_error_read_edit_bash_success': {
        'description': 'TypeScript error → read type file → edit → type check success',
        'automation_potential': 'High - common type errors are predictable',
        'example': 'Property missing → add property → type check pass'
    },

    # Lint error auto-fix
    'bash_ruff_error_read_edit_bash_success': {
        'description': 'Lint error → read file → edit → lint success',
        'automation_potential': 'Medium - some lint fixes are deterministic',
        'example': 'E501 line too long → break line → lint pass'
    },

    # Import organization
    'grep_imports_read_edit_bash_success': {
        'description': 'Search imports → read → organize → verify',
        'automation_potential': 'Medium - import sorting is deterministic',
        'example': 'Find imports → read file → sort alphabetically → verify'
    }
}


def get_exclusion_stats() -> dict:
    """
    Return statistics about pattern exclusions.

    Useful for debugging and monitoring the exclusion system.
    """
    return {
        'exclusion_categories': {
            'task_tracking': 'TodoWrite + Bash/Read/Edit patterns',
            'command_inspect': 'Bash → Read verification patterns',
            'context_gathering': 'Multiple Read operations',
            'batch_edits': 'Multiple Edit operations',
            'search_modify': 'Grep → Read → Edit patterns',
            'change_workflow': 'Read → Edit → Bash patterns'
        },
        'minimum_frequency': 50,
        'requires_mixed_tools': True,
        'requires_bash': True,
        'known_valuable_patterns': len(VALUABLE_PATTERN_SIGNATURES)
    }


# ============================================================================
# PATTERN CLASSIFICATION
# ============================================================================

def classify_pattern_type(tool_sequence: list[str]) -> str:
    """
    Classify a pattern by its likely purpose.

    Returns:
        Category string (for logging/debugging)
    """
    seq = tuple(tool_sequence)

    if 'TodoWrite' in seq:
        return 'task_tracking'
    elif 'Grep' in seq and 'Edit' in seq:
        return 'search_modify'
    elif seq.count('Read') >= 2:
        return 'context_gathering'
    elif seq.count('Edit') >= 2:
        return 'batch_edits'
    elif 'Bash' in seq and 'Read' in seq:
        return 'command_inspect'
    elif 'Read' in seq and 'Edit' in seq and 'Bash' in seq:
        return 'change_workflow'
    else:
        return 'uncategorized'
