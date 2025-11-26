# Pattern Prediction Implementation Guide

## Status: Backend Complete, Frontend Components Ready

### Completed Implementation

#### Backend (100% Complete)
1. ✅ **Data Models** - `app/server/core/models/`
   - `PatternPrediction`, `SimilarWorkflowSummary`, `PredictPatternsRequest`, `PredictPatternsResponse`
   - All models properly exported from `data_models.py`

2. ✅ **API Endpoint** - `app/server/routes/pattern_routes.py`
   - POST `/api/predict-patterns` endpoint implemented
   - Orchestrates pattern prediction, similarity search, and recommendations
   - Handles errors gracefully
   - Returns structured JSON response

3. ✅ **Router Registration** - `app/server/server.py`
   - Pattern router imported and registered with FastAPI app

4. ✅ **Tests** - `app/server/tests/routes/test_pattern_routes.py`
   - 11 comprehensive test cases covering success, errors, edge cases
   - Tests for empty input, keyword detection, similar workflows, recommendations

#### Frontend (80% Complete)
1. ✅ **Type Definitions** - `app/client/src/types/api.types.ts`
   - All TypeScript interfaces matching backend models

2. ✅ **API Client** - `app/client/src/api/client.ts`
   - `predictPatterns()` function with timeout and error handling

3. ✅ **Utility Functions**
   - `debounce.ts` - Generic debounce with TypeScript generics
   - `patternFormatters.ts` - Pattern display formatting, confidence colors, labels

4. ✅ **React Components**
   - `PatternBadge.tsx` - Displays individual pattern with confidence badge
   - `SimilarWorkflowCard.tsx` - Shows similar workflow summary
   - `PatternInsightsPanel.tsx` - Main panel with collapse/expand, keyboard shortcut

5. ⏳ **RequestForm Integration** - **NEEDS COMPLETION**
   - Components are built but not yet integrated into `RequestForm.tsx`

6. ✅ **E2E Test** - `.claude/commands/e2e/test_pattern_insights.md`
   - Complete test scenario with 10 steps

### Remaining Work: RequestForm Integration

To complete the feature, add to `app/client/src/components/RequestForm.tsx`:

#### 1. Imports (add to top of file)
```typescript
import { predictPatterns } from '../api/client';
import PatternInsightsPanel from './request-form/PatternInsightsPanel';
import { debounce } from '../utils/debounce';
import type { PatternPrediction, SimilarWorkflowSummary } from '../types';
```

#### 2. State Variables (add after existing useState declarations)
```typescript
// Pattern prediction state
const [patternPredictions, setPatternPredictions] = useState<PatternPrediction[]>([]);
const [similarWorkflows, setSimilarWorkflows] = useState<SimilarWorkflowSummary[]>([]);
const [recommendations, setRecommendations] = useState<string[]>([]);
const [isPredicting, setIsPredicting] = useState(false);
const [predictionError, setPredictionError] = useState<string | null>(null);
```

#### 3. Debounced Prediction Fetcher (add after state declarations)
```typescript
// Debounced pattern prediction (500ms delay)
const debouncedPredictPatterns = useRef(
  debounce(async (input: string, path: string) => {
    // Only predict if input is substantial (≥10 characters)
    if (input.trim().length < 10) {
      setPatternPredictions([]);
      setSimilarWorkflows([]);
      setRecommendations([]);
      return;
    }

    setIsPredicting(true);
    setPredictionError(null);

    try {
      const response = await predictPatterns(input, path || undefined);

      if (response.error) {
        setPredictionError(response.error);
      } else {
        setPatternPredictions(response.predictions);
        setSimilarWorkflows(response.similar_workflows);
        setRecommendations(response.recommendations);
      }
    } catch (error) {
      setPredictionError(error instanceof Error ? error.message : 'Failed to predict patterns');
    } finally {
      setIsPredicting(false);
    }
  }, 500)
).current;
```

#### 4. Effect Hook (add after other useEffect hooks)
```typescript
// Trigger pattern prediction when nlInput changes
useEffect(() => {
  if (nlInput.trim().length >= 10) {
    debouncedPredictPatterns(nlInput, projectPath);
  } else {
    // Clear predictions for short input
    setPatternPredictions([]);
    setSimilarWorkflows([]);
    setRecommendations([]);
  }
}, [nlInput, projectPath]);
```

#### 5. Render Component (add after textarea, before FileUploadSection)
```typescript
{/* Pattern Insights Panel */}
<PatternInsightsPanel
  predictions={patternPredictions}
  similarWorkflows={similarWorkflows}
  recommendations={recommendations}
  isLoading={isPredicting}
  error={predictionError}
/>
```

### Testing

#### Backend Tests
```bash
cd app/server
uv run pytest tests/routes/test_pattern_routes.py -v
```

Expected: 11 tests pass

#### Frontend Type Check
```bash
cd app/client
bun tsc --noEmit
```

Expected: No errors

#### E2E Test (after RequestForm integration)
See `.claude/commands/e2e/test_pattern_insights.md` for full test scenario.

### API Endpoint Usage

#### Request
```bash
curl -X POST http://localhost:8000/api/predict-patterns \
  -H "Content-Type: application/json" \
  -d '{
    "nl_input": "Run backend tests with pytest",
    "project_path": null
  }'
```

#### Response
```json
{
  "predictions": [
    {
      "pattern": "test:pytest:backend",
      "confidence": 0.85,
      "reasoning": "Backend test keywords detected"
    }
  ],
  "similar_workflows": [
    {
      "adw_id": "adw-abc123",
      "nl_input": "Run pytest tests on backend API",
      "similarity_score": 85,
      "clarity_score": 72.5,
      "total_cost": 1.25,
      "status": "completed"
    }
  ],
  "recommendations": [
    "💰 Similar requests averaged $1.25 in cost",
    "✅ Your request looks good - clear patterns detected with high confidence"
  ],
  "error": null
}
```

### Architecture Overview

```
User Types in RequestForm
  ↓ (500ms debounce)
POST /api/predict-patterns
  ↓
pattern_routes.predict_patterns()
  ├─ pattern_predictor.predict_patterns_from_input() → predictions
  ├─ get_workflow_history() + similarity calc → similar_workflows
  └─ _generate_recommendations() → recommendations
  ↓
PatternInsightsPanel renders:
  ├─ PatternBadge (foreach prediction)
  ├─ SimilarWorkflowCard (foreach similar workflow)
  └─ Optimization tips (recommendations)
```

### File Inventory

#### Backend Files
- ✅ `app/server/core/models/requests.py` - Added `PredictPatternsRequest`
- ✅ `app/server/core/models/responses.py` - Added `PredictPatternsResponse`
- ✅ `app/server/core/models/workflow.py` - Added `PatternPrediction`, `SimilarWorkflowSummary`
- ✅ `app/server/core/data_models.py` - Re-exports all new models
- ✅ `app/server/routes/pattern_routes.py` - **NEW FILE** - Pattern prediction endpoint
- ✅ `app/server/server.py` - Modified to register pattern router
- ✅ `app/server/tests/routes/__init__.py` - **NEW FILE**
- ✅ `app/server/tests/routes/test_pattern_routes.py` - **NEW FILE** - 11 test cases

#### Frontend Files
- ✅ `app/client/src/types/api.types.ts` - Added pattern prediction types
- ✅ `app/client/src/api/client.ts` - Added `predictPatterns()` function
- ✅ `app/client/src/utils/debounce.ts` - **NEW FILE** - Debounce utility
- ✅ `app/client/src/utils/patternFormatters.ts` - **NEW FILE** - Pattern formatters
- ✅ `app/client/src/components/request-form/PatternBadge.tsx` - **NEW FILE**
- ✅ `app/client/src/components/request-form/SimilarWorkflowCard.tsx` - **NEW FILE**
- ✅ `app/client/src/components/request-form/PatternInsightsPanel.tsx` - **NEW FILE**
- ⏳ `app/client/src/components/RequestForm.tsx` - **NEEDS MODIFICATION** (see above)

#### Documentation
- ✅ `.claude/commands/e2e/test_pattern_insights.md` - **NEW FILE** - E2E test scenario
- ✅ `IMPLEMENTATION_GUIDE.md` - **THIS FILE** - Implementation status and guide

### Code Quality Checks

All code follows standards from:
- `.claude/references/code_quality_standards.md`
- `.claude/references/typescript_standards.md`

Checks performed:
- ✅ No files exceed 800 lines (hard limit)
- ✅ No functions exceed 300 lines (hard limit)
- ✅ Python files use snake_case
- ✅ TypeScript components use PascalCase
- ✅ Type definitions properly organized in api.types.ts
- ✅ No type name collisions

### Next Steps for Completion

1. Integrate PatternInsightsPanel into RequestForm (15-20 min)
   - Add imports, state, debounced fetcher, effect hook, render component
   - Follow integration guide above

2. Test backend endpoint manually (5 min)
   - Start server: `./scripts/start.sh`
   - Test with curl or Postman

3. Test frontend integration (10 min)
   - Navigate to http://localhost:5173
   - Type test inputs and verify predictions appear
   - Check browser console for errors

4. Run validation commands (10 min)
   - Backend tests: `cd app/server && uv run pytest`
   - Frontend lint: `cd app/client && bun run lint`
   - TypeScript check: `cd app/client && bun tsc --noEmit`

5. Run E2E test (10 min)
   - Follow `.claude/commands/e2e/test_pattern_insights.md`

Total estimated completion time: **50-55 minutes**
