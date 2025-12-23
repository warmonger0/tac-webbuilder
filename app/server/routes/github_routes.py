"""
GitHub integration endpoints for issue creation and preview.
"""
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from core.data_models import (
    ConfirmResponse,
    CostEstimate,
    GitHubIssue,
    SubmitRequestData,
    SubmitRequestResponse,
)
from core.models import PlannedFeatureUpdate
from fastapi import APIRouter, Request, Response
from services.planned_features_service import PlannedFeaturesService
from services.websocket_manager import get_connection_manager
from utils.webhook_security import validate_webhook_request

logger = logging.getLogger(__name__)

# Router will be created with dependencies injected from server.py
router = APIRouter(prefix="", tags=["GitHub Integration"])


def init_github_routes(github_issue_service):
    """
    Initialize GitHub routes with service dependencies.

    This function is called from server.py to inject service dependencies.
    """

    async def _broadcast_planned_features_update():
        """Broadcast planned features update to all WebSocket clients"""
        try:
            manager = get_connection_manager()
            service = PlannedFeaturesService()

            features = service.get_all(limit=200)
            stats = service.get_statistics()

            # Broadcast update
            await manager.broadcast({
                "type": "planned_features_update",
                "data": {
                    "features": [f.model_dump() for f in features],
                    "stats": stats
                }
            })
            logger.info("[WEBHOOK] Broadcasted planned features update to WebSocket clients")
        except Exception as e:
            logger.error(f"[WEBHOOK] Failed to broadcast planned features update: {e}")

    @router.post("/webhooks/github")
    async def handle_github_webhook(request: Request) -> Response:
        """
        Handle GitHub webhook events and sync to planned_features.

        Supports:
        - issues (opened, closed, reopened, labeled, unlabeled)
        - issue_comment (for tracking activity)

        Syncs GitHub issue state to planned_features table and broadcasts
        WebSocket updates for real-time UI refresh.
        """
        try:
            # Validate webhook signature for security
            body = await validate_webhook_request(request)
            payload = json.loads(body)

            event_type = request.headers.get("X-GitHub-Event", "unknown")
            logger.info(f"[WEBHOOK] Received GitHub webhook: {event_type}")

            # Handle issue events
            if event_type == "issues":
                action = payload.get("action", "unknown")
                issue = payload.get("issue", {})
                issue_number = issue.get("number")

                if not issue_number:
                    logger.warning("[WEBHOOK] Issue webhook missing issue number")
                    return Response(status_code=200, content="OK (no issue number)")

                logger.info(f"[WEBHOOK] Processing issue #{issue_number} action: {action}")

                # Find planned feature with this GitHub issue number
                service = PlannedFeaturesService()
                features = service.get_all(limit=500)
                feature = next((f for f in features if f.github_issue_number == issue_number), None)

                if not feature:
                    logger.info(f"[WEBHOOK] No planned feature found for issue #{issue_number}")
                    return Response(status_code=200, content="OK (not linked)")

                # Sync GitHub issue state to planned feature
                updates = {}
                needs_update = False

                # Sync status based on issue state
                if action == "closed":
                    if feature.status != "completed":
                        updates["status"] = "completed"
                        updates["completed_at"] = datetime.now(UTC).isoformat()
                        needs_update = True
                        logger.info(f"[WEBHOOK] Marking feature {feature.id} as completed (issue #{issue_number} closed)")

                        # CRITICAL: Update workflow state files to mark as completed
                        # This prevents adw_monitor from showing closed issues as "paused"
                        agents_dir = Path("agents")
                        if agents_dir.exists():
                            for agent_dir in agents_dir.iterdir():
                                if agent_dir.is_dir():
                                    state_file = agent_dir / "adw_state.json"
                                    if state_file.exists():
                                        try:
                                            state_data = json.loads(state_file.read_text())
                                            if str(state_data.get("issue_number")) == str(issue_number):
                                                state_data["status"] = "completed"
                                                state_data["completed_at"] = datetime.now(UTC).isoformat()
                                                state_file.write_text(json.dumps(state_data, indent=2))
                                                logger.info(f"[WEBHOOK] Updated workflow state for {agent_dir.name}")
                                        except Exception as e:
                                            logger.warning(f"[WEBHOOK] Failed to update state file {state_file}: {e}")

                elif action == "reopened":
                    if feature.status == "completed":
                        updates["status"] = "in_progress"
                        updates["completed_at"] = None
                        needs_update = True
                        logger.info(f"[WEBHOOK] Marking feature {feature.id} as in_progress (issue #{issue_number} reopened)")

                elif action in ["labeled", "unlabeled"]:
                    # Sync labels to tags
                    labels = issue.get("labels", [])
                    new_tags = [label["name"] for label in labels if isinstance(label, dict) and "name" in label]

                    if set(new_tags) != set(feature.tags or []):
                        updates["tags"] = new_tags
                        needs_update = True
                        logger.info(f"[WEBHOOK] Updating tags for feature {feature.id}: {new_tags}")

                # Update the feature if changes detected
                if needs_update and updates:
                    service.update(feature.id, PlannedFeatureUpdate(**updates))
                    logger.info(f"[WEBHOOK] Updated planned feature {feature.id} from issue #{issue_number}")

                    # Broadcast WebSocket update for real-time UI refresh
                    await _broadcast_planned_features_update()

                    return Response(
                        status_code=200,
                        content=f"OK (updated feature {feature.id})"
                    )
                else:
                    logger.info(f"[WEBHOOK] No updates needed for feature {feature.id}")
                    return Response(status_code=200, content="OK (no changes)")

            # Handle other event types (future expansion)
            elif event_type == "issue_comment":
                # Future: Track activity timestamps
                logger.info("[WEBHOOK] Received issue_comment event (not processed)")
                return Response(status_code=200, content="OK (comment ignored)")

            else:
                logger.info(f"[WEBHOOK] Unhandled event type: {event_type}")
                return Response(status_code=200, content="OK (unhandled event)")

        except Exception as e:
            logger.error(f"[WEBHOOK] Error processing GitHub webhook: {e}", exc_info=True)
            # Return 200 to prevent GitHub from retrying
            return Response(status_code=200, content="OK (error logged)")

    @router.post("/request", response_model=SubmitRequestResponse)
    async def submit_nl_request(request: SubmitRequestData) -> SubmitRequestResponse:
        """Process natural language request and generate GitHub issue preview WITH cost estimate - delegates to GitHubIssueService"""
        return await github_issue_service.submit_nl_request(request)

    @router.get("/preview/{request_id}", response_model=GitHubIssue)
    async def get_issue_preview(request_id: str) -> GitHubIssue:
        """Get the GitHub issue preview for a pending request - delegates to GitHubIssueService"""
        return await github_issue_service.get_issue_preview(request_id)

    @router.get("/preview/{request_id}/cost", response_model=CostEstimate)
    async def get_cost_estimate(request_id: str) -> CostEstimate:
        """Get cost estimate for a pending request - delegates to GitHubIssueService"""
        return await github_issue_service.get_cost_estimate(request_id)

    @router.post("/confirm/{request_id}", response_model=ConfirmResponse)
    async def confirm_and_post_issue(request_id: str) -> ConfirmResponse:
        """Confirm and post the GitHub issue - delegates to GitHubIssueService"""
        return await github_issue_service.confirm_and_post_issue(request_id)
