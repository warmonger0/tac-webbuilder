# E2E Test: Workflow History Performance & Error Analytics

## User Story
As a developer using the ADW system, I want to see detailed performance metrics and error analytics for each workflow execution, so that I can identify bottlenecks, understand failure patterns, optimize workflow efficiency, and make data-driven decisions about retry strategies and resource allocation.

## Test Scenario
This test validates that the Workflow History cards display performance analysis (phase durations, bottleneck detection, idle time) and enhanced error analysis (error categories, retry reasons, error phase distribution, recovery time) when the data is available.

## Prerequisites
- Backend server running on port 8000
- Frontend running on configured port
- Database migration 002_add_performance_metrics.sql has been applied
- At least one workflow with phase_durations data in the database
- At least one workflow with error_category data in the database

## Test Steps

### 1. Navigate to History Tab
```
1. Open the application in browser
2. Click on the "History" tab in the navigation
3. Wait for page to load
```

**Expected Result:**
- History view loads without errors
- Workflow cards are displayed
- Take screenshot: 01_history_tab_loaded.png

### 2. Find Workflow with Performance Data
```
1. Scroll through workflow cards
2. Click "Show Details" on a workflow card
3. Look for "⚡ Performance Analysis" section
4. If not visible, try another workflow card
```

**Verify:**
- At least one workflow has the "⚡ Performance Analysis" section
- Take screenshot: 02_performance_analysis_section.png

### 3. Verify Performance Analysis Section
```
1. In the expanded workflow card with performance data, verify:
   - Section header shows "⚡ Performance Analysis"
   - Phase Duration Chart displays with horizontal bars
   - Each phase shows:
     * Phase name (capitalized)
     * Duration in human-readable format (e.g., "2m 30s")
     * Percentage of total time
     * Color-coded bar (green=fast, yellow=medium, red=slow)
   - Total Duration is displayed at the bottom
2. Check for bottleneck alert (yellow banner)
   - If present, should show: "⚠️ Bottleneck Detected: {phase} phase"
   - Subtext should explain: "This phase took significantly longer than others (>30% of total time)"
3. Check for idle time display
   - If present, should show: "Idle time between phases: {duration}"
```

**Verify:**
- PhaseDurationChart renders correctly with bars
- Phase names are capitalized and readable
- Durations are formatted correctly (seconds, minutes, or hours)
- Percentages add up to approximately 100%
- Bar colors reflect performance (green < 30% of max, yellow 30-60%, red > 60%)
- Total duration matches sum of phase durations
- If bottleneck detected, yellow alert banner displays correctly
- If idle time > 0, it displays in readable format
- Take screenshot: 03_phase_duration_chart.png
- If bottleneck alert present, take screenshot: 04_bottleneck_alert.png

### 4. Find Workflow with Error Data
```
1. Scroll through workflow cards
2. Look for a workflow with status "failed" or retry_count > 0
3. Click "Show Details" on the workflow card
4. Look for "⚠️ Error Analysis" section
```

**Verify:**
- At least one workflow has the "⚠️ Error Analysis" section with enhanced data
- Take screenshot: 05_error_analysis_section.png

### 5. Verify Error Category Badge
```
1. In the expanded workflow card with error data, verify:
   - Error category badge is displayed at the top
   - Badge has red background (bg-red-100)
   - Badge shows error category in uppercase (e.g., "SYNTAX ERROR", "TIMEOUT", "API QUOTA", "VALIDATION", "UNKNOWN")
   - Category name has underscores replaced with spaces
```

**Verify:**
- Error category badge renders correctly
- Text is uppercase and readable
- Badge styling matches design (red background, red text, border)
- Take screenshot: 06_error_category_badge.png

### 6. Verify Error Message Display
```
1. Check that error message is displayed (if available)
2. Verify:
   - Red background container (bg-red-50)
   - Border (border-red-200)
   - Header "Error Message:"
   - Error text is readable and complete
```

**Verify:**
- Error message displays correctly in red-styled container
- Text is not truncated
- Styling is consistent with design

### 7. Verify Retry Reasons List
```
1. Check if "Retry Triggers:" section is present
2. Verify:
   - Section header displays: "Retry Triggers:"
   - Bulleted list (list-disc, list-inside)
   - Each retry reason is displayed on a separate line
   - Underscores in reason names are replaced with spaces
   - List is in a gray bordered container
```

**Verify:**
- If workflow has retry_reasons data, list displays correctly
- Each reason is on its own line
- Formatting is clean and readable
- Gray container styling matches design
- Take screenshot: 07_retry_reasons_list.png (if present)

### 8. Verify Error Phase Distribution
```
1. Check if "Errors by Phase:" section is present
2. Verify:
   - Section header displays: "Errors by Phase:"
   - Grid layout with 2-3 columns
   - Each phase shows:
     * Phase name (capitalized)
     * Error count (e.g., "2 errors" or "1 error")
   - Red background styling (bg-red-50, border-red-200)
```

**Verify:**
- If workflow has error_phase_distribution data, grid displays correctly
- Phase names are capitalized
- Error counts are grammatically correct (singular/plural)
- Grid is responsive (2 cols on mobile, 3 on desktop)
- Red styling is consistent
- Take screenshot: 08_error_phase_distribution.png (if present)

### 9. Verify Recovery Time Display
```
1. Check if recovery time is displayed
2. Verify:
   - Text shows: "Total recovery time: {duration}"
   - Duration is in human-readable format (e.g., "3m 45s")
   - Text is gray colored (text-gray-600)
```

**Verify:**
- If workflow has recovery_time_seconds > 0, it displays correctly
- Duration format matches other duration displays in the card
- Take screenshot: 09_recovery_time.png (if present)

### 10. Verify Retry Count and Cost Impact (Existing Feature)
```
1. Verify existing retry count display is still present
2. Check "Retries Required" card shows:
   - Number of retries
   - Orange styling
3. Check "Estimated Retry Cost Impact" card (if over budget)
```

**Verify:**
- Existing retry functionality still works
- New error analytics sections don't break existing features
- All sections display harmoniously together

### 11. Test Graceful Degradation
```
1. Find a workflow without performance data (old workflow)
2. Click "Show Details"
3. Verify:
   - No "⚡ Performance Analysis" section appears
   - Other sections still display correctly
   - No errors or broken layouts
4. Find a workflow without error data
5. Click "Show Details"
6. Verify:
   - No "⚠️ Error Analysis" section appears (unless retry_count > 0 or status=failed)
   - No errors or broken layouts
```

**Verify:**
- Workflows without new data don't show empty sections
- No console errors or React warnings
- UI gracefully handles missing data
- Take screenshot: 10_graceful_degradation.png

### 12. Verify Responsive Design
```
1. Resize browser window to mobile width (375px)
2. Verify:
   - Phase duration bars remain readable
   - Error phase distribution grid adjusts to 2 columns
   - Text doesn't overflow containers
3. Resize to tablet width (768px)
4. Verify layout adjusts appropriately
5. Resize to desktop width (1920px)
6. Verify all elements display optimally
```

**Verify:**
- Performance Analysis section is responsive
- Error Analysis section is responsive
- All grids and layouts adjust correctly
- No horizontal scrolling or overflow
- Take screenshot: 11_mobile_view.png (mobile width)
- Take screenshot: 12_desktop_view.png (desktop width)

## Success Criteria

### UI Elements Present (When Data Available)
- [x] "⚡ Performance Analysis" section header
- [x] PhaseDurationChart component with horizontal bars
- [x] Phase names, durations, and percentages
- [x] Total duration display
- [x] Bottleneck alert (yellow banner when detected)
- [x] Idle time display (when > 0)
- [x] "⚠️ Error Analysis" section header
- [x] Error category badge (red, uppercase)
- [x] Error message display (red container)
- [x] "Retry Triggers:" list
- [x] "Errors by Phase:" grid
- [x] Recovery time display

### Functionality Works
- [x] PhaseDurationChart renders bars correctly
- [x] Bar colors reflect performance (green/yellow/red)
- [x] Percentages calculate correctly
- [x] Bottleneck detection displays when phase > 30% of total
- [x] Error category displays from database field
- [x] Retry reasons display as bulleted list
- [x] Error phase distribution displays as grid
- [x] Recovery time displays in readable format
- [x] Graceful degradation for missing data
- [x] No sections shown when data unavailable

### Data Accuracy
- [x] Phase durations match database values
- [x] Total duration = sum of phase durations
- [x] Bottleneck phase is correct (>30% rule)
- [x] Error category matches categorize_error() output
- [x] Retry reasons match database array
- [x] Error phase distribution counts are accurate
- [x] Recovery time matches database value

### Visual Design
- [x] Performance section uses lightning bolt emoji (⚡)
- [x] Error section uses warning emoji (⚠️)
- [x] Colors follow Tailwind patterns:
  - Performance bars: green-500, yellow-500, red-500
  - Bottleneck alert: yellow-50 bg, yellow-200 border
  - Error category badge: red-100 bg, red-800 text
  - Error message: red-50 bg, red-200 border
  - Retry reasons: gray-50 bg, gray-200 border
  - Error phase grid: red-50 bg, red-200 border
- [x] Typography is consistent (font sizes, weights)
- [x] Spacing is uniform (padding, margins, gaps)
- [x] Responsive design works on all screen sizes
- [x] No layout breaks or visual glitches

### Integration with Existing Features
- [x] Cost Economics section still works
- [x] Token Analysis section still works
- [x] Existing Error section (retry count) still works
- [x] Resource Usage section still works
- [x] Workflow Journey section still works
- [x] All sections display in correct order
- [x] No conflicts or styling issues between sections

## Known Limitations
- Performance metrics only available for workflows with timestamps in cost_data
- Error categorization depends on pattern matching in error messages
- Retry reasons not yet tracked (database field exists but not populated)
- Error phase distribution not yet tracked (database field exists but not populated)
- Recovery time not yet calculated (database field exists but not populated)

## Screenshots
Capture screenshots at key steps:
1. History tab loaded with workflow cards
2. Performance Analysis section with phase duration chart
3. Phase duration chart showing color-coded bars
4. Bottleneck alert (if detected)
5. Error Analysis section with error category badge
6. Error category badge close-up
7. Retry reasons list (if available)
8. Error phase distribution grid (if available)
9. Recovery time display (if available)
10. Workflow without new data (graceful degradation)
11. Mobile responsive view
12. Desktop full view with all sections expanded
