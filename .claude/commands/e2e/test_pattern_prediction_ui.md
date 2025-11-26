# E2E Test: Pattern Prediction UI

**Test ID:** e2e_pattern_prediction_ui
**Feature:** Phase 1 - Pattern Prediction Display
**Objective:** Verify that predicted patterns are displayed correctly in the UI after submitting a request

## Prerequisites

- Application is running (backend on port 8000, frontend on port 5173)
- Database migration 010 has been applied
- Pattern prediction is enabled

## Test Steps

### 1. Navigate to Application

Navigate to the application URL (http://localhost:5173) and take a screenshot of the initial state.

### 2. Enter Test Request

In the "Natural Language Input" field, enter the following test request:
```
Run backend pytest tests with coverage reporting
```

Take a screenshot showing the input field populated.

### 3. Submit Request

Click the "Generate Issue" button to submit the request.

Wait for the request to be processed (loading indicator should appear).

### 4. Verify Predicted Patterns Section

After the preview loads, verify that:

1. **Predicted Patterns Section Appears**
   - A section with the heading "🎯 Detected Patterns" should be visible
   - The section should have an emerald-colored background (emerald-500/10)
   - The section should appear above the Cost Estimate card

2. **Pattern Badges Display**
   - At least one pattern badge should be visible
   - The badge for "test:pytest:backend" should be present
   - Badge should have emerald text color (text-emerald-300)
   - Badge should have emerald background (bg-emerald-500/20)

3. **Confidence Scores Display**
   - Each pattern should have a confidence percentage displayed
   - Confidence should be shown in gray text (text-gray-400)
   - Confidence for "test:pytest:backend" should be between 65-85%

Take a screenshot showing the predicted patterns section.

### 5. Verify Pattern Details

Inspect the pattern prediction display and verify:

- Pattern name is readable and correctly formatted
- Confidence percentage is displayed as a whole number (e.g., "85%")
- Multiple patterns (if predicted) are displayed side-by-side with proper spacing
- The emerald color scheme is consistent with success/detection states

### 6. Test Alternative Input

Cancel the current request and submit a new request:
```
Build and deploy the frontend application to production
```

Verify that:
- Different patterns are predicted (e.g., "build:typecheck:backend", "deploy:production")
- UI updates correctly with new patterns
- Styling remains consistent

Take a screenshot of the new predicted patterns.

### 7. Test No Patterns Scenario

Submit a request that should not trigger any pattern predictions:
```
Update the README documentation with installation instructions
```

Verify that:
- No "Detected Patterns" section appears
- Preview still loads correctly
- No visual errors or broken UI elements

## Success Criteria

- ✅ Predicted patterns section renders correctly
- ✅ Pattern badges are visible with proper styling
- ✅ Confidence scores display as percentages
- ✅ Multiple patterns display side-by-side
- ✅ Emerald color scheme is applied consistently
- ✅ Section appears above Cost Estimate card
- ✅ UI handles cases with no predictions gracefully
- ✅ Screenshots capture all key UI states

## Expected Screenshots

1. `pattern_prediction_initial.png` - Initial application state
2. `pattern_prediction_input.png` - Test input entered
3. `pattern_prediction_display.png` - Predicted patterns displayed
4. `pattern_prediction_alternative.png` - Alternative patterns displayed

## Failure Scenarios

If any of these occur, the test fails:

- Predicted patterns section does not appear
- Pattern badges are not visible or incorrectly styled
- Confidence scores are missing or incorrectly formatted
- Section does not appear above Cost Estimate
- UI breaks when no patterns are predicted
- Colors do not match emerald scheme

## Notes

- This test validates Phase 1 implementation of pattern prediction UI
- Pattern prediction accuracy is tested separately in backend tests
- Future phases will add pattern validation and analytics
