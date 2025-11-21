"""
Workflow history tracking module for ADW workflows.

This module provides database operations for storing and retrieving workflow
execution history, including metadata, costs, performance metrics, token usage,
and detailed status information.

This is a facade module that re-exports functionality from workflow_history_utils
submodules for backwards compatibility.
"""

import logging

# Database operations
from core.workflow_history_utils.database import (
    DB_PATH,
    get_history_analytics,
    get_workflow_by_adw_id,
    get_workflow_history,
    init_db,
    insert_workflow_history,
    update_workflow_history,
    update_workflow_history_by_issue,
)

# Synchronization operations
from core.workflow_history_utils.sync_manager import (
    resync_all_completed_workflows,
    resync_workflow_cost,
    sync_workflow_history,
)

logger = logging.getLogger(__name__)

# Define public API
__all__ = [
    # Database path (for testing)
    "DB_PATH",
    # Database operations
    "init_db",
    "insert_workflow_history",
    "update_workflow_history_by_issue",
    "update_workflow_history",
    "get_workflow_by_adw_id",
    "get_workflow_history",
    "get_history_analytics",
    # Synchronization operations
    "sync_workflow_history",
    "resync_workflow_cost",
    "resync_all_completed_workflows",
]

# All functionality is re-exported from submodules for backwards compatibility.
# See workflow_history_utils/ for implementation details:
# - database.py: Database operations and CRUD
# - sync_manager.py: Synchronization and orchestration
# - enrichment.py: Data enrichment operations
# - filesystem.py: Agent directory scanning
# - github_client.py: GitHub API integration
# - metrics.py: Metric calculations
# - models.py: Type definitions and constants
