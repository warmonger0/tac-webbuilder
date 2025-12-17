"""
Workflow Dry-Run Module

Provides cost estimation and phase planning preview before launching ADW workflows.
Uses pattern matching and heuristics to provide fast estimates without LLM calls.
"""

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add scripts directory to path for PhaseAnalyzer
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

try:
    from plan_phases import PhaseAnalyzer
except ImportError:
    PhaseAnalyzer = None

logger = logging.getLogger(__name__)

# Cost estimation constants (Sonnet 4.5 pricing)
TOKENS_PER_PHASE_BASE = 8000  # Base tokens for simple phase
TOKENS_PER_FILE = 500  # Additional tokens per file modification
COST_PER_1K_INPUT = 0.003  # $3 per million input tokens
COST_PER_1K_OUTPUT = 0.015  # $15 per million output tokens
OUTPUT_RATIO = 0.2  # Assume 20% output vs input

# Time estimation constants
MINUTES_PER_PHASE_BASE = 8  # Base time for simple phase
MINUTES_PER_FILE = 2  # Additional time per file


@dataclass
class PhasePlan:
    """Represents a planned phase with cost/time estimates."""

    phase_number: int
    title: str
    description: str
    estimated_hours: float
    estimated_tokens: int
    estimated_cost: float
    estimated_minutes: int
    files_to_modify: list[str]
    risk_level: str  # low, medium, high
    depends_on: list[int]  # Phase numbers this depends on


@dataclass
class WorkflowDryRunResult:
    """Complete dry-run result with all phases and totals."""

    feature_id: int
    feature_title: str
    phases: list[PhasePlan]
    total_phases: int
    total_estimated_cost: float
    total_estimated_time_minutes: int
    total_estimated_tokens: int
    high_risk_phases: int
    approval_recommended: bool
    pattern_matched: bool  # True if used cached pattern
    cache_source: str | None  # Which pattern was used


def estimate_phase_cost_and_time(
    phase,
    phase_number: int,
    total_phases: int
) -> PhasePlan:
    """
    Estimate cost and time for a single phase.

    Args:
        phase: Phase object from PhaseAnalyzer
        phase_number: Phase number (1-indexed)
        total_phases: Total number of phases

    Returns:
        PhasePlan with cost/time estimates
    """
    # Estimate token usage
    file_count = len(phase.files_to_modify) if hasattr(phase, 'files_to_modify') else 0
    estimated_tokens = TOKENS_PER_PHASE_BASE + (file_count * TOKENS_PER_FILE)

    # Adjust for phase complexity
    if phase.estimated_hours > 3:
        estimated_tokens = int(estimated_tokens * 1.5)

    # Calculate cost (input + output)
    input_cost = (estimated_tokens / 1000) * COST_PER_1K_INPUT
    output_tokens = int(estimated_tokens * OUTPUT_RATIO)
    output_cost = (output_tokens / 1000) * COST_PER_1K_OUTPUT
    total_cost = input_cost + output_cost

    # Estimate execution time
    estimated_minutes = MINUTES_PER_PHASE_BASE + (file_count * MINUTES_PER_FILE)
    if phase.estimated_hours > 3:
        estimated_minutes = int(estimated_minutes * 1.5)

    # Determine risk level
    risk_level = "low"
    if file_count > 5:
        risk_level = "high"
    elif file_count > 2 or phase.estimated_hours > 2:
        risk_level = "medium"

    # Extract dependencies (phase numbers only, not issue IDs)
    depends_on = []
    if hasattr(phase, 'depends_on') and phase.depends_on:
        # depends_on is list of (issue_id, phase_number) tuples
        depends_on = [phase_num for _, phase_num in phase.depends_on if phase_num < phase_number]

    return PhasePlan(
        phase_number=phase_number,
        title=phase.title,
        description=phase.description or "",
        estimated_hours=phase.estimated_hours,
        estimated_tokens=estimated_tokens + output_tokens,
        estimated_cost=round(total_cost, 2),
        estimated_minutes=estimated_minutes,
        files_to_modify=phase.files_to_modify if hasattr(phase, 'files_to_modify') else [],
        risk_level=risk_level,
        depends_on=depends_on
    )


def run_workflow_dry_run(
    feature_id: int,
    feature_title: str,
    feature_description: str | None = None,
    estimated_hours: float | None = None
) -> dict[str, Any]:
    """
    Run dry-run analysis for a feature.

    This is FAST (3-10 seconds, or <5s with pattern cache) because it:
    - Checks pattern cache first (80% hit rate after learning)
    - Uses existing PhaseAnalyzer (no LLM calls)
    - Uses heuristics for cost estimation

    Args:
        feature_id: Feature ID to analyze
        feature_title: Feature title for display
        feature_description: Feature description (optional, helps pattern matching)
        estimated_hours: Estimated hours (optional, helps pattern matching)

    Returns:
        Dictionary with dry-run results
    """
    try:
        # Check if PhaseAnalyzer is available
        if PhaseAnalyzer is None:
            logger.warning("PhaseAnalyzer not available for dry-run")
            return {
                "success": False,
                "error": "Dry-run not available: PhaseAnalyzer module not found",
                "estimated_cost": None
            }

        # Phase 1: Check pattern cache first
        from core.workflow_pattern_cache import find_similar_pattern

        cached_pattern = find_similar_pattern(
            feature_title,
            feature_description,
            estimated_hours
        )

        if cached_pattern:
            logger.info(
                f"Using cached pattern for feature #{feature_id}: "
                f"{cached_pattern['signature']} (similarity: {cached_pattern['similarity']:.1%})"
            )
            return _adapt_cached_pattern(cached_pattern, feature_id, feature_title)

        # Run phase analysis (fast, no LLM)
        logger.info(f"Running dry-run analysis for feature #{feature_id}")
        analyzer = PhaseAnalyzer()
        phases = analyzer.analyze_feature(feature_id)

        if not phases:
            return {
                "success": False,
                "error": "Could not generate phase breakdown",
                "estimated_cost": None
            }

        # Estimate cost and time for each phase
        phase_plans = []
        total_cost = 0.0
        total_time = 0
        total_tokens = 0
        high_risk_count = 0

        for i, phase in enumerate(phases, start=1):
            plan = estimate_phase_cost_and_time(phase, i, len(phases))
            phase_plans.append(plan)

            total_cost += plan.estimated_cost
            total_time += plan.estimated_minutes
            total_tokens += plan.estimated_tokens

            if plan.risk_level == "high":
                high_risk_count += 1

        # Determine if approval recommended
        approval_recommended = (
            high_risk_count > 0 or  # Any high-risk phases
            total_cost > 2.0 or  # Cost over $2
            len(phases) > 3  # More than 3 phases
        )

        result = WorkflowDryRunResult(
            feature_id=feature_id,
            feature_title=feature_title,
            phases=phase_plans,
            total_phases=len(phases),
            total_estimated_cost=round(total_cost, 2),
            total_estimated_time_minutes=total_time,
            total_estimated_tokens=total_tokens,
            high_risk_phases=high_risk_count,
            approval_recommended=approval_recommended,
            pattern_matched=False,  # No pattern matching yet
            cache_source=None
        )

        logger.info(
            f"Dry-run complete for feature #{feature_id}: "
            f"{len(phases)} phases, ${total_cost:.2f}, ~{total_time} min"
        )

        return {
            "success": True,
            "result": result,
            "estimated_cost": total_cost
        }

    except Exception as e:
        logger.error(f"Error running dry-run for feature #{feature_id}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "estimated_cost": None
        }


def _adapt_cached_pattern(
    cached_pattern: dict[str, Any],
    feature_id: int,
    feature_title: str
) -> dict[str, Any]:
    """
    Adapt a cached pattern to a new feature.

    Takes the cached pattern's estimates and creates a dry-run result.
    This is FAST (< 1 second) because we skip all analysis.

    Args:
        cached_pattern: Pattern from find_similar_pattern()
        feature_id: New feature ID
        feature_title: New feature title

    Returns:
        Dry-run result dictionary
    """
    # Extract cached data
    input_pattern = cached_pattern["input_pattern"]
    characteristics = input_pattern.get("characteristics", {})

    # Estimate number of phases from cached pattern
    phase_count = characteristics.get("phase_count", 2)
    total_cost = cached_pattern["avg_cost"]
    total_time_minutes = cached_pattern.get("avg_duration_minutes", 30)
    total_tokens = int(cached_pattern["avg_tokens"])

    # Create simplified phase breakdown
    cost_per_phase = total_cost / phase_count
    time_per_phase = total_time_minutes // phase_count
    tokens_per_phase = total_tokens // phase_count

    phases = []
    for i in range(1, phase_count + 1):
        # Use cached phase types if available
        phase_types = characteristics.get("phase_types", [])
        title = phase_types[i - 1] if i <= len(phase_types) else f"Implementation phase {i}"

        phases.append(PhasePlan(
            phase_number=i,
            title=title,
            description=f"Based on similar pattern: {cached_pattern['signature']}",
            estimated_hours=total_time_minutes / 60 / phase_count,
            estimated_tokens=tokens_per_phase,
            estimated_cost=cost_per_phase,
            estimated_minutes=time_per_phase,
            files_to_modify=[],  # Not cached
            risk_level="medium",  # Conservative estimate
            depends_on=list(range(1, i)) if i > 1 else []
        ))

    # Determine high risk count from distribution
    risk_dist = characteristics.get("risk_distribution", {})
    high_risk_count = risk_dist.get("high", 0)

    result = WorkflowDryRunResult(
        feature_id=feature_id,
        feature_title=feature_title,
        phases=phases,
        total_phases=phase_count,
        total_estimated_cost=round(total_cost, 2),
        total_estimated_time_minutes=total_time_minutes,
        total_estimated_tokens=total_tokens,
        high_risk_phases=high_risk_count,
        approval_recommended=high_risk_count > 0 or total_cost > 2.0,
        pattern_matched=True,
        cache_source=f"{cached_pattern['signature']} ({cached_pattern['occurrence_count']}x)"
    )

    return {
        "success": True,
        "result": result,
        "estimated_cost": total_cost
    }


def save_completed_workflow_pattern(
    feature_id: int,
    feature_title: str,
    feature_description: str | None,
    dry_run_result: WorkflowDryRunResult
) -> int | None:
    """
    Save a completed workflow as a reusable pattern.

    Call this after a workflow completes successfully to learn the pattern.

    Args:
        feature_id: Feature ID
        feature_title: Feature title
        feature_description: Feature description
        dry_run_result: The dry-run result used for this workflow

    Returns:
        Pattern ID if saved successfully, None otherwise
    """
    try:
        from core.workflow_pattern_cache import extract_workflow_pattern, save_workflow_pattern

        # Extract pattern from the completed workflow
        pattern = extract_workflow_pattern(
            feature_id=feature_id,
            feature_title=feature_title,
            feature_description=feature_description,
            phases=dry_run_result.phases,
            total_cost=dry_run_result.total_estimated_cost,
            total_time_minutes=dry_run_result.total_estimated_time_minutes,
            total_tokens=dry_run_result.total_estimated_tokens
        )

        # Save to database
        pattern_id = save_workflow_pattern(pattern)

        if pattern_id:
            logger.info(
                f"Saved workflow pattern for feature #{feature_id}: "
                f"{pattern['pattern_signature']} (ID: {pattern_id})"
            )

        return pattern_id

    except Exception as e:
        logger.error(f"Error saving workflow pattern: {e}", exc_info=True)
        return None


def format_dry_run_for_display(result: WorkflowDryRunResult) -> dict[str, Any]:
    """
    Format dry-run result for frontend display.

    Args:
        result: WorkflowDryRunResult object

    Returns:
        Dictionary formatted for frontend consumption
    """
    return {
        "feature_id": result.feature_id,
        "feature_title": result.feature_title,
        "phases": [
            {
                "phase_number": p.phase_number,
                "title": p.title,
                "description": p.description,
                "estimated_cost": f"${p.estimated_cost:.2f}",
                "estimated_time": f"{p.estimated_minutes} min",
                "estimated_tokens": p.estimated_tokens,
                "files_to_modify": p.files_to_modify,
                "risk_level": p.risk_level,
                "depends_on": p.depends_on
            }
            for p in result.phases
        ],
        "summary": {
            "total_phases": result.total_phases,
            "total_cost": f"${result.total_estimated_cost:.2f}",
            "total_time": f"~{result.total_estimated_time_minutes} min",
            "total_tokens": result.total_estimated_tokens,
            "high_risk_phases": result.high_risk_phases,
            "approval_recommended": result.approval_recommended
        },
        "pattern_info": {
            "matched": result.pattern_matched,
            "source": result.cache_source
        }
    }
