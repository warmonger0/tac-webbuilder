# E2E Test: Pattern Insights UI

## User Story
As a user submitting a workflow request, I want to see pattern predictions in real-time as I type my request, so that I can refine my input before submission for better accuracy and cost efficiency.

## Test Scenario
Validate that pattern insights are displayed correctly in the RequestForm component.

## Prerequisites
- Application running at http://localhost:5173 (or port from .ports.env)
- Backend API running and accessible
- Pattern prediction endpoint (`/api/predict-patterns`) operational

## Test Steps

### Step 1: Navigate to Application
- Action: Open browser to application URL
- Expected: RequestForm loads successfully

### Step 2: Verify Initial State
- Action: Take screenshot of initial RequestForm
- Expected: PatternInsightsPanel shows empty state message ("Start typing to see pattern predictions...")

### Step 3: Type Pattern-Triggering Input
- Action: Type "run backend tests with pytest" into nl_input textarea
- Action: Wait 700ms (500ms debounce + 200ms API response buffer)
- Action: Take screenshot showing PatternInsightsPanel with predictions

### Step 4: Verify Pattern Predictions Display
- Expected: PatternInsightsPanel is visible and expanded
- Expected: At least one PatternBadge is displayed
- Expected: PatternBadge shows "test:pytest:backend" pattern
- Expected: Confidence score is displayed (e.g., "85% High")
- Expected: Badge has green background (high confidence ≥75%)

### Step 5: Verify Similar Workflows (if history exists)
- Expected: If workflow history exists with similar requests, SimilarWorkflowCard components are visible
- Expected: Each card shows similarity score, clarity score (if available), cost (if available), and status

### Step 6: Verify Recommendations
- Expected: "Optimization Tips" section is visible
- Expected: At least one recommendation is displayed
- Expected: Recommendations are relevant (e.g., clarity suggestions, cost estimates)

### Step 7: Test Collapse/Expand Functionality
- Action: Click collapse button (chevron icon) on PatternInsightsPanel header
- Action: Take screenshot showing collapsed state
- Expected: PatternInsightsPanel content is hidden
- Expected: Header still shows pattern count summary

### Step 8: Test Keyboard Shortcut
- Action: Press Cmd+I (Mac) or Ctrl+I (Windows/Linux)
- Expected: PatternInsightsPanel expands
- Action: Take screenshot showing expanded state

### Step 9: Test Different Pattern Types
- Action: Clear textarea
- Action: Type "typecheck frontend code"
- Action: Wait 700ms
- Expected: Pattern predictions update to show "build:typecheck:frontend" or similar
- Expected: Badge color reflects confidence level

### Step 10: Verify Form Submission Still Works
- Action: Click "Generate Preview" button
- Expected: Form submission proceeds normally
- Expected: Pattern insights don't interfere with existing functionality

## Success Criteria
- ✓ Pattern predictions appear within 1 second after typing stops
- ✓ PatternBadge displays pattern signature and confidence with correct color coding
- ✓ Similar workflows display if available
- ✓ Recommendations are generated and displayed
- ✓ Collapse/expand functionality works smoothly
- ✓ Keyboard shortcut (Cmd/Ctrl+I) toggles panel correctly
- ✓ 4+ screenshots captured showing different states
- ✓ No JavaScript errors in browser console
- ✓ Existing RequestForm functionality continues to work

## Cleanup
- Close browser
- No database cleanup required (read-only operations)

## Notes
- Test requires workflow history database to contain similar workflows for full validation of SimilarWorkflowCard feature
- If no history exists, similar workflows section will be empty (expected behavior)
- Debounce delay is 500ms - wait at least 600ms after typing stops before asserting predictions
