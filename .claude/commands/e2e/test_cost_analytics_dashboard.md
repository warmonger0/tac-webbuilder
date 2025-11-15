# E2E Test: Cost Analytics Dashboard

## User Story
As a user, I want to view comprehensive cost analytics for workflow executions in an intuitive dashboard format, so that I can understand spending patterns, optimize cache usage, track budget adherence, and identify cost-saving opportunities across all workflow phases.

## Test Steps

### Step 1: Navigate to Application and Verify Initial State
1. Navigate to `http://localhost:5173`
2. Wait for the workflow history panel to load
3. Take screenshot: `01-workflow-history-initial.png`
4. Verify workflow history cards are visible

### Step 2: Locate and Expand Workflow with Full Cost Data
1. Identify a completed workflow card (status: completed)
2. Look for workflows with actual_cost_total > 0 and preferably cost_breakdown data
3. Click the "Show Details" button to expand the workflow card
4. Wait for expanded details to render
5. Take screenshot: `02-workflow-expanded-overview.png`

### Step 3: Verify Cost Economics Section
1. Scroll to and verify "💰 Cost Economics" section header is visible
2. Verify CostBreakdownChart is rendered (bar chart showing costs by phase)
3. Verify CumulativeCostChart is rendered (area chart showing cumulative costs)
4. Verify "Budget Comparison" subsection displays:
   - Estimated Total cost card (blue)
   - Actual Total cost card (green)
   - Budget Delta card (color-coded: green for under, red for over, gray for neutral)
   - Delta displays both dollar amount and percentage
5. Verify "Estimated per Step" and "Actual per Step" cards are visible
6. Take screenshot: `03-cost-economics-section.png`
7. Take screenshot focused on charts: `04-cost-charts.png`

### Step 4: Verify Token Analysis Section
1. Scroll to and verify "🔢 Token Analysis" section header is visible
2. Verify TokenBreakdownChart is rendered (donut chart with token types)
3. Verify total token count is formatted with K/M notation (e.g., "45.2K")
4. Verify CacheEfficiencyBadge is displayed with:
   - Cache efficiency percentage
   - Cache savings amount in dollars
   - Appropriate color coding and emoji icon
5. Verify "Cache Hit/Miss Ratio" visualization:
   - Progress bar showing green (hits) vs orange (misses)
   - Percentage label on progress bar
   - Hit and miss token counts displayed below
6. Verify "Token Details" table shows:
   - Input, Output, Cached, Total token counts
7. Take screenshot: `05-token-analysis-section.png`
8. Take screenshot focused on TokenBreakdownChart: `06-token-breakdown-chart.png`

### Step 5: Verify Cost of Errors Section (If Applicable)
1. If the workflow has retry_count > 0 OR status = 'failed':
   - Verify "⚠️ Cost of Errors" section header is visible
   - Verify error message is displayed in red-bordered card
   - Verify "Retries Required" card shows retry count
   - Verify retry cost impact is calculated and displayed
   - Take screenshot: `07-cost-of-errors-section.png`
2. If the workflow has retry_count = 0 AND status != 'failed':
   - Verify "Cost of Errors" section is NOT displayed

### Step 6: Verify Resource Usage Section
1. Scroll to and verify "💾 Resource Usage" section header is visible
2. Verify resource metrics are displayed:
   - Backend Port (if available)
   - Frontend Port (if available)
   - Concurrent Workflows
   - Worktree Reused (Yes/No)
3. Take screenshot: `08-resource-usage-section.png`

### Step 7: Verify Structured Input Section
1. Scroll to and verify "📋 Structured Input" section header is visible
2. Verify formatted view displays extracted fields:
   - Issue number (if present)
   - Classification badge (if present)
   - Workflow name (if present)
   - Model name (if present)
3. Verify "View Raw JSON" collapsible section is present
4. Click "View Raw JSON" to expand
5. Verify raw JSON is displayed in formatted code block
6. Take screenshot: `09-structured-input-section.png`

### Step 8: Verify Full Dashboard View
1. Scroll to top of expanded details
2. Ensure all four sections are visible in viewport or scroll through them
3. Take screenshot showing full dashboard layout: `10-full-dashboard-layout.png`

### Step 9: Test Responsive Layout - Mobile View
1. Resize browser window to mobile width (375px or use device emulation for iPhone)
2. Verify single-column layout for charts and cards
3. Verify all sections remain accessible and readable
4. Verify no horizontal scrolling on section content (except code blocks)
5. Take screenshot: `11-mobile-layout.png`
6. Scroll through sections to verify responsive behavior
7. Take screenshot of Token Analysis on mobile: `12-mobile-token-analysis.png`

### Step 10: Test Responsive Layout - Desktop View
1. Resize browser window to desktop width (1920px)
2. Verify two-column grid layout for charts within Cost Economics and Token Analysis sections
3. Verify spacing and padding are appropriate
4. Take screenshot: `13-desktop-layout.png`

### Step 11: Test Workflow Without Cost Breakdown
1. Collapse current workflow card (click "Hide Details")
2. Find and expand an older workflow that may not have cost_breakdown.by_phase data
3. Verify graceful degradation message appears:
   "Cost breakdown by phase is not available for this workflow (may be from an older execution)"
4. Verify other sections (Token Analysis, Resource Usage) still render correctly
5. Take screenshot: `14-workflow-without-cost-breakdown.png`

### Step 12: Verify No Console Errors
1. Open browser developer console
2. Check for JavaScript errors or React warnings
3. Verify no error messages related to chart rendering or data formatting
4. Verify no "key" prop warnings or other React issues
5. Take screenshot of clean console: `15-console-no-errors.png`

### Step 13: Collapse and Re-expand Workflow
1. Click "Hide Details" to collapse the expanded view
2. Verify expanded section is hidden
3. Click "Show Details" again to re-expand
4. Verify all sections render correctly on re-expansion
5. Verify charts and visualizations load properly

## Success Criteria

✅ **Section Rendering**
- All four sections render when workflow has complete data: Cost Economics, Token Analysis, Resource Usage, Structured Input
- Cost of Errors section appears conditionally based on retry_count and status
- Section headers display with appropriate emoji icons

✅ **Chart Integration**
- CostBreakdownChart displays per-phase cost bars with correct colors
- CumulativeCostChart shows area chart with cost progression
- TokenBreakdownChart renders donut chart with token type breakdown
- All charts use Recharts library consistently

✅ **Budget Comparison**
- Estimated vs Actual costs display in separate cards
- Budget delta shows correct color coding (green/red/gray) based on status
- Delta displays both absolute cost and percentage
- Per-step comparison displays correctly

✅ **Cache Efficiency**
- CacheEfficiencyBadge displays with correct efficiency percentage
- Cache savings amount calculated and displayed
- Cache hit/miss ratio progress bar shows correct percentages
- Token Details table shows all token types

✅ **Error Section**
- Only displays when retry_count > 0 OR status = 'failed'
- Error message displays in red-bordered card
- Retry count and cost impact calculated correctly
- Shows appropriate message when retries didn't cause budget overrun

✅ **Responsive Layout**
- Desktop view uses 2-column grid for charts (lg:grid-cols-2)
- Mobile view uses single-column stacking (grid-cols-1)
- All content remains readable and accessible at all breakpoints
- No horizontal overflow on mobile (except intentional code blocks)

✅ **Graceful Degradation**
- Workflows without cost_breakdown.by_phase show fallback message
- Missing cache efficiency data doesn't break rendering
- Workflows with zero tokens show "No token data available"
- All conditional sections handle missing data properly

✅ **Structured Input Enhancement**
- Formatted view extracts and displays key fields (issue, classification, workflow, model)
- Raw JSON view is collapsible via <details> element
- Both views render correctly and are accessible

✅ **No Errors**
- Console shows no JavaScript errors
- No React warnings about keys, props, or rendering
- Charts render without errors
- All data transformations work correctly

✅ **User Experience**
- Expand/collapse behavior works smoothly
- All sections visible and well-organized
- Color coding is consistent and meaningful
- Text is readable with good contrast
- Interactive elements (details/summary) work correctly

## Expected Screenshots
1. `01-workflow-history-initial.png` - Initial view of workflow history panel
2. `02-workflow-expanded-overview.png` - Full expanded view of workflow card
3. `03-cost-economics-section.png` - Cost Economics section with budget comparison
4. `04-cost-charts.png` - Close-up of CostBreakdownChart and CumulativeCostChart
5. `05-token-analysis-section.png` - Token Analysis section with all visualizations
6. `06-token-breakdown-chart.png` - Close-up of TokenBreakdownChart donut chart
7. `07-cost-of-errors-section.png` - Cost of Errors section (if workflow has retries/errors)
8. `08-resource-usage-section.png` - Resource Usage section
9. `09-structured-input-section.png` - Structured Input with formatted and raw views
10. `10-full-dashboard-layout.png` - Full dashboard showing all sections
11. `11-mobile-layout.png` - Mobile responsive view (375px width)
12. `12-mobile-token-analysis.png` - Token Analysis on mobile
13. `13-desktop-layout.png` - Desktop responsive view (1920px width)
14. `14-workflow-without-cost-breakdown.png` - Graceful degradation for older workflow
15. `15-console-no-errors.png` - Browser console with no errors

## Notes
- Test should be run against a workflow with complete data including cost_breakdown.by_phase
- If no workflows with complete data exist, may need to run a workflow first to generate test data
- Screenshots should be captured at key decision points and after each major verification step
- Pay special attention to responsive behavior at mobile (375px), tablet (768px), and desktop (1024px+) breakpoints
