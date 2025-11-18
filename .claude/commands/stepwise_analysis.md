# Stepwise Refinement Analysis

You are analyzing a GitHub issue to determine if it should be broken down into smaller, more manageable sub-issues.

## Issue Details

**Issue Number:** {0}
**Issue Data:**
```json
{1}
```

## Your Task

Analyze this issue and determine whether it is **ATOMIC** (ready to implement as-is) or should be **DECOMPOSED** into sub-issues.

## Decision Criteria

### ✅ ATOMIC (Do NOT decompose) if:
- Single, well-defined task
- Can be completed in one PR (< 500 lines of code)
- Clear acceptance criteria
- No obvious logical subdivisions
- Dependencies are minimal or sequential
- Estimated effort: < 4 hours

### ⚠️ DECOMPOSE (Break down) if:
- Multiple independent features/changes
- Large scope (> 500 lines of code)
- Can be parallelized across multiple PRs
- Has natural boundaries (frontend + backend, multiple components)
- Complex with many dependencies
- Estimated effort: > 4 hours
- Risk reduction benefit from incremental delivery

## Output Format

You MUST output a YAML configuration block with your analysis:

```yaml
# STEPWISE REFINEMENT ANALYSIS

decision: ATOMIC  # or DECOMPOSE

reasoning: |
  Brief explanation of why you made this decision.
  Consider: scope, complexity, parallelization potential, risk.

confidence: high  # high, medium, or low

sub_issues:  # Only if decision is DECOMPOSE, otherwise empty list
  - title: "Sub-issue 1 title"
    body: |
      Detailed description of what this sub-issue should accomplish.
      Include acceptance criteria.
    labels:
      - feature  # or bug, chore, etc.
      - sub-issue
    depends_on: []  # List of sub-issue indices this depends on (0-indexed)

  - title: "Sub-issue 2 title"
    body: |
      Detailed description.
    labels:
      - feature
      - sub-issue
    depends_on: [0]  # Depends on first sub-issue

# Total estimated sub-issues: 2-5 (if DECOMPOSE)
# Recommended workflow per sub-issue: adw_sdlc_complete_iso or adw_lightweight_iso
```

## Guidelines for Sub-Issue Creation

1. **Granularity**: Each sub-issue should be independently valuable
2. **Size**: Target 200-500 lines of code per sub-issue
3. **Dependencies**: Minimize inter-dependencies, make them explicit
4. **Parallelization**: Maximize opportunities for parallel work
5. **Testing**: Each sub-issue should be independently testable
6. **Count**: Aim for 2-5 sub-issues (avoid over-decomposition)

## Examples

### Example 1: ATOMIC Decision
```yaml
decision: ATOMIC
reasoning: |
  This is a simple bug fix in a single file (UserAuth.tsx).
  Clear reproduction steps and expected behavior.
  Estimated 50 lines of code change.
  No logical subdivisions.
confidence: high
sub_issues: []
```

### Example 2: DECOMPOSE Decision
```yaml
decision: DECOMPOSE
reasoning: |
  This feature requires:
  - New database schema (backend)
  - API endpoints (backend)
  - UI components (frontend)
  - Integration tests (both)

  These can be parallelized and incrementally delivered.
  Total estimated 800+ lines of code.
  Risk reduction through incremental delivery.
confidence: high
sub_issues:
  - title: "Database schema for user preferences"
    body: |
      Create database migration and models for user preferences.

      Acceptance Criteria:
      - Migration creates user_preferences table
      - Model includes fields: user_id, theme, language, notifications
      - Indexes on user_id for performance
      - Tests for model validation
    labels:
      - feature
      - backend
      - sub-issue
    depends_on: []

  - title: "API endpoints for user preferences"
    body: |
      Implement REST API endpoints for managing preferences.

      Acceptance Criteria:
      - GET /api/preferences - fetch user preferences
      - PUT /api/preferences - update user preferences
      - Validation and error handling
      - Unit tests for all endpoints
    labels:
      - feature
      - backend
      - sub-issue
    depends_on: [0]

  - title: "Frontend preference settings UI"
    body: |
      Create UI components for user preference management.

      Acceptance Criteria:
      - PreferenceSettings component
      - Form validation
      - API integration with backend
      - Component tests
    labels:
      - feature
      - frontend
      - sub-issue
    depends_on: [1]
```

## Important Notes

- **Always** output the YAML block - this is parsed programmatically
- Be conservative with decomposition - only decompose when clear benefit exists
- Consider team velocity and context switching costs
- Link sub-issues to parent issue automatically (handled by automation)
- Each sub-issue should deliver incremental value

## Analysis

Proceed with your analysis now.
