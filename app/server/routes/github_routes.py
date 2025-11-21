"""
GitHub integration endpoints for issue creation and preview.
"""
import logging

from core.data_models import (
    ConfirmResponse,
    CostEstimate,
    GitHubIssue,
    SubmitRequestData,
    SubmitRequestResponse,
)
from fastapi import APIRouter

logger = logging.getLogger(__name__)

# Router will be created with dependencies injected from server.py
router = APIRouter(prefix="", tags=["GitHub Integration"])


def init_github_routes(github_issue_service):
    """
    Initialize GitHub routes with service dependencies.

    This function is called from server.py to inject service dependencies.
    """

    @router.post("/api/request", response_model=SubmitRequestResponse)
    async def submit_nl_request(request: SubmitRequestData) -> SubmitRequestResponse:
        """Process natural language request and generate GitHub issue preview WITH cost estimate - delegates to GitHubIssueService"""
        return await github_issue_service.submit_nl_request(request)

    @router.get("/api/preview/{request_id}", response_model=GitHubIssue)
    async def get_issue_preview(request_id: str) -> GitHubIssue:
        """Get the GitHub issue preview for a pending request - delegates to GitHubIssueService"""
        return await github_issue_service.get_issue_preview(request_id)

    @router.get("/api/preview/{request_id}/cost", response_model=CostEstimate)
    async def get_cost_estimate(request_id: str) -> CostEstimate:
        """Get cost estimate for a pending request - delegates to GitHubIssueService"""
        return await github_issue_service.get_cost_estimate(request_id)

    @router.post("/api/confirm/{request_id}", response_model=ConfirmResponse)
    async def confirm_and_post_issue(request_id: str) -> ConfirmResponse:
        """Confirm and post the GitHub issue - delegates to GitHubIssueService"""
        return await github_issue_service.confirm_and_post_issue(request_id)
