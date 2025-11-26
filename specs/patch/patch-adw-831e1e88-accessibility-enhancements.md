# Patch: Accessibility Enhancements for ADW Monitor

## Metadata
adw_id: `adw-831e1e88`
review_change_request: `Issue #5: Accessibility enhancements were not implemented. The spec required ARIA labels for status indicators, keyboard navigation support, screen reader announcements for status changes, and comprehensive accessibility testing. These features are missing from the current implementation. Resolution: Implement accessibility features: 1) Add ARIA labels to all status indicators and interactive elements, 2) Implement keyboard navigation (Tab through phase nodes, Enter to expand), 3) Add screen reader announcements for status changes using aria-live regions, 4) Ensure focus indicators are visible, 5) Test with NVDA/JAWS screen readers. Severity: blocker`

## Issue Summary
**Original Spec:** specs/issue-110-adw-adw-831e1e88-sdlc_planner-phase-3-polish-integration.md (Step 11: Accessibility & Final Polish)
**Issue:** The ADW Monitor implementation lacks accessibility features required by WCAG 2.1 Level AA standards. Status indicators, interactive elements, and dynamic content updates are not accessible to screen reader users or keyboard-only navigation.
**Solution:** Add comprehensive accessibility support including ARIA labels, keyboard navigation, live regions for status updates, and visible focus indicators across all ADW Monitor components.

## Files to Modify
Use these files to implement the patch:

- `app/client/src/components/AdwMonitorCard.tsx` - Add aria-live region for connection status, ARIA labels for retry button and error messages
- `app/client/src/components/WorkflowPipelineView.tsx` - Add ARIA labels for workflow status, metadata, and interactive pipeline elements
- `app/client/src/components/PhaseNode.tsx` - Add keyboard navigation (Tab, Enter), ARIA labels, focus indicators for phase nodes
- `app/client/src/components/WorkflowStatusBadge.tsx` - Add ARIA labels for status badges with descriptive text
- `app/client/src/components/ConnectionStatusIndicator.tsx` - Add ARIA labels for connection status with role and state attributes
- `app/client/src/components/LoadingSkeleton.tsx` - Add ARIA live region and loading announcement

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add ARIA live regions for dynamic status updates
- Add `aria-live="polite"` region in `AdwMonitorCard.tsx` for connection status changes
- Add `aria-live="assertive"` for critical errors requiring immediate attention
- Add `role="alert"` to error messages for screen reader announcements
- Add `aria-atomic="true"` to ensure complete status messages are announced

### Step 2: Add ARIA labels to all interactive elements
- Add descriptive `aria-label` to retry button in `AdwMonitorCard.tsx` error state
- Add `aria-label` to connection status indicator in `ConnectionStatusIndicator.tsx`
- Add `aria-label` to workflow status badges in `WorkflowStatusBadge.tsx` with full status description
- Add `aria-describedby` to link status indicators with detailed descriptions
- Add `role="status"` to non-interactive status displays

### Step 3: Implement keyboard navigation for phase nodes
- Add `tabIndex={0}` to phase nodes in `PhaseNode.tsx` to make them keyboard focusable
- Add `onKeyDown` handler to support Enter/Space key for expanding phase details
- Add `aria-expanded` attribute to indicate collapsible state
- Add `role="button"` for interactive phase nodes
- Add visible focus ring using CSS `focus:ring-2 focus:ring-blue-500 focus:outline-none`

### Step 4: Add semantic HTML and ARIA roles
- Add `role="region"` with `aria-label` to main workflow pipeline section
- Add `role="list"` to phase nodes container with individual phase nodes as `role="listitem"`
- Add `aria-current="step"` to active phase node
- Add `role="progressbar"` with `aria-valuenow`, `aria-valuemin`, `aria-valuemax` to progress indicators
- Add `aria-label` to loading skeleton in `LoadingSkeleton.tsx` announcing "Loading workflow data"

### Step 5: Ensure visible focus indicators
- Add consistent focus styling across all interactive components
- Use `focus-visible:` utility classes for keyboard-only focus indicators
- Ensure focus ring has minimum 3:1 contrast ratio with background
- Add `outline-offset` to separate focus indicator from component boundary
- Test focus order follows logical reading sequence (top to bottom, left to right)

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **TypeScript Type Check**
   ```bash
   cd app/client && bun tsc --noEmit
   ```
   - Validates all new ARIA attributes and props are correctly typed

2. **Frontend Build**
   ```bash
   cd app/client && bun run build
   ```
   - Ensures accessibility changes don't break production build

3. **Manual Keyboard Navigation Test**
   - Start the application: `./scripts/start.sh`
   - Navigate to ADW Monitor card using Tab key
   - Verify all phase nodes are keyboard accessible
   - Verify Enter key expands/collapses phase details
   - Verify focus indicators are clearly visible
   - Verify focus order is logical

4. **Screen Reader Test (Manual)**
   - Test with NVDA (Windows) or VoiceOver (macOS)
   - Verify workflow status is announced on load
   - Verify status changes are announced via live regions
   - Verify phase nodes announce their status (pending/active/completed)
   - Verify connection status changes are announced
   - Verify error messages are announced immediately

5. **Accessibility Audit**
   ```bash
   # Run axe-core accessibility tests (if configured)
   cd app/client && bun run test:a11y
   ```
   - Validates WCAG 2.1 Level AA compliance
   - Checks for missing ARIA labels, roles, and keyboard accessibility

## Patch Scope
**Lines of code to change:** ~150 lines across 6 files
**Risk level:** Low (additive changes only, no logic modifications)
**Testing required:** Manual keyboard navigation testing, screen reader testing with NVDA/VoiceOver, automated accessibility audit
