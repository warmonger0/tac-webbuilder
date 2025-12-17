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


def run_workflow_dry_run(feature_id: int, feature_title: str) -> dict[str, Any]:
    """
    Run dry-run analysis for a feature.

    This is FAST (3-10 seconds) because it:
    - Uses existing PhaseAnalyzer (no LLM calls)
    - Uses heuristics for cost estimation
    - Can match patterns from previous workflows (future enhancement)

    Args:
        feature_id: Feature ID to analyze
        feature_title: Feature title for display

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

        # TODO: Check pattern cache first (Phase 2 - Pattern Matching)
        # pattern = check_pattern_cache(feature_title, feature_description)
        # if pattern:
        #     return adapt_cached_pattern(pattern, feature_id, feature_title)

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
