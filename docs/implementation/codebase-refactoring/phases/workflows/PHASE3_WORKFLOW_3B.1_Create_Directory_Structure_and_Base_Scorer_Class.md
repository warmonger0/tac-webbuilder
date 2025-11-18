## Workflow 3B.1: Create Directory Structure and Base Scorer Class

**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** None

**Input Files:**
- `app/server/core/workflow_analytics.py` (existing)

**Output Files:**
- `app/server/core/workflow_analytics/__init__.py` (new)
- `app/server/core/workflow_analytics/scoring/__init__.py` (new)
- `app/server/core/workflow_analytics/scoring/base.py` (new)

**Tasks:**

1. **Create directory structure**
   ```bash
   mkdir -p app/server/core/workflow_analytics/scoring
   touch app/server/core/workflow_analytics/__init__.py
   touch app/server/core/workflow_analytics/scoring/__init__.py
   touch app/server/core/workflow_analytics/scoring/base.py
   ```

2. **Rename original file as backup**
   ```bash
   mv app/server/core/workflow_analytics.py app/server/core/workflow_analytics_original.py.bak
   ```

3. **Create base scorer class**
   ```python
   # app/server/core/workflow_analytics/scoring/base.py
   """
   Base class for workflow scoring systems.

   Provides common pattern for all scorers:
   - Calculate base score
   - Apply penalties
   - Apply bonuses
   - Normalize to 0-100 range
   """

   from abc import ABC, abstractmethod
   from typing import Dict, Optional
   import logging

   logger = logging.getLogger(__name__)

   class BaseScorer(ABC):
       """Abstract base class for workflow scoring."""

       def __init__(self, workflow: Dict):
           """
           Initialize scorer with workflow data.

           Args:
               workflow: Workflow data dictionary
           """
           self.workflow = workflow
           self.base_score = 0.0
           self.penalties = 0.0
           self.bonuses = 0.0

       @abstractmethod
       def calculate_base_score(self) -> float:
           """
           Calculate the base score before penalties/bonuses.

           Returns:
               Base score value
           """
           pass

       @abstractmethod
       def apply_penalties(self) -> float:
           """
           Calculate total penalties to subtract from score.

           Returns:
               Total penalty value
           """
           pass

       @abstractmethod
       def apply_bonuses(self) -> float:
           """
           Calculate total bonuses to add to score.

           Returns:
               Total bonus value
           """
           pass

       def calculate(self) -> float:
           """
           Calculate final score with normalization.

           Process:
           1. Calculate base score
           2. Apply penalties
           3. Apply bonuses
           4. Normalize to 0-100 range

           Returns:
               Final score between 0.0 and 100.0
           """
           try:
               self.base_score = self.calculate_base_score()
               self.penalties = self.apply_penalties()
               self.bonuses = self.apply_bonuses()

               # Calculate final score
               final_score = self.base_score - self.penalties + self.bonuses

               # Normalize to 0-100 range
               normalized_score = max(0.0, min(100.0, final_score))

               logger.debug(
                   f"{self.__class__.__name__}: "
                   f"base={self.base_score:.1f}, "
                   f"penalties={self.penalties:.1f}, "
                   f"bonuses={self.bonuses:.1f}, "
                   f"final={normalized_score:.1f}"
               )

               return normalized_score

           except Exception as e:
               logger.error(f"Error calculating {self.__class__.__name__}: {e}")
               return 0.0

       def get_score_breakdown(self) -> Dict:
           """
           Get detailed score breakdown for debugging.

           Returns:
               Dictionary with score components
           """
           return {
               'base_score': self.base_score,
               'penalties': self.penalties,
               'bonuses': self.bonuses,
               'final_score': self.calculate(),
           }
   ```

4. **Create facade __init__.py**
   ```python
   # app/server/core/workflow_analytics/__init__.py
   """
   Workflow Analytics Scoring Engine

   This module provides comprehensive scoring and analysis functions for ADW workflows.
   Refactored from monolithic file into focused submodules.

   Core scoring metrics:
   1. NL Input Clarity Score - Evaluates quality and clarity of natural language inputs
   2. Cost Efficiency Score - Analyzes cost performance including model appropriateness
   3. Performance Score - Measures execution speed and bottleneck detection
   4. Quality Score - Assesses error rates and execution quality

   Additional features:
   - Helper functions for temporal extraction and complexity detection
   - Anomaly detection with configurable thresholds
   - Similar workflow discovery
   - Optimization recommendations
   """

   # Temporary: Import from backup until migration complete
   import sys
   from pathlib import Path

   backup_path = Path(__file__).parent.parent
   if str(backup_path) not in sys.path:
       sys.path.insert(0, str(backup_path))

   from workflow_analytics_original import *

   __all__ = [
       # Helper functions
       'extract_hour',
       'extract_day_of_week',
       'detect_complexity',

       # Scoring functions
       'calculate_nl_input_clarity_score',
       'calculate_cost_efficiency_score',
       'calculate_performance_score',
       'calculate_quality_score',

       # Analysis functions
       'find_similar_workflows',
       'detect_anomalies',
       'generate_optimization_recommendations',
   ]
   ```

5. **Verify imports still work**
   ```bash
   python -c "from app.server.core.workflow_analytics import calculate_nl_input_clarity_score; print('Import successful')"
   ```

**Acceptance Criteria:**
- [ ] Directory structure created
- [ ] Base scorer class implemented
- [ ] Backup file created
- [ ] Temporary imports work
- [ ] All existing tests pass

**Verification Commands:**
```bash
# Verify structure
ls -la app/server/core/workflow_analytics/
ls -la app/server/core/workflow_analytics/scoring/

# Test imports
python -c "
from app.server.core.workflow_analytics.scoring.base import BaseScorer
print('Base scorer import successful')
"

# Run existing tests
cd app/server && pytest tests/test_workflow_analytics.py -v
```

**Status:** Not Started

---
