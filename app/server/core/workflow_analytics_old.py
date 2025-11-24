"""
Workflow Analytics Scoring Engine

This module provides comprehensive scoring and analysis functions for ADW workflows.
It calculates four core scoring metrics:
1. NL Input Clarity Score - Evaluates quality and clarity of natural language inputs
2. Cost Efficiency Score - Analyzes cost performance including model appropriateness
3. Performance Score - Measures execution speed and bottleneck detection
4. Quality Score - Assesses error rates and execution quality

Additionally provides:
- Helper functions for temporal extraction and complexity detection
- Anomaly detection with configurable thresholds
- Similar workflow discovery
- Optimization recommendations
"""

import logging
from datetime import datetime
from typing import Union

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================

def extract_hour(timestamp: str) -> int:
    """
    Extract hour (0-23) from ISO timestamp.

    Args:
        timestamp: ISO format timestamp string (e.g., "2025-01-15T14:30:00Z")

    Returns:
        Hour as integer (0-23), or -1 if parsing fails
    """
    try:
        # Handle various ISO format variations (Z, +00:00, etc.)
        if not timestamp:
            return -1

        # Remove timezone markers for consistent parsing
        clean_timestamp = timestamp.replace('Z', '+00:00')

        # Parse ISO format
        dt = datetime.fromisoformat(clean_timestamp)
        return dt.hour
    except (ValueError, AttributeError, TypeError) as e:
        logger.warning(f"Failed to extract hour from timestamp '{timestamp}': {e}")
        return -1


def extract_day_of_week(timestamp: str) -> int:
    """
    Extract day of week from ISO timestamp.

    Args:
        timestamp: ISO format timestamp string

    Returns:
        Day of week as integer (0=Monday, 6=Sunday), or -1 if parsing fails
    """
    try:
        # Handle various ISO format variations
        if not timestamp:
            return -1

        # Remove timezone markers for consistent parsing
        clean_timestamp = timestamp.replace('Z', '+00:00')

        # Parse ISO format
        dt = datetime.fromisoformat(clean_timestamp)
        # Python's weekday() returns 0=Monday, 6=Sunday (exactly what we need)
        return dt.weekday()
    except (ValueError, AttributeError, TypeError) as e:
        logger.warning(f"Failed to extract day of week from timestamp '{timestamp}': {e}")
        return -1


# ============================================================================
# Core Scoring Functions
# ============================================================================

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


def calculate_cost_efficiency_score(workflow: dict) -> float:
    """
    Calculate cost efficiency score (0-100).

    Evaluates based on:
    - Budget variance (under budget = higher score)
    - Cache efficiency (>50% cache hit rate = bonus)
    - Retry penalty (each retry reduces score)
    - Model appropriateness (matches complexity level)

    Args:
        workflow: Workflow data containing cost metrics

    Returns:
        Cost efficiency score between 0.0 and 100.0
        Returns 0.0 for legacy workflows without estimated_cost_total
    """
    try:
        # Validate required data
        estimated_cost = workflow.get("estimated_cost_total")
        if estimated_cost is None or estimated_cost == 0:
            # Legacy workflow without cost estimate - return default score
            logger.debug(f"[SCORING] No estimated_cost_total for workflow {workflow.get('adw_id', 'unknown')} - using default score")
            return 0.0

        actual_cost = workflow.get("actual_cost_total", 0) or 0

        # Calculate budget variance score (60 points max)
        if actual_cost <= estimated_cost * 0.8:
            # Well under budget
            budget_score = 60.0
        elif actual_cost <= estimated_cost:
            # Under budget
            ratio = actual_cost / estimated_cost
            budget_score = 50.0 + (1.0 - ratio) * 50.0
        elif actual_cost <= estimated_cost * 1.2:
            # Slightly over budget
            ratio = actual_cost / estimated_cost
            budget_score = 40.0 - (ratio - 1.0) * 50.0
        else:
            # Significantly over budget
            ratio = actual_cost / estimated_cost
            budget_score = max(10.0, 40.0 - (ratio - 1.2) * 30.0)

        # Cache efficiency bonus (10 points max)
        cache_read_tokens = workflow.get("cache_read_tokens", 0) or 0
        total_input_tokens = workflow.get("total_input_tokens", 0) or 0

        cache_score = 0
        if total_input_tokens > 0:
            cache_efficiency = cache_read_tokens / total_input_tokens
            if cache_efficiency > 0.5:
                cache_score = 10.0
            elif cache_efficiency > 0.3:
                cache_score = 6.0
            elif cache_efficiency > 0.1:
                cache_score = 3.0

        # Retry penalty (10 points deduction per retry)
        retry_count = workflow.get("retry_count", 0) or 0
        retry_penalty = retry_count * 10

        # Model appropriateness scoring (10 points max)
        complexity = detect_complexity(workflow)
        model = workflow.get("model_used", "").lower()

        model_score = 0
        if complexity == "simple" and "haiku" in model or complexity == "complex" and "sonnet" in model:
            model_score = 10  # Perfect match
        elif complexity == "medium":
            model_score = 8   # Either model is fine
        elif "sonnet" in model and complexity == "simple":
            model_score = 5   # Overkill but works
        elif "haiku" in model and complexity == "complex":
            model_score = 3   # Underpowered
        else:
            model_score = 5   # Unknown model, neutral score

        # Combine scores: reweight to incorporate model component
        # budget_score (60) + cache_score (10) = 70 points
        # Reweight to 90%, then add model_score (10)
        base_total = budget_score + cache_score - retry_penalty
        final_score = base_total * 0.9 + model_score

        return max(0.0, min(100.0, final_score))

    except ValueError:
        # Re-raise ValueError for missing estimated cost
        raise
    except Exception as e:
        logger.error(f"Error calculating cost efficiency score: {e}")
        return 0.0


def calculate_performance_score(workflow: dict) -> float:
    """
    Calculate performance score (0-100).

    Evaluates based on:
    - Duration compared to similar workflows
    - Bottleneck detection (phases taking >30% of time)
    - Idle time penalties
    - Absolute duration fallback if no similar workflows

    Args:
        workflow: Workflow data containing duration and phase metrics

    Returns:
        Performance score between 0.0 and 100.0
    """
    try:
        duration = workflow.get("duration_seconds", 0) or 0
        if duration <= 0:
            return 0.0

        # Use baseline of 180s (3 minutes) as reasonable workflow time
        baseline_duration = 180.0

        # Check if we have similar workflow data for comparison
        similar_avg_duration = workflow.get("similar_avg_duration")
        if similar_avg_duration and similar_avg_duration > 0:
            baseline_duration = similar_avg_duration

        # Calculate base score from duration comparison
        ratio = duration / baseline_duration
        if ratio <= 0.5:
            # Much faster than average
            base_score = 95.0
        elif ratio <= 0.75:
            # Faster than average
            base_score = 85.0 + (0.75 - ratio) * 40.0
        elif ratio <= 1.0:
            # Around average
            base_score = 70.0 + (1.0 - ratio) * 60.0
        elif ratio <= 1.5:
            # Slower than average
            base_score = 50.0 + (1.5 - ratio) * 40.0
        elif ratio <= 2.0:
            # Much slower
            base_score = 30.0 + (2.0 - ratio) * 40.0
        else:
            # Very slow
            base_score = max(10.0, 30.0 - (ratio - 2.0) * 10.0)

        # Bottleneck detection penalty
        phase_durations = workflow.get("phase_durations", {})
        if phase_durations and duration > 0:
            for phase, phase_duration in phase_durations.items():
                if phase_duration and phase_duration > duration * 0.3:
                    # Phase takes more than 30% of total time - bottleneck
                    base_score -= 10
                    logger.info(f"Bottleneck detected in phase '{phase}': {phase_duration}s ({phase_duration/duration*100:.1f}%)")
                    break  # Only penalize once

        # Idle time penalty (if available)
        idle_time = workflow.get("idle_time_seconds", 0) or 0
        if idle_time > 0 and duration > 0:
            idle_ratio = idle_time / duration
            if idle_ratio > 0.2:  # More than 20% idle time
                penalty = min(15.0, idle_ratio * 30.0)
                base_score -= penalty

        return max(0.0, min(100.0, base_score))

    except Exception as e:
        logger.error(f"Error calculating performance score: {e}")
        return 0.0


def calculate_quality_score(workflow: dict) -> float:
    """
    Calculate quality score (0-100).

    Evaluates based on:
    - Error rate (0 errors = 90-100 score)
    - Retry count penalty (-5 per retry)
    - Error category weighting (syntax_error=-10, timeout=-8, api_quota=-5)
    - PR/CI success bonus

    Args:
        workflow: Workflow data containing error and quality metrics

    Returns:
        Quality score between 0.0 and 100.0
    """
    try:
        error_count = workflow.get("error_count", 0) or 0
        retry_count = workflow.get("retry_count", 0) or 0

        # Start with high base score for perfect execution
        if error_count == 0 and retry_count == 0:
            base_score = 95.0
        elif error_count == 0:
            # No errors but had retries
            base_score = 90.0 - (retry_count * 5)
        else:
            # Has errors - start lower
            base_score = max(40.0, 80.0 - (error_count * 10))

        # Retry penalty
        retry_penalty = retry_count * 5
        base_score -= retry_penalty

        # Error category weighting (if error details available)
        error_types = workflow.get("error_types", [])
        if error_types:
            error_severity_map = {
                "syntax_error": -10,
                "type_error": -10,
                "timeout": -8,
                "rate_limit": -8,
                "api_quota": -5,
                "network": -5,
                "validation": -7,
            }

            for error_type in error_types:
                error_type_lower = error_type.lower() if isinstance(error_type, str) else ""
                for error_key, penalty in error_severity_map.items():
                    if error_key in error_type_lower:
                        base_score += penalty  # penalty is negative
                        break

        # PR/CI success bonus
        pr_success = workflow.get("pr_merged", False)
        ci_success = workflow.get("ci_passed", False)

        if pr_success:
            base_score += 5
        if ci_success:
            base_score += 5

        return max(0.0, min(100.0, base_score))

    except Exception as e:
        logger.error(f"Error calculating quality score: {e}")
        return 0.0


# ============================================================================
# Advanced Analytics Functions
# ============================================================================

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


def detect_complexity(workflow: dict) -> str:
    """
    Detect workflow complexity level based on multiple factors.

    Complexity is determined by analyzing:
    - Natural language input length (word count)
    - Execution duration
    - Error count

    Args:
        workflow: Workflow dictionary with metrics

    Returns:
        "simple", "medium", or "complex"

    Complexity thresholds:
        Simple: <50 words AND <300s duration AND <3 errors
        Complex: >200 words OR >1800s duration OR >5 errors
        Medium: Everything else
    """
    try:
        # Support both old and new field names for backward compatibility
        word_count = workflow.get('nl_input_word_count', 0) or 0
        if word_count == 0 and 'nl_input' in workflow:
            # Old format: count words from nl_input text
            nl_input = workflow.get('nl_input', '')
            word_count = len(nl_input.split()) if nl_input else 0

        # Support both old (duration_seconds) and new (total_duration_seconds) field names
        duration = workflow.get('total_duration_seconds', 0) or 0
        if duration == 0:
            duration = workflow.get('duration_seconds', 0) or 0

        # Support both old (error_count) and new (errors list) field names
        if 'errors' in workflow:
            errors = workflow.get('errors', [])
            error_count = len(errors) if isinstance(errors, list) else 0
        else:
            error_count = workflow.get('error_count', 0) or 0

        # Simple: All metrics are low
        if word_count < 50 and duration < 300 and error_count < 3:
            return "simple"

        # Complex: Any metric is very high
        elif word_count > 200 or duration > 1800 or error_count > 5:
            return "complex"

        # Medium: Everything else
        else:
            return "medium"

    except Exception as e:
        logger.error(f"Error detecting complexity: {e}")
        return "medium"  # Default to medium on error


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


def detect_anomalies(workflow: dict, historical_data: list[dict]) -> list[dict]:
    """
    Detect anomalies in workflow execution.

    Detects:
    - Cost anomaly: actual_cost > 2x average
    - Duration anomaly: duration > 2x average
    - Retry anomaly: retry_count >= 3
    - Cache anomaly: cache_efficiency < 20%
    - Error category anomaly: unexpected error types

    Requires minimum 3 similar workflows for statistical comparison.
    Filters historical data by same classification_type and workflow_template.

    Args:
        workflow: Workflow to analyze
        historical_data: Historical workflows for comparison

    Returns:
        List of detected anomalies with type, severity, message, actual, expected, threshold
    """
    anomalies = []

    try:
        # Get current workflow metrics
        actual_cost = workflow.get("actual_cost_total", 0) or 0
        duration = workflow.get("duration_seconds", 0) or 0
        retry_count = workflow.get("retry_count", 0) or 0
        cache_read_tokens = workflow.get("cache_read_tokens", 0) or 0
        total_input_tokens = workflow.get("total_input_tokens", 0) or 0
        error_category = workflow.get("error_category", "")
        workflow_template = workflow.get("workflow_template", "")
        classification_type = workflow.get("classification_type", "")
        current_adw_id = workflow.get("adw_id", "")

        # Filter historical data to similar workflows (same template and classification, exclude self)
        similar_workflows = [
            wf for wf in historical_data
            if wf.get("workflow_template") == workflow_template
            and wf.get("classification_type") == classification_type
            and wf.get("adw_id") != current_adw_id
        ]

        # Require minimum 3 similar workflows for statistical validity
        if len(similar_workflows) >= 3:
            costs = [wf.get("actual_cost_total", 0) or 0 for wf in similar_workflows if wf.get("actual_cost_total")]
            durations = [wf.get("duration_seconds", 0) or 0 for wf in similar_workflows if wf.get("duration_seconds")]

            avg_cost = sum(costs) / len(costs) if costs else 0
            avg_duration = sum(durations) / len(durations) if durations else 0

            # Cost anomaly detection (>2x average)
            if avg_cost > 0 and actual_cost > avg_cost * 2.0:
                anomalies.append({
                    "type": "cost_anomaly",
                    "severity": "high" if actual_cost > avg_cost * 3.0 else "medium",
                    "message": f"Cost ${actual_cost:.4f} is {actual_cost/avg_cost:.1f}x higher than average ${avg_cost:.4f}",
                    "actual": actual_cost,
                    "expected": avg_cost,
                    "threshold": 2.0
                })

            # Duration anomaly detection (>2x average)
            if avg_duration > 0 and duration > avg_duration * 2.0:
                anomalies.append({
                    "type": "duration_anomaly",
                    "severity": "high" if duration > avg_duration * 3.0 else "medium",
                    "message": f"Duration {duration}s is {duration/avg_duration:.1f}x longer than average {avg_duration:.0f}s",
                    "actual": duration,
                    "expected": avg_duration,
                    "threshold": 2.0
                })

        # Retry anomaly detection (>=3 retries)
        if retry_count >= 3:
            anomalies.append({
                "type": "retry_anomaly",
                "severity": "high" if retry_count >= 5 else "medium",
                "message": f"Workflow required {retry_count} retries",
                "actual": retry_count,
                "threshold": 3
            })

        # Cache anomaly detection (<20% efficiency)
        if total_input_tokens > 0:
            cache_efficiency = cache_read_tokens / total_input_tokens
            if cache_efficiency < 0.2:
                anomalies.append({
                    "type": "cache_anomaly",
                    "severity": "low",
                    "message": f"Low cache efficiency: {cache_efficiency*100:.1f}%",
                    "actual": cache_efficiency,
                    "threshold": 0.2
                })

        # Error category anomaly detection (unexpected error types)
        # Common expected errors: timeout, rate_limit, validation
        # Unexpected errors: syntax_error, runtime_error, system_error
        if error_category and error_category in ["syntax_error", "runtime_error", "system_error", "fatal_error"]:
            anomalies.append({
                "type": "error_category_anomaly",
                "severity": "high",
                "message": f"Unexpected error category: {error_category}",
                "actual": error_category,
                "threshold": "expected_categories"
            })

        return anomalies

    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        return []


def generate_optimization_recommendations(workflow: dict, anomalies: list[dict]) -> list[str]:  # noqa: C901
    """
    Generate actionable optimization recommendations with emoji prefixes.

    Recommendation categories:
    - 💡 Model selection (Haiku for simple, Sonnet for complex)
    - 📦 Cache optimization (improve cache hit rate)
    - 📝 Input quality (add details, structure, acceptance criteria)
    - ⏱️ Workflow restructuring (break down bottleneck phases)
    - 💰 Cost reduction (reduce retries, improve error handling)
    - 🐛 Error prevention (validation steps, better error handling)
    - 🚀 Performance optimization (remove unnecessary steps)

    Returns max 5 recommendations prioritized by impact.

    Args:
        workflow: Workflow data
        anomalies: List of detected anomalies

    Returns:
        List of recommendation strings with emoji prefixes
    """
    recommendations = []

    try:
        if not anomalies:
            return ["✅ Workflow performing well - no anomalies detected"]

        # Get workflow details
        model = workflow.get("model_used", "")
        phase_durations = workflow.get("phase_durations", {})
        error_count = workflow.get("error_count", 0)
        nl_input = workflow.get("nl_input", "")

        # Detect workflow complexity for model recommendations
        complexity = detect_complexity(workflow)

        for anomaly in anomalies:
            anomaly_type = anomaly.get("type", "")

            if anomaly_type == "cost_anomaly":
                # Model selection recommendations
                if "sonnet" in model.lower() and complexity == "simple":
                    recommendations.append(
                        "💡 Consider using Haiku model for this simple task to reduce costs by ~80%"
                    )
                elif "opus" in model.lower():
                    recommendations.append(
                        "💡 Consider using Sonnet instead of Opus to reduce costs by ~50%"
                    )

                # Cost reduction recommendations
                recommendations.append(
                    f"💰 Cost is {anomaly.get('actual', 0) / anomaly.get('expected', 1):.1f}x higher than expected - "
                    "review prompt complexity and reduce unnecessary context"
                )

            elif anomaly_type == "duration_anomaly":
                # Bottleneck analysis
                if phase_durations:
                    total_duration = sum(phase_durations.values())
                    slowest_phase = max(phase_durations.items(), key=lambda x: x[1])
                    phase_name, phase_time = slowest_phase

                    if phase_time > total_duration * 0.3:  # >30% of total time
                        recommendations.append(
                            f"⏱️ Bottleneck in '{phase_name}' phase (takes {phase_time}s, {phase_time/total_duration*100:.0f}% of total) - "
                            "consider breaking down into smaller tasks"
                        )
                else:
                    recommendations.append(
                        "🚀 Duration is significantly longer than average - "
                        "review workflow steps and remove unnecessary operations"
                    )

            elif anomaly_type == "retry_anomaly":
                # Error handling and cost reduction
                if error_count > 0:
                    recommendations.append(
                        f"🐛 Workflow required {anomaly.get('actual', 0)} retries with {error_count} errors - "
                        "add input validation and improve error handling to reduce costs"
                    )
                else:
                    recommendations.append(
                        f"💰 Workflow required {anomaly.get('actual', 0)} retries - "
                        "review workflow stability and external dependencies to reduce retry costs"
                    )

            elif anomaly_type == "cache_anomaly":
                # Cache optimization
                cache_efficiency = anomaly.get("actual", 0)
                recommendations.append(
                    f"📦 Low cache efficiency ({cache_efficiency*100:.1f}%) - "
                    "use more consistent prompts and system messages to improve caching and reduce costs"
                )

            elif anomaly_type == "error_category_anomaly":
                # Error prevention
                error_category = anomaly.get("actual", "")
                recommendations.append(
                    f"🐛 Unexpected error category '{error_category}' - "
                    "add validation steps and improve error handling to prevent runtime errors"
                )

        # Add input quality recommendation if input is too brief or unclear
        if nl_input and len(nl_input.split()) < 20:
            recommendations.append(
                "📝 Natural language input is very brief (<20 words) - "
                "add more details, specific requirements, and acceptance criteria for better results"
            )

        # Model upgrade recommendation for complex workflows using Haiku
        if "haiku" in model.lower() and complexity == "complex" and error_count > 2:
            recommendations.append(
                "💡 Complex workflow with multiple errors - "
                "consider upgrading to Sonnet model for better reasoning and fewer retries"
            )

        # Deduplicate and limit to top 5 recommendations by priority
        unique_recommendations = list(dict.fromkeys(recommendations))

        # Prioritize by emoji (cost/model first, then errors, then performance)
        priority_order = ["💡", "💰", "🐛", "📦", "📝", "⏱️", "🚀"]
        def get_priority(rec: str) -> int:
            for i, emoji in enumerate(priority_order):
                if rec.startswith(emoji):
                    return i
            return len(priority_order)

        sorted_recommendations = sorted(unique_recommendations, key=get_priority)
        return sorted_recommendations[:5]  # Return max 5 recommendations

    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return ["⚠️ Unable to generate recommendations due to error"]
