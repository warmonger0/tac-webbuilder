# Workflow History UI Enhancements - Header & Journey Display

**ADW ID:** a5b80595
**Date:** 2025-11-14
**Specification:** specs/issue-17-adw-a5b80595-sdlc_planner-workflow-history-ui-enhancements.md

## Overview

Enhanced the WorkflowHistoryCard component to display richer workflow metadata, including classification badges, plain-English descriptors, and a comprehensive "Workflow Journey" section that traces the transformation from natural language input to structured execution parameters. This Phase 1 enhancement improves transparency and makes it easier to understand workflow decisions without digging through state files.

## What Was Built

- **Classification Badge**: Color-coded badges (blue=feature, red=bug, yellow=chore) displayed next to ADW ID in the header
- **Plain-English Descriptor**: First 60 characters of the natural language input displayed as a readable summary
- **Enhanced Metadata Row**: Workflow template and model information prominently displayed below the issue number
- **Workflow Journey Section**: New expandable section containing four subsections:
  - Original Request: Raw natural language input from the user
  - Classification: Type and reasoning for why the workflow was classified
  - Model Selection: Selected model and reasoning for the choice
  - Structured Input: Formatted key-value display with raw JSON toggle
- **Graceful Degradation**: Component handles missing optional fields by displaying "Not recorded" or hiding sections
- **Type Safety**: New `StructuredInputData` interface for better TypeScript support

## Technical Implementation

### Files Modified

- `app/client/src/components/WorkflowHistoryCard.tsx` (+138/-64 lines)
  - Added three helper functions: `truncateText()`, `getClassificationColor()`, `formatStructuredInputForDisplay()`
  - Enhanced header to display classification badge and descriptor text
  - Added workflow template and model metadata row
  - Replaced standalone "Structured Input" section with comprehensive "Workflow Journey" section
  - Removed redundant "Natural Language Input" and metadata display (now integrated into journey)

- `app/client/src/types/api.types.ts` (+14/-1 lines)
  - Created new `StructuredInputData` interface with typed fields
  - Added `classification_reasoning` and `model_selection_reasoning` optional fields
  - Updated `WorkflowHistoryItem.structured_input` to use `StructuredInputData` instead of generic `Record<string, any>`

- `.mcp.json` and `playwright-mcp-config.json` (2 lines each)
  - Updated paths for new tree workspace (a5b80595)

### Key Changes

1. **Header Enhancement**: Classification badge uses conditional coloring based on type. Descriptor text truncates at 60 characters with ellipsis for long inputs. Layout is responsive with flex-wrap for mobile compatibility.

2. **Workflow Journey Section**: Organizes related information into themed subsections with distinct background colors (blue for request, purple for classification, green for model selection, gray for structured input). Each subsection uses definition lists for structured display.

3. **Improved Information Architecture**: Removed redundant "Natural Language Input" section at the top and "Structured Input" as standalone section. Consolidated all workflow decision-making information into a single cohesive "Workflow Journey" that tells the complete story.

4. **Type Safety**: New interface provides autocomplete and type checking for structured input fields, reducing potential runtime errors.

5. **Raw JSON Toggle**: Structured Input subsection includes collapsible details element for viewing the complete raw JSON, useful for debugging or detailed inspection.

## How to Use

### Viewing Enhanced Workflow History

1. Navigate to the History tab in the application
2. Browse the list of workflow executions
3. Observe the classification badge (colored tag) next to each ADW ID
4. Read the plain-English descriptor to quickly understand what each workflow did
5. Note the workflow template and model information displayed below the issue number
6. Click "Show Details" to expand the workflow card
7. Scroll to the "Workflow Journey" section (appears after "Resource Usage")

### Understanding the Workflow Journey

- **Original Request**: Read the exact natural language input the user provided
- **Classification**: See how the system classified the request and why
- **Model Selection**: Understand which model was chosen and the reasoning
- **Structured Input**: View formatted key-value pairs or click "View Raw JSON" for complete details

### Interpreting Classification Badges

- 🔵 **Blue (FEATURE)**: New functionality or capabilities
- 🔴 **Red (BUG)**: Bug fixes or error corrections
- 🟡 **Yellow (CHORE)**: Maintenance, refactoring, or housekeeping tasks
- ⚪ **Gray**: Default/unclassified workflows

## Configuration

No configuration required. The feature automatically uses data from existing workflow state files stored in `agents/{adw_id}/adw_state.json`.

### Data Requirements

The feature expects the following optional fields in `structured_input`:
- `classification`: String ("feature", "bug", "chore")
- `classification_reasoning`: String explaining why this classification was chosen
- `model_selection_reasoning`: String explaining why the model was chosen
- Standard fields: `issue_number`, `workflow`, `model`

When these fields are missing, the component gracefully degrades:
- Missing classification: No badge displayed
- Missing reasoning: Shows "Not recorded"
- Missing entire structured_input: Section hidden

## Testing

### Manual Testing

1. **Start the frontend**: `cd app/client && bun run dev`
2. **Navigate to History tab** and expand several workflow cards
3. **Verify classification badges** appear with correct colors
4. **Check descriptor truncation** for workflows with long nl_input
5. **Test responsive layout** using browser dev tools (mobile view)
6. **Expand "Workflow Journey"** and verify all four subsections render
7. **Click "View Raw JSON"** toggle to verify it expands/collapses
8. **Test graceful degradation** by viewing older workflows with minimal structured_input

### Validation Commands

```bash
# Type check
cd app/client && bun tsc --noEmit

# Production build
cd app/client && bun run build

# Backend tests (ensure no regressions)
cd app/server && uv run pytest
```

## Notes

### Design Decisions

- **Color Semantics**: Badge colors follow common conventions (blue=feature, red=bug, yellow=chore) for immediate visual recognition
- **60-Character Truncation**: Balances providing enough context while preventing UI overflow on narrow screens
- **Themed Subsections**: Distinct background colors help users quickly scan and locate specific information within the journey
- **Collapsible Raw JSON**: Advanced users can inspect complete data without cluttering the default view

### Backwards Compatibility

The feature works with existing workflows that lack new optional fields. Older workflow executions will display less information but will not break or show errors.

### Phase 1 of 3

This is the first phase of workflow history enhancements:
- **Phase 1** (this): Header & Journey Display
- **Phase 2** (future): Performance metrics and execution timing
- **Phase 3** (future): Advanced analytics and comparison tools

### Limitations

- Classification badge only appears if `structured_input.classification` exists
- Reasoning fields show "Not recorded" for workflows executed before this feature
- Very long structured input objects may cause horizontal scrolling in the key-value display
- No syntax highlighting in raw JSON view (plain text formatting)

### Future Enhancements

- Consider extracting `ClassificationBadge` as reusable component
- Add syntax highlighting to raw JSON view
- Add tooltips explaining classification and model selection reasoning
- Consider pagination for very large structured input objects
- Add filtering/search by classification type in history view
