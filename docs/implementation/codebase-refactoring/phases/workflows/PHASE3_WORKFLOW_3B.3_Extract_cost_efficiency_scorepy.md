## Workflow 3B.3: Extract cost_efficiency_score.py

**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 3B.1

**Input Files:**
- `app/server/core/workflow_analytics_original.py.bak` (lines 192-286)

**Output Files:**
- `app/server/core/workflow_analytics/scoring/cost_efficiency_score.py` (new)

**Tasks:**

1. **Create cost_efficiency_score.py**
   ```python
   """
   Cost Efficiency Scorer.

   Analyzes cost performance including model appropriateness.

   Scoring criteria:
   - Base: 70.0
   - Penalties:
     - Over budget: Variable based on percentage
     - Wrong model for complexity: -20
     - Excessive retry cost: Variable
     - High cache miss rate: Variable
   - Bonuses:
     - Under budget: +20
     - Appropriate model selection: +15
     - Good cache utilization: +15
   """

   import logging
   from typing import Dict
   from .base import BaseScorer
   from ..complexity import detect_complexity

   logger = logging.getLogger(__name__)

   class CostEfficiencyScorer(BaseScorer):
       """Scorer for cost efficiency."""

       def calculate_base_score(self) -> float:
           """Start with base score of 70."""
           return 70.0

       def apply_penalties(self) -> float:
           """Apply penalties for cost inefficiencies."""
           penalties = 0.0

           # Budget penalties
           total_cost = self.workflow.get('total_cost', 0.0)
           budget = self.workflow.get('budget', 0.0)

           if budget > 0 and total_cost > budget:
               over_budget_pct = ((total_cost - budget) / budget) * 100
               if over_budget_pct > 50:
                   penalties += 30.0
               elif over_budget_pct > 20:
                   penalties += 20.0
               elif over_budget_pct > 10:
                   penalties += 10.0

           # Model appropriateness penalty
           complexity = detect_complexity(self.workflow)
           model = self.workflow.get('model', '')

           if complexity == 'simple' and 'opus' in model.lower():
               penalties += 20.0  # Overkill
           elif complexity == 'complex' and 'haiku' in model.lower():
               penalties += 20.0  # Underpowered

           # Retry cost penalty
           retry_cost = self.workflow.get('retry_cost', 0.0)
           if total_cost > 0:
               retry_pct = (retry_cost / total_cost) * 100
               if retry_pct > 30:
                   penalties += 25.0
               elif retry_pct > 15:
                   penalties += 15.0

           # Cache miss penalty
           cache_read = self.workflow.get('cache_read_tokens', 0)
           cache_creation = self.workflow.get('cache_creation_tokens', 0)
           total_tokens = self.workflow.get('input_tokens', 0) + self.workflow.get('output_tokens', 0)

           if total_tokens > 0 and cache_creation > 0:
               cache_utilization = cache_read / (cache_read + cache_creation) if (cache_read + cache_creation) > 0 else 0
               if cache_utilization < 0.3:
                   penalties += 15.0

           return penalties

       def apply_bonuses(self) -> float:
           """Apply bonuses for good cost efficiency."""
           bonuses = 0.0

           # Under budget bonus
           total_cost = self.workflow.get('total_cost', 0.0)
           budget = self.workflow.get('budget', 0.0)

           if budget > 0 and total_cost < budget:
               under_budget_pct = ((budget - total_cost) / budget) * 100
               if under_budget_pct > 20:
                   bonuses += 20.0
               elif under_budget_pct > 10:
                   bonuses += 10.0

           # Appropriate model bonus
           complexity = detect_complexity(self.workflow)
           model = self.workflow.get('model', '')

           if complexity == 'simple' and 'haiku' in model.lower():
               bonuses += 15.0
           elif complexity == 'medium' and 'sonnet' in model.lower():
               bonuses += 15.0
           elif complexity == 'complex' and 'opus' in model.lower():
               bonuses += 15.0

           # Good cache utilization bonus
           cache_read = self.workflow.get('cache_read_tokens', 0)
           cache_creation = self.workflow.get('cache_creation_tokens', 0)

           if cache_creation > 0:
               cache_utilization = cache_read / (cache_read + cache_creation) if (cache_read + cache_creation) > 0 else 0
               if cache_utilization > 0.7:
                   bonuses += 15.0

           return bonuses


   def calculate_cost_efficiency_score(workflow: Dict) -> float:
       """
       Calculate cost efficiency score for a workflow.

       Args:
           workflow: Workflow data dictionary

       Returns:
           Cost efficiency score from 0.0 to 100.0
       """
       scorer = CostEfficiencyScorer(workflow)
       return scorer.calculate()
   ```

2. **Update imports**

**Acceptance Criteria:**
- [ ] CostEfficiencyScorer created
- [ ] Model appropriateness checked
- [ ] Budget compliance checked
- [ ] Cache utilization evaluated
- [ ] Tests pass

**Verification Commands:**
```bash
python -c "
from app.server.core.workflow_analytics import calculate_cost_efficiency_score
workflow = {
    'total_cost': 0.50,
    'budget': 1.00,
    'model': 'claude-3-haiku',
    'nl_input': 'simple task',
    'duration_seconds': 60,
}
score = calculate_cost_efficiency_score(workflow)
print(f'Cost efficiency score: {score}')
"
```

**Status:** Not Started

---
