# Stepwise Refinement Architecture

## Overview

Stepwise refinement is a pre-workflow analysis phase that determines whether a GitHub issue is **ATOMIC** (ready for implementation) or requires **DECOMPOSITION** (should be broken into sub-issues). This workflow uses **inverted context flow** to minimize AI calls and maximize decision accuracy.

## Architecture

### Workflow Phases

```
┌─────────────────────────────────────────────────────────────┐
│                    STEPWISE REFINEMENT                       │
│                                                              │
│  Phase 1: ANALYSIS (ONE AI CALL)                           │
│    - Fetch GitHub issue                                     │
│    - Analyze complexity & decomposition potential           │
│    - Output structured YAML configuration                   │
│                                                              │
│  Phase 2: EXECUTION (ZERO AI CALLS)                        │
│    - Parse & validate YAML                                  │
│    - Create sub-issues via GitHub API (if DECOMPOSE)        │
│    - Link dependencies deterministically                    │
│    - Post summary comment                                   │
│                                                              │
│  Exit: Status code indicates decision                       │
│    - Code 0: ATOMIC (proceed with implementation)          │
│    - Code 10: DECOMPOSE (sub-issues created, pause)        │
│    - Code 1: Error occurred                                 │
└─────────────────────────────────────────────────────────────┘
```

### Inverted Context Flow

Traditional approach loads context multiple times (expensive):
1. Load issue context → Classify
2. Load issue context → Analyze dependencies
3. Load issue context → Plan decomposition
4. Create each sub-issue with AI

**Inverted flow loads context ONCE:**
1. Load full issue context → Make ALL decisions → Output structured plan
2. Execute plan deterministically with zero AI calls

## Decision Criteria

### ATOMIC Decision

An issue is considered ATOMIC when:

- **Single responsibility**: Addresses one clear, focused objective
- **Well-scoped**: Can be implemented in one development session
- **No natural boundaries**: Cannot be meaningfully decomposed without artificial splits
- **Clear acceptance criteria**: Success is unambiguous
- **Estimated complexity**: Low to medium (< 4 hours of work)

**Example ATOMIC issues:**
- Fix login button alignment on mobile devices
- Add email validation to registration form
- Update API response format for user endpoint
- Refactor authentication helper function

### DECOMPOSE Decision

An issue requires DECOMPOSITION when:

- **Multiple responsibilities**: Involves distinct, separable concerns
- **Large scope**: Too complex for single implementation session
- **Natural boundaries**: Can be split along functional/architectural lines
- **Sequential dependencies**: Some parts must precede others
- **High complexity**: Estimated > 4 hours or touches many systems
- **Risk reduction**: Breaking apart reduces implementation risk

**Example DECOMPOSE issues:**
- Implement complete user authentication system
- Add analytics dashboard with multiple chart types
- Migrate database from PostgreSQL to MongoDB
- Redesign entire application layout

### Confidence Levels

The analyzer outputs confidence in its decision:

- **high**: Clear indicators, unambiguous decision (>90% certainty)
- **medium**: Most indicators align, some ambiguity (70-90% certainty)
- **low**: Conflicting signals, borderline case (50-70% certainty)

**Note:** Low confidence triggers more conservative decomposition to reduce risk.

## Sub-Issue Creation Process

### 1. Configuration Structure

The AI outputs a structured YAML configuration:

```yaml
decision: DECOMPOSE
reasoning: |
  This issue involves multiple independent components: user authentication,
  session management, and password reset flow. Each can be implemented and
  tested separately, reducing risk and enabling parallel development.
confidence: high

sub_issues:
  - title: Implement user registration endpoint
    body: |
      Create POST /api/auth/register endpoint with email/password validation.

      ## Acceptance Criteria
      - Validate email format and uniqueness
      - Hash passwords with bcrypt
      - Return JWT token on success
      - Return 400 for validation errors

      ## Technical Notes
      - Use existing User model
      - Add email validation utility
      - Implement password strength checker
    labels:
      - enhancement
      - backend
      - authentication
    depends_on: []  # No dependencies, can start immediately

  - title: Add login endpoint with session management
    body: |
      Create POST /api/auth/login endpoint and implement session handling.

      ## Acceptance Criteria
      - Verify email/password credentials
      - Generate and return JWT token
      - Set secure HTTP-only cookie
      - Return 401 for invalid credentials

      ## Technical Notes
      - Integrate with User model from registration
      - Use JWT secret from environment
      - 24-hour token expiration
    labels:
      - enhancement
      - backend
      - authentication
    depends_on: [0]  # Requires registration to be complete

  - title: Implement password reset flow
    body: |
      Create password reset request and confirmation endpoints.

      ## Acceptance Criteria
      - POST /api/auth/reset-request sends email
      - POST /api/auth/reset-confirm updates password
      - Use secure random tokens with expiration
      - Prevent token reuse

      ## Technical Notes
      - Add PasswordResetToken model
      - Integrate with email service
      - Token valid for 1 hour
    labels:
      - enhancement
      - backend
      - authentication
    depends_on: [0]  # Requires User model from registration
```

### 2. Validation Rules

Before creating sub-issues, the system validates:

- **Required fields**: All sub-issues must have title, body, labels, depends_on
- **Count limits**: Minimum 2, maximum 5 sub-issues (prevents over/under decomposition)
- **Dependency validity**: All dependency indices must reference valid sub-issues
- **No circular dependencies**: Prevents impossible execution order
- **Label consistency**: All sub-issues must have at least one label

### 3. Deterministic Creation

Sub-issues are created via GitHub API with:

- **Sequential processing**: Issues created in order to establish dependencies
- **Automatic linking**: Parent issue reference added to each sub-issue body
- **Dependency tracking**: Cross-references added as issues are created
- **Zero AI calls**: Pure API operations based on validated configuration

### 4. Dependency Management

The `depends_on` field uses array indices:

```yaml
sub_issues:
  - title: Issue A
    depends_on: []      # Index 0: No dependencies
  - title: Issue B
    depends_on: [0]     # Index 1: Depends on Issue A
  - title: Issue C
    depends_on: [0, 1]  # Index 2: Depends on A and B
```

Created issues include dependency references:

```markdown
## Sub-issue Body

---
**Parent Issue:** #123
**Depends on:** #124, #125
```

## Inverted Context Flow Usage

### Traditional Multi-Call Approach (EXPENSIVE)

```
Call 1: Load issue → Classify type          (50K tokens)
Call 2: Load issue → Analyze scope          (50K tokens)
Call 3: Load issue → Identify boundaries    (50K tokens)
Call 4: Load issue → Plan decomposition     (50K tokens)
Call 5: Create sub-issue 1                  (30K tokens)
Call 6: Create sub-issue 2                  (30K tokens)
Call 7: Create sub-issue 3                  (30K tokens)
---------------------------------------------------
Total: 290K tokens (~$0.45 per analysis)
```

### Inverted Flow Approach (OPTIMIZED)

```
Call 1: Load issue → Make ALL decisions → Output YAML (80K tokens)
GitHub API: Create sub-issues (deterministic, 0 tokens)
---------------------------------------------------
Total: 80K tokens (~$0.13 per analysis)
```

**Savings: 72% token reduction**

### Key Optimization Principles

1. **Load context once**: Single comprehensive analysis call
2. **Output structured data**: YAML/JSON for deterministic execution
3. **Validate, don't regenerate**: Check structure without reloading context
4. **Use APIs directly**: GitHub operations need no AI assistance

## Exit Codes and Their Meaning

### Exit Code 0: ATOMIC

**Meaning**: Issue is ready for implementation as-is

**Workflow behavior**:
- Post "Issue is ATOMIC" comment to GitHub
- Exit with code 0 (success)
- Calling script should proceed to next phase (e.g., `adw_sdlc_complete_iso`)

**State saved**:
```json
{
  "stepwise_decision": "ATOMIC",
  "stepwise_confidence": "high",
  "stepwise_reasoning": "Single focused feature with clear scope..."
}
```

**Example usage**:
```bash
uv run adw_stepwise_iso.py 123
# Exit code: 0
# Next: uv run adw_sdlc_complete_iso.py 123
```

### Exit Code 10: DECOMPOSE

**Meaning**: Issue decomposed into sub-issues

**Workflow behavior**:
- Create sub-issues via GitHub API
- Post summary with sub-issue links
- Exit with code 10 (pause for review)
- Calling script should HALT and wait for human review

**State saved**:
```json
{
  "stepwise_decision": "DECOMPOSE",
  "stepwise_confidence": "high",
  "stepwise_reasoning": "Multiple independent components identified...",
  "sub_issue_numbers": ["124", "125", "126"]
}
```

**Example usage**:
```bash
uv run adw_stepwise_iso.py 123
# Exit code: 10
# Sub-issues #124, #125, #126 created
# Human reviews, then runs workflow on each sub-issue
```

### Exit Code 1: ERROR

**Meaning**: Analysis or execution failed

**Common causes**:
- YAML parsing failure
- Validation errors (invalid dependencies, missing fields)
- GitHub API errors (rate limit, permissions)
- Network connectivity issues

**Workflow behavior**:
- Post error message to GitHub issue
- Exit with code 1 (error)
- Calling script should abort and report failure

## Example Workflows

### Example 1: Simple Feature (ATOMIC)

**Issue #101**: "Add export button to data table"

**Analysis**:
```yaml
decision: ATOMIC
reasoning: |
  Single focused feature: adding one button with clear behavior.
  Scope is well-defined and can be implemented in single session.
  No natural decomposition boundaries.
confidence: high
```

**Outcome**:
- Exit code: 0
- Next step: Run `adw_sdlc_complete_iso.py 101`
- Implementation proceeds immediately

### Example 2: Complex Feature (DECOMPOSE)

**Issue #202**: "Implement analytics dashboard"

**Analysis**:
```yaml
decision: DECOMPOSE
reasoning: |
  Multiple independent components: user metrics, system health,
  revenue charts, and data export. Each component has distinct
  data sources and can be developed in parallel.
confidence: high

sub_issues:
  - title: Create user metrics component
    body: Display active users, new signups, retention rate
    labels: [enhancement, frontend, analytics]
    depends_on: []

  - title: Add system health monitoring
    body: CPU, memory, API response times visualization
    labels: [enhancement, frontend, analytics]
    depends_on: []

  - title: Implement revenue charts
    body: Daily/weekly/monthly revenue with trend analysis
    labels: [enhancement, frontend, analytics]
    depends_on: []

  - title: Create analytics dashboard layout
    body: Integrate all components into cohesive dashboard
    labels: [enhancement, frontend, analytics]
    depends_on: [0, 1, 2]
```

**Outcome**:
- Exit code: 10
- Sub-issues #203, #204, #205, #206 created
- Human reviews decomposition
- Runs workflow independently on each sub-issue
- Issue #202 closed when all sub-issues complete

### Example 3: Borderline Complexity (ATOMIC with Medium Confidence)

**Issue #303**: "Add image upload with validation"

**Analysis**:
```yaml
decision: ATOMIC
reasoning: |
  While this involves multiple steps (file selection, validation,
  upload, preview), they form a cohesive user flow that should
  be implemented together. Splitting would create artificial
  boundaries and incomplete features.
confidence: medium
```

**Outcome**:
- Exit code: 0
- Implemented as single feature despite complexity
- Medium confidence noted for potential follow-up if issues arise

### Example 4: Backend Migration (DECOMPOSE)

**Issue #404**: "Migrate from REST API to GraphQL"

**Analysis**:
```yaml
decision: DECOMPOSE
reasoning: |
  Large-scale architectural change affecting multiple systems.
  Natural decomposition by domain (users, products, orders).
  Sequential dependencies require staged rollout.
confidence: high

sub_issues:
  - title: Set up GraphQL server and schema foundation
    body: Install Apollo Server, define base schema structure
    labels: [enhancement, backend, graphql]
    depends_on: []

  - title: Migrate user queries and mutations
    body: Convert user REST endpoints to GraphQL resolvers
    labels: [enhancement, backend, graphql]
    depends_on: [0]

  - title: Migrate product queries and mutations
    body: Convert product REST endpoints to GraphQL resolvers
    labels: [enhancement, backend, graphql]
    depends_on: [0]

  - title: Update frontend to use GraphQL client
    body: Replace axios with Apollo Client, update queries
    labels: [enhancement, frontend, graphql]
    depends_on: [1, 2]

  - title: Remove deprecated REST endpoints
    body: Clean up old REST routes after GraphQL migration
    labels: [cleanup, backend]
    depends_on: [3]
```

**Outcome**:
- Exit code: 10
- Sub-issues #405-#409 created
- Sequential implementation respects dependencies
- Enables parallel work where possible (issues #406 and #407)

## Integration with Complete SDLC

### Usage Pattern

```bash
# Optional pre-workflow analysis
uv run adw_stepwise_iso.py 123

# If exit code 0 (ATOMIC), proceed:
uv run adw_sdlc_complete_iso.py 123

# If exit code 10 (DECOMPOSE), review sub-issues then:
uv run adw_sdlc_complete_iso.py 124  # First sub-issue
uv run adw_sdlc_complete_iso.py 125  # Second sub-issue
# ... etc
```

### Automated Integration (Future)

Could be integrated into orchestrator workflows:

```python
# In adw_sdlc_complete_iso.py (hypothetical)
result = subprocess.run(["adw_stepwise_iso.py", issue_number])

if result.returncode == 0:
    # ATOMIC: proceed with implementation
    continue_with_sdlc()
elif result.returncode == 10:
    # DECOMPOSE: pause for review
    print("Sub-issues created. Run workflow on each sub-issue.")
    sys.exit(10)
else:
    # ERROR: abort
    sys.exit(1)
```

## Cost Analysis

### Per-Analysis Costs

**Token usage breakdown**:
- Issue fetch: ~1K tokens
- Comprehensive analysis: ~70-80K tokens (depends on issue complexity)
- YAML parsing & validation: 0 tokens (pure Python)
- GitHub API operations: 0 tokens (direct API calls)

**Total: 71-81K tokens per analysis**

**Cost calculation** (using Claude Sonnet 4.5 pricing):
- Input tokens: ~5K @ $3/M = $0.015
- Output tokens: ~75K @ $15/M = $1.125
- **Total: ~$1.14 per analysis**

**Note**: This is a one-time cost per issue. If it prevents inappropriate decomposition or catches over-scoped issues, the savings in downstream workflows far exceed the analysis cost.

### Comparison Scenarios

**Scenario 1: Large issue implemented without decomposition**
- Cost: $15-25 (single massive SDLC run with many failures/retries)
- Time: 2-4 hours
- Risk: High (testing/review complexity, hard to debug)

**Scenario 2: Large issue analyzed and decomposed**
- Analysis cost: $1.14
- Implementation cost: 4 × $4 = $16 (4 smaller SDLC runs)
- Total: $17.14
- Time: 4-6 hours (parallelizable)
- Risk: Low (each sub-issue independently testable)

**Savings**: While total cost is similar, decomposed approach has:
- Lower risk
- Parallelizable work
- Easier debugging
- Incremental progress
- Better code review

**Scenario 3: Small issue incorrectly decomposed (false positive)**
- Analysis cost: $1.14
- Would cost extra if forced decomposition
- **Mitigation**: Human reviews decision before creating sub-issues

### Cost Optimization Strategies

1. **Use for borderline cases only**: Don't analyze obviously simple issues
2. **Trust high confidence**: High confidence ATOMIC → proceed immediately
3. **Review medium/low confidence**: Human sanity check before decomposing
4. **Learn from patterns**: Track which issue types benefit most from analysis

### ROI Calculation

**Break-even point**: Stepwise analysis pays for itself if it:
- Prevents one failed SDLC run (~$5-10 wasted)
- Enables parallel work on sub-issues (saves human time)
- Reduces review/debugging time (smaller changesets)

**Expected ROI**: 200-500% on complex issues that benefit from decomposition

## Technical Implementation

### File: `adw_stepwise_iso.py`

**Key components**:
- `parse_stepwise_analysis()`: Extracts YAML from AI output
- `validate_stepwise_config()`: Validates structure and dependencies
- `create_github_issue()`: Creates sub-issue via `gh` CLI
- `create_sub_issues()`: Orchestrates sub-issue creation with linking
- `run_stepwise_analysis()`: Single AI call for decision making

### Dependencies

- `python-dotenv`: Environment configuration
- `pydantic`: Data validation
- `pyyaml`: YAML parsing
- `gh` CLI: GitHub API operations

### State Management

Stepwise analysis saves to ADWState:
```json
{
  "stepwise_decision": "ATOMIC|DECOMPOSE",
  "stepwise_confidence": "high|medium|low",
  "stepwise_reasoning": "Detailed explanation...",
  "sub_issue_numbers": ["124", "125", "126"]  // Only if DECOMPOSE
}
```

### GitHub Comments

**ATOMIC decision**:
```
✅ Issue is ATOMIC - Ready for implementation

Recommended workflow: `adw_sdlc_complete_iso` or `adw_lightweight_iso`
```

**DECOMPOSE decision**:
```
✅ Issue Decomposed - Created 3 sub-issues

Sub-issues:
- #124
- #125
- #126

Next Steps:
1. Review sub-issues for accuracy
2. Run workflow on each sub-issue independently
3. Close parent issue when all sub-issues are complete

Recommended workflow per sub-issue: `adw_sdlc_complete_iso`
```

## Best Practices

### When to Use Stepwise Refinement

**Use for**:
- Epics and large features
- Issues with ambiguous scope
- New feature areas with uncertainty
- Team requests for decomposition analysis

**Skip for**:
- Bug fixes (usually atomic)
- Minor enhancements
- Well-defined small features
- Urgent hotfixes

### Reviewing Decomposition Results

Before implementing sub-issues, review:

1. **Logical boundaries**: Do sub-issues represent cohesive units of work?
2. **Dependencies**: Are dependency relationships correct and necessary?
3. **Granularity**: Are sub-issues too large or too small?
4. **Completeness**: Does decomposition cover all aspects of parent issue?
5. **Labels**: Are labels appropriate for routing to correct team members?

### Handling Medium/Low Confidence

When confidence is not "high":

1. **Manual review required**: Don't auto-execute decomposition
2. **Consider hybrid approach**: Implement core as single issue, extensions as sub-issues
3. **Gather more information**: May need clarification from issue author
4. **Start conservative**: When uncertain, prefer ATOMIC and decompose later if needed

## Future Enhancements

### Planned Improvements

1. **Learning from history**: Track which decompositions work well, adjust heuristics
2. **Custom decomposition strategies**: Per-project configuration for decision criteria
3. **Interactive mode**: Allow human to guide decomposition boundaries
4. **Effort estimation**: Include time estimates in sub-issues
5. **Auto-labeling**: Smarter label suggestions based on sub-issue content
6. **Parallel execution triggers**: Automatically start workflows on independent sub-issues
