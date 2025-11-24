"""
IssueLinkingService

Utility service for generating GitHub issue reference links.
Provides reusable methods for creating issue body text that includes references to related issues.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


class IssueLinkingService:
    """Handle GitHub issue reference linking via body text"""

    @staticmethod
    def format_parent_reference(parent_issue_number: int) -> str:
        """
        Format a parent issue reference for inclusion in child issue body.

        Args:
            parent_issue_number: Parent issue number

        Returns:
            Formatted markdown text with parent issue reference
        """
        return f"**Parent Issue:** #{parent_issue_number}"

    @staticmethod
    def format_child_references(child_issue_numbers: List[int]) -> str:
        """
        Format child issue references for inclusion in parent issue.

        Args:
            child_issue_numbers: List of child issue numbers

        Returns:
            Formatted markdown text with all child issue references
        """
        if not child_issue_numbers:
            return ""

        references = "\n".join(f"- #{num}" for num in child_issue_numbers)
        return f"""## Child Issues

{references}
"""

    @staticmethod
    def format_execution_order(phase_number: int, total_phases: int) -> str:
        """
        Format execution order information for a phase.

        Args:
            phase_number: Current phase number
            total_phases: Total number of phases

        Returns:
            Formatted execution order text
        """
        if phase_number == 1:
            return "**Execution Order:** Executes first"
        else:
            return f"**Execution Order:** After Phase {phase_number - 1}"

    @staticmethod
    def format_context_reference(parent_issue_number: int) -> str:
        """
        Format a context reference footer for child issues.

        Args:
            parent_issue_number: Parent issue number

        Returns:
            Formatted footer text
        """
        return f"""
---

**Full Context:** See parent issue #{parent_issue_number} for complete multi-phase request context.
"""
