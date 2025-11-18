## Workflow 3A.7: Extract resync.py Module

**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 3A.2, 3A.4

**Input Files:**
- `app/server/core/workflow_history_original.py.bak` (lines 1099-1276)

**Output Files:**
- `app/server/core/workflow_history/resync.py` (new)

**Tasks:**

1. **Create resync.py for cost resync operations**
   ```python
   """
   Workflow cost resync operations.

   Handles resyncing cost data for workflows that completed
   before cost tracking was implemented.
   """

   import logging
   from typing import Dict, List, Optional
   from datetime import datetime

   from .database import get_workflow_by_id, update_workflow
   from .enrichment import load_cost_data, enrich_workflow_with_cost_data

   logger = logging.getLogger(__name__)
   ```

2. **Extract resync_workflow_cost()** (~80 lines)
   ```python
   def resync_workflow_cost(workflow_id: str) -> Dict:
       """
       Resync cost data for a single workflow.

       Loads fresh cost data from completion file and updates database.

       Args:
           workflow_id: Workflow identifier

       Returns:
           Dictionary with:
           - success: bool
           - workflow_id: str
           - updated: bool
           - message: str
       """
       try:
           # Get current workflow data
           workflow = get_workflow_by_id(workflow_id)
           if not workflow:
               return {
                   'success': False,
                   'workflow_id': workflow_id,
                   'updated': False,
                   'message': 'Workflow not found in database'
               }

           # Load fresh cost data
           cost_data = load_cost_data(workflow_id)
           if not cost_data:
               return {
                   'success': False,
                   'workflow_id': workflow_id,
                   'updated': False,
                   'message': 'No cost data available'
               }

           # Enrich workflow with cost data
           enriched = enrich_workflow_with_cost_data(workflow)

           # Update database
           updated = update_workflow(workflow_id, enriched)

           return {
               'success': updated,
               'workflow_id': workflow_id,
               'updated': updated,
               'message': 'Cost data resynced successfully' if updated else 'Update failed'
           }

       except Exception as e:
           logger.error(f"Error resyncing workflow {workflow_id}: {e}")
           return {
               'success': False,
               'workflow_id': workflow_id,
               'updated': False,
               'message': str(e)
           }
   ```

3. **Extract resync_all_completed_workflows()** (~90 lines)
   ```python
   def resync_all_completed_workflows(
       status_filter: str = 'completed',
       batch_size: int = 50
   ) -> Dict:
       """
       Resync cost data for all workflows matching status filter.

       Args:
           status_filter: Status to filter by (default: completed)
           batch_size: Number of workflows to process per batch

       Returns:
           Dictionary with:
           - total_processed: int
           - successful: int
           - failed: int
           - workflows: List of workflow_ids processed
       """
       from .database import get_workflow_history

       results = {
           'total_processed': 0,
           'successful': 0,
           'failed': 0,
           'workflows': []
       }

       offset = 0
       while True:
           # Get batch of workflows
           batch = get_workflow_history(
               limit=batch_size,
               offset=offset,
               status=status_filter
           )

           workflows = batch.get('workflows', [])
           if not workflows:
               break

           # Resync each workflow
           for workflow in workflows:
               workflow_id = workflow.get('id')
               if not workflow_id:
                   continue

               result = resync_workflow_cost(workflow_id)
               results['total_processed'] += 1
               results['workflows'].append(workflow_id)

               if result['success']:
                   results['successful'] += 1
               else:
                   results['failed'] += 1

           offset += batch_size

           # Log progress
           logger.info(
               f"Resync progress: {results['total_processed']} workflows, "
               f"{results['successful']} successful, {results['failed']} failed"
           )

       logger.info(f"Resync complete: {results}")
       return results
   ```

4. **Add selective resync**
   ```python
   def resync_workflows_by_date_range(
       start_date: str,
       end_date: str
   ) -> Dict:
       """
       Resync workflows within a date range.

       Args:
           start_date: ISO format date string
           end_date: ISO format date string

       Returns:
           Resync results dictionary
       """
       # Implementation for date-filtered resync
       pass
   ```

5. **Update __init__.py**
   ```python
   from .resync import (
       resync_workflow_cost,
       resync_all_completed_workflows,
   )
   ```

**Acceptance Criteria:**
- [ ] resync.py created with resync functions
- [ ] Single workflow resync works correctly
- [ ] Batch resync processes all workflows
- [ ] Progress logging during batch operations
- [ ] Error handling for missing cost data
- [ ] Import works from __init__.py

**Verification Commands:**
```bash
# Test resync
python -c "
from app.server.core.workflow_history.resync import resync_workflow_cost
result = resync_workflow_cost('test-workflow-123')
print('Resync result:', result)
"
```

**Status:** Not Started

---
