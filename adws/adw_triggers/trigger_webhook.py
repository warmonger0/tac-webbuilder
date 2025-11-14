#!/usr/bin/env -S uv run
# /// script
# dependencies = ["fastapi", "uvicorn", "python-dotenv"]
# ///

"""
GitHub Webhook Trigger - AI Developer Workflow (ADW)

FastAPI webhook endpoint that receives GitHub issue events and triggers ADW workflows.
Responds immediately to meet GitHub's 10-second timeout by launching workflows
in the background. Supports both standard and isolated workflows.

Usage: uv run trigger_webhook.py

Environment Requirements:
- PORT: Server port (default: 8001)
- All workflow requirements (GITHUB_PAT, ANTHROPIC_API_KEY, etc.)
"""

import os
import subprocess
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Optional
from fastapi import FastAPI, Request, BackgroundTasks
from dotenv import load_dotenv
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adw_modules.utils import make_adw_id, setup_logger, get_safe_subprocess_env
from adw_modules.github import make_issue_comment, ADW_BOT_IDENTIFIER
from adw_modules.workflow_ops import extract_adw_info, AVAILABLE_ADW_WORKFLOWS
from adw_modules.state import ADWState

# Add app/server to path for ADW lock and quota imports
app_server_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "app", "server")
sys.path.insert(0, app_server_path)

from core.adw_lock import acquire_lock, update_lock_status, release_lock
from core.api_quota import can_start_adw, log_quota_warning

# Load environment variables
load_dotenv()

# Configuration
PORT = int(os.getenv("PORT", "8001"))
CLASSIFIER_TIMEOUT = 30  # Maximum seconds to wait for ADW classification

# Dependent workflows that require existing worktrees
# These cannot be triggered directly via webhook
DEPENDENT_WORKFLOWS = [
    "adw_build_iso",
    "adw_test_iso",
    "adw_review_iso",
    "adw_document_iso",
    "adw_ship_iso",
]

# Create FastAPI app
app = FastAPI(
    title="ADW Webhook Trigger", description="GitHub webhook endpoint for ADW"
)

# Thread pool for background classification with timeout
executor = ThreadPoolExecutor(max_workers=4)

print(f"Starting ADW Webhook Trigger on port {PORT}")


def extract_adw_info_with_timeout(content: str, temp_id: str, timeout: int = CLASSIFIER_TIMEOUT):
    """
    Extract ADW info with timeout protection.

    Args:
        content: Content to classify (issue body or comment)
        temp_id: Temporary ADW ID for classification
        timeout: Maximum seconds to wait

    Returns:
        ADWExtractionResult or None if timeout/error
    """
    try:
        future = executor.submit(extract_adw_info, content, temp_id)
        result = future.result(timeout=timeout)
        return result
    except FuturesTimeoutError:
        print(f"⚠️ ADW classification timed out after {timeout}s - content length: {len(content)}")
        return None
    except Exception as e:
        print(f"⚠️ ADW classification error: {e}")
        return None


async def process_webhook_background(
    event_type: str,
    action: str,
    issue_number: int,
    content_to_check: str,
    trigger_source: str
):
    """
    Process webhook in background with classification and workflow launch.

    Args:
        event_type: GitHub event type (issues, issue_comment)
        action: Event action (opened, created)
        issue_number: GitHub issue number
        content_to_check: Content to analyze (issue body or comment)
        trigger_source: Description of trigger (e.g., "New issue", "Comment")
    """
    try:
        print(f"🔄 Background processing: {trigger_source} for issue #{issue_number}")

        # Use temporary ID for classification
        temp_id = make_adw_id()

        # Extract workflow info with timeout
        extraction_result = extract_adw_info_with_timeout(content_to_check, temp_id)

        if not extraction_result or not extraction_result.has_workflow:
            print(f"⚠️ No workflow detected in {trigger_source} for issue #{issue_number}")
            return

        workflow = extraction_result.workflow_command
        provided_adw_id = extraction_result.adw_id
        model_set = extraction_result.model_set
        trigger_reason = f"{trigger_source} with {workflow} workflow"

        # Validate workflow constraints (case-insensitive)
        if any(workflow.lower() == dep.lower() for dep in DEPENDENT_WORKFLOWS):
            if not provided_adw_id:
                print(f"❌ {workflow} requires ADW ID for issue #{issue_number}")
                try:
                    make_issue_comment(
                        str(issue_number),
                        f"❌ Error: `{workflow}` is a dependent workflow that requires an existing ADW ID.\n\n"
                        f"To run this workflow, you must provide the ADW ID in your comment, for example:\n"
                        f"`{workflow} adw-12345678`\n\n"
                        f"The ADW ID should come from a previous workflow run (like `adw_plan_iso` or `adw_patch_iso`).",
                    )
                except Exception as e:
                    print(f"Failed to post error comment: {e}")
                return

        # Check API quota before proceeding
        log_quota_warning()
        can_proceed, quota_error = can_start_adw()
        if not can_proceed:
            print(f"❌ Cannot start ADW workflow - API quota unavailable: {quota_error}")
            try:
                make_issue_comment(
                    str(issue_number),
                    f"❌ **Cannot Start ADW Workflow**\n\n"
                    f"API quota unavailable: {quota_error}\n\n"
                    f"The workflow will automatically retry when quota is restored.\n\n"
                    f"{ADW_BOT_IDENTIFIER}",
                )
            except Exception as e:
                print(f"Failed to post quota error comment: {e}")
            return

        # Check if issue is already locked by another ADW (concurrency control)
        if not provided_adw_id:  # Only check lock for new workflows, not continuing ones
            # Use provided ADW ID or generate a new one
            adw_id = make_adw_id()

            # Try to acquire lock
            lock_acquired = acquire_lock(issue_number, adw_id)
            if not lock_acquired:
                print(f"❌ Issue #{issue_number} is already being processed by another ADW workflow")
                try:
                    make_issue_comment(
                        str(issue_number),
                        f"⚠️ **ADW Concurrency Conflict**\n\n"
                        f"Another ADW workflow is already processing this issue.\n\n"
                        f"Please wait for the existing workflow to complete before starting a new one.\n\n"
                        f"You can check active locks with the `/api/adw/locks` endpoint.\n\n"
                        f"{ADW_BOT_IDENTIFIER}",
                    )
                except Exception as e:
                    print(f"Failed to post lock conflict comment: {e}")
                return

            print(f"✅ Lock acquired for issue #{issue_number} by ADW {adw_id}")
        else:
            # Use provided ADW ID for continuing workflow
            adw_id = provided_adw_id

        # If ADW ID was provided, update/create state file
        if provided_adw_id:
            state = ADWState.load(provided_adw_id)
            if state:
                state.update(issue_number=str(issue_number), model_set=model_set)
            else:
                state = ADWState(provided_adw_id)
                state.update(
                    adw_id=provided_adw_id,
                    issue_number=str(issue_number),
                    model_set=model_set,
                )
            state.save("webhook_trigger")
        else:
            # Create new state for newly generated ADW ID
            state = ADWState(adw_id)
            state.update(
                adw_id=adw_id, issue_number=str(issue_number), model_set=model_set
            )
            state.save("webhook_trigger")

        # Set up logger
        logger = setup_logger(adw_id, "webhook_trigger")
        logger.info(
            f"Detected workflow: {workflow} from content: {content_to_check[:100]}..."
        )
        if provided_adw_id:
            logger.info(f"Using provided ADW ID: {provided_adw_id}")

        # Post comment to issue about detected workflow
        try:
            make_issue_comment(
                str(issue_number),
                f"🤖 ADW Webhook: Detected `{workflow}` workflow request\n\n"
                f"Starting workflow with ID: `{adw_id}`\n"
                f"Workflow: `{workflow}` 🏗️\n"
                f"Model Set: `{model_set}` ⚙️\n"
                f"Reason: {trigger_reason}\n\n"
                f"Logs will be available at: `agents/{adw_id}/{workflow}/`",
            )
        except Exception as e:
            logger.warning(f"Failed to post issue comment: {e}")

        # Build command to run the appropriate workflow
        script_dir = os.path.dirname(os.path.abspath(__file__))
        adws_dir = os.path.dirname(script_dir)
        repo_root = os.path.dirname(adws_dir)
        trigger_script = os.path.join(adws_dir, f"{workflow}.py")

        cmd = ["uv", "run", trigger_script, str(issue_number), adw_id]

        print(f"🚀 Launching {workflow} for issue #{issue_number}")
        print(f"Command: {' '.join(cmd)} (reason: {trigger_reason})")
        print(f"Working directory: {repo_root}")

        # Launch in background using Popen with filtered environment
        process = subprocess.Popen(
            cmd,
            cwd=repo_root,
            env=get_safe_subprocess_env(),
            start_new_session=True,
        )

        print(f"✅ Background process started for issue #{issue_number} with ADW ID: {adw_id}")
        print(f"Logs will be written to: agents/{adw_id}/{workflow}/execution.log")

    except Exception as e:
        print(f"❌ Error in background processing: {e}")
        import traceback
        traceback.print_exc()


@app.post("/gh-webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle GitHub webhook events - responds immediately and processes in background."""
    try:
        # Get event type from header
        event_type = request.headers.get("X-GitHub-Event", "")

        # Parse webhook payload
        payload = await request.json()

        # Extract event details
        action = payload.get("action", "")
        issue = payload.get("issue", {})
        issue_number = issue.get("number")

        print(
            f"✅ Received webhook: event={event_type}, action={action}, issue_number={issue_number}"
        )

        should_process = False
        content_to_check = ""
        trigger_source = ""

        # Check if this is an issue opened event
        if event_type == "issues" and action == "opened" and issue_number:
            issue_body = issue.get("body", "")
            content_to_check = issue_body

            # Ignore issues from ADW bot to prevent loops
            if ADW_BOT_IDENTIFIER in issue_body:
                print(f"⏭️  Ignoring ADW bot issue to prevent loop")
            # Check if body contains "adw_"
            elif "adw_" in issue_body.lower():
                should_process = True
                trigger_source = "New issue"

        # Check if this is an issue comment
        elif event_type == "issue_comment" and action == "created" and issue_number:
            comment = payload.get("comment", {})
            comment_body = comment.get("body", "")
            content_to_check = comment_body

            print(f"Comment body: '{comment_body[:100]}...'")

            # Ignore comments from ADW bot to prevent loops
            if ADW_BOT_IDENTIFIER in comment_body:
                print(f"⏭️  Ignoring ADW bot comment to prevent loop")
            # Check if comment contains "adw_"
            elif "adw_" in comment_body.lower():
                should_process = True
                trigger_source = "Comment"

        if should_process:
            # Add background task for processing
            background_tasks.add_task(
                process_webhook_background,
                event_type,
                action,
                issue_number,
                content_to_check,
                trigger_source
            )

            # Return immediately to GitHub (within 10 second timeout)
            return {
                "status": "accepted",
                "issue": issue_number,
                "message": f"Webhook received - processing {trigger_source.lower()} in background",
                "event": event_type,
                "action": action,
            }
        else:
            print(
                f"⏭️  Ignoring webhook: event={event_type}, action={action}, issue_number={issue_number}"
            )
            return {
                "status": "ignored",
                "reason": f"Not a triggering event (event={event_type}, action={action})",
            }

    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        import traceback
        traceback.print_exc()
        # Always return 200 to GitHub to prevent retries
        return {"status": "error", "message": "Internal error processing webhook"}


@app.get("/health")
async def health():
    """Health check endpoint - runs comprehensive system health check."""
    try:
        # Run the health check script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Health check is in adw_tests, not adw_triggers
        health_check_script = os.path.join(
            os.path.dirname(script_dir), "adw_tests", "health_check.py"
        )

        # Run health check with timeout
        result = subprocess.run(
            ["uv", "run", health_check_script],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(script_dir),  # Run from adws directory
        )

        # Print the health check output for debugging
        print("=== Health Check Output ===")
        print(result.stdout)
        if result.stderr:
            print("=== Health Check Errors ===")
            print(result.stderr)

        # Parse the output - look for the overall status
        output_lines = result.stdout.strip().split("\n")
        is_healthy = result.returncode == 0

        # Extract key information from output
        warnings = []
        errors = []

        capturing_warnings = False
        capturing_errors = False

        for line in output_lines:
            if "⚠️  Warnings:" in line:
                capturing_warnings = True
                capturing_errors = False
                continue
            elif "❌ Errors:" in line:
                capturing_errors = True
                capturing_warnings = False
                continue
            elif "📝 Next Steps:" in line:
                break

            if capturing_warnings and line.strip().startswith("-"):
                warnings.append(line.strip()[2:])
            elif capturing_errors and line.strip().startswith("-"):
                errors.append(line.strip()[2:])

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "service": "adw-webhook-trigger",
            "health_check": {
                "success": is_healthy,
                "warnings": warnings,
                "errors": errors,
                "details": "Run health_check.py directly for full report",
            },
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "unhealthy",
            "service": "adw-webhook-trigger",
            "error": "Health check timed out",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "adw-webhook-trigger",
            "error": f"Health check failed: {str(e)}",
        }


if __name__ == "__main__":
    print(f"Starting server on http://0.0.0.0:{PORT}")
    print(f"Webhook endpoint: POST /gh-webhook")
    print(f"Health check: GET /health")

    uvicorn.run(app, host="0.0.0.0", port=PORT)
