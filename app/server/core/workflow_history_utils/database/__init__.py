"""
Database operations for workflow history.

This package provides all database CRUD operations for workflow history tracking,
including schema initialization, insertions, updates, queries, and analytics.

Refactored from monolithic database.py into focused modules:
- schema.py: Database schema initialization and migrations
- mutations.py: Insert and update operations
- queries.py: Read operations and filtering
- analytics.py: Analytics and aggregate queries

All original functions remain accessible via this package for backward compatibility.
"""

# Schema operations
# Analytics operations
from .analytics import get_history_analytics

# Mutation operations (INSERT, UPDATE)
from .mutations import (
    insert_workflow_history,
    update_workflow_history,
    update_workflow_history_by_issue,
)

# Query operations (SELECT)
from .queries import (
    get_workflow_by_adw_id,
    get_workflow_history,
)
from .schema import DB_PATH, init_db
from utils.db_connection import get_connection as get_db_connection

__all__ = [
    # Schema
    'init_db',
    'DB_PATH',
    'get_db_connection',
    # Mutations
    'insert_workflow_history',
    'update_workflow_history_by_issue',
    'update_workflow_history',
    # Queries
    'get_workflow_by_adw_id',
    'get_workflow_history',
    # Analytics
    'get_history_analytics',
]
