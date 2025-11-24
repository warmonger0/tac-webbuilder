"""
MultiPhaseIssueHandler

Handles multi-phase GitHub issue creation and phase queueing.
Separates multi-phase workflow logic from the main GitHub issue service.
"""

import logging
import uuid
from typing import List

from fastapi import HTTPException

from core.data_models import (
    GitHubIssue,
    SubmitRequestData,
    SubmitRequestResponse,
    ChildIssueInfo
)
from core.github_poster import GitHubPoster

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
        Handle multi-phase request by creating parent issue, child issues, and enqueueing phases.

        Workflow:
        1. Create parent GitHub issue with overview of all phases
        2. Create child issues for each phase
        3. Enqueue phases with dependency tracking
        4. Link issues via references in issue bodies

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
            # 1. Create parent issue
            parent_issue_number = await self._create_parent_issue(request)
            logger.info(f"[SUCCESS] Created parent issue #{parent_issue_number}")

            # 2. Create child issues and enqueue phases
            child_issues = await self._create_child_issues_and_enqueue(request, parent_issue_number)

            # 3. Generate unique request ID (for consistency with single-phase flow)
            request_id = str(uuid.uuid4())

            logger.info(
                f"[SUCCESS] Multi-phase request complete: "
                f"parent #{parent_issue_number}, {len(child_issues)} child issues created"
            )

            return SubmitRequestResponse(
                request_id=request_id,
                is_multi_phase=True,
                parent_issue_number=parent_issue_number,
                child_issues=child_issues
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ERROR] Failed to handle multi-phase request: {str(e)}")
            raise HTTPException(500, f"Error processing multi-phase request: {str(e)}")

    async def _create_parent_issue(self, request: SubmitRequestData) -> int:
        """
        Create parent GitHub issue with overview of all phases.

        Args:
            request: SubmitRequestData with phases

        Returns:
            Parent issue number

        Raises:
            Exception: If GitHub posting fails
        """
        parent_title = f"[Multi-Phase] {request.phases[0].title}"
        parent_body = f"""# Multi-Phase Request

This is a multi-phase request with {len(request.phases)} phases that will be executed sequentially.

## Overview

{request.nl_input}

## Phases

"""
        for phase in request.phases:
            parent_body += f"""
### Phase {phase.number}: {phase.title}

{phase.content[:200]}...

"""
            if phase.externalDocs:
                parent_body += f"**Referenced Documents:** {', '.join(phase.externalDocs)}\n\n"

        # Create parent issue
        parent_issue = GitHubIssue(
            title=parent_title,
            body=parent_body,
            labels=["multi-phase"],
            classification="feature",  # Default to feature for multi-phase
            workflow="adw_sdlc_iso",
            model_set="base"
        )
        parent_issue_number = self.github_poster.post_issue(parent_issue, confirm=False)
        return parent_issue_number

    async def _create_child_issues_and_enqueue(
        self,
        request: SubmitRequestData,
        parent_issue_number: int
    ) -> List[ChildIssueInfo]:
        """
        Create child issues for each phase and enqueue them.

        JUST-IN-TIME STRATEGY:
        - Phase 1: Create issue immediately (ready to execute)
        - Phase 2+: Enqueue WITHOUT issue number (created when phase becomes ready)

        Args:
            request: SubmitRequestData with phases
            parent_issue_number: Parent issue number for reference

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
                parent_issue=parent_issue_number,
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
                child_issue_number = await self._create_child_issue(
                    phase,
                    parent_issue_number,
                    len(request.phases)
                )
                logger.info(f"[SUCCESS] Created child issue #{child_issue_number} for Phase {phase.number}")

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

    async def _create_child_issue(
        self,
        phase,
        parent_issue_number: int,
        total_phases: int
    ) -> int:
        """
        Create a single child issue for a phase.

        Args:
            phase: Phase object with title, content, externalDocs
            parent_issue_number: Parent issue number for reference
            total_phases: Total number of phases

        Returns:
            Child issue number

        Raises:
            Exception: If GitHub posting fails
        """
        child_title = f"Phase {phase.number}: {phase.title}"
        child_body = f"""# Phase {phase.number} of {total_phases}

**Parent Issue:** #{parent_issue_number}
**Execution Order:** {"Executes first" if phase.number == 1 else f"After Phase {phase.number - 1}"}

## Description

{phase.content}

"""
        if phase.externalDocs:
            child_body += f"""
## Referenced Documents

{chr(10).join(f'- `{doc}`' for doc in phase.externalDocs)}

"""

        child_body += f"""
---

**Full Context:** See parent issue #{parent_issue_number} for complete multi-phase request context.
"""

        child_issue = GitHubIssue(
            title=child_title,
            body=child_body,
            labels=[f"phase-{phase.number}", "multi-phase-child"],
            classification="feature",
            workflow="adw_sdlc_iso",
            model_set="base"
        )
        child_issue_number = self.github_poster.post_issue(child_issue, confirm=False)
        return child_issue_number
