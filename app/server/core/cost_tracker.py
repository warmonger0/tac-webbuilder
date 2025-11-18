"""
Cost tracking utility for ADW workflows.

This module reads cost data from raw_output.jsonl files in the agents directory
and calculates cost metrics including total cost, cache efficiency, and per-phase breakdowns.
"""

import json
import logging
from collections import defaultdict
from pathlib import Path

from core.data_models import (
    CostData,
    PhaseCost,
    TokenBreakdown,
)

logger = logging.getLogger(__name__)


def calculate_api_call_cost(
    model: str,
    input_tokens: int,
    cache_creation_tokens: int,
    cache_read_tokens: int,
    output_tokens: int,
) -> float:
    """
    Calculate cost for a single API call based on Claude pricing.

    Pricing as of 2025:
    - Sonnet 4.5: Input $3/1M, Cache Write $3.75/1M, Cache Read $0.30/1M, Output $15/1M
    - Opus: Input $15/1M, Cache Write $18.75/1M, Cache Read $1.50/1M, Output $75/1M
    """
    if "opus" in model.lower():
        input_cost = (input_tokens / 1_000_000) * 15
        cache_write_cost = (cache_creation_tokens / 1_000_000) * 18.75
        cache_read_cost = (cache_read_tokens / 1_000_000) * 1.50
        output_cost = (output_tokens / 1_000_000) * 75
    else:  # Default to Sonnet pricing
        input_cost = (input_tokens / 1_000_000) * 3
        cache_write_cost = (cache_creation_tokens / 1_000_000) * 3.75
        cache_read_cost = (cache_read_tokens / 1_000_000) * 0.30
        output_cost = (output_tokens / 1_000_000) * 15

    return input_cost + cache_write_cost + cache_read_cost + output_cost


def parse_jsonl_file(file_path: Path) -> dict | None:
    """
    Parse a raw_output.jsonl file and extract API call statistics.

    Returns a dict with model, input_tokens, cache_creation_tokens,
    cache_read_tokens, output_tokens, or None if parsing fails.
    """
    try:
        with open(file_path) as f:
            lines = f.readlines()

        # Find the result message (last message with type="result")
        result_msg = None
        for line in reversed(lines):
            try:
                data = json.loads(line.strip())
                if data.get("type") == "result":
                    result_msg = data
                    break
            except json.JSONDecodeError:
                continue

        if not result_msg:
            logger.debug(f"No result message found in {file_path}")
            return None

        # Extract usage statistics
        usage = result_msg.get("usage", {})
        model = result_msg.get("model", "unknown")

        return {
            "model": model,
            "input_tokens": usage.get("input_tokens", 0),
            "cache_creation_tokens": usage.get("cache_creation_input_tokens", 0),
            "cache_read_tokens": usage.get("cache_read_input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
        }

    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
        return None


def infer_phase_from_path(file_path: Path) -> str:
    """
    Infer the workflow phase from the agent directory name.

    Common patterns:
    - agents/{adw_id}/sdlc_planner -> plan
    - agents/{adw_id}/builder -> build
    - agents/{adw_id}/test -> test
    - agents/{adw_id}/reviewer -> review
    - agents/{adw_id}/documenter -> document
    - agents/{adw_id}/shipper -> ship
    """
    parts = file_path.parts
    if len(parts) < 2:
        return "unknown"

    agent_name = parts[-2].lower()

    # Map agent names to phases
    phase_mapping = {
        "planner": "plan",
        "sdlc_planner": "plan",
        "builder": "build",
        "test": "test",
        "tester": "test",
        "reviewer": "review",
        "review": "review",
        "documenter": "document",
        "documentation": "document",
        "shipper": "ship",
        "ship": "ship",
    }

    for key, phase in phase_mapping.items():
        if key in agent_name:
            return phase

    return agent_name  # Return agent name as fallback


def read_cost_history(adw_id: str) -> CostData:
    """
    Read cost history for a specific ADW workflow.

    Locates all raw_output.jsonl files in agents/{adw_id}/*/ and aggregates
    cost data by phase.

    Raises:
        FileNotFoundError: If no agents directory exists for the given adw_id
        ValueError: If no valid cost data could be parsed
    """
    # Locate the agents directory
    project_root = Path(__file__).parent.parent.parent.parent
    agents_dir = project_root / "agents" / adw_id

    if not agents_dir.exists():
        raise FileNotFoundError(f"No agents directory found for ADW ID: {adw_id}")

    # Find all raw_output.jsonl files
    jsonl_files = list(agents_dir.glob("*/raw_output.jsonl"))

    if not jsonl_files:
        raise ValueError(f"No raw_output.jsonl files found for ADW ID: {adw_id}")

    # Aggregate costs by phase
    phase_data: dict[str, dict] = defaultdict(lambda: {
        "input_tokens": 0,
        "cache_creation_tokens": 0,
        "cache_read_tokens": 0,
        "output_tokens": 0,
        "cost": 0.0,
        "model": "unknown",
    })

    total_cost = 0.0
    total_input = 0
    total_cache_write = 0
    total_cache_read = 0
    total_output = 0

    for jsonl_file in sorted(jsonl_files):
        stats = parse_jsonl_file(jsonl_file)
        if not stats:
            continue

        # Infer phase from directory name
        phase = infer_phase_from_path(jsonl_file)

        # Calculate cost for this API call
        cost = calculate_api_call_cost(
            stats["model"],
            stats["input_tokens"],
            stats["cache_creation_tokens"],
            stats["cache_read_tokens"],
            stats["output_tokens"],
        )

        # Aggregate by phase
        phase_data[phase]["input_tokens"] += stats["input_tokens"]
        phase_data[phase]["cache_creation_tokens"] += stats["cache_creation_tokens"]
        phase_data[phase]["cache_read_tokens"] += stats["cache_read_tokens"]
        phase_data[phase]["output_tokens"] += stats["output_tokens"]
        phase_data[phase]["cost"] += cost
        phase_data[phase]["model"] = stats["model"]  # Use last model seen

        # Update totals
        total_cost += cost
        total_input += stats["input_tokens"]
        total_cache_write += stats["cache_creation_tokens"]
        total_cache_read += stats["cache_read_tokens"]
        total_output += stats["output_tokens"]

    if not phase_data:
        raise ValueError(f"Could not parse any valid cost data for ADW ID: {adw_id}")

    # Calculate cache efficiency
    total_tokens = total_input + total_cache_write + total_cache_read + total_output
    cache_efficiency_percent = (
        (total_cache_read / (total_input + total_cache_write + total_cache_read)) * 100
        if (total_input + total_cache_write + total_cache_read) > 0
        else 0.0
    )

    # Calculate cache savings
    # If cache read tokens were charged as regular input tokens, how much more would it cost?
    # Assuming Sonnet pricing: $3/1M for input vs $0.30/1M for cache reads
    cache_savings_amount = (total_cache_read / 1_000_000) * (3 - 0.30)

    # Build phase costs list
    phases: list[PhaseCost] = []
    for phase_name, data in sorted(phase_data.items()):
        phases.append(
            PhaseCost(
                phase=phase_name,
                cost=data["cost"],
                tokens=TokenBreakdown(
                    input_tokens=data["input_tokens"],
                    cache_creation_tokens=data["cache_creation_tokens"],
                    cache_read_tokens=data["cache_read_tokens"],
                    output_tokens=data["output_tokens"],
                ),
                timestamp=None,  # Could extract from file metadata if needed
            )
        )

    return CostData(
        adw_id=adw_id,
        phases=phases,
        total_cost=total_cost,
        cache_efficiency_percent=cache_efficiency_percent,
        cache_savings_amount=cache_savings_amount,
        total_tokens=total_tokens,
    )
