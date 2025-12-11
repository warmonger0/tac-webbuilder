# ADW Phase Contracts and Dependencies

**Purpose:** This document defines explicit input/output contracts for all 10 ADW SDLC phases, making dependencies explicit and enabling better validation.

**Version:** 1.1
**Last Updated:** 2025-12-10
**Related:** Session 19 Phase 2 Part 2 - Single Source of Truth for ADW State

---

## State Management Architecture (SSoT)

**IMPORTANT:** All phases follow Single Source of Truth (SSoT) architecture for state management:

- **Database (phase_queue table)** = Coordination State (status, current_phase, timing)
- **Files (adw_state.json)** = Execution Metadata (paths, ports, outputs)

**Complete Documentation:** See `docs/adw/state-management-ssot.md` for full SSoT rules, decision tree, and examples.

**Key Rules:**
1. ✅ **DO** update database for workflow status and current phase (via `PhaseQueueRepository`)
2. ✅ **DO** update files for execution metadata (worktree paths, ports, results)
3. ✅ **DO** broadcast phase changes via WebSocket for real-time dashboard updates
4. ❌ **DO NOT** store `status` or `current_phase` in `adw_state.json`
5. ❌ **DO NOT** duplicate coordination state in both database and files

---

## Table of Contents

1. [Phase 1: Plan](#phase-1-plan)
2. [Phase 2: Validate](#phase-2-validate)
3. [Phase 3: Build](#phase-3-build)
4. [Phase 4: Lint](#phase-4-lint)
5. [Phase 5: Test](#phase-5-test)
6. [Phase 6: Review](#phase-6-review)
7. [Phase 7: Document](#phase-7-document)
8. [Phase 8: Ship](#phase-8-ship)
9. [Phase 9: Cleanup](#phase-9-cleanup)
10. [Phase 10: Verify](#phase-10-verify)

---

## Phase 1: Plan

**Script:** `adws/adw_plan_iso.py`
**Purpose:** Generate SDLC implementation plan in isolated worktree

### REQUIRES

**Input Parameters:**
- `issue_number`: int - Valid GitHub issue number
- `adw_id`: str (optional) - ADW identifier (auto-generated if not provided)

**Database State:**
- PostgreSQL connection available
- `phase_queue` table exists
- `observability_events` table exists

**External Services:**
- GitHub API accessible (issue read, comment write, PR create)
- Anthropic API accessible (plan generation via Claude Code)
- Git repository initialized with `main` branch

**Environment Variables:**
- `GITHUB_TOKEN` - GitHub PAT with repo:write access
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude

### PRODUCES

**Files Created:**
- `trees/{adw_id}/` - Isolated git worktree directory
- `trees/{adw_id}/specs/issue-{issue_number}-adw-{adw_id}-sdlc_planner-{slug}.md` - SDLC plan (5-15 KB)
- `trees/{adw_id}/specs/patch/patch-adw-{adw_id}-{slug}.md` - For patch issues
- `trees/{adw_id}/adw_state.json` - Initial state tracking
- `trees/{adw_id}/.ports.env` - Port configuration

**Database Records:**
- `phase_queue` record with:
  - `queue_id`: auto-increment
  - `adw_id`: workflow identifier
  - `issue_number`: GitHub issue number
  - `status`: 'planned'
  - `phase_name`: 'Plan'
  - `created_at`: timestamp

- `observability_events` record for plan creation:
  - `event_type`: 'phase_completion'
  - `phase_name`: 'Plan'
  - `adw_id`: workflow identifier
  - `success`: True
  - `timestamp`: completion time

**State Updates:**
- `adw_id`: workflow identifier
- `issue_number`: GitHub issue number
- `worktree_path`: absolute path to worktree
- `backend_port`: allocated port (9100-9114)
- `frontend_port`: allocated port (9200-9214)
- `branch_name`: generated feature branch name
- `plan_file`: absolute path to plan file
- `issue_class`: `/feature`, `/bug`, `/chore`, or `/patch`
- `integration_checklist`: dict with validation items
- `integration_checklist_markdown`: formatted markdown string
- `start_time`: ISO timestamp

**Return Values:**
- Exit code 0 on success
- Exit code 1 on failure
- JSON output with adw_id and worktree_path (via state file)

### STATE_MANAGEMENT

**Database Updates (Coordination):**
- Creates `phase_queue` record with `status='planned'` and `current_phase='plan'`
- Updates via `PhaseQueueRepository.insert_phase()`

**File Updates (Execution Metadata):**
- Creates `adw_state.json` with execution metadata (paths, ports, branch name)
- Does NOT include `status` or `current_phase` (database is SSoT)

**WebSocket Broadcast:**
- Broadcasts phase update for real-time dashboard: `broadcast_phase_update(adw_id, "Plan", "running")`

See `docs/adw/state-management-ssot.md` for complete SSoT rules.

### SIDE_EFFECTS

- Creates git worktree at `trees/{adw_id}/` with new branch
- Allocates ports deterministically based on adw_id
- Creates `.ports.env` in worktree with port configuration
- Updates GitHub issue with plan comment
- Creates/updates GitHub PR with plan
- Records cost in observability system
- Initializes directory structure in worktree

### ERROR_CONDITIONS

**Exit Code 1: Issue Not Found**
- Symptom: GitHub API returns 404 for issue number
- Message: "Issue #{issue_number} not found"
- Recovery: Verify issue exists and is accessible

**Exit Code 1: Invalid Issue Format**
- Symptom: Issue missing title, body, or required fields
- Message: "Error classifying issue: {error}"
- Recovery: Check issue has valid title and body

**Exit Code 1: Database Unavailable**
- Symptom: PostgreSQL connection fails
- Message: "Database connection failed: {error}"
- Recovery: Verify PostgreSQL is running and accessible

**Exit Code 1: Insufficient Permissions**
- Symptom: GitHub API returns 403
- Message: "GitHub API error: Insufficient permissions"
- Recovery: Check GITHUB_TOKEN has repo:write access

**Exit Code 1: Port Allocation Failure**
- Symptom: All ports in range are in use
- Message: "Could not allocate ports for ADW {adw_id}"
- Recovery: Free up ports or increase port range

**Exit Code 1: Worktree Creation Failed**
- Symptom: Git worktree add fails
- Message: "Error creating worktree: {error}"
- Recovery: Check git repository state, remove stale worktrees

**Exit Code 1: Plan File Not Found**
- Symptom: Agent created plan but file not at expected path
- Message: "Plan file not found at expected path: {path}"
- Recovery: Check agent output, verify file system permissions

---

## Phase 2: Validate

**Script:** `adws/adw_validate_iso.py`
**Purpose:** Establish baseline error state before implementation

### REQUIRES

**Input Parameters:**
- `issue_number`: str - GitHub issue number
- `adw_id`: str - ADW identifier (REQUIRED)

**State Fields:**
- `worktree_path`: absolute path to worktree
- `adw_id`: workflow identifier

**External Dependencies:**
- `adw_build_external.py` script exists
- Worktree exists at `worktree_path`
- PostgreSQL connection available

### PRODUCES

**State Updates:**
- `baseline_errors`: dict with:
  - `frontend.type_errors`: int - Number of TypeScript errors
  - `frontend.build_errors`: int - Number of build errors
  - `frontend.warnings`: int - Number of warnings
  - `frontend.error_details`: list - Detailed error information
  - `validation_timestamp`: ISO timestamp
  - `worktree_base_commit`: git commit hash
  - `duration_seconds`: float - Validation duration

**Database Records:**
- `observability_events` record for validation completion

### SIDE_EFFECTS

- Runs build check on UNMODIFIED worktree
- Updates state with baseline error data
- Posts GitHub comment with validation results
- Never modifies code

### ERROR_CONDITIONS

**Exit Code 0: Always Succeeds**
- This phase NEVER fails
- Errors are recorded as baseline data
- Workflow continues regardless of baseline state

**Warnings (Non-Blocking):**
- "Build external script not found" - Script missing, validation skipped
- "Failed to reload state" - State file issues, validation skipped
- "Validation encountered an issue: {error}" - Generic validation issues

---

## Phase 3: Build

**Script:** `adws/adw_build_iso.py`
**Purpose:** Implement solution based on plan in worktree

### REQUIRES

**Input Parameters:**
- `issue_number`: str - GitHub issue number
- `adw_id`: str - ADW identifier (REQUIRED)
- `--no-external`: flag (optional) - Disable external build tools

**State Fields (REQUIRED):**
- `worktree_path`: absolute path to worktree
- `branch_name`: feature branch name
- `plan_file`: absolute path to plan file
- `issue_class`: issue classification
- `baseline_errors` (optional): baseline error state from Validate phase

**External Dependencies:**
- `adw_build_external.py` script (if using external tools)
- Claude Code CLI available
- Plan file exists at `plan_file` path

### PRODUCES

**Code Changes:**
- Implementation files modified according to plan
- May create new files, modify existing files, or delete files

**State Updates:**
- `external_build_results`: dict with:
  - `success`: bool - Build passed
  - `summary.total_errors`: int - Total errors
  - `summary.type_errors`: int - TypeScript errors
  - `summary.build_errors`: int - Build errors
  - `errors`: list - Error details (file, line, column, message)

**Git Commits:**
- Commit message from `create_commit()` with:
  - Type: feat/fix/refactor based on `issue_class`
  - Subject: Brief description
  - Body: Detailed changes
  - Footer: ADW metadata

**Database Records:**
- `observability_events` record for build completion

### SIDE_EFFECTS

- Implements code changes in worktree
- Runs external build tools for type validation (if enabled)
- Performs differential error analysis (new vs baseline)
- Commits implementation to branch
- Pushes to remote and updates PR
- Posts GitHub comments with build results

### ERROR_CONDITIONS

**Exit Code 1: No State Found**
- Symptom: `adw_state.json` missing for adw_id
- Message: "No state found for ADW ID: {adw_id}"
- Recovery: Run Plan phase first

**Exit Code 1: Worktree Validation Failed**
- Symptom: Worktree doesn't exist or is invalid
- Message: "Worktree validation failed: {error}"
- Recovery: Run Plan phase to create worktree

**Exit Code 1: Missing Branch Name**
- Symptom: `branch_name` not in state
- Message: "No branch name in state - run adw_plan_iso.py first"
- Recovery: Run Plan phase to generate branch

**Exit Code 1: Missing Plan File**
- Symptom: `plan_file` not in state
- Message: "No plan file in state - run adw_plan_iso.py first"
- Recovery: Run Plan phase to create plan

**Exit Code 1: Build Errors (New)**
- Symptom: Build check detects NEW errors (not in baseline)
- Message: "Build check failed: {N} NEW error(s) introduced"
- Recovery: Fix type errors, re-run build
- Note: Baseline errors are ignored (differential analysis)

**Exit Code 1: Implementation Failed**
- Symptom: Claude Code fails to implement plan
- Message: "Error implementing solution: {error}"
- Recovery: Check plan file, verify Claude Code is working

**Exit Code 1: Commit Failed**
- Symptom: Git commit fails
- Message: "Error committing implementation: {error}"
- Recovery: Check git status, resolve conflicts

---

## Phase 4: Lint

**Script:** `adws/adw_lint_iso.py`
**Purpose:** Run linting with hybrid auto-fix loop

### REQUIRES

**Input Parameters:**
- `issue_number`: str - GitHub issue number
- `adw_id`: str - ADW identifier (REQUIRED)
- `--fix-mode`: flag (optional) - Enable auto-fix
- `--no-external`: flag (optional) - Disable external lint tools
- `--target=both|frontend|backend`: target selection (default: both)

**State Fields (REQUIRED):**
- `worktree_path`: absolute path to worktree
- `adw_id`: workflow identifier

**External Dependencies:**
- `adw_lint_external.py` script (if using external tools)
- `ruff` (Python linter) installed in worktree
- `eslint` (JavaScript/TypeScript linter) installed in worktree

### PRODUCES

**State Updates:**
- `external_lint_results`: dict with:
  - `success`: bool - All errors resolved
  - `summary.total_errors`: int - Total errors
  - `summary.style_errors`: int - Style errors
  - `summary.quality_errors`: int - Quality errors
  - `summary.fixable_count`: int - Auto-fixable errors
  - `errors`: list - Error details (file, line, rule, message)

**Code Changes:**
- Auto-fixed lint errors (if `--fix-mode` enabled)
- Multiple fix attempts (up to MAX_EXTERNAL_ATTEMPTS = 3)

**Git Commits:**
- One commit per auto-fix attempt with message:
  - `style: Auto-fix lint errors (attempt {N})`
  - Body: "Fixed errors using ruff/eslint auto-fix"

**Database Records:**
- `observability_events` record for lint completion

### SIDE_EFFECTS

- Runs hybrid lint loop:
  1. External auto-fix (up to 3 attempts)
  2. LLM fallback for remaining errors (if <50 errors)
- Commits auto-fixes after each attempt
- Posts GitHub comments with lint results
- **NEVER blocks workflow** - always continues

### ERROR_CONDITIONS

**Exit Code 0: Always Continues**
- This phase NEVER blocks the workflow
- Lint errors are logged and reduced, but workflow continues

**Warnings (Non-Blocking):**
- "External lint tool error: {error}" - External tool failed
- "LLM fallback not yet implemented" - Remaining errors logged
- "Inline lint execution not yet implemented" - Use external tools
- "{N} errors remaining (not blocking)" - Errors logged, workflow continues

**Hybrid Loop Behavior:**
- Attempt 1-3: External auto-fix tries to resolve errors
- After 3 attempts: LLM fallback (if enabled and <50 errors)
- Final: Always exits 0, logs remaining errors

---

## Phase 5: Test

**Script:** `adws/adw_test_iso.py`
**Purpose:** Run tests with resolution loop and coverage enforcement

### REQUIRES

**Input Parameters:**
- `issue_number`: str - GitHub issue number
- `adw_id`: str - ADW identifier (REQUIRED)
- `--skip-e2e`: flag (optional) - Skip E2E tests
- `--no-external`: flag (optional) - Disable external test tools
- `--skip-coverage`: flag (optional) - Skip coverage enforcement
- `--coverage-threshold N`: int (optional) - Override coverage threshold

**State Fields (REQUIRED):**
- `worktree_path`: absolute path to worktree
- `adw_id`: workflow identifier
- `baseline_errors` (optional): baseline from Validate phase

**External Dependencies:**
- `adw_test_external.py` script (if using external tools)
- `pytest` installed in worktree for backend tests
- `vitest` installed in worktree for frontend tests
- Test files exist in `tests/` directories

**GitHub Labels:**
- Issue must have label: `lightweight`, `standard`, or `complex` (for coverage threshold)
- Default: `standard` (70% coverage required)

### PRODUCES

**Test Results:**
- Unit test results (passed/failed counts)
- E2E test results (if not skipped)
- Coverage data:
  - `coverage.percentage`: float - Overall coverage %
  - `coverage.lines_covered`: int - Lines covered
  - `coverage.lines_total`: int - Total lines
  - `coverage.missing_files`: list - Files with 0% coverage

**State Updates:**
- `external_test_results`: dict with test results
- `coverage_check`: "passed" | "failed"
- `coverage_percentage`: float
- `coverage_threshold`: int
- `coverage_missing`: float (if failed)
- `coverage_lines_covered`: int
- `coverage_lines_total`: int

**Git Commits:**
- Commit with test results and any fixes

**Database Records:**
- `observability_events` record for test completion

### SIDE_EFFECTS

- Runs verification-based retry loop (max 3 attempts):
  1. Run tests
  2. If failures: Attempt resolution via `/resolve_failed_test`
  3. **CRITICAL:** Re-run tests to verify fixes
  4. Exit if no progress detected
- Circuit breaker: Detects agent loops (8+ comments in 15)
- Posts GitHub comments with test results
- Enforces coverage thresholds:
  - LIGHTWEIGHT: 0% (no requirement)
  - STANDARD: 70% minimum
  - COMPLEX: 80% minimum
- **BLOCKS on coverage failure** (exits 1 if coverage < threshold)
- **BLOCKS on test failures** after max retries

### ERROR_CONDITIONS

**Exit Code 1: Loop Detected**
- Symptom: Same agent posted 8+ times in last 15 comments
- Message: "Loop Detected - Aborting. Agent {agent} posted {count} times"
- Recovery: Manual review, check for stuck test failures

**Exit Code 1: No Progress Detected**
- Symptom: Tests re-run after resolution shows same failure count
- Message: "No Progress Detected. Agent claimed to fix {N} tests, but verification shows {M} failures remain"
- Recovery: Resolution didn't work, needs different approach

**Exit Code 1: Coverage Below Threshold**
- Symptom: Test coverage < required threshold for issue type
- Message: "Coverage check failed: {X}% < {threshold}%"
- Details:
  - Issue Type: LIGHTWEIGHT/STANDARD/COMPLEX
  - Current Coverage: {X}%
  - Required Coverage: {threshold}%
  - Missing Coverage: {diff}%
- Recovery: Add tests to increase coverage

**Exit Code 1: Test Failures After Max Retries**
- Symptom: Tests still failing after 3 resolution attempts
- Message: "Reached maximum retry attempts (3) with {N} failures"
- Recovery: Manual test fixes required

**Warnings (Non-Blocking):**
- "External test tool failed after retries, falling back to inline" - Infrastructure issues
- "Circuit breaker check failed (continuing anyway)" - Monitoring failure, continues

---

## Phase 6: Review

**Script:** `adws/adw_review_iso.py`
**Purpose:** Review implementation against spec with data integrity validation

### REQUIRES

**Input Parameters:**
- `issue_number`: str - GitHub issue number
- `adw_id`: str - ADW identifier (REQUIRED)
- `--skip-resolution`: flag (optional) - Disable blocker resolution

**State Fields (REQUIRED):**
- `worktree_path`: absolute path to worktree
- `plan_file`: absolute path to spec file
- `backend_port`: backend port for review
- `frontend_port`: frontend port for review

**External Dependencies:**
- R2 bucket configured (for screenshot uploads)
- Application can be started for review
- Spec file exists

### PRODUCES

**Review Results:**
- `review_summary`: str - Overall review summary
- `review_issues`: list of ReviewIssue:
  - `review_issue_number`: int - Issue number in review
  - `issue_description`: str - What's wrong
  - `issue_resolution`: str - How to fix
  - `issue_severity`: "blocker" | "tech_debt" | "skippable"
  - `screenshot_path`: str - Local screenshot path
  - `screenshot_url`: str - R2 uploaded URL
- `screenshots`: list of local paths
- `screenshot_urls`: list of R2 URLs

**Files Created:**
- Screenshots in `agents/{adw_id}/reviewer/review_img/`
- Uploaded to R2 at `adw/{adw_id}/review/{filename}`

**Git Commits:**
- Commit with review results

**Database Records:**
- `observability_events` record for review completion

### SIDE_EFFECTS

- Starts application using `prepare_application_for_review()`
- Captures screenshots of critical functionality
- Uploads screenshots to R2 storage
- **Data Integrity Validation:**
  - Checks if review shows empty data
  - Cross-references with database
  - Fails if DB has data but review shows empty (phantom failure)
- Blocker Resolution Loop (max 3 attempts):
  1. Run review
  2. If blockers found and `--skip-resolution` not set:
     - Create patch plans for each blocker
     - Implement patches
     - Re-run review
  3. Repeat until no blockers or max attempts reached

### ERROR_CONDITIONS

**Exit Code 1: No State Found**
- Symptom: `adw_state.json` missing
- Message: "No state found for ADW ID: {adw_id}"
- Recovery: Run previous phases

**Exit Code 1: Worktree Validation Failed**
- Symptom: Worktree invalid
- Message: "Worktree validation failed: {error}"
- Recovery: Check worktree state

**Exit Code 1: Spec File Not Found**
- Symptom: Cannot find spec file
- Message: "Could not find spec file for review"
- Recovery: Verify Plan phase created spec

**Exit Code 1: Data Integrity Failure**
- Symptom: Review shows empty data but database has records
- Message: "DATA INTEGRITY FAILURE! Database contains {N} records, but review shows empty data"
- Details:
  - Database record count
  - Backend log errors (if any)
  - Schema mismatch indicators
- Recovery: Fix backend query/schema issues
- **CRITICAL FIX (Issue #64):** Prevents false success from phantom failures

**Exit Code 1: Application Preparation Failed**
- Symptom: Cannot start backend/frontend for review
- Message: "Failed to prepare application: {error}"
- Recovery: Check port availability, service health

**Exit Code 1: Review Failed**
- Symptom: Review agent returns error
- Message: "Review failed: {error}"
- Recovery: Check review agent logs

---

## Phase 7: Document

**Script:** `adws/adw_document_iso.py`
**Purpose:** Generate feature documentation and update KPIs

### REQUIRES

**Input Parameters:**
- `issue_number`: str - GitHub issue number
- `adw_id`: str - ADW identifier (REQUIRED)

**State Fields (REQUIRED):**
- `worktree_path`: absolute path to worktree
- `plan_file`: absolute path to spec file

**External Dependencies:**
- Spec file exists
- Git changes exist between branch and `origin/main`

### PRODUCES

**Documentation Files:**
- Feature documentation in `app_docs/`
- README in archived folder (if cleanup runs)

**State Updates:**
- Documentation metadata

**Git Commits:**
- Commit with documentation
- Commit with KPI updates (separate, non-blocking)

**Database Records:**
- `observability_events` record for documentation completion
- Agentic KPI updates (via `/track_agentic_kpis`)

### SIDE_EFFECTS

- Pre-computes changed files list (deterministic, no AI)
- Generates documentation using `/document` command
- Tracks agentic KPIs (NEVER fails workflow)
- Posts GitHub comments with documentation status

### ERROR_CONDITIONS

**Exit Code 0: No Changes**
- Symptom: No git diff between branch and `origin/main`
- Message: "No changes detected - skipping documentation"
- Recovery: This is expected for no-op branches

**Exit Code 1: No State Found**
- Symptom: `adw_state.json` missing
- Message: "No state found for ADW ID: {adw_id}"
- Recovery: Run previous phases

**Exit Code 1: Worktree Validation Failed**
- Symptom: Worktree invalid
- Message: "Worktree validation failed: {error}"
- Recovery: Check worktree state

**Exit Code 1: Spec File Not Found**
- Symptom: Cannot find spec file
- Message: "Could not find spec file for documentation"
- Recovery: Verify Plan phase created spec

**Exit Code 1: Documentation Generation Failed**
- Symptom: Agent fails to create docs
- Message: "Documentation generation failed: {error}"
- Recovery: Check agent logs, verify spec file

**Warnings (Non-Blocking):**
- "Failed to update agentic KPIs - continuing anyway" - KPI tracking failed but workflow continues
- "Failed to commit KPI update" - KPI commit failed but workflow continues

---

## Phase 8: Ship

**Script:** `adws/adw_ship_iso.py`
**Purpose:** Merge PR and close issue with verification

### REQUIRES

**Input Parameters:**
- `issue_number`: str - GitHub issue number
- `adw_id`: str - ADW identifier (REQUIRED)

**State Fields (ALL REQUIRED):**
- `adw_id`: workflow identifier
- `issue_number`: GitHub issue number
- `branch_name`: feature branch name
- `plan_file`: plan file path
- `issue_class`: issue classification
- `worktree_path`: worktree path
- `backend_port`: backend port
- `frontend_port`: frontend port
- `integration_checklist` (optional): validation checklist

**External Dependencies:**
- GitHub PR exists for `branch_name`
- `gh` CLI authenticated
- PR is mergeable (no conflicts, checks passing)

### PRODUCES

**GitHub Actions:**
- PR merged via GitHub API (squash merge)
- Branch deleted (if not in use by worktree)
- Issue closed with success comment

**State Updates:**
- Ship completion metadata
- Merge verification results

**Database Records:**
- `observability_events` record for ship completion

### SIDE_EFFECTS

- Validates ALL state fields are populated (completeness check)
- Validates integration checklist (if present):
  - Checks required items
  - Posts validation report to PR
  - **Does NOT block** on failures, only reports
- Merges PR via `gh pr merge --squash --delete-branch`
- **CRITICAL:** Post-merge verification (prevents phantom merges):
  1. Get merge commit SHA from PR
  2. Fetch latest from `origin/main`
  3. Verify commit exists on `origin/main`
  4. Verify commit is ancestor of main HEAD
  5. **Fails if verification fails** (Issue #63 fix)
- Closes issue with success comment
- Updates issue with PR link

### ERROR_CONDITIONS

**Exit Code 1: No State Found**
- Symptom: `adw_state.json` missing
- Message: "No state found for ADW ID: {adw_id}"
- Recovery: Run previous phases

**Exit Code 1: State Validation Failed**
- Symptom: Required state fields are None
- Message: "State validation failed. Missing fields: {fields}"
- Missing fields examples:
  - plan_file, branch_name, issue_class (from Plan)
  - worktree_path, backend_port, frontend_port (from Plan)
- Recovery: Run missing phases

**Exit Code 1: Worktree Validation Failed**
- Symptom: Worktree doesn't exist
- Message: "Worktree validation failed: {error}"
- Recovery: Check worktree state

**Exit Code 1: No PR Found**
- Symptom: No PR exists for branch
- Message: "No PR found for branch {branch_name}"
- Recovery: Create PR manually or re-run Plan phase

**Exit Code 1: PR Merge Failed**
- Symptom: GitHub API returns error on merge
- Message: "Failed to merge PR #{pr_number}: {error}"
- Recovery: Check PR status, resolve conflicts, check CI

**Exit Code 1: Phantom Merge Detected**
- Symptom: GitHub reports merge success but commit not on main
- Message: "PHANTOM MERGE DETECTED! PR #{pr_number} reported as merged, but commit {sha} not found on main"
- Details:
  - Merge commit SHA
  - Branches containing commit
  - Origin/main status
- Recovery: Manual investigation required
- **CRITICAL FIX (Issue #63):** Prevents false success from phantom merges

**Warnings (Non-Blocking):**
- "PR merged but branch deletion failed (worktree in use)" - Branch will be cleaned up later
- "Integration checklist validation found issues" - Reported but doesn't block merge

---

## Phase 9: Cleanup

**Script:** `adws/adw_cleanup_iso.py`
**Purpose:** Organize documentation and free resources

### REQUIRES

**Input Parameters:**
- `issue_number`: str - GitHub issue number
- `adw_id`: str - ADW identifier (REQUIRED)

**State Fields:**
- `worktree_path`: worktree path to remove
- Any state from previous phases

**External Dependencies:**
- File system access to move files
- Git worktree command available

### PRODUCES

**File Reorganization:**
- Specs moved from `specs/` to `docs/archived_issues/{issue_number}/specs/`
- Plans moved to `docs/archived_issues/{issue_number}/plans/`
- Summaries moved to `docs/archived_issues/{issue_number}/summaries/`
- README created in archived folder

**Resources Freed:**
- Worktree removed at `trees/{adw_id}/`
- Ports freed (backend and frontend)
- Disk space freed

**State Updates:**
- Cleanup completion metadata

**Database Records:**
- `observability_events` record for cleanup completion

### SIDE_EFFECTS

- Moves documentation files to archived folder
- Creates README in archived folder
- Removes git worktree using `git worktree remove`
- Posts GitHub comments with cleanup summary
- **NEVER fails** - all errors logged as warnings

### ERROR_CONDITIONS

**Exit Code 0: Always Succeeds**
- This phase NEVER fails
- All errors are logged as warnings
- Workflow always completes

**Warnings (Non-Blocking):**
- "Documentation cleanup error (non-fatal): {error}" - File move failed
- "Failed to remove worktree: {error}" - Worktree removal failed
- "Error removing worktree (non-fatal): {error}" - Generic worktree error
- Manual cleanup: `./scripts/purge_tree.sh {adw_id}`

**Best-Effort Behavior:**
- Attempts to move all documentation files
- Attempts to remove worktree
- Logs errors but continues
- Posts summary of what succeeded/failed

---

## Phase 10: Verify

**Script:** `adws/adw_verify_iso.py`
**Purpose:** Post-deployment verification with follow-up issue creation

### REQUIRES

**Input Parameters:**
- `issue_number`: str - GitHub issue number
- `adw_id`: str - ADW identifier (REQUIRED)

**State Fields (REQUIRED):**
- `backend_port`: backend port for smoke tests
- `frontend_port`: frontend port for smoke tests
- `ship_timestamp` (optional): timestamp when Ship completed

**External Dependencies:**
- Backend logs at `logs/{adw_id}_backend.log`
- Frontend logs at `logs/{adw_id}_frontend_build.log`
- Application accessible on ports
- `gh` CLI for creating follow-up issues

**Timing:**
- Runs 5 minutes after Ship (VERIFICATION_DELAY_SECONDS = 300)
- Checks logs from last 10 minutes (LOG_CHECK_WINDOW_MINUTES = 10)

### PRODUCES

**Verification Results:**
- `backend_log_errors`: list - Backend error patterns found
- `frontend_errors`: list - Frontend console errors found
- `smoke_test_failures`: list - Health check failures
- `warnings`: list - Non-critical issues

**GitHub Actions:**
- Follow-up issue created (if failures detected):
  - Title: `[Auto-Verify] Post-deployment issues detected for #{issue_number}`
  - Labels: `bug`, `auto-verify`, `post-deployment`
  - Body: Detailed verification report with recommended actions
- Comment on original issue linking to follow-up

**Database Records:**
- `observability_events` record for verify completion

### SIDE_EFFECTS

- **Time delay:** Waits 5 minutes after ship for services to stabilize
- Checks backend logs for error patterns:
  - `Exception`, `Traceback`, `ERROR`, `500 Internal Server Error`, `Failed to`, `Error:`
- Checks frontend logs for console errors:
  - `console.error`, `console.warn`, `Uncaught`, `TypeError`, `ReferenceError`, `React.*Error`
- Runs smoke tests:
  - Backend health check: `curl http://localhost:{backend_port}/health`
  - Frontend accessibility: `curl http://localhost:{frontend_port}`
- **Non-blocking:** Creates issues but doesn't revert code
- Posts verification summary to original issue

### ERROR_CONDITIONS

**Exit Code 1: No State Found**
- Symptom: `adw_state.json` missing
- Message: "Verification failed: No state found"
- Recovery: Run previous phases

**Exit Code 1: Ports Not Found**
- Symptom: `backend_port` or `frontend_port` missing in state
- Message: "Verification failed: Ports not found in state"
- Recovery: Check Plan phase populated ports

**Exit Code 1: Verification Failed (With Follow-Up Issue)**
- Symptom: Errors/failures detected during verification
- Message: "Verification completed with issues. Follow-up issue #{N} created"
- Actions:
  - Follow-up issue created with:
    - Backend log errors (if any)
    - Frontend console errors (if any)
    - Smoke test failures (if any)
    - Recommended actions
  - Comment added to original issue
  - **Code NOT reverted** - issues addressed in new PR

**Exit Code 0: Verification Passed**
- Symptom: All checks completed successfully
- Message: "Verification passed. All checks completed successfully"
- Result:
  - Backend logs: Clean
  - Frontend console: Clean
  - Smoke tests: Passed

**Warnings (Non-Blocking):**
- "Ship timestamp not found in state, using fallback" - Uses current time - 10 minutes
- "Backend log file not found" - No log to check
- "Frontend build log not found" - No log to check
- "Failed to create follow-up issue" - Verification failed but issue creation failed

---

## Summary Matrix

| Phase | Blocks on Failure? | Can Skip? | Retries? | Max Duration |
|-------|-------------------|-----------|----------|--------------|
| 1. Plan | Yes | No | No | ~5 min |
| 2. Validate | No | No | No | ~2 min |
| 3. Build | Yes | No | No | ~10 min |
| 4. Lint | No | No | Yes (3x) | ~5 min |
| 5. Test | Yes (coverage) | No | Yes (3x) | ~20 min |
| 6. Review | Yes (data integrity) | No | Yes (3x blockers) | ~15 min |
| 7. Document | No (if no changes) | No | No | ~5 min |
| 8. Ship | Yes | No | No | ~2 min |
| 9. Cleanup | No (best-effort) | No | No | ~2 min |
| 10. Verify | No (creates issue) | No | No | ~10 min |

## Dependency Chain

```
Plan (Phase 1)
  ↓ produces: worktree, plan_file, branch_name, ports
Validate (Phase 2)
  ↓ produces: baseline_errors
Build (Phase 3)
  ↓ produces: implementation code
Lint (Phase 4)
  ↓ produces: lint results (non-blocking)
Test (Phase 5)
  ↓ produces: test results, coverage
Review (Phase 6)
  ↓ produces: review results, screenshots
Document (Phase 7)
  ↓ produces: documentation
Ship (Phase 8)
  ↓ produces: merged PR, closed issue
Cleanup (Phase 9)
  ↓ produces: organized docs, freed resources
Verify (Phase 10)
  ↓ produces: verification results, follow-up issue (if needed)
```

## Critical State Fields

These fields MUST be populated by Ship phase:

- `adw_id` - Workflow identifier (Plan)
- `issue_number` - GitHub issue (Plan)
- `branch_name` - Feature branch (Plan)
- `plan_file` - Spec file path (Plan)
- `issue_class` - Issue type (Plan)
- `worktree_path` - Worktree location (Plan)
- `backend_port` - Backend port (Plan)
- `frontend_port` - Frontend port (Plan)

Optional but recommended:

- `baseline_errors` - Error baseline (Validate)
- `integration_checklist` - Validation checklist (Plan)

---

**End of Phase Contracts Documentation**
