## Workflow 3A.8: Create sync.py Orchestration and Integration Tests

**Estimated Time:** 3 hours
**Complexity:** Medium
**Dependencies:** Workflows 3A.2-3A.7

**Input Files:**
- `app/server/core/workflow_history_original.py.bak` (lines 808-1096, main sync function)

**Output Files:**
- `app/server/core/workflow_history/sync.py` (new)
- `app/server/tests/test_workflow_history_integration.py` (new)

**Tasks:**

1. **Create sync.py orchestration module**
   ```python
   """
   Main workflow history sync orchestration.

   Coordinates all sub-modules to perform complete workflow sync:
   1. Scan agents directory
   2. Enrich with cost data
   3. Calculate analytics scores
   4. Calculate similarity
   5. Update database
   6. Learn patterns (Phase 1 integration)
   """

   import logging
   from typing import Dict, List
   from datetime import datetime

   from .scanner import scan_agents_directory
   from .enrichment import enrich_workflows_batch
   from .analytics import calculate_workflow_scores, calculate_phase_metrics
   from .similarity import find_similar_workflows
   from .database import get_workflow_by_id, insert_workflow, update_workflow, init_db

   logger = logging.getLogger(__name__)
   ```

2. **Extract sync_workflow_history() with clear phases**
   ```python
   def sync_workflow_history(silent: bool = False) -> Dict:
       """
       Synchronize workflow history from file system to database.

       This is the main orchestration function that coordinates:
       - Phase 1: File system scanning
       - Phase 2: Cost data enrichment
       - Phase 3: Analytics calculation
       - Phase 3E: Similarity detection
       - Phase 4: Database updates
       - Phase 5: Pattern learning (if available)

       Args:
           silent: If True, suppress info logging (errors still logged)

       Returns:
           Dictionary with sync statistics:
           - scanned: Number of workflows found
           - enriched: Number of workflows enriched with cost data
           - inserted: Number of new workflows inserted
           - updated: Number of existing workflows updated
           - failed: Number of workflows that failed to sync
           - duration_seconds: Total sync duration
       """
       start_time = datetime.now()

       if not silent:
           logger.info("=== Starting workflow history sync ===")

       stats = {
           'scanned': 0,
           'enriched': 0,
           'inserted': 0,
           'updated': 0,
           'failed': 0,
           'duration_seconds': 0,
       }

       try:
           # Ensure database initialized
           init_db()

           # Phase 1: Scan agents directory
           if not silent:
               logger.info("Phase 1: Scanning agents directory...")
           workflows = scan_agents_directory()
           stats['scanned'] = len(workflows)

           if not workflows:
               if not silent:
                   logger.info("No workflows found to sync")
               return stats

           # Phase 2: Enrich with cost data
           if not silent:
               logger.info(f"Phase 2: Enriching {len(workflows)} workflows with cost data...")
           workflows = enrich_workflows_batch(workflows)
           stats['enriched'] = sum(1 for w in workflows if 'total_cost' in w)

           # Phase 3: Calculate analytics scores
           if not silent:
               logger.info("Phase 3: Calculating analytics scores...")
           for workflow in workflows:
               try:
                   scores = calculate_workflow_scores(workflow)
                   workflow.update(scores)

                   # Calculate phase metrics if cost data available
                   if 'phase_costs' in workflow:
                       phase_metrics = calculate_phase_metrics(workflow.get('cost_data'))
                       workflow.update(phase_metrics)
               except Exception as e:
                   logger.error(f"Error calculating scores for {workflow.get('id')}: {e}")

           # Phase 3E: Calculate similarity
           if not silent:
               logger.info("Phase 3E: Calculating workflow similarities...")
           for workflow in workflows:
               try:
                   similar = find_similar_workflows(workflow, workflows, threshold=0.5, limit=5)
                   workflow['similar_workflows'] = [
                       {'id': w.get('id'), 'similarity_score': score}
                       for w, score in similar
                   ]
               except Exception as e:
                   logger.error(f"Error calculating similarity for {workflow.get('id')}: {e}")

           # Phase 4: Update database
           if not silent:
               logger.info("Phase 4: Updating database...")
           for workflow in workflows:
               workflow_id = workflow.get('id')
               if not workflow_id:
                   stats['failed'] += 1
                   continue

               try:
                   # Check if workflow exists
                   existing = get_workflow_by_id(workflow_id)

                   if existing:
                       # Update existing
                       success = update_workflow(workflow_id, workflow)
                       if success:
                           stats['updated'] += 1
                       else:
                           stats['failed'] += 1
                   else:
                       # Insert new
                       success = insert_workflow(workflow)
                       if success:
                           stats['inserted'] += 1
                       else:
                           stats['failed'] += 1

               except Exception as e:
                   logger.error(f"Error syncing workflow {workflow_id}: {e}")
                   stats['failed'] += 1

           # Phase 5: Pattern learning (if pattern detection available)
           try:
               from core.pattern_detector import detect_patterns_in_workflow

               if not silent:
                   logger.info("Phase 5: Learning patterns...")

               for workflow in workflows:
                   try:
                       detect_patterns_in_workflow(workflow)
                   except Exception as e:
                       logger.debug(f"Pattern detection skipped for {workflow.get('id')}: {e}")

           except ImportError:
               # Pattern detection not available, skip
               if not silent:
                   logger.debug("Pattern detection module not available, skipping Phase 5")

           # Calculate duration
           end_time = datetime.now()
           stats['duration_seconds'] = int((end_time - start_time).total_seconds())

           if not silent:
               logger.info(f"=== Sync complete in {stats['duration_seconds']}s ===")
               logger.info(f"Scanned: {stats['scanned']}, Enriched: {stats['enriched']}")
               logger.info(f"Inserted: {stats['inserted']}, Updated: {stats['updated']}, Failed: {stats['failed']}")

           return stats

       except Exception as e:
           logger.error(f"Fatal error during sync: {e}")
           stats['failed'] = stats['scanned']
           raise
   ```

3. **Create integration tests**
   ```python
   # app/server/tests/test_workflow_history_integration.py
   """
   Integration tests for workflow_history module.

   Tests the complete sync workflow from file scanning to database updates.
   """

   import pytest
   import tempfile
   import json
   from pathlib import Path

   from app.server.core.workflow_history import (
       sync_workflow_history,
       get_workflow_history,
       get_workflow_by_id,
       init_db,
   )

   @pytest.fixture
   def temp_agents_dir():
       """Create temporary agents directory with test workflows."""
       with tempfile.TemporaryDirectory() as tmpdir:
           agents_path = Path(tmpdir) / "agents"
           agents_path.mkdir()

           # Create test workflow
           workflow_dir = agents_path / "test-workflow-123"
           workflow_dir.mkdir()

           state_data = {
               "id": "test-workflow-123",
               "status": "completed",
               "nl_input": "Test workflow",
               "created_at": "2025-01-01T00:00:00Z",
               "duration_seconds": 120,
           }

           with open(workflow_dir / "adw_state.json", 'w') as f:
               json.dump(state_data, f)

           yield agents_path

   def test_full_sync_workflow(temp_agents_dir, monkeypatch):
       """Test complete workflow sync process."""
       # Patch AGENTS_DIR to use temp directory
       import app.server.core.workflow_history.scanner as scanner
       monkeypatch.setattr(scanner, 'AGENTS_DIR', temp_agents_dir)

       # Initialize database
       init_db()

       # Run sync
       result = sync_workflow_history(silent=True)

       # Verify results
       assert result['scanned'] == 1
       assert result['inserted'] == 1
       assert result['failed'] == 0

       # Verify workflow in database
       workflow = get_workflow_by_id('test-workflow-123')
       assert workflow is not None
       assert workflow['status'] == 'completed'

   def test_sync_updates_existing_workflow(temp_agents_dir, monkeypatch):
       """Test that sync updates existing workflows."""
       import app.server.core.workflow_history.scanner as scanner
       monkeypatch.setattr(scanner, 'AGENTS_DIR', temp_agents_dir)

       init_db()

       # First sync
       result1 = sync_workflow_history(silent=True)
       assert result1['inserted'] == 1

       # Second sync (should update)
       result2 = sync_workflow_history(silent=True)
       assert result2['updated'] == 1
       assert result2['inserted'] == 0

   def test_get_workflow_history_pagination():
       """Test workflow history pagination."""
       result = get_workflow_history(limit=10, offset=0)

       assert 'workflows' in result
       assert 'total' in result
       assert len(result['workflows']) <= 10
   ```

4. **Update __init__.py with final imports**
   ```python
   # Complete __init__.py
   """
   Workflow history tracking module for ADW workflows.

   This module provides database operations for storing and retrieving workflow
   execution history, including metadata, costs, performance metrics, token usage,
   and detailed status information.

   NOTE: This module was refactored from a monolithic file into focused submodules.
   The public API remains unchanged for backwards compatibility.
   """

   from .database import (
       init_db,
       get_workflow_by_id,
       insert_workflow,
       update_workflow,
       get_workflow_history,
   )

   from .sync import (
       sync_workflow_history,
   )

   from .resync import (
       resync_workflow_cost,
       resync_all_completed_workflows,
   )

   from .analytics import (
       get_history_analytics,
       calculate_phase_metrics,
       calculate_workflow_scores,
   )

   __all__ = [
       # Database operations
       'init_db',
       'get_workflow_by_id',
       'insert_workflow',
       'update_workflow',
       'get_workflow_history',

       # Main sync function
       'sync_workflow_history',

       # Resync operations
       'resync_workflow_cost',
       'resync_all_completed_workflows',

       # Analytics
       'get_history_analytics',
       'calculate_phase_metrics',
       'calculate_workflow_scores',
   ]
   ```

5. **Remove backup file**
   ```bash
   rm app/server/core/workflow_history_original.py.bak
   ```

6. **Update all imports in codebase**
   ```bash
   # Search for imports
   grep -r "from core.workflow_history import" app/server/

   # Verify all imports still work (should be backwards compatible)
   ```

**Acceptance Criteria:**
- [ ] sync.py created with complete orchestration
- [ ] All phases execute in correct order
- [ ] Integration tests pass
- [ ] Backwards compatibility maintained
- [ ] Original backup file removed
- [ ] All imports across codebase work
- [ ] No regression in functionality

**Verification Commands:**
```bash
# Test full sync
python -c "
from app.server.core.workflow_history import sync_workflow_history
result = sync_workflow_history(silent=True)
print('Sync result:', result)
"

# Run all workflow_history tests
cd app/server && pytest tests/test_workflow_history.py -v
cd app/server && pytest tests/test_workflow_history_integration.py -v

# Test imports from other files
cd app/server && python -c "
from core.workflow_history import (
    sync_workflow_history,
    get_workflow_history,
    init_db
)
print('All imports successful')
"
```

**Status:** Not Started

---
