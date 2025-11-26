# Patch: Implement Animation System for ADW Monitor

## Metadata
adw_id: `adw-831e1e88`
review_change_request: `Issue #3: Animation system was not implemented. The spec required CSS transitions for status changes, loading skeletons, progress bar interpolation, and phase node transition effects. None of these visual enhancements are present in the current implementation. Resolution: Implement animation system: 1) Add CSS transitions for status badge changes (200ms), 2) Create loading skeleton component for initial data fetch, 3) Implement smooth progress bar interpolation using requestAnimationFrame (500ms), 4) Add phase node transition animations with scale and glow effects (300ms), 5) Ensure animations respect prefers-reduced-motion setting. Severity: blocker`

## Issue Summary
**Original Spec:** docs/adw_monitor_phase3.md
**Issue:** Animation system required by Phase 3 spec (lines 265-270) is missing. Status badge changes are instant without transitions, loading state lacks skeleton, no progress bar interpolation, phase node transitions are abrupt, and accessibility motion preferences are not respected.
**Solution:** Add CSS transitions for status changes (200ms), create LoadingSkeleton component, implement smooth progress interpolation with requestAnimationFrame (500ms), enhance phase node transitions with scale/glow effects (300ms), and respect prefers-reduced-motion media query.

## Files to Modify
Use these files to implement the patch:

1. `app/client/src/components/WorkflowStatusBadge.tsx` - Add 200ms status transition
2. `app/client/src/components/LoadingSkeleton.tsx` - New component for loading state
3. `app/client/src/components/PhaseNode.tsx` - Add 300ms scale and glow transitions
4. `app/client/src/components/WorkflowPipelineView.tsx` - Add progress bar interpolation
5. `app/client/src/components/AdwMonitorCard.tsx` - Integrate LoadingSkeleton and motion preference
6. `app/client/src/utils/formatters.ts` - Add progress interpolation utility (new file already exists)
7. `app/client/src/hooks/useReducedMotion.ts` - New hook for motion preference detection

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create useReducedMotion hook for accessibility
- Create `app/client/src/hooks/useReducedMotion.ts`
- Export `useReducedMotion()` hook that returns boolean
- Use `window.matchMedia('(prefers-reduced-motion: reduce)')`
- Add event listener for dynamic changes
- Clean up listener on unmount

### Step 2: Add CSS transitions to WorkflowStatusBadge (200ms)
- Add `transition-all duration-200 ease-in-out` to badge container className
- Add `transition-all duration-200 ease-in-out` to status dot
- Ensure transitions apply to background, text color, and dot appearance
- Test status changes smoothly transition over 200ms

### Step 3: Create LoadingSkeleton component for initial load
- Create `app/client/src/components/LoadingSkeleton.tsx`
- Export `LoadingSkeleton` component with shimmer animation
- Match layout structure of WorkflowPipelineView
- Include skeleton for: header (title, badge), central hub circle, 9 phase nodes
- Use Tailwind `animate-pulse` for shimmer effect
- Add gradient background from slate-700 to slate-600 for shimmer

### Step 4: Add smooth progress interpolation to WorkflowPipelineView (500ms)
- Create `app/client/src/hooks/useProgressInterpolation.ts`
- Export `useProgressInterpolation(targetProgress: number)` hook
- Use `requestAnimationFrame` to interpolate from current to target over 500ms
- Return `interpolatedProgress` number
- Integrate into WorkflowPipelineView for phase completion percentage
- Apply to any numerical progress displays

### Step 5: Enhance PhaseNode transitions with scale and glow (300ms)
- Add `transition-all duration-300 ease-in-out` to phase node container
- Add `scale-100` for pending/completed, `scale-110` for active status
- Add `transition-opacity duration-300` to glow effects
- Ensure border, shadow, and background transitions are smooth
- Test phase transitions feel responsive and polished

### Step 6: Integrate animations into AdwMonitorCard
- Replace loading state div with `<LoadingSkeleton />` component
- Import and use `useReducedMotion()` hook
- Add `motion-reduce:transition-none` Tailwind classes to animated elements
- Conditionally disable animations when `prefersReducedMotion === true`
- Test loading skeleton appears on initial load
- Verify all animations respect motion preferences

### Step 7: Add global CSS for motion-reduce fallbacks
- Add `@media (prefers-reduced-motion: reduce)` block to AdwMonitorCard style tag
- Disable all animations: `animation: none !important`
- Disable all transitions: `transition: none !important`
- Ensure instant state changes when motion is reduced
- Test with browser DevTools "Emulate CSS prefers-reduced-motion" option

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **TypeScript type check**: `cd app/client && bun tsc --noEmit`
   - Purpose: Verify new hooks and components have correct types

2. **Frontend build**: `cd app/client && bun run build`
   - Purpose: Ensure animations don't break production build

3. **Visual validation**: Start dev server and verify:
   - Status badge changes smoothly transition colors (200ms)
   - Loading skeleton displays on initial page load
   - Phase node transitions include scale and glow effects (300ms)
   - Progress numbers interpolate smoothly (500ms)
   - All animations respect `prefers-reduced-motion` setting

4. **Accessibility check**: Enable "Emulate CSS prefers-reduced-motion: reduce" in browser DevTools
   - Purpose: Verify all animations are disabled
   - Confirm status changes are instant
   - Confirm phase transitions have no motion

5. **Performance check**: Monitor browser performance panel during animations
   - Purpose: Ensure animations stay at 60fps
   - Verify no layout thrashing
   - Confirm requestAnimationFrame is efficient

## Patch Scope
**Lines of code to change:** ~200 lines
- New files: LoadingSkeleton.tsx (~50 lines), useReducedMotion.ts (~20 lines), useProgressInterpolation.ts (~40 lines)
- Modified files: WorkflowStatusBadge.tsx (+5 lines), PhaseNode.tsx (+10 lines), WorkflowPipelineView.tsx (+30 lines), AdwMonitorCard.tsx (+30 lines), style block (+15 lines)

**Risk level:** low
- Pure UI enhancement with no backend changes
- New components are isolated and don't affect existing logic
- Graceful degradation via prefers-reduced-motion
- Animations use CSS transitions (hardware accelerated)

**Testing required:** Visual validation + accessibility testing with motion preferences
- Manual browser testing for animation smoothness
- DevTools motion emulation for accessibility
- Cross-browser testing (Chrome, Firefox, Safari)
- Performance profiling to ensure 60fps
