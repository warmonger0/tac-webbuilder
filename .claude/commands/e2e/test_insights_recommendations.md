# E2E Test: Phase 3D Insights & Recommendations

## User Story
As a workflow administrator, I want to view automated insights and optimization recommendations for my workflows, so that I can identify performance issues, reduce costs, and improve workflow efficiency without manual analysis.

## Test Steps

### 1. Navigate to History Tab
- Open the application at http://localhost:5173
- Wait for page to load completely
- Click on the "History" tab
- Verify the workflow history panel is visible

### 2. Verify Workflow with Insights Data Exists
- Check if at least one workflow card is visible
- Look for a workflow that has completed status
- If no workflows with insights exist, note this as a test precondition failure
- Take screenshot: `01-history-panel-insights.png`

### 3. Expand Workflow Card with Insights Data
- Identify a workflow card that likely has anomalies or recommendations
- Click to expand the workflow card details
- Wait for expansion animation to complete
- Verify the card is fully expanded
- Take screenshot: `02-expanded-workflow-with-insights.png`

### 4. Verify Insights & Recommendations Section Exists
- Scroll to find "💡 Insights & Recommendations" heading
- Verify the section is visible
- Verify the section appears after "📊 Efficiency Scores" section
- Check section has proper border and spacing (border-b border-gray-200 pb-6)
- Take screenshot: `03-insights-section-visible.png`

### 5. Verify Anomalies Detected Subsection
- Look for "⚠️ Anomalies Detected" subheading
- Verify the subheading has orange color (text-orange-700)
- Verify anomalies are displayed as a list (ul with space-y-2)
- Count number of anomaly items displayed (should be 1-5)
- Take screenshot: `04-anomalies-detected.png`

### 6. Verify Anomaly Styling
- For each anomaly item, verify:
  - Orange background (bg-orange-50)
  - Orange border (border-orange-200)
  - Rounded corners (rounded)
  - Padding (p-3)
  - Small text size (text-sm)
  - Text is readable and not truncated
- Verify spacing between anomaly items (space-y-2)
- Take screenshot: `05-anomaly-styling.png`

### 7. Verify Anomaly Content
- Read each anomaly message
- Verify messages contain specific information:
  - Cost anomalies mention dollar amounts and multipliers (e.g., "2.5x higher")
  - Duration anomalies mention seconds and multipliers
  - Retry anomalies mention retry count
  - Cache anomalies mention efficiency percentage
  - Error category anomalies mention error type
- Verify messages are actionable and informative
- Take screenshot: `06-anomaly-content.png`

### 8. Verify Optimization Tips Subsection
- Look for "✅ Optimization Tips" subheading
- Verify the subheading has green color (text-green-700)
- Verify recommendations are displayed as a list (ul with space-y-2)
- Count number of recommendation items displayed (should be 1-5)
- Take screenshot: `07-optimization-tips.png`

### 9. Verify Recommendation Styling
- For each recommendation item, verify:
  - Green background (bg-green-50)
  - Green border (border-green-200)
  - Rounded corners (rounded)
  - Padding (p-3)
  - Small text size (text-sm)
  - Text is readable and not truncated
- Verify spacing between recommendation items (space-y-2)
- Take screenshot: `08-recommendation-styling.png`

### 10. Verify Recommendation Content and Emojis
- Read each recommendation message
- Verify recommendations start with emoji prefixes:
  - 💡 = Model selection recommendations
  - 📦 = Cache optimization recommendations
  - 📝 = Input quality recommendations
  - ⏱️ = Workflow restructuring recommendations
  - 💰 = Cost reduction recommendations
  - 🐛 = Error prevention recommendations
  - 🚀 = Performance optimization recommendations
  - ✅ = Positive feedback (no anomalies)
- Verify recommendations are specific and actionable
- Take screenshot: `09-recommendation-emojis.png`

### 11. Verify Insights Section Conditional Rendering
- Scroll through multiple workflow cards
- Find a workflow WITHOUT anomalies or recommendations
- Expand that workflow card
- Verify "💡 Insights & Recommendations" section is NOT displayed
- Verify other sections still render correctly
- Take screenshot: `10-no-insights-hidden.png`

### 12. Verify Section Order and Layout
- For a workflow with full Phase 3 data, verify section order:
  1. Basic workflow info (collapsed by default)
  2. 📊 Efficiency Scores (if scores exist)
  3. 💡 Insights & Recommendations (if insights exist)
  4. 🔗 Similar Workflows (if similar workflows exist)
  5. Other sections (error analysis, etc.)
- Verify consistent border-b and pb-6 spacing between sections
- Take screenshot: `11-section-layout.png`

### 13. Test Mobile Viewport (375px width)
- Resize browser viewport to 375px width (iPhone SE)
- Expand a workflow with insights
- Verify anomaly items stack vertically
- Verify recommendation items stack vertically
- Verify all text remains readable
- Verify no horizontal scrolling required
- Verify emoji display correctly on mobile
- Take screenshot: `12-mobile-insights.png`

### 14. Test Tablet Viewport (768px width)
- Resize browser viewport to 768px width (iPad)
- Expand a workflow with insights
- Verify layout is balanced and readable
- Verify section widths are appropriate
- Take screenshot: `13-tablet-insights.png`

### 15. Verify No Console Errors
- Open browser developer console
- Check for any JavaScript errors
- Check for any React warnings related to insights rendering
- Verify no 404 network errors
- Check for any JSON parsing errors in network tab
- Take screenshot: `14-console-clean.png`

### 16. Test Workflow with Only Anomalies
- Find or create a workflow with only anomalies (no recommendations)
- Expand the workflow card
- Verify "⚠️ Anomalies Detected" displays
- Verify "✅ Optimization Tips" does NOT display
- Verify section still renders correctly
- Take screenshot: `15-only-anomalies.png`

### 17. Test Workflow with Only Recommendations
- Find or create a workflow with only recommendations (no anomalies)
- Expand the workflow card
- Verify "⚠️ Anomalies Detected" does NOT display
- Verify "✅ Optimization Tips" displays
- Verify section still renders correctly
- Take screenshot: `16-only-recommendations.png`

### 18. Test Workflow with Positive Feedback
- Find or create a workflow with no anomalies
- Expand the workflow card
- Verify insights section displays
- Verify recommendation shows: "✅ Workflow performing well - no anomalies detected"
- Verify green styling is used
- Take screenshot: `17-positive-feedback.png`

## Success Criteria

### Functional Requirements (Must Pass)
- ✅ Insights & Recommendations section displays when anomalies or recommendations exist
- ✅ Section is hidden when no insights data exists
- ✅ Anomalies subsection displays with orange styling (bg-orange-50, border-orange-200)
- ✅ Recommendations subsection displays with green styling (bg-green-50, border-green-200)
- ✅ Section headers use correct colors (text-orange-700, text-green-700)
- ✅ Anomaly messages contain specific information (costs, durations, percentages)
- ✅ Recommendation messages contain actionable advice
- ✅ Recommendations include emoji prefixes (💡 📦 📝 ⏱️ 💰 🐛 🚀 ✅)
- ✅ Maximum 5 anomalies/recommendations displayed per workflow
- ✅ Section appears after Efficiency Scores section
- ✅ Conditional rendering works (shows/hides subsections appropriately)

### Visual Requirements (Must Pass)
- ✅ All text is readable and not truncated
- ✅ Spacing and padding are consistent (space-y-2, p-3, pb-6)
- ✅ Border styling matches specification (border-b, border-gray-200)
- ✅ Orange/green color schemes are visually distinct
- ✅ Emojis display correctly in all browsers
- ✅ No visual glitches or broken layouts
- ✅ List items have proper rounded corners and borders

### Responsive Requirements (Must Pass)
- ✅ Mobile layout (375px): All items stack vertically
- ✅ Tablet layout (768px): Layout remains readable
- ✅ No horizontal scrolling required
- ✅ Emojis and text scale appropriately
- ✅ Touch targets are large enough (44px minimum)

### Quality Requirements (Must Pass)
- ✅ No console errors or warnings
- ✅ No JSON parsing errors in network tab
- ✅ No 404 network errors
- ✅ Insights section loads with workflow data (no delayed rendering)
- ✅ Smooth scrolling and animations

### Data Requirements (Must Pass)
- ✅ Anomalies are correctly deserialized from JSON
- ✅ Recommendations are correctly deserialized from JSON
- ✅ Empty arrays default to hiding subsections
- ✅ Malformed JSON doesn't crash UI

### Screenshot Requirements (Must Pass)
- ✅ At least 18 screenshots captured
- ✅ All screenshots show expected UI state
- ✅ Screenshots clearly show insights styling
- ✅ Screenshots demonstrate conditional rendering

## Output Format

Return a JSON object with the following structure:

```json
{
  "test_name": "Phase 3D Insights & Recommendations E2E Test",
  "status": "passed" | "failed",
  "timestamp": "2024-01-01T00:00:00Z",
  "screenshots": [
    "01-history-panel-insights.png",
    "02-expanded-workflow-with-insights.png",
    "03-insights-section-visible.png",
    "04-anomalies-detected.png",
    "05-anomaly-styling.png",
    "06-anomaly-content.png",
    "07-optimization-tips.png",
    "08-recommendation-styling.png",
    "09-recommendation-emojis.png",
    "10-no-insights-hidden.png",
    "11-section-layout.png",
    "12-mobile-insights.png",
    "13-tablet-insights.png",
    "14-console-clean.png",
    "15-only-anomalies.png",
    "16-only-recommendations.png",
    "17-positive-feedback.png"
  ],
  "success_criteria_met": {
    "functional": true | false,
    "visual": true | false,
    "responsive": true | false,
    "quality": true | false,
    "data": true | false
  },
  "errors": [],
  "notes": "Any additional observations or issues found during testing",
  "insights_found": {
    "workflows_with_anomalies": 0,
    "workflows_with_recommendations": 0,
    "workflows_with_both": 0,
    "workflows_with_neither": 0
  }
}
```

## Test Data Requirements

For this test to pass, the following data should exist:

1. **At least one workflow with anomalies:**
   - anomaly_flags: string[] with 1-5 items containing specific messages

2. **At least one workflow with recommendations:**
   - optimization_recommendations: string[] with 1-5 items starting with emoji prefixes

3. **At least one workflow with both anomalies and recommendations**

4. **At least one workflow without insights (empty arrays or null)**

5. **At least one workflow with positive feedback:**
   - No anomalies detected
   - optimization_recommendations: ["✅ Workflow performing well - no anomalies detected"]

If test data doesn't exist, the test runner should:
1. Run workflow sync to populate insights data: `cd app/server && uv run python -c "from core.workflow_history import sync_workflow_history; sync_workflow_history()"`
2. Verify database has workflows with varying insights data
3. If still no data, seed the database with mock workflows

## Notes

- This test validates the complete Phase 3D Insights & Recommendations implementation
- Test focuses on conditional rendering, styling, and content accuracy
- Test ensures insights are actionable and properly formatted
- Test covers emoji rendering across different browsers
- Test verifies JSON deserialization from database
- Test ensures backwards compatibility with workflows lacking insights data
- Test validates that anomaly detection and recommendations integrate correctly with the UI
