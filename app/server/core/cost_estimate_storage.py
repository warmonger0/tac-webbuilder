"""
Cost Estimate Storage

Persists cost estimates by issue number so they can be retrieved
when workflows are synced from the agents directory.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

STORAGE_FILE = Path("app/db/cost_estimates_by_issue.json")


def save_cost_estimate(
    issue_number: int,
    estimated_cost_total: float,
    estimated_cost_breakdown: dict[str, float],
    level: str,
    confidence: float,
    reasoning: str,
    recommended_workflow: str
) -> None:
    """
    Save cost estimate for an issue number.

    Args:
        issue_number: GitHub issue number
        estimated_cost_total: Total estimated cost
        estimated_cost_breakdown: Per-phase cost breakdown
        level: Complexity level (lightweight/standard/complex)
        confidence: Confidence score (0.0 to 1.0)
        reasoning: Reasoning for the estimate
        recommended_workflow: Recommended workflow to use
    """
    # Load existing estimates
    estimates = _load_estimates()

    # Store estimate with timestamp
    estimates[str(issue_number)] = {
        "estimated_cost_total": estimated_cost_total,
        "estimated_cost_breakdown": estimated_cost_breakdown,
        "level": level,
        "confidence": confidence,
        "reasoning": reasoning,
        "recommended_workflow": recommended_workflow,
        "timestamp": datetime.now().isoformat()
    }

    # Save back to file
    _save_estimates(estimates)


def get_cost_estimate(issue_number: int) -> dict | None:
    """
    Retrieve cost estimate for an issue number.

    Returns:
        Dict with cost estimate data or None if not found
    """
    estimates = _load_estimates()
    return estimates.get(str(issue_number))


def cleanup_old_estimates(days: int = 7) -> int:
    """
    Remove estimates older than specified days.

    Args:
        days: Number of days to keep estimates

    Returns:
        Number of estimates removed
    """
    estimates = _load_estimates()
    cutoff = datetime.now() - timedelta(days=days)
    removed_count = 0

    for issue_num in list(estimates.keys()):
        estimate = estimates[issue_num]
        timestamp = datetime.fromisoformat(estimate.get("timestamp", "2000-01-01"))
        if timestamp < cutoff:
            del estimates[issue_num]
            removed_count += 1

    if removed_count > 0:
        _save_estimates(estimates)

    return removed_count


def _load_estimates() -> dict:
    """Load estimates from storage file."""
    if STORAGE_FILE.exists():
        try:
            with open(STORAGE_FILE) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_estimates(estimates: dict) -> None:
    """Save estimates to storage file."""
    STORAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STORAGE_FILE, 'w') as f:
        json.dump(estimates, f, indent=2)
