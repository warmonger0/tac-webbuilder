"""
PhaseCoordinator Service - Backwards Compatibility Wrapper

This module re-exports PhaseCoordinator from the new modular structure
for backwards compatibility.

The service has been refactored into focused modules:
- phase_coordination/phase_coordinator.py: Main coordination logic
- phase_coordination/workflow_completion_detector.py: Status detection
- phase_coordination/phase_github_notifier.py: GitHub notifications

For new code, prefer importing from the package:
    from services.phase_coordination import PhaseCoordinator
"""

from services.phase_coordination import (
    PhaseCoordinator,
    PhaseGitHubNotifier,
    WorkflowCompletionDetector,
)

__all__ = [
    "PhaseCoordinator",
    "PhaseGitHubNotifier",
    "WorkflowCompletionDetector",
]
