# Feature: Workflows Documentation Tab with 2-Column Layout

## Metadata
issue_number: `1`
adw_id: `d2ac5466`
issue_json: `{"number":1,"title":"Add workflows documentation tab with 2-column layout","body":"## Feature Request\n\nAdd a new sub-tab or section within the Workflows tab that displays available ADW workflows with descriptions.\n\n### Requirements\n\n**Layout:**\n- Two-column layout\n- Left column: Workflow name (clickable/readable)\n- Right column: Brief description of what the workflow does and when to use it\n\n**Workflows to document:**\n1. `adw_plan_iso` - Planning phase only\n2. `adw_build_iso` - Build/implementation phase only\n3. `adw_test_iso` - Testing phase only\n4. `adw_review_iso` - Code review phase only\n5. `adw_document_iso` - Documentation generation phase only\n6. `adw_ship_iso` - Ship phase (PR approval and merge)\n7. `adw_sdlc_zte_iso` - Complete SDLC with Zero Touch Execution (auto-ship)\n8. `adw_sdlc_iso` - Complete SDLC without auto-ship\n9. `adw_plan_build_iso` - Plan + Build phases\n10. `adw_plan_build_test_iso` - Plan + Build + Test phases\n11. `adw_plan_build_test_review_iso` - Plan + Build + Test + Review phases\n12. `adw_patch_iso` - Quick patch workflow\n\n### Technical Details\n\n- Use React + TypeScript + Tailwind CSS (matching existing components)\n- Integrate with existing `WorkflowDashboard` component at `app/client/src/components/WorkflowDashboard.tsx`\n- Responsive design (mobile-friendly)\n- Descriptions should come from the workflow files or be defined in a constants file\n\n### Acceptance Criteria\n\n- [ ] Two-column layout displays all ADW workflows\n- [ ] Each workflow has a clear, concise description\n- [ ] Layout is responsive and accessible\n- [ ] Follows existing design patterns in the app\n- [ ] Component is tested\n\n/adw_sdlc_zte_iso"}`

## Feature Description
This feature adds a new "Workflows" section to the Natural Language SQL Interface application that displays available AI Developer Workflow (ADW) scripts in a two-column layout. The left column shows the workflow name, and the right column provides a description of what the workflow does and when to use it. This provides users with clear documentation about the 12 available ADW workflows for GitHub issue automation.

## User Story
As a developer using the Natural Language SQL Interface application
I want to view available ADW workflows with descriptions in an organized layout
So that I can understand what each workflow does and when to use it for automating GitHub issue processing

## Problem Statement
Currently, there is no user-facing documentation or interface that explains the available ADW workflows. Developers need to manually explore the `adws/` directory to understand what workflows exist and what they do. This creates a knowledge gap and makes it difficult to effectively utilize the ADW automation system.

## Solution Statement
Create a new "Workflows" section in the main application interface that displays all 12 ADW workflows in a clean, two-column layout. Each workflow will have its name displayed on the left and a clear description on the right explaining its purpose and use case. The section will be styled consistently with the existing application design and will be responsive for mobile devices.

## Relevant Files
Use these files to implement the feature:

- `app/client/index.html` - Main HTML template where we'll add the workflows section. This file contains the application structure and is relevant because we need to add a new section for displaying workflows.

- `app/client/src/main.ts` - Main TypeScript entry point that initializes the application. This file is relevant because we'll need to add initialization logic for the workflows section.

- `app/client/src/style.css` - Global styles file that defines the application's visual design. This file is relevant because we need to add styles for the two-column workflow layout that match existing patterns.

- `app/client/src/types.d.ts` - TypeScript type definitions. This file is relevant because we'll need to define types for workflow data structures.

- `README.md` - Project documentation. This file is relevant to understand the project structure and ADW system context.

- `adws/README.md` - ADW system documentation. This file is relevant to understand workflow descriptions and use cases.

- `.claude/commands/test_e2e.md` - E2E test runner instructions. This file is relevant because we need to understand how to create E2E tests for UI features.

- `.claude/commands/e2e/test_basic_query.md` - Example E2E test. This file is relevant as a reference for creating our workflows E2E test.

- `.claude/commands/e2e/test_complex_query.md` - Another example E2E test. This file is relevant as a reference for creating comprehensive E2E tests.

### New Files

- `app/client/src/workflows.ts` - New module containing workflow data constants and initialization logic for the workflows section.

- `.claude/commands/e2e/test_workflows_documentation.md` - E2E test file to validate the workflows documentation section displays correctly with all 12 workflows.

## Implementation Plan

### Phase 1: Foundation
Define the workflow data structure and create the constants file that will hold all workflow information. This includes workflow names, descriptions, and metadata. Research the ADW system by reading `adws/README.md` to ensure accurate descriptions.

### Phase 2: Core Implementation
Implement the workflows section in the HTML, create the TypeScript module to handle workflow display, and add CSS styles for the two-column layout. Ensure the layout is responsive and follows existing design patterns from the application.

### Phase 3: Integration
Integrate the workflows section into the main application flow by adding initialization logic in `main.ts`. Create comprehensive E2E tests to validate the feature works correctly across different viewport sizes.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Research ADW workflows and define data structure

- Read `adws/README.md` to understand the ADW system and gather accurate workflow descriptions
- Read the 12 ADW workflow Python files in the `adws/` directory to understand what each workflow does:
  - `adws/adw_plan_iso.py`
  - `adws/adw_build_iso.py`
  - `adws/adw_test_iso.py`
  - `adws/adw_review_iso.py`
  - `adws/adw_document_iso.py`
  - `adws/adw_ship_iso.py`
  - `adws/adw_sdlc_zte_iso.py`
  - `adws/adw_sdlc_iso.py`
  - `adws/adw_plan_build_iso.py`
  - `adws/adw_plan_build_test_iso.py`
  - `adws/adw_plan_build_test_review_iso.py`
  - `adws/adw_patch_iso.py`
- Define TypeScript interface for workflow data in `app/client/src/types.d.ts`
- Create comprehensive workflow descriptions based on research

### Create workflows constants module

- Create `app/client/src/workflows.ts` with workflow data constants
- Define an array of workflow objects containing: name, script_name, description, use_case, and category (single-phase, multi-phase, or full-sdlc)
- Implement a function to get all workflows
- Export constants and functions for use in main.ts

### Add workflows section HTML

- Add a new workflows section to `app/client/index.html` after the tables section
- Create a container with an h3 header "Available ADW Workflows"
- Add a div with id `workflows-list` for displaying workflow items
- Include a brief introductory paragraph explaining what ADW workflows are
- Follow existing HTML structure patterns from the tables section

### Implement workflows display logic

- Add workflow display functionality to `app/client/src/main.ts`
- Create `displayWorkflows()` function to render workflow items
- Implement two-column layout structure: left column for name, right column for description
- Add category grouping (Single Phase, Multi-Phase, Complete SDLC)
- Initialize workflows display on DOMContentLoaded
- Import and use workflow data from workflows.ts

### Style the workflows section

- Add CSS styles for workflows section to `app/client/src/style.css`
- Style the workflow item cards with consistent spacing and borders
- Implement two-column responsive grid layout
- Add hover effects for better interactivity
- Style category headers to distinguish workflow groups
- Ensure mobile responsiveness with appropriate breakpoints (stack columns on small screens)
- Match existing design patterns (colors, shadows, border radius) from tables section

### Create E2E test for workflows documentation

- Create `.claude/commands/e2e/test_workflows_documentation.md`
- Define user story: As a user, I want to view ADW workflow documentation, so that I can understand available workflows
- Write test steps:
  1. Navigate to application URL
  2. Take screenshot of initial page state
  3. Verify "Available ADW Workflows" section exists
  4. Verify all 12 workflows are displayed
  5. Verify two-column layout is present
  6. Verify each workflow has a name and description
  7. Take screenshot of workflows section
  8. Test responsive behavior by resizing viewport to mobile size
  9. Take screenshot of mobile view
  10. Verify workflows section is accessible
- Define success criteria: All 12 workflows display, layout is responsive, section follows design patterns
- Specify 3 screenshots to capture

### Run validation commands

- Execute all validation commands listed in the "Validation Commands" section
- Fix any issues that arise from validation
- Ensure zero regressions in existing functionality
- Confirm E2E test passes with all screenshots captured

## Testing Strategy

### Unit Tests
No traditional unit tests are required for this feature as it is primarily a static display component. However, the E2E test will validate:
- Workflow data structure is correctly defined
- All 12 workflows are rendered
- Two-column layout displays properly
- Responsive design works on mobile and desktop viewports
- HTML structure is semantically correct

### Edge Cases
- **No workflows found**: While not applicable in this implementation (workflows are hardcoded), the display function should handle empty arrays gracefully
- **Long workflow descriptions**: Test that descriptions wrap properly and don't break the layout
- **Mobile viewport**: Ensure columns stack vertically on small screens (< 768px width)
- **Very wide viewport**: Ensure layout doesn't stretch too wide and remains readable
- **Accessibility**: Test keyboard navigation and screen reader compatibility
- **Category grouping**: Verify workflows are correctly grouped by category (Single Phase, Multi-Phase, Complete SDLC)

## Acceptance Criteria
- All 12 ADW workflows are displayed in the workflows section
- Two-column layout clearly separates workflow names (left) and descriptions (right)
- Workflows are grouped by category (Single Phase, Multi-Phase, Complete SDLC)
- Layout is fully responsive and works on mobile devices (columns stack on small screens)
- Section follows existing design patterns from the application (colors, spacing, shadows, borders)
- E2E test validates the workflows section displays correctly
- No existing functionality is broken (zero regressions)
- Workflow descriptions are accurate and helpful based on ADW documentation
- HTML is semantically correct and accessible
- CSS styles are consistent with the existing style.css patterns

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

Read `.claude/commands/test_e2e.md`, then read and execute your new E2E `.claude/commands/e2e/test_workflows_documentation.md` test file to validate this functionality works.

- `cd app/server && uv run pytest` - Run server tests to validate the feature works with zero regressions
- `cd app/client && bun tsc --noEmit` - Run frontend TypeScript compilation to validate no type errors exist
- `cd app/client && bun run build` - Run frontend build to validate the feature works with zero regressions

## Notes

### Workflow Categories
Workflows are organized into three logical categories:

**Single Phase Workflows** (targeted, isolated operations):
- `adw_plan_iso` - Creates implementation plans only
- `adw_build_iso` - Implements code changes only
- `adw_test_iso` - Runs and fixes tests only
- `adw_review_iso` - Performs code review only
- `adw_document_iso` - Generates documentation only
- `adw_ship_iso` - Handles PR approval and merge only

**Multi-Phase Workflows** (combinations of phases):
- `adw_plan_build_iso` - Planning + Implementation
- `adw_plan_build_test_iso` - Planning + Implementation + Testing
- `adw_plan_build_test_review_iso` - Planning + Implementation + Testing + Review
- `adw_patch_iso` - Quick patch workflow for urgent fixes

**Complete SDLC Workflows** (full software development lifecycle):
- `adw_sdlc_iso` - Complete SDLC requiring manual PR approval
- `adw_sdlc_zte_iso` - Complete SDLC with Zero Touch Execution (automatic PR merge)

### Design Considerations
- The workflows section should appear below the "Available Tables" section as it represents system-level functionality rather than data-level functionality
- Use existing CSS variables for colors, spacing, and shadows to maintain design consistency
- The two-column layout should have approximately 30% width for names and 70% width for descriptions on desktop
- On mobile (< 768px), columns should stack vertically with the name appearing above the description
- Consider adding subtle visual separators between workflow categories for improved readability

### Future Enhancements
This feature creates a foundation for potential future improvements:
- Make workflow names clickable to show more detailed documentation
- Add a search/filter functionality to find specific workflows
- Include status indicators showing which workflows are currently running
- Add links to ADW documentation or GitHub workflows
- Display workflow execution history or statistics
