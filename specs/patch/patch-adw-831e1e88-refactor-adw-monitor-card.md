# Patch: Refactor AdwMonitorCard.tsx to Meet 800-Line Hard Limit

## Metadata
adw_id: `adw-831e1e88`
review_change_request: `Issue #1: AdwMonitorCard.tsx exceeds the 800-line hard limit with 885 lines. Code quality standards mandate that files exceeding 800 lines MUST be refactored before merging. Resolution: Refactor AdwMonitorCard.tsx by extracting logical components: 1) Split workflow visualization into separate component (WorkflowPipelineView.tsx), 2) Extract phase node rendering to PhaseNode.tsx, 3) Create WorkflowStatusBadge.tsx for status indicators, 4) Move cost/duration formatting to utility functions. Target: Reduce main component to under 500 lines. Severity: blocker`

## Issue Summary
**Original Spec:** `/Users/Warmonger0/tac/tac-webbuilder/trees/adw-831e1e88/specs/issue-110-adw-adw-831e1e88-sdlc_planner-phase-3-polish-integration.md`
**Issue:** AdwMonitorCard.tsx currently has 885 lines, exceeding the 800-line hard limit defined in code quality standards. This violates blocking-level requirements and must be refactored before merging.
**Solution:** Extract logical components and utilities to reduce AdwMonitorCard.tsx to under 500 lines by creating: WorkflowPipelineView.tsx (workflow visualization), PhaseNode.tsx (phase node rendering), WorkflowStatusBadge.tsx (status indicators), and formatters.ts (cost/duration formatting utilities).

## Files to Modify
- `app/client/src/components/AdwMonitorCard.tsx` - Main component (885 lines → target <500 lines)

## Files to Create
- `app/client/src/components/WorkflowPipelineView.tsx` - Extract workflow pipeline visualization (~200 lines)
- `app/client/src/components/PhaseNode.tsx` - Extract phase node rendering with icons and animations (~150 lines)
- `app/client/src/components/WorkflowStatusBadge.tsx` - Extract status badge rendering (~50 lines)
- `app/client/src/utils/formatters.ts` - Extract formatDuration and formatCost utilities (~30 lines)

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create Formatter Utilities
- Create `app/client/src/utils/formatters.ts`
- Extract `formatDuration` function from AdwMonitorCard.tsx
- Extract `formatCost` function from AdwMonitorCard.tsx
- Add TypeScript type annotations for parameters and return values
- Add JSDoc comments for each function

### Step 2: Extract PhaseNode Component
- Create `app/client/src/components/PhaseNode.tsx`
- Extract phase rendering logic including:
  - Icon rendering helper (renderIcon function with all SVG icons)
  - Phase status determination logic
  - Phase node styling and animations (glow effects, transitions)
- Define PhaseNodeProps interface with: name, icon, status, progress, isActive
- Import and use in WorkflowPipelineView

### Step 3: Extract WorkflowStatusBadge Component
- Create `app/client/src/components/WorkflowStatusBadge.tsx`
- Extract status badge rendering logic
- Support status types: running, completed, failed, paused, pending
- Include status-specific styling (colors, animations, icons)
- Define WorkflowStatusBadgeProps interface with: status, size (optional)

### Step 4: Extract WorkflowPipelineView Component
- Create `app/client/src/components/WorkflowPipelineView.tsx`
- Extract complete workflow visualization logic including:
  - workflowPhases array definition
  - Pipeline rendering with phase nodes
  - Progress bars and connections between phases
  - Workflow metadata display (adw_id, elapsed time, cost)
- Define WorkflowPipelineViewProps interface with: workflow (AdwWorkflowStatus type)
- Import PhaseNode and WorkflowStatusBadge components
- Import formatDuration and formatCost from utils

### Step 5: Refactor AdwMonitorCard.tsx
- Remove extracted code (formatters, phase rendering, pipeline visualization, status badges)
- Import new components: WorkflowPipelineView, WorkflowStatusBadge
- Import utilities: formatDuration, formatCost from '@/utils/formatters'
- Simplify main component to focus on:
  - Data fetching (useReliablePolling hook)
  - State management (workflows, summary, error states)
  - Top-level layout (summary cards, workflow list container)
  - Connection status indicator
- Replace inline workflow rendering with <WorkflowPipelineView workflow={workflow} /> calls
- Verify component still functions identically after refactoring

### Step 6: Verify Line Count Reduction
- Run `wc -l app/client/src/components/AdwMonitorCard.tsx` to verify <500 lines
- Run `wc -l app/client/src/components/WorkflowPipelineView.tsx` to verify <500 lines
- Run `wc -l app/client/src/components/PhaseNode.tsx` to verify <300 lines
- Run `wc -l app/client/src/components/WorkflowStatusBadge.tsx` to verify <200 lines
- Run `wc -l app/client/src/utils/formatters.ts` to verify <100 lines

## Validation
Execute every command to validate the patch is complete with zero regressions.

### Code Quality Validation
1. `wc -l app/client/src/components/AdwMonitorCard.tsx` - Verify <500 lines (target met)
2. `wc -l app/client/src/components/WorkflowPipelineView.tsx` - Verify component exists and <500 lines
3. `wc -l app/client/src/components/PhaseNode.tsx` - Verify component exists and <300 lines
4. `wc -l app/client/src/components/WorkflowStatusBadge.tsx` - Verify component exists and <200 lines
5. `wc -l app/client/src/utils/formatters.ts` - Verify utility exists and <100 lines

### TypeScript Validation
6. `cd app/client && bun tsc --noEmit` - Verify no TypeScript errors introduced

### Linting Validation
7. `cd app/client && bun run lint` - Verify ESLint passes with no new violations

### Build Validation
8. `cd app/client && bun run build` - Verify production build succeeds

### Functional Validation
9. Start server: `cd app/server && uv run python server.py` (background process)
10. Start client: `cd app/client && bun run dev` (background process)
11. Visual verification: Open browser to `http://localhost:9211` and verify ADW Monitor Card renders correctly with workflows visible
12. Verify no console errors in browser DevTools
13. Stop processes

### Test Validation
14. `cd app/client && bun run test` - Run frontend unit tests (if any exist for AdwMonitorCard)

## Patch Scope
**Lines of code to change:** ~885 lines refactored into 5 files (~400 lines remain in main component, ~485 lines extracted)
**Risk level:** medium (large refactor but purely structural - no logic changes)
**Testing required:** TypeScript compilation, linting, build verification, visual regression testing to ensure identical UI/behavior
