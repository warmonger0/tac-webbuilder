## Workflow 3A.6: Extract similarity.py Module

**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 3A.1

**Input Files:**
- `app/server/core/workflow_history_original.py.bak` (lines 1049-1093)

**Output Files:**
- `app/server/core/workflow_history/similarity.py` (new)

**Tasks:**

1. **Create similarity.py for Phase 3E similarity detection**
   ```python
   """
   Workflow similarity detection (Phase 3E).

   Calculates similarity scores between workflows based on:
   - Natural language input similarity
   - Execution pattern similarity
   - Cost profile similarity
   """

   import logging
   from typing import Dict, List, Optional, Tuple
   from difflib import SequenceMatcher

   logger = logging.getLogger(__name__)
   ```

2. **Extract calculate_similarity_score()** (~40 lines)
   ```python
   def calculate_similarity_score(workflow1: Dict, workflow2: Dict) -> float:
       """
       Calculate similarity score between two workflows.

       Weighted combination of:
       - NL input similarity (40%)
       - Status match (20%)
       - Cost similarity (20%)
       - Duration similarity (20%)

       Args:
           workflow1: First workflow data
           workflow2: Second workflow data

       Returns:
           Similarity score from 0.0 to 1.0
       """
       # Calculate NL input similarity
       nl_sim = calculate_nl_similarity(
           workflow1.get('nl_input', ''),
           workflow2.get('nl_input', '')
       )

       # Status match
       status_sim = 1.0 if workflow1.get('status') == workflow2.get('status') else 0.0

       # Cost similarity
       cost_sim = calculate_cost_similarity(
           workflow1.get('total_cost', 0.0),
           workflow2.get('total_cost', 0.0)
       )

       # Duration similarity
       duration_sim = calculate_duration_similarity(
           workflow1.get('duration_seconds', 0),
           workflow2.get('duration_seconds', 0)
       )

       # Weighted average
       similarity = (
           nl_sim * 0.40 +
           status_sim * 0.20 +
           cost_sim * 0.20 +
           duration_sim * 0.20
       )

       return similarity
   ```

3. **Add NL similarity calculation**
   ```python
   def calculate_nl_similarity(nl1: str, nl2: str) -> float:
       """
       Calculate similarity between two natural language inputs.

       Uses SequenceMatcher for fuzzy string matching.

       Args:
           nl1: First NL input
           nl2: Second NL input

       Returns:
           Similarity ratio from 0.0 to 1.0
       """
       if not nl1 or not nl2:
           return 0.0

       matcher = SequenceMatcher(None, nl1.lower(), nl2.lower())
       return matcher.ratio()
   ```

4. **Add cost and duration similarity**
   ```python
   def calculate_cost_similarity(cost1: float, cost2: float) -> float:
       """Calculate similarity based on cost values."""
       if cost1 == 0.0 and cost2 == 0.0:
           return 1.0
       if cost1 == 0.0 or cost2 == 0.0:
           return 0.0

       ratio = min(cost1, cost2) / max(cost1, cost2)
       return ratio

   def calculate_duration_similarity(dur1: int, dur2: int) -> float:
       """Calculate similarity based on duration values."""
       if dur1 == 0 and dur2 == 0:
           return 1.0
       if dur1 == 0 or dur2 == 0:
           return 0.0

       ratio = min(dur1, dur2) / max(dur1, dur2)
       return ratio
   ```

5. **Extract find_similar_workflows()** (~60 lines)
   ```python
   def find_similar_workflows(
       target_workflow: Dict,
       all_workflows: List[Dict],
       threshold: float = 0.5,
       limit: int = 5
   ) -> List[Tuple[Dict, float]]:
       """
       Find workflows similar to the target workflow.

       Args:
           target_workflow: Workflow to find similarities for
           all_workflows: Complete list of workflows to search
           threshold: Minimum similarity score (0.0-1.0)
           limit: Maximum number of similar workflows to return

       Returns:
           List of (workflow, similarity_score) tuples, sorted by score
       """
       similarities = []
       target_id = target_workflow.get('id')

       for workflow in all_workflows:
           # Skip self
           if workflow.get('id') == target_id:
               continue

           score = calculate_similarity_score(target_workflow, workflow)

           if score >= threshold:
               similarities.append((workflow, score))

       # Sort by similarity score (highest first)
       similarities.sort(key=lambda x: x[1], reverse=True)

       # Return top N
       return similarities[:limit]
   ```

6. **Add batch similarity calculation**
   ```python
   def calculate_all_similarities(workflows: List[Dict]) -> Dict[str, List[Tuple[str, float]]]:
       """
       Calculate similarities for all workflows.

       Args:
           workflows: List of all workflows

       Returns:
           Dictionary mapping workflow_id to list of (similar_id, score) tuples
       """
       similarities = {}

       for workflow in workflows:
           workflow_id = workflow.get('id')
           if not workflow_id:
               continue

           similar = find_similar_workflows(workflow, workflows)
           similarities[workflow_id] = [
               (w.get('id'), score) for w, score in similar
           ]

       logger.info(f"Calculated similarities for {len(similarities)} workflows")
       return similarities
   ```

7. **Update __init__.py**
   ```python
   from .similarity import (
       calculate_similarity_score,
       find_similar_workflows,
   )
   ```

**Acceptance Criteria:**
- [ ] similarity.py created with all similarity functions
- [ ] Similarity scores calculated correctly
- [ ] NL similarity uses proper fuzzy matching
- [ ] Similar workflows found and ranked
- [ ] Performance acceptable for large datasets
- [ ] Import works from __init__.py

**Verification Commands:**
```bash
# Test similarity
python -c "
from app.server.core.workflow_history.similarity import calculate_similarity_score
w1 = {'nl_input': 'test', 'status': 'completed', 'total_cost': 1.0}
w2 = {'nl_input': 'test', 'status': 'completed', 'total_cost': 1.1}
score = calculate_similarity_score(w1, w2)
print(f'Similarity: {score}')
"
```

**Status:** Not Started
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
