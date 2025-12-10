# Design: Issue Already Resolved Detection System

## Problem
ADW workflows are launched for issues that are already fixed, wasting compute resources and creating duplicate work (e.g., issues #156, #157, #159 all trying to fix the same already-resolved code).

## Objective
Add intelligent detection to preflight checks that identifies when an issue is already resolved, preventing unnecessary ADW workflow launches.

## Solution Architecture

### 1. Enhanced Preflight Check API

**Modify endpoint:** `/api/v1/preflight-checks`

Add optional parameter:
- `issue_number` (optional): GitHub issue number to validate

**Example:**
```bash
GET /api/v1/preflight-checks?issue_number=159&skip_tests=false
```

### 2. New Check Function: `check_issue_already_resolved()`

**Check Type:** WARNING (not blocking)
- False positives are possible
- Human can override and launch anyway
- Provides confidence score and evidence

**Heuristics (Fast, No AI):**

#### A. GitHub Issue State Check
```python
# Check if issue is already closed
gh issue view {issue_number} --json state,closedAt,labels
# If closed recently (< 24 hours) and has "duplicate" label → HIGH confidence
```

#### B. Git History Analysis
```python
# Search recent commits (last 50) for issue mentions
git log -50 --oneline --all --grep="#{issue_number}"
git log -50 --oneline --all --grep="Fix.*{issue_number}"
# If found → MEDIUM confidence
```

#### C. Code Pattern Analysis (Optional, file-specific)
```python
# If issue mentions specific file/function
# Extract from issue body: "Fix in app/client/src/api/workLogClient.ts"
# Check if expected pattern exists
# Example: Search for "if (!response.ok)" in deleteWorkLog function
```

### 3. Response Structure

```json
{
  "passed": true,
  "blocking_failures": [],
  "warnings": [
    {
      "check": "Issue Already Resolved",
      "message": "Issue #159 may already be fixed (confidence: 85%)",
      "impact": "Launching workflow may create duplicate work",
      "evidence": [
        "Issue closed 2 hours ago (duplicate label)",
        "Commit 6a3d8d0 mentions fix for #156 (same file)",
        "Code pattern 'if (!response.ok)' found in workLogClient.ts:86"
      ],
      "recommendation": "Review commit 6a3d8d0 before proceeding"
    }
  ],
  "checks_run": [...],
  "issue_validation": {
    "issue_number": 159,
    "is_resolved": true,
    "confidence": 0.85,
    "closed_at": "2025-12-10T06:12:00Z",
    "related_commits": ["6a3d8d0"],
    "duplicate_of": [156, 157]
  }
}
```

### 4. Confidence Scoring

| Evidence | Confidence Boost | Reasoning |
|----------|-----------------|-----------|
| Issue closed with "duplicate" label | +40% | Strong signal of resolution |
| Issue closed < 24h ago | +20% | Recent, likely related to current codebase |
| Recent commit mentions issue # | +25% | Direct evidence of fix |
| Code pattern matches expected fix | +30% | Technical validation |
| Multiple related closed issues | +15% | Pattern of duplicates |

**Thresholds:**
- **< 50%**: No warning (uncertain)
- **50-75%**: Low confidence warning
- **75-90%**: Medium confidence warning (show in UI)
- **> 90%**: High confidence warning (recommend not launching)

### 5. UI Integration

**Panel 1 - Preflight Check Display:**

```
⚠️  WARNINGS:
  • Issue Already Resolved (confidence: 85%)
    Issue #159 appears to be fixed in commit 6a3d8d0

    Evidence:
    - Issue closed 2 hours ago as duplicate
    - Commit 6a3d8d0 fixed #156 (same file: workLogClient.ts)
    - Expected code pattern found at line 86

    Recommendation: Review commit before launching workflow

    [Review Commit] [Launch Anyway]
```

### 6. Implementation Plan

#### Phase 1: Core Detection (This Session)
- [ ] Modify preflight_checks.py to accept issue_number
- [ ] Implement check_issue_already_resolved()
  - GitHub state check
  - Git history search
- [ ] Add warning to response (not blocking)
- [ ] Update API endpoint signature

#### Phase 2: Code Pattern Analysis (Future)
- [ ] Parse issue body for file/line references
- [ ] Extract expected code patterns
- [ ] Validate patterns exist in codebase
- [ ] Increase confidence when patterns match

#### Phase 3: UI Enhancement (Future)
- [ ] Display warnings prominently in Panel 1
- [ ] Add "Review Commit" button linking to GitHub
- [ ] Add "Launch Anyway" option with confirmation
- [ ] Show confidence score visually (progress bar)

## Performance Considerations

- **Target: < 2 seconds** for issue validation
- GitHub API call: ~200-500ms
- Git log search: ~50-200ms
- Code pattern check: ~100-300ms
- **Total: ~350-1000ms** (acceptable overhead)

## Edge Cases

1. **Issue number doesn't exist**
   - Skip check, return no warning

2. **Issue closed but fix reverted**
   - Git history would show revert commit
   - Lower confidence score

3. **Issue mentions multiple files**
   - Check all mentioned files
   - Aggregate confidence scores

4. **False positive (issue closed, but fix incomplete)**
   - WARNING (not blocking) allows override
   - Human reviews and decides

## Testing Strategy

```python
# Test Case 1: Recently closed duplicate issue
assert check_issue_already_resolved(159)["confidence"] > 0.8

# Test Case 2: Open issue, no commits
assert check_issue_already_resolved(9999)["confidence"] == 0.0

# Test Case 3: Closed issue, old commit (30 days ago)
assert check_issue_already_resolved(100)["confidence"] < 0.5
```

## Rollout Strategy

1. **Week 1**: Deploy as WARNING only (not blocking)
2. **Week 2**: Monitor false positive rate
3. **Week 3**: Adjust confidence thresholds based on data
4. **Week 4**: Add UI integration

## Success Metrics

- **Reduce duplicate workflows by 80%**
- **False positive rate < 10%**
- **Check performance < 2 seconds**
- **User satisfaction: Fewer "why did this fail?" questions**

## Related Issues

- Closes: N/A (new feature)
- Related: #156, #157, #159 (inspired by these duplicates)
- Depends on: Preflight check system (already exists)

---

**Status**: Design Complete - Ready for Implementation
**Estimated Time**: 2-3 hours for Phase 1
**Priority**: Medium-High (prevents wasted compute)
