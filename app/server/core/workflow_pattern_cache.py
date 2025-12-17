"""
Workflow Pattern Caching

Learns from completed workflows to provide instant dry-run estimates.
Matches new features against learned patterns to skip full analysis.
"""

import json
import logging
import re
from typing import Any
from difflib import SequenceMatcher

from database import get_database_adapter

logger = logging.getLogger(__name__)

# Similarity threshold for pattern matching (0.0-1.0)
SIMILARITY_THRESHOLD = 0.70  # 70% similar = use cached pattern


def extract_workflow_pattern(
    feature_id: int,
    feature_title: str,
    feature_description: str | None,
    phases: list,
    total_cost: float,
    total_time_minutes: int,
    total_tokens: int
) -> dict[str, Any]:
    """
    Extract pattern characteristics from a completed workflow.

    Args:
        feature_id: Feature ID
        feature_title: Feature title
        feature_description: Feature description
        phases: List of phase plan objects
        total_cost: Total workflow cost
        total_time_minutes: Total execution time
        total_tokens: Total tokens used

    Returns:
        Pattern dictionary ready for storage
    """
    # Create normalized signature from title
    signature = _normalize_text(feature_title)

    # Extract key characteristics
    characteristics = {
        "title_keywords": _extract_keywords(feature_title),
        "description_keywords": _extract_keywords(feature_description or ""),
        "phase_count": len(phases),
        "phase_types": [p.title for p in phases],
        "total_files": sum(len(p.files_to_modify) if hasattr(p, 'files_to_modify') else 0 for p in phases),
        "risk_distribution": {
            "low": sum(1 for p in phases if hasattr(p, 'risk_level') and p.risk_level == "low"),
            "medium": sum(1 for p in phases if hasattr(p, 'risk_level') and p.risk_level == "medium"),
            "high": sum(1 for p in phases if hasattr(p, 'risk_level') and p.risk_level == "high"),
        },
    }

    pattern = {
        "pattern_signature": f"workflow:{signature[:50]}",
        "pattern_type": "workflow",
        "typical_input_pattern": json.dumps({
            "title": feature_title,
            "description": feature_description or "",
            "characteristics": characteristics
        }),
        "avg_tokens_with_llm": total_tokens,  # Store as "with LLM" even though dry-run doesn't use LLM
        "avg_cost_with_llm": total_cost,
        "avg_duration_minutes": total_time_minutes,
        "occurrence_count": 1,
        "automation_status": "template",  # Mark as template for reuse
        "confidence_score": 50.0,  # Start with moderate confidence
    }

    return pattern


def find_similar_pattern(
    feature_title: str,
    feature_description: str | None,
    estimated_hours: float | None = None
) -> dict[str, Any] | None:
    """
    Find a similar workflow pattern from cache.

    Args:
        feature_title: Title of new feature
        feature_description: Description of new feature
        estimated_hours: Estimated hours (optional, for better matching)

    Returns:
        Cached pattern if found with >70% similarity, None otherwise
    """
    try:
        adapter = get_database_adapter()
        placeholder = adapter.get_placeholder()

        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Get all workflow patterns
            cursor.execute(f"""
                SELECT
                    id,
                    pattern_signature,
                    typical_input_pattern,
                    avg_tokens_with_llm,
                    avg_cost_with_llm,
                    avg_duration_minutes,
                    occurrence_count,
                    confidence_score
                FROM operation_patterns
                WHERE pattern_type = {placeholder}
                AND automation_status = {placeholder}
                ORDER BY occurrence_count DESC
                LIMIT 50
            """, ("workflow", "template"))

            patterns = cursor.fetchall()

            if not patterns:
                logger.debug("No workflow patterns found in cache")
                return None

            # Find best match
            best_match = None
            best_similarity = 0.0

            for pattern in patterns:
                # Parse stored pattern
                input_pattern = json.loads(
                    pattern['typical_input_pattern'] if isinstance(pattern, dict)
                    else pattern[2]
                )

                # Calculate similarity
                similarity = _calculate_similarity(
                    feature_title,
                    feature_description or "",
                    input_pattern.get("title", ""),
                    input_pattern.get("description", "")
                )

                if similarity > best_similarity and similarity >= SIMILARITY_THRESHOLD:
                    best_similarity = similarity
                    best_match = {
                        "id": pattern['id'] if isinstance(pattern, dict) else pattern[0],
                        "signature": pattern['pattern_signature'] if isinstance(pattern, dict) else pattern[1],
                        "input_pattern": input_pattern,
                        "avg_tokens": pattern['avg_tokens_with_llm'] if isinstance(pattern, dict) else pattern[3],
                        "avg_cost": pattern['avg_cost_with_llm'] if isinstance(pattern, dict) else pattern[4],
                        "avg_duration_minutes": pattern['avg_duration_minutes'] if isinstance(pattern, dict) else pattern[5],
                        "occurrence_count": pattern['occurrence_count'] if isinstance(pattern, dict) else pattern[6],
                        "confidence_score": pattern['confidence_score'] if isinstance(pattern, dict) else pattern[7],
                        "similarity": similarity,
                    }

            if best_match:
                logger.info(
                    f"Found similar pattern: {best_match['signature']} "
                    f"(similarity: {best_similarity:.1%}, occurrences: {best_match['occurrence_count']})"
                )
                return best_match

            logger.debug(f"No similar patterns found (best similarity: {best_similarity:.1%})")
            return None

    except Exception as e:
        logger.error(f"Error finding similar pattern: {e}", exc_info=True)
        return None


def save_workflow_pattern(pattern: dict[str, Any]) -> int | None:
    """
    Save or update a workflow pattern in the database.

    Args:
        pattern: Pattern dictionary from extract_workflow_pattern()

    Returns:
        Pattern ID if successful, None otherwise
    """
    try:
        adapter = get_database_adapter()
        placeholder = adapter.get_placeholder()

        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Check if pattern already exists
            cursor.execute(f"""
                SELECT id, occurrence_count
                FROM operation_patterns
                WHERE pattern_signature = {placeholder}
            """, (pattern["pattern_signature"],))

            existing = cursor.fetchone()

            if existing:
                # Update existing pattern (running average)
                pattern_id = existing['id'] if isinstance(existing, dict) else existing[0]
                old_count = existing['occurrence_count'] if isinstance(existing, dict) else existing[1]
                new_count = old_count + 1

                cursor.execute(f"""
                    UPDATE operation_patterns
                    SET
                        occurrence_count = {placeholder},
                        avg_tokens_with_llm = (avg_tokens_with_llm * {placeholder} + {placeholder}) / {placeholder},
                        avg_cost_with_llm = (avg_cost_with_llm * {placeholder} + {placeholder}) / {placeholder},
                        avg_duration_minutes = (COALESCE(avg_duration_minutes, 0) * {placeholder} + {placeholder}) / {placeholder},
                        last_seen = CURRENT_TIMESTAMP
                    WHERE id = {placeholder}
                """, (
                    new_count,
                    old_count, pattern["avg_tokens_with_llm"], new_count,
                    old_count, pattern["avg_cost_with_llm"], new_count,
                    old_count, pattern["avg_duration_minutes"], new_count,
                    pattern_id
                ))

                logger.info(f"Updated pattern {pattern['pattern_signature']} (occurrences: {new_count})")
                return pattern_id

            else:
                # Insert new pattern
                cursor.execute(f"""
                    INSERT INTO operation_patterns (
                        pattern_signature,
                        pattern_type,
                        typical_input_pattern,
                        occurrence_count,
                        automation_status,
                        confidence_score,
                        avg_tokens_with_llm,
                        avg_cost_with_llm,
                        avg_duration_minutes,
                        created_at,
                        last_seen
                    ) VALUES (
                        {placeholder}, {placeholder}, {placeholder}, {placeholder},
                        {placeholder}, {placeholder}, {placeholder}, {placeholder},
                        {placeholder}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """, (
                    pattern["pattern_signature"],
                    pattern["pattern_type"],
                    pattern["typical_input_pattern"],
                    pattern["occurrence_count"],
                    pattern["automation_status"],
                    pattern["confidence_score"],
                    pattern["avg_tokens_with_llm"],
                    pattern["avg_cost_with_llm"],
                    pattern.get("avg_duration_minutes", 0)
                ))

                # Get the inserted ID
                if adapter.get_db_type() == "postgresql":
                    cursor.execute("SELECT lastval()")
                    pattern_id = cursor.fetchone()[0]
                else:
                    pattern_id = cursor.lastrowid

                conn.commit()

                logger.info(f"Created new pattern {pattern['pattern_signature']} (ID: {pattern_id})")
                return pattern_id

    except Exception as e:
        logger.error(f"Error saving workflow pattern: {e}", exc_info=True)
        return None


# ============================================================================
# Helper Functions
# ============================================================================

def _normalize_text(text: str) -> str:
    """Normalize text for signature generation."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', '_', text)
    return text.strip()


def _extract_keywords(text: str) -> list[str]:
    """Extract important keywords from text."""
    # Remove common words
    stop_words = {
        'a', 'an', 'and', 'the', 'to', 'for', 'of', 'in', 'on', 'at',
        'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did',
        'this', 'that', 'these', 'those',
        'with', 'from', 'by'
    }

    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    keywords = [w for w in words if w not in stop_words]

    # Return top 10 most common (frequency-based)
    from collections import Counter
    return [word for word, _ in Counter(keywords).most_common(10)]


def _calculate_similarity(
    title1: str,
    desc1: str,
    title2: str,
    desc2: str
) -> float:
    """
    Calculate similarity between two feature descriptions.

    Uses weighted combination of:
    - Title similarity (70% weight)
    - Description similarity (30% weight)

    Args:
        title1: First feature title
        desc1: First feature description
        title2: Second feature title
        desc2: Second feature description

    Returns:
        Similarity score (0.0-1.0)
    """
    # Title similarity (most important)
    title_sim = SequenceMatcher(None, title1.lower(), title2.lower()).ratio()

    # Description similarity
    if desc1 and desc2:
        desc_sim = SequenceMatcher(None, desc1.lower(), desc2.lower()).ratio()
    else:
        desc_sim = 0.0

    # Weighted average (title is more important)
    similarity = (title_sim * 0.7) + (desc_sim * 0.3)

    return similarity
