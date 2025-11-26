"""
Workflow Similarity Analysis.

This module provides functions for calculating text similarity and finding similar workflows.
"""

import logging
from typing import Union

from .helpers import detect_complexity

logger = logging.getLogger(__name__)


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two text strings using Jaccard index.

    The Jaccard index measures similarity as the intersection over union of word sets.
    This is a simple but effective measure for comparing natural language inputs.

    Args:
        text1: First text string to compare
        text2: Second text string to compare

    Returns:
        Similarity score from 0.0 (no overlap) to 1.0 (identical)

    Examples:
        >>> calculate_text_similarity("hello world", "hello world")
        1.0
        >>> calculate_text_similarity("foo bar", "baz qux")
        0.0
        >>> calculate_text_similarity("implement auth system", "add authentication")
        0.2  # "auth"/"authentication" don't match in simple word overlap
    """
    # Handle edge cases
    if not text1 or not text2:
        return 0.0

    # Normalize and tokenize
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    # Calculate Jaccard similarity: |intersection| / |union|
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


def find_similar_workflows(workflow: dict, all_workflows: list[dict]) -> Union[list[str], list[dict]]:
    """
    Find similar workflows using multi-factor similarity scoring.

    Supports two modes for backward compatibility:
    - New mode (Phase 3E): Uses 'adw_id' field, returns list of ADW ID strings
    - Old mode: Uses 'id' field, returns list of full workflow dictionaries

    Similarity is determined by combining multiple factors:
    - Classification type match: 30 points
    - Workflow template match: 30 points
    - Complexity level match: 20 points
    - Natural language input similarity: 0-20 points (text similarity * 20)

    Only workflows with a total score >= 70 points are considered similar.
    Returns the top 10 most similar workflows, sorted by score.

    Args:
        workflow: Target workflow to find matches for
        all_workflows: List of all historical workflows

    Returns:
        List of ADW IDs (new mode) or list of workflow dictionaries (old mode)

    Example:
        >>> workflow = {
        ...     'adw_id': '1',
        ...     'classification_type': 'feature',
        ...     'workflow_template': 'adw_plan_build_test',
        ...     'nl_input': 'implement user authentication',
        ...     # ... other fields
        ... }
        >>> similar_ids = find_similar_workflows(workflow, all_workflows)
        >>> print(similar_ids)  # ['adw-abc123', 'adw-def456', ...]
    """
    try:
        # Determine mode: new (adw_id) or old (id)
        current_id = workflow.get('adw_id')
        old_mode = False
        if not current_id:
            current_id = workflow.get('id')
            old_mode = True

        if not current_id:
            logger.warning("Workflow missing adw_id or id, cannot find similar workflows")
            return []

        # Old mode: simple template + model matching for backward compatibility
        if old_mode:
            candidates = []
            for candidate in all_workflows:
                # Skip the same workflow
                if candidate.get('id') == current_id:
                    continue

                # Match on workflow_template and model_used
                if (workflow.get('workflow_template') == candidate.get('workflow_template') and
                    workflow.get('model_used') == candidate.get('model_used')):
                    # Calculate duration proximity for sorting
                    current_duration = workflow.get('duration_seconds', 0)
                    candidate_duration = candidate.get('duration_seconds', 0)
                    duration_diff = abs(current_duration - candidate_duration)

                    candidates.append({
                        'workflow': candidate,
                        'duration_diff': duration_diff
                    })

            # Sort by duration proximity (closest first)
            candidates.sort(key=lambda x: x['duration_diff'])

            # Return workflow objects
            return [c['workflow'] for c in candidates]

        # New mode: multi-factor scoring
        candidates = []

        for candidate in all_workflows:
            # Skip the same workflow
            if candidate.get('adw_id') == current_id:
                continue

            similarity_score = 0.0

            # Factor 1: Same classification type (30 points)
            if workflow.get('classification_type') == candidate.get('classification_type'):
                similarity_score += 30

            # Factor 2: Same workflow template (30 points)
            if workflow.get('workflow_template') == candidate.get('workflow_template'):
                similarity_score += 30

            # Factor 3: Similar complexity (20 points)
            current_complexity = detect_complexity(workflow)
            candidate_complexity = detect_complexity(candidate)
            if current_complexity == candidate_complexity:
                similarity_score += 20

            # Factor 4: Similar NL input (0-20 points based on text similarity)
            current_nl = workflow.get('nl_input', '')
            candidate_nl = candidate.get('nl_input', '')
            text_sim = calculate_text_similarity(current_nl, candidate_nl)
            similarity_score += text_sim * 20

            # Only include if similarity >= 70 points (strong match)
            if similarity_score >= 70:
                candidates.append({
                    'adw_id': candidate['adw_id'],
                    'similarity_score': similarity_score
                })

        # Sort by similarity score (highest first)
        candidates.sort(key=lambda x: x['similarity_score'], reverse=True)

        # Return top 10 ADW IDs only
        return [c['adw_id'] for c in candidates[:10]]

    except Exception as e:
        logger.error(f"Error finding similar workflows: {e}")
        return []
