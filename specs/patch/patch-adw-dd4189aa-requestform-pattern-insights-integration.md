# Patch: RequestForm PatternInsightsPanel Integration

## Metadata
adw_id: `adw-dd4189aa`
review_change_request: `Issue #1: RequestForm component missing PatternInsightsPanel integration - The RequestForm.tsx file does not import PatternInsightsPanel, does not have pattern prediction state variables, does not implement debounced pattern fetching with useEffect, and does not render the PatternInsightsPanel component below the textarea. The entire Task 10 from the spec was not implemented. Resolution: Modify RequestForm.tsx to: (1) Import PatternInsightsPanel and predictPatterns from API client, (2) Add state for patternPredictions, similarWorkflows, recommendations, isPredicting, predictionError, (3) Create debounced useEffect that triggers pattern prediction when nlInput changes (minimum 10 characters), (4) Render PatternInsightsPanel between the textarea (line 314) and FileUploadSection (line 316) with all prediction state passed as props. Severity: blocker`

## Issue Summary
**Original Spec:** `specs/issue-111-adw-adw-dd4189aa-sdlc_planner-phase-2-add-submission-time-pattern-detection.md`
**Issue:** Task 10 "Integrate Pattern Insights into RequestForm" was not implemented. RequestForm.tsx is missing all pattern prediction functionality including imports, state management, debounced API calls, and PatternInsightsPanel rendering.
**Solution:** Add complete pattern prediction integration to RequestForm.tsx following the exact specifications in Task 10 of the original spec.

## Files to Modify
- `app/client/src/components/RequestForm.tsx` - Add pattern prediction state, debounced useEffect, and PatternInsightsPanel rendering

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add imports for pattern prediction functionality
- Import `PatternInsightsPanel` from `./request-form/PatternInsightsPanel`
- Import `predictPatterns` from `../api/client`
- Import `debounce` from `../utils/debounce`
- Import types: `PatternPrediction`, `SimilarWorkflowSummary` from `../types/api.types`

### Step 2: Add pattern prediction state variables
- Add state: `patternPredictions: PatternPrediction[] = []`
- Add state: `similarWorkflows: SimilarWorkflowSummary[] = []`
- Add state: `recommendations: string[] = []`
- Add state: `isPredicting: boolean = false`
- Add state: `predictionError: string | null = null`

### Step 3: Implement debounced pattern prediction fetcher
- Create async function `fetchPatternPredictions(input: string)` that:
  - Sets `isPredicting: true` and `predictionError: null`
  - Calls `predictPatterns(input, projectPath)`
  - Updates state with response: `patternPredictions`, `similarWorkflows`, `recommendations`
  - Handles errors by setting `predictionError`
  - Sets `isPredicting: false`
- Create debounced version with 500ms delay: `debouncedFetchPatterns = debounce(fetchPatternPredictions, 500)`
- Add `useEffect` that triggers when `nlInput` changes:
  - Check if `nlInput.trim().length >= 10` (minimum 10 characters)
  - If true, call `debouncedFetchPatterns(nlInput)`
  - If false, clear predictions state

### Step 4: Render PatternInsightsPanel between textarea and FileUploadSection
- Insert `<PatternInsightsPanel />` component after line 314 (after textarea closing tag) and before line 316 (before FileUploadSection)
- Pass props: `predictions={patternPredictions}`, `similarWorkflows={similarWorkflows}`, `recommendations={recommendations}`, `isLoading={isPredicting}`, `error={predictionError}`
- Add 16px bottom margin (mb-4) to separate from FileUploadSection

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. `cd app/client && bun tsc --noEmit` - Verify TypeScript compilation with no errors
2. `cd app/client && bun run lint` - Verify ESLint passes with no errors
3. `cd app/client && bun run build` - Verify frontend builds successfully
4. `cd app/client && bun test RequestForm` - Run RequestForm tests (if they exist)
5. Manual test in browser:
   - Start app: `./scripts/start.sh`
   - Navigate to http://localhost:5173
   - Type "run backend tests with pytest" in RequestForm textarea
   - Wait 600ms and verify PatternInsightsPanel appears with predictions
   - Verify panel shows pattern badges with confidence scores
   - Verify panel collapses/expands correctly
6. `cd app/server && uv run pytest` - Verify backend tests still pass (no regressions)

## Patch Scope
**Lines of code to change:** ~60-80 lines (imports, state, useEffect, JSX rendering)
**Risk level:** low (isolated to RequestForm.tsx, uses existing tested components)
**Testing required:** TypeScript compilation, frontend build, manual browser testing of pattern prediction flow
