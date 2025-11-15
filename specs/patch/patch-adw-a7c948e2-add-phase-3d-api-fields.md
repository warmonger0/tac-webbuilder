# Patch: Add Phase 3D Fields to API Data Model

## Metadata
adw_id: `a7c948e2`
review_change_request: `Issue #1: CRITICAL BLOCKER: API data model is missing Phase 3D fields. The WorkflowHistoryItem Pydantic model in app/server/core/data_models.py (lines 236-316) does not include anomaly_flags and optimization_recommendations fields. Database has the columns, backend generates the data, frontend has UI components, but the API cannot transmit insights data because the response model lacks these fields. Resolution: Add the following fields to WorkflowHistoryItem in app/server/core/data_models.py after line 316 (after Phase 3B section):
# Phase 3D: Insights & Recommendations
anomaly_flags: Optional[List[str]] = Field(None, description="List of anomaly messages")
optimization_recommendations: Optional[List[str]] = Field(None, description="List of optimization recommendations")

This will allow the API to serialize and transmit insights data to the frontend, completing the end-to-end data flow. Severity: blocker`

## Issue Summary
**Original Spec:** specs/issue-31-adw-a7c948e2-sdlc_planner-phase-3d-insights-recommendations.md
**Issue:** The WorkflowHistoryItem Pydantic model is missing anomaly_flags and optimization_recommendations fields, preventing the API from transmitting Phase 3D insights data to the frontend. Database columns exist, backend generates the data, and frontend UI is ready, but the API response model drops these fields during serialization at server.py:351 where `WorkflowHistoryItem(**workflow)` is called.
**Solution:** Add the two missing Phase 3D fields to the WorkflowHistoryItem model in data_models.py after line 316, allowing the API to include insights data in responses.

## Files to Modify
Use these files to implement the patch:

- `app/server/core/data_models.py` (lines 236-316) - Add Phase 3D fields to WorkflowHistoryItem model

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Phase 3D fields to WorkflowHistoryItem model
- Read app/server/core/data_models.py to locate the WorkflowHistoryItem class (lines 236-316)
- Add the Phase 3D section after line 316 (after scoring_version field, before class definition ends)
- Add comment header: `# Phase 3D: Insights & Recommendations`
- Add field: `anomaly_flags: Optional[List[str]] = Field(None, description="List of anomaly messages")`
- Add field: `optimization_recommendations: Optional[List[str]] = Field(None, description="List of optimization recommendations")`
- Ensure proper indentation matches existing fields
- Import List from typing at top of file if not already imported

### Step 2: Verify API can now serialize insights data
- Run Python syntax check to ensure no syntax errors: `cd app/server && uv run python -m py_compile core/data_models.py`
- Run backend code quality check: `cd app/server && uv run ruff check core/data_models.py`
- Run TypeScript type check to ensure frontend compatibility: `cd app/client && bun tsc --noEmit`

## Validation
Execute every command to validate the patch is complete with zero regressions.

- `cd app/server && uv run python -m py_compile core/data_models.py` - Validate Python syntax
- `cd app/server && uv run ruff check core/data_models.py` - Validate code quality
- `cd app/server && uv run python -m py_compile server.py main.py core/*.py` - Full backend syntax check
- `cd app/server && uv run ruff check .` - Full backend linting
- `cd app/server && uv run pytest tests/ -v --tb=short` - All backend tests must pass
- `cd app/client && bun tsc --noEmit` - TypeScript type check
- `cd app/client && bun run build` - Frontend build validation

## Patch Scope
**Lines of code to change:** 3 lines (1 comment + 2 field definitions)
**Risk level:** low
**Testing required:** Syntax validation, backend tests, TypeScript type checking, frontend build. The change is additive-only (adding optional fields with default None), so it cannot break existing functionality.
