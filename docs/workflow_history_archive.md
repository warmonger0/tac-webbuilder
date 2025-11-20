# Workflow History Archive System

## Overview

The workflow history archive system allows you to remove workflow records from the active history panel while preserving them for future reference. This is useful for:

- Cleaning up test/debug workflows
- Removing experimental or failed attempts
- Archiving completed project phases
- Keeping the history panel focused on relevant work

## Database Tables

### Active Table: `workflow_history`
- Located in: `app/server/db/workflow_history.db`
- Contains all active workflow records
- Powers the workflow history panel in the UI

### Archive Table: `workflow_history_archive`
- Located in: `app/server/db/workflow_history.db`
- Contains archived workflow records
- Includes additional metadata:
  - `original_id`: The ID from the original workflow_history table
  - `archived_at`: Timestamp when the record was archived
  - `archive_reason`: Description of why it was archived

## Usage

### Archive Workflows by Issue Number

```bash
./scripts/archive_workflows.sh <issue_number> [issue_number2 ...]
```

**Examples:**
```bash
# Archive a single issue
./scripts/archive_workflows.sh 999

# Archive multiple issues
./scripts/archive_workflows.sh 999 6 13
```

### Manual Archival (SQL)

```sql
-- Archive specific workflows
INSERT INTO workflow_history_archive (
    original_id, adw_id, issue_number, /* ... other columns ... */
    archive_reason
)
SELECT id, adw_id, issue_number, /* ... other columns ... */,
    'Your reason here'
FROM workflow_history
WHERE issue_number IN (6, 13, 999);

-- Remove from active table
DELETE FROM workflow_history WHERE issue_number IN (6, 13, 999);
```

### View Archived Records

```sql
-- View all archived records
SELECT original_id, adw_id, issue_number, status, archive_reason, archived_at
FROM workflow_history_archive
ORDER BY archived_at DESC;

-- View archived records for specific issues
SELECT original_id, adw_id, issue_number, status, archive_reason
FROM workflow_history_archive
WHERE issue_number IN (999, 6, 13)
ORDER BY issue_number;
```

### Restore Archived Records (if needed)

```sql
-- Restore specific records back to active table
INSERT INTO workflow_history (
    adw_id, issue_number, /* ... other columns ... */
)
SELECT adw_id, issue_number, /* ... other columns ... */
FROM workflow_history_archive
WHERE issue_number = 999;

-- Optionally remove from archive
DELETE FROM workflow_history_archive WHERE issue_number = 999;
```

## Initial Archive (2025-11-19)

**Archived Issues:** #999, #6, #13

**Records Archived:** 4 workflows
- Issue #6: 1 workflow (ADW: 5b27f57c)
- Issue #13: 1 workflow (ADW: 3d193a52)
- Issue #999: 2 workflows (ADWs: f8d2280c, 64970dee)

**Reason:** Manual archive - cleanup of test/debug issues

**Impact:** These issues no longer appear in the workflow history panel

## Notes

- Archiving is permanent (unless manually restored)
- All workflow data is preserved in the archive table
- The history panel queries only the active `workflow_history` table
- Archived records retain all their original data plus archive metadata
- The archive table has indexes on `issue_number`, `adw_id`, and `archived_at` for efficient querying

## Future Enhancements

Potential improvements to the archive system:

1. **Auto-archival**: Automatically archive workflows older than X days
2. **Archive UI**: Add a tab in the history panel to view archived workflows
3. **Bulk operations**: Archive by date range, status, or workflow template
4. **Archive export**: Export archived workflows to JSON/CSV for external storage
5. **Retention policy**: Automatically delete archived records after a retention period
