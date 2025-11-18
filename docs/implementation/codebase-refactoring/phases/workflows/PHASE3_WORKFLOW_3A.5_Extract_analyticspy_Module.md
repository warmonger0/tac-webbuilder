## Workflow 3A.5: Extract analytics.py Module

**Estimated Time:** 2 hours
**Complexity:** Low
**Dependencies:** Workflow 3A.1

**Input Files:**
- `app/server/core/workflow_history_original.py.bak` (lines 615-728)

**Output Files:**
- `app/server/core/workflow_history/analytics.py` (new)

**Tasks:**

1. **Create analytics.py for history analytics**
   ```python
   """
   Analytics calculations for workflow history.

   Provides aggregate analytics and statistics across workflow history.
   """

   import logging
   from typing import Dict, List, Optional
   from datetime import datetime, timedelta

   from core.workflow_analytics import (
       extract_hour,
       extract_day_of_week,
       calculate_nl_input_clarity_score,
       calculate_cost_efficiency_score,
       calculate_performance_score,
       calculate_quality_score,
   )

   logger = logging.getLogger(__name__)
   ```

2. **Extract calculate_phase_metrics()** (lines 34-120 from original)
   ```python
   def calculate_phase_metrics(cost_data) -> Dict:
       """
       Calculate phase-level performance metrics from cost_data.

       Args:
           cost_data: CostData object containing phase information

       Returns:
           Dictionary with phase durations, bottlenecks, and idle time
       """
       # Implementation from original lines 34-120
   ```

3. **Extract get_history_analytics()** (lines 615-728)
   ```python
   def get_history_analytics(workflows: List[Dict]) -> Dict:
       """
       Calculate aggregate analytics across workflow history.

       Args:
           workflows: List of workflow dictionaries

       Returns:
           Dictionary with analytics:
           - total_workflows: Count of all workflows
           - completed_count: Count of completed workflows
           - failed_count: Count of failed workflows
           - average_cost: Average cost per workflow
           - average_duration: Average duration in seconds
           - total_cost: Sum of all costs
           - date_range: First and last workflow dates
       """
       # Implementation from original lines 615-728
   ```

4. **Add temporal analytics**
   ```python
   def get_temporal_analytics(workflows: List[Dict]) -> Dict:
       """
       Analyze workflow timing patterns.

       Args:
           workflows: List of workflow dictionaries

       Returns:
           Dictionary with temporal patterns:
           - hourly_distribution: Workflows by hour of day
           - daily_distribution: Workflows by day of week
           - peak_hours: Most active hours
       """
       hourly_counts = {}
       daily_counts = {}

       for workflow in workflows:
           timestamp = workflow.get('created_at')
           if not timestamp:
               continue

           hour = extract_hour(timestamp)
           day = extract_day_of_week(timestamp)

           if hour >= 0:
               hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
           if day >= 0:
               daily_counts[day] = daily_counts.get(day, 0) + 1

       return {
           'hourly_distribution': hourly_counts,
           'daily_distribution': daily_counts,
           'peak_hours': sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:3],
       }
   ```

5. **Add scoring analytics**
   ```python
   def calculate_workflow_scores(workflow: Dict) -> Dict:
       """
       Calculate all analytics scores for a workflow.

       Args:
           workflow: Workflow data dictionary

       Returns:
           Dictionary with all scores:
           - nl_clarity_score
           - cost_efficiency_score
           - performance_score
           - quality_score
       """
       return {
           'nl_clarity_score': calculate_nl_input_clarity_score(workflow),
           'cost_efficiency_score': calculate_cost_efficiency_score(workflow),
           'performance_score': calculate_performance_score(workflow),
           'quality_score': calculate_quality_score(workflow),
       }
   ```

6. **Update __init__.py**
   ```python
   from .analytics import (
       get_history_analytics,
       calculate_phase_metrics,
       calculate_workflow_scores,
   )
   ```

**Acceptance Criteria:**
- [ ] analytics.py created with analytics functions
- [ ] Phase metrics calculated correctly
- [ ] History analytics aggregate properly
- [ ] Temporal analytics work
- [ ] Scoring functions integrated
- [ ] Import works from __init__.py

**Verification Commands:**
```bash
# Test analytics
python -c "
from app.server.core.workflow_history.analytics import get_history_analytics
workflows = []  # Would normally load from DB
analytics = get_history_analytics(workflows)
print('Analytics:', analytics)
"
```

**Status:** Not Started
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
