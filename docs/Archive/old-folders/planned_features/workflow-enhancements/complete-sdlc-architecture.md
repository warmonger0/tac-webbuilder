# Complete SDLC Architecture

## Overview

The Complete SDLC workflow (`adw_sdlc_complete_iso.py`) executes all 8 phases of the Software Development Life Cycle in isolation, providing production-ready features with comprehensive quality gates. This is the **RECOMMENDED** workflow for feature implementation, ensuring code quality through linting, testing, review, documentation, and automated shipping.

## The 8 Phases

```
┌─────────────────────────────────────────────────────────────┐
│                   COMPLETE SDLC WORKFLOW                     │
│                                                              │
│  Phase 1: PLAN      - Create implementation specification   │
│  Phase 2: BUILD     - Implement the solution                │
│  Phase 3: LINT      - Verify code quality standards  ✨ NEW │
│  Phase 4: TEST      - Run unit and integration tests        │
│  Phase 5: REVIEW    - Validate against requirements         │
│  Phase 6: DOCUMENT  - Generate comprehensive docs           │
│  Phase 7: SHIP      - Approve and merge PR           ✨ NEW │
│  Phase 8: CLEANUP   - Organize documentation         ✨ NEW │
│                                                              │
│  Each phase runs in isolated worktree with dedicated ports  │
│  Failure at any phase (1-5) aborts the workflow             │
│  Documentation/cleanup failures are non-blocking            │
└─────────────────────────────────────────────────────────────┘
```

### Phase 1: PLAN

**Purpose**: Create detailed implementation specification

**What it does**:
1. Creates isolated git worktree at `trees/<adw_id>/`
2. Allocates unique ports (backend: 9100-9114, frontend: 9200-9214)
3. Fetches and classifies GitHub issue (bug/feature/chore)
4. Creates feature branch in worktree
5. Generates implementation plan with AI
6. Commits plan and creates/updates pull request

**Outputs**:
- Implementation plan: `agents/<adw_id>/<adw_id>_plan_spec.md`
- Worktree: `trees/<adw_id>/`
- Branch: `feat-123-abc12345-feature-name`
- Pull request on GitHub

**Can use optimized variant**: `adw_plan_iso_optimized.py`
- Uses inverted context flow
- 77% cost reduction (1.173M → 271K tokens)
- Single comprehensive AI call vs multiple sequential calls

**State saved**:
```json
{
  "adw_id": "abc12345",
  "issue_number": "123",
  "issue_class": "/feature",
  "branch_name": "feat-123-abc12345-add-export",
  "plan_file": "agents/abc12345/abc12345_plan_spec.md",
  "worktree_path": "trees/abc12345",
  "backend_port": 9107,
  "frontend_port": 9207
}
```

### Phase 2: BUILD

**Purpose**: Implement the solution according to plan

**What it does**:
1. Validates worktree exists and switches to correct branch
2. Reads implementation plan from Phase 1
3. Implements solution using AI with full codebase context
4. Runs build checks (TypeScript compilation)
5. Commits changes and pushes to PR

**External tool optimization** (optional):
- `--no-external` flag disables optimization
- With external tools (default): 70-95% token reduction
- Executes builds externally, returns only errors
- Passes compact JSON to AI instead of full build logs

**Typical changes**:
- Source code modifications
- Configuration updates
- Database migrations (if needed)
- API endpoint additions/modifications

**Validation**:
- TypeScript compiles without errors
- No syntax errors introduced
- Changes align with plan

### Phase 3: LINT ✨ NEW

**Purpose**: Enforce code quality standards before testing

**What it does**:
1. Runs linters on modified code (ESLint, Pylint, etc.)
2. Checks code formatting (Prettier, Black, etc.)
3. Validates import organization
4. Identifies code smells and anti-patterns
5. Auto-fixes issues when possible
6. Commits fixes if auto-fix applied

**Why this phase is critical**:

Before Phase 3 existed, issues would proceed to testing/review with:
- Inconsistent code formatting
- Linting violations
- Import order issues
- Code style inconsistencies

This caused:
- Review phase wasted time on style issues
- Test failures due to linting errors
- Back-and-forth between phases
- Higher overall token usage
- Delayed shipping

**With Phase 3**:
- Code quality enforced BEFORE testing
- Review focuses on logic, not style
- Consistent code across all features
- Faster review cycles
- Professional quality output

**External tool optimization** (optional):
- Runs linters externally
- Returns only violations in compact JSON
- AI sees structured errors, not raw logs
- 80-90% token reduction for linting phase

**Lint rules enforced**:
- ESLint for TypeScript/JavaScript
- Pylint for Python
- Prettier for code formatting
- Import organization (isort, etc.)
- Custom project-specific rules

**Failure handling**:
- Critical violations: Abort workflow
- Auto-fixable issues: Fix and continue
- Warnings: Log but allow continuation

### Phase 4: TEST

**Purpose**: Verify implementation correctness

**What it does**:
1. Runs unit tests with pytest (backend) and vitest (frontend)
2. Measures code coverage
3. Identifies failing tests
4. Auto-resolves test failures with AI assistance
5. Optionally runs E2E tests (skipped in SDLC workflows)
6. Commits test additions/fixes

**Test execution**:
- Backend: `pytest` with coverage reporting
- Frontend: `vitest` with coverage reporting
- Always skips E2E tests in SDLC (use `--skip-e2e` flag)

**External tool optimization** (optional):
- Executes tests externally
- Returns only test failures in compact JSON
- 90% token reduction when tests pass (50K → 5K tokens)
- 84% reduction even with failures (50K → 8K tokens)

**Auto-resolution**:
- Analyzes test failures
- Identifies root causes
- Generates fixes
- Re-runs tests to verify
- Maximum 3 resolution attempts

**Failure handling**:
- Aborts workflow if tests fail after auto-resolution
- Posts failure details to GitHub issue
- Developer must fix manually

### Phase 5: REVIEW

**Purpose**: Validate implementation against requirements

**What it does**:
1. Compares implementation to original issue requirements
2. Checks for completeness and correctness
3. Captures screenshots of UI changes (using isolated ports)
4. Identifies blockers, warnings, and suggestions
5. Auto-resolves blockers with AI assistance
6. Uploads screenshots to GitHub PR

**Review criteria**:
- All acceptance criteria met
- No functional regressions
- UI/UX matches specifications
- Error handling implemented
- Edge cases considered

**Screenshot capture**:
- Uses allocated ports (9100-9114 backend, 9200-9214 frontend)
- Captures before/after states
- Annotates with review findings
- Uploads to PR for human verification

**Auto-resolution** (optional, disable with `--skip-resolution`):
- Addresses blocking issues
- Makes necessary corrections
- Re-runs review to verify
- Maximum 3 resolution attempts

**Failure handling**:
- Blockers: Abort workflow unless auto-resolved
- Warnings: Continue but document
- Suggestions: Note for future improvements

### Phase 6: DOCUMENT

**Purpose**: Generate comprehensive documentation

**What it does**:
1. Analyzes changes in worktree
2. Identifies new features and modifications
3. Generates documentation in `app_docs/`
4. Creates feature overviews and technical guides
5. Documents API changes and usage examples
6. Commits documentation

**Documentation generated**:
- Feature overviews: `app_docs/features/<feature>/overview.md`
- Technical guides: `app_docs/features/<feature>/technical-guide.md`
- API documentation (if applicable)
- Usage examples and tutorials

**Failure handling**:
- Non-blocking: Documentation failure does NOT abort workflow
- Logs warning and continues to ship
- Can be re-run manually later

**Rationale for non-blocking**:
- Documentation can be added post-release
- Should not block critical bug fixes
- Can be improved iteratively

### Phase 7: SHIP ✨ NEW

**Purpose**: Approve and merge PR to production

**What it does**:
1. Validates ADWState completeness (all required fields present)
2. Verifies worktree exists and is clean
3. Finds PR for the feature branch
4. Approves the PR via GitHub API
5. Merges PR to main using squash method
6. Confirms merge success

**State validation**:
Before shipping, ensures all fields are populated:
- `adw_id`: Workflow identifier
- `issue_number`: GitHub issue being addressed
- `branch_name`: Feature branch name
- `plan_file`: Implementation plan location
- `issue_class`: Issue type classification
- `worktree_path`: Isolated worktree location
- `backend_port`: Allocated backend port
- `frontend_port`: Allocated frontend port

**Merge strategy**:
- Uses squash merge to keep main branch history clean
- Single commit per feature
- Preserves issue references

**Failure handling**:
- Critical: Abort if state validation fails
- Critical: Abort if PR cannot be found
- Critical: Abort if merge fails
- Posts error details to GitHub issue
- Manual intervention required

**Difference from ZTE variant**:
- `adw_sdlc_complete_iso.py`: Ships after all phases pass
- `adw_sdlc_complete_zte_iso.py`: Ships automatically (Zero Touch Execution)

### Phase 8: CLEANUP ✨ NEW

**Purpose**: Organize documentation and free resources

**What it does**:
1. Moves documentation from active to archived locations
2. Organizes files by feature and date
3. Removes worktree (optional, enabled by default)
4. Frees allocated ports
5. Updates state to mark completion

**Cleanup operations** (pure Python, no LLM calls):
- Move completed docs to `docs/archive/`
- Organize by feature and timestamp
- Remove temporary files
- Clean up agent output directories
- Remove worktree via `git worktree remove`

**Failure handling**:
- Non-blocking: Cleanup failure does NOT abort workflow
- Logs warnings for partial failures
- Workflow still considered successful
- Manual cleanup possible via `./scripts/purge_tree.sh <adw_id>`

**Rationale for non-blocking**:
- Cleanup is housekeeping, not quality gate
- Manual cleanup is straightforward
- Should not block successful feature delivery

## Why Lint Was Missing and Why It's Critical

### Historical Context: The Missing Phase

**Original SDLC** (Phases 1-7 without Lint):
```
Plan → Build → Test → Review → Document → Ship → Cleanup
```

**Problems encountered**:
1. **Style inconsistencies**: Every implementation had different formatting
2. **Test failures from linting**: Tests would fail on style violations
3. **Review waste**: Reviewers spent time on style instead of logic
4. **Back-and-forth**: Build → Test fails on style → Build again → Test again
5. **Increased token usage**: Multiple passes to fix linting issues
6. **Unprofessional output**: Inconsistent code quality

**Example scenario without Lint phase**:
```
Phase 2 (Build): Implements feature, no formatting check
Phase 4 (Test): Tests fail because ESLint errors in test files
Phase 2 (Build): Fix ESLint errors
Phase 4 (Test): Tests pass but code still has Prettier violations
Phase 5 (Review): Reviewer requests formatting fixes
Phase 2 (Build): Apply Prettier
Phase 4 (Test): Re-run tests
Phase 5 (Review): Finally approved

Result: 6 phases instead of 5, higher cost, more time
```

### Why Lint Phase is Critical

**1. Separation of Concerns**

Each phase has a clear responsibility:
- Build: Implement functionality
- **Lint: Ensure code quality**
- Test: Verify correctness
- Review: Validate requirements

Without Lint, Build or Test had to handle quality, creating confusion.

**2. Early Failure Detection**

Catches issues BEFORE expensive testing:
- Syntax errors
- Import problems
- Formatting inconsistencies
- Code smells

Failing fast saves tokens and time.

**3. Consistent Quality**

Enforces standards across all features:
- Every feature follows same style guide
- No "good code" vs "sloppy code"
- Professional codebase appearance
- Easier maintenance long-term

**4. Reduced Cognitive Load**

Developers and reviewers focus on logic:
- Build: "Does this implement the feature?"
- Lint: "Does this meet quality standards?"
- Test: "Does this work correctly?"
- Review: "Does this meet requirements?"

Clear responsibilities reduce cognitive burden.

**5. Token Efficiency**

Structured linting output is compact:
```json
{
  "errors": [
    {
      "file": "app/client/src/Component.tsx",
      "line": 42,
      "rule": "react-hooks/exhaustive-deps",
      "message": "Missing dependency 'userId'"
    }
  ]
}
```

VS raw ESLint output (hundreds of lines of text).

### Integration Point

**Optimal position: After Build, Before Test**

```
Phase 2 (Build): Create functionality
Phase 3 (Lint): Verify code quality ← QUALITY GATE
Phase 4 (Test): Verify correctness
```

**Why not before Build?**
- Nothing to lint yet
- Build creates the code to check

**Why not after Test?**
- Test failures might be due to linting issues
- Want to catch quality issues before running expensive tests

**Why not combine with Build?**
- Build focuses on functionality
- Lint focuses on quality
- Separate concerns, separate phases

## Phase Dependencies and Ordering

### Critical Dependencies

```
Phase 1 (PLAN)
    ↓ Creates worktree, branch, plan file
Phase 2 (BUILD)
    ↓ Creates code to lint
Phase 3 (LINT)
    ↓ Ensures quality before testing
Phase 4 (TEST)
    ↓ Verifies correctness
Phase 5 (REVIEW)
    ↓ Validates requirements
Phase 6 (DOCUMENT)
    ↓ Documents features
Phase 7 (SHIP)
    ↓ Merges to production
Phase 8 (CLEANUP)
    ↓ Cleanup and archival
```

### Why This Order?

**1. Plan → Build**: Cannot build without plan
- Plan defines WHAT to build
- Build implements HOW to build it

**2. Build → Lint**: Cannot lint non-existent code
- Lint checks code quality
- Must have code first

**3. Lint → Test**: Quality before correctness
- Linting errors can cause test failures
- Fix quality issues before testing logic
- Avoid false test failures

**4. Test → Review**: Correctness before validation
- Review assumes tests pass
- No point reviewing broken code
- Tests validate implementation, review validates requirements

**5. Review → Document**: Document what works
- Documentation describes validated features
- Should not document non-working code
- Review ensures features are complete

**6. Document → Ship**: Ship documented features
- Production code should have documentation
- Documentation helps future maintenance
- Non-blocking: can ship without docs in emergencies

**7. Ship → Cleanup**: Clean up after deployment
- Cleanup shouldn't prevent shipping
- Worktree needed until merge completes
- Free resources after successful deployment

### Required vs Optional Phases

**Required (blocking)**:
- Phase 1: PLAN - Cannot proceed without plan
- Phase 2: BUILD - Cannot test non-existent code
- Phase 3: LINT - Cannot ship poor quality code
- Phase 4: TEST - Cannot ship broken code
- Phase 5: REVIEW - Cannot ship unvalidated code

**Optional (non-blocking)**:
- Phase 6: DOCUMENT - Can ship without docs (warning logged)
- Phase 8: CLEANUP - Can leave worktree (manual cleanup later)

**Conditional**:
- Phase 7: SHIP - Only in complete/ZTE workflows, not basic SDLC

### Parallel Execution Opportunities

While phases must run sequentially, **sub-issues can run in parallel**:

```
Parent Issue #100: Implement dashboard
    ↓ Stepwise decomposition
Sub-issue #101: User metrics   ┐
Sub-issue #102: System health  ├─ Run in parallel
Sub-issue #103: Revenue charts ┘
    ↓ All complete
Sub-issue #104: Dashboard layout (depends on 101-103)
```

Each sub-issue runs complete SDLC independently.

## External Workflow Optimization

### The Problem: Token Waste

**Traditional inline execution**:
```
AI: "Run tests"
System: Executes pytest
System: Returns 5000 lines of test output
AI: Reads all 5000 lines
AI: Identifies 3 failures
AI: Generates fixes
```

**Token usage**: 50K tokens to process test output

### The Solution: External Tools

**Optimized external execution**:
```
Main workflow: Calls external test ADW
External ADW: Runs pytest
External ADW: Parses output to JSON
External ADW: Returns only failures
{
  "failures": [
    {"test": "test_auth", "line": 42, "error": "AssertionError"}
  ]
}
Main workflow: Passes compact JSON to AI
AI: Sees structured data
AI: Generates fixes
```

**Token usage**: 5K tokens (90% reduction)

### External Tool Chain

```
Main ADW (adw_test_iso.py)
    ↓ subprocess.run()
External ADW Wrapper (adw_test_external.py)
    ↓ Loads state, gets worktree_path
    ↓ subprocess.run()
Tool Workflow (adw_test_workflow.py)
    ↓ Executes pytest/vitest
    ↓ Returns compact JSON (failures only)
    ↓ Stores in state["external_test_results"]
Main ADW reads state
    ↓ Processes compact results
```

### Available External Tools

**1. Test Runner** (`adw_test_workflow.py`)
- Runs pytest/vitest externally
- Returns only failures
- 90% token reduction (50K → 5K tokens)

**2. Build Checker** (`adw_build_workflow.py`)
- Runs TypeScript/build externally
- Returns only errors
- 85% token reduction (30K → 4K tokens)

**3. Lint Checker** (`adw_lint_workflow.py`)
- Runs ESLint/Pylint externally
- Returns only violations
- 80-90% token reduction

### When to Use External Tools

**Use external tools (default)**:
- Standard test suites
- TypeScript compilation
- Linting checks
- When output is predictable and parseable

**Use inline execution (`--no-external`)**:
- Complex debugging scenarios
- When AI needs full context
- Non-standard tooling
- Development/testing of workflows themselves

### Configuration Flags

```bash
# Enable external tools (default, recommended)
uv run adw_sdlc_complete_iso.py 123

# Disable external tools (higher token usage)
uv run adw_sdlc_complete_iso.py 123 --no-external

# Use optimized planner (77% cost reduction)
uv run adw_sdlc_complete_iso.py 123 --use-optimized-plan

# Both optimizations (maximum savings)
uv run adw_sdlc_complete_iso.py 123 --use-optimized-plan
# (external tools are enabled by default)
```

## Error Handling at Each Phase

### Phase 1: PLAN

**Possible errors**:
- GitHub API failures (rate limit, permissions)
- Worktree creation failures (disk space, git errors)
- AI planning failures (invalid output, timeouts)

**Handling**:
- Retry GitHub API with exponential backoff
- Validate worktree before proceeding
- Parse and validate AI output structure
- Abort on critical errors, post to GitHub issue

**Exit behavior**:
- Exit code 1 on failure
- Worktree removed if created
- No PR created
- Issue comment explains failure

### Phase 2: BUILD

**Possible errors**:
- Worktree not found (invalid ADW ID)
- Plan file missing or corrupted
- Build failures (TypeScript errors)
- AI implementation failures

**Handling**:
- Validate state before starting
- Verify plan file exists and is readable
- Run builds externally, parse errors
- Retry failed builds once
- Abort if critical errors persist

**Exit behavior**:
- Exit code 1 on failure
- Changes may be partially committed
- PR updated with error details
- Worktree preserved for debugging

### Phase 3: LINT

**Possible errors**:
- Linter not installed
- Configuration file missing
- Critical linting violations
- Auto-fix failures

**Handling**:
- Verify linter availability before running
- Use default config if project config missing
- Attempt auto-fix for fixable issues
- Abort on critical violations
- Log warnings for minor issues

**Exit behavior**:
- Exit code 1 on critical violations
- Auto-fixed changes committed
- PR updated with linting report
- Developer must address violations

### Phase 4: TEST

**Possible errors**:
- Test suite failures
- Coverage below threshold
- Test environment setup failures
- Timeout on long-running tests

**Handling**:
- Auto-resolve up to 3 times
- Identify root causes with AI
- Generate and apply fixes
- Re-run tests to verify
- Abort if auto-resolution fails

**Exit behavior**:
- Exit code 1 on test failures
- Test output saved to state
- PR updated with failure details
- Manual fix required

### Phase 5: REVIEW

**Possible errors**:
- Screenshot capture failures
- Blocker findings (requirements not met)
- Server startup failures (ports in use)
- AI review failures

**Handling**:
- Retry screenshot capture up to 3 times
- Auto-resolve blockers (unless --skip-resolution)
- Fall back to alternative ports
- Continue without screenshots if persistent failures

**Exit behavior**:
- Exit code 1 on unresolved blockers
- Warnings logged but workflow continues
- Screenshots uploaded if captured
- PR updated with review findings

### Phase 6: DOCUMENT

**Possible errors**:
- Documentation generation failures
- File write errors (permissions)
- AI documentation failures

**Handling**:
- **Non-blocking**: Log error and continue
- Attempt to generate partial docs
- Skip if critical errors
- Workflow continues to ship

**Exit behavior**:
- Exit code 0 (success) even on failure
- Warning posted to GitHub
- Can re-run documentation later
- Does NOT block shipping

### Phase 7: SHIP

**Possible errors**:
- State validation failures (incomplete state)
- PR not found
- Approval failures (permissions)
- Merge conflicts
- Merge failures

**Handling**:
- Validate state completely before shipping
- Search for PR by branch name
- Verify user has approval permissions
- Check for merge conflicts
- Abort on any critical error

**Exit behavior**:
- Exit code 1 on failure
- PR remains open
- Issue comment explains failure
- Manual intervention required

### Phase 8: CLEANUP

**Possible errors**:
- File move failures (permissions)
- Worktree removal failures (in use)
- Directory access errors

**Handling**:
- **Non-blocking**: Log errors and continue
- Attempt each cleanup operation
- Continue even if some fail
- Report partial success

**Exit behavior**:
- Exit code 0 (success) even on partial failure
- Warnings posted to GitHub
- Manual cleanup script available
- Workflow considered successful

## When to Use Complete vs Partial Workflows

### Complete SDLC (`adw_sdlc_complete_iso.py`)

**Use for**:
- Production features
- User-facing changes
- API modifications
- Critical bug fixes
- Anything requiring documentation
- Features that will be shipped

**Characteristics**:
- All 8 phases
- Lint + Test + Review quality gates
- Documentation generated
- Shipped to production
- Highest confidence in quality

**Cost**: $4-6 per workflow (with external tools)
**Time**: 15-30 minutes
**Quality**: Production-ready

### Lightweight SDLC (`adw_lightweight_iso.py`)

**Use for**:
- Quick experiments
- Proof of concepts
- Development testing
- Features not ready to ship
- Throwaway implementations

**Characteristics**:
- Plan + Build only
- No quality gates
- No documentation
- No shipping
- Fast iteration

**Cost**: $1-2 per workflow
**Time**: 5-10 minutes
**Quality**: Development-grade

### Individual Phases

**Use for**:
- Re-running failed phases
- Debugging specific issues
- Incremental development
- Manual quality checks

**Examples**:
```bash
# Just test existing implementation
uv run adw_test_iso.py 123 abc12345

# Just lint existing code
uv run adw_lint_iso.py 123 abc12345

# Just review existing implementation
uv run adw_review_iso.py 123 abc12345
```

### Zero Touch Execution (`adw_sdlc_complete_zte_iso.py`)

**Use for**:
- Fully automated deployments
- Well-tested issue types
- Low-risk changes
- Documentation updates
- Minor enhancements

**Characteristics**:
- All 8 phases including auto-ship
- No human intervention
- Merges to main automatically
- Highest automation

**Cost**: $4-6 per workflow
**Time**: 15-30 minutes
**Risk**: Ships automatically, use with caution

### Comparison Table

| Workflow | Phases | Quality Gates | Ships | Documentation | Use Case |
|----------|--------|---------------|-------|---------------|----------|
| Complete SDLC | 8 | Lint, Test, Review | Manual | Yes | Production features |
| Complete ZTE | 8 | Lint, Test, Review | Auto | Yes | Trusted automation |
| Standard SDLC | 5 | Test, Review | No | No | Pre-lint workflows |
| Lightweight | 2 | None | No | No | Quick experiments |
| Individual | 1 | Phase-specific | No | No | Debugging, re-runs |

## Cost Comparison

### Complete SDLC Cost Breakdown

**With external tools (default, recommended)**:
- Phase 1 (Plan): $0.34 (optimized) or $1.90 (standard)
- Phase 2 (Build): $0.50 (with external build checks)
- Phase 3 (Lint): $0.10 (external lint results)
- Phase 4 (Test): $0.20 (external test results, passing)
- Phase 5 (Review): $1.50 (screenshots and validation)
- Phase 6 (Document): $0.80 (documentation generation)
- Phase 7 (Ship): $0.05 (state validation, API calls)
- Phase 8 (Cleanup): $0.00 (pure Python, no LLM)

**Total: $3.49 (optimized) or $5.05 (standard)**

**Without external tools (`--no-external`)**:
- Phase 1 (Plan): $0.34 (optimized) or $1.90 (standard)
- Phase 2 (Build): $2.50 (inline build checking)
- Phase 3 (Lint): $1.20 (inline lint processing)
- Phase 4 (Test): $2.00 (inline test processing)
- Phase 5 (Review): $1.50 (same, screenshots required)
- Phase 6 (Document): $0.80 (same)
- Phase 7 (Ship): $0.05 (same)
- Phase 8 (Cleanup): $0.00 (same)

**Total: $8.39 (optimized) or $10.05 (standard)**

**Savings with external tools: 58-50%**

### Incomplete Workflow Costs (Historical)

**Before Lint phase existed** (Plan → Build → Test → Review → Document):
- Build failures due to linting: +$0.50 per retry
- Test failures due to style: +$0.50 per retry
- Review iterations for formatting: +$0.30 per iteration
- Average retries: 2-3
- **Total additional cost: $2.60-3.90**
- **Total workflow cost: $7.65-10.95**

**With Lint phase** (current):
- Lint catches issues early: $0.10
- No build/test retries for style
- No review iterations for formatting
- **Total workflow cost: $3.49-5.05**

**Savings from Lint phase: 54-54% vs incomplete workflow**

### ROI Analysis

**Investment**:
- Initial setup: $0 (already implemented)
- Per-workflow cost: $3.49-5.05

**Returns**:
- No manual code review for style: 15-30 minutes saved
- No back-and-forth for linting: 2-3 iterations avoided
- Professional code quality: Improved maintainability
- Faster onboarding: Consistent style across codebase

**Break-even**: Immediate (prevents more expensive incomplete workflows)

**Long-term value**:
- Consistent codebase: Easier maintenance
- Professional output: Better team morale
- Automated quality: No manual enforcement needed

## Technical Implementation

### File: `adw_sdlc_complete_iso.py`

**Structure**:
```python
def main():
    # Parse flags
    skip_e2e = "--skip-e2e" in sys.argv
    use_external = "--no-external" not in sys.argv
    use_optimized_plan = "--use-optimized-plan" in sys.argv

    # Ensure ADW ID
    adw_id = ensure_adw_id(issue_number, adw_id)

    # Execute phases sequentially
    # Phase 1: PLAN
    plan_script = "adw_plan_iso_optimized.py" if use_optimized_plan else "adw_plan_iso.py"
    subprocess.run([...])
    if returncode != 0: abort()

    # Phase 2: BUILD
    subprocess.run([...])
    if returncode != 0: abort()

    # Phase 3: LINT ✨
    subprocess.run([...])
    if returncode != 0: abort()

    # Phase 4: TEST
    subprocess.run([...])
    if returncode != 0: abort()

    # Phase 5: REVIEW
    subprocess.run([...])
    if returncode != 0: abort()

    # Phase 6: DOCUMENT
    subprocess.run([...])
    if returncode != 0: warn_and_continue()

    # Phase 7: SHIP ✨
    subprocess.run([...])
    if returncode != 0: abort()

    # Phase 8: CLEANUP ✨
    cleanup_shipped_issue(...)
    if errors: warn_but_continue()

    # Success!
    post_completion_message()
```

### State Management

**ADWState fields**:
```json
{
  "adw_id": "abc12345",
  "issue_number": "123",
  "issue_class": "/feature",
  "branch_name": "feat-123-abc12345-export",
  "plan_file": "agents/abc12345/abc12345_plan_spec.md",
  "worktree_path": "trees/abc12345",
  "backend_port": 9107,
  "frontend_port": 9207,
  "external_build_results": {...},
  "external_test_results": {...},
  "external_lint_results": {...}
}
```

### GitHub Integration

**Issue comments**:
- Start: "Starting Complete SDLC Workflow"
- Each phase: "Phase X/8: [NAME]" with status
- Success: "Complete SDLC Finished!"
- Failure: "SDLC aborted - [PHASE] failed"

**PR updates**:
- Plan committed
- Implementation committed
- Lint fixes committed
- Test fixes committed
- Review fixes committed
- Documentation committed
- PR approved and merged (Phase 7)

## Best Practices

### When to Run Complete SDLC

**Always use for**:
- User-facing features
- API changes
- Database migrations
- Security fixes
- Performance optimizations
- Production bug fixes

**Consider lightweight for**:
- Internal refactoring (no user impact)
- Development tooling
- Experimental features
- Proof of concepts

### Configuration Recommendations

**Default (recommended)**:
```bash
uv run adw_sdlc_complete_iso.py 123 --use-optimized-plan
```
- External tools enabled (default)
- Optimized planner (77% cost reduction)
- All quality gates enforced
- **Cost: ~$3.50, Time: 15-25 minutes**

**Debugging mode**:
```bash
uv run adw_sdlc_complete_iso.py 123 --no-external
```
- Inline execution (AI sees full output)
- Useful for troubleshooting
- **Cost: ~$8.40, Time: 20-30 minutes**

**Fast iteration**:
```bash
uv run adw_lightweight_iso.py 123
```
- Plan + Build only
- No quality gates
- **Cost: ~$1.50, Time: 5-10 minutes**

### Monitoring Workflow Progress

**Check logs**:
```bash
tail -f logs/abc12345_adw_sdlc_complete_iso.log
```

**Check state**:
```bash
cat agents/abc12345/adw_state.json | jq
```

**Check worktree**:
```bash
cd trees/abc12345
git status
git log
```

### Handling Failures

**Phase 1-5 failures**: Critical, must fix
- Review error logs
- Fix underlying issue
- Re-run complete workflow

**Phase 6 failure**: Non-critical, can skip
- Document manually later
- Or re-run: `uv run adw_document_iso.py 123 abc12345`

**Phase 8 failure**: Non-critical, cleanup manually
- Run: `./scripts/purge_tree.sh abc12345`
- Or leave for periodic cleanup

## Future Enhancements

### Planned Improvements

1. **Parallel sub-issue execution**: Auto-trigger workflows on independent sub-issues
2. **Smart retry**: Automatically retry transient failures
3. **Incremental phases**: Resume from failed phase instead of full re-run
4. **Phase telemetry**: Track success rates and average costs per phase
5. **Custom phase ordering**: Allow project-specific phase sequences
6. **Conditional phases**: Skip phases based on issue type (e.g., no E2E for backend-only changes)

### Integration Opportunities

1. **CI/CD integration**: Trigger on PR events
2. **Slack notifications**: Real-time phase completion updates
3. **Dashboard**: Visualize workflow progress and metrics
4. **Quality metrics**: Track lint/test/review trends over time
