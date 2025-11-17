# Out-Loop Coding Implementation Plan

**Vision:** Automatically identify repetitive LLM operations and offload them to deterministic Python scripts over time, reducing token usage by 30-60% while maintaining workflow flexibility.

**Date:** 2025-11-16
**Status:** Planning Phase
**Priority:** HIGH - Strategic cost reduction

---

## Executive Summary

### What We Have (60% Complete)
- ✅ **Database schema** for pattern learning (migration 004 applied)
- ✅ **Workflow analytics** infrastructure (scoring, anomaly detection)
- ✅ **Cost tracking** with detailed breakdowns
- ✅ **External tools** architecture (ADW chaining for test/build)
- ✅ **API quota monitoring** (prevent exhaustion)
- ✅ **Input size analyzer** (detect when to split issues)

### What We Need (40% Missing)
- ❌ **Pattern detection engine** (track repetitive operations automatically)
- ❌ **Context efficiency analysis** (what context was actually needed vs loaded)
- ❌ **Integration layer** (wire existing components together)
- ❌ **Learning algorithms** (auto-discover automation opportunities)
- ❌ **Tool orchestration** (automatically route to scripts vs LLM)

### Expected Impact
- **Token reduction:** 30-60% across all workflows
- **Cost savings:** ~$9-18/month based on current usage
- **API limit safety:** Proactive quota management prevents failures
- **Developer velocity:** Faster workflows with focused context

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     GITHUB ISSUE CREATED                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: INPUT ANALYSIS (Pre-Flight)                           │
│  • Analyze issue size & complexity                              │
│  • Recommend splits if oversized (>300 words, >2 concerns)     │
│  • Estimate token usage & cost                                  │
│  • Check API quota availability                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │ [issue approved]
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: PATTERN MATCHING (Route Decision)                     │
│  • Check operation_patterns table for known patterns            │
│  • Calculate similarity score                                   │
│  • Route to specialized tool if match >70% confidence           │
│  • Fallback to LLM if no match or low confidence               │
└────────────────────────┬────────────────────────────────────────┘
                         │
          ┌──────────────┴───────────────┐
          │                              │
          ▼                              ▼
┌─────────────────────┐      ┌──────────────────────────┐
│  SPECIALIZED TOOL   │      │   LLM WORKFLOW           │
│  (Python Script)    │      │   (Claude Code)          │
│                     │      │                          │
│  • Execute test     │      │  • Full context          │
│  • Run build        │      │  • Creative work         │
│  • Format code      │      │  • Complex reasoning     │
│  • Return compact   │      │  • Track operations      │
│    results only     │      │                          │
└─────────┬───────────┘      └──────────┬───────────────┘
          │                             │
          └──────────────┬──────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: OBSERVABILITY (Learning Loop)                         │
│  • Capture tool_calls, hook_events to database                 │
│  • Track context usage (files accessed, tokens consumed)        │
│  • Record pattern_occurrences                                   │
│  • Calculate cost_savings_log                                   │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 4: PATTERN LEARNING (Auto-Discovery)                     │
│  • Analyze workflow_history for repetitive operations           │
│  • Increment operation_patterns.occurrence_count                │
│  • Calculate potential_monthly_savings                           │
│  • Auto-create GitHub issue if threshold reached:               │
│    - occurrence_count >= 5                                      │
│    - confidence_score >= 70                                     │
│    - potential_monthly_savings >= $0.50                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema Reference

### Tables (Already Exist ✅)

**`operation_patterns`** - Pattern learning core
```sql
- pattern_signature: Unique fingerprint of operation
- occurrence_count: How many times seen
- avg_tokens_with_llm: Cost using LLM approach
- avg_tokens_with_tool: Cost using specialized tool
- potential_monthly_savings: Projected savings
- automation_status: detected → candidate → approved → implemented → active
- confidence_score: 0-100 (based on consistency)
```

**`tool_calls`** - Track all tool invocations
```sql
- tool_name: Which tool was called
- duration_seconds: How long it took
- tokens_saved: Compared to LLM approach
- cost_saved_usd: Dollar savings
```

**`pattern_occurrences`** - Links workflows to patterns
```sql
- pattern_id: Reference to operation_patterns
- workflow_id: Which workflow exhibited this pattern
- similarity_score: How closely it matched
```

**`hook_events`** - Raw observability data
```sql
- event_type: PreToolUse, PostToolUse, UserPromptSubmit, etc.
- payload: Full event data (JSON)
- processed: For pattern learning queue
```

**`cost_savings_log`** - ROI tracking
```sql
- optimization_type: tool_call, input_split, pattern_offload, inverted_flow
- tokens_saved: Actual savings measured
- cost_saved_usd: Dollar impact
```

**`adw_tools`** - Registry of available specialized tools
```sql
- tool_name: Unique identifier
- script_path: Path to executable
- input_patterns: Trigger keywords (JSON array)
- avg_cost_usd: Performance metrics
- success_rate: Reliability tracking
```

---

## Implementation Phases

### Phase 1: Pattern Detection Engine (Week 1)
**Goal:** Start tracking repetitive operations automatically

#### 1.1 Create Pattern Detector Module
**File:** `app/server/core/pattern_detector.py`

**Key Functions:**
```python
def extract_operation_signature(workflow: Dict) -> str:
    """
    Generate unique signature for an operation.

    Example signatures:
    - "test:pytest:backend" - Running pytest on backend
    - "build:typecheck:frontend" - Running typecheck on frontend
    - "format:prettier:all" - Running prettier on all files
    """
    pass

def detect_patterns_in_workflow(workflow: Dict) -> List[str]:
    """
    Analyze workflow and extract operation patterns.

    Looks at:
    - nl_input keywords
    - tool_calls made
    - files_accessed
    - error_messages (pattern of failures)
    """
    pass

def record_pattern_occurrence(pattern_signature: str, workflow_id: str):
    """
    Record that we saw this pattern in a workflow.
    Updates operation_patterns table.
    """
    pass

def update_pattern_statistics(pattern_id: int, workflow: Dict):
    """
    Update avg_tokens_with_llm, confidence_score based on new data.
    """
    pass
```

#### 1.2 Integrate into Workflow Sync
**File:** `app/server/core/workflow_history.py`

**Modification:**
```python
def sync_workflow_history():
    # ... existing sync logic ...

    # NEW: Pattern learning pass
    logger.info("[SYNC] Phase: Pattern Learning")
    for workflow in workflows:
        patterns = pattern_detector.detect_patterns_in_workflow(workflow)

        for pattern_sig in patterns:
            pattern_detector.record_pattern_occurrence(
                pattern_sig,
                workflow['workflow_id']
            )
```

#### 1.3 Test with Historical Data
**Script:** `scripts/backfill_pattern_learning.py`

Run pattern detection on existing workflow_history to seed the database.

**Expected output after Phase 1:**
```sql
SELECT * FROM operation_patterns ORDER BY occurrence_count DESC LIMIT 10;

-- Results show most common operations:
-- test:pytest:backend (count: 15)
-- build:typecheck:both (count: 12)
-- test:vitest:frontend (count: 8)
```

---

### Phase 2: Context Efficiency Analysis (Week 1-2)
**Goal:** Track what context was actually needed vs what was loaded

#### 2.1 Context Usage Tracker
**File:** `app/server/core/context_tracker.py`

**Key Functionality:**
```python
def track_file_access(workflow_id: str, file_path: str, access_type: str):
    """
    Record when a file is read/written during workflow.
    Stored in hook_events table with event_type='FileAccess'.
    """
    pass

def calculate_context_efficiency(workflow_id: str) -> Dict:
    """
    Analyze what context was loaded vs what was actually used.

    Returns:
        {
            'files_loaded': 150,
            'files_accessed': 23,
            'efficiency': 15.3,  # 23/150 = 15.3% actually used
            'recommended_context': ['src/**/*.py', 'tests/**/*.py']
        }
    """
    pass
```

#### 2.2 Hook Integration
**File:** `.claude/hooks/post_tool_use.py` (new)

Capture file access patterns from tool use events.

#### 2.3 Context Recommendations
**File:** `app/server/core/context_optimizer.py`

```python
def build_context_profile(pattern_signature: str) -> Dict:
    """
    Analyze all workflows matching this pattern to determine
    typical context requirements.

    Returns:
        {
            'typical_files': ['src/api/*.py', 'tests/integration/*.py'],
            'typical_docs': ['.claude/references/api_endpoints.md'],
            'avg_files_loaded': 45,
            'avg_tokens_saved_with_profile': 15000
        }
    """
    pass
```

**Expected output after Phase 2:**
```python
# For "test:pytest:backend" pattern
{
    'files_loaded_avg': 150,
    'files_accessed_avg': 25,
    'efficiency': 16.7,
    'token_waste': 45000,  # 150-25 = 125 files × 360 tokens/file
    'recommended_glob': ['app/server/**/*.py', 'app/server/tests/**/*.py']
}
```

---

### Phase 3: Automated Tool Routing (Week 2)
**Goal:** Automatically route operations to specialized tools

#### 3.1 Pattern Matcher Engine
**File:** `app/server/core/pattern_matcher.py`

```python
def match_input_to_pattern(nl_input: str) -> Optional[Dict]:
    """
    Check if input matches a known pattern with high confidence.

    Returns pattern info if match, None otherwise.
    """
    # Query operation_patterns where automation_status='active'
    # Calculate similarity scores
    # Return best match if confidence >= 70
    pass

def route_to_tool(pattern: Dict, workflow_context: Dict) -> Dict:
    """
    Execute specialized tool for this pattern.

    Returns:
        {
            'tool_name': 'run_test_workflow',
            'result': {...},
            'tokens_saved': 48000,
            'cost_saved_usd': 0.144
        }
    """
    pass
```

#### 3.2 ADW Integration
**File:** `adws/adw_sdlc_iso.py` (modify)

```python
def execute_adw(issue_number, adw_id):
    # Load workflow state
    state = load_state(adw_id)

    # NEW: Check for pattern match
    pattern = pattern_matcher.match_input_to_pattern(state['nl_input'])

    if pattern and pattern['automation_status'] == 'active':
        logger.info(f"Pattern match found: {pattern['pattern_signature']}")

        # Route to specialized tool
        result = pattern_matcher.route_to_tool(pattern, state)

        # Record cost savings
        log_cost_savings(
            optimization_type='pattern_offload',
            workflow_id=state['workflow_id'],
            pattern_id=pattern['id'],
            tokens_saved=result['tokens_saved']
        )

        # Update state with result
        state['external_results'] = result['result']
        save_state(state)

        return result
    else:
        # Fallback to LLM
        logger.info("No pattern match - using LLM workflow")
        return execute_with_llm(state)
```

#### 3.3 Tool Registry Population
**Script:** `scripts/register_tools.py`

Register existing external tools in `adw_tools` table:
```python
register_tool(
    tool_name='run_test_workflow',
    script_path='adws/adw_test_workflow.py',
    input_patterns=['run tests', 'test suite', 'pytest', 'vitest'],
    status='active'
)

register_tool(
    tool_name='run_build_workflow',
    script_path='adws/adw_build_workflow.py',
    input_patterns=['build', 'typecheck', 'compile'],
    status='active'
)
```

**Expected output after Phase 3:**
```
Issue #45: "Run the test suite"
✅ Pattern matched: test:pytest:backend (confidence: 85%)
🚀 Routing to run_test_workflow tool
💰 Saved 48,000 tokens ($0.144)
```

---

### Phase 4: Auto-Discovery & Recommendations (Week 3)
**Goal:** System automatically suggests new automation opportunities

#### 4.1 Pattern Analysis Job
**File:** `scripts/analyze_patterns.py` (cron job - runs weekly)

```python
def analyze_automation_candidates():
    """
    Find patterns that meet automation threshold:
    - occurrence_count >= 5
    - confidence_score >= 70
    - potential_monthly_savings >= $0.50
    - automation_status = 'detected' or 'candidate'
    """

    candidates = db.query("""
        SELECT * FROM operation_patterns
        WHERE occurrence_count >= 5
        AND confidence_score >= 70
        AND potential_monthly_savings >= 0.50
        AND automation_status IN ('detected', 'candidate')
        ORDER BY potential_monthly_savings DESC
    """)

    for pattern in candidates:
        # Update status to 'candidate'
        db.update_pattern_status(pattern['id'], 'candidate')

        # Create GitHub issue
        create_automation_suggestion_issue(pattern)
```

#### 4.2 GitHub Issue Template
```markdown
## 🤖 Automation Opportunity Detected

**Pattern:** {pattern_signature}
**Frequency:** Observed {occurrence_count} times
**Potential Savings:** ${potential_monthly_savings}/month (${potential_monthly_savings * 12}/year)

### Analysis

This pattern has been detected in {occurrence_count} workflows with high consistency:

**Current approach (LLM):**
- Avg tokens: {avg_tokens_with_llm:,}
- Avg cost: ${avg_cost_with_llm:.4f}

**Optimized approach (Tool):**
- Estimated tokens: {estimated_tokens_with_tool:,}
- Estimated cost: ${estimated_cost_with_tool:.4f}
- **Savings per use:** ${savings_per_use:.4f} ({savings_percent}%)

### Typical Operations
{typical_operations_json}

### Recommended Implementation

Create script: `adws/adw_{tool_name}_workflow.py`

**Input patterns:** {input_patterns}
**Expected behavior:** {expected_behavior}

### Recent Examples
{list_of_recent_workflow_ids}

---
**Labels:** automation-candidate, cost-optimization
**Priority:** {priority_based_on_savings}
```

**Expected output after Phase 4:**
```
GitHub Issue #102 created: "Automation Opportunity: dependency-update"
- Frequency: 7 times
- Savings: $1.20/month
- Confidence: 82%
```

---

### Phase 5: Proactive Quota Management (Week 3-4)
**Goal:** Prevent API quota exhaustion through intelligent forecasting

#### 5.1 Token Usage Forecasting
**File:** `app/server/core/quota_forecaster.py`

```python
def forecast_monthly_usage() -> Dict:
    """
    Predict monthly token usage based on current trends.

    Returns:
        {
            'current_month_tokens': 185_000_000,
            'days_remaining': 14,
            'projected_total': 345_000_000,
            'quota_limit': 300_000_000,
            'risk_level': 'high',  # will exceed limit
            'recommendations': [...]
        }
    """
    # Analyze last 7 days usage
    # Calculate daily average
    # Project to end of month
    # Compare to known limits
    pass

def should_throttle_workflows() -> Tuple[bool, str]:
    """
    Decide if new workflows should be delayed to preserve quota.
    """
    forecast = forecast_monthly_usage()

    if forecast['risk_level'] == 'high':
        return True, f"Approaching monthly limit: {forecast['projected_total']:,} / {forecast['quota_limit']:,}"

    return False, None
```

#### 5.2 Workflow Budgets
**File:** `app/server/core/workflow_budgets.py`

```python
def estimate_workflow_cost(issue_body: str, workflow_type: str) -> Dict:
    """
    Predict token usage before starting workflow.

    Uses historical data from similar workflows.
    """
    # Find similar workflows by:
    # - Similar word count in issue
    # - Same workflow_type
    # - Similar complexity

    # Return avg token usage
    pass

def check_budget(estimated_tokens: int) -> Tuple[bool, str]:
    """
    Verify workflow doesn't exceed cost budget.

    Default budget: 5M tokens per workflow
    """
    if estimated_tokens > 5_000_000:
        return False, f"Estimated {estimated_tokens:,} tokens exceeds budget"

    return True, None
```

#### 5.3 Integration into ADW Executor
```python
def can_start_adw(issue_number: int, workflow_type: str) -> Tuple[bool, str]:
    # Check 1: API quota available
    quota_ok, quota_msg = api_quota.can_start_adw()
    if not quota_ok:
        return False, quota_msg

    # Check 2: Monthly forecast
    should_throttle, throttle_msg = quota_forecaster.should_throttle_workflows()
    if should_throttle:
        return False, throttle_msg

    # Check 3: Workflow budget
    issue = get_issue(issue_number)
    estimate = workflow_budgets.estimate_workflow_cost(issue['body'], workflow_type)
    budget_ok, budget_msg = workflow_budgets.check_budget(estimate['estimated_tokens'])
    if not budget_ok:
        return False, budget_msg

    return True, None
```

**Expected output after Phase 5:**
```
📊 Monthly Usage Forecast:
- Current: 185M tokens (14 days)
- Projected: 345M tokens (end of month)
- Limit: 300M tokens
⚠️ Risk: HIGH - will exceed limit by 45M tokens

🚦 Throttling enabled - delaying low-priority workflows

Issue #50: "Run tests"
✅ Pre-flight check passed
- Estimated: 2.5M tokens
- Budget: Within limits
- Quota: Available
🚀 Starting workflow...
```

---

## Integration Checklist

### Webhook Integration
- [ ] Call `input_analyzer.analyze_input()` on new issues
- [ ] Post split recommendations as GitHub comments
- [ ] Check quota before auto-triggering ADW
- [ ] Estimate cost and require approval if >$5

### ADW Executor Integration
- [ ] Call `pattern_matcher.match_input_to_pattern()` at start
- [ ] Route to specialized tool if high-confidence match
- [ ] Track operations with `pattern_detector.detect_patterns_in_workflow()`
- [ ] Log cost savings to `cost_savings_log` table

### External Tools Integration
- [ ] Remove `--use-external` flag requirement
- [ ] Auto-enable for test/build operations
- [ ] Register all tools in `adw_tools` table
- [ ] Track success_rate and update automatically

### Observability Integration
- [ ] Capture hook events to `hook_events` table
- [ ] Track file access patterns
- [ ] Record tool calls with token savings
- [ ] Export metrics for dashboard

---

## Testing Strategy

### Phase 1 Testing
```bash
# Test pattern detection on historical data
python scripts/backfill_pattern_learning.py

# Verify patterns detected
sqlite3 app/server/db/workflow_history.db "
  SELECT pattern_signature, occurrence_count, confidence_score
  FROM operation_patterns
  ORDER BY occurrence_count DESC LIMIT 10;
"
```

### Phase 2 Testing
```bash
# Run workflow and track context usage
cd adws/
uv run adw_test_iso.py 42 --track-context

# Check context efficiency report
python scripts/analyze_context_efficiency.py adw-test-123
```

### Phase 3 Testing
```bash
# Test pattern matching
python -c "
from app.server.core.pattern_matcher import match_input_to_pattern
result = match_input_to_pattern('run the backend tests')
print(f'Matched: {result}')
"

# Verify tool routing
cd adws/
uv run adw_sdlc_iso.py 43  # Should auto-route to test tool
```

### Phase 4 Testing
```bash
# Manually trigger pattern analysis
python scripts/analyze_patterns.py

# Check for automation candidate issues created
gh issue list --label automation-candidate
```

### Phase 5 Testing
```bash
# Test quota forecasting
python -c "
from app.server.core.quota_forecaster import forecast_monthly_usage
forecast = forecast_monthly_usage()
print(f'Projected: {forecast[\"projected_total\"]:,} tokens')
print(f'Risk: {forecast[\"risk_level\"]}')
"
```

---

## Success Metrics

### Immediate (After Phase 1-2)
- [ ] **Pattern detection working** - 10+ patterns identified in first week
- [ ] **Context efficiency tracked** - Avg efficiency score calculated
- [ ] **Database populated** - operation_patterns table has data

### Short-term (After Phase 3-4)
- [ ] **Tool routing active** - 40% of test/build operations auto-routed
- [ ] **Cost savings measurable** - cost_savings_log shows $2+ saved
- [ ] **Auto-suggestions created** - 2+ automation opportunity issues

### Long-term (After Phase 5 + 1 month)
- [ ] **Token usage reduced 30%** - From ~20M/day to ~14M/day
- [ ] **Cost savings $9+/month** - Measured in cost_savings_log
- [ ] **No quota incidents** - Forecasting prevents exhaustion
- [ ] **Pattern library grown** - 15+ active automated patterns

---

## Rollback Plan

Each phase can be rolled back independently:

**Phase 1-2 (Observability):**
- Disable pattern tracking in `workflow_history.sync()`
- No impact on existing workflows

**Phase 3 (Tool Routing):**
- Set all patterns to `automation_status='deprecated'`
- Workflows fallback to LLM approach automatically

**Phase 4 (Auto-discovery):**
- Disable cron job
- Delete automation-candidate issues if needed

**Phase 5 (Quota Management):**
- Disable throttling checks
- Remove budget enforcement

---

## Timeline

| Week | Phase | Deliverables | Owner |
|------|-------|--------------|-------|
| 1 | Phase 1 | Pattern detector, backfill script | - |
| 1-2 | Phase 2 | Context tracker, efficiency analysis | - |
| 2 | Phase 3 | Pattern matcher, tool routing | - |
| 3 | Phase 4 | Auto-discovery, GitHub integration | - |
| 3-4 | Phase 5 | Quota forecasting, budgets | - |
| 4 | Testing | E2E validation, documentation | - |

**Total:** 4 weeks to full implementation

---

## Open Questions

1. **Pattern Signature Design:**
   - What granularity? `test:pytest` or `test:pytest:backend:unit`?
   - How to handle variations (pytest vs pytest-xdist)?

2. **Context Profiling:**
   - Should we build ML model for context prediction?
   - Or use simple heuristics based on workflow_type?

3. **Tool Failure Handling:**
   - Max retry attempts before fallback to LLM?
   - Auto-disable tool if success_rate < 80%?

4. **Quota Management:**
   - What's the actual Anthropic quota limit? (unknown from API)
   - Should we pause all ADWs or just low-priority ones?

5. **Human-in-the-Loop:**
   - Require approval before activating new patterns?
   - Or auto-activate if confidence >90%?

---

## Next Steps

**Immediate (This Session):**
1. Review this plan with user
2. Clarify open questions
3. Decide which phase to start with (recommend Phase 1)

**Next Session:**
1. Implement Phase 1: Pattern Detector
2. Backfill historical data
3. Verify patterns detected correctly

**Following Sessions:**
2. Continue through phases sequentially
3. Test each phase before moving forward
4. Adjust based on learnings

---

## References

- **Database schema:** `app/server/db/migrations/004_add_observability_and_pattern_learning.sql`
- **Existing analytics:** `app/server/core/workflow_analytics.py`
- **Cost tracking:** `app/server/core/cost_tracker.py`
- **External tools:** `docs/EXTERNAL_TOOLS_INTEGRATION_GUIDE.md`
- **Cost optimization design:** `docs/COST_OPTIMIZATION_INTELLIGENCE.md`
