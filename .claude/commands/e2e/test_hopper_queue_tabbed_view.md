# E2E Test: Hopper Queue Tabbed View

Test that the Hopper Queue card displays a tabbed interface with "In Progress" and "Completed" tabs, and that the "In Progress" tab shows a styled "Queue Empty" card.

## User Story

As a user monitoring ZTE hopper queue activity
I want to see a tabbed interface with "In Progress" and "Completed" tabs
So that I can easily distinguish between active queue items and completed ones, with clear visual feedback when the queue is empty

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** the "Hopper Queue" heading is visible (changed from "ZTE Hopper Queue")
4. **Verify** two tabs are visible: "In Progress" and "Completed"
5. **Verify** the "In Progress" tab is selected by default (has emerald border-bottom and emerald text color)
6. **Verify** the "In Progress" tab content displays a card with:
   - Fixed height of 295px
   - Background color rgb(16, 185, 129) - emerald green
   - "Queue Empty" text in white, bold, left-justified
7. Take a screenshot showing the "In Progress" tab active state
8. Click on the "Completed" tab
9. **Verify** the "Completed" tab becomes active (emerald border and text)
10. **Verify** the "In Progress" tab becomes inactive (gray text, no border)
11. **Verify** the "Completed" tab content displays placeholder text: "Completed items will be displayed here"
12. Take a screenshot showing the "Completed" tab active state
13. Click back on the "In Progress" tab
14. **Verify** the view switches back to show the "Queue Empty" card
15. Take a screenshot confirming tab switching works smoothly
16. **Verify** the Hopper Queue card maintains equal height with the adjacent "Create New Request" card
17. Take a screenshot of the complete layout with both cards side by side

## Success Criteria
- "In Progress" and "Completed" tabs are both visible
- "In Progress" tab is selected by default
- Tab switching works smoothly without layout shifts
- "Queue Empty" card has emerald green background (rgb(16, 185, 129))
- "Queue Empty" text is white, bold, and left-justified
- Card has fixed height of 295px
- "Completed" tab shows placeholder content
- Tab styling changes appropriately (active vs inactive states)
- Component maintains equal height with adjacent card
- 5 screenshots are captured
