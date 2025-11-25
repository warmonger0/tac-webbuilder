"""
MultiPhaseIssueHandler

Handles multi-phase GitHub issue creation and phase queueing.
Separates multi-phase workflow logic from the main GitHub issue service.
"""

import logging
import uuid

from core.data_models import ChildIssueInfo, GitHubIssue, SubmitRequestData, SubmitRequestResponse
from core.github_poster import GitHubPoster
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class MultiPhaseIssueHandler:
    """Handle multi-phase issue creation and queueing"""

    def __init__(self, github_poster: GitHubPoster, phase_queue_service):
        """
        Initialize handler.

        Args:
            github_poster: GitHubPoster instance for creating issues
            phase_queue_service: PhaseQueueService instance for enqueueing phases
        """
        self.github_poster = github_poster
        self.phase_queue_service = phase_queue_service

    async def handle_multi_phase_request(self, request: SubmitRequestData) -> SubmitRequestResponse:
        """
        Handle multi-phase request by creating sequential issues and enqueueing phases.

        Workflow:
        1. Create Phase 1 issue (ready to execute immediately)
        2. Enqueue Phase 2+ without issues (created just-in-time)
        3. Phase 1 issue includes workflow command to auto-trigger

        Args:
            request: SubmitRequestData with phases populated

        Returns:
            SubmitRequestResponse with multi-phase information

        Raises:
            HTTPException: If validation fails or GitHub posting fails
        """
        if not self.phase_queue_service:
            raise HTTPException(
                500,
                "Multi-phase requests not supported: PhaseQueueService not initialized"
            )

        if not request.phases or len(request.phases) < 2:
            raise HTTPException(
                400,
                "Multi-phase request must have at least 2 phases"
            )

        try:
            # Create Phase 1 issue and enqueue all phases
            child_issues = await self._create_phase_issues_and_enqueue(request)

            # Generate unique request ID (for consistency with single-phase flow)
            request_id = str(uuid.uuid4())

            logger.info(
                f"[SUCCESS] Multi-phase request complete: "
                f"Phase 1 issue #{child_issues[0].issue_number} created, {len(child_issues)-1} phases queued"
            )

            return SubmitRequestResponse(
                request_id=request_id,
                is_multi_phase=True,
                parent_issue_number=None,  # No parent issue in new flow
                child_issues=child_issues
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ERROR] Failed to handle multi-phase request: {str(e)}")
            raise HTTPException(500, f"Error processing multi-phase request: {str(e)}") from e

    async def _create_phase_issues_and_enqueue(
        self,
        request: SubmitRequestData
    ) -> list[ChildIssueInfo]:
        """
        Create Phase 1 issue and enqueue all phases.

        JUST-IN-TIME STRATEGY:
        - Phase 1: Create issue immediately with workflow command (auto-triggers)
        - Phase 2+: Enqueue WITHOUT issue number (created when phase becomes ready)

        Args:
            request: SubmitRequestData with phases

        Returns:
            List of ChildIssueInfo objects

        Raises:
            Exception: If GitHub posting or enqueueing fails
        """
        child_issues = []

        for phase in request.phases:
            depends_on_phase = phase.number - 1 if phase.number > 1 else None

            # Enqueue phase first (without issue number for Phase 2+)
            queue_id = self.phase_queue_service.enqueue(
                parent_issue=0,  # No parent issue in new flow
                phase_number=phase.number,
                phase_data={
                    "title": phase.title,
                    "content": phase.content,
                    "externalDocs": phase.externalDocs or [],
                    "total_phases": len(request.phases)  # Store for just-in-time creation
                },
                depends_on_phase=depends_on_phase
            )

            # Only create GitHub issue for Phase 1 (ready to execute immediately)
            child_issue_number = None
            if phase.number == 1:
                child_issue_number = await self._create_phase_issue(
                    phase,
                    len(request.phases)
                )
                logger.info(f"[SUCCESS] Created Phase 1 issue #{child_issue_number} with workflow command")

                # Update queue with issue number
                self.phase_queue_service.update_issue_number(queue_id, child_issue_number)
            else:
                logger.info(f"[QUEUED] Phase {phase.number} queued without issue (will be created just-in-time)")

            child_issues.append(ChildIssueInfo(
                phase_number=phase.number,
                issue_number=child_issue_number,  # None for Phase 2+
                queue_id=queue_id
            ))

        return child_issues

    async def _create_phase_issue(
        self,
        phase,
        total_phases: int
    ) -> int:
        """
        Create a single phase issue with workflow command.

        Args:
            phase: Phase object with title, content, externalDocs
            total_phases: Total number of phases

        Returns:
            Phase issue number

        Raises:
            Exception: If GitHub posting fails
        """
        phase_title = f"Phase {phase.number}: {phase.title}"
        phase_body = f"""# Phase {phase.number} of {total_phases}

**Execution Order:** {"Executes first" if phase.number == 1 else f"After Phase {phase.number - 1}"}

## Description

{phase.content}

"""
        if phase.externalDocs:
            phase_body += f"""
## Referenced Documents

{chr(10).join(f'- `{doc}`' for doc in phase.externalDocs)}

"""

        # Add workflow command to trigger ADW automatically
        phase_body += """
---

**Workflow:** adw_plan_iso with base model
"""

        phase_issue = GitHubIssue(
            title=phase_title,
            body=phase_body,
            labels=[f"phase-{phase.number}", "multi-phase"],
            classification="feature",
            workflow="adw_sdlc_iso",
            model_set="base"
        )
        phase_issue_number = self.github_poster.post_issue(phase_issue, confirm=False)
        return phase_issue_number
