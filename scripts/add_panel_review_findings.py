#!/usr/bin/env python3
"""
Add Panel Review Findings to Planned Features Database

This script adds all issues found during the comprehensive panel review
to the planned_features database for tracking in the Plans Panel.

Session: 17 - Panel Review and Bug Fixes
Date: 2025-12-08
"""

import sys
from pathlib import Path

# Add app/server to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "server"))

from core.models import PlannedFeatureCreate
from services.planned_features_service import PlannedFeaturesService


def add_panel_review_findings():
    """Add all panel review findings as planned features."""
    service = PlannedFeaturesService()

    findings = [
        # CRITICAL ISSUES (High Priority)
        {
            "item_type": "bug",
            "title": "Remove production console.log statements from WebSocket hooks",
            "description": (
                "30+ console.log statements in useReliableWebSocket.ts and useWebSocket.ts "
                "are flooding the browser console in production (50-100+ logs/minute). "
                "Should be removed or gated behind debug flag.\n\n"
                "Files:\n"
                "- app/client/src/hooks/useReliableWebSocket.ts (10 statements)\n"
                "- app/client/src/hooks/useWebSocket.ts (11 statements)\n"
                "- app/client/src/hooks/useReliablePolling.ts (5 statements)"
            ),
            "status": "planned",
            "priority": "high",
            "estimated_hours": 1.0,
            "tags": ["frontend", "console-logs", "websocket", "production-issue"],
        },
        {
            "item_type": "bug",
            "title": "Fix hardcoded GitHub URL in Plans Panel",
            "description": (
                "PlansPanel.tsx line 252 contains hardcoded 'user/repo' in GitHub URL, "
                "making all issue links non-functional. Should import and use "
                "apiConfig.github.getIssueUrl() from existing config."
            ),
            "status": "planned",
            "priority": "high",
            "estimated_hours": 0.25,
            "tags": ["frontend", "plans-panel", "github-integration", "bug"],
        },
        {
            "item_type": "bug",
            "title": "Fix N+1 query pattern in SimilarWorkflowsComparison",
            "description": (
                "SimilarWorkflowsComparison.tsx lines 36-45 makes N separate HTTP requests "
                "in a loop (N+1 pattern). Should use existing fetchWorkflowsBatch() API "
                "from workflowClient for single batch request.\n\n"
                "Impact: Poor performance with multiple similar workflows, network overhead."
            ),
            "status": "planned",
            "priority": "high",
            "estimated_hours": 0.5,
            "tags": ["frontend", "performance", "n-plus-one", "history-panel"],
        },
        {
            "item_type": "bug",
            "title": "Fix state bug in LogPanel tab switching",
            "description": (
                "LogPanel.tsx lines 150, 160, 170: Offset state not reset when switching tabs. "
                "If user paginates to page 3 in Work Logs then switches to Task Logs, "
                "Task Logs tries to show items at offset 100 (which may not exist).\n\n"
                "Fix: Add setOffset(0) when changing tabs."
            ),
            "status": "planned",
            "priority": "medium",
            "estimated_hours": 0.25,
            "tags": ["frontend", "log-panel", "state-management", "bug"],
        },
        # MEDIUM PRIORITY ISSUES
        {
            "item_type": "enhancement",
            "title": "Add mutation error handling to ReviewPanel",
            "description": (
                "ReviewPanel.tsx lines 40-69: approveMutation, rejectMutation, and "
                "commentMutation lack onError handlers. Users see no feedback when "
                "mutations fail. Should add error state and display to UI."
            ),
            "status": "planned",
            "priority": "medium",
            "estimated_hours": 0.5,
            "tags": ["frontend", "review-panel", "error-handling"],
        },
        {
            "item_type": "enhancement",
            "title": "Add mutation error handling to LogPanel",
            "description": (
                "LogPanel.tsx lines 57-72: createMutation and deleteMutation lack "
                "onError handlers. Should add error state and user feedback for failed operations."
            ),
            "status": "planned",
            "priority": "medium",
            "estimated_hours": 0.5,
            "tags": ["frontend", "log-panel", "error-handling"],
        },
        {
            "item_type": "enhancement",
            "title": "Add error handling for statistics query in PlansPanel",
            "description": (
                "PlansPanel.tsx lines 22-27: Statistics query doesn't destructure error "
                "or isLoading. If stats API fails, dashboard silently doesn't render. "
                "Should show error message or loading state."
            ),
            "status": "planned",
            "priority": "medium",
            "estimated_hours": 0.25,
            "tags": ["frontend", "plans-panel", "error-handling"],
        },
        {
            "item_type": "enhancement",
            "title": "Replace window.alert/confirm with proper UI modals",
            "description": (
                "Multiple components use browser native alert() and confirm() dialogs:\n\n"
                "ReviewPanel.tsx lines 73, 84, 87:\n"
                "- confirm('Approve pattern...')\n"
                "- alert('Reason is required')\n\n"
                "LogPanel.tsx lines 89, 418:\n"
                "- alert('Summary must be 280 characters or less')\n"
                "- confirm('Delete this entry?')\n\n"
                "PhaseQueueCard.tsx lines 71, 75:\n"
                "- alert() for success/error messages\n\n"
                "Should replace with toast notifications or modal components for better UX."
            ),
            "status": "planned",
            "priority": "medium",
            "estimated_hours": 2.0,
            "tags": ["frontend", "ux", "modals", "toast-notifications"],
        },
        {
            "item_type": "enhancement",
            "title": "Add refetchIntervalInBackground control to polling queries",
            "description": (
                "Multiple components poll data even when tab is hidden:\n\n"
                "- PlansPanel: 30s/60s intervals\n"
                "- HistoryView: 30s interval\n\n"
                "Should add refetchIntervalInBackground: false to TanStack Query config "
                "to stop polling when tab inactive, reducing unnecessary API calls."
            ),
            "status": "planned",
            "priority": "medium",
            "estimated_hours": 0.5,
            "tags": ["frontend", "performance", "polling", "react-query"],
        },
        {
            "item_type": "bug",
            "title": "Add missing AbortController to SimilarWorkflowsComparison",
            "description": (
                "SimilarWorkflowsComparison.tsx useEffect makes fetch requests without cleanup. "
                "If component unmounts during fetch, requests continue causing potential "
                "memory leaks and 'state update on unmounted component' warnings.\n\n"
                "Should add AbortController for cleanup."
            ),
            "status": "planned",
            "priority": "medium",
            "estimated_hours": 0.5,
            "tags": ["frontend", "memory-leak", "cleanup", "history-panel"],
        },
        {
            "item_type": "enhancement",
            "title": "Fix missing query invalidation in ReviewPanel comment mutation",
            "description": (
                "ReviewPanel.tsx lines 62-69: commentMutation doesn't invalidate queries "
                "after adding comment. Pattern list doesn't refresh to show updated "
                "comment count or status.\n\n"
                "Fix: Add queryClient.invalidateQueries in onSuccess."
            ),
            "status": "planned",
            "priority": "medium",
            "estimated_hours": 0.25,
            "tags": ["frontend", "review-panel", "react-query"],
        },
        {
            "item_type": "bug",
            "title": "Fix missing error handling in workLogClient.deleteWorkLog",
            "description": (
                "workLogClient.ts lines 81-85: deleteWorkLog() doesn't check response.ok, "
                "silently failing on 404/500 errors. Should throw error on failed response."
            ),
            "status": "planned",
            "priority": "medium",
            "estimated_hours": 0.25,
            "tags": ["frontend", "api-client", "error-handling"],
        },
        # LOW PRIORITY ISSUES
        {
            "item_type": "enhancement",
            "title": "Add 'Show More' button for completed items in PlansPanel",
            "description": (
                "PlansPanel.tsx line 137: Silently truncates to 15 completed items with "
                "no indication to user. Should add 'Show More' button to view full history."
            ),
            "status": "planned",
            "priority": "low",
            "estimated_hours": 0.5,
            "tags": ["frontend", "plans-panel", "ux"],
        },
        {
            "item_type": "enhancement",
            "title": "Add accessibility improvements to PlansPanel checkbox",
            "description": (
                "PlansPanel.tsx lines 180-186: Disabled checkbox lacks aria-label. "
                "Should add aria-label='Completed' or 'Not completed' and title attribute "
                "for screen readers."
            ),
            "status": "planned",
            "priority": "low",
            "estimated_hours": 0.25,
            "tags": ["frontend", "accessibility", "plans-panel"],
        },
        {
            "item_type": "enhancement",
            "title": "Memoize expensive computations in RoutesView",
            "description": (
                "RoutesView.tsx line 91: Methods array recalculated on every render. "
                "Should use useMemo to memoize the computation based on routes dependency."
            ),
            "status": "planned",
            "priority": "low",
            "estimated_hours": 0.25,
            "tags": ["frontend", "performance", "routes-panel"],
        },
        {
            "item_type": "enhancement",
            "title": "Add guard clauses to HistoryAnalytics formatters",
            "description": (
                "HistoryAnalytics.tsx formatDuration(): Doesn't handle undefined/null seconds, "
                "could return 'NaNm'. Should add guard clause for invalid input."
            ),
            "status": "planned",
            "priority": "low",
            "estimated_hours": 0.25,
            "tags": ["frontend", "history-panel", "data-validation"],
        },
        {
            "item_type": "enhancement",
            "title": "Add retry configuration to React Query queries",
            "description": (
                "PlansPanel and other components lack retry configuration. If initial load "
                "fails due to network issue, user must refresh entire page. Should add "
                "retry config with exponential backoff."
            ),
            "status": "planned",
            "priority": "low",
            "estimated_hours": 0.5,
            "tags": ["frontend", "react-query", "resilience"],
        },
        {
            "item_type": "enhancement",
            "title": "Remove hardcoded path fallback in ContextAnalysisButton",
            "description": (
                "ContextAnalysisButton.tsx line 43: Contains hardcoded fallback "
                "'/Users/Warmonger0/tac/tac-webbuilder'. Should use environment variable "
                "or remove fallback entirely."
            ),
            "status": "planned",
            "priority": "low",
            "estimated_hours": 0.25,
            "tags": ["frontend", "request-form", "hardcoded-data"],
        },
        # BACKEND ISSUES
        {
            "item_type": "enhancement",
            "title": "Reduce backend startup log verbosity",
            "description": (
                "Background task cancellation logs are too verbose (5+ INFO lines during shutdown). "
                "Service [INIT] logs could be DEBUG instead of INFO (10+ lines during startup).\n\n"
                "Recommendation:\n"
                "- Change individual watcher cancellation from INFO → DEBUG\n"
                "- Change service [INIT] logs from INFO → DEBUG\n"
                "- Keep only high-level [STARTUP]/[SHUTDOWN] at INFO level"
            ),
            "status": "planned",
            "priority": "low",
            "estimated_hours": 0.5,
            "tags": ["backend", "logging", "startup"],
        },
        {
            "item_type": "enhancement",
            "title": "Add server port binding confirmation log",
            "description": (
                "server.py: No explicit log showing 'Server listening on port 8000'. "
                "Should add after uvicorn.run() or in main() startup sequence."
            ),
            "status": "planned",
            "priority": "low",
            "estimated_hours": 0.25,
            "tags": ["backend", "logging", "startup"],
        },
        # STUB PANELS (Future Work)
        {
            "item_type": "feature",
            "title": "Implement Patterns Panel (Panel 6)",
            "description": (
                "PatternsPanel.tsx is currently a stub. Backend API exists "
                "(patternReviewClient.ts with full CRUD). Need to implement:\n\n"
                "- Fetch and display pending patterns\n"
                "- Pattern approval/rejection workflow\n"
                "- Comment/discussion functionality\n"
                "- Review statistics dashboard\n"
                "- Integration with pattern learning engine"
            ),
            "status": "planned",
            "priority": "low",
            "estimated_hours": 6.0,
            "tags": ["frontend", "patterns-panel", "stub", "feature"],
        },
        {
            "item_type": "feature",
            "title": "Implement Quality Panel (Panel 7)",
            "description": (
                "QualityPanel.tsx is currently a stub. Backend quality scoring exists "
                "(quality_scorer.py). Need to implement:\n\n"
                "- Create quality API routes\n"
                "- Display quality metrics and scores\n"
                "- Show compliance information\n"
                "- Error rates and quality trends\n"
                "- Integration with workflow analytics"
            ),
            "status": "planned",
            "priority": "low",
            "estimated_hours": 6.0,
            "tags": ["frontend", "quality-panel", "stub", "feature"],
        },
        {
            "item_type": "feature",
            "title": "Implement Data Panel (Panel 9)",
            "description": (
                "DataPanel.tsx is currently a stub. Need requirements gathering and implementation "
                "for data structure visualization features."
            ),
            "status": "planned",
            "priority": "low",
            "estimated_hours": 6.0,
            "tags": ["frontend", "data-panel", "stub", "feature"],
        },
        # TESTING
        {
            "item_type": "enhancement",
            "title": "Add test coverage for panel components",
            "description": (
                "Most panel components lack test coverage:\n\n"
                "Missing tests:\n"
                "- HistoryView.test.tsx\n"
                "- WorkflowHistoryView.test.tsx\n"
                "- RoutesView.test.tsx\n"
                "- PlansPanel.test.tsx\n"
                "- ReviewPanel.test.tsx\n"
                "- LogPanel.test.tsx\n"
                "- TaskLogsView.test.tsx\n"
                "- UserPromptsView.test.tsx\n\n"
                "Only SimilarWorkflowsComparison.test.tsx exists.\n\n"
                "Should add comprehensive test coverage for critical user flows and error states."
            ),
            "status": "planned",
            "priority": "low",
            "estimated_hours": 8.0,
            "tags": ["frontend", "testing", "quality"],
        },
    ]

    print("Adding panel review findings to database...")
    print(f"Total findings to add: {len(findings)}\n")

    created_count = 0
    for finding in findings:
        try:
            feature_data = PlannedFeatureCreate(**finding)
            created_feature = service.create(feature_data)
            created_count += 1
            print(
                f"✅ [{created_feature.priority.upper()}] {created_feature.title} (ID: {created_feature.id})"
            )
        except Exception as e:
            print(f"❌ Error creating '{finding['title']}': {e}")

    print(f"\n✅ Successfully added {created_count}/{len(findings)} findings to database")

    # Print statistics
    stats = service.get_statistics()
    print(f"\n📊 Updated Statistics:")
    print(f"   By Status: {stats['by_status']}")
    print(f"   By Priority: {stats['by_priority']}")
    print(f"   Total Estimated Hours: {stats['total_estimated_hours']:.1f}h")


if __name__ == "__main__":
    add_panel_review_findings()
