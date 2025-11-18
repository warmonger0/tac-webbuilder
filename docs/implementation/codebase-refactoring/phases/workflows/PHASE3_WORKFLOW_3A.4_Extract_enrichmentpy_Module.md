## Workflow 3A.4: Extract enrichment.py Module

**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 3A.1

**Input Files:**
- `app/server/core/workflow_history_original.py.bak` (lines 808-1096, focus on cost enrichment)

**Output Files:**
- `app/server/core/workflow_history/enrichment.py` (new)

**Tasks:**

1. **Create enrichment.py for cost data enrichment**
   ```python
   """
   Cost data enrichment for workflows.

   Loads cost data from workflow completion files and enriches
   workflow metadata with detailed cost information.
   """

   import json
   import logging
   from pathlib import Path
   from typing import Dict, List, Optional

   from core.cost_tracker import read_cost_history
   from core.data_models import CostData

   logger = logging.getLogger(__name__)
   ```

2. **Extract load_cost_data()** (~50 lines)
   ```python
   def load_cost_data(workflow_id: str) -> Optional[CostData]:
       """
       Load cost data from workflow completion file.

       Args:
           workflow_id: Workflow identifier (directory name)

       Returns:
           CostData object or None if not found
       """
       try:
           cost_data = read_cost_history(workflow_id)
           return cost_data
       except FileNotFoundError:
           logger.debug(f"No cost data found for workflow {workflow_id}")
           return None
       except Exception as e:
           logger.error(f"Error loading cost data for {workflow_id}: {e}")
           return None
   ```

3. **Extract enrich_workflow_with_cost_data()** (~80 lines)
   ```python
   def enrich_workflow_with_cost_data(workflow: Dict) -> Dict:
       """
       Enrich workflow with cost data from completion file.

       Args:
           workflow: Base workflow data

       Returns:
           Enriched workflow data with cost fields populated
       """
       workflow_id = workflow.get('id')
       if not workflow_id:
           return workflow

       cost_data = load_cost_data(workflow_id)
       if not cost_data:
           return workflow

       # Enrich with cost fields
       workflow['total_cost'] = cost_data.total_cost
       workflow['input_tokens'] = cost_data.total_input_tokens
       workflow['output_tokens'] = cost_data.total_output_tokens
       workflow['cache_read_tokens'] = cost_data.total_cache_read_tokens
       workflow['cache_creation_tokens'] = cost_data.total_cache_creation_tokens

       # Add phase-level costs
       if cost_data.phases:
           workflow['phase_costs'] = [
               {
                   'phase': p.phase,
                   'cost': p.cost,
                   'input_tokens': p.input_tokens,
                   'output_tokens': p.output_tokens,
                   'timestamp': p.timestamp,
               }
               for p in cost_data.phases
           ]

       # Add retry information
       workflow['retry_count'] = cost_data.retry_count
       workflow['retry_cost'] = cost_data.retry_cost

       return workflow
   ```

4. **Extract enrich_workflows_batch()** (~50 lines)
   ```python
   def enrich_workflows_batch(workflows: List[Dict]) -> List[Dict]:
       """
       Enrich multiple workflows with cost data.

       Args:
           workflows: List of workflow data dictionaries

       Returns:
           List of enriched workflows
       """
       enriched_workflows = []

       for workflow in workflows:
           try:
               enriched = enrich_workflow_with_cost_data(workflow)
               enriched_workflows.append(enriched)
           except Exception as e:
               logger.error(f"Error enriching workflow {workflow.get('id')}: {e}")
               # Include workflow without enrichment
               enriched_workflows.append(workflow)

       logger.info(f"Enriched {len(enriched_workflows)}/{len(workflows)} workflows with cost data")
       return enriched_workflows
   ```

5. **Add cost summary calculation**
   ```python
   def calculate_cost_summary(workflows: List[Dict]) -> Dict:
       """
       Calculate aggregate cost statistics across workflows.

       Args:
           workflows: List of workflow data dictionaries

       Returns:
           Dictionary with cost summary statistics
       """
       total_cost = 0.0
       total_tokens = 0
       workflow_count = 0

       for workflow in workflows:
           if 'total_cost' in workflow:
               total_cost += workflow['total_cost']
               workflow_count += 1
           if 'input_tokens' in workflow and 'output_tokens' in workflow:
               total_tokens += workflow['input_tokens'] + workflow['output_tokens']

       return {
           'total_cost': total_cost,
           'total_tokens': total_tokens,
           'workflow_count': workflow_count,
           'average_cost': total_cost / workflow_count if workflow_count > 0 else 0.0,
       }
   ```

6. **Update __init__.py**
   ```python
   from .enrichment import (
       load_cost_data,
       enrich_workflow_with_cost_data,
       enrich_workflows_batch,
   )
   ```

**Acceptance Criteria:**
- [ ] enrichment.py created with cost operations
- [ ] Cost data loads correctly from completion files
- [ ] Workflows enriched with all cost fields
- [ ] Batch enrichment handles errors gracefully
- [ ] Missing cost data doesn't break enrichment
- [ ] Import works from __init__.py

**Verification Commands:**
```bash
# Test enrichment
python -c "
from app.server.core.workflow_history.enrichment import enrich_workflows_batch
workflows = [{'id': 'test-123', 'status': 'completed'}]
enriched = enrich_workflows_batch(workflows)
print(f'Enriched {len(enriched)} workflows')
"
```

**Status:** Not Started

---
