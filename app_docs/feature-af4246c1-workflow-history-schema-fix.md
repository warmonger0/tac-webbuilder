# Workflow History Schema Fix - Temporal Column Mismatch

**ADW ID:** af4246c1
**Date:** 2025-11-20
**Specification:** specs/issue-64-adw-af4246c1-sdlc_planner-bug-diagnose-and-fix-tac-webbuilder-s-inability-to.md

## Overview

Fixed a critical schema mismatch bug that prevented the Workflow History feature from loading data. The database columns `submission_hour` and `submission_day_of_week` were renamed to `hour_of_day` and `day_of_week` to match the Python code expectations, resolving errors that appeared repeatedly in API calls and WebSocket connections.

## Screenshots

![Workflow History Page Loading Successfully](assets/01_workflow_history_page_loading_successfully.png)

The Workflow History page now loads successfully without schema errors, displaying the Analytics Summary and workflow data properly.

## What Was Built

- **Database Migration 005**: Created a comprehensive migration to rename temporal analytics columns from `submission_hour`/`submission_day_of_week` to `hour_of_day`/`day_of_week`
- **Migration 003 Update**: Updated the original analytics migration file to reflect corrected column names for future database initializations
- **Schema Alignment**: Ensured database schema matches Python data models and code throughout the application

## Technical Implementation

### Files Modified

- `app/server/db/migrations/005_rename_temporal_columns.sql` (new file, 127 additions): Complete migration script that handles SQLite's limited ALTER TABLE capabilities by recreating the table with correct column names while preserving all existing data
- `app/server/db/migrations/003_add_analytics_metrics.sql` (6 additions, 4 deletions): Updated column definitions and index names to use `hour_of_day` and `day_of_week` instead of `submission_hour` and `submission_day_of_week`

### Key Changes

- **Migration 005 Implementation**: Uses a sophisticated approach to work around SQLite's ALTER TABLE limitations:
  1. Creates new columns with correct names (`hour_of_day`, `day_of_week`)
  2. Copies data from old columns (`submission_hour`, `submission_day_of_week`)
  3. Creates temporary table backup with only the desired columns
  4. Drops and recreates the workflow_history table with proper schema
  5. Restores all data and recreates indexes with corrected names

- **Index Updates**: Renamed indexes from `idx_submission_hour` and `idx_submission_day_of_week` to `idx_hour_of_day` and `idx_day_of_week` to maintain query performance with the new column names

- **Migration 003 Correction**: Updated the original analytics migration to define columns with the correct names from the start, preventing this issue in fresh database installations

## How to Use

### Running the Migration

1. Navigate to the server directory:
   ```bash
   cd app/server
   ```

2. Run the migration script:
   ```bash
   uv run python scripts/run_migrations.py
   ```

3. Verify the schema change:
   ```bash
   sqlite3 app/server/db/workflow_history.db "PRAGMA table_info(workflow_history);" | grep -E "(hour_of_day|day_of_week)"
   ```

4. Start the server and verify no errors appear:
   ```bash
   cd app/server && uv run python server.py
   ```

5. Access the Workflow History page in the web UI to confirm it loads without errors

## Configuration

No configuration changes required. The migration automatically:
- Preserves all existing workflow history data
- Maintains all indexes for query performance
- Works with existing code without requiring code changes

## Testing

### Verification Steps

1. **Schema Verification**: Confirm the columns are renamed correctly in the database schema
2. **API Testing**: Test the `/api/workflow-history` endpoint to ensure it returns data without errors
3. **WebSocket Testing**: Verify WebSocket connections to `/ws/workflow-history` work properly
4. **UI Testing**: Load the Workflow History page in the browser and confirm the Analytics Summary displays correctly

### Validation Commands

```bash
# Run the migration
cd app/server && uv run python scripts/run_migrations.py

# Verify schema
sqlite3 app/server/db/workflow_history.db "PRAGMA table_info(workflow_history);" | grep -E "(hour_of_day|day_of_week)"

# Test API endpoint
curl -s http://localhost:8000/api/workflow-history?limit=5 | jq '.workflows | length'

# Run database tests
cd app/server && uv run pytest tests/core/workflow_history_utils/test_database.py -v

# Run integration tests
cd app/server && uv run pytest tests/integration/test_workflow_history_integration.py -v
```

## Notes

- **Root Cause**: The bug was introduced during Phase 3A analytics implementation when the SQL migration used different naming conventions (`submission_*`) than the Python code (`hour_of_day`, `day_of_week`)
- **Backwards Compatibility**: The migration preserves all existing data - no workflow history is lost during the column rename process
- **SQLite Limitations**: SQLite's limited ALTER TABLE RENAME COLUMN support required a more complex migration strategy involving table recreation
- **Prevention**: Migration 003 has been updated to use the correct column names, preventing this issue in fresh database installations
- **No Code Changes Required**: All Python code already used the correct column names - only the database schema needed correction
