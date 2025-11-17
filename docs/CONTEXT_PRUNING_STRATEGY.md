# Context Pruning Strategy

**Problem:** ADW workflows load full conversation history on each iteration, causing:
- Token bloat (200K+ tokens per iteration)
- Cache inefficiency (modified files = cache misses)
- Quota consumption (4.6M tokens for simple workflows)

**Goal:** Reduce context loading by 60-80% without sacrificing quality

**Status:** Planning (Not started)
**Priority:** HIGH - Directly impacts quota limits
**Estimated Effort:** 1-2 weeks

---

## Problem Analysis

### Current Behavior (Issue #35 Example)

**Test Phase - 4 Iterations:**
```
Iteration 1: Load 200K tokens (prime + plan + build)
Iteration 2: Load 230K tokens (above + test iter 1 output)
Iteration 3: Load 260K tokens (above + test iter 2 output)
Iteration 4: Load 290K tokens (above + test iter 3 output)
Total: 980K tokens just for context loading
```

**What Actually Needed:**
```
Iteration 1: Load 200K tokens (full context - first time)
Iteration 2: Load 50K tokens (current code + last test failures)
Iteration 3: Load 50K tokens (current code + last test failures)
Iteration 4: Load 50K tokens (current code + last test failures)
Total: 350K tokens (64% reduction)
```

### Why This Matters for Quota Limits

**Cached tokens count toward quota:**
- Issue #35: 4.6M total tokens (including cache)
- Anthropic quota: Based on TOTAL tokens (not just fresh tokens)
- Problem: High cache usage = fast quota depletion even with cost savings

**Example:**
- Monthly quota: 300M tokens
- Current usage: 4.6M tokens/workflow × 65 workflows/month = 299M tokens (99.7% quota)
- With pruning: 1.8M tokens/workflow × 65 workflows/month = 117M tokens (39% quota)

---

## Solution: Conversation Snapshots

### Core Concept

Instead of loading the ENTIRE conversation history, create **phase-boundary snapshots** that contain only essential context.

### Architecture

```python
# app/server/core/context_pruner.py

class ConversationSnapshot:
    """Snapshot of conversation at a phase boundary."""

    def __init__(self, phase: str, iteration: int = 1):
        self.phase = phase
        self.iteration = iteration
        self.timestamp = datetime.now()

        # Essential context only
        self.task_summary: str = ""           # "Implement pattern signatures"
        self.current_files: List[str] = []    # Only files touched this phase
        self.current_state: str = ""          # "Testing phase, 3 tests failing"
        self.last_result: Dict = {}           # Last test/build/review result
        self.next_actions: List[str] = []     # What to do next

    def to_prompt(self) -> str:
        """Convert snapshot to compact prompt (~5K tokens vs 200K full history)."""
        return f"""
## Task Summary
{self.task_summary}

## Current State ({self.phase}, Iteration {self.iteration})
{self.current_state}

## Modified Files ({len(self.current_files)} files)
{chr(10).join(f"- {f}" for f in self.current_files[:10])}

## Last Result
{json.dumps(self.last_result, indent=2)[:500]}

## Next Actions
{chr(10).join(f"{i+1}. {action}" for i, action in enumerate(self.next_actions))}
"""

    def estimate_tokens(self) -> int:
        """Estimate token count of this snapshot."""
        return len(self.to_prompt()) // 4  # Rough estimate
```

### Implementation Phases

#### Phase 1: Snapshot Creation (Week 1, Days 1-2)

**Deliverables:**
- `app/server/core/context_pruner.py` (~300 lines)
- Snapshot models and serialization
- Integration points in ADW workflows

**Where to Create Snapshots:**
```python
# In adw_plan_iso.py - End of planning phase
snapshot = ConversationSnapshot(phase="plan")
snapshot.task_summary = plan_response.output[:500]
snapshot.current_files = []  # No files yet
snapshot.current_state = "Planning complete, ready to implement"
snapshot.next_actions = ["Implement core module", "Write tests"]
state.update(context_snapshot=snapshot.to_dict())

# In adw_build_iso.py - End of build phase
snapshot = ConversationSnapshot(phase="build")
snapshot.task_summary = state.get("task_summary")
snapshot.current_files = get_git_modified_files(worktree_path)
snapshot.current_state = "Implementation complete, ready to test"
snapshot.last_result = {"files_created": 2, "lines_added": 907}
snapshot.next_actions = ["Run tests", "Fix any failures"]
state.update(context_snapshot=snapshot.to_dict())

# In adw_test_iso.py - Each iteration
snapshot = ConversationSnapshot(phase="test", iteration=iteration)
snapshot.task_summary = state.get("task_summary")
snapshot.current_files = state.get("modified_files", [])
snapshot.current_state = f"{failed_count} tests failing"
snapshot.last_result = {"passed": passed_count, "failed": failed_count, "failures": failures[:5]}
snapshot.next_actions = ["Fix failing tests", "Re-run test suite"]
state.update(context_snapshot=snapshot.to_dict())
```

#### Phase 2: Snapshot Loading (Week 1, Days 3-4)

**Deliverables:**
- Modified agent execution to load snapshots
- Fallback to full context if snapshot missing
- A/B testing framework

**Integration:**
```python
# In adw_modules/agent.py - execute_template function

def execute_template(request: AgentTemplateRequest) -> AgentPromptResponse:
    """Execute agent with optional snapshot context."""

    # Load snapshot if available and iteration > 1
    state = ADWState.load(request.adw_id)
    snapshot_dict = state.get("context_snapshot")

    if snapshot_dict and should_use_snapshot(request):
        # Use compact snapshot context
        snapshot = ConversationSnapshot.from_dict(snapshot_dict)
        prompt = build_prompt_from_snapshot(snapshot, request)
        logger.info(f"Using snapshot context (~{snapshot.estimate_tokens()}K tokens)")
    else:
        # Use full conversation history (current behavior)
        prompt = build_full_prompt(request)
        logger.info(f"Using full context (~{estimate_full_context()}K tokens)")

    # Execute with Claude
    response = claude_api_call(prompt)
    return response
```

#### Phase 3: Intelligent Pruning Rules (Week 1, Days 5-7)

**Deliverables:**
- Pruning heuristics per phase
- Token budget management
- Metrics tracking

**Pruning Rules:**
```python
def should_use_snapshot(request: AgentTemplateRequest) -> bool:
    """Determine if snapshot should be used instead of full context."""

    # Rule 1: Always use full context for first iteration
    state = ADWState.load(request.adw_id)
    iteration = state.get(f"{request.agent_name}_iteration", 1)
    if iteration == 1:
        return False

    # Rule 2: Use snapshot for test/build retry iterations
    if request.agent_name in ["test_runner", "build_executor"] and iteration > 1:
        return True

    # Rule 3: Use snapshot if context size > threshold
    estimated_full_context = estimate_full_context_size(request.adw_id)
    if estimated_full_context > 150_000:  # 150K tokens
        return True

    # Rule 4: Use snapshot if previous iteration succeeded
    last_success = state.get(f"{request.agent_name}_last_success", False)
    if last_success and iteration > 2:
        return True

    # Default: Use full context
    return False


def build_prompt_from_snapshot(
    snapshot: ConversationSnapshot,
    request: AgentTemplateRequest
) -> str:
    """Build minimal prompt from snapshot."""

    # Load only essential files
    file_contents = {}
    for file_path in snapshot.current_files[:10]:  # Limit to 10 most recent
        content = read_file(file_path, max_lines=500)  # Truncate large files
        file_contents[file_path] = content

    prompt = f"""
# Context Snapshot ({snapshot.phase.upper()} Phase)

{snapshot.to_prompt()}

## File Contents (Last Modified)
"""

    for file_path, content in file_contents.items():
        prompt += f"\n### {file_path}\n```\n{content}\n```\n"

    # Add current command/request
    prompt += f"\n## Current Task\n{request.slash_command}\n"

    return prompt
```

#### Phase 4: Validation & Metrics (Week 2)

**Deliverables:**
- A/B testing on 10 workflows
- Metrics dashboard integration
- Documentation

**Success Criteria:**
- [ ] 60%+ token reduction on iterations 2+
- [ ] No quality degradation (test pass rates unchanged)
- [ ] Cache hit rate improves (less context = more stable cache)
- [ ] Quota consumption reduced by 50%+

**Metrics to Track:**
```python
# In app/server/core/workflow_analytics.py

def track_pruning_metrics(workflow_id: str, agent_name: str):
    """Track context pruning effectiveness."""

    metrics = {
        "workflow_id": workflow_id,
        "agent_name": agent_name,
        "full_context_tokens": estimate_full_context(),
        "snapshot_tokens": estimate_snapshot(),
        "tokens_saved": full_context - snapshot,
        "reduction_percentage": (tokens_saved / full_context) * 100,
        "cache_hit_rate": get_cache_hit_rate(workflow_id),
        "success": response.success,  # Did task complete successfully?
        "quality_score": calculate_quality_score(response)
    }

    # Store in database
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO context_pruning_metrics
        (workflow_id, agent_name, full_context_tokens, snapshot_tokens,
         tokens_saved, reduction_percentage, cache_hit_rate, success, quality_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tuple(metrics.values()))
```

---

## Database Schema

```sql
-- Migration: Add context pruning metrics table

CREATE TABLE IF NOT EXISTS context_pruning_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    iteration INTEGER DEFAULT 1,

    -- Token measurements
    full_context_tokens INTEGER NOT NULL,
    snapshot_tokens INTEGER NOT NULL,
    tokens_saved INTEGER NOT NULL,
    reduction_percentage REAL NOT NULL,

    -- Cache efficiency
    cache_hit_rate REAL,
    cache_tokens INTEGER,

    -- Quality metrics
    success BOOLEAN NOT NULL,
    quality_score REAL,  -- 0-100 based on output quality

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (workflow_id) REFERENCES workflow_history(id)
);

CREATE INDEX idx_pruning_workflow ON context_pruning_metrics(workflow_id);
CREATE INDEX idx_pruning_agent ON context_pruning_metrics(agent_name);
```

---

## Expected Impact

### Token Reduction

| Phase | Current (Full Context) | With Snapshots | Savings |
|-------|------------------------|----------------|---------|
| Planning (Iter 1) | 200K | 200K | 0% (baseline) |
| Build (Iter 1) | 220K | 220K | 0% (baseline) |
| Test (Iter 1) | 240K | 240K | 0% (baseline) |
| Test (Iter 2) | 270K | 60K | 78% |
| Test (Iter 3) | 300K | 65K | 78% |
| Test (Iter 4) | 330K | 70K | 79% |
| Review (Iter 1) | 350K | 80K | 77% |
| Document (Iter 1) | 370K | 90K | 76% |
| **Total** | **2.28M** | **1.02M** | **55%** |

### Quota Impact

**Before Pruning:**
- Workflow tokens: 4.6M (with cache)
- 65 workflows/month: 299M tokens (99.7% of 300M quota)
- Risk: HIGH - Constantly near quota limit

**After Pruning:**
- Workflow tokens: 1.8M (with cache + pruning)
- 65 workflows/month: 117M tokens (39% of 300M quota)
- Risk: LOW - Comfortable headroom

**Cost Impact:**
- Before: $3.28/workflow
- After: $1.91/workflow (42% reduction)
- Monthly savings: $89/month

---

## Risks & Mitigations

### Risk 1: Quality Degradation
**Symptom:** Agent can't complete task without full context
**Mitigation:**
- Fallback to full context if snapshot fails
- A/B test on non-critical workflows first
- Track quality scores

### Risk 2: Snapshot Too Aggressive
**Symptom:** Snapshot missing critical information
**Mitigation:**
- Tune pruning rules based on metrics
- Include "context breadcrumbs" for recovery
- User can force full context with flag

### Risk 3: Implementation Complexity
**Symptom:** Hard to maintain, breaks existing workflows
**Mitigation:**
- Feature flag to enable/disable pruning
- Gradual rollout (test phase only → all phases)
- Comprehensive logging

---

## Implementation Checklist

- [ ] **Week 1, Days 1-2:** Implement ConversationSnapshot class
- [ ] **Week 1, Days 1-2:** Add snapshot creation in plan/build/test phases
- [ ] **Week 1, Days 3-4:** Modify execute_template to load snapshots
- [ ] **Week 1, Days 3-4:** Implement pruning rules (should_use_snapshot)
- [ ] **Week 1, Days 5-7:** Add metrics tracking
- [ ] **Week 1, Days 5-7:** Create database migration for pruning metrics
- [ ] **Week 2, Days 1-3:** A/B test on 10 workflows
- [ ] **Week 2, Days 1-3:** Validate quality scores (no degradation)
- [ ] **Week 2, Days 4-5:** Tune pruning thresholds based on data
- [ ] **Week 2, Days 4-5:** Document usage and best practices
- [ ] **Week 2, Days 4-5:** Deploy to production with feature flag

---

## Success Metrics

### Primary Goals
- [ ] ✅ 55%+ token reduction on workflows with multiple iterations
- [ ] ✅ No quality degradation (95%+ tasks complete successfully)
- [ ] ✅ 50%+ quota usage reduction
- [ ] ✅ Improved cache hit rates (more stable context = better caching)

### Secondary Goals
- [ ] ✅ Cost reduction: 40%+ per workflow
- [ ] ✅ Faster execution (less context = faster API calls)
- [ ] ✅ Documentation complete

---

## Future Enhancements

### Phase 5: Smart Context Compression (Future)
- Use Claude to summarize conversation history
- Generate "semantic snapshots" (not just metadata)
- Adaptive compression based on task complexity

### Phase 6: Context Prediction (Future)
- ML model predicts what context will be needed
- Preload only relevant files
- Dynamic context expansion if needed

### Phase 7: Cross-Workflow Learning (Future)
- Share snapshots across similar workflows
- "This test failure looks like workflow #123, here's the fix pattern"
- Pattern-based context templates

---

## Getting Started

**To implement this strategy:**

1. Read this document fully
2. Review Phase 1.1 implementation (pattern signatures) for code style
3. Start with Phase 1 (Snapshot Creation) - lowest risk
4. Test on a single workflow (use --enable-pruning flag)
5. Validate metrics before broader rollout
6. Iterate based on data

**Questions? See:**
- Context efficiency analysis: `PHASE_2B_CONTEXT_EFFICIENCY_ANALYSIS.md`
- Out-loop coding plan: `OUT_LOOP_CODING_IMPLEMENTATION_PLAN.md`

---

**Last Updated:** 2025-11-17
**Status:** Planning Complete - Ready for Implementation
**Estimated Completion:** 2 weeks from start
