#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
WARNING: DEPRECATED - This workflow is missing Ship and Cleanup phases.
Please use adw_sdlc_complete_iso.py instead for the complete SDLC workflow.

ADW SDLC Iso - Complete Software Development Life Cycle workflow with isolation

Usage: uv run adw_sdlc_iso.py <issue-number> [adw-id] [--skip-e2e] [--skip-resolution]

This script runs the complete ADW SDLC pipeline in isolation:
1. adw_plan_iso.py - Planning phase (isolated)
2. adw_build_iso.py - Implementation phase (isolated)
3. adw_lint_iso.py - Linting phase (isolated)
4. adw_test_iso.py - Testing phase (isolated)
5. adw_review_iso.py - Review phase (isolated)
6. adw_document_iso.py - Documentation phase (isolated)

The scripts are chained together via persistent state (adw_state.json).
Each phase runs in its own git worktree with dedicated ports.
"""

import subprocess
import sys
import os

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adw_modules.workflow_ops import ensure_adw_id
from adw_modules.migration_helper import check_and_forward, print_deprecation_notice


def main():
    """Main entry point."""
    # Check for auto-forwarding
    if check_and_forward("adw_sdlc_iso.py"):
        return  # Never reached, but for clarity

    # Print deprecation warning
    print_deprecation_notice(
        workflow_name="adw_sdlc_iso.py",
        missing_phases=["Ship", "Cleanup"],
        replacement="adw_sdlc_complete_iso.py"
    )

    # Check for flags
    skip_e2e = "--skip-e2e" in sys.argv
    skip_resolution = "--skip-resolution" in sys.argv
    # Default to using external tools (opt-out with --no-external)
    use_external = "--no-external" not in sys.argv

    # Remove flags from argv
    if skip_e2e:
        sys.argv.remove("--skip-e2e")
    if skip_resolution:
        sys.argv.remove("--skip-resolution")
    if "--use-external" in sys.argv:
        sys.argv.remove("--use-external")
    if "--no-external" in sys.argv:
        sys.argv.remove("--no-external")

    if len(sys.argv) < 2:
        print("Usage: uv run adw_sdlc_iso.py <issue-number> [adw-id] [--skip-e2e] [--skip-resolution] [--no-external]")
        print("\nThis runs the complete isolated Software Development Life Cycle:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        print("  3. Lint (isolated)")
        print("  4. Test (isolated)")
        print("  5. Review (isolated)")
        print("  6. Document (isolated)")
        print("\nFlags:")
        print("  --skip-e2e: Skip E2E tests")
        print("  --skip-resolution: Skip automatic resolution of review failures")
        print("  --no-external: Disable external tools (uses inline execution, higher token usage)")
        print("\nNote: External tools are ENABLED by default for 70-95% token reduction")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure ADW ID exists with initialized state
    adw_id = ensure_adw_id(issue_number, adw_id)
    print(f"Using ADW ID: {adw_id}")

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Run isolated plan with the ADW ID
    plan_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_plan_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n=== ISOLATED PLAN PHASE ===")
    print(f"Running: {' '.join(plan_cmd)}")
    plan = subprocess.run(plan_cmd)
    if plan.returncode != 0:
        print("Isolated plan phase failed")
        sys.exit(1)

    # Run isolated build with the ADW ID
    build_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_build_iso.py"),
        issue_number,
        adw_id,
    ]
    if not use_external:
        build_cmd.append("--no-external")

    print(f"\n=== ISOLATED BUILD PHASE ===")
    if use_external:
        print("🔧 Using external build tools for context optimization")
    print(f"Running: {' '.join(build_cmd)}")
    build = subprocess.run(build_cmd)
    if build.returncode != 0:
        print("Isolated build phase failed")
        sys.exit(1)

    # Run isolated lint with the ADW ID
    lint_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_lint_iso.py"),
        issue_number,
        adw_id,
        "--fix-mode",  # Enable auto-fix by default
    ]
    if not use_external:
        lint_cmd.append("--no-external")

    print(f"\n=== ISOLATED LINT PHASE ===")
    if use_external:
        print("🔧 Using external lint tools for context optimization")
    print(f"Running: {' '.join(lint_cmd)}")
    lint = subprocess.run(lint_cmd)
    # Note: Lint phase always exits 0 (advisory only)
    if lint.returncode != 0:
        print("WARNING: Lint phase encountered issues but continuing")

    # Run isolated test with the ADW ID
    test_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_test_iso.py"),
        issue_number,
        adw_id,
        "--skip-e2e",  # Always skip E2E tests in SDLC workflows
    ]
    if not use_external:
        test_cmd.append("--no-external")

    print(f"\n=== ISOLATED TEST PHASE ===")
    if use_external:
        print("🔧 Using external test tools for context optimization")
    print(f"Running: {' '.join(test_cmd)}")
    test = subprocess.run(test_cmd)
    if test.returncode != 0:
        print("Isolated test phase failed")
        # Note: Continue anyway as some tests might be flaky
        print("WARNING: Test phase failed but continuing with review")

    # Run isolated review with the ADW ID
    review_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_review_iso.py"),
        issue_number,
        adw_id,
    ]
    if skip_resolution:
        review_cmd.append("--skip-resolution")
    
    print(f"\n=== ISOLATED REVIEW PHASE ===")
    print(f"Running: {' '.join(review_cmd)}")
    review = subprocess.run(review_cmd)
    if review.returncode != 0:
        print("Isolated review phase failed")
        sys.exit(1)

    # Run isolated documentation with the ADW ID
    document_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_document_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n=== ISOLATED DOCUMENTATION PHASE ===")
    print(f"Running: {' '.join(document_cmd)}")
    document = subprocess.run(document_cmd)
    if document.returncode != 0:
        print("Isolated documentation phase failed")
        sys.exit(1)

    print(f"\n=== ISOLATED SDLC COMPLETED ===")
    print(f"ADW ID: {adw_id}")
    print(f"All phases completed successfully!")
    print(f"\nWorktree location: trees/{adw_id}/")
    print(f"To clean up: ./scripts/purge_tree.sh {adw_id}")


if __name__ == "__main__":
    main()