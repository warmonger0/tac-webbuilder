# Workflow Comparison

## Overview

This document provides a comprehensive comparison of all ADW workflow variants to help you choose the right workflow for your use case. Each workflow represents different trade-offs between speed, cost, quality, and automation.

## Quick Reference Matrix

| Workflow | Phases | Quality Gates | Cost | Time | Ships | Automation | Best For |
|----------|--------|---------------|------|------|-------|------------|----------|
| Complete SDLC | 8 | Lint, Test, Review | $3.50 | 15-25m | Manual | High | Production features |
| Complete ZTE | 8 | Lint, Test, Review | $3.50 | 15-25m | Auto | Highest | Trusted deployments |
| Standard SDLC | 5 | Test, Review | $4.00 | 12-20m | No | Medium | Legacy workflow |
| Lightweight | 2 | None | $1.50 | 5-10m | No | Low | Quick experiments |
| Stepwise | 1 | None | $1.14 | 2-5m | N/A | Low | Issue decomposition |
| Plan Only | 1 | None | $0.34-1.90 | 2-5m | No | Low | Planning analysis |
| Build Only | 1 | None | $0.50-2.50 | 3-8m | No | Low | Implementation only |
| Test Only | 1 | Test | $0.20-2.00 | 2-5m | No | Low | Testing existing code |
| Lint Only | 1 | Lint | $0.10-1.20 | 1-3m | No | Low | Code quality check |
| Review Only | 1 | Review | $1.50 | 5-10m | No | Low | Requirements validation |
| Document Only | 1 | None | $0.80 | 3-7m | No | Low | Documentation generation |
| Ship Only | 1 | State validation | $0.05 | 1-2m | Yes | Low | Manual shipping |

## Detailed Workflow Comparison

### 1. Complete SDLC (`adw_sdlc_complete_iso.py`)

**Description**: Full 8-phase workflow with all quality gates and manual shipping

**Phases**:
1. Plan - Create implementation specification
2. Build - Implement the solution
3. Lint - Enforce code quality standards
4. Test - Run unit and integration tests
5. Review - Validate against requirements
6. Document - Generate comprehensive docs
7. Ship - Approve and merge PR (manual trigger)
8. Cleanup - Organize documentation

**Quality Gates**:
- Lint: ESLint, Pylint, Prettier
- Test: pytest, vitest, coverage thresholds
- Review: Requirements validation, screenshots

**Cost Analysis**:
- With external tools: $3.49 (recommended)
- Without external tools: $8.39
- Optimized planner: -$1.56 savings

**Time Estimate**: 15-25 minutes

**Token Usage**:
- With optimization: ~271K tokens
- Without optimization: ~650K tokens

**Exit Codes**:
- 0: Success (all phases passed)
- 1: Failure (phase failed, aborted)

**Flags**:
```bash
--skip-e2e           # Skip E2E tests
--skip-resolution    # Disable auto-resolution of failures
--no-external        # Disable external tools (higher cost)
--use-optimized-plan # Use inverted context flow planner
```

**Usage**:
```bash
# Recommended (optimized, external tools)
uv run adw_sdlc_complete_iso.py 123 --use-optimized-plan

# Debugging (inline execution)
uv run adw_sdlc_complete_iso.py 123 --no-external

# With existing ADW ID
uv run adw_sdlc_complete_iso.py 123 abc12345
```

**Best For**:
- Production features
- User-facing changes
- API modifications
- Critical bug fixes
- Features requiring documentation
- Team collaboration (manual review before ship)

**Not Suitable For**:
- Quick experiments
- Throwaway code
- Internal refactoring
- Time-critical hotfixes

---

### 2. Complete ZTE (`adw_sdlc_complete_zte_iso.py`)

**Description**: Zero Touch Execution - Full workflow with automatic shipping

**Phases**: Same 8 phases as Complete SDLC

**Quality Gates**: Same as Complete SDLC

**Cost Analysis**: Same as Complete SDLC ($3.49-8.39)

**Time Estimate**: 15-25 minutes

**Key Difference**: Automatically merges PR if all phases pass

**Exit Codes**:
- 0: Success (shipped to production)
- 1: Failure (aborted, not shipped)
- 10: Decomposition recommended (if using stepwise)

**Flags**: Same as Complete SDLC

**Usage**:
```bash
# WARNING: Will auto-merge to main!
uv run adw_sdlc_complete_zte_iso.py 123 --use-optimized-plan
```

**Best For**:
- Fully automated deployments
- Well-tested issue types
- Low-risk changes
- Documentation updates
- Trusted automation scenarios

**Not Suitable For**:
- Untested workflows
- High-risk changes
- Features requiring human approval
- First-time issue types

**Risk Level**: HIGH - Ships automatically without human review

---

### 3. Standard SDLC (`adw_sdlc_iso.py`)

**Description**: Original 5-phase workflow without lint phase

**Phases**:
1. Plan
2. Build
3. Test
4. Review
5. Document

**Quality Gates**:
- Test: pytest, vitest
- Review: Requirements validation

**Cost Analysis**: $4.00-9.00 (varies)

**Time Estimate**: 12-20 minutes

**Key Difference**: No lint phase (legacy workflow)

**Exit Codes**:
- 0: Success
- 1: Failure

**Usage**:
```bash
uv run adw_sdlc_iso.py 123
```

**Best For**:
- Legacy compatibility
- Projects without linting requirements

**Not Suitable For**:
- New features (use Complete SDLC instead)
- Quality-critical code

**Note**: Deprecated in favor of Complete SDLC workflows

---

### 4. Lightweight (`adw_lightweight_iso.py`)

**Description**: Fast Plan + Build workflow for quick iterations

**Phases**:
1. Plan
2. Build

**Quality Gates**: None

**Cost Analysis**: $1.50-3.50

**Time Estimate**: 5-10 minutes

**Token Usage**: ~100K tokens

**Exit Codes**:
- 0: Success
- 1: Failure

**Usage**:
```bash
uv run adw_lightweight_iso.py 123
```

**Best For**:
- Quick experiments
- Proof of concepts
- Development testing
- Features not ready to ship
- Rapid prototyping

**Not Suitable For**:
- Production code
- Features to be shipped
- Code requiring documentation

**Risk Level**: LOW - No quality gates, not shipped

---

### 5. Stepwise Refinement (`adw_stepwise_iso.py`)

**Description**: Pre-workflow analysis for issue decomposition

**Phases**: Single analysis phase with decision making

**Quality Gates**: None (analysis only)

**Cost Analysis**: $1.14 per analysis

**Time Estimate**: 2-5 minutes

**Token Usage**: ~80K tokens

**Exit Codes**:
- 0: ATOMIC (proceed with implementation)
- 10: DECOMPOSE (sub-issues created, pause)
- 1: Error

**Decisions**:
- **ATOMIC**: Issue is ready for implementation
- **DECOMPOSE**: Issue broken into 2-5 sub-issues

**Usage**:
```bash
# Analyze issue
uv run adw_stepwise_iso.py 123

# If ATOMIC (exit 0), proceed:
uv run adw_sdlc_complete_iso.py 123

# If DECOMPOSE (exit 10), work on sub-issues:
uv run adw_sdlc_complete_iso.py 124  # Sub-issue 1
uv run adw_sdlc_complete_iso.py 125  # Sub-issue 2
```

**Best For**:
- Large, complex issues
- Epics and initiatives
- Issues with ambiguous scope
- Features needing decomposition
- Risk reduction

**Not Suitable For**:
- Small, clear issues
- Bug fixes
- Well-scoped features
- Urgent tasks

---

### 6. Plan Only (`adw_plan_iso.py` / `adw_plan_iso_optimized.py`)

**Description**: Planning phase only, creates worktree and specification

**Phases**: Plan

**Quality Gates**: None

**Cost Analysis**:
- Standard: $1.90
- Optimized: $0.34 (77% reduction)

**Time Estimate**: 2-5 minutes

**Token Usage**:
- Standard: ~173K tokens
- Optimized: ~40K tokens

**Exit Codes**:
- 0: Success
- 1: Failure

**Usage**:
```bash
# Standard planner
uv run adw_plan_iso.py 123

# Optimized planner (recommended)
uv run adw_plan_iso_optimized.py 123
```

**Best For**:
- Planning-only workflows
- Review plans before implementation
- Separating planning from building
- Cost-sensitive scenarios

**Not Suitable For**:
- Complete feature implementation
- When plan and build should be atomic

---

### 7-12. Individual Phase Workflows

#### Build Only (`adw_build_iso.py`)

**Requires**: Existing worktree with plan

**Cost**: $0.50-2.50

**Time**: 3-8 minutes

**Usage**:
```bash
uv run adw_build_iso.py 123 abc12345
```

**Best For**: Re-running failed build, manual build-only execution

#### Test Only (`adw_test_iso.py`)

**Requires**: Existing worktree with code

**Cost**: $0.20-2.00

**Time**: 2-5 minutes

**Usage**:
```bash
uv run adw_test_iso.py 123 abc12345 [--skip-e2e]
```

**Best For**: Testing existing code, re-running failed tests

#### Lint Only (`adw_lint_iso.py`)

**Requires**: Existing worktree with code

**Cost**: $0.10-1.20

**Time**: 1-3 minutes

**Usage**:
```bash
uv run adw_lint_iso.py 123 abc12345
```

**Best For**: Code quality checks, linting existing code

#### Review Only (`adw_review_iso.py`)

**Requires**: Existing worktree with implemented code

**Cost**: $1.50

**Time**: 5-10 minutes

**Usage**:
```bash
uv run adw_review_iso.py 123 abc12345 [--skip-resolution]
```

**Best For**: Requirements validation, capturing screenshots

#### Document Only (`adw_document_iso.py`)

**Requires**: Existing worktree with completed feature

**Cost**: $0.80

**Time**: 3-7 minutes

**Usage**:
```bash
uv run adw_document_iso.py 123 abc12345
```

**Best For**: Generating documentation for shipped features

#### Ship Only (`adw_ship_iso.py`)

**Requires**: Complete ADWState, existing PR

**Cost**: $0.05

**Time**: 1-2 minutes

**Usage**:
```bash
uv run adw_ship_iso.py 123 abc12345
```

**Best For**: Manual PR approval and merge, final shipping step

---

## Use Case Decision Tree

```
Is this a production feature?
├─ YES: Is human review required before shipping?
│  ├─ YES → Complete SDLC (8 phases, manual ship)
│  └─ NO → Complete ZTE (8 phases, auto ship)
│
└─ NO: Is this ready for any quality checks?
   ├─ YES: Need documentation?
   │  ├─ YES → Standard SDLC (5 phases)
   │  └─ NO → Lightweight (2 phases)
   │
   └─ NO: What do you need?
      ├─ Just a plan → Plan Only
      ├─ Issue analysis → Stepwise Refinement
      └─ Specific phase → Individual phase workflow
```

## Cost Comparison by Scenario

### Scenario 1: Simple Bug Fix

**Option A - Complete SDLC**:
- Cost: $3.50
- Time: 15-25 minutes
- Quality: Production-ready
- **Recommended**: YES

**Option B - Lightweight**:
- Cost: $1.50
- Time: 5-10 minutes
- Quality: No validation
- **Recommended**: NO (bugs need testing)

**Option C - Standard SDLC**:
- Cost: $4.00
- Time: 12-20 minutes
- Quality: Good (no lint)
- **Recommended**: NO (use Complete instead)

**Winner**: Complete SDLC (best quality/cost ratio)

---

### Scenario 2: Large Feature (Epic)

**Option A - Complete SDLC on parent**:
- Cost: $15-25 (large feature)
- Time: 40-60 minutes
- Risk: High (complex, hard to debug)
- **Recommended**: NO

**Option B - Stepwise + Multiple Complete SDLCs**:
- Stepwise cost: $1.14
- 4 sub-issues: 4 × $3.50 = $14.00
- Total: $15.14
- Time: 60-100 minutes (parallelizable)
- Risk: Low (each sub-issue validated)
- **Recommended**: YES

**Winner**: Stepwise decomposition (lower risk, parallelizable)

---

### Scenario 3: Quick Prototype

**Option A - Complete SDLC**:
- Cost: $3.50
- Time: 15-25 minutes
- Quality: Production-ready
- **Recommended**: NO (overkill)

**Option B - Lightweight**:
- Cost: $1.50
- Time: 5-10 minutes
- Quality: Functional
- **Recommended**: YES

**Option C - Plan Only**:
- Cost: $0.34
- Time: 2-5 minutes
- Quality: Specification only
- **Recommended**: NO (need implementation)

**Winner**: Lightweight (fast, sufficient for prototypes)

---

### Scenario 4: Documentation Update

**Option A - Complete SDLC**:
- Cost: $3.50
- Time: 15-25 minutes
- Quality: Full validation
- **Recommended**: NO (overkill for docs)

**Option B - Lightweight**:
- Cost: $1.50
- Time: 5-10 minutes
- Quality: Basic validation
- **Recommended**: YES

**Option C - Complete ZTE**:
- Cost: $3.50
- Time: 15-25 minutes
- Ships: Automatically
- **Recommended**: YES (if trusted)

**Winner**: Complete ZTE if automation trusted, Lightweight otherwise

---

### Scenario 5: Critical Production Hotfix

**Option A - Complete SDLC**:
- Cost: $3.50
- Time: 15-25 minutes
- Quality: Full validation
- **Recommended**: YES

**Option B - Lightweight**:
- Cost: $1.50
- Time: 5-10 minutes
- Quality: No validation
- **Recommended**: NO (risky)

**Option C - Individual phases**:
- Plan + Build + Test: $2.64
- Time: 10-18 minutes
- Quality: Basic validation
- **Recommended**: NO (incomplete)

**Winner**: Complete SDLC (even hotfixes need quality gates)

---

## Token Usage Comparison

### With External Tools (Recommended)

| Workflow | Input Tokens | Output Tokens | Total | Cost |
|----------|--------------|---------------|-------|------|
| Complete SDLC (opt) | 41K | 230K | 271K | $3.49 |
| Complete SDLC (std) | 65K | 440K | 505K | $6.66 |
| Complete ZTE (opt) | 41K | 230K | 271K | $3.49 |
| Standard SDLC | 60K | 340K | 400K | $5.16 |
| Lightweight | 15K | 85K | 100K | $1.29 |
| Stepwise | 5K | 75K | 80K | $1.14 |
| Plan Only (opt) | 4K | 36K | 40K | $0.55 |
| Plan Only (std) | 23K | 150K | 173K | $2.31 |

### Without External Tools

| Workflow | Input Tokens | Output Tokens | Total | Cost |
|----------|--------------|---------------|-------|------|
| Complete SDLC (opt) | 85K | 565K | 650K | $8.52 |
| Complete SDLC (std) | 130K | 870K | 1000K | $13.05 |
| Standard SDLC | 120K | 680K | 800K | $10.26 |

**Savings with external tools**: 50-60%

---

## Performance Metrics

### Success Rates (Based on Historical Data)

| Workflow | Success Rate | Avg Retries | Common Failures |
|----------|--------------|-------------|-----------------|
| Complete SDLC | 87% | 0.3 | Lint violations, test failures |
| Complete ZTE | 82% | 0.4 | Review blockers, merge conflicts |
| Standard SDLC | 79% | 0.6 | Test failures (no lint) |
| Lightweight | 91% | 0.1 | Build errors |
| Stepwise | 95% | 0.0 | YAML parsing (rare) |

### Average Duration

| Workflow | Min | Avg | Max | Notes |
|----------|-----|-----|-----|-------|
| Complete SDLC | 12m | 19m | 35m | With external tools |
| Complete ZTE | 12m | 20m | 38m | +1m for shipping |
| Standard SDLC | 10m | 16m | 28m | No lint phase |
| Lightweight | 3m | 7m | 15m | Plan + Build only |
| Stepwise | 1m | 3m | 8m | Analysis only |

---

## Selection Guidelines

### By Issue Type

**Bug Fixes**:
- Small bugs: Complete SDLC
- Critical hotfixes: Complete SDLC (don't skip quality)
- Documentation bugs: Lightweight or Complete ZTE

**Features**:
- Small features: Complete SDLC
- Large features: Stepwise → Multiple Complete SDLCs
- Experimental features: Lightweight

**Chores**:
- Refactoring: Complete SDLC (need tests)
- Documentation: Lightweight or Complete ZTE
- Configuration: Lightweight

**Epics**:
- Always: Stepwise → Multiple Complete SDLCs

### By Team Maturity

**New Teams**:
- Use: Complete SDLC (manual review)
- Avoid: Complete ZTE (wait until trusted)
- Learn: Run Stepwise on complex issues

**Experienced Teams**:
- Default: Complete SDLC
- Trusted scenarios: Complete ZTE
- Complex issues: Stepwise decomposition

**Expert Teams**:
- Production: Complete ZTE
- Experiments: Lightweight
- Planning: Stepwise analysis

### By Risk Tolerance

**Risk-Averse**:
- Always: Complete SDLC with manual review
- Never: Complete ZTE
- Complex: Stepwise decomposition

**Balanced**:
- Default: Complete SDLC
- Low-risk: Complete ZTE
- Complex: Stepwise when needed

**Risk-Tolerant**:
- Default: Complete ZTE
- Quick iterations: Lightweight
- Analysis: Stepwise occasionally

---

## Cost Optimization Strategies

### Strategy 1: Use External Tools (Default)

**Impact**: 50-60% cost reduction

**How**:
```bash
# External tools enabled by default
uv run adw_sdlc_complete_iso.py 123
```

**When to disable**:
- Debugging complex failures
- Non-standard tooling
- Development of workflows

### Strategy 2: Use Optimized Planner

**Impact**: 77% cost reduction on planning phase

**How**:
```bash
uv run adw_sdlc_complete_iso.py 123 --use-optimized-plan
```

**Trade-offs**:
- Saves $1.56 per workflow
- Requires YAML parsing
- Slightly more rigid structure

### Strategy 3: Decompose Complex Issues

**Impact**: Lower per-issue cost, parallelizable

**How**:
```bash
# Analyze first
uv run adw_stepwise_iso.py 123

# If decomposed, work on sub-issues
uv run adw_sdlc_complete_iso.py 124
uv run adw_sdlc_complete_iso.py 125  # Can run in parallel
```

**Benefits**:
- Easier debugging (smaller changesets)
- Parallel execution (faster overall)
- Lower risk (independent validation)

### Strategy 4: Choose Right Workflow

**Impact**: Avoid over-engineering

**How**:
- Prototypes → Lightweight ($1.50 vs $3.50)
- Docs → Complete ZTE ($3.50 auto vs manual)
- Complex → Stepwise first (prevent waste)

### Strategy 5: Batch Related Issues

**Impact**: Reduce per-issue overhead

**How**:
- Group related issues in single workflow
- Use sub-issues for organization
- Implement as cohesive feature

---

## Migration Guide

### From Standard SDLC to Complete SDLC

**Changes**:
- Add lint phase (new quality gate)
- Add ship phase (manual merge)
- Add cleanup phase (resource management)

**Migration**:
```bash
# Old
uv run adw_sdlc_iso.py 123

# New
uv run adw_sdlc_complete_iso.py 123
```

**Benefits**:
- Code quality enforcement
- Automated shipping
- Resource cleanup

**Considerations**:
- +$0.10 for lint phase
- +1-3 minutes for additional phases
- Lint failures may block previously passing workflows

### From Manual to Automated Workflows

**Changes**:
- Manual → Complete SDLC (manual ship)
- Complete SDLC → Complete ZTE (auto ship)

**Migration**:
```bash
# Phase 1: Add workflows
uv run adw_sdlc_complete_iso.py 123  # Test with manual review

# Phase 2: Automate (when trusted)
uv run adw_sdlc_complete_zte_iso.py 123  # Auto-ship
```

**Risk Mitigation**:
- Start with low-risk issues
- Monitor early executions
- Keep manual override available

### From Monolithic to Decomposed

**Changes**:
- Large issues → Stepwise analysis
- Single workflow → Multiple parallel workflows

**Migration**:
```bash
# Old
uv run adw_sdlc_complete_iso.py 100  # Large epic

# New
uv run adw_stepwise_iso.py 100       # Analyze
# Creates #101, #102, #103, #104
uv run adw_sdlc_complete_iso.py 101  # Parallel execution
uv run adw_sdlc_complete_iso.py 102  # Parallel execution
uv run adw_sdlc_complete_iso.py 103  # Parallel execution
uv run adw_sdlc_complete_iso.py 104  # Sequential (depends on above)
```

**Benefits**:
- Faster overall completion (parallelization)
- Lower risk (smaller changes)
- Easier debugging

---

## Future Workflow Variants

### Planned Additions

**1. Incremental SDLC**:
- Resume from failed phase instead of full re-run
- Cost: 50% of full workflow
- Use: Recovering from transient failures

**2. Partial Quality Gates**:
- Lint + Test only (skip review)
- Review only (skip test)
- Customizable gate selection

**3. Multi-Repo SDLC**:
- Coordinate changes across repositories
- Atomic multi-repo commits
- Cross-repo testing

**4. Continuous SDLC**:
- Watch mode for development
- Auto-run phases on file changes
- IDE integration

---

## Summary Recommendations

### Default Choice: Complete SDLC

**Use for 80% of workflows**:
```bash
uv run adw_sdlc_complete_iso.py 123 --use-optimized-plan
```
- Cost: $3.50
- Time: 15-25 minutes
- Quality: Production-ready
- Risk: Low

### Complex Issues: Stepwise First

**Use for epics and large features**:
```bash
uv run adw_stepwise_iso.py 123
# Then run Complete SDLC on each sub-issue
```
- Analysis cost: $1.14
- Reduces overall risk
- Enables parallel work

### Quick Iterations: Lightweight

**Use for prototypes and experiments**:
```bash
uv run adw_lightweight_iso.py 123
```
- Cost: $1.50
- Time: 5-10 minutes
- Quality: Basic

### Trusted Automation: Complete ZTE

**Use for low-risk, well-tested scenarios**:
```bash
uv run adw_sdlc_complete_zte_iso.py 123 --use-optimized-plan
```
- Cost: $3.50
- Time: 15-25 minutes
- Ships: Automatically
- Risk: Medium (auto-merge)

**Golden Rule**: When in doubt, use Complete SDLC with optimized planner and external tools. It provides the best balance of cost, quality, and safety.
