#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
WARNING: DEPRECATED - This is a partial workflow chain.
Please use adw_sdlc_complete_iso.py instead for the complete SDLC workflow.

ADW Plan Build Test Iso - Compositional workflow for isolated planning, building, and testing

Usage: uv run adw_plan_build_test_iso.py <issue-number> [adw-id] [--skip-e2e]

This script runs:
1. adw_plan_iso.py - Planning phase (isolated)
2. adw_build_iso.py - Implementation phase (isolated)
3. adw_test_iso.py - Testing phase (isolated)

The scripts are chained together via persistent state (adw_state.json).
"""

import subprocess
import sys
import os

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adw_modules.workflow_ops import ensure_adw_id


def main():
    """Main entry point."""
    # Print deprecation warning and auto-forward
    print("=" * 70)
    print("⚠️  DEPRECATED WORKFLOW - AUTO-FORWARDING")
    print("=" * 70)
    print("This workflow is incomplete (only Plan, Build, Test phases)")
    print("Auto-forwarding to: adw_sdlc_complete_iso.py")
    print("This ensures your work gets shipped with PR creation & merge")
    print("=" * 70)
    print()

    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: uv run adw_plan_build_test_iso.py <issue-number> [adw-id] [--skip-e2e]")
        print("\nThis workflow is DEPRECATED. Use adw_sdlc_complete_iso.py instead.")
        sys.exit(1)

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Forward all arguments to the complete workflow
    forward_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_sdlc_complete_iso.py"),
    ] + sys.argv[1:]  # Pass all arguments

    print(f"Executing: {' '.join(forward_cmd)}\n")
    result = subprocess.run(forward_cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()