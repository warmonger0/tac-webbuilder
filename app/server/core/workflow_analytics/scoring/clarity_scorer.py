"""
Natural Language Input Clarity Scoring.

This module calculates clarity scores for workflow natural language inputs.
"""

import logging

logger = logging.getLogger(__name__)


def calculate_nl_input_clarity_score(workflow: dict) -> float:
    """
    Calculate natural language input clarity score (0-100).

    Evaluates based on:
    - Word count (optimal range: 100-200 words)
    - Presence of clear criteria (bullet points, numbers, specific terms)
    - Verbosity penalty (>500 words)
    - Brevity penalty (<50 words)

    Args:
        workflow: Workflow data containing nl_input field

    Returns:
        Clarity score between 0.0 and 100.0
    """
    try:
        nl_input = workflow.get("nl_input", "")
        if not nl_input:
            return 0.0

        # Calculate word count
        words = nl_input.split()
        word_count = len(words)

        # Base score from word count
        if word_count < 10:
            # Very short input
            base_score = 10.0
        elif word_count < 50:
            # Short input - scale from 20 to 50
            base_score = 20.0 + (word_count - 10) * (30.0 / 40.0)
        elif word_count < 100:
            # Approaching optimal - scale from 50 to 80
            base_score = 50.0 + (word_count - 50) * (30.0 / 50.0)
        elif word_count <= 200:
            # Optimal range - high scores (80-90)
            base_score = 80.0 + (word_count - 100) * (10.0 / 100.0)
        elif word_count <= 500:
            # Starting to get verbose - scale from 70 down to 50
            base_score = 70.0 - (word_count - 200) * (20.0 / 300.0)
        else:
            # Too verbose - penalty
            base_score = max(30.0, 50.0 - (word_count - 500) * 0.02)

        # Bonus for clear criteria indicators
        criteria_bonus = 0
        criteria_indicators = [
            '-', '•', '*',  # Bullet points
            '1.', '2.', '3.',  # Numbered lists
            'must', 'should', 'require', 'need',  # Requirements
            'step', 'phase', 'stage',  # Structure
            'test', 'validate', 'verify',  # Quality indicators
        ]

        for indicator in criteria_indicators:
            if indicator in nl_input.lower():
                criteria_bonus += 2
                if criteria_bonus >= 10:
                    break

        final_score = min(100.0, base_score + criteria_bonus)
        return max(0.0, final_score)

    except Exception as e:
        logger.error(f"Error calculating clarity score: {e}")
        return 0.0
