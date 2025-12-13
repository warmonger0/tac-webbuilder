# Using Pattern Predictions - Quick Start Guide

**Status:** ✅ Feature Active (Phase 2 Complete)
**Last Updated:** 2025-12-01

## Overview

Pattern prediction automatically detects operation types from your natural language input and displays them in the queue UI. This helps you understand what operations each phase will perform and enables future optimizations.

## How It Works

1. **Submission:** When you submit a request, the system analyzes your natural language input
2. **Detection:** Keywords trigger pattern predictions (e.g., "test" → `test:pytest:backend`)
3. **Display:** Predicted patterns appear as badges when you expand phases in the queue
4. **Learning:** The system tracks prediction accuracy over time

## Pattern Types & Triggers

### Test Patterns

**Keywords:** `test`, `pytest`, `vitest`, `unit test`, `integration test`, `e2e`

**Predictions:**
- `test:pytest:backend` (85% confidence if "pytest" mentioned, 65% otherwise)
- `test:vitest:frontend` (85% confidence if "vitest" mentioned, 65% otherwise)

**Examples:**
```
✅ "Run backend tests with pytest"
   → test:pytest:backend (85%)

✅ "Test all API endpoints"
   → test:pytest:backend (65%)

✅ "Run frontend component tests"
   → test:vitest:frontend (65%)

✅ "Run vitest tests for the UI"
   → test:vitest:frontend (85%)
```

### Build Patterns

**Keywords:** `build`, `compile`, `typecheck`, `tsc`, `typescript`

**Predictions:**
- `build:typecheck:backend` (75% confidence)

**Examples:**
```
✅ "Build the backend and check types"
   → build:typecheck:backend (75%)

✅ "Run TypeScript compiler"
   → build:typecheck:backend (75%)
```

### Deploy Patterns

**Keywords:** `deploy`, `ship`, `release`, `publish`, `production`, `staging`

**Predictions:**
- `deploy:production` (70% confidence)

**Examples:**
```
✅ "Deploy to production environment"
   → deploy:production (70%)

✅ "Ship the new feature"
   → deploy:production (70%)
```

### Fix Patterns

**Keywords:** `fix`, `bug`, `patch`, `hotfix`

**Predictions:**
- `fix:bug` (60% confidence)

**Examples:**
```
✅ "Fix authentication bug in login"
   → fix:bug (60%)

✅ "Patch the security vulnerability"
   → fix:bug (60%)
```

## Step-by-Step Usage

### 1. Access the UI

Navigate to: **http://localhost:5173**

### 2. Submit a Request

Enter natural language input with pattern keywords:

**Single-Phase Example:**
```
Run backend tests with pytest and fix any failures
```

**Multi-Phase Example:**
```
Phase 1: Run backend tests with pytest
Phase 2: Build and validate TypeScript types
Phase 3: Deploy to staging environment
```

### 3. Navigate to Queue

Click on **"Queue"** or **"ZTE Hopper"** tab

### 4. Expand Phase Details

Click the **▼ (expand)** button on any phase card

### 5. View Pattern Badges

Look for the **"Patterns:"** section with emerald-colored badges:

```
Patterns: [test:pytest:backend] [build:typecheck:backend]
```

## UI Features

### Pattern Badge Styling
- **Background:** Emerald translucent (emerald-500/20)
- **Text:** Emerald bright (emerald-300)
- **Border:** Emerald outline (emerald-500/30)
- **Size:** Small text (text-xs)
- **Shape:** Rounded corners (rounded-md)

### Conditional Display
- Pattern section **only appears** when patterns exist
- No clutter for phases without patterns
- Badges wrap gracefully with multiple patterns

### Persistence
- Patterns persist through status changes (queued → ready → running → completed)
- Stored in `phase_data.predicted_patterns`

## Testing Pattern Predictions

### Test 1: Single Pattern Detection
```
Input: "Run backend tests with pytest"
Expected: test:pytest:backend (85%)
```

### Test 2: Multiple Pattern Detection
```
Input: "Run all tests, build, and deploy"
Expected:
  - test:pytest:backend (65%)
  - test:vitest:frontend (65%)
  - build:typecheck:backend (75%)
  - deploy:production (70%)
```

### Test 3: No Pattern Detection
```
Input: "Update documentation and review changes"
Expected: No pattern badges displayed
```

### Test 4: Multi-Phase Patterns
```
Input:
  Phase 1: Run backend tests with pytest
  Phase 2: Build and validate types
  Phase 3: Deploy to production

Expected:
  Phase 1: test:pytest:backend (85%)
  Phase 2: build:typecheck:backend (75%)
  Phase 3: deploy:production (70%)
```

## Architecture

### Backend Components
- **`app/server/core/pattern_predictor.py`** - Prediction logic
- **`app/server/services/github_issue_service.py`** - Integration point
- **Database:** Pattern predictions stored in `pattern_predictions` table

### Frontend Components
- **`app/client/src/components/PhaseQueueCard.tsx`** - Pattern display (lines 178-192)
- **Type:** `PhaseQueueItem.phase_data.predicted_patterns?: string[]`

### Pattern Flow
```
User Input
    ↓
predict_patterns_from_input()
    ↓
store_predicted_patterns()
    ↓
multi_phase_handler passes patterns to queue
    ↓
PhaseQueueCard displays badges
```

## Confidence Scores

### What They Mean
- **85%:** Explicit keyword match (e.g., "pytest" in input)
- **75%:** Strong keyword match (build/typecheck)
- **70%:** Moderate keyword match (deploy/release)
- **65%:** Generic keyword match (e.g., "test" without tool name)
- **60%:** Weak keyword match (fix/bug)

### How They're Used
- Displayed internally (not shown in UI by design)
- Used for validation after workflow completion
- Improves prediction accuracy over time

## Advanced Features

### Pattern Validation (Phase 4 - Not Yet Implemented)
After workflow completion, the system will:
1. Compare predicted patterns vs. actual patterns detected
2. Calculate prediction accuracy
3. Update confidence scores based on validation results

### Pattern Dashboard (Phase 5 - Not Yet Implemented)
Future observability panel will show:
- Total patterns learned
- Prediction accuracy over time
- Top patterns by frequency
- Recent pattern discoveries

## Troubleshooting

### Patterns Not Showing

**Issue:** Submitted request but no patterns displayed

**Solutions:**
1. Check backend logs for pattern prediction errors:
   ```bash
   cd app/server && tail -f server.log | grep "Predictor"
   ```
2. Verify request contains pattern keywords
3. Ensure phase is expanded (click ▼ button)
4. Check browser console for errors

### Wrong Patterns Detected

**Issue:** Patterns don't match intent

**Explanation:** The predictor uses keyword matching. To improve:
1. Use specific tool names ("pytest" instead of "test")
2. Include scope keywords ("backend", "frontend")
3. The system learns from validation (future feature)

### Pattern Section Always Empty

**Issue:** Pattern section visible but no badges

**Solutions:**
1. Check `phase_data.predicted_patterns` exists:
   ```bash
   sqlite3 app/server/data/workflow_history.db
   SELECT queue_id, phase_data FROM phase_queue LIMIT 5;
   ```
2. Verify PhaseQueueCard component receiving correct props
3. Check browser console for React errors

## API Reference

### Backend

**Predict patterns:**
```python
from core.pattern_predictor import predict_patterns_from_input

predictions = predict_patterns_from_input(
    nl_input="Run backend tests with pytest",
    project_path="/path/to/project"  # Optional
)
# Returns: [{'pattern': 'test:pytest:backend', 'confidence': 0.85, 'reasoning': '...'}]
```

**Store predictions:**
```python
from core.pattern_predictor import store_predicted_patterns

store_predicted_patterns(
    request_id="req-123",
    predictions=predictions,
    db_connection=conn
)
```

### Frontend

**PhaseQueueItem type:**
```typescript
interface PhaseQueueItem {
  queue_id: string;
  phase_data: {
    title: string;
    content: string;
    predicted_patterns?: string[];  // Pattern signatures
  };
  // ... other fields
}
```

## Related Documentation

- **Implementation Plan:** `docs/pattern_recognition/PATTERN_RECOGNITION_IMPLEMENTATION_PLAN.md`
- **Phase 1 Verification:** `docs/pattern_recognition/PHASE_1_VERIFICATION.md`
- **E2E Test Guide:** `.claude/commands/e2e/test_pattern_predictions_queue.md`
- **Pattern Predictor Source:** `app/server/core/pattern_predictor.py`

## Current Status

- ✅ **Phase 1:** Post-workflow pattern collection (Complete)
- ✅ **Phase 2:** Submission-time pattern detection (Complete)
- ⏳ **Phase 3:** Queue integration (Complete - this is the active feature!)
- 🔜 **Phase 4:** Validation loop (Not yet implemented)
- 🔜 **Phase 5:** Observability dashboard (Not yet implemented)

## Next Steps

To get the most out of pattern predictions:

1. **Submit requests** with clear operation keywords
2. **Expand phases** in the queue to see patterns
3. **Validate predictions** by checking if they match actual operations
4. **Provide feedback** if predictions are inaccurate (helps future improvements)

---

**Quick Links:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- GitHub Issues: https://github.com/[your-org]/tac-webbuilder/issues
