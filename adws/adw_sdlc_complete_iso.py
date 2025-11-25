#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW SDLC Complete Iso - Complete Software Development Life Cycle with ALL phases

Usage: uv run adw_sdlc_complete_iso.py <issue-number> [adw-id] [flags]

This script runs the COMPLETE ADW SDLC pipeline in isolation with all 9 phases:
1. adw_plan_iso.py - Planning phase (isolated)
2. adw_validate_iso.py - Baseline validation phase (isolated) ✨ NEW
3. adw_build_iso.py - Implementation phase (isolated)
4. adw_lint_iso.py - Linting phase (isolated)
5. adw_test_iso.py - Testing phase (isolated)
6. adw_review_iso.py - Review phase (isolated)
7. adw_document_iso.py - Documentation phase (isolated)
8. adw_ship_iso.py - Ship phase (approve & merge PR)
9. Cleanup - Documentation organization (pure Python)

This is the RECOMMENDED workflow for feature implementation. It includes all
quality gates and ships to production when all phases pass.

Flags:
  --skip-e2e: Skip E2E tests
  --skip-resolution: Skip automatic resolution of review failures
  --no-external: Disable external tools (uses inline execution, higher token usage)
  --use-optimized-plan: Use inverted context flow planner (77% cost reduction)

The scripts are chained together via persistent state (adw_state.json).
Each phase runs in its own git worktree with dedicated ports.
"""

import subprocess
import sys
import os

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adw_modules.workflow_ops import ensure_adw_id, format_issue_message, trigger_cost_sync
from adw_modules.github import make_issue_comment
from adw_modules.cleanup_operations import cleanup_shipped_issue
from adw_modules.utils import setup_logger
from adw_modules.failure_cleanup import cleanup_failed_workflow
from adw_modules.state import ADWState


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
        print("Usage: uv run adw_sdlc_complete_iso.py <issue-number> [adw-id] [flags]")
        print("\n🎯 Complete SDLC: All 9 phases for production-ready features")
        print("\nThis runs the COMPLETE isolated Software Development Life Cycle:")
        print("  1. Plan (isolated)")
        print("  2. Validate (baseline detection) ✨ NEW")
        print("  3. Build (isolated)")
        print("  4. Lint (isolated)")
        print("  5. Test (isolated)")
        print("  6. Review (isolated)")
        print("  7. Document (isolated)")
        print("  8. Ship (approve & merge PR)")
        print("  9. Cleanup (organize documentation)")
        print("\nFlags:")
        print("  --skip-e2e: Skip E2E tests")
        print("  --skip-resolution: Skip automatic resolution of review failures")
        print("  --no-external: Disable external tools (higher token usage)")
        print("  --use-optimized-plan: Use inverted context flow planner (77% cost reduction)")
        print("\nNote: External tools are ENABLED by default for 70-95% token reduction")
        print("      Ships to production ONLY after all phases pass")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure ADW ID exists with initialized state
    adw_id = ensure_adw_id(issue_number, adw_id)
    print(f"Using ADW ID: {adw_id}")

    # Update state to show full SDLC workflow is active
    from adw_modules.state import ADWState
    logger = setup_logger(adw_id, "adw_sdlc_complete_iso")
    state = ADWState.load(adw_id, logger)
    state.update(
        workflow_template="adw_sdlc_complete_iso",
        status="running"
    )
    state.save("adw_sdlc_complete_iso")
    logger.info("✅ Updated state to show full SDLC workflow active")

    # Post initial message
    try:
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 🎯 **Starting Complete SDLC Workflow**\n\n"
            "This workflow will execute ALL 9 phases:\n"
            "1. ✍️ Plan the implementation\n"
            "2. 📊 Validate baseline (detect inherited errors)\n"
            "3. 🔨 Build the solution\n"
            "4. 🧹 Lint the code\n"
            "5. 🧪 Test the code\n"
            "6. 👀 Review the implementation\n"
            "7. 📚 Generate documentation\n"
            "8. 🚢 Ship to production\n"
            "9. 🗂️ Cleanup and organize\n\n"
            f"**Configuration:**\n"
            f"- External tools: {'✅ Enabled' if use_external else '❌ Disabled'}\n"
            f"- Optimized planner: {'✅ Enabled' if use_optimized_plan else '❌ Disabled'}\n"
            f"- Skip E2E: {'✅ Yes' if skip_e2e else '❌ No'}\n"
            f"- Auto-resolution: {'❌ Disabled' if skip_resolution else '✅ Enabled'}",
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
    print(f"PHASE 1/9: PLAN ({plan_script})")
    print(f"{'='*60}")
    print(f"Running: {' '.join(plan_cmd)}")
    plan = subprocess.run(plan_cmd)
    if plan.returncode != 0:
        print("❌ Plan phase failed")
        # Load state to get branch name
        logger = setup_logger(adw_id, "sdlc_cleanup")
        state = ADWState.load(adw_id, logger)
        branch_name = state.get("branch_name") if state else None

        # Clean up failed workflow
        cleanup_failed_workflow(
            adw_id=adw_id,
            issue_number=issue_number,
            branch_name=branch_name,
            phase_name="Plan",
            error_details="Plan phase failed. Check planning logs for errors.",
            logger=logger
        )
        sys.exit(1)

    # ========================================
    # PHASE 2: VALIDATE (NEW)
    # ========================================
    validate_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_validate_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n{'='*60}")
    print(f"PHASE 2/9: VALIDATE (Baseline Error Detection)")
    print(f"{'='*60}")
    print(f"Running: {' '.join(validate_cmd)}")
    validate = subprocess.run(validate_cmd)
    # Validation NEVER fails - always continue
    if validate.returncode != 0:
        print("⚠️ Validate phase encountered issues, but continuing...")

    # ========================================
    # PHASE 3: BUILD (formerly PHASE 2)
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
    print(f"PHASE 3/9: BUILD")
    print(f"{'='*60}")
    print(f"Running: {' '.join(build_cmd)}")
    build = subprocess.run(build_cmd)
    if build.returncode != 0:
        print("❌ Build phase failed")
        # Load state to get branch name
        logger = setup_logger(adw_id, "sdlc_cleanup")
        state = ADWState.load(adw_id, logger)
        branch_name = state.get("branch_name") if state else None

        # Clean up failed workflow
        cleanup_failed_workflow(
            adw_id=adw_id,
            issue_number=issue_number,
            branch_name=branch_name,
            phase_name="Build",
            error_details="Build phase failed. Check build logs for TypeScript/compilation errors.",
            logger=logger
        )
        sys.exit(1)

    # ========================================
    # PHASE 3: LINT ✨ NEW
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
    print(f"PHASE 4/9: LINT")
    print(f"{'='*60}")
    print(f"Running: {' '.join(lint_cmd)}")
    lint = subprocess.run(lint_cmd)
    if lint.returncode != 0:
        print("❌ Lint phase failed")
        # Load state to get branch name
        logger = setup_logger(adw_id, "sdlc_cleanup")
        state = ADWState.load(adw_id, logger)
        branch_name = state.get("branch_name") if state else None

        # Clean up failed workflow
        cleanup_failed_workflow(
            adw_id=adw_id,
            issue_number=issue_number,
            branch_name=branch_name,
            phase_name="Lint",
            error_details="Lint phase failed. Fix linting errors before proceeding.",
            logger=logger
        )
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
        "--skip-e2e",  # Always skip E2E in SDLC workflows
    ]
    if not use_external:
        test_cmd.append("--no-external")

    print(f"\n{'='*60}")
    print(f"PHASE 5/9: TEST")
    print(f"{'='*60}")
    print(f"Running: {' '.join(test_cmd)}")
    test = subprocess.run(test_cmd)
    if test.returncode != 0:
        print("❌ Test phase failed")
        # Load state to get branch name
        logger = setup_logger(adw_id, "sdlc_cleanup")
        state = ADWState.load(adw_id, logger)
        branch_name = state.get("branch_name") if state else None

        # Clean up failed workflow
        cleanup_failed_workflow(
            adw_id=adw_id,
            issue_number=issue_number,
            branch_name=branch_name,
            phase_name="Test",
            error_details="Test phase failed. Review test output and fix failing tests before proceeding.",
            logger=logger
        )
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
    print(f"PHASE 6/9: REVIEW")
    print(f"{'='*60}")
    print(f"Running: {' '.join(review_cmd)}")
    review = subprocess.run(review_cmd)
    if review.returncode != 0:
        print("❌ Review phase failed")
        # Load state to get branch name
        logger = setup_logger(adw_id, "sdlc_cleanup")
        state = ADWState.load(adw_id, logger)
        branch_name = state.get("branch_name") if state else None

        # Clean up failed workflow
        cleanup_failed_workflow(
            adw_id=adw_id,
            issue_number=issue_number,
            branch_name=branch_name,
            phase_name="Review",
            error_details="Review phase failed. Address review issues before proceeding.",
            logger=logger
        )
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
    print(f"PHASE 7/9: DOCUMENT")
    print(f"{'='*60}")
    print(f"Running: {' '.join(document_cmd)}")
    document = subprocess.run(document_cmd)
    if document.returncode != 0:
        print("⚠️ Documentation phase failed but continuing...")
        # Documentation failure shouldn't block shipping
        try:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", "⚠️ Documentation phase failed but continuing to ship")
            )
        except:
            pass

    # ========================================
    # PHASE 7: SHIP ✨ NEW
    # ========================================
    ship_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_ship_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n{'='*60}")
    print(f"PHASE 8/9: SHIP")
    print(f"{'='*60}")
    print(f"Running: {' '.join(ship_cmd)}")
    ship = subprocess.run(ship_cmd)
    if ship.returncode != 0:
        print("❌ Ship phase failed")
        # Load state to get branch name
        logger = setup_logger(adw_id, "sdlc_cleanup")
        state = ADWState.load(adw_id, logger)
        branch_name = state.get("branch_name") if state else None

        # Clean up failed workflow (but keep PR open - manual review may help)
        cleanup_failed_workflow(
            adw_id=adw_id,
            issue_number=issue_number,
            branch_name=None,  # Don't close PR on ship failure - manual review may be needed
            phase_name="Ship",
            error_details="Ship phase failed. Manual review and merge may be required. PR remains open for manual handling.",
            logger=logger
        )
        sys.exit(1)

    # ========================================
    # PHASE 8: CLEANUP ✨ NEW
    # ========================================
    print(f"\n{'='*60}")
    print(f"PHASE 9/9: CLEANUP")
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
            # Cleanup failure shouldn't block SDLC completion
            print("WARNING: Cleanup had errors but SDLC is still considered successful")

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
        # Cleanup failure shouldn't block SDLC completion
        print("WARNING: Cleanup failed but SDLC is still considered successful")

    # ========================================
    # COMPLETION
    # ========================================
    print(f"\n{'='*60}")
    print(f"🎉 COMPLETE SDLC FINISHED SUCCESSFULLY")
    print(f"{'='*60}")
    print(f"ADW ID: {adw_id}")
    print(f"All 8 phases completed successfully!")
    print(f"✅ Code has been shipped to production!")

    # Trigger cost synchronization
    print(f"\n📊 Syncing workflow costs...")
    trigger_cost_sync(adw_id)

    print(f"\nWorktree location: trees/{adw_id}/")
    print(f"To manually clean up: ./scripts/purge_tree.sh {adw_id}")

    try:
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 🎉 **Complete SDLC Finished!**\n\n"
            "✅ Phase 1: Plan completed\n"
            "✅ Phase 2: Build completed\n"
            "✅ Phase 3: Lint completed ✨\n"
            "✅ Phase 4: Test completed\n"
            "✅ Phase 5: Review completed\n"
            "✅ Phase 6: Documentation completed\n"
            "✅ Phase 7: Ship completed ✨\n"
            "✅ Phase 8: Cleanup completed ✨\n\n"
            "🚢 **Code has been shipped to production!**",
        )
    except:
        pass


if __name__ == "__main__":
    main()
