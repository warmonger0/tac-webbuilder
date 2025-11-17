# Anthropic API Usage Analysis & Optimization Recommendations

**Date:** November 15, 2025
**Issue:** Hit monthly API token limits despite having credits remaining
**Current Usage:** 311M tokens in November (primarily cached input tokens)

---

## Summary of the Issue

### What Happened

1. **ADW Workflow Stalled**
   - Issue #33 (Phase 3E implementation) stopped mid-execution
   - Stalled after classification step, before branch name generation
   - No error messages in logs - silent failure

2. **Root Cause Identified**
   - Anthropic API quota exhausted: "You have reached your specified API usage limits"
   - Despite having **$37.73 in credits remaining**
   - Despite being a **Claude Max $200/month subscriber**

3. **Usage Analysis**
   - **311,531,851 input tokens** consumed in November
   - **3,332,312 output tokens** consumed
   - Major spike on **Nov 9** (~100M tokens in one day)
   - Most tokens were **cached** (10% cost) but still counted toward limits

4. **Resolution**
   - Upgraded to next usage tier in Anthropic Console
   - Immediate issue resolved, but underlying usage problem remains

---

## Why Usage Is So High

### 1. **ADW Workflows Are Token-Intensive**

Each ADW workflow (e.g., `adw_plan_iso.py`) spawns **multiple Claude Code sessions**:

```
Single ADW Workflow → Multiple Claude Sessions:
├── Issue Classification    (~50K tokens)
├── Branch Name Generation  (~30K tokens)
├── Implementation Planning  (~500K-2M tokens)
├── Code Implementation     (~1M-5M tokens)
├── Testing & Validation    (~500K-1M tokens)
└── Code Review            (~300K-1M tokens)

Total per workflow: 2.5M - 10M tokens
```

### 2. **Context Loading for Each Session**

Each Claude Code session loads:
- **Project files** (codebase context)
- **Documentation** (`.claude/` directory)
- **Issue descriptions** (often verbose with code examples)
- **Previous conversation history** (if applicable)

**Example from Issue #33:**
- Issue body: **~15,000 tokens** (entire Phase 3E spec with code examples)
- Loaded **multiple times** across different workflow steps

### 3. **Caching Helps Cost, Not Limits**

- Cached tokens cost **10% of normal price** ✅ Good for budget
- Cached tokens count **100% toward rate/monthly limits** ❌ Bad for quotas
- Your usage shows heavy caching (green spikes in graph)
- You're being cost-efficient but hitting limits faster

### 4. **Automated Triggering**

From webhook logs, ADW workflows are triggered automatically:
- On issue comments containing `adw_` commands
- Potentially running multiple workflows concurrently
- No manual approval gate before consuming tokens

---

## Token Usage Breakdown (Estimated)

Based on 311M tokens over ~15 days in November:

| Source | Est. Daily Tokens | Est. Monthly Tokens | % of Total |
|--------|------------------|---------------------|------------|
| ADW Planning Sessions | 5M | 150M | 48% |
| ADW Implementation | 8M | 240M | 77% |
| ADW Testing/Review | 2M | 60M | 19% |
| Manual Claude Sessions | 500K | 15M | 5% |
| **Total** | **~20M/day** | **~311M** | **100%** |

**Note:** Overlap exists - implementation includes planning/testing

---

## Recommendations to Reduce Usage

### 🔴 High-Impact (Implement Immediately)

#### 1. **Implement Pre-Flight Cost Estimation**

**Problem:** No visibility into token cost before running workflows
**Solution:** Add cost estimation before each ADW execution

```python
# In adws/adw_modules/cost_estimator.py
def estimate_workflow_cost(issue: GitHubIssue, workflow_type: str) -> dict:
    """
    Estimate token usage before running workflow.

    Returns:
        {
            'estimated_input_tokens': 2500000,
            'estimated_output_tokens': 150000,
            'estimated_cost_usd': 8.50,
            'warnings': ['High token count due to large issue description']
        }
    """
    # Analyze issue body length
    # Predict workflow complexity
    # Estimate based on historical data
    pass

# Require manual approval if estimate > threshold
```

**Implementation:**
- Add to `adw_plan_iso.py` before starting workflow
- Post estimate to GitHub issue as comment
- Require explicit confirmation if cost > $5 or tokens > 5M

#### 2. **Optimize Issue Descriptions**

**Problem:** Issue #33 has **~15K tokens** in description (full code examples)
**Solution:** Separate specs from issue descriptions

**Current:**
```markdown
# Issue #33
[15K tokens of detailed implementation specs with code examples]
```

**Optimized:**
```markdown
# Issue #33: Phase 3E - Similar Workflows

**Scope:** Implement workflow similarity detection

**Full Spec:** See `docs/PHASE_3E_SIMILAR_WORKFLOWS.md`
**Complexity:** HIGH
**Estimated Cost:** $1-2
```

**Action Items:**
- Move detailed specs to `/docs` directory
- Keep issue bodies under 500 tokens
- Reference documentation files instead of embedding

#### 3. **Implement Lightweight Workflow Mode**

**Problem:** Every workflow loads full context, even for simple tasks
**Solution:** Create tiered workflow system

```bash
# Ultra-lightweight (< 100K tokens)
adw_micro_iso <issue>     # Simple fixes, typos, one-file changes

# Lightweight (< 500K tokens)
adw_lightweight_iso <issue>  # Bug fixes, minor features

# Standard (< 2M tokens)
adw_plan_iso <issue>     # Normal features

# Heavy (< 10M tokens)
adw_plan_iso with advanced model  # Complex refactors
```

**Implementation:**
- Audit existing `adw_lightweight_iso.py` for effectiveness
- Create `adw_micro_iso.py` for trivial changes
- Add auto-routing based on issue complexity

#### 4. **Batch Similar Operations**

**Problem:** Each workflow step spawns a separate Claude session
**Solution:** Combine steps where possible

**Current:**
```
classify_issue()     → New session → 50K tokens
generate_branch()    → New session → 30K tokens
build_plan()         → New session → 2M tokens
```

**Optimized:**
```
plan_and_setup()     → Single session → 1.5M tokens
  ├── Classify issue
  ├── Generate branch name
  └── Create plan outline
```

**Savings:** ~30-40% reduction by eliminating context reloading

---

### 🟡 Medium-Impact (Implement Within 1 Week)

#### 5. **Add Usage Monitoring Dashboard**

**Implementation:**
```bash
# scripts/monitor_api_usage.py
"""
Track daily API usage and alert when approaching limits.

Features:
- Daily token usage by workflow type
- Cost projections for current month
- Alerts when > 75% of monthly limit used
- Recommendations to pause non-critical workflows
"""
```

**Integration:**
- Run as cron job (daily at midnight)
- Post summary to Slack/Discord
- Auto-disable automated workflows at 90% limit

#### 6. **Implement Selective Context Loading**

**Problem:** Loading entire codebase for every session
**Solution:** Load only relevant files

```python
# In adw_modules/agent.py
def build_context(issue: GitHubIssue, workflow_step: str) -> str:
    """
    Load only files relevant to this issue.

    For backend issue → Load only app/server/
    For frontend issue → Load only app/client/
    For docs issue → Load only docs/
    """
    issue_class = classify_issue_type(issue)

    if issue_class == "backend":
        context_files = glob("app/server/**/*.py")
    elif issue_class == "frontend":
        context_files = glob("app/client/src/**/*.{ts,tsx}")
    else:
        context_files = []  # Minimal context

    return build_context_from_files(context_files)
```

**Savings:** 50-70% reduction in input tokens per session

#### 7. **Cache-Aware Workflow Design**

**Problem:** Not optimizing for Anthropic's cache behavior
**Solution:** Structure prompts to maximize cache hits

**Anthropic Caching Rules:**
- Last 1024 tokens of prompt are cacheable
- Cache lasts 5 minutes
- Sequential requests benefit

**Optimization:**
```python
# Structure prompts with static context at the end
prompt = f"""
{dynamic_instruction}  # Changes each time

---
# Static Context (cached)
{project_readme}
{api_documentation}
{code_standards}
"""
```

#### 8. **Implement Workflow Quotas**

**Problem:** No limits on how many workflows can run
**Solution:** Add daily/weekly quotas

```python
# adws/adw_modules/quota_manager.py
DAILY_LIMITS = {
    "adw_plan_iso": 5,           # Max 5 planning workflows/day
    "adw_lightweight_iso": 20,   # Max 20 lightweight/day
    "adw_test_iso": 10,          # Max 10 test runs/day
}

def check_quota(workflow_type: str) -> bool:
    """Return False if quota exceeded for today."""
    pass
```

---

### 🟢 Low-Impact / Long-Term (Nice to Have)

#### 9. **Historical Data Analysis**

Create database to track:
- Token usage per workflow type
- Success/failure rates
- Cost per issue resolved
- Identify inefficient workflows

#### 10. **A/B Test Smaller Models**

For certain tasks, test if Claude Haiku (cheaper, faster) is sufficient:
- Issue classification
- Branch name generation
- Simple code reviews

**Potential Savings:** 80% cost reduction for eligible tasks

#### 11. **Implement Incremental Planning**

Instead of generating full implementation plan upfront:
- Generate high-level plan (Phase 1)
- Generate detailed specs only when ready to implement (Phase 2)
- Avoid wasting tokens on plans that may change

---

## Immediate Action Plan

### This Week

- [ ] **Audit all open issues** - Close or consolidate verbose issue descriptions
- [ ] **Move specs to `/docs`** - Extract long specs from issues #33, #27, etc.
- [ ] **Add cost estimator** to `adw_plan_iso.py`
- [ ] **Set up usage alerts** - Email when hitting 75% of monthly limit
- [ ] **Document workflow selection** - When to use lightweight vs. standard vs. heavy

### Next Week

- [ ] **Implement selective context loading**
- [ ] **Create `adw_micro_iso.py`** for trivial changes
- [ ] **Add workflow quotas** (5 planning workflows/day max)
- [ ] **Test Haiku** for classification/branch generation

### This Month

- [ ] **Build usage monitoring dashboard**
- [ ] **Analyze historical token usage** by workflow type
- [ ] **Optimize caching strategy**
- [ ] **A/B test workflow consolidation** (batch operations)

---

## Expected Impact

### Conservative Estimates

| Optimization | Token Reduction | Implementation Effort |
|--------------|-----------------|---------------------|
| Move specs to docs | 40% | 2 hours |
| Selective context loading | 50% | 8 hours |
| Batch workflow steps | 30% | 16 hours |
| Workflow quotas | 20% | 4 hours |
| Haiku for simple tasks | 15% | 8 hours |

**Combined potential reduction:** 60-70% of current usage
**From 311M → ~100M tokens/month**
**Cost reduction:** ~$400/month → ~$130/month (at standard rates)

---

## Monitoring Strategy

### Weekly Review

Every Monday, review:
1. Total tokens used (input + output)
2. Cost per workflow type
3. Number of workflows triggered
4. Failed/stalled workflows (wasted tokens)
5. Cache hit rate

### Monthly Review

First of each month:
1. Compare to previous month
2. Identify highest-cost workflows
3. Adjust quotas and limits
4. Plan optimization priorities

### Alerts

Set up alerts for:
- Daily usage > 25M tokens
- Single workflow > 10M tokens
- Monthly total > 200M tokens (at 65% of 311M)
- Cost spike (>2x average daily cost)

---

## Conclusion

Your high API usage is driven by:
1. **Token-intensive ADW workflows** (2.5M-10M per workflow)
2. **Verbose issue descriptions** loading repeatedly
3. **Full context loading** for every session
4. **No cost gates** before execution

**Quick wins:**
- Move specs to `/docs` directory → 40% reduction
- Add cost estimator with approval gate
- Implement workflow quotas

**Long-term:**
- Selective context loading
- Batch workflow operations
- Test smaller models for simple tasks

**Target:** Reduce from **311M → 100M tokens/month** (67% reduction)

**Next Steps:**
1. Review this document
2. Prioritize immediate actions
3. Implement cost estimator this week
4. Move specs to `/docs` directory
5. Set up weekly usage review
