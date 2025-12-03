# E2E Test: Cost Per Completion Metric Display

## Test Objective
Validate that the new "Average Cost Per Successful Completion" metric displays correctly in the History panel with trend indicators and expandable phase breakdown.

## Prerequisites
- Application is running (frontend + backend)
- Test database has at least one completed workflow with cost data
- Browser automation tools are available (Playwright)

## Test Steps

### Step 1: Navigate to Application
- Open browser and navigate to application URL (typically http://localhost:5173)
- Wait for page to load completely
- Verify homepage renders without errors

### Step 2: Navigate to History Panel
- Click on "History" tab in the navigation
- Wait for History panel (Panel 3) to load
- Verify workflow history table is visible

### Step 3: Verify Analytics Summary Section
- Scroll to "Analytics Summary" section at top of History panel
- Verify section has heading "Analytics Summary"
- Verify grid layout displays metrics

### Step 4: Verify "Avg Cost/Success" Metric
- Locate the "Avg Cost/Success" stat in the analytics grid
- Verify metric displays in format: "$X.XXX" (3 decimal places)
- Verify label reads "Avg Cost/Success"
- Take screenshot: `analytics-summary-with-cost-per-success.png`

### Step 5: Verify Trend Indicator (if data available)
- Check if trend indicator appears below the "Avg Cost/Success" value
- If visible, verify it shows:
  - Arrow character (↑ for up, ↓ for down, → for neutral)
  - Percentage change (e.g., "+5.2%" or "-3.1%")
  - Appropriate color:
    - Green for cost decrease (↓)
    - Red for cost increase (↑)
    - Gray for neutral (→)
- Take screenshot: `cost-trend-indicator.png`

### Step 6: Test CostPerCompletionMetric Component (if implemented)
- Look for "View Details" button or expanded metric section
- If present, click to expand detailed view
- Verify expanded view shows:
  - Larger metric display
  - Period toggle buttons (7d, 30d, All Time)
  - Completion count and total cost context
  - "Phase Cost Breakdown" section (if available)

### Step 7: Test Phase Breakdown Expansion
- If "Phase Cost Breakdown" section exists, click to expand it
- Verify phase breakdown displays:
  - List of phases sorted by cost (descending)
  - Cost value for each phase
  - Horizontal bar chart showing percentage
  - Workflow count per phase
  - Percentage of total cost
- Take screenshot: `phase-cost-breakdown-expanded.png`

### Step 8: Test Period Toggle
- If period toggle exists (7d/30d/All), click on "30d" button
- Wait for metric to update
- Verify metric value changes (if data differs)
- Verify trend indicator updates
- Take screenshot: `cost-metric-30d-view.png`

### Step 9: Verify Responsive Behavior
- Resize browser window to mobile width (< 768px)
- Verify analytics grid adapts to 2 columns on mobile
- Verify "Avg Cost/Success" metric remains readable
- Verify trend indicator doesn't overflow

### Step 10: Test Empty State
- If no completed workflows exist, verify:
  - Metric displays "$0.000"
  - Message indicates "No successful completions in this period"
  - No trend indicator shown (or shows "N/A")

## Expected Results

### Success Criteria
- ✅ "Avg Cost/Success" metric appears as 6th stat in analytics grid
- ✅ Metric displays cost with 3 decimal places ($0.XXX format)
- ✅ Trend indicator shows correct arrow direction and color
- ✅ Trend percentage displays with + or - sign
- ✅ Phase breakdown expands/collapses correctly
- ✅ Period toggle switches between 7d/30d/all correctly
- ✅ All screenshots captured successfully
- ✅ No console errors during interaction
- ✅ Responsive layout works on mobile

### Screenshots to Capture
1. `analytics-summary-with-cost-per-success.png` - Overview of analytics with new metric
2. `cost-trend-indicator.png` - Close-up of trend indicator
3. `phase-cost-breakdown-expanded.png` - Expanded phase breakdown view
4. `cost-metric-30d-view.png` - Metric after toggling to 30-day period

## Failure Scenarios

### If Metric Not Visible
- Check if backend analytics endpoint is returning new fields
- Verify TypeScript types are updated
- Check browser console for errors
- Verify component import paths are correct

### If Trend Indicator Missing
- Check if `cost_trend_7d` field is present in analytics data
- Verify trend calculation logic in utils/trendCalculations.ts
- Check if TrendIndicator component is imported correctly

### If Phase Breakdown Empty
- Verify workflows have `cost_breakdown` JSON field populated
- Check backend phase aggregation function
- Verify API endpoint includes `include_breakdown=true` parameter

## Cleanup
- Close browser
- Save all screenshots to test artifacts directory
- Document any failures or unexpected behavior
- Report test status (passed/failed)

## Notes
- This test validates the complete user journey for the new cost metric
- Test can be run manually or automated with Playwright
- Screenshots provide visual proof of correct implementation
- Test should be run with real workflow data for accurate validation
