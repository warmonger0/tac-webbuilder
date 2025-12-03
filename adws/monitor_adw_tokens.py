#!/usr/bin/env python3
"""Monitor token usage for ADW workflows without adding to context overhead.

This script runs OUTSIDE of Claude Code and monitors token usage by reading
the raw_output.jsonl files that agents create. It does not interfere with
the workflow execution or add to context.

Usage:
    # Monitor specific ADW
    uv run adws/monitor_adw_tokens.py <adw_id>

    # Auto-monitor latest ADW
    uv run adws/monitor_adw_tokens.py --latest

    # Continuous monitoring
    uv run adws/monitor_adw_tokens.py <adw_id> --watch

    # Detailed view
    uv run adws/monitor_adw_tokens.py <adw_id> --detail
"""

import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Get project root dynamically
PROJECT_ROOT = Path(__file__).parent.parent
AGENTS_DIR = PROJECT_ROOT / "agents"


def get_latest_adw_id() -> Optional[str]:
    """Get the most recently created ADW ID."""
    if not AGENTS_DIR.exists():
        return None

    adw_dirs = [d for d in AGENTS_DIR.iterdir() if d.is_dir()]
    if not adw_dirs:
        return None

    # Sort by modification time, most recent first
    latest = max(adw_dirs, key=lambda d: d.stat().st_mtime)
    return latest.name


def parse_token_usage(jsonl_file: Path) -> Dict[str, Any]:
    """Parse token usage from a raw_output.jsonl file."""
    if not jsonl_file.exists():
        return {
            'messages': 0,
            'input': 0,
            'cache_create': 0,
            'cache_read': 0,
            'output': 0,
        }

    usage_data = []
    with open(jsonl_file) as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get('type') == 'assistant' and 'usage' in data.get('message', {}):
                    usage_data.append(data['message']['usage'])
            except json.JSONDecodeError:
                continue

    if not usage_data:
        return {
            'messages': 0,
            'input': 0,
            'cache_create': 0,
            'cache_read': 0,
            'output': 0,
        }

    return {
        'messages': len(usage_data),
        'input': sum(u.get('input_tokens', 0) for u in usage_data),
        'cache_create': sum(u.get('cache_creation_input_tokens', 0) for u in usage_data),
        'cache_read': sum(u.get('cache_read_input_tokens', 0) for u in usage_data),
        'output': sum(u.get('output_tokens', 0) for u in usage_data),
    }


def get_adw_phases(adw_id: str) -> Dict[str, Dict[str, Any]]:
    """Get token usage for all phases of an ADW workflow."""
    agents_dir = AGENTS_DIR / adw_id

    if not agents_dir.exists():
        return {}

    phases = {}
    for jsonl_file in agents_dir.glob("*/raw_output.jsonl"):
        phase_name = jsonl_file.parent.name
        phases[phase_name] = parse_token_usage(jsonl_file)

    return phases


def format_number(n: int) -> str:
    """Format large numbers with commas."""
    return f"{n:,}"


def calculate_cache_efficiency(cache_create: int, cache_read: int) -> float:
    """Calculate cache hit ratio as percentage."""
    total = cache_create + cache_read
    if total == 0:
        return 0.0
    return (cache_read / total) * 100


def print_phase_summary(phase_name: str, stats: Dict[str, Any], detail: bool = False):
    """Print summary for a single phase."""
    if stats['messages'] == 0:
        return

    cache_eff = calculate_cache_efficiency(stats['cache_create'], stats['cache_read'])

    print(f"\n📦 {phase_name}")
    print(f"  Messages: {stats['messages']}")

    if detail:
        print(f"  Input: {format_number(stats['input'])}")
        print(f"  Cache Create: {format_number(stats['cache_create'])}")
        print(f"  Cache Read: {format_number(stats['cache_read'])}")
        print(f"  Output: {format_number(stats['output'])}")
        if cache_eff > 0:
            print(f"  Cache Efficiency: {cache_eff:.1f}%")
    else:
        total_input = stats['input'] + stats['cache_create'] + stats['cache_read']
        print(f"  Total In: {format_number(total_input)} | Out: {format_number(stats['output'])}")


def print_workflow_summary(adw_id: str, phases: Dict[str, Dict[str, Any]], detail: bool = False):
    """Print complete workflow token usage summary."""
    if not phases:
        print(f"❌ No data found for ADW {adw_id}")
        return

    # Calculate totals
    totals = {
        'messages': sum(p['messages'] for p in phases.values()),
        'input': sum(p['input'] for p in phases.values()),
        'cache_create': sum(p['cache_create'] for p in phases.values()),
        'cache_read': sum(p['cache_read'] for p in phases.values()),
        'output': sum(p['output'] for p in phases.values()),
    }

    print(f"\n{'='*60}")
    print(f"📊 ADW Token Usage Report: {adw_id}")
    print(f"{'='*60}")

    # Sort phases by typical workflow order (tac-webbuilder phases)
    phase_order = [
        'adw_plan_iso', 'adw_validate_iso', 'adw_build_iso',
        'adw_lint_iso', 'adw_test_iso', 'adw_review_iso',
        'adw_document_iso', 'adw_ship_iso', 'adw_cleanup_iso',
        'sdlc_planner', 'sdlc_implementor', 'test_runner',
        'e2e_test_runner', 'reviewer', 'documenter'
    ]
    sorted_phases = sorted(phases.items(),
                          key=lambda x: phase_order.index(x[0]) if x[0] in phase_order else 999)

    for phase_name, stats in sorted_phases:
        print_phase_summary(phase_name, stats, detail)

    # Print totals
    cache_eff = calculate_cache_efficiency(totals['cache_create'], totals['cache_read'])

    print(f"\n{'─'*60}")
    print(f"📈 TOTALS")
    print(f"  Total Messages: {totals['messages']}")
    print(f"  Total Input: {format_number(totals['input'])}")
    print(f"  Total Cache Create: {format_number(totals['cache_create'])}")
    print(f"  Total Cache Read: {format_number(totals['cache_read'])}")
    print(f"  Total Output: {format_number(totals['output'])}")
    print(f"  Cache Efficiency: {cache_eff:.1f}%")

    # Cost estimate (Claude Sonnet 4.5 pricing as of Jan 2025)
    cost_input = totals['input'] * 3 / 1_000_000
    cost_cache_create = totals['cache_create'] * 3.75 / 1_000_000
    cost_cache_read = totals['cache_read'] * 0.30 / 1_000_000
    cost_output = totals['output'] * 15 / 1_000_000
    total_cost = cost_input + cost_cache_create + cost_cache_read + cost_output

    # Cache savings calculation
    cache_savings = 0.0
    if totals['cache_read'] > 0:
        # Savings = what we would have paid if cache_read was regular input
        cache_savings = (totals['cache_read'] * 3 / 1_000_000) - cost_cache_read

    print(f"\n💰 Estimated Cost (Sonnet 4.5)")
    print(f"  Input: ${cost_input:.2f}")
    print(f"  Cache Create: ${cost_cache_create:.2f}")
    print(f"  Cache Read: ${cost_cache_read:.2f}")
    print(f"  Output: ${cost_output:.2f}")
    print(f"  TOTAL: ${total_cost:.2f}")
    if cache_savings > 0:
        print(f"  💾 Cache Savings: ${cache_savings:.2f}")
    print(f"{'='*60}\n")


def monitor_workflow(adw_id: str, watch: bool = False, detail: bool = False):
    """Monitor workflow token usage, optionally in watch mode."""
    if watch:
        print(f"👀 Watching ADW {adw_id} (Ctrl+C to stop)...")
        try:
            while True:
                phases = get_adw_phases(adw_id)
                print("\033[2J\033[H")  # Clear screen
                print(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
                print_workflow_summary(adw_id, phases, detail)
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped")
    else:
        phases = get_adw_phases(adw_id)
        print_workflow_summary(adw_id, phases, detail)


def main():
    parser = argparse.ArgumentParser(
        description="Monitor ADW workflow token usage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor specific workflow
  uv run adws/monitor_adw_tokens.py 5afcc315

  # Monitor latest workflow
  uv run adws/monitor_adw_tokens.py --latest

  # Continuous monitoring
  uv run adws/monitor_adw_tokens.py 5afcc315 --watch

  # Detailed view
  uv run adws/monitor_adw_tokens.py 5afcc315 --detail

  # Watch mode with detail
  uv run adws/monitor_adw_tokens.py --latest --watch --detail
        """
    )
    parser.add_argument('adw_id', nargs='?', help='ADW ID to monitor')
    parser.add_argument('--latest', action='store_true', help='Monitor latest ADW')
    parser.add_argument('--watch', '-w', action='store_true', help='Continuous monitoring mode')
    parser.add_argument('--detail', '-d', action='store_true', help='Show detailed stats')

    args = parser.parse_args()

    if args.latest:
        adw_id = get_latest_adw_id()
        if not adw_id:
            print("❌ No ADW workflows found")
            print(f"   (Looking in: {AGENTS_DIR})")
            sys.exit(1)
        print(f"📍 Monitoring latest ADW: {adw_id}\n")
    elif args.adw_id:
        adw_id = args.adw_id
    else:
        parser.print_help()
        sys.exit(1)

    monitor_workflow(adw_id, args.watch, args.detail)


if __name__ == "__main__":
    main()
