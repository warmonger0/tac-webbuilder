# E2E Test: ZTE Hopper Queue Card Layout

Test that the ZTE Hopper Queue card is visible, positioned correctly, and matches the height of the Create New Request card.

## User Story

As a user
I want to see a ZTE Hopper Queue card alongside the Create New Request card
So that I can access ZTE Hopper queue functionality with a consistent and visually balanced layout

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** the "Create New Request" heading is visible
4. **Verify** the "ZTE Hopper Queue" heading is visible
5. **Verify** both cards are displayed side by side (not stacked)
6. **Verify** both cards have matching heights
7. **Verify** the spacing between the two cards is consistent (gap-6 = 1.5rem)
8. **Verify** the System Status Panel is positioned below both cards
9. Take a screenshot of the two-card layout
10. **Verify** the ZTE Hopper Queue card displays the placeholder text "Queue information will be displayed here"
11. Take a screenshot showing the complete layout with both cards and the System Status Panel

## Success Criteria
- ZTE Hopper Queue card is visible
- Card is positioned to the right of Create New Request card
- Both cards have equal heights
- Spacing between cards matches the spacing to System Status Panel (1.5rem)
- System Status Panel remains below both cards
- Layout is responsive and visually consistent
- 3 screenshots are taken
