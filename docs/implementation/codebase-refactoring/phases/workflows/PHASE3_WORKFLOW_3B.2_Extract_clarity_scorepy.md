## Workflow 3B.2: Extract clarity_score.py

**Estimated Time:** 1.5 hours
**Complexity:** Low
**Dependencies:** Workflow 3B.1

**Input Files:**
- `app/server/core/workflow_analytics_original.py.bak` (lines 123-189)

**Output Files:**
- `app/server/core/workflow_analytics/scoring/clarity_score.py` (new)

**Tasks:**

1. **Create clarity_score.py using BaseScorer**
   ```python
   """
   NL Input Clarity Scorer.

   Evaluates the quality and clarity of natural language inputs.

   Scoring criteria:
   - Base: 60.0 (starts at passing grade)
   - Penalties:
     - Very short input (<10 words): -30
     - Short input (10-20 words): -10
     - Very long input (>200 words): -15
     - Empty/missing input: -60
   - Bonuses:
     - Good length (20-150 words): +20
     - Proper capitalization: +10
     - Clear structure (multiple sentences): +10
   """

   import logging
   from typing import Dict
   from .base import BaseScorer

   logger = logging.getLogger(__name__)

   class ClarityScorer(BaseScorer):
       """Scorer for natural language input clarity."""

       def calculate_base_score(self) -> float:
           """Start with base passing score of 60."""
           return 60.0

       def apply_penalties(self) -> float:
           """Apply penalties for clarity issues."""
           penalties = 0.0
           nl_input = self.workflow.get('nl_input', '')

           if not nl_input:
               penalties += 60.0  # Complete failure
               return penalties

           word_count = len(nl_input.split())

           # Length penalties
           if word_count < 10:
               penalties += 30.0  # Very short
           elif word_count < 20:
               penalties += 10.0  # Short

           if word_count > 200:
               penalties += 15.0  # Too verbose

           return penalties

       def apply_bonuses(self) -> float:
           """Apply bonuses for good clarity."""
           bonuses = 0.0
           nl_input = self.workflow.get('nl_input', '')

           if not nl_input:
               return bonuses

           word_count = len(nl_input.split())

           # Good length bonus
           if 20 <= word_count <= 150:
               bonuses += 20.0

           # Capitalization bonus
           if nl_input[0].isupper():
               bonuses += 10.0

           # Structure bonus (multiple sentences)
           sentence_count = nl_input.count('.') + nl_input.count('!') + nl_input.count('?')
           if sentence_count >= 2:
               bonuses += 10.0

           return bonuses


   def calculate_nl_input_clarity_score(workflow: Dict) -> float:
       """
       Calculate NL input clarity score for a workflow.

       This is the public API function that maintains backwards compatibility.

       Args:
           workflow: Workflow data dictionary

       Returns:
           Clarity score from 0.0 to 100.0
       """
       scorer = ClarityScorer(workflow)
       return scorer.calculate()
   ```

2. **Update scoring/__init__.py**
   ```python
   from .clarity_score import calculate_nl_input_clarity_score

   __all__ = [
       'calculate_nl_input_clarity_score',
   ]
   ```

3. **Update main __init__.py**
   ```python
   # Replace temporary import with:
   from .scoring import calculate_nl_input_clarity_score
   ```

**Acceptance Criteria:**
- [ ] ClarityScorer class created
- [ ] Uses BaseScorer pattern
- [ ] calculate_nl_input_clarity_score() function works
- [ ] Backwards compatible API
- [ ] Tests pass

**Verification Commands:**
```bash
python -c "
from app.server.core.workflow_analytics import calculate_nl_input_clarity_score
workflow = {'nl_input': 'This is a test workflow with good clarity and structure.'}
score = calculate_nl_input_clarity_score(workflow)
print(f'Clarity score: {score}')
assert 0 <= score <= 100
"
```

**Status:** Not Started
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
