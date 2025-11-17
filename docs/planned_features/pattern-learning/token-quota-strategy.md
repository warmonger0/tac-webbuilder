# Token Quota Optimization Strategy

**Problem:** Cached tokens count toward Anthropic API quota limits, causing rapid quota depletion even with cost savings

**Root Cause:** Issue #35 used 4.6M tokens (92.3% cached = 4.23M cached tokens) which still count toward quota

**Goal:** Reduce TOTAL token consumption (cached + non-cached) by 60-70% without sacrificing cost savings

**Status:** Planning (Not started)
**Priority:** CRITICAL - Directly impacts quota limits and workflow capacity
**Estimated Effort:** 2-3 weeks (runs in parallel with other optimizations)

---

## The Quota Problem Explained

### How Anthropic Quotas Work

**All tokens count toward quota:**
```
Total tokens = input_tokens + output_tokens + cached_tokens

Quota consumption = total_tokens (NOT just fresh tokens)
```

**Issue #35 Example:**
```
Input (fresh):     326,432 tokens  (7.7%)
Output:             48,366 tokens  (1.1%)
Cache Hit:       4,234,687 tokens  (91.2%)
Cache Write:        28,413 tokens  (0.6%)
────────────────────────────────────────
Total:           4,635,898 tokens  (100%)

Cost:                $3.28
Quota consumed:      4.6M tokens ← THIS IS THE PROBLEM
```

**Why this matters:**
- Monthly quota: 300M tokens
- Current usage: 4.6M tokens/workflow
- Capacity: 65 workflows/month (299M tokens = 99.7% quota)
- **Risk:** Can't run workflows even though we have budget

---

## Current State Analysis

### Quota Consumption Breakdown

| Component | Tokens | % of Total | Counts Toward Quota? |
|-----------|--------|------------|----------------------|
| Fresh input | 326K | 7.7% | ✅ Yes |
| Output | 48K | 1.1% | ✅ Yes |
| Cached input | 4.23M | 91.2% | ✅ Yes (PROBLEM!) |
| **Total** | **4.6M** | **100%** | **✅ Yes** |

**The paradox:**
- High cache efficiency (92.3%) saves money ✅
- But still consumes 4.6M tokens from quota ❌
- Need to reduce TOTAL tokens, not just fresh tokens

---

## Optimization Strategy

### Three-Pronged Approach

1. **Reduce Cacheable Context** (Target: -60% cached tokens)
   - Context pruning (snapshots instead of full history)
   - Smaller file loads (only modified files)
   - Truncate large files

2. **Reduce Fresh Tokens** (Target: -70% fresh tokens)
   - External tools for test/build (outloop system)
   - Structured state instead of conversational history
   - Compact error reporting

3. **Improve Cache Stability** (Target: 95%+ cache hit rate)
   - Stable prompts across iterations
   - Deterministic file ordering
   - Avoid re-loading unchanged context

---

## Implementation Phases

### Phase 1: Context Reduction (Week 1)

**See:** `CONTEXT_PRUNING_STRATEGY.md` for detailed plan

**Key Actions:**
- Implement conversation snapshots (~5K tokens vs 200K full history)
- Load only modified files (not entire codebase)
- Truncate large files to 500 lines max

**Expected Impact:**
```
Before: 4.6M total tokens (92.3% cached)
After:  1.8M total tokens (95% cached)
Reduction: 61% total tokens
```

**Quota Impact:**
```
Before: 65 workflows/month × 4.6M = 299M tokens (99.7% quota)
After:  65 workflows/month × 1.8M = 117M tokens (39% quota)
Headroom: +182M tokens (60% quota freed)
```

---

### Phase 2: External Tools (Week 2)

**Status:** Partially implemented (needs to be default)

**Key Actions:**
- ✅ Default `--use-external` flag (DONE today!)
- Implement external build tools
- Structured result formats (JSON, not full logs)

**Expected Impact:**
```
Test phase before:    1.1M tokens
Test phase after:     12K tokens
Reduction:            98.9% for test phase
```

**Per-workflow savings:**
```
Before: 4.6M tokens
After:  3.5M tokens (just from test phase optimization)
Reduction: 24%
```

---

### Phase 3: Output Token Reduction (Week 2)

**Problem:** Output tokens (48K in Issue #35) never get cached

**Key Actions:**

1. **Structured State Instead of Comments**
   ```python
   # Instead of:
   make_issue_comment(issue_number, full_test_results)  # 30K tokens output

   # Do:
   state.update(test_results=compact_summary)  # 1K tokens output
   make_issue_comment(issue_number, summary_only)  # 2K tokens output
   ```

2. **Compact Error Reporting**
   ```python
   # Instead of full tracebacks:
   {
       "failed_tests": [
           {"name": "test_foo", "file": "test.py:42", "error": "AssertionError: ..."}
       ]
   }

   # Use error codes:
   {
       "failed_tests": [
           {"name": "test_foo", "loc": "test.py:42", "code": "ASSERT_FAIL"}
       ]
   }
   ```

3. **Suppress Verbose Logs**
   ```python
   # Don't output full pytest/vitest logs to Claude
   # Just parse and return failures
   ```

**Expected Impact:**
```
Output tokens before:  48K
Output tokens after:   8K
Reduction:             83%
```

**Cost/Quota Impact:**
```
Output tokens cost 5x input tokens
Savings: 40K tokens × $15/M = $0.60/workflow
Quota: 40K tokens saved per workflow
```

---

### Phase 4: Cache Stability (Week 3)

**Goal:** Improve cache hit rate from 92.3% → 95%+

**Key Actions:**

1. **Deterministic Prompts**
   ```python
   # Always use same file order
   files = sorted(get_modified_files())  # Alphabetical

   # Always use same format
   prompt_template = load_template("test_phase.txt")  # Consistent
   ```

2. **Stable Context Windows**
   ```python
   # Don't append to conversation history
   # Use fixed-size snapshot windows

   # Bad: Context grows each iteration
   context = load_full_history()  # 200K → 230K → 260K → 290K

   # Good: Context stays fixed
   context = load_snapshot(last_n=1)  # 50K → 50K → 50K → 50K
   ```

3. **Version Pinning**
   ```python
   # Pin prompt templates to specific versions
   # Changes to prompts invalidate cache

   # Track prompt version in state
   state.update(prompt_version="2024-11-17-v1")
   ```

**Expected Impact:**
```
Cache hit rate before:  92.3%
Cache hit rate after:   95.5%
Fresh tokens reduced:   40% (more cache hits)
```

---

### Phase 5: Intelligent Batching (Week 3)

**Concept:** Group multiple small operations into one API call

**Example: Test Resolution**
```python
# Before: 4 separate API calls for 4 test failures
for test in failed_tests:  # 4 iterations
    fix_test(test)  # 200K tokens × 4 = 800K tokens

# After: 1 API call for all failures
fix_all_tests(failed_tests)  # 220K tokens × 1 = 220K tokens
Savings: 72%
```

**Implementation:**
```python
def resolve_failed_tests_batch(
    failed_tests: List[TestResult],
    adw_id: str,
    worktree_path: str
) -> Dict[str, bool]:
    """Resolve multiple test failures in one API call."""

    # Create batch prompt
    prompt = "Fix the following test failures:\n\n"
    for i, test in enumerate(failed_tests, 1):
        prompt += f"## Test {i}: {test.test_name}\n"
        prompt += f"File: {test.file_path}\n"
        prompt += f"Error: {test.error_message}\n\n"

    # Single API call
    response = execute_template(AgentTemplateRequest(
        agent_name="test_resolver_batch",
        prompt=prompt,
        adw_id=adw_id,
        working_dir=worktree_path
    ))

    # Parse results
    # Return which tests were fixed
```

**Expected Impact:**
```
Test resolution before:  4 calls × 200K = 800K tokens
Test resolution after:   1 call × 220K = 220K tokens
Reduction:               72%
```

---

## Combined Impact

### Token Reduction Cascade

| Optimization | Baseline | After | Reduction |
|--------------|----------|-------|-----------|
| **Baseline** | 4.6M | - | - |
| + Context pruning | 4.6M | 1.8M | -61% |
| + External tools | 1.8M | 1.7M | -6% more |
| + Output reduction | 1.7M | 1.65M | -3% more |
| + Cache stability | 1.65M | 1.5M | -9% more |
| + Intelligent batching | 1.5M | 1.2M | -20% more |
| **Total** | **4.6M** | **1.2M** | **-74%** |

### Quota Impact

**Before optimizations:**
```
Workflow tokens:     4.6M
Monthly workflows:   65
Total tokens/month:  299M (99.7% of 300M quota)
Workflows possible:  65
```

**After all optimizations:**
```
Workflow tokens:     1.2M
Monthly workflows:   250 (quota allows this many)
Total tokens/month:  300M (100% of quota, but 3.8x capacity)
Workflows possible:  250 (3.8x increase)
```

**Or, if we maintain 65 workflows/month:**
```
Workflow tokens:     1.2M
Monthly workflows:   65
Total tokens/month:  78M (26% of 300M quota)
Quota headroom:      222M tokens (74% free)
```

---

## Cost vs Quota Trade-offs

### Understanding the Balance

**The tension:**
- Caching saves money (fresh tokens cost more)
- But cached tokens still count toward quota
- Need to reduce BOTH fresh AND cached tokens

**Strategies:**

1. **Reduce cacheable context** (best of both worlds)
   - Smaller prompts = less to cache
   - Still get high cache hit rate on smaller context
   - Saves quota AND cost

2. **External tools** (reduces fresh tokens)
   - No context loaded for external execution
   - Saves quota AND cost

3. **Structured state** (reduces output tokens)
   - Output never cached (always fresh)
   - High cost per token ($15/M vs $3/M)
   - Saves quota AND cost

**Ideal state:**
```
Context:    50K tokens (cached)    ← 70% reduction
Input:      10K tokens (fresh)     ← 70% reduction
Output:     5K tokens (fresh)      ← 90% reduction
Total:      65K tokens/API call    ← 87% reduction

Cost:       $0.50/workflow         ← 85% reduction
Quota:      1.2M tokens/workflow   ← 74% reduction
```

---

## Implementation Priority

### Immediate (This Week)
1. ✅ **Default external tools** - DONE today!
   - Impact: -1.1M tokens/workflow
   - Effort: 5 minutes (already done)

### High Priority (Weeks 1-2)
2. **Context pruning** - See `CONTEXT_PRUNING_STRATEGY.md`
   - Impact: -2.8M tokens/workflow
   - Effort: 1-2 weeks
   - ROI: HIGHEST

3. **Output reduction**
   - Impact: -40K tokens/workflow
   - Effort: 2-3 days
   - ROI: HIGH (expensive tokens)

### Medium Priority (Week 3)
4. **Cache stability**
   - Impact: -150K tokens/workflow
   - Effort: 3-4 days
   - ROI: MEDIUM

5. **Intelligent batching**
   - Impact: -300K tokens/workflow
   - Effort: 1 week
   - ROI: MEDIUM

---

## Monitoring & Validation

### Metrics to Track

**Per-workflow:**
```sql
CREATE TABLE quota_tracking (
    workflow_id TEXT PRIMARY KEY,
    total_tokens INTEGER,
    fresh_tokens INTEGER,
    cached_tokens INTEGER,
    output_tokens INTEGER,
    cache_hit_rate REAL,
    quota_percentage REAL,
    optimization_flags TEXT,  -- JSON: which optimizations applied
    created_at TIMESTAMP
);
```

**Dashboard widgets:**
- Daily quota consumption (running total)
- Workflows remaining this month (at current rate)
- Average tokens per workflow (7-day rolling)
- Cache hit rate trend
- Optimization effectiveness (before/after comparison)

### Alerts

```python
# Alert if approaching quota
if current_month_tokens > (quota_limit * 0.80):
    send_alert("WARNING: 80% of monthly quota consumed")
    enable_aggressive_throttling()

# Alert on quota-inefficient workflows
if workflow_tokens > 3_000_000:
    send_alert(f"High-quota workflow detected: {workflow_id}")
    log_for_investigation(workflow_id)

# Alert on cache efficiency drop
if cache_hit_rate < 0.90:
    send_alert(f"Cache efficiency dropped to {cache_hit_rate:.1%}")
    investigate_prompt_stability()
```

---

## Success Metrics

### Primary Goals
- [ ] ✅ 70%+ total token reduction (4.6M → 1.4M or less)
- [ ] ✅ 3x workflow capacity increase (65 → 195+ workflows/month)
- [ ] ✅ Cache hit rate ≥ 95%
- [ ] ✅ Cost reduction maintained (ideally improved)

### Secondary Goals
- [ ] ✅ No quality degradation (task success rate unchanged)
- [ ] ✅ Quota headroom ≥ 60% month-end
- [ ] ✅ Output tokens reduced by 80%
- [ ] ✅ Predictable quota consumption (±10% variance)

---

## Risk Management

### Risk 1: Cache Efficiency Drops
**Symptom:** Smaller context = more cache misses
**Mitigation:**
- Test extensively on historical workflows
- A/B test snapshot vs full context
- Fallback to full context if cache drops below 90%

### Risk 2: Quality Degradation
**Symptom:** Tasks fail without full context
**Mitigation:**
- Start with non-critical workflows
- Track success rates closely
- Expand context window if needed (configurable)

### Risk 3: Over-Optimization
**Symptom:** System too complex, hard to maintain
**Mitigation:**
- Implement incrementally (one phase at a time)
- Feature flags for each optimization
- Comprehensive logging and rollback capability

---

## Long-Term Vision

### Auto-Scaling Quota Management

```python
class QuotaManager:
    """Intelligent quota management with auto-scaling."""

    def select_optimization_level(self, remaining_quota: int) -> str:
        """Choose optimization level based on quota headroom."""

        quota_percentage = remaining_quota / self.monthly_quota

        if quota_percentage > 0.60:
            return "minimal"  # Full context, high quality
        elif quota_percentage > 0.30:
            return "balanced"  # Snapshots, external tools
        elif quota_percentage > 0.10:
            return "aggressive"  # Max optimization
        else:
            return "emergency"  # Throttle workflows, queue for next month

    def forecast_end_of_month(self) -> Dict:
        """Predict quota consumption at month-end."""

        days_remaining = days_until_month_end()
        daily_avg = self.get_daily_average_tokens()
        projected = daily_avg * days_remaining

        return {
            "projected_total": projected,
            "quota_limit": self.monthly_quota,
            "will_exceed": projected > self.monthly_quota,
            "headroom": self.monthly_quota - projected,
            "recommended_action": self.recommend_action(projected)
        }
```

---

## Getting Started

**Recommended implementation order:**

1. ✅ **Today:** Default external tools (DONE)
2. **Week 1:** Implement context pruning (highest impact)
3. **Week 1-2:** Output token reduction
4. **Week 2:** Run cost analysis (validate savings)
5. **Week 3:** Cache stability + batching
6. **Week 3:** Deploy monitoring dashboard
7. **Week 4:** Validate metrics, tune thresholds

**Total timeline:** 3-4 weeks to full implementation

---

## Related Documents

- **Context Pruning:** `CONTEXT_PRUNING_STRATEGY.md`
- **Cost Analysis:** `WORKFLOW_COST_ANALYSIS_PLAN.md`
- **Out-Loop Coding:** `OUT_LOOP_CODING_IMPLEMENTATION_PLAN.md`
- **Phase 5 (Quota Mgmt):** `implementation/PHASE_5_QUOTA_MANAGEMENT.md`

---

**Last Updated:** 2025-11-17
**Status:** Planning Complete - Ready for Implementation
**Critical Priority:** Addresses quota exhaustion risk
