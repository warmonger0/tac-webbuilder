# Phase 1: Workflow History UI Enhancements - Header & Journey Display

## Overview
Enhance the WorkflowHistoryCard component to display richer metadata about workflow execution, making it easier to understand what each workflow did and why decisions were made.

## Current State
- WorkflowHistoryCard shows ADW ID, status, issue number, cost analytics, and token metrics
- Missing: classification type, plain-English descriptor, workflow/model info prominence, decision reasoning

## Requirements

### 1. Enhanced Header Section
Update the header to show classification and descriptor alongside ADW ID:

**Current:**
```
ADW: feature-abc123 [Status Badge]
Issue #42
```

**New:**
```
ADW: feature-abc123 [FEATURE] "Add user authentication system..."
Issue #42
Workflow: adw_sdlc_iso | Model: claude-sonnet-4-5
```

**Implementation Details:**
- Extract `structured_input.classification` (feature/bug/chore)
- Display as colored badge next to ADW ID (blue=feature, red=bug, yellow=chore)
- Show first 60 chars of `nl_input` as plain-English descriptor with ellipsis
- Add new row below issue number showing `workflow_template` and `model_used`
- Ensure responsive layout (stack on mobile)

### 2. Workflow Journey Section
Add new expandable section titled "Workflow Journey" (below "Resource Usage" section) containing:

#### 2.1 Original Request
Display the raw user input:
```tsx
<div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
  <h4 className="font-semibold text-gray-700 mb-2">Original Request</h4>
  <p className="text-sm text-gray-900">{workflow.nl_input}</p>
</div>
```

#### 2.2 ADW Classification & Reasoning
Display classification decision:
```tsx
<div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
  <h4 className="font-semibold text-gray-700 mb-2">Classification</h4>
  <dl className="text-sm space-y-2">
    <div>
      <dt className="text-gray-600">Type:</dt>
      <dd className="font-medium">{structured_input.classification}</dd>
    </div>
    <div>
      <dt className="text-gray-600">Reasoning:</dt>
      <dd>{structured_input.classification_reasoning || 'Not recorded'}</dd>
    </div>
  </dl>
</div>
```

#### 2.3 Model Selection Reasoning
Display why specific model was chosen:
```tsx
<div className="bg-green-50 border border-green-200 rounded-lg p-4">
  <h4 className="font-semibold text-gray-700 mb-2">Model Selection</h4>
  <dl className="text-sm space-y-2">
    <div>
      <dt className="text-gray-600">Selected:</dt>
      <dd className="font-medium">{workflow.model_used}</dd>
    </div>
    <div>
      <dt className="text-gray-600">Reason:</dt>
      <dd>{structured_input.model_selection_reasoning || 'Not recorded'}</dd>
    </div>
  </dl>
</div>
```

#### 2.4 Final Structured Input
Show the complete structured input with formatted display:
```tsx
<div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
  <h4 className="font-semibold text-gray-700 mb-2">Structured Input</h4>
  <dl className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
    {/* Show all relevant fields from structured_input */}
  </dl>
  <details className="mt-3">
    <summary className="text-xs text-blue-600 cursor-pointer">View Raw JSON</summary>
    <pre className="text-xs bg-white rounded p-2 mt-2 overflow-x-auto">
      {JSON.stringify(workflow.structured_input, null, 2)}
    </pre>
  </details>
</div>
```

### 3. Data Model Updates

Add these optional fields to `WorkflowHistoryItem` type in `app/client/src/types/api.types.ts`:

```typescript
// In structured_input object:
classification_reasoning?: string;
model_selection_reasoning?: string;
```

These fields should be populated from the ADW state file when available, but gracefully degrade to "Not recorded" if missing.

## Acceptance Criteria

- [ ] Classification badge appears next to ADW ID in header
- [ ] Plain-English descriptor (first 60 chars of nl_input) displays next to classification
- [ ] New metadata row shows workflow template and model below issue number
- [ ] "Workflow Journey" section appears in details area (collapsed by default)
- [ ] Original Request shows user's raw nl_input
- [ ] Classification section shows type and reasoning (or "Not recorded")
- [ ] Model Selection section shows model and reasoning (or "Not recorded")
- [ ] Structured Input section shows formatted key-value pairs
- [ ] Raw JSON toggle works for Structured Input
- [ ] All sections are responsive and work on mobile screens
- [ ] No TypeScript errors or console warnings
- [ ] Existing cost analytics and token breakdown sections still work
- [ ] Component renders correctly when optional fields are missing

## Testing Notes

Test with workflows that:
1. Have complete `structured_input` with all new fields
2. Have minimal `structured_input` (missing reasoning fields)
3. Have no `structured_input` at all
4. Have very long `nl_input` (test 60-char truncation)
5. Different classification types (feature/bug/chore)

## Files to Modify

- `app/client/src/components/WorkflowHistoryCard.tsx` - Main component updates
- `app/client/src/types/api.types.ts` - Type definition updates (if needed)

## Notes

- This is Phase 1 of 3-phase workflow history enhancement
- Focuses purely on UI/UX improvements
- No database schema changes required (uses existing `structured_input` field)
- Future phases will add performance metrics and advanced analytics
