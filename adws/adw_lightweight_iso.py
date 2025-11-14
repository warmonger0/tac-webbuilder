#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Lightweight Iso - Optimized workflow for simple, low-complexity changes

Usage: uv run adw_lightweight_iso.py <issue-number> [adw-id]

This workflow is optimized for simple changes like:
- UI-only modifications (styling, layout, text changes)
- Documentation updates
- Simple bug fixes
- Single-file changes

Workflow (Simplified):
1. Fetch issue & classify
2. Analyze complexity (verify lightweight is appropriate)
3. Create worktree
4. Plan implementation (minimal)
5. Implement changes
6. Quick validation (no extensive testing)
7. Commit & create PR
8. Ship (auto-merge if passing)

Target Cost: $0.20 - $0.50 (vs $3-5 for full SDLC)
"""

import subprocess
import sys
import os
import logging

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adw_modules.workflow_ops import ensure_adw_id
from adw_modules.github import make_issue_comment


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: uv run adw_lightweight_iso.py <issue-number> [adw-id]")
        print("\n⚡ Lightweight Workflow: Optimized for simple changes")
        print("\nThis runs a streamlined workflow:")
        print("  1. Plan (minimal)")
        print("  2. Implement (focused)")
        print("  3. Quick validation")
        print("  4. Ship (auto-merge)")
        print("\n💰 Target Cost: $0.20 - $0.50")
        print("\nBest for:")
        print("  - UI-only changes")
        print("  - Documentation updates")
        print("  - Simple bug fixes")
        print("  - Single-file modifications")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure ADW ID exists with initialized state
    adw_id = ensure_adw_id(issue_number, adw_id)
    print(f"Using ADW ID: {adw_id}")

    # Post initial message
    try:
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: ⚡ **Starting Lightweight Workflow**\n\n"
            "This optimized workflow will:\n"
            "1. ✍️ Create minimal plan\n"
            "2. 🔨 Implement changes (focused)\n"
            "3. ✅ Quick validation\n"
            "4. 🚢 Ship to production\n\n"
            "💰 Estimated cost: $0.20 - $0.50",
        )
    except Exception as e:
        print(f"Warning: Failed to post initial comment: {e}")

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Run plan phase (standard)
    plan_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_plan_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n=== PLAN PHASE ===")
    print(f"Running: {' '.join(plan_cmd)}")
    plan = subprocess.run(plan_cmd)
    if plan.returncode != 0:
        print("Plan phase failed")
        sys.exit(1)

    # Run build phase (standard)
    build_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_build_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n=== BUILD PHASE ===")
    print(f"Running: {' '.join(build_cmd)}")
    build = subprocess.run(build_cmd)
    if build.returncode != 0:
        print("Build phase failed")
        sys.exit(1)

    # Quick validation (build only, skip tests)
    print(f"\n=== QUICK VALIDATION ===")
    print("Skipping extensive testing for lightweight workflow")
    try:
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: ✅ Quick validation passed (skipped extensive testing for lightweight workflow)",
        )
    except:
        pass

    # Ship immediately (no review, no docs)
    ship_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_ship_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n=== SHIP PHASE ===")
    print(f"Running: {' '.join(ship_cmd)}")
    ship = subprocess.run(ship_cmd)
    if ship.returncode != 0:
        print("Ship phase failed")
        try:
            make_issue_comment(
                issue_number,
                f"{adw_id}_ops: ❌ **Lightweight Workflow Failed** - Ship phase failed\n\n"
                "Could not automatically merge the PR.\n"
                "Please check the ship logs and merge manually if needed.",
            )
        except:
            pass
        sys.exit(1)

    print(f"\n=== ⚡ LIGHTWEIGHT WORKFLOW COMPLETED ===")
    print(f"ADW ID: {adw_id}")
    print(f"✅ Code has been shipped!")
    print(f"\nWorktree location: trees/{adw_id}/")
    print(f"To clean up: ./scripts/purge_tree.sh {adw_id}")

    try:
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: ⚡ **Lightweight Workflow Complete!**\n\n"
            "✅ Plan phase completed\n"
            "✅ Build phase completed\n"
            "✅ Quick validation passed\n"
            "✅ Ship phase completed\n\n"
            "🚢 **Code has been shipped!**",
        )
    except:
        pass


if __name__ == "__main__":
    main()
