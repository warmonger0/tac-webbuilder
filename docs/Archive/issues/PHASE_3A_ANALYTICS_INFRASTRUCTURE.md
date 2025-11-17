# Phase 3A: Analytics Infrastructure (Foundation)

**Status:** Not Started
**Complexity:** LOW
**Estimated Cost:** $0.20-0.30 (Haiku)
**Execution:** **LOCAL CLAUDE CODE** (not ADW)
**Duration:** 15-20 minutes

## Overview

Establish the foundational infrastructure for analytics without implementing complex logic. This phase creates the database schema, type definitions, and module structure that all subsequent phases will build upon.

## Why This Can Run Locally

- **No complex algorithms** - Just structural changes
- **Straightforward SQL** - Standard ALTER TABLE statements
- **Simple type definitions** - Copy/paste from spec
- **No integration complexity** - Just creating empty stubs
- **Fast verification** - Run migration, check types compile

## Dependencies

- Phase 1 completed (UI foundation)
- Phase 2 completed (performance metrics foundation)

## Scope

### 1. Database Migration

**File:** `app/server/db/migrations/003_add_analytics_metrics.sql`

```sql
-- Phase 3A: Add analytics metrics columns to workflow_history table

ALTER TABLE workflow_history ADD COLUMN nl_input_word_count INTEGER;
ALTER TABLE workflow_history ADD COLUMN nl_input_clarity_score REAL;
ALTER TABLE workflow_history ADD COLUMN structured_input_completeness_percent REAL;

ALTER TABLE workflow_history ADD COLUMN submission_hour INTEGER;
ALTER TABLE workflow_history ADD COLUMN submission_day_of_week INTEGER;

ALTER TABLE workflow_history ADD COLUMN pr_merged BOOLEAN DEFAULT 0;
ALTER TABLE workflow_history ADD COLUMN time_to_merge_hours REAL;
ALTER TABLE workflow_history ADD COLUMN review_cycles INTEGER;
ALTER TABLE workflow_history ADD COLUMN ci_test_pass_rate REAL;

ALTER TABLE workflow_history ADD COLUMN cost_efficiency_score REAL;
ALTER TABLE workflow_history ADD COLUMN performance_score REAL;
ALTER TABLE workflow_history ADD COLUMN quality_score REAL;

ALTER TABLE workflow_history ADD COLUMN similar_workflow_ids TEXT;
ALTER TABLE workflow_history ADD COLUMN anomaly_flags TEXT;
ALTER TABLE workflow_history ADD COLUMN optimization_recommendations TEXT;
```

### 2. Backend Module Structure

**File:** `app/server/core/workflow_analytics.py`

```python
"""
Advanced analytics engine for workflow history.
Provides pattern detection, scoring, and optimization recommendations.

This module is the foundation for Phase 3 analytics features.
Phase 3B will implement the actual scoring logic.
"""

from typing import Dict, List, Optional


def calculate_nl_input_clarity_score(nl_input: str) -> float:
    """
    Calculate NL input clarity score (0-100).

    Score based on:
    - Length (sweet spot: 50-300 words)
    - Presence of acceptance criteria keywords
    - Technical specificity
    - Question vs statement ratio

    Args:
        nl_input: Natural language input text

    Returns:
        Score from 0-100 (higher is better)

    TODO: Implement in Phase 3B
    """
    return 0.0


def calculate_cost_efficiency_score(workflow: Dict) -> float:
    """
    Calculate cost efficiency score (0-100).

    Score based on:
    - Actual vs estimated cost (penalty for over-budget)
    - Cache efficiency (bonus for high cache hit rate)
    - Retry rate (penalty for retries)
    - Model selection appropriateness

    Args:
        workflow: Workflow data dictionary

    Returns:
        Score from 0-100 (higher is better)

    TODO: Implement in Phase 3B
    """
    return 0.0


def calculate_performance_score(workflow: Dict, similar_workflows: List[Dict]) -> float:
    """
    Calculate performance score (0-100) by comparing to similar workflows.

    Score based on:
    - Duration vs average for same template
    - Bottleneck presence
    - Idle time percentage

    Args:
        workflow: Current workflow data
        similar_workflows: List of similar workflow data dictionaries

    Returns:
        Score from 0-100 (higher is better)

    TODO: Implement in Phase 3B
    """
    return 0.0


def calculate_quality_score(workflow: Dict) -> float:
    """
    Calculate quality score (0-100).

    Score based on:
    - Error rate during execution
    - Retry count
    - PR review cycles
    - CI test pass rate

    Args:
        workflow: Workflow data dictionary

    Returns:
        Score from 0-100 (higher is better)

    TODO: Implement in Phase 3B
    """
    return 0.0


def find_similar_workflows(workflow: Dict, all_workflows: List[Dict]) -> List[str]:
    """
    Find similar workflows based on multiple criteria.

    Similarity based on:
    - Same classification type
    - Same workflow template
    - Similar complexity metrics
    - Similar nl_input (cosine similarity)

    Args:
        workflow: Current workflow data
        all_workflows: All historical workflows

    Returns:
        List of ADW IDs for similar workflows

    TODO: Implement in Phase 3E
    """
    return []


def detect_anomalies(workflow: Dict, historical_data: List[Dict]) -> List[str]:
    """
    Detect anomalies in workflow execution.

    Anomalies include:
    - Cost >2x average for similar workflows
    - Duration >2x average
    - Unusually high retry count
    - Unexpected error category

    Args:
        workflow: Current workflow data
        historical_data: Historical workflow data for comparison

    Returns:
        List of anomaly descriptions (empty if no anomalies)

    TODO: Implement in Phase 3D
    """
    return []


def generate_optimization_recommendations(workflow: Dict) -> List[str]:
    """
    Generate actionable optimization recommendations.

    Examples:
    - "Consider using Haiku model for similar simple features"
    - "Cache efficiency is low - review prompt structure"
    - "Build phase is bottleneck - consider splitting into subtasks"
    - "NL input lacks acceptance criteria - improves with explicit criteria"

    Args:
        workflow: Workflow data dictionary

    Returns:
        List of recommendation strings (empty if none)

    TODO: Implement in Phase 3D
    """
    return []
```

### 3. Python Type Updates

**File:** `app/server/core/data_models.py`

Add fields to `WorkflowHistoryItem` model:

```python
class WorkflowHistoryItem(BaseModel):
    # ... existing fields ...

    # Input quality metrics (Phase 3A)
    nl_input_word_count: Optional[int] = None
    nl_input_clarity_score: Optional[float] = None
    structured_input_completeness_percent: Optional[float] = None

    # Temporal patterns (Phase 3A)
    submission_hour: Optional[int] = None
    submission_day_of_week: Optional[int] = None

    # Outcome tracking (Phase 3A)
    pr_merged: Optional[bool] = None
    time_to_merge_hours: Optional[float] = None
    review_cycles: Optional[int] = None
    ci_test_pass_rate: Optional[float] = None

    # Efficiency scores (Phase 3A)
    cost_efficiency_score: Optional[float] = None
    performance_score: Optional[float] = None
    quality_score: Optional[float] = None

    # Pattern metadata (Phase 3A)
    similar_workflow_ids: Optional[List[str]] = None
    anomaly_flags: Optional[List[str]] = None
    optimization_recommendations: Optional[List[str]] = None
```

### 4. TypeScript Type Updates

**File:** `app/client/src/types/api.types.ts`

Add to `WorkflowHistoryItem` interface:

```typescript
export interface WorkflowHistoryItem {
  // ... existing fields ...

  // Input quality metrics
  nl_input_word_count?: number;
  nl_input_clarity_score?: number;
  structured_input_completeness_percent?: number;

  // Temporal patterns
  submission_hour?: number;
  submission_day_of_week?: number;

  // Outcome tracking
  pr_merged?: boolean;
  time_to_merge_hours?: number;
  review_cycles?: number;
  ci_test_pass_rate?: number;

  // Efficiency scores
  cost_efficiency_score?: number;
  performance_score?: number;
  quality_score?: number;

  // Pattern metadata
  similar_workflow_ids?: string[];
  anomaly_flags?: string[];
  optimization_recommendations?: string[];
}
```

## Acceptance Criteria

- [ ] Migration file `003_add_analytics_metrics.sql` created
- [ ] Migration runs successfully without errors
- [ ] All 16 new columns added to `workflow_history` table
- [ ] `workflow_analytics.py` module created with all function stubs
- [ ] Module imports successfully in Python
- [ ] Python types updated in `data_models.py`
- [ ] TypeScript types updated in `api.types.ts`
- [ ] No TypeScript compilation errors
- [ ] No Python import errors
- [ ] Backend server starts without errors
- [ ] Frontend builds without errors

## Testing

### Database Migration Test

```bash
# Run migration
sqlite3 app/server/workflows.db < app/server/db/migrations/003_add_analytics_metrics.sql

# Verify columns exist
sqlite3 app/server/workflows.db "PRAGMA table_info(workflow_history);" | grep -E "(clarity_score|cost_efficiency|performance_score)"
```

### Module Import Test

```bash
# Test Python imports
cd app/server
uv run python -c "from core.workflow_analytics import calculate_nl_input_clarity_score; print('OK')"
```

### Type Check Test

```bash
# TypeScript
cd app/client
bun run typecheck

# Python (if using mypy)
cd app/server
uv run mypy core/data_models.py
```

## Verification Steps

1. Create all files
2. Run database migration
3. Check database schema: `sqlite3 workflows.db "PRAGMA table_info(workflow_history);"`
4. Import analytics module: `python -c "import core.workflow_analytics"`
5. Run TypeScript build: `cd app/client && bun run build`
6. Start backend: `cd app/server && uv run python server.py`
7. Verify no errors in startup logs

## Files to Create

- `app/server/db/migrations/003_add_analytics_metrics.sql`
- `app/server/core/workflow_analytics.py`

## Files to Modify

- `app/server/core/data_models.py` (add fields to WorkflowHistoryItem)
- `app/client/src/types/api.types.ts` (add fields to WorkflowHistoryItem)

## Time Estimate

- Database migration: 5 minutes
- Module creation: 5 minutes
- Type updates: 5 minutes
- Testing/verification: 5 minutes
- **Total: 20 minutes**

## Next Phase

After Phase 3A is complete:
- **Phase 3B** will implement the actual scoring logic
- All infrastructure will be in place to support analytics features
- Types will prevent errors during implementation

## Notes

- This phase intentionally has NO business logic
- All functions return default values (0.0, empty lists)
- Focus is on **structure, not implementation**
- Enables parallel development of later phases
- Can be completed quickly with high confidence
- No risk of breaking existing functionality

## Why Run This Locally (Not ADW)?

1. **Extremely simple** - Just SQL and type definitions
2. **No complex logic** - Nothing to test beyond compilation
3. **Fast feedback** - Can verify in minutes
4. **Low risk** - Only additive changes
5. **Not worth ADW overhead** - ADW setup takes longer than the task itself
6. **Perfect for interactive work** - Quick iteration if any adjustments needed

## Recommended Approach

```bash
# Run locally with Claude Code in interactive mode
# Estimated time: 15-20 minutes
# Estimated cost: $0.20-0.30

1. Create migration file
2. Create analytics module with stubs
3. Update Python types
4. Update TypeScript types
5. Run migration
6. Test imports
7. Verify builds
8. Commit changes
```

## Success Metrics

- Migration runs without errors
- All types compile
- Server starts normally
- Frontend builds normally
- Git commit created with all changes
- Ready for Phase 3B implementation
