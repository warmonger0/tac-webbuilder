# E2E Test: Cost Visualization on Workflow Cards

Test cost visualization functionality in the ADW monitoring dashboard.

## User Story

As a developer using the ADW system
I want to see detailed cost visualizations on workflow cards
So that I can understand the cost breakdown by phase, track cumulative costs, and appreciate the cache efficiency savings

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** the page displays workflow cards for active ADW workflows

4. Locate a workflow card on the page
5. **Verify** the workflow card displays:
   - Issue number
   - ADW ID
   - Current phase badge
   - Progress bar
   - "View on GitHub" link

6. **Verify** the "Cost Analysis" section is present on the workflow card
7. **Verify** the Cache Efficiency Badge is visible showing:
   - Cache efficiency percentage (should be displayed with % symbol)
   - Savings amount in dollars (should include $ symbol)
   - Icon indicator (🚀, ✅, ⚡, or ⚠️ based on efficiency)

8. Take a screenshot of the workflow card with cost analysis collapsed

9. Click the "Cost Analysis" expandable section to reveal cost details
10. **Verify** the expanded cost section displays:
    - Total Cost summary card
    - Total Tokens summary card
    - Phases Completed summary card

11. **Verify** the Cost Breakdown Chart is visible:
    - Bar chart showing per-phase costs
    - X-axis labels showing phase names (plan, build, test, review, document, ship)
    - Y-axis showing cost in dollars
    - Colored bars matching phase colors

12. **Verify** the Cumulative Cost Chart is visible:
    - Area chart showing cost progression
    - Total cost displayed prominently
    - Gradient fill for the area

13. **Verify** the Phase Details table is visible showing:
    - Phase column
    - Cost column
    - Input Tokens column
    - Cache Write column
    - Cache Read column (highlighted in green)
    - Output column

14. Take a screenshot of the expanded cost visualization

15. Hover over a bar in the Cost Breakdown Chart
16. **Verify** a tooltip appears showing:
    - Phase name
    - Cost amount
    - Token breakdown (Input, Cache Write, Cache Read, Output)

17. Take a screenshot of the chart tooltip

18. Click the "Cost Analysis" section again to collapse it
19. **Verify** the cost section collapses and only shows the badge

## Success Criteria

- Workflow cards display correctly with cost analysis section
- Cache efficiency badge shows percentage and savings amount
- Cost section expands and collapses on click
- Cost breakdown chart displays with correct phase colors
- Cumulative cost chart shows cost progression
- Phase details table displays all token metrics
- Tooltips provide detailed information on hover
- No console errors during test execution
- Cache efficiency is clearly highlighted (should show ~90% for typical workflows)
- All cost data loads asynchronously without blocking card rendering
- 3 screenshots are taken documenting the feature
