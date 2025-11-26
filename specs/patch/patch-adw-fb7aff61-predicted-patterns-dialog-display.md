# Patch: Display Predicted Patterns in Confirmation Dialog

## Metadata
adw_id: `adw-fb7aff61`
review_change_request: `Issue #1: Predicted patterns section does not appear in the UI preview/confirmation dialog. The implementation at RequestForm.tsx:394-418 conditionally renders predicted patterns only when preview exists AND showConfirm is false. However, showConfirm is set to true immediately after submission (line 233), preventing the patterns from ever being displayed. The spec requires patterns to be visible in the preview above the Cost Estimate card. Resolution: Move the predicted patterns display section inside the confirmation dialog (after line 394), or refactor the condition to show patterns regardless of showConfirm state. The patterns section should be rendered inside the dialog component that appears when showConfirm is true, positioned above the CostEstimateCard component. Severity: blocker`

## Issue Summary
**Original Spec:** specs/issue-114-adw-adw-fb7aff61-sdlc_planner-phase-1-complete-submission-time-pattern-detection.md
**Issue:** The predicted patterns section at RequestForm.tsx:394-418 is conditionally rendered only when `preview && !showConfirm && !autoPost` is true. However, when `showConfirm` is set to `true` (line 233), this condition becomes false, preventing the patterns from displaying in the confirmation dialog. The spec requires patterns to be visible in the preview above the Cost Estimate card.
**Solution:** Add predicted patterns display to the ConfirmDialog component, positioned above the CostEstimateCard component, so patterns are visible when the confirmation dialog appears.

## Files to Modify
- `app/client/src/components/ConfirmDialog.tsx` - Add predicted patterns display above CostEstimateCard
- `app/client/src/components/RequestForm.tsx` - Pass predictedPatterns prop to ConfirmDialog

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update ConfirmDialog interface to accept predicted patterns
- Add `predictedPatterns` prop to ConfirmDialogProps interface
- Type as optional array: `predictedPatterns?: Array<{ pattern: string; confidence: number; reasoning: string }> | null`

### Step 2: Add predicted patterns display in ConfirmDialog component
- Insert predicted patterns section after the title (line 22) and before the CostEstimateCard (line 24-27)
- Use the same styling and structure as RequestForm.tsx:398-417
- Conditionally render only when predictedPatterns exists and has length > 0
- Position above CostEstimateCard to match spec requirements

### Step 3: Pass predictedPatterns to ConfirmDialog in RequestForm
- Update ConfirmDialog invocation at RequestForm.tsx:462-468
- Add `predictedPatterns={predictedPatterns}` prop
- No other changes to RequestForm needed

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **TypeScript type check:**
```bash
cd app/client && bun tsc --noEmit
```
Expected: No type errors

2. **Frontend build:**
```bash
cd app/client && bun run build
```
Expected: Build succeeds with no errors

3. **Frontend tests:**
```bash
cd app/client && bun test
```
Expected: All tests pass

4. **E2E test for pattern prediction UI:**
Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_pattern_prediction_ui.md` to validate pattern prediction UI displays correctly in the confirmation dialog with screenshots.
Expected: Test passes, screenshots show predicted patterns above cost estimate, UI styling correct

5. **Backend tests (regression check):**
```bash
cd app/server && uv run pytest
```
Expected: All tests pass, zero failures

## Patch Scope
**Lines of code to change:** ~15 lines
**Risk level:** low
**Testing required:** TypeScript type checking, frontend build, E2E UI test for pattern display in confirmation dialog
