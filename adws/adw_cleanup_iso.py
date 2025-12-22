#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Cleanup Iso - AI Developer Workflow for documentation cleanup after shipping

Usage:
  uv run adw_cleanup_iso.py <issue-number> <adw-id>

Workflow:
1. Load state and validate all previous phases completed
2. Organize documentation files:
   - Move specs from /specs/ to archived issues folder
   - Move implementation plans from /docs/ to archived issues folder
   - Move summaries and related docs to archived issues folder
3. Create README in archived folder
4. Remove worktree and free resources
5. Update state with cleanup metadata
6. Post cleanup summary to issue

This workflow is designed to run after successful ship (adw_ship_iso.py) to
organize documentation files into appropriate subfolders. It can also be run
manually for any completed issue.

This workflow NEVER fails - all errors are logged as warnings and the workflow
continues. Cleanup is a best-effort operation.
"""

import sys
import os
import logging
import json
from typing import Optional
from dotenv import load_dotenv

from adw_modules.state import ADWState
from utils.idempotency import (
    check_and_skip_if_complete,
    validate_phase_completion,
    ensure_database_state,
)
from adw_modules.github import make_issue_comment
from adw_modules.workflow_ops import format_issue_message
from adw_modules.utils import setup_logger, check_env_vars
from adw_modules.doc_cleanup import cleanup_adw_documentation
from adw_modules.worktree_ops import remove_worktree
from adw_modules.observability import log_phase_completion, get_phase_number
from adw_modules.tool_call_tracker import ToolCallTracker

# Agent name constant
AGENT_CLEANUP = "cleanup"


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse command line args
    if len(sys.argv) < 3:
        print("Usage: uv run adw_cleanup_iso.py <issue-number> <adw-id>")
        print("\nError: Both issue-number and adw-id are required")
        print("This workflow organizes documentation after successful ship")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2]

    # Try to load existing state
    temp_logger = setup_logger(adw_id, "adw_cleanup_iso")
    state = ADWState.load(adw_id, temp_logger)
    if not state:
        # No existing state found
        logger = setup_logger(adw_id, "adw_cleanup_iso")
        logger.error(f"No state found for ADW ID: {adw_id}")
        logger.error("Run the complete SDLC workflow before cleanup")
        print(f"\nError: No state found for ADW ID: {adw_id}")
        print("Run the complete SDLC workflow before cleanup")
        sys.exit(1)

    # Update issue number from state if available
    issue_number = state.get("issue_number", issue_number)

    # Track that this ADW workflow has run
    state.append_adw_id("adw_cleanup_iso")

    # Set up logger with ADW ID
    logger = setup_logger(adw_id, "adw_cleanup_iso")
    logger.info(f"ADW Cleanup Iso starting - ID: {adw_id}, Issue: {issue_number}")

    # Validate environment
    check_env_vars(logger)

    # IDEMPOTENCY CHECK: Skip if cleanup phase already complete
    if check_and_skip_if_complete('cleanup', int(issue_number), logger):
        logger.info(f"{'='*60}")
        logger.info(f"Cleanup phase already complete for issue {issue_number}")
        state = ADWState.load(adw_id, temp_logger)
        logger.info(f"Cleanup complete: {state.get('cleanup_complete', {})}")
        logger.info(f"{'='*60}")
        sys.exit(0)

    # Post initial status
    make_issue_comment(
        issue_number,
        format_issue_message(
            adw_id, "ops", f"🧹 Starting documentation cleanup workflow\n"
                           f"📋 Organizing documentation files..."
        )
    )

    with ToolCallTracker(adw_id=adw_id, issue_number=int(issue_number), phase_name="Cleanup") as tracker:
        # Step 1: Run cleanup
        logger.info("Starting documentation cleanup...")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                AGENT_CLEANUP,
                "📁 Organizing documentation files...\n"
                "- Moving specs to archived issues\n"
                "- Moving implementation plans\n"
                "- Moving summaries and related docs\n"
                "- Removing worktree and freeing resources"
            )
        )

        try:
            cleanup_result = cleanup_adw_documentation(
                issue_number=issue_number,
                adw_id=adw_id,
                state=state,
                logger=logger,
                dry_run=False
            )

            if cleanup_result["success"]:
                if cleanup_result["files_moved"] > 0:
                    logger.info(f"✅ Cleaned up {cleanup_result['files_moved']} documentation files")

                    # Build detailed summary
                    summary_msg = f"✅ **Documentation cleanup completed**\n\n"
                    summary_msg += f"📊 **Summary:**\n{cleanup_result['summary']}\n"

                    if cleanup_result.get("moves"):
                        summary_msg += f"\n📝 **Files organized:**\n"
                        for move in cleanup_result["moves"][:10]:  # Show first 10
                            src_name = os.path.basename(move["src"])
                            summary_msg += f"- `{src_name}` → `{move['dest']}`\n"

                        if len(cleanup_result["moves"]) > 10:
                            summary_msg += f"\n... and {len(cleanup_result['moves']) - 10} more files\n"

                    if cleanup_result.get("errors"):
                        summary_msg += f"\n⚠️ **Warnings:** {len(cleanup_result['errors'])} file(s) could not be moved\n"

                    make_issue_comment(
                        issue_number,
                        format_issue_message(adw_id, AGENT_CLEANUP, summary_msg)
                    )
                else:
                    logger.info("ℹ️ No documentation files needed cleanup")
                    make_issue_comment(
                        issue_number,
                        format_issue_message(
                            adw_id,
                            AGENT_CLEANUP,
                            "ℹ️ No documentation files needed cleanup\n"
                            "All files are already organized"
                        )
                    )
            else:
                logger.warning(f"Cleanup completed with errors: {cleanup_result['errors']}")
                make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id,
                        AGENT_CLEANUP,
                        f"⚠️ **Documentation cleanup completed with warnings**\n\n"
                        f"{cleanup_result['summary']}\n\n"
                        f"Errors: {', '.join(cleanup_result['errors'][:3])}"
                    )
                )

        except Exception as e:
            # Never fail the cleanup workflow
            error_msg = f"Documentation cleanup error (non-fatal): {e}"
            logger.error(error_msg)
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_CLEANUP,
                    f"⚠️ **Documentation cleanup encountered an error**\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Manual cleanup may be needed"
                )
            )

        # Step 2: Remove worktree
        logger.info("Removing worktree...")
        try:
            worktree_path = state.get("worktree_path")
            if worktree_path:
                make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id,
                        AGENT_CLEANUP,
                        f"🗑️ Removing worktree at `{worktree_path}`..."
                    )
                )

                success, error = remove_worktree(adw_id, logger, tracker=tracker)
                if success:
                    logger.info(f"✅ Worktree removed: {worktree_path}")
                    make_issue_comment(
                        issue_number,
                        format_issue_message(
                            adw_id,
                            AGENT_CLEANUP,
                            f"✅ Worktree removed successfully\n"
                            f"Freed resources: Backend port, Frontend port, Disk space"
                        )
                    )
                else:
                    logger.warning(f"Failed to remove worktree: {error}")
                    make_issue_comment(
                        issue_number,
                        format_issue_message(
                            adw_id,
                            AGENT_CLEANUP,
                            f"⚠️ Failed to remove worktree: {error}\n"
                            f"You can manually remove it with: `./scripts/purge_tree.sh {adw_id}`"
                        )
                    )
            else:
                logger.info("No worktree path in state - skipping worktree removal")
        except Exception as e:
            # Never fail cleanup due to worktree removal errors
            logger.error(f"Error removing worktree (non-fatal): {e}")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_CLEANUP,
                    f"⚠️ Error removing worktree: {str(e)}\n"
                    f"Manual cleanup: `./scripts/purge_tree.sh {adw_id}`"
                )
            )

        # IDEMPOTENCY VALIDATION: Ensure phase outputs are valid
        try:
            validate_phase_completion('cleanup', int(issue_number), logger)
            ensure_database_state(int(issue_number), 'cleaned_up', 'cleanup', logger)
        except Exception as e:
            logger.error(f"Phase validation failed: {e}")
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", f"❌ Cleanup phase validation failed: {e}")
            )
            sys.exit(1)

        # OBSERVABILITY: Log phase completion
        from datetime import datetime
        start_time = datetime.fromisoformat(state.get("start_time")) if state.get("start_time") else None
        log_phase_completion(
            adw_id=adw_id,
            issue_number=int(issue_number),
            phase_name="Cleanup",
            phase_number=get_phase_number("Cleanup"),
            success=True,
            workflow_template="adw_cleanup_iso",
            started_at=start_time,
        )

        # Step 3: Save final state
        state.save("adw_cleanup_iso")

        # Post final state summary
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 📋 Final cleanup state:\n```json\n{json.dumps(state.data, indent=2)}\n```"
        )

        logger.info("Cleanup workflow completed successfully")


if __name__ == "__main__":
    main()
