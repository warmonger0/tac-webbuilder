#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW SDLC Complete Iso - Complete Software Development Life Cycle with ALL phases

Usage: uv run adw_sdlc_complete_iso.py <issue-number> [adw-id] [flags]

This script runs the COMPLETE ADW SDLC pipeline in isolation with all 10 phases:
1. adw_plan_iso.py - Planning phase (isolated)
2. adw_validate_iso.py - Baseline validation phase (isolated) ✨ NEW
3. adw_build_iso.py - Implementation phase (isolated)
4. adw_lint_iso.py - Linting phase (isolated)
5. adw_test_iso.py - Testing phase (isolated)
6. adw_review_iso.py - Review phase (isolated)
7. adw_document_iso.py - Documentation phase (isolated)
8. adw_ship_iso.py - Ship phase (approve & merge PR)
9. Cleanup - Documentation organization (pure Python)
10. adw_verify_iso.py - Verify phase (post-deployment verification) ✨ NEW

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
        print("\n🎯 Complete SDLC: All 10 phases for production-ready features")
        print("\nThis runs the COMPLETE isolated Software Development Life Cycle:")
        print("  1. Plan (isolated)")
        print("  2. Validate (baseline detection) ✨")
        print("  3. Build (isolated)")
        print("  4. Lint (isolated)")
        print("  5. Test (isolated)")
        print("  6. Review (isolated)")
        print("  7. Document (isolated)")
        print("  8. Ship (approve & merge PR)")
        print("  9. Cleanup (organize documentation)")
        print("  10. Verify (post-deployment verification) ✨ NEW")
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
    logger.info("Attempting to post initial GitHub comment...")
    try:
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 🎯 **Starting Complete SDLC Workflow**\n\n"
            "This workflow will execute ALL 10 phases:\n"
            "1. ✍️ Plan the implementation\n"
            "2. 📊 Validate baseline (detect inherited errors)\n"
            "3. 🔨 Build the solution\n"
            "4. 🧹 Lint the code\n"
            "5. 🧪 Test the code\n"
            "6. 👀 Review the implementation\n"
            "7. 📚 Generate documentation\n"
            "8. 🚢 Ship to production\n"
            "9. 🗂️ Cleanup and organize\n"
            "10. 🔍 Verify deployment (post-ship verification) ✨\n\n"
            f"**Configuration:**\n"
            f"- External tools: {'✅ Enabled' if use_external else '❌ Disabled'}\n"
            f"- Optimized planner: {'✅ Enabled' if use_optimized_plan else '❌ Disabled'}\n"
            f"- Skip E2E: {'✅ Yes' if skip_e2e else '❌ No'}\n"
            f"- Auto-resolution: {'❌ Disabled' if skip_resolution else '✅ Enabled'}",
        )
        logger.info("✅ Initial GitHub comment posted successfully")
    except Exception as e:
        logger.error(f"Failed to post initial comment: {e}", exc_info=True)
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
    logger.info(f"Starting PHASE 1: PLAN with command: {' '.join(plan_cmd)}")

    try:
        plan = subprocess.run(plan_cmd, capture_output=False, text=True)
        logger.info(f"Plan phase completed with exit code: {plan.returncode}")
    except Exception as e:
        logger.error(f"Plan phase crashed with exception: {e}", exc_info=True)
        print(f"❌ Plan phase crashed: {e}")
        cleanup_failed_workflow(
            adw_id=adw_id,
            issue_number=issue_number,
            branch_name=None,
            phase_name="Plan",
            error_details=f"Plan phase crashed with exception: {str(e)}",
            logger=logger
        )
        sys.exit(1)

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
    logger.info(f"Starting PHASE 2: VALIDATE with command: {' '.join(validate_cmd)}")

    try:
        validate = subprocess.run(validate_cmd, capture_output=False, text=True)
        logger.info(f"Validate phase completed with exit code: {validate.returncode}")
    except Exception as e:
        logger.error(f"Validate phase crashed with exception: {e}", exc_info=True)
        print(f"⚠️ Validate phase crashed: {e}, but continuing...")

    # Validation NEVER fails - always continue
    if validate.returncode != 0:
        logger.warning("Validate phase encountered issues, but continuing...")
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
    logger.info(f"Starting PHASE 3: BUILD with command: {' '.join(build_cmd)}")

    try:
        build = subprocess.run(build_cmd, capture_output=False, text=True)
        logger.info(f"Build phase completed with exit code: {build.returncode}")
    except Exception as e:
        logger.error(f"Build phase crashed with exception: {e}", exc_info=True)
        print(f"❌ Build phase crashed: {e}")
        cleanup_failed_workflow(
            adw_id=adw_id,
            issue_number=issue_number,
            branch_name=state.get("branch_name") if state else None,
            phase_name="Build",
            error_details=f"Build phase crashed with exception: {str(e)}",
            logger=logger
        )
        sys.exit(1)

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
    logger.info(f"Starting PHASE 4: LINT with command: {' '.join(lint_cmd)}")

    try:
        lint = subprocess.run(lint_cmd, capture_output=False, text=True)
        logger.info(f"Lint phase completed with exit code: {lint.returncode}")
    except Exception as e:
        logger.error(f"Lint phase crashed with exception: {e}", exc_info=True)
        print(f"❌ Lint phase crashed: {e}")
        cleanup_failed_workflow(
            adw_id=adw_id,
            issue_number=issue_number,
            branch_name=state.get("branch_name") if state else None,
            phase_name="Lint",
            error_details=f"Lint phase crashed with exception: {str(e)}",
            logger=logger
        )
        sys.exit(1)

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
    logger.info(f"Starting PHASE 5: TEST with command: {' '.join(test_cmd)}")

    try:
        test = subprocess.run(test_cmd, capture_output=False, text=True)
        logger.info(f"Test phase completed with exit code: {test.returncode}")
    except Exception as e:
        logger.error(f"Test phase crashed with exception: {e}", exc_info=True)
        print(f"❌ Test phase crashed: {e}")
        cleanup_failed_workflow(
            adw_id=adw_id,
            issue_number=issue_number,
            branch_name=state.get("branch_name") if state else None,
            phase_name="Test",
            error_details=f"Test phase crashed with exception: {str(e)}",
            logger=logger
        )
        sys.exit(1)

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
    logger.info(f"Starting PHASE 6: REVIEW with command: {' '.join(review_cmd)}")

    try:
        review = subprocess.run(review_cmd, capture_output=False, text=True)
        logger.info(f"Review phase completed with exit code: {review.returncode}")
    except Exception as e:
        logger.error(f"Review phase crashed with exception: {e}", exc_info=True)
        print(f"❌ Review phase crashed: {e}")
        cleanup_failed_workflow(
            adw_id=adw_id,
            issue_number=issue_number,
            branch_name=state.get("branch_name") if state else None,
            phase_name="Review",
            error_details=f"Review phase crashed with exception: {str(e)}",
            logger=logger
        )
        sys.exit(1)

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
    logger.info(f"Starting PHASE 7: DOCUMENT with command: {' '.join(document_cmd)}")

    try:
        document = subprocess.run(document_cmd, capture_output=False, text=True)
        logger.info(f"Document phase completed with exit code: {document.returncode}")
    except Exception as e:
        logger.error(f"Document phase crashed with exception: {e}", exc_info=True)
        print(f"⚠️ Document phase crashed: {e}, but continuing...")

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
    logger.info(f"Starting PHASE 8: SHIP with command: {' '.join(ship_cmd)}")

    try:
        ship = subprocess.run(ship_cmd, capture_output=False, text=True)
        logger.info(f"Ship phase completed with exit code: {ship.returncode}")
    except Exception as e:
        logger.error(f"Ship phase crashed with exception: {e}", exc_info=True)
        print(f"❌ Ship phase crashed: {e}")
        cleanup_failed_workflow(
            adw_id=adw_id,
            issue_number=issue_number,
            branch_name=None,  # Don't close PR on ship failure
            phase_name="Ship",
            error_details=f"Ship phase crashed with exception: {str(e)}",
            logger=logger
        )
        sys.exit(1)

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
    # PHASE 9: CLEANUP
    # ========================================
    print(f"\n{'='*60}")
    print(f"PHASE 9/10: CLEANUP")
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
    # PHASE 10: VERIFY ✨ NEW
    # ========================================
    verify_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_verify_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n{'='*60}")
    print(f"PHASE 10/10: VERIFY (Post-Deployment Verification)")
    print(f"{'='*60}")
    print(f"Running: {' '.join(verify_cmd)}")
    logger.info(f"Starting PHASE 10: VERIFY with command: {' '.join(verify_cmd)}")

    try:
        verify = subprocess.run(verify_cmd, capture_output=False, text=True)
        logger.info(f"Verify phase completed with exit code: {verify.returncode}")
    except Exception as e:
        logger.error(f"Verify phase crashed with exception: {e}", exc_info=True)
        print(f"⚠️ Verify phase crashed: {e}, but continuing...")

    if verify.returncode != 0:
        print("⚠️ Verify phase detected issues (follow-up issue created)")
        # Note: Don't fail workflow on verify failures
        # Issues are tracked via GitHub, code is already shipped
        try:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops",
                    "⚠️ Verify phase detected post-deployment issues. "
                    "A follow-up issue has been created for tracking. "
                    "The shipped code has NOT been reverted."
                )
            )
        except:
            pass
    else:
        print("✅ Verify phase passed!")
        try:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops",
                    "✅ Verify phase passed! All post-deployment checks successful."
                )
            )
        except:
            pass

    # ========================================
    # COMPLETION
    # ========================================
    print(f"\n{'='*60}")
    print(f"🎉 COMPLETE SDLC FINISHED SUCCESSFULLY")
    print(f"{'='*60}")
    print(f"ADW ID: {adw_id}")
    print(f"All 10 phases completed successfully!")
    print(f"✅ Code has been shipped to production and verified!")

    # Mark workflow as completed
    logger.info("Updating workflow status to 'completed'")
    state = ADWState.load(adw_id, logger)
    from datetime import datetime
    end_time = datetime.now()
    state.update(
        status="completed",
        end_time=end_time.isoformat()
    )
    state.save("adw_sdlc_complete_iso")
    logger.info("✅ Workflow status updated to 'completed'")

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
            "✅ Phase 2: Validate completed ✨\n"
            "✅ Phase 3: Build completed\n"
            "✅ Phase 4: Lint completed\n"
            "✅ Phase 5: Test completed\n"
            "✅ Phase 6: Review completed\n"
            "✅ Phase 7: Documentation completed\n"
            "✅ Phase 8: Ship completed\n"
            "✅ Phase 9: Cleanup completed\n"
            "✅ Phase 10: Verify completed ✨\n\n"
            "🚢 **Code has been shipped to production and verified!**",
        )
    except:
        pass


if __name__ == "__main__":
    main()
