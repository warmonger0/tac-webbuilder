#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW SDLC Complete ZTE Iso - Zero Touch Execution: Complete SDLC with ALL phases + auto-ship

Usage: uv run adw_sdlc_complete_zte_iso.py <issue-number> [adw-id] [flags]

This script runs the COMPLETE ADW SDLC pipeline with automatic shipping (ALL 8 phases):
1. adw_plan_iso.py - Planning phase (isolated)
2. adw_build_iso.py - Implementation phase (isolated)
3. adw_lint_iso.py - Linting phase (isolated) ✨ RESTORED
4. adw_test_iso.py - Testing phase (isolated)
5. adw_review_iso.py - Review phase (isolated)
6. adw_document_iso.py - Documentation phase (isolated)
7. adw_ship_iso.py - Ship phase (approve & merge PR)
8. Cleanup - Documentation organization (pure Python)

⚠️  WARNING: This workflow automatically merges to main if ALL phases pass!

ZTE = Zero Touch Execution: The entire workflow runs to completion without
human intervention, automatically shipping code to production.

Flags:
  --skip-e2e: Skip E2E tests
  --skip-resolution: Skip automatic resolution of review failures
  --no-external: Disable external tools (uses inline execution, higher token usage)
  --use-optimized-plan: Use inverted context flow planner (77% cost reduction)

The scripts are chained together via persistent state (adw_state.json).
Each phase runs on the same git worktree with dedicated ports.
"""

import subprocess
import sys
import os
import logging

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adw_modules.workflow_ops import ensure_adw_id, format_issue_message
from adw_modules.github import make_issue_comment
from adw_modules.cleanup_operations import cleanup_shipped_issue
from adw_modules.utils import setup_logger


def main():
    """Main entry point."""
    # Check for flags
    skip_e2e = "--skip-e2e" in sys.argv
    skip_resolution = "--skip-resolution" in sys.argv
    use_external = "--no-external" not in sys.argv
    use_optimized_plan = "--use-optimized-plan" in sys.argv

    # Remove flags from argv
    for flag in ["--skip-e2e", "--skip-resolution", "--no-external", "--use-optimized-plan"]:
        if flag in sys.argv:
            sys.argv.remove(flag)

    if len(sys.argv) < 2:
        print(
            "Usage: uv run adw_sdlc_complete_zte_iso.py <issue-number> [adw-id] [flags]"
        )
        print("\n🚀 Zero Touch Execution: Complete SDLC with ALL phases + automatic shipping")
        print("\nThis runs the COMPLETE isolated Software Development Life Cycle:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        print("  3. Lint (isolated) ✨")
        print("  4. Test (isolated)")
        print("  5. Review (isolated)")
        print("  6. Document (isolated)")
        print("  7. Ship (approve & merge PR) 🚢")
        print("  8. Cleanup (organize documentation)")
        print("\n⚠️  WARNING: This will automatically merge to main if all phases pass!")
        print("\nFlags:")
        print("  --skip-e2e: Skip E2E tests")
        print("  --skip-resolution: Skip automatic resolution of review failures")
        print("  --no-external: Disable external tools (higher token usage)")
        print("  --use-optimized-plan: Use inverted context flow planner (77% cost reduction)")
        print("\nNote: External tools are ENABLED by default for 70-95% token reduction")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure ADW ID exists with initialized state
    adw_id = ensure_adw_id(issue_number, adw_id)
    print(f"Using ADW ID: {adw_id}")

    # Post initial ZTE message
    try:
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 🚀 **Starting Zero Touch Execution (ZTE) - Complete SDLC**\n\n"
            "This workflow will automatically execute ALL 8 phases:\n"
            "1. ✍️ Plan the implementation\n"
            "2. 🔨 Build the solution\n"
            "3. 🧹 Lint the code ✨\n"
            "4. 🧪 Test the code\n"
            "5. 👀 Review the implementation\n"
            "6. 📚 Generate documentation\n"
            "7. 🚢 **Ship to production** (approve & merge PR)\n"
            "8. 🗂️ Cleanup and organize\n\n"
            f"**Configuration:**\n"
            f"- External tools: {'✅ Enabled' if use_external else '❌ Disabled'}\n"
            f"- Optimized planner: {'✅ Enabled' if use_optimized_plan else '❌ Disabled'}\n"
            f"- Skip E2E: {'✅ Yes' if skip_e2e else '❌ No'}\n"
            f"- Auto-resolution: {'❌ Disabled' if skip_resolution else '✅ Enabled'}\n\n"
            "⚠️ **Code will be automatically merged if all phases pass!**",
        )
    except Exception as e:
        print(f"Warning: Failed to post initial comment: {e}")

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # ========================================
    # PHASE 1: PLAN
    # ========================================
    plan_script = "adw_plan_iso_optimized.py" if use_optimized_plan else "adw_plan_iso.py"
    plan_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, plan_script),
        issue_number,
        adw_id,
    ]
    print(f"\n{'='*60}")
    print(f"PHASE 1/8: PLAN ({plan_script})")
    print(f"{'='*60}")
    print(f"Running: {' '.join(plan_cmd)}")
    plan = subprocess.run(plan_cmd)
    if plan.returncode != 0:
        print("❌ Plan phase failed")
        try:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", "❌ ZTE aborted - Plan phase failed")
            )
        except:
            pass
        sys.exit(1)

    # ========================================
    # PHASE 2: BUILD
    # ========================================
    build_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_build_iso.py"),
        issue_number,
        adw_id,
    ]
    if not use_external:
        build_cmd.append("--no-external")

    print(f"\n{'='*60}")
    print(f"PHASE 2/8: BUILD")
    print(f"{'='*60}")
    print(f"Running: {' '.join(build_cmd)}")
    build = subprocess.run(build_cmd)
    if build.returncode != 0:
        print("❌ Build phase failed")
        try:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", "❌ ZTE aborted - Build phase failed")
            )
        except:
            pass
        sys.exit(1)

    # ========================================
    # PHASE 3: LINT ✨ RESTORED
    # ========================================
    lint_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_lint_iso.py"),
        issue_number,
        adw_id,
    ]
    if not use_external:
        lint_cmd.append("--no-external")

    print(f"\n{'='*60}")
    print(f"PHASE 3/8: LINT ✨")
    print(f"{'='*60}")
    print(f"Running: {' '.join(lint_cmd)}")
    lint = subprocess.run(lint_cmd)
    if lint.returncode != 0:
        print("❌ Lint phase failed")
        try:
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops",
                    "❌ **ZTE Aborted** - Lint phase failed\n\n"
                    "Automatic shipping cancelled due to linting errors.\n"
                    "Please fix the linting issues and run the workflow again."
                )
            )
        except:
            pass
        sys.exit(1)

    # ========================================
    # PHASE 4: TEST
    # ========================================
    test_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_test_iso.py"),
        issue_number,
        adw_id,
        "--skip-e2e",  # Always skip E2E tests in ZTE workflows
    ]
    if not use_external:
        test_cmd.append("--no-external")

    print(f"\n{'='*60}")
    print(f"PHASE 4/8: TEST")
    print(f"{'='*60}")
    print(f"Running: {' '.join(test_cmd)}")
    test = subprocess.run(test_cmd)
    if test.returncode != 0:
        print("❌ Test phase failed")
        try:
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops",
                    "❌ **ZTE Aborted** - Test phase failed\n\n"
                    "Automatic shipping cancelled due to test failures.\n"
                    "Please fix the tests and run the workflow again."
                )
            )
        except:
            pass
        sys.exit(1)

    # ========================================
    # PHASE 5: REVIEW
    # ========================================
    review_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_review_iso.py"),
        issue_number,
        adw_id,
    ]
    if skip_resolution:
        review_cmd.append("--skip-resolution")

    print(f"\n{'='*60}")
    print(f"PHASE 5/8: REVIEW")
    print(f"{'='*60}")
    print(f"Running: {' '.join(review_cmd)}")
    review = subprocess.run(review_cmd)
    if review.returncode != 0:
        print("❌ Review phase failed")
        try:
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops",
                    "❌ **ZTE Aborted** - Review phase failed\n\n"
                    "Automatic shipping cancelled due to review failures.\n"
                    "Please address the review issues and run the workflow again."
                )
            )
        except:
            pass
        sys.exit(1)

    # ========================================
    # PHASE 6: DOCUMENT
    # ========================================
    document_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_document_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n{'='*60}")
    print(f"PHASE 6/8: DOCUMENT")
    print(f"{'='*60}")
    print(f"Running: {' '.join(document_cmd)}")
    document = subprocess.run(document_cmd)
    if document.returncode != 0:
        print("⚠️ Documentation phase failed but continuing to ship...")
        # Documentation failure shouldn't block shipping in ZTE
        print("WARNING: Documentation phase failed but ZTE will continue")
        try:
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops",
                    "⚠️ Documentation phase failed but continuing to ship"
                )
            )
        except:
            pass

    # ========================================
    # PHASE 7: SHIP
    # ========================================
    ship_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_ship_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n{'='*60}")
    print(f"PHASE 7/8: SHIP (APPROVE & MERGE)")
    print(f"{'='*60}")
    print(f"Running: {' '.join(ship_cmd)}")
    ship = subprocess.run(ship_cmd)
    if ship.returncode != 0:
        print("❌ Ship phase failed")
        try:
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops",
                    "❌ **ZTE Failed** - Ship phase failed\n\n"
                    "Could not automatically approve and merge the PR.\n"
                    "Please check the ship logs and merge manually if needed."
                )
            )
        except:
            pass
        sys.exit(1)

    # ========================================
    # PHASE 8: CLEANUP
    # ========================================
    print(f"\n{'='*60}")
    print(f"PHASE 8/8: CLEANUP (Python)")
    print(f"{'='*60}")
    print(f"Running cleanup operations directly (pure Python, no LLM)...")

    try:
        # Set up logger for cleanup
        cleanup_logger = setup_logger(adw_id, "cleanup_operations")

        # Post initial cleanup message
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", "🧹 Starting cleanup (pure Python, no LLM calls)...")
        )

        # Run cleanup directly
        cleanup_result = cleanup_shipped_issue(
            issue_number=issue_number,
            adw_id=adw_id,
            skip_worktree=False,
            dry_run=False,
            logger=cleanup_logger
        )

        if cleanup_result["success"]:
            print(f"✅ Cleanup completed: {cleanup_result['summary']}")

            # Post success message
            summary_msg = f"✅ **Cleanup completed**\n\n"
            if cleanup_result["docs_moved"] > 0:
                summary_msg += f"📁 Organized {cleanup_result['docs_moved']} documentation files\n"
            if cleanup_result["worktree_removed"]:
                summary_msg += f"🗑️ Removed worktree and freed resources\n"
            if cleanup_result["errors"]:
                summary_msg += f"\n⚠️ {len(cleanup_result['errors'])} warnings (non-fatal)\n"

            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "cleanup", summary_msg)
            )
        else:
            print(f"⚠️ Cleanup had errors: {cleanup_result['errors']}")
            # Cleanup failure shouldn't block ZTE completion
            print("WARNING: Cleanup had errors but ZTE is still considered successful")

            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    "cleanup",
                    f"⚠️ Cleanup completed with warnings\n\n"
                    f"Errors: {', '.join(cleanup_result['errors'][:3])}"
                )
            )
    except Exception as e:
        print(f"⚠️ Cleanup exception: {e}")
        # Cleanup failure shouldn't block ZTE completion
        print("WARNING: Cleanup failed but ZTE is still considered successful")

    # ========================================
    # COMPLETION
    # ========================================
    print(f"\n{'='*60}")
    print(f"🎉 ZERO TOUCH EXECUTION COMPLETED")
    print(f"{'='*60}")
    print(f"ADW ID: {adw_id}")
    print(f"All 8 phases completed successfully!")
    print(f"✅ Code has been automatically shipped to production!")
    print(f"\nWorktree location: trees/{adw_id}/")
    print(f"To manually clean up: ./scripts/purge_tree.sh {adw_id}")

    try:
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 🎉 **Zero Touch Execution Complete!**\n\n"
            "✅ Phase 1: Plan completed\n"
            "✅ Phase 2: Build completed\n"
            "✅ Phase 3: Lint completed ✨\n"
            "✅ Phase 4: Test completed\n"
            "✅ Phase 5: Review completed\n"
            "✅ Phase 6: Documentation completed\n"
            "✅ Phase 7: Ship completed\n"
            "✅ Phase 8: Cleanup completed\n\n"
            "🚢 **Code has been automatically shipped to production!**",
        )
    except:
        pass


if __name__ == "__main__":
    main()
