# E2E Test: Workflows Documentation Tab

Test the workflows documentation section displays correctly with all 12 ADW workflows in a two-column layout.

## User Story

As a developer using the Natural Language SQL Interface application
I want to view available ADW workflows with descriptions in an organized layout
So that I can understand what each workflow does and when to use it for automating GitHub issue processing

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial page state
3. **Verify** the page title is "Natural Language SQL Interface"
4. Scroll down to the "Available ADW Workflows" section
5. **Verify** the "Available ADW Workflows" section exists
6. **Verify** the introductory paragraph about ADW workflows is present
7. Take a screenshot of the workflows section header

8. **Verify** the "Single Phase Workflows" category header exists
9. **Verify** the category description is present
10. **Verify** all 6 single-phase workflows are displayed:
    - Plan Only (adw_plan_iso)
    - Build Only (adw_build_iso)
    - Test Only (adw_test_iso)
    - Review Only (adw_review_iso)
    - Document Only (adw_document_iso)
    - Ship (adw_ship_iso)

11. **Verify** the "Multi-Phase Workflows" category header exists
12. **Verify** all 4 multi-phase workflows are displayed:
    - Plan + Build (adw_plan_build_iso)
    - Plan + Build + Test (adw_plan_build_test_iso)
    - Plan + Build + Test + Review (adw_plan_build_test_review_iso)
    - Quick Patch (adw_patch_iso)

13. **Verify** the "Complete SDLC Workflows" category header exists
14. **Verify** all 2 complete SDLC workflows are displayed:
    - Complete SDLC (adw_sdlc_iso)
    - Zero Touch Execution (adw_sdlc_zte_iso)

15. **Verify** each workflow card has a two-column layout:
    - Left column: Workflow name and script name
    - Right column: Description and use case

16. Take a screenshot of the complete workflows section (desktop view)

17. **Verify** the workflow script names are styled with monospace font
18. **Verify** the "When to use" section is highlighted for each workflow
19. **Verify** hover effects work on workflow cards (border color changes)

20. Resize browser window to mobile width (< 768px)
21. **Verify** the two-column layout stacks vertically on mobile
22. **Verify** workflow information remains readable on mobile
23. Take a screenshot of the workflows section (mobile view)

## Success Criteria
- All 12 workflows are displayed (6 single-phase, 4 multi-phase, 2 complete SDLC)
- Workflows are grouped into 3 categories with headers and descriptions
- Two-column layout displays on desktop (30% name / 70% description split)
- Columns stack vertically on mobile devices (< 768px width)
- Each workflow has: name, script name, description, and use case
- Script names are styled with monospace font and background color
- Use case sections are visually distinguished with border and background
- Section follows existing design patterns (colors, spacing, shadows, borders)
- Layout is fully responsive and accessible
- 3 screenshots are captured (initial, desktop workflows, mobile workflows)
