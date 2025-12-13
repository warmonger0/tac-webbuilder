# Feature #106: Plans Panel Enhancements + Auto-Workflow Launcher

## Overview
Two-part feature:
1. **Part A**: Plans Panel UI/UX improvements (detailed below)
2. **Part B**: Auto-workflow launcher integration (deferred pending Part A)

---

## Part A: Plans Panel UI/UX Enhancements

### Visual Changes

#### 1. Collapsible Work Items
**Requirement**: Collapse items to show only title and category, expand individually or all at once.

**Behavior**:
- Default state: Collapsed (title + category visible only)
- Single click on item: Toggle expand/collapse for that item
- Show "Expand All" / "Collapse All" button at section level
- Expanded view shows: Full description, tags, estimated hours, all metadata

**Example**:
```
Collapsed:
[>] #66: Branch Name Not Visible in Workflow State [Bug]

Expanded:
[v] #66: Branch Name Not Visible in Workflow State [Bug]
    Description: Planning phase outputs branch_name but not visible in UI...
    Priority: High | Estimated: 0.75h | Status: Planned
    Tags: backend, database, workflow-state
```

#### 2. Collapsible Section Headers
**Requirement**: Collapse "In Progress", "Planned Fixes & Enhancements", etc. with item counts.

**Behavior**:
- Default state: Expanded (show all items in section)
- Click section header: Collapse to show only header + count
- Count updates dynamically as items move between sections

**Example**:
```
Collapsed:
[>] In Progress (1)
[>] Planned Fixes & Enhancements (43)

Expanded:
[v] In Progress (1)
    [>] #63: Implement Pattern Validation Loop [Feature]
[v] Planned Fixes & Enhancements (43)
    [>] #66: Branch Name Not Visible in Workflow State [Bug]
    [>] #88: E2E ADW Workflow Validation [Enhancement]
    ...
```

#### 3. Implementation Planning Section
**Requirement**: Add collapsible "Implementation Planning:" sub-element to each work item.

**Behavior**:
- Nested inside each expanded work item
- Collapsed by default
- Shows implementation notes, phase breakdown, dependencies
- Editable (future enhancement)

**Example**:
```
[v] #63: Implement Pattern Validation Loop [Feature]
    Description: Complete Phase 3 of Pattern Recognition...
    Priority: High | Estimated: 3.0h | Status: In Progress

    [>] Implementation Planning:
        (Collapsed - click to expand)

    [v] Implementation Planning:
        Phase 1: Create pattern_validator.py (1.0h)
        Phase 2: Integrate workflow completion hook (0.75h)
        Phase 3: Add analytics queries (0.75h)
        Phase 4: Write tests (0.5h)
        Dependencies: Migration 010 verified
```

### Functional Changes

#### 4. Selectable Work Items
**Requirement**: Make work items selectable with visual feedback.

**Behavior**:
- **Single click**: Toggle selection
- **Selected state**: Highlighted background (light yellow or theme-appropriate)
- **Deselection**: Click again OR select different item
- **Auto-expand**: If collapsed, selecting expands the item
- **Single selection**: Only one item selected at a time (radio behavior)

**Visual States**:
```
Normal:     [>] #66: Branch Name Not Visible...
Hover:      [>] #66: Branch Name Not Visible... (subtle highlight)
Selected:   [v] #66: Branch Name Not Visible... (light yellow background, expanded)
```

#### 5. Auto-Highlight Next Priority
**Requirement**: System identifies and highlights next priority work item.

**Behavior**:
- **Priority algorithm**:
  1. "In Progress" items first (resume work)
  2. High-priority planned items
  3. Quick Wins (≤2h) for momentum
  4. Oldest planned items (prevent stale work)

- **Visual indicator**:
  - Header highlighted with light yellow background
  - Optional badge: "🎯 Next"
  - Tooltip: "System recommends this task next"

- **User override**: Clicking different item removes auto-highlight

**Example**:
```
[v] In Progress (1)
    [v] 🎯 #63: Implement Pattern Validation Loop [Feature]  ← HIGHLIGHTED
        (Auto-highlighted because it's in progress)

[v] Planned Fixes & Enhancements (43)
    [>] #66: Branch Name Not Visible in Workflow State [Bug]
    [>] #88: E2E ADW Workflow Validation [Enhancement]
```

---

## Part B: Auto-Workflow Launcher (Deferred)

### Requirements (For Future Implementation)

Once Part A is complete, add:

#### 6. "Generate & Launch" Button
**Requirement**: From Plans Panel, generate prompt and auto-launch workflow.

**Behavior**:
1. User selects work item (#66)
2. Clicks "Generate & Launch" button
3. System runs: `./scripts/gen_prompt.sh 66`
4. Auto-populates Request Form (Panel 1) with generated prompt
5. Pre-selects appropriate workflow template
6. Sets model/timeout/cost limits from work item metadata
7. User reviews and clicks "Submit" (or auto-submit with confirmation)

#### 7. Workflow Tracking Link
**Requirement**: Return workflow tracking link after launch.

**Behavior**:
- After submission, display: "✅ Workflow launched: #123 → [View Status]"
- Link opens Panel 2 (ADW Dashboard) filtered to that workflow
- Work item auto-updates status to "In Progress"

---

## Implementation Strategy

### Phase 1: Visual Changes (1.5-2.0h)
**Focus**: UI/UX improvements only
- Collapsible work items
- Collapsible section headers with counts
- Implementation planning section

**Files**:
- `app/client/src/components/PlansPanel.tsx`
- `app/client/src/components/PlanItem.tsx` (new component)
- CSS/Tailwind styling

### Phase 2: Functional Changes (1.0-1.5h)
**Focus**: Selection and highlighting
- Selectable work items (single selection)
- Auto-highlight next priority

**Files**:
- `app/client/src/components/PlansPanel.tsx`
- `app/client/src/hooks/usePlanSelection.ts` (new hook)
- Priority algorithm logic

### Phase 3: Auto-Launcher (Deferred - 1.5h)
**Focus**: Integration with gen_prompt.sh
- Generate & Launch button
- Request Form auto-population
- Workflow tracking link

**Files**:
- Backend: `app/server/routes/planned_features_routes.py` (new endpoint)
- Frontend: `app/client/src/components/PlansPanel.tsx`
- Integration: Request Form population logic

---

## Success Criteria

### Part A (Phases 1-2)
- ✅ Work items collapse/expand individually
- ✅ Section headers collapse/expand with counts
- ✅ Implementation planning section visible when expanded
- ✅ Work items selectable with visual feedback
- ✅ Auto-highlight shows next recommended task
- ✅ All existing functionality preserved
- ✅ Responsive design maintained

### Part B (Phase 3 - Deferred)
- ✅ Generate & Launch button functional
- ✅ Request Form auto-populates correctly
- ✅ Workflow launches with correct parameters
- ✅ Tracking link returns and works
- ✅ Work item status updates automatically

---

## Open Questions

1. **Implementation planning data source**:
   - Store in `planned_features.implementation_notes` (new field)?
   - Generate dynamically from feature description?
   - Load from separate markdown files?

2. **Priority algorithm**:
   - Should user be able to override priority order?
   - Should "Quick Wins" always be prioritized?
   - How to handle tied priorities?

3. **Auto-launch permissions**:
   - Should auto-launch require confirmation?
   - Should it respect cost limits?
   - What if backend/frontend servers aren't running?

---

## Related Features

- #104: Plan-to-Prompt Generator (✅ Complete) - Used by Part B
- #63: Pattern Validation Loop (In Progress) - Example work item
- #101: Plans Panel Auto-Update Logic (Planned) - Status sync

---

## Notes

- Part A can be implemented independently
- Part B depends on Part A being complete
- Part B also depends on #104 (Plan-to-Prompt Generator) which is ✅ complete
- Consider Part A as "Quick Win" sequence (2 phases × 1-1.5h each)
- Part B can be separate feature if needed

---

**Status**: Requirements documented, awaiting prioritization decision
**Next Step**: Decide whether to implement Part A now or defer entire #106
