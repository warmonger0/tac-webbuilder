"""
GitHub Issue Service

Handles GitHub issue creation workflow:
- Processing natural language requests
- Generating GitHub issue previews with cost estimates
- Posting confirmed issues to GitHub
- Managing pending request state
"""

import logging
import os
import sys
import traceback
import uuid
from datetime import datetime

import httpx
from fastapi import HTTPException

# Import ADW complexity analyzer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'adws'))
from adw_modules.complexity_analyzer import analyze_issue_complexity
from adw_modules.data_types import GitHubIssue as ADWGitHubIssue
from core.cost_estimate_storage import save_cost_estimate
from core.data_models import (
    ConfirmResponse,
    CostEstimate,
    GitHubIssue,
    ProjectContext,
    SubmitRequestData,
    SubmitRequestResponse,
)
from core.github_poster import GitHubPoster
from core.nl_processor import process_request
from core.project_detector import detect_project_context

logger = logging.getLogger(__name__)


class GitHubIssueService:
    """
    Service for managing GitHub issue creation workflow.

    Handles the complete workflow from natural language input to GitHub issue creation:
    1. Process NL request → Generate issue preview + cost estimate
    2. Store pending request with cost data
    3. Allow preview retrieval
    4. Confirm and post to GitHub
    5. Save cost estimate for workflow tracking
    """

    def __init__(
        self,
        webhook_trigger_url: str | None = None,
        github_repo: str | None = None
    ):
        """
        Initialize GitHub Issue Service.

        Args:
            webhook_trigger_url: URL of ADW webhook trigger service (default: http://localhost:8001)
            github_repo: GitHub repository in format "owner/repo" (default: from env)
        """
        self.webhook_trigger_url = webhook_trigger_url or os.environ.get("WEBHOOK_TRIGGER_URL", "http://localhost:8001")
        self.github_repo = github_repo or os.environ.get("GITHUB_REPO", "warmonger0/tac-webbuilder")
        self.pending_requests: dict[str, dict] = {}

        logger.info(f"[INIT] GitHubIssueService initialized (webhook: {self.webhook_trigger_url}, repo: {self.github_repo})")

    async def submit_nl_request(self, request: SubmitRequestData) -> SubmitRequestResponse:
        """
        Process natural language request and generate GitHub issue preview WITH cost estimate.

        Args:
            request: Natural language request data with optional project path

        Returns:
            SubmitRequestResponse with unique request ID for preview/confirm

        Raises:
            HTTPException: If request processing fails
        """
        try:
            logger.info(f"[INFO] Processing NL request: {request.nl_input[:100]}...")

            # Detect project context
            if request.project_path:
                project_context = detect_project_context(request.project_path)
            else:
                # Default context if no project path provided
                project_context = ProjectContext(
                    path=os.getcwd(),
                    is_new_project=False,
                    complexity="medium",
                    has_git=True
                )

            # Process the request to generate GitHub issue
            github_issue = await process_request(request.nl_input, project_context)

            # 🆕 ADD COST ESTIMATION
            # Create ADW-compatible issue object for complexity analysis
            # ADW GitHubIssue expects: number, title, body, user (str), labels (List[GitHubLabel])
            # We'll use a simplified structure since we're just analyzing, not creating a real issue
            adw_issue = ADWGitHubIssue(
                number=0,  # Placeholder - not created yet
                title=github_issue.title,
                body=github_issue.body,
                state="open",
                author={"login": "user", "avatar_url": "", "url": ""},  # Placeholder user
                assignees=[],
                labels=[],  # Convert string labels to ADW format if needed
                milestone=None,
                comments=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                closed_at=None,
                url=""
            )

            # Analyze complexity and get cost estimate
            # Pass classification as issue_class (e.g., "/feature", "/bug", "/chore")
            issue_class = f"/{github_issue.classification}"
            cost_analysis = analyze_issue_complexity(adw_issue, issue_class)

            # Generate unique request ID
            request_id = str(uuid.uuid4())

            # Store in pending requests WITH cost estimate
            self.pending_requests[request_id] = {
                'issue': github_issue,
                'project_context': project_context,
                'cost_estimate': {  # 🆕 NEW FIELD
                    'level': cost_analysis.level,
                    'min_cost': cost_analysis.estimated_cost_range[0],
                    'max_cost': cost_analysis.estimated_cost_range[1],
                    'total': cost_analysis.estimated_cost_total,
                    'breakdown': cost_analysis.cost_breakdown_estimate,
                    'confidence': cost_analysis.confidence,
                    'reasoning': cost_analysis.reasoning,
                    'recommended_workflow': cost_analysis.recommended_workflow
                }
            }

            logger.info(
                f"[SUCCESS] Request processed with cost estimate: {cost_analysis.level} "
                f"(${cost_analysis.estimated_cost_range[0]:.2f}-${cost_analysis.estimated_cost_range[1]:.2f})"
            )
            return SubmitRequestResponse(request_id=request_id)

        except Exception as e:
            logger.error(f"[ERROR] Failed to process NL request: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            raise HTTPException(500, f"Error processing request: {str(e)}") from e

    async def get_issue_preview(self, request_id: str) -> GitHubIssue:
        """
        Get the GitHub issue preview for a pending request.

        Args:
            request_id: Unique ID from submit_nl_request

        Returns:
            GitHubIssue preview object

        Raises:
            HTTPException: If request_id not found
        """
        try:
            if request_id not in self.pending_requests:
                raise HTTPException(404, f"Request ID '{request_id}' not found")

            issue = self.pending_requests[request_id]['issue']
            logger.info(f"[SUCCESS] Retrieved preview for request: {request_id}")
            return issue

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ERROR] Failed to get preview: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            raise HTTPException(500, f"Error retrieving preview: {str(e)}") from e

    async def get_cost_estimate(self, request_id: str) -> CostEstimate:
        """
        Get cost estimate for a pending request.

        Args:
            request_id: Unique ID from submit_nl_request

        Returns:
            CostEstimate object with level, costs, breakdown, reasoning

        Raises:
            HTTPException: If request_id not found or no cost estimate available
        """
        try:
            if request_id not in self.pending_requests:
                raise HTTPException(404, f"Request ID '{request_id}' not found")

            cost_estimate = self.pending_requests[request_id].get('cost_estimate')
            if not cost_estimate:
                raise HTTPException(404, "No cost estimate available for this request")

            logger.info(f"[SUCCESS] Retrieved cost estimate for request: {request_id}")
            return CostEstimate(**cost_estimate)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ERROR] Failed to get cost estimate: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            raise HTTPException(500, f"Error retrieving cost estimate: {str(e)}") from e

    async def check_webhook_trigger_health(self) -> dict:
        """
        Check if the ADW webhook trigger service is online and healthy.

        Returns:
            dict: Health status from webhook trigger service

        Raises:
            HTTPException: If webhook trigger is offline or unhealthy
        """
        health_endpoint = f"{self.webhook_trigger_url}/health"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(health_endpoint)
                response.raise_for_status()
                health_data = response.json()

                # Check if service reports healthy status
                if health_data.get("status") != "healthy":
                    errors = health_data.get("health_check", {}).get("errors", [])
                    error_msg = ", ".join(errors) if errors else "Service reported unhealthy status"
                    raise HTTPException(
                        503,
                        f"ADW webhook trigger is unhealthy: {error_msg}. "
                        f"Please start the trigger service: cd adws && uv run adw_triggers/trigger_webhook.py"
                    )

                return health_data

        except httpx.TimeoutException as e:
            logger.error(f"[ERROR] Webhook trigger health check timed out at {health_endpoint}")
            raise HTTPException(
                503,
                "ADW webhook trigger is not responding (timeout). "
                "Please start the trigger service: cd adws && uv run adw_triggers/trigger_webhook.py"
            ) from e
        except httpx.ConnectError as e:
            logger.error(f"[ERROR] Cannot connect to webhook trigger at {health_endpoint}")
            raise HTTPException(
                503,
                "ADW webhook trigger is offline. "
                "Please start the trigger service: cd adws && uv run adw_triggers/trigger_webhook.py"
            ) from e
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ERROR] Unexpected error checking webhook trigger health: {str(e)}")
            raise HTTPException(
                503,
                f"Failed to verify ADW webhook trigger status: {str(e)}"
            ) from e

    async def confirm_and_post_issue(self, request_id: str) -> ConfirmResponse:
        """
        Confirm and post the GitHub issue.

        Workflow:
        1. Pre-flight check: Verify webhook trigger is online
        2. Retrieve pending request and cost estimate
        3. Post issue to GitHub
        4. Save cost estimate for workflow tracking
        5. Clean up pending request

        Args:
            request_id: Unique ID from submit_nl_request

        Returns:
            ConfirmResponse with issue number and GitHub URL

        Raises:
            HTTPException: If webhook offline, request_id not found, or posting fails
        """
        try:
            # Pre-flight check: Ensure webhook trigger is online
            await self.check_webhook_trigger_health()
            logger.info("[SUCCESS] Webhook trigger health check passed")

            if request_id not in self.pending_requests:
                raise HTTPException(404, f"Request ID '{request_id}' not found")

            # Get the issue and cost estimate from pending requests
            issue = self.pending_requests[request_id]['issue']
            cost_estimate = self.pending_requests[request_id].get('cost_estimate', {})

            # Post to GitHub
            github_poster = GitHubPoster()
            issue_number = github_poster.post_issue(issue, confirm=False)

            # Save cost estimate for later retrieval during workflow sync
            if cost_estimate:
                save_cost_estimate(
                    issue_number=issue_number,
                    estimated_cost_total=cost_estimate.get('total', (cost_estimate['min_cost'] + cost_estimate['max_cost']) / 2.0),
                    estimated_cost_breakdown=cost_estimate.get('breakdown', {}),
                    level=cost_estimate['level'],
                    confidence=cost_estimate['confidence'],
                    reasoning=cost_estimate['reasoning'],
                    recommended_workflow=cost_estimate['recommended_workflow']
                )
                logger.info(f"[SUCCESS] Saved cost estimate for issue #{issue_number}: ${cost_estimate.get('total', 0):.2f}")

            # Get GitHub URL
            github_url = f"https://github.com/{self.github_repo}/issues/{issue_number}"

            # Clean up pending request
            del self.pending_requests[request_id]

            logger.info(f"[SUCCESS] Posted issue #{issue_number}: {github_url}")
            return ConfirmResponse(issue_number=issue_number, github_url=github_url)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ERROR] Failed to post issue: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            raise HTTPException(500, f"Error posting issue: {str(e)}") from e
