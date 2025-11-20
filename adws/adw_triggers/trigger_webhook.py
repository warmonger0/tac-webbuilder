#!/usr/bin/env -S uv run
# /// script
# dependencies = ["fastapi", "uvicorn", "python-dotenv", "anthropic", "pydantic"]
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
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Optional, Dict, List
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

# Global stats tracking
webhook_stats = {
    "start_time": time.time(),
    "total_received": 0,
    "successful": 0,
    "failed": 0,
    "recent_failures": [],
    "last_successful": None,
}

print(f"Starting ADW Webhook Trigger on port {PORT}")


def count_active_worktrees() -> int:
    """Count number of active worktrees in trees/ directory."""
    try:
        trees_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "trees"
        )
        if os.path.exists(trees_dir):
            return len([d for d in os.listdir(trees_dir) if os.path.isdir(os.path.join(trees_dir, d))])
        return 0
    except Exception:
        return 0


def get_disk_usage() -> float:
    """Get disk usage percentage (0.0 to 1.0)."""
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        return used / total
    except Exception:
        return 0.0


def can_launch_workflow(workflow: str, issue_number: int, provided_adw_id: Optional[str]) -> tuple[bool, Optional[str]]:
    """Comprehensive pre-flight check before launching workflow.

    Returns:
        (can_launch, error_message)
    """
    # 1. Check API quota
    log_quota_warning()
    can_proceed, quota_error = can_start_adw()
    if not can_proceed:
        return False, f"API quota unavailable: {quota_error}"

    # 2. Check concurrency locks (only for new workflows)
    if not provided_adw_id:
        # This check is done in the main flow, so we skip here
        pass

    # 3. Check disk space
    disk_usage = get_disk_usage()
    if disk_usage > 0.95:
        return False, f"Disk space critical (>95% used: {disk_usage*100:.1f}%)"

    # 4. Check worktree availability
    worktree_count = count_active_worktrees()
    if worktree_count >= 15:
        return False, f"Max worktrees reached ({worktree_count}/15)"

    # 5. Validate workflow exists
    if workflow not in AVAILABLE_ADW_WORKFLOWS:
        return False, f"Unknown workflow: {workflow}"

    return True, None


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
    # Set up logger for error tracking
    error_logger = setup_logger("webhook_error", "webhook_trigger")

    try:
        print(f"🔄 Background processing: {trigger_source} for issue #{issue_number}")
        error_logger.info(f"Processing {trigger_source} for issue #{issue_number}")

        # Use temporary ID for classification
        temp_id = make_adw_id()

        # Extract workflow info with timeout
        try:
            extraction_result = extract_adw_info_with_timeout(content_to_check, temp_id)
        except Exception as e:
            error_msg = f"Workflow extraction failed: {str(e)}"
            print(f"❌ {error_msg}")
            error_logger.error(f"{error_msg} for issue #{issue_number}")
            import traceback
            error_logger.error(f"Traceback:\n{traceback.format_exc()}")

            # Notify user on GitHub
            try:
                make_issue_comment(
                    str(issue_number),
                    f"⚠️ **Workflow Detection Failed**\n\n"
                    f"Error: `{str(e)[:200]}`\n\n"
                    f"To manually trigger, add a comment with:\n"
                    f"`adw_plan_iso` or another workflow command\n\n"
                    f"**Available workflows:**\n"
                    f"- `adw_plan_iso` - Plan implementation\n"
                    f"- `adw_lightweight_iso` - Quick fixes ($0.20-0.50)\n"
                    f"- `adw_patch_iso` - Apply specific changes\n\n"
                    f"{ADW_BOT_IDENTIFIER}",
                )
            except Exception as comment_error:
                error_logger.error(f"Failed to post error comment: {comment_error}")
            return

        if not extraction_result or not extraction_result.has_workflow:
            print(f"⚠️ No workflow detected in {trigger_source} for issue #{issue_number}")
            error_logger.info(f"No workflow detected for issue #{issue_number}")

            # If content contains "adw_" but couldn't parse, help the user
            if "adw_" in content_to_check.lower():
                error_logger.warning(f"Found 'adw_' in content but couldn't parse workflow for issue #{issue_number}")
                try:
                    make_issue_comment(
                        str(issue_number),
                        f"⚠️ **Could Not Parse Workflow Command**\n\n"
                        f"I detected 'adw_' in your message but couldn't identify the workflow.\n\n"
                        f"**Available workflows:**\n"
                        f"- `adw_plan_iso` - Plan implementation with base model\n"
                        f"- `adw_plan_iso with advanced model` - Use advanced model set\n"
                        f"- `adw_lightweight_iso` - Quick fixes ($0.20-0.50)\n"
                        f"- `adw_patch_iso` - Apply specific changes\n"
                        f"- `adw_build_iso adw-12345678` - Build (requires ADW ID)\n"
                        f"- `adw_test_iso adw-12345678` - Test (requires ADW ID)\n"
                        f"- `adw_ship_iso adw-12345678` - Ship to main (requires ADW ID)\n\n"
                        f"**Example usage:**\n"
                        f"`adw_plan_iso with base model`\n\n"
                        f"{ADW_BOT_IDENTIFIER}",
                    )
                except Exception as comment_error:
                    error_logger.error(f"Failed to post help comment: {comment_error}")
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

        # Run comprehensive pre-flight checks
        can_proceed, preflight_error = can_launch_workflow(workflow, issue_number, provided_adw_id)
        if not can_proceed:
            print(f"❌ Pre-flight check failed: {preflight_error}")
            error_logger.warning(f"Pre-flight check failed for issue #{issue_number}: {preflight_error}")
            try:
                make_issue_comment(
                    str(issue_number),
                    f"❌ **Cannot Start ADW Workflow**\n\n"
                    f"{preflight_error}\n\n"
                    f"**System Status:**\n"
                    f"- Active worktrees: {count_active_worktrees()}/15\n"
                    f"- Disk usage: {get_disk_usage()*100:.1f}%\n\n"
                    f"The workflow will automatically retry when resources are available.\n\n"
                    f"{ADW_BOT_IDENTIFIER}",
                )
            except Exception as e:
                print(f"Failed to post preflight error comment: {e}")
                error_logger.error(f"Failed to post preflight error comment: {e}")
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
        error_logger.info(f"Successfully launched {workflow} for issue #{issue_number} with ADW ID {adw_id}")

        # Track success
        webhook_stats["successful"] += 1
        webhook_stats["last_successful"] = {
            "issue": issue_number,
            "adw_id": adw_id,
            "workflow": workflow,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        error_msg = f"Error in background processing: {e}"
        print(f"❌ {error_msg}")
        import traceback
        tb = traceback.format_exc()
        print(tb)

        # Log to file with full context
        error_logger.error(f"Webhook processing failed for issue #{issue_number}")
        error_logger.error(f"Error: {e}")
        error_logger.error(f"Traceback:\n{tb}")

        # Track failure
        webhook_stats["failed"] += 1
        failure_record = {
            "issue": issue_number,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)[:200],
        }
        webhook_stats["recent_failures"].append(failure_record)
        # Keep only last 10 failures
        if len(webhook_stats["recent_failures"]) > 10:
            webhook_stats["recent_failures"] = webhook_stats["recent_failures"][-10:]

        # Post detailed error to GitHub issue
        try:
            make_issue_comment(
                str(issue_number),
                f"❌ **ADW Webhook Processing Failed**\n\n"
                f"Error: `{str(e)[:200]}`\n\n"
                f"The webhook received your request but failed during processing.\n\n"
                f"**Next Steps:**\n"
                f"1. Check webhook logs in `agents/webhook_error/webhook_trigger/`\n"
                f"2. Run health check: `cd adws && uv run adw_tests/health_check.py`\n"
                f"3. Manually trigger: `cd adws && uv run adw_plan_iso.py {issue_number}`\n\n"
                f"**Common Issues:**\n"
                f"- API quota exhausted (wait for reset)\n"
                f"- Invalid workflow command (check spelling)\n"
                f"- System resources unavailable\n\n"
                f"{ADW_BOT_IDENTIFIER}",
            )
        except Exception as comment_error:
            error_logger.error(f"Failed to post error comment: {comment_error}")


@app.post("/gh-webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle GitHub webhook events - responds immediately and processes in background."""
    try:
        # Get event type from header
        event_type = request.headers.get("X-GitHub-Event", "")

        # Parse webhook payload
        # GitHub can send either JSON or form-urlencoded
        content_type = request.headers.get("content-type", "")

        try:
            if "application/json" in content_type:
                payload = await request.json()
            elif "application/x-www-form-urlencoded" in content_type:
                # GitHub webhooks configured with form encoding send payload=<json>
                import json as json_module
                import urllib.parse
                form_data = await request.body()
                decoded = urllib.parse.unquote(form_data.decode())
                # Remove "payload=" prefix if present
                if decoded.startswith("payload="):
                    decoded = decoded[8:]
                payload = json_module.loads(decoded)
            else:
                # Try JSON as default
                payload = await request.json()
        except Exception as json_error:
            # GitHub sometimes sends ping events with empty body
            print(f"⚠️ Failed to parse payload: {json_error}")
            print(f"Content-Type: {content_type}")
            print(f"Headers: {dict(request.headers)}")
            body = await request.body()
            print(f"Raw body (first 200 chars): {body[:200]}")

            # If this is a ping event, return success
            if event_type == "ping":
                return {"status": "ok", "message": "Webhook ping received"}

            # Otherwise, this is an error
            return {"status": "error", "message": f"Invalid payload: {str(json_error)}"}

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
            # Check if body contains ADW workflow command (not just adw_modules, adw_triggers, etc.)
            # Only trigger on patterns like "adw_plan_iso", "adw_build_iso", etc.
            elif re.search(r'\badw_[a-z]+(?:_[a-z]+)*_iso\b', issue_body.lower()):
                should_process = True
                trigger_source = "New issue"

        # Check if this is an issue state change (closed/reopened)
        elif event_type == "issues" and action in ["closed", "reopened"] and issue_number:
            # Update workflow history database with new GitHub issue state
            print(f"📝 Issue #{issue_number} {action} - updating workflow history")
            try:
                # Import here to avoid circular dependency
                sys.path.insert(0, app_server_path)
                from core.workflow_history import update_workflow_history_by_issue

                # Update all workflows for this issue number
                new_state = "closed" if action == "closed" else "open"
                updated_count = update_workflow_history_by_issue(
                    issue_number=issue_number,
                    gh_issue_state=new_state
                )
                print(f"✅ Updated {updated_count} workflow(s) for issue #{issue_number} to state: {new_state}")
            except Exception as e:
                print(f"⚠️ Failed to update workflow history: {e}")

            return {
                "status": "ok",
                "message": f"Issue state updated to {action}"
            }

        # Check if this is an issue comment
        elif event_type == "issue_comment" and action == "created" and issue_number:
            comment = payload.get("comment", {})
            comment_body = comment.get("body", "")
            content_to_check = comment_body

            print(f"Comment body: '{comment_body[:100]}...'")

            # Ignore comments from ADW bot to prevent loops
            if ADW_BOT_IDENTIFIER in comment_body:
                print(f"⏭️  Ignoring ADW bot comment to prevent loop")
            # Check if comment contains ADW workflow command (not just adw_modules, adw_triggers, etc.)
            # Only trigger on patterns like "adw_plan_iso", "adw_build_iso", etc.
            elif re.search(r'\badw_[a-z]+(?:_[a-z]+)*_iso\b', comment_body.lower()):
                should_process = True
                trigger_source = "Comment"

        if should_process:
            # Track received webhook
            webhook_stats["total_received"] += 1

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


@app.get("/webhook-status")
async def webhook_status():
    """Get webhook processing status and statistics."""
    uptime_seconds = time.time() - webhook_stats["start_time"]
    uptime_hours = uptime_seconds / 3600

    # Calculate success rate
    total_processed = webhook_stats["successful"] + webhook_stats["failed"]
    success_rate = (
        (webhook_stats["successful"] / total_processed * 100)
        if total_processed > 0
        else 0
    )

    return {
        "status": "healthy" if webhook_stats["failed"] == 0 or success_rate > 80 else "degraded",
        "uptime": {
            "seconds": int(uptime_seconds),
            "hours": round(uptime_hours, 2),
            "human": f"{int(uptime_hours)}h {int((uptime_seconds % 3600) / 60)}m",
        },
        "stats": {
            "total_received": webhook_stats["total_received"],
            "successful": webhook_stats["successful"],
            "failed": webhook_stats["failed"],
            "success_rate": f"{success_rate:.1f}%",
        },
        "recent_failures": webhook_stats["recent_failures"][-5:],  # Last 5 failures
        "last_successful": webhook_stats["last_successful"],
    }


@app.get("/ping")
async def ping():
    """Fast health check endpoint - returns immediately."""
    return {
        "status": "healthy",
        "service": "adw-webhook-trigger",
        "timestamp": time.time()
    }


@app.get("/health")
async def health():
    """Comprehensive health check endpoint - runs full system health check (slow)."""
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
    print(f"Fast health check: GET /ping")
    print(f"Full health check: GET /health")

    uvicorn.run(app, host="0.0.0.0", port=PORT)
