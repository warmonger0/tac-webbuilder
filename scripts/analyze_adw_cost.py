#!/usr/bin/env python3
"""
Analyze ADW workflow costs by parsing JSONL output files.

Usage: python3 scripts/analyze_adw_cost.py <adw_id>

This script:
1. Finds all JSONL files for the given ADW ID
2. Parses token usage from each API call
3. Calculates total costs based on Claude pricing
4. Shows caching efficiency
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class APICallStats:
    """Statistics for a single API call."""
    agent_name: str
    slash_command: str
    model: str
    input_tokens: int
    cache_creation_tokens: int
    cache_read_tokens: int
    output_tokens: int

    @property
    def total_input_tokens(self) -> int:
        return self.input_tokens + self.cache_creation_tokens + self.cache_read_tokens

    def calculate_cost(self) -> float:
        """Calculate cost for this API call based on Claude pricing."""
        # Claude Sonnet 4.5 pricing (as of 2025)
        # Input: $3 per 1M tokens
        # Cache writes: $3.75 per 1M tokens
        # Cache reads: $0.30 per 1M tokens
        # Output: $15 per 1M tokens

        # Opus pricing
        # Input: $15 per 1M tokens
        # Cache writes: $18.75 per 1M tokens
        # Cache reads: $1.50 per 1M tokens
        # Output: $75 per 1M tokens

        if "opus" in self.model.lower():
            input_cost = (self.input_tokens / 1_000_000) * 15
            cache_write_cost = (self.cache_creation_tokens / 1_000_000) * 18.75
            cache_read_cost = (self.cache_read_tokens / 1_000_000) * 1.50
            output_cost = (self.output_tokens / 1_000_000) * 75
        else:  # sonnet
            input_cost = (self.input_tokens / 1_000_000) * 3
            cache_write_cost = (self.cache_creation_tokens / 1_000_000) * 3.75
            cache_read_cost = (self.cache_read_tokens / 1_000_000) * 0.30
            output_cost = (self.output_tokens / 1_000_000) * 15

        return input_cost + cache_write_cost + cache_read_cost + output_cost


def parse_jsonl_file(file_path: Path) -> Tuple[str, APICallStats]:
    """Parse a JSONL file and extract API call statistics."""
    try:
        with open(file_path, 'r') as f:
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
            return None, None

        # Extract usage statistics
        usage = result_msg.get("usage", {})

        # Determine agent name and slash command from file path
        # Path format: agents/<adw_id>/<agent_name>/raw_output.jsonl
        parts = file_path.parts
        agent_name = parts[-2] if len(parts) >= 2 else "unknown"

        # Try to find slash command from prompts file
        prompts_dir = file_path.parent / "prompts"
        slash_command = "unknown"
        if prompts_dir.exists():
            prompt_files = list(prompts_dir.glob("*.txt"))
            if prompt_files:
                slash_command = f"/{prompt_files[0].stem}"

        # Get model from result message
        model = result_msg.get("model", "unknown")

        stats = APICallStats(
            agent_name=agent_name,
            slash_command=slash_command,
            model=model,
            input_tokens=usage.get("input_tokens", 0),
            cache_creation_tokens=usage.get("cache_creation_input_tokens", 0),
            cache_read_tokens=usage.get("cache_read_input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
        )

        return agent_name, stats

    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return None, None


def analyze_adw_cost(adw_id: str) -> None:
    """Analyze costs for an ADW workflow."""
    # Find the agents directory
    project_root = Path(__file__).parent.parent
    agents_dir = project_root / "agents" / adw_id

    if not agents_dir.exists():
        print(f"Error: No agents directory found for ADW ID: {adw_id}")
        print(f"Expected path: {agents_dir}")
        sys.exit(1)

    # Find all JSONL files
    jsonl_files = list(agents_dir.glob("*/raw_output.jsonl"))

    if not jsonl_files:
        print(f"Error: No JSONL output files found for ADW ID: {adw_id}")
        sys.exit(1)

    print(f"\n{'='*80}")
    print(f"ADW Cost Analysis: {adw_id}")
    print(f"{'='*80}\n")

    # Parse all files
    all_stats: List[APICallStats] = []
    for jsonl_file in sorted(jsonl_files):
        agent_name, stats = parse_jsonl_file(jsonl_file)
        if stats:
            all_stats.append(stats)

    if not all_stats:
        print("Error: Could not parse any API call statistics")
        sys.exit(1)

    # Display individual call details
    print(f"{'Agent':<20} {'Command':<20} {'Model':<10} {'Input':<10} {'Cache W':<10} {'Cache R':<10} {'Output':<10} {'Cost':<10}")
    print(f"{'-'*120}")

    total_cost = 0.0
    total_input = 0
    total_cache_write = 0
    total_cache_read = 0
    total_output = 0

    for stats in all_stats:
        cost = stats.calculate_cost()
        total_cost += cost
        total_input += stats.input_tokens
        total_cache_write += stats.cache_creation_tokens
        total_cache_read += stats.cache_read_tokens
        total_output += stats.output_tokens

        print(f"{stats.agent_name:<20} {stats.slash_command:<20} {stats.model:<10} "
              f"{stats.input_tokens:<10,} {stats.cache_creation_tokens:<10,} "
              f"{stats.cache_read_tokens:<10,} {stats.output_tokens:<10,} ${cost:>8.4f}")

    # Summary
    print(f"{'-'*120}")
    print(f"{'TOTAL':<20} {'':<20} {'':<10} "
          f"{total_input:<10,} {total_cache_write:<10,} "
          f"{total_cache_read:<10,} {total_output:<10,} ${total_cost:>8.4f}")

    # Calculate caching efficiency
    total_input_all = total_input + total_cache_write + total_cache_read
    if total_cache_read > 0:
        cache_percentage = (total_cache_read / total_input_all) * 100

        # Calculate savings from caching
        # If those cached tokens were regular input tokens:
        # Sonnet: $3/1M vs $0.30/1M = 90% savings
        # Opus: $15/1M vs $1.50/1M = 90% savings
        cost_without_cache = total_cost + (total_cache_read / 1_000_000) * (3 - 0.30)  # Assuming mostly sonnet
        savings = cost_without_cache - total_cost
        savings_percentage = (savings / cost_without_cache) * 100 if cost_without_cache > 0 else 0

        print(f"\n{'='*80}")
        print(f"Caching Efficiency:")
        print(f"  - Cached tokens: {total_cache_read:,} ({cache_percentage:.1f}% of input)")
        print(f"  - Estimated savings: ${savings:.4f} ({savings_percentage:.1f}%)")
        print(f"  - Cost without caching: ${cost_without_cache:.4f}")

    print(f"\n{'='*80}")
    print(f"Total API Calls: {len(all_stats)}")
    print(f"Total Cost: ${total_cost:.4f}")
    print(f"{'='*80}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/analyze_adw_cost.py <adw_id>")
        print("\nExample: python3 scripts/analyze_adw_cost.py abc12345")
        sys.exit(1)

    adw_id = sys.argv[1]
    analyze_adw_cost(adw_id)


if __name__ == "__main__":
    main()
