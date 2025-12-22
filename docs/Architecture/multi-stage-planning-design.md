# Multi-Stage Planning with Sub-Agents - Architecture Design

**Created:** 2025-12-22
**Status:** Approved for Implementation
**Impact:** Core ADW Planning Enhancement

---

## Executive Summary

This document describes the architectural design for implementing multi-stage planning in ADW workflows using Claude Code's native Task tool for sub-agent delegation. This approach enables component-first planning, automated DRY checking, and context-aware phase boundaries while **reducing costs by ~19%** compared to current monolithic planning.

---

## Problem Statement

### Current Limitations

1. **Monolithic Planning:** Single comprehensive AI call generates entire plan without structured decomposition
2. **No DRY Checking:** Plans don't identify duplicate code opportunities before implementation
3. **Context Blindness:** Phase boundaries don't consider file counts or token requirements
4. **Large Feature Challenges:** 30+ file features create massive context windows, risking:
   - Quota exhaustion
   - Multi-session overflow
   - High token costs
   - Poor phase boundaries

### Cost Impact

- Current lightweight: $0.10-0.30
- Current standard: $3.00-5.00
- Large features (50+ files) can exceed single-session capacity
- No mechanism to optimize phase splitting for context management

---

## Solution: Multi-Stage Planning Architecture

### Core Innovation

Leverage Claude Code CLI's **Task tool** to spawn specialized sub-agents within a single session for:
1. **Component Analysis** - Decompose features into logical components
2. **DRY Checking** - Identify code reuse opportunities
3. **File Context Analysis** - Calculate token requirements and optimal phase boundaries
4. **Plan Synthesis** - Generate comprehensive plan using all sub-agent findings

### Key Architectural Insight

**Previous Misunderstanding:**
- Assumed sub-agents required separate Claude Code subprocess calls
- Estimated 65% cost increase due to context reloading

**Reality:**
- Task tool spawns sub-agents **within the same Claude Code session**
- Sub-agents share parent context (no redundant loading)
- Each sub-agent has focused scope = smaller prompts
- Main agent synthesizes findings = one coherent plan

**Result:** ~19% cost **reduction** vs. current approach

---

## Architecture Overview

### Session Flow

```
Single Claude Code CLI Session
│
├─ STAGE 1: Component Analysis (Task → Explore sub-agent)
│  ├─ Input: Issue description + worktree context
│  ├─ Analysis: Identify backend/frontend/database components
│  ├─ Output: JSON with components + dependencies
│  └─ Tokens: ~40k (focused analysis)
│
├─ STAGE 2: DRY Analysis (Task → codebase-expert sub-agent)
│  ├─ Input: Stage 1 component list
│  ├─ Analysis: Search for similar patterns, existing implementations
│  ├─ Output: JSON with reuse opportunities + duplicate warnings
│  └─ Tokens: ~30k (targeted searches)
│
├─ STAGE 3: File Context Analysis (Task → Explore sub-agent)
│  ├─ Input: Stage 1 components + Stage 2 findings
│  ├─ Analysis: Count files, estimate tokens, calculate phase boundaries
│  ├─ Output: JSON with file groups + token estimates
│  └─ Tokens: ~20k (calculations + small reads)
│
└─ STAGE 4: Plan Synthesis (Main Agent)
   ├─ Input: All sub-agent findings
   ├─ Synthesis: Generate comprehensive implementation plan
   ├─ Output: Complete markdown plan with optimized phases
   └─ Tokens: ~80k (synthesis + plan generation)

Total Session: ~220k tokens ($0.35) vs current 271k ($0.43)
Cost Reduction: 19%
```

### Sub-Agent Types

| Sub-Agent | Purpose | Tools | Context Scope |
|-----------|---------|-------|---------------|
| **Explore** | Codebase research, architecture analysis | Read, Glob, Grep | Read-only, focused searches |
| **codebase-expert** | Code pattern finding, similarity detection | Read, Grep, Glob | Specialized code understanding |
| **Plan** (built-in) | Research mode planning | Read, Glob | Information gathering |

### Custom Sub-Agents (New)

We will define specialized sub-agents in `.claude/subagents/`:

1. **component_analyzer.md** - Component decomposition specialist
2. **dry_checker.md** - Code duplication detection specialist
3. **context_calculator.md** - Token/file counting specialist

---

## Implementation Strategy

### Phase 1: Sub-Agent Definitions (1-2 days)

**Create `.claude/subagents/component_analyzer.md`:**
```markdown
# Component Analyzer Sub-Agent

You are a software architecture specialist focused on component decomposition.

## Your Task
Analyze feature descriptions and break them into discrete, logical components.

## Output Format (JSON)
{
  "components": [
    {
      "name": "UserAuthService",
      "type": "backend|frontend|database|test",
      "description": "Handles user authentication logic",
      "estimated_files": 3,
      "complexity": "low|medium|high",
      "dependencies": ["SessionManager"]
    }
  ],
  "architecture_notes": "...",
  "integration_points": [...]
}

## Analysis Guidelines
- Identify natural separation of concerns
- Look for reusable abstractions
- Consider data flow and dependencies
- Flag tight coupling opportunities
```

**Create `.claude/subagents/dry_checker.md`:**
```markdown
# DRY Checker Sub-Agent

You are a code quality specialist focused on identifying code duplication.

## Your Task
Search codebase for similar patterns that could be reused instead of reimplemented.

## Output Format (JSON)
{
  "reuse_opportunities": [
    {
      "component": "UserProfileAPI",
      "similar_code": "app/server/services/user_service.py",
      "similarity": "high|medium|low",
      "recommendation": "Extend UserService base class instead of creating new service"
    }
  ],
  "duplicate_patterns": [...],
  "refactoring_suggestions": [...]
}

## Search Strategy
- Look for similar function signatures
- Check for duplicate utility functions
- Identify copy-pasted code blocks
- Find opportunities to extract common patterns
```

**Create `.claude/subagents/context_calculator.md`:**
```markdown
# Context Calculator Sub-Agent

You are a context management specialist focused on file grouping and token estimation.

## Your Task
Calculate file counts, estimate token requirements, and recommend phase boundaries.

## Output Format (JSON)
{
  "file_analysis": {
    "backend_files": 12,
    "frontend_files": 8,
    "test_files": 5,
    "total_files": 25
  },
  "token_estimates": {
    "backend_context": "~60k tokens",
    "frontend_context": "~40k tokens",
    "total_context": "~100k tokens"
  },
  "phase_recommendations": {
    "min_phases": 2,
    "recommended_phases": 3,
    "reasoning": "Backend has 12 files (exceeds 10/phase limit), split into 2 phases"
  }
}

## Calculation Rules
- Max 15 files per phase (safe context limit)
- Avg 5k tokens per file (conservative estimate)
- Max 100k tokens per phase (leaves room for conversation)
- Group tightly-coupled files together
```

### Phase 2: ADW Integration (2-3 days)

**Create `adws/adw_plan_multistage_iso.py`:**

```python
#!/usr/bin/env python3
"""
Multi-Stage Planning Workflow with Sub-Agent Delegation

Uses Claude Code's Task tool to spawn specialized sub-agents for:
1. Component analysis
2. DRY checking
3. File context calculation
4. Comprehensive plan synthesis

All happens in ONE Claude Code session for cost efficiency.
"""

import logging
import sys
from pathlib import Path

from adw_modules.agent import AgentTemplateRequest, execute_template
from adw_modules.state import ADWState
from adw_modules.workflow_ops import fetch_github_issue
from adw_modules.worktree_ops import create_or_validate_worktree

logger = logging.getLogger(__name__)


def build_multistage_prompt(issue, worktree_path: str) -> str:
    """
    Construct prompt that instructs Claude Code to use Task tool for sub-agents.
    """
    return f"""
You are planning implementation for GitHub Issue #{issue.number}: {issue.title}

**MULTI-STAGE PLANNING PROCESS:**

STAGE 1: Component Decomposition
- Use Task tool: Task prompt="Analyze this feature and break it into logical components" subagent_type="codebase-expert"
- Load .claude/subagents/component_analyzer.md for guidance
- Identify: backend components, frontend components, database changes, tests
- Output: JSON with components, dependencies, complexity estimates

STAGE 2: DRY Analysis
- Use Task tool: Task prompt="Search for similar code patterns for reuse" subagent_type="codebase-expert"
- Load .claude/subagents/dry_checker.md for guidance
- Search: existing services, similar UI components, duplicate utilities
- Output: JSON with reuse opportunities, duplicate warnings

STAGE 3: File Context Analysis
- Use Task tool: Task prompt="Calculate file counts and token estimates" subagent_type="Explore"
- Load .claude/subagents/context_calculator.md for guidance
- Calculate: file counts per component, estimated tokens, phase boundaries
- Output: JSON with file analysis, token estimates, phase recommendations

STAGE 4: Plan Synthesis (YOU - Main Agent)
- Synthesize ALL sub-agent findings
- Generate comprehensive implementation plan with:
  * Component-aware phase breakdown
  * DRY-optimized implementation (reuse existing patterns)
  * Context-optimized phases (max 15 files each)
  * Clear integration points
  * Validation commands

**ISSUE DETAILS:**
Title: {issue.title}
Body:
{issue.body}

**WORKTREE PATH:** {worktree_path}

**IMPORTANT:**
- Use Task tool for stages 1-3 (sub-agents do focused analysis)
- YOU synthesize findings in stage 4 (main agent creates coherent plan)
- Output final plan in standard markdown format to specs/ directory
"""


def execute_multistage_planning(
    issue_number: str,
    adw_id: str,
) -> None:
    """
    Execute multi-stage planning workflow.

    Creates worktree, spawns Claude Code with multistage prompt,
    Claude Code internally uses Task tool for sub-agents.
    """
    logger.info(f"[adw_plan_multistage_iso] Starting for issue #{issue_number}")

    # Fetch issue
    issue = fetch_github_issue(issue_number)

    # Create/validate worktree
    worktree_path = create_or_validate_worktree(adw_id, logger)

    # Load or create state
    state = ADWState.load_or_create(adw_id, issue_number, logger)
    state.update(worktree_path=worktree_path)
    state.save("adw_plan_multistage_iso")

    # Build multistage prompt
    prompt = build_multistage_prompt(issue, worktree_path)

    # Execute Claude Code (it handles all sub-agent spawning internally)
    logger.info("[adw_plan_multistage_iso] Executing multistage planning...")
    response = execute_template(AgentTemplateRequest(
        agent_name="multistage_planner",
        slash_command="/plan",  # Use standard /plan, enhanced with Task instructions
        args=[prompt],
        adw_id=adw_id,
        working_dir=worktree_path,
    ))

    # Extract plan file path from response
    plan_file = extract_plan_file_from_response(response)

    # Update state
    state.update(
        plan_file=plan_file,
        planning_approach="multistage",
        stages_completed=["component_analysis", "dry_check", "context_calc", "synthesis"]
    )
    state.save("adw_plan_multistage_iso")

    logger.info(f"[adw_plan_multistage_iso] Complete. Plan: {plan_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: adw_plan_multistage_iso.py <issue_number> [adw_id]")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    execute_multistage_planning(issue_number, adw_id)
```

### Phase 3: Observability Enhancements (1 day)

**Update `adw_modules/tool_call_tracker.py` to track sub-agent spawning:**

```python
class ToolCallTracker:
    def track_subagent_spawn(self, subagent_type: str, prompt: str):
        """Track when Task tool spawns a sub-agent."""
        self.tool_calls.append({
            "tool_name": "Task",
            "subagent_type": subagent_type,
            "prompt_summary": prompt[:100],
            "started_at": datetime.now().isoformat(),
        })
```

**Add to `hook_events` table schema (if needed):**
- Track `SubagentStart` and `SubagentStop` events
- Record sub-agent type, duration, success/failure

### Phase 4: Testing & Validation (2 days)

**Test on 3-5 real issues:**
1. Small feature (5-10 files) - Verify phases don't over-split
2. Medium feature (15-20 files) - Verify optimal phase boundaries
3. Large feature (30+ files) - Verify context management works
4. Bug fix with DRY opportunity - Verify reuse suggestions
5. Complex refactor - Verify component decomposition quality

**Metrics to collect:**
- Token usage (expect ~220k vs 271k baseline = 19% reduction)
- Plan quality (manual review - are phases logical?)
- Time to complete (might be slightly slower due to sub-agent overhead)
- DRY suggestions quality (are they actionable?)

---

## Integration with Existing Workflows

### Backward Compatibility

**No Breaking Changes:**
- `adw_plan_iso.py` remains unchanged (legacy support)
- `adw_plan_iso_optimized.py` remains unchanged (alternative)
- New `adw_plan_multistage_iso.py` is opt-in

**Orchestrator Integration:**

Update `adw_sdlc_complete_iso.py` to support flag:
```python
parser.add_argument("--use-multistage-plan", action="store_true",
                    help="Use multi-stage planning with sub-agents")

if args.use_multistage_plan:
    plan_script = "adw_plan_multistage_iso.py"
else:
    plan_script = "adw_plan_iso.py"  # Legacy
```

### Gradual Rollout Strategy

1. **Week 1-2:** Implement + test on non-critical issues
2. **Week 3-4:** Enable by default for features with 20+ estimated files
3. **Month 2:** Enable by default for all features
4. **Month 3:** Deprecate legacy `adw_plan_iso.py` (keep as fallback)

---

## Cost Analysis

### Token Breakdown Comparison

| Stage | Current (Monolithic) | Multistage | Savings |
|-------|---------------------|------------|---------|
| Context Loading | 50k (full issue) | 50k (shared once) | 0k |
| Component Analysis | N/A (embedded) | 40k (focused) | N/A |
| DRY Checking | N/A (none) | 30k (targeted) | N/A |
| Context Calculation | N/A (none) | 20k (small reads) | N/A |
| Plan Generation | 221k (monolithic) | 80k (synthesis) | 141k saved |
| **Total** | **271k** | **220k** | **51k (19%)** |

### Per-Workflow Cost Impact

| Workflow Type | Current | Multistage | Change |
|---------------|---------|------------|--------|
| Lightweight | $0.10-0.30 | $0.08-0.25 | -20% |
| Standard | $3.00-5.00 | $2.50-4.25 | -17% |
| Complex | $5.00-8.00 | $4.25-6.80 | -15% |

### Monthly Savings Estimate

Assuming 50 workflows/month:
- Current: $150-200
- Multistage: $125-170
- **Savings: $25-30/month (15-20%)**

Plus qualitative improvements:
- Better phase boundaries = fewer retries
- DRY checking = less redundant code
- Component focus = clearer architecture

---

## Risk Assessment & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Sub-agent quality varies | Medium | Define clear sub-agent prompts, test extensively |
| Token estimates inaccurate | Low | Use conservative 5k/file avg, validate on real features |
| Synthesis quality degrades | Medium | Main agent has all context, can request clarifications |
| Cost doesn't improve | Low | Measure token usage, revert if >271k baseline |
| Compatibility issues | Low | Opt-in flag, legacy fallback always available |
| Sub-agent loops/failures | Medium | Task tool has built-in timeout, circuit breaker reuses existing mechanisms |

---

## Success Criteria

### Must-Have (Launch Blockers)

- [ ] Token usage ≤ 271k per workflow (no cost increase)
- [ ] Sub-agents complete successfully 95%+ of the time
- [ ] Plans include DRY suggestions when applicable
- [ ] Phase boundaries respect file count limits (≤15/phase)
- [ ] No breaking changes to existing workflows

### Should-Have (Quality Goals)

- [ ] Token usage < 250k per workflow (8% reduction)
- [ ] DRY suggestions are actionable 80%+ of the time
- [ ] Component decomposition matches manual analysis
- [ ] File context estimates within 20% of actual

### Nice-to-Have (Stretch Goals)

- [ ] Token usage < 220k per workflow (19% reduction)
- [ ] Sub-agent reusable for other workflows
- [ ] Automated metrics dashboard for tracking
- [ ] Integration with pattern learning system

---

## Future Enhancements

### Phase 1 Extensions (Q1 2026)

1. **Parallel Sub-Agent Execution:**
   - Run component analysis + DRY checking concurrently
   - Potential 30-40% time savings

2. **Smart Caching:**
   - Cache component analysis results for similar issues
   - Reuse DRY findings across related features

3. **External Tool Integration:**
   - Use `jscpd` for TypeScript duplication detection
   - Use `pylint --duplicate-code` for Python
   - Integrate with pattern learning database

### Phase 2 Extensions (Q2 2026)

1. **Adaptive Planning:**
   - Choose planning approach based on issue complexity
   - Simple issues: monolithic (faster)
   - Complex issues: multistage (better quality)

2. **Learning Feedback Loop:**
   - Track which sub-agent suggestions were implemented
   - Update confidence scores based on outcomes
   - Feed into pattern learning system

3. **Multi-Issue Coordination:**
   - Detect dependencies across planned features
   - Suggest implementation ordering
   - Warn about conflicting changes

---

## References

### Documentation
- Official Claude Code Docs: https://code.claude.com/docs/en/sub-agents
- Task Tool Guide: https://claudelog.com/mechanics/task-agent-tools/
- MCP Protocol: https://docs.claude.com/en/docs/mcp

### Codebase Files
- `.claude/commands/implement.md` - Current Task tool usage examples
- `.claude/CODE_STANDARDS.md` - Delegation mandate (Section 3)
- `CLAUDE.md` - Progressive loading + logic gates
- `.claude/settings.json` - SubagentStop hook configuration
- `adws/adw_modules/agent.py` - Agent execution framework

### Research Papers
- HALO Framework (May 2025) - Hierarchical agent orchestration
- AgentOrchestra (2025) - Multi-agent task decomposition
- Anthropic Research System - Orchestrator-worker pattern

---

## Appendix A: Sub-Agent Prompt Templates

See `.claude/subagents/` directory for complete prompt templates:
- `component_analyzer.md`
- `dry_checker.md`
- `context_calculator.md`

## Appendix B: Testing Checklist

- [ ] Sub-agent definitions created
- [ ] `adw_plan_multistage_iso.py` implemented
- [ ] Token tracking integrated
- [ ] Test on 5 sample issues
- [ ] Measure token usage vs baseline
- [ ] Validate DRY suggestions quality
- [ ] Check phase boundaries correctness
- [ ] Verify no breaking changes
- [ ] Update documentation
- [ ] Deploy to production (opt-in)

---

**Document Version:** 1.0
**Last Updated:** 2025-12-22
**Status:** Ready for Implementation
