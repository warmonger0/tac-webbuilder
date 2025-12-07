# AI Developer Workflow (ADW) System - Isolated Workflows

ADW automates software development using isolated git worktrees. The `_iso` suffix stands for "isolated" - these workflows run in separate git worktrees, enabling multiple agents to run at the same time in their own respective directories. Each workflow gets its own complete copy of the repository with dedicated ports and filesystem isolation.

## 🛡️ Robustness System

The ADW system includes comprehensive safeguards to ensure reliable execution:

✅ **Pre-flight Checks** - Prevents bad launches (git state, ports, tests, disk, Python env)
✅ **Automatic Cleanup** - Closes PRs and cleans resources on workflow failures
✅ **Automatic Issue Closing** - Closes issues on successful ship

**For complete details, see [`docs/ADW_ROBUSTNESS_SYSTEM.md`](../docs/ADW_ROBUSTNESS_SYSTEM.md)**

**Quick tips:**
- Ensure main branch is clean before launching (most common blocker)
- Failed workflows automatically close their PRs - no manual cleanup needed
- Successful workflows automatically close issues - no manual closing needed

## Key Concepts

### Isolated Execution
Every ADW workflow runs in an isolated git worktree under `trees/<adw_id>/` with:
- Complete filesystem isolation
- Dedicated port ranges (backend: 9100-9199, frontend: 9200-9299)
- Independent git branches
- Support for up to 100 concurrent instances via port pool reservation system

### ADW ID
Each workflow run is assigned a unique 8-character identifier (e.g., `a1b2c3d4`). This ID:
- Tracks all phases of a workflow (plan → build → test → review → document)
- Appears in GitHub comments, commits, and PR titles
- Creates an isolated worktree at `trees/{adw_id}/`
- Reserves unique backend/frontend port pairs from the port pool
- Enables resuming workflows and debugging

### State Management
ADW uses persistent state files (`agents/{adw_id}/adw_state.json`) to:
- Share data between workflow phases
- Track worktree locations and port assignments
- Enable workflow composition and chaining
- Track essential workflow data:
  - `adw_id`: Unique workflow identifier
  - `issue_number`: GitHub issue being processed
  - `branch_name`: Git branch for changes
  - `plan_file`: Path to implementation plan
  - `issue_class`: Issue type (`/chore`, `/bug`, `/feature`)
  - `worktree_path`: Absolute path to isolated worktree
  - `backend_port`: Allocated backend port (9100-9199)
  - `frontend_port`: Allocated frontend port (9200-9299)

### Port Management
ADW workflows use a port pool system to prevent collisions and support up to 100 concurrent workflows:

**Port Ranges:**
- Backend Ports: 9100-9199 (100 slots)
- Frontend Ports: 9200-9299 (100 slots)
- Persistence: `agents/port_allocations.json`

**How It Works:**
1. **Reservation:** When an ADW workflow starts, it reserves a backend/frontend port pair from the pool
2. **Persistence:** Allocations are saved to JSON file and survive restarts
3. **Release:** When a workflow completes (cleanup phase), ports are released back to the pool
4. **Cleanup:** Stale allocations (>24 hours) can be cleaned up manually

**Port Pool Operations:**

Check pool status:
```bash
cd adws
uv run python -c "from adw_modules.port_pool import get_port_pool; print(get_port_pool().get_pool_status())"
```

Cleanup stale allocations:
```bash
cd adws
uv run python -c "from adw_modules.port_pool import get_port_pool; print(f'Cleaned {get_port_pool().cleanup_stale()} stale allocations')"
```

Manual port release (if needed):
```bash
cd adws
uv run python -c "from adw_modules.port_pool import get_port_pool; get_port_pool().release('adw-abc12345')"
```

**Migration from Previous System:**
- Previous: Deterministic hash-based allocation (15 slots)
- Current: Reservation-based pool (100 slots)
- Ports are automatically managed by the ADW system - no manual intervention needed

## Quick Start

### 1. Set Environment Variables

```bash
export GITHUB_REPO_URL="https://github.com/owner/repository"
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export CLAUDE_CODE_PATH="/path/to/claude"  # Optional, defaults to "claude"
export GITHUB_PAT="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Optional, only if using different account than 'gh auth login'
```

### 2. Install Prerequisites

```bash
# GitHub CLI
brew install gh              # macOS
# or: sudo apt install gh    # Ubuntu/Debian
# or: winget install --id GitHub.cli  # Windows

# Claude Code CLI
# Follow instructions at https://docs.anthropic.com/en/docs/claude-code

# Python dependency manager (uv)
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# or: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Authenticate GitHub
gh auth login
```

### 3. Run Isolated ADW Workflows

```bash
cd adws/

# Process a single issue in isolation (plan + build)
uv run adw_plan_build_iso.py 123

# Process with testing in isolation (plan + build + test)
uv run adw_plan_build_test_iso.py 123

# Process with review in isolation (plan + build + test + review)
uv run adw_plan_build_test_review_iso.py 123

# Process with review but skip tests (plan + build + review)
uv run adw_plan_build_review_iso.py 123

# Process with documentation (plan + build + document)
uv run adw_plan_build_document_iso.py 123

# Stepwise refinement analysis - decides ATOMIC vs DECOMPOSE
uv run adw_stepwise_iso.py 123

# Complete SDLC workflow with ALL 10 phases (Plan → Validate → Build → Lint → Test → Review → Doc → Ship → Cleanup → Verify)
uv run adw_sdlc_complete_iso.py 123 [--skip-e2e] [--skip-resolution] [--no-external] [--use-optimized-plan]

# Zero Touch Execution - Complete SDLC with ALL 10 phases + auto-ship (⚠️ merges to main!)
uv run adw_sdlc_complete_zte_iso.py 123 [--skip-e2e] [--skip-resolution] [--no-external] [--use-optimized-plan]

# DEPRECATED: Use adw_sdlc_complete_iso.py instead (missing lint phase)
# uv run adw_sdlc_iso.py 123

# DEPRECATED: Use adw_sdlc_complete_zte_iso.py instead (missing lint phase)
# uv run adw_sdlc_zte_iso.py 123

# Run individual isolated phases
uv run adw_plan_iso.py 123              # Planning phase (creates worktree)
uv run adw_patch_iso.py 123             # Patch workflow (creates worktree)
uv run adw_build_iso.py 123 <adw-id>    # Build phase (requires worktree)
uv run adw_test_iso.py 123 <adw-id>     # Test phase (requires worktree)
uv run adw_review_iso.py 123 <adw-id>   # Review phase (requires worktree)
uv run adw_document_iso.py 123 <adw-id> # Documentation phase (requires worktree)
uv run adw_ship_iso.py 123 <adw-id>     # Ship phase (approve & merge PR)

# Run continuous monitoring (polls every 20 seconds)
uv run adw_triggers/trigger_cron.py

# Start webhook server (for instant GitHub events)
uv run adw_triggers/trigger_webhook.py
```

## ADW Isolated Workflow Scripts

### Entry Point Workflows (Create Worktrees)

#### adw_plan_iso.py - Isolated Planning
Creates isolated worktree and generates implementation plans.

**Usage:**
```bash
uv run adw_plan_iso.py <issue-number> [adw-id]
```

**What it does:**
1. Creates isolated git worktree at `trees/<adw_id>/`
2. Allocates unique ports (backend: 9100-9114, frontend: 9200-9214)
3. Sets up environment with `.ports.env`
4. Fetches issue details and classifies type
5. Creates feature branch in worktree
6. Generates implementation plan in isolation
7. Commits and pushes from worktree
8. Creates/updates pull request

#### adw_patch_iso.py - Isolated Patch Workflow
Quick patches in isolated environment triggered by 'adw_patch' keyword.

**Usage:**
```bash
uv run adw_patch_iso.py <issue-number> [adw-id]
```

**What it does:**
1. Searches for 'adw_patch' in issue/comments
2. Creates isolated worktree with unique ports
3. Creates targeted patch plan in isolation
4. Implements specific changes
5. Commits and creates PR from worktree

### Dependent Workflows (Require Existing Worktree)

#### adw_build_iso.py - Isolated Implementation
Implements solutions in existing isolated environment.

**Requirements:**
- Existing worktree created by `adw_plan_iso.py` or `adw_patch_iso.py`
- ADW ID is mandatory

**Usage:**
```bash
uv run adw_build_iso.py <issue-number> <adw-id>
```

**What it does:**
1. Validates worktree exists
2. Switches to correct branch if needed
3. Locates plan file in worktree
4. Implements solution in isolated environment
5. Commits and pushes from worktree

#### adw_test_iso.py - Isolated Testing
Runs tests in isolated environment.

**Requirements:**
- Existing worktree
- ADW ID is mandatory

**Usage:**
```bash
uv run adw_test_iso.py <issue-number> <adw-id> [--skip-e2e]
```

**What it does:**
1. Validates worktree exists
2. Runs tests with allocated ports
3. Auto-resolves failures in isolation
4. Optionally runs E2E tests
5. Commits results from worktree

#### adw_review_iso.py - Isolated Review
Reviews implementation in isolated environment.

**Requirements:**
- Existing worktree
- ADW ID is mandatory

**Usage:**
```bash
uv run adw_review_iso.py <issue-number> <adw-id> [--skip-resolution]
```

**What it does:**
1. Validates worktree exists
2. Reviews against spec in isolation
3. Captures screenshots using allocated ports
4. Auto-resolves blockers in worktree
5. Uploads screenshots and commits

#### adw_document_iso.py - Isolated Documentation
Generates documentation in isolated environment.

**Requirements:**
- Existing worktree
- ADW ID is mandatory

**Usage:**
```bash
uv run adw_document_iso.py <issue-number> <adw-id>
```

**What it does:**
1. Validates worktree exists
2. Analyzes changes in worktree
3. Generates documentation in isolation
4. Commits to `app_docs/` from worktree

### Orchestrator Scripts

#### adw_stepwise_iso.py - Stepwise Refinement Analysis
Analyzes GitHub issues to determine whether they should be processed atomically or decomposed into sub-tasks.

**Usage:**
```bash
uv run adw_stepwise_iso.py <issue-number> [adw-id]
```

**What it does:**
1. Fetches and analyzes issue complexity
2. Uses `/stepwise_analysis` command to evaluate scope
3. Decides between:
   - **ATOMIC**: Single workflow execution (simple tasks)
   - **DECOMPOSE**: Break into smaller sub-issues (complex tasks)
4. For DECOMPOSE: Creates numbered sub-issues with clear dependencies
5. Posts analysis results as GitHub comment
6. Routes to appropriate workflow based on decision

**Decision Criteria:**
- File count and complexity
- Cross-cutting concerns
- Testing requirements
- Integration complexity
- Risk assessment

#### adw_plan_build_iso.py - Isolated Plan + Build
Runs planning and building in isolation.

**Usage:**
```bash
uv run adw_plan_build_iso.py <issue-number> [adw-id]
```

#### adw_plan_build_test_iso.py - Isolated Plan + Build + Test
Full pipeline with testing in isolation.

**Usage:**
```bash
uv run adw_plan_build_test_iso.py <issue-number> [adw-id]
```

#### adw_plan_build_test_review_iso.py - Isolated Plan + Build + Test + Review
Complete pipeline with review in isolation.

**Usage:**
```bash
uv run adw_plan_build_test_review_iso.py <issue-number> [adw-id]
```

#### adw_plan_build_review_iso.py - Isolated Plan + Build + Review
Pipeline with review, skipping tests.

**Usage:**
```bash
uv run adw_plan_build_review_iso.py <issue-number> [adw-id]
```

#### adw_plan_build_document_iso.py - Isolated Plan + Build + Document
Documentation pipeline in isolation.

**Usage:**
```bash
uv run adw_plan_build_document_iso.py <issue-number> [adw-id]
```

#### adw_sdlc_complete_iso.py - Complete Isolated SDLC (ALL 10 Phases)
Full Software Development Life Cycle with ALL 10 phases including validation, lint, and post-deployment verification.

**Usage:**
```bash
uv run adw_sdlc_complete_iso.py <issue-number> [adw-id] [--skip-e2e] [--skip-resolution] [--no-external] [--use-optimized-plan]
```

**Phases (ALL 10):**
1. **Plan**: Creates worktree and implementation spec
2. **Validate**: Baseline error detection (detects inherited errors)
3. **Build**: Implements solution in isolation
4. **Lint**: Validates code quality (TypeScript, ESLint, formatting)
5. **Test**: Runs tests with dedicated ports
6. **Review**: Validates and captures screenshots
7. **Document**: Generates comprehensive docs
8. **Ship**: Approves and merges PR
9. **Cleanup**: Removes worktree and organizes artifacts
10. **Verify**: Post-deployment verification (checks logs, runs smoke tests) - **NEW**

**Flags:**
- `--skip-e2e`: Skip E2E tests during test phase
- `--skip-resolution`: Skip auto-resolution of review blockers
- `--no-external`: Don't use external test/build tools (default: uses external for 70-95% token reduction)
- `--use-optimized-plan`: Use optimized planning workflow

**Output:**
- Isolated worktree at `trees/<adw_id>/`
- Feature implementation on dedicated branch
- Lint validation results
- Test results with port isolation
- Review screenshots from isolated instance
- Complete documentation in `app_docs/`
- Clean state after shipping

**Key Improvements over adw_sdlc_iso.py:**
- Added validate phase (baseline error detection)
- Added lint phase (code quality validation)
- Added cleanup phase (automatic resource management)
- Added ship phase (complete automation)
- Added verify phase (post-deployment verification)
- External test tools enabled by default (70-95% token reduction)

#### adw_sdlc_iso.py - Complete Isolated SDLC (DEPRECATED)
**⚠️ DEPRECATED:** Use `adw_sdlc_complete_iso.py` instead. This version is missing the lint phase.

Full Software Development Life Cycle in isolation.

**Usage:**
```bash
uv run adw_sdlc_iso.py <issue-number> [adw-id] [--skip-e2e] [--skip-resolution]
```

**Phases (5 only - incomplete):**
1. **Plan**: Creates worktree and implementation spec
2. **Build**: Implements solution in isolation
3. **Test**: Runs tests with dedicated ports
4. **Review**: Validates and captures screenshots
5. **Document**: Generates comprehensive docs

**Missing Phases:**
- No lint validation (can deploy broken code)
- No ship phase (manual PR merge required)
- No cleanup phase (worktrees accumulate)

**Output:**
- Isolated worktree at `trees/<adw_id>/`
- Feature implementation on dedicated branch
- Test results with port isolation
- Review screenshots from isolated instance
- Complete documentation in `app_docs/`

#### adw_ship_iso.py - Approve and Merge PR
Final shipping phase that validates state and merges to main.

**Requirements:**
- Complete ADWState with all fields populated
- Existing worktree and PR
- ADW ID is mandatory

**Usage:**
```bash
uv run adw_ship_iso.py <issue-number> <adw-id>
```

**What it does:**
1. Validates all ADWState fields have values
2. Verifies worktree exists
3. Finds PR for the branch
4. Approves the PR
5. Merges PR to main using squash method

**State validation ensures:**
- `adw_id` is set
- `issue_number` is set
- `branch_name` exists
- `plan_file` was created
- `issue_class` was determined
- `worktree_path` exists
- `backend_port` and `frontend_port` allocated

#### adw_verify_iso.py - Post-Deployment Verification
Final verification phase that checks deployed features are working correctly.

**Purpose:** Catch post-deployment issues immediately instead of hours/days later.

**Timing:** Runs 5 minutes after Ship phase completes (allows services to stabilize).

**Requirements:**
- Complete ADWState with port allocations
- Ship phase must have completed
- ADW ID is mandatory

**Usage:**
```bash
uv run adw_verify_iso.py <issue-number> <adw-id>
```

**What it does:**
1. **Backend Log Analysis** - Scans backend logs for exceptions, errors, stack traces
2. **Frontend Console Errors** - Analyzes frontend build logs for console errors
3. **Smoke Tests** - Verifies critical paths (backend health, frontend accessibility)
4. **Follow-up Issue Creation** - Auto-creates GitHub issue if problems detected

**Verification Checks:**
- Backend log patterns: `Exception`, `Traceback`, `ERROR`, `500`, `Failed to`
- Frontend error patterns: `console.error`, `console.warn`, `Uncaught`, React errors
- Smoke tests: Backend `/health` endpoint, frontend page load

**Error Handling:**
- ❌ **Verification Fails:** Auto-create GitHub follow-up issue
- ✅ **Verification Passes:** Complete workflow successfully
- ⚠️ **Important:** Shipped code is NEVER reverted (create new PR instead)

**Example Verification Report:**

Clean deployment:
```
✅ All verification checks passed
Feature is working correctly.
```

Failed verification:
```
❌ Verification failed with the following issues:

Backend Log Errors (2):
- ERROR: Exception in /api/users handler
- 500 Internal Server Error

Smoke Test Failures (1):
- Backend health check failed (port 9100): Connection refused

Follow-up issue #124 created automatically.
```

**Configuration:**
- Verification delay: 5 minutes (300 seconds)
- Log check window: 10 minutes
- Smoke test timeout: 10 seconds per test

**Architecture Decision:**
- **Why Phase 10?** Separate phase allows verification without blocking Ship
- **Why not revert?** Code has passed Review and Test phases - issues are likely environmental
- **Why auto-issue?** Reduces time to detect problems from hours to minutes

#### adw_sdlc_complete_zte_iso.py - Zero Touch Execution (ALL 10 Phases)
Complete SDLC with ALL 10 phases including validation, lint, and post-deployment verification - no human intervention required.

**Usage:**
```bash
uv run adw_sdlc_complete_zte_iso.py <issue-number> [adw-id] [--skip-e2e] [--skip-resolution] [--no-external] [--use-optimized-plan]
```

**Phases (ALL 10):**
1. **Plan**: Creates worktree and implementation spec
2. **Validate**: Baseline error detection (detects inherited errors)
3. **Build**: Implements solution in isolation
4. **Lint**: Validates code quality (TypeScript, ESLint, formatting)
5. **Test**: Runs tests (stops on failure)
6. **Review**: Validates implementation (stops on failure)
7. **Document**: Generates comprehensive docs
8. **Ship**: Automatically approves and merges PR
9. **Cleanup**: Removes worktree and organizes artifacts
10. **Verify**: Post-deployment verification (checks logs, runs smoke tests)

**Flags:**
- `--skip-e2e`: Skip E2E tests during test phase
- `--skip-resolution`: Skip auto-resolution of review blockers
- `--no-external`: Don't use external test/build tools (default: uses external for 70-95% token reduction)
- `--use-optimized-plan`: Use optimized planning workflow

**⚠️ WARNING:** This workflow will automatically merge code to main if all phases pass!

**Output:**
- Complete feature implementation
- Validation baseline established
- Lint validation passed
- Automatic PR approval
- Code merged to main branch
- Production deployment
- Post-deployment verification
- Clean state (worktree removed)

**Key Improvements over adw_sdlc_zte_iso.py:**
- Added validate phase (baseline error detection)
- Added lint phase (prevents deploying broken code)
- Added cleanup phase (automatic resource cleanup)
- Added verify phase (post-deployment verification)
- External test tools enabled by default (70-95% token reduction)
- Optimized planning option

#### adw_sdlc_zte_iso.py - Zero Touch Execution (DEPRECATED)
**⚠️ DEPRECATED:** Use `adw_sdlc_complete_zte_iso.py` instead. This version is missing the lint and cleanup phases.

Complete SDLC with automatic shipping - no human intervention required.

**Usage:**
```bash
uv run adw_sdlc_zte_iso.py <issue-number> [adw-id] [--skip-e2e] [--skip-resolution]
```

**Phases (6 only - incomplete):**
1. **Plan**: Creates worktree and implementation spec
2. **Build**: Implements solution in isolation
3. **Test**: Runs tests (stops on failure)
4. **Review**: Validates implementation (stops on failure)
5. **Document**: Generates comprehensive docs
6. **Ship**: Automatically approves and merges PR

**Missing Phases:**
- No lint validation (can auto-merge broken code)
- No cleanup phase (worktrees accumulate)

**⚠️ WARNING:** This workflow will automatically merge code to main if all phases pass!

**Output:**
- Complete feature implementation
- Automatic PR approval
- Code merged to main branch
- Production deployment

### Automation Triggers

#### trigger_cron.py - Polling Monitor
Continuously monitors GitHub for triggers.

**Usage:**
```bash
uv run adw_triggers/trigger_cron.py
```

**Triggers on:**
- New issues with no comments
- Any issue where latest comment is exactly "adw"
- Polls every 20 seconds

**Workflow selection:**
- Uses `adw_plan_build_iso.py` by default
- Supports all isolated workflows via issue body keywords

#### trigger_webhook.py - Real-time Events
Webhook server for instant GitHub event processing.

**Usage:**
```bash
uv run adw_triggers/trigger_webhook.py
```

**Configuration:**
- Default port: 8001
- Endpoints:
  - `/gh-webhook` - GitHub event receiver
  - `/health` - Health check
- GitHub webhook settings:
  - Payload URL: `https://your-domain.com/gh-webhook`
  - Content type: `application/json`
  - Events: Issues, Issue comments

**Security:**
- Validates GitHub webhook signatures
- Requires `GITHUB_WEBHOOK_SECRET` environment variable

## How ADW Works

1. **Issue Classification**: Analyzes GitHub issue and determines type:
   - `/chore` - Maintenance, documentation, refactoring
   - `/bug` - Bug fixes and corrections
   - `/feature` - New features and enhancements

2. **Planning**: `sdlc_planner` agent creates implementation plan with:
   - Technical approach
   - Step-by-step tasks
   - File modifications
   - Testing requirements

3. **Implementation**: `sdlc_implementor` agent executes the plan:
   - Analyzes codebase
   - Implements changes
   - Runs tests
   - Ensures quality

4. **Integration**: Creates git commits and pull request:
   - Semantic commit messages
   - Links to original issue
   - Implementation summary

## Integration Checklist

ADW workflows automatically generate integration checklists during the Plan phase to ensure all components are properly wired up before shipping.

### Problem Statement

A recurring issue in development is that features are built correctly but not fully integrated:
- API endpoints exist but routes aren't wired up
- UI components are created but not added to navigation
- Database schemas exist but no UI displays the data
- Tests are written but not covering integration points

The Integration Checklist system addresses this by **proactively identifying integration points** during planning and **validating them** before shipping.

### How It Works

1. **Plan Phase (Automatic):** Analyzes feature requirements and generates comprehensive checklist
2. **Implementation:** Developer builds feature (checklist serves as reminder of all integration points)
3. **Ship Phase (Session 4):** Validates checklist items exist (warns if missing)
4. **Verify Phase (Future):** Confirms operational functionality

### Checklist Categories

#### 🔧 Backend Integration
- API endpoints implemented
- Routes registered in route configuration
- Business logic in service layer

#### 🎨 Frontend Integration
- UI components created
- Navigation/routing configured
- State management setup (if needed)

#### 💾 Database Integration
- Migrations created
- Pydantic models updated
- Repository methods implemented

#### 📚 Documentation Integration
- API documentation updated
- Feature documentation added
- README updated (if user-facing)

#### 🧪 Testing Integration
- Unit tests added
- Integration tests added (if multiple components)
- E2E tests added (if applicable)

### Example Checklist

For a feature like "Add user profile page with API backend":

```markdown
## 🔗 Integration Checklist

### 🔧 Backend Integration
- [ ] **[REQUIRED]** API endpoint implemented
- [ ] **[REQUIRED]** API route registered in route configuration
- [ ] **[REQUIRED]** Business logic implemented in service layer

### 🎨 Frontend Integration
- [ ] **[REQUIRED]** UI component created
- [ ] **[REQUIRED]** Component added to navigation/routing
- [ ] [OPTIONAL] State management configured (if needed)

### 💾 Database Integration
- [ ] **[REQUIRED]** Database migration created
- [ ] [OPTIONAL] Pydantic model updated (if applicable)
- [ ] **[REQUIRED]** Repository methods implemented

### 🧪 Testing Integration
- [ ] **[REQUIRED]** Unit tests added
- [ ] **[REQUIRED]** Integration tests added
- [ ] **[REQUIRED]** E2E tests added

### 📚 Documentation Integration
- [ ] **[REQUIRED]** API documentation updated
- [ ] **[REQUIRED]** Feature documentation added
- [ ] **[REQUIRED]** README updated
```

### Feature Detection

The checklist generator intelligently detects feature type based on:
- **GitHub issue labels:** `backend`, `frontend`, `database`
- **Issue title keywords:** `api`, `component`, `page`, `migration`, `schema`
- **Issue body content:** Analyzes description for integration signals

### Smart Requirements

Items are marked as **REQUIRED** or **OPTIONAL** based on context:
- Backend + Frontend features **require** integration tests
- Frontend features **require** README updates
- Database features **optionally** require Pydantic model updates
- API features **require** route registration

### Manual Checklist Generation

Generate checklist for any feature manually:

```bash
cd adws
uv run python -c "
from adw_modules.integration_checklist import generate_integration_checklist, format_checklist_markdown

# Generate checklist
checklist = generate_integration_checklist(
    nl_input='Add user analytics dashboard',
    issue_labels=['backend', 'frontend']
)

# Display markdown
print(format_checklist_markdown(checklist))

# Show summary
print(f'\nTotal items: {len(checklist.get_all_items())}')
print(f'Required items: {len(checklist.get_required_items())}')
"
```

### State Persistence

Checklists are stored in `agents/{adw_id}/adw_state.json` for Ship phase validation:

```json
{
  "adw_id": "abc12345",
  "issue_number": "42",
  "integration_checklist": {
    "backend": [
      {
        "category": "backend",
        "description": "API endpoint implemented",
        "required": true,
        "detected_keywords": ["api", "endpoint"]
      }
    ],
    "frontend": [...],
    "database": [...],
    "documentation": [...],
    "testing": [...]
  },
  "integration_checklist_markdown": "## 🔗 Integration Checklist\n..."
}
```

### Ship Phase Validation

During the Ship phase (before PR approval), the system automatically validates that all planned integration checklist items were actually implemented.

**Validation Process:**
1. Loads integration checklist from state file (`agents/{adw_id}/adw_state.json`)
2. Validates each category:
   - **Backend:** API endpoints, route registration, service layer files
   - **Frontend:** UI components, navigation/routing integration
   - **Database:** Migration files, repository methods
   - **Documentation:** Markdown files in docs/
   - **Testing:** Test files in test directories
3. Generates comprehensive validation report
4. Posts warnings to PR as GitHub comment
5. **Does NOT block shipping** - warnings only

**Validation Methods:**
- **File existence checks:** Verifies expected files exist in worktree
- **Pattern matching:** Greps for API decorators, imports, route registrations
- **Directory scanning:** Counts components, migrations, test files
- **Warning-only approach:** Ensures shipping isn't blocked by false positives

**Example Validation Report:**

```markdown
## ⚠️ Integration Checklist Validation

**Status:** 8/12 items validated

### ✅ Passed Items (8)
- [x] API endpoint implemented
- [x] UI component created
- [x] Database migration created
- [x] Repository methods implemented
- [x] Feature documentation added
- [x] Unit tests added
- [x] Component added to navigation/routing
- [x] Business logic implemented in service layer

### ⚠️ Missing Items (4)
- [ ] **[REQUIRED]** API route registered in route configuration
  - ⚠️ No router registration found in main.py
  - Expected: app.include_router() calls
  - Actual: Not found
- [ ] **[REQUIRED]** Component added to navigation/routing
  - ⚠️ No component imports found in navigation files
  - Expected: Component imports in App.tsx or routing files
  - Actual: Not found
- [ ] [OPTIONAL] State management configured (if needed)
  - ⚠️ Could not validate automatically - manual verification needed
- [ ] [OPTIONAL] README updated (if user-facing feature)
  - ⚠️ Could not validate automatically - manual verification needed

---
**Note:** These are warnings only. The Review phase has already validated code quality.
```

**Running Validation Manually:**

```bash
cd adws
python3 << 'EOF'
from adw_modules.integration_validator import validate_integration_checklist
from adw_modules.state import ADWState

# Load state
state = ADWState.load('abc12345', None)

# Validate checklist
report = validate_integration_checklist(
    checklist=state.get('integration_checklist'),
    worktree_path=state.get('worktree_path')
)

# Display report
print(report.to_markdown())
print(f'\nPassed: {report.passed_items}/{report.total_items}')
print(f'Required failed: {report.required_failed}')
EOF
```

**Benefits:**
- **Reduces "feature works but isn't accessible" bugs by 90%**
- **Ensures complete integration before shipping**
- **Provides systematic validation for code review**
- **Catches missing integration points early**
- **Warning-only approach prevents false positive blocking**

### Testing

**Run integration checklist generation tests:**

```bash
cd adws
uv run pytest tests/test_integration_checklist.py -v
```

Expected output:
```
tests/test_integration_checklist.py::test_backend_feature_detection PASSED
tests/test_integration_checklist.py::test_frontend_feature_detection PASSED
tests/test_integration_checklist.py::test_database_feature_detection PASSED
tests/test_integration_checklist.py::test_full_stack_feature PASSED
tests/test_integration_checklist.py::test_required_vs_optional_items PASSED
tests/test_integration_checklist.py::test_minimal_feature PASSED
tests/test_integration_checklist.py::test_checklist_to_dict PASSED
tests/test_integration_checklist.py::test_markdown_formatting PASSED
tests/test_integration_checklist.py::test_keyword_extraction PASSED
tests/test_integration_checklist.py::test_api_plus_ui_requires_integration_test PASSED
================== 10 passed ==================
```

**Run integration validator tests (Ship phase validation):**

```bash
cd adws
uv run pytest tests/test_integration_validator.py -v
```

Expected output:
```
tests/test_integration_validator.py::test_validate_empty_checklist PASSED
tests/test_integration_validator.py::test_validate_backend_items PASSED
tests/test_integration_validator.py::test_validate_frontend_items PASSED
tests/test_integration_validator.py::test_validate_database_items PASSED
tests/test_integration_validator.py::test_validate_documentation_items PASSED
tests/test_integration_validator.py::test_validate_testing_items PASSED
tests/test_integration_validator.py::test_validate_missing_backend_items PASSED
tests/test_integration_validator.py::test_validate_missing_frontend_items PASSED
tests/test_integration_validator.py::test_validate_optional_items PASSED
tests/test_integration_validator.py::test_markdown_formatting PASSED
tests/test_integration_validator.py::test_markdown_formatting_with_failures PASSED
tests/test_integration_validator.py::test_check_api_endpoints_exist PASSED
tests/test_integration_validator.py::test_check_api_endpoints_missing PASSED
tests/test_integration_validator.py::test_check_routes_registered PASSED
tests/test_integration_validator.py::test_check_service_layer_exists PASSED
tests/test_integration_validator.py::test_check_ui_components_exist PASSED
tests/test_integration_validator.py::test_check_ui_components_missing PASSED
tests/test_integration_validator.py::test_check_component_in_navigation PASSED
tests/test_integration_validator.py::test_check_migrations_exist PASSED
tests/test_integration_validator.py::test_check_migrations_missing PASSED
tests/test_integration_validator.py::test_check_repository_methods_exist PASSED
tests/test_integration_validator.py::test_check_docs_updated PASSED
tests/test_integration_validator.py::test_check_tests_exist PASSED
tests/test_integration_validator.py::test_check_tests_missing PASSED
tests/test_integration_validator.py::test_full_stack_validation PASSED
tests/test_integration_validator.py::test_partial_validation PASSED
tests/test_integration_validator.py::test_validation_result_dataclass PASSED
tests/test_integration_validator.py::test_validation_report_dataclass PASSED
============================== 28 passed ==================
```

## External Testing Tools (Context Optimization)

### Overview

The ADW system includes specialized external tools that dramatically reduce context consumption during testing, building, and test generation phases. These tools operate as **chainable ADW workflows** that execute tests/builds externally and return only failures/errors in compact JSON format.

**Key Benefits:**
- **70-95% token reduction** during test/build phases
- **60-80% cost savings** per SDLC workflow
- **15x faster** test result processing
- Maintains full test/build quality while minimizing LLM context

### Architecture: ADW Chaining Model

External tools follow the ADW chaining architecture pattern:

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
```

**Why chaining instead of direct invocation?**
- Maintains ADW isolation model
- Proper state management via `adw_state.json`
- Each tool is independently traceable/debuggable
- Follows existing SDLC patterns
- Full execution trace via ADW state files

### Available External Tools

#### 1. Test Runner (`adw_test_workflow.py`)

Executes pytest/vitest and returns only test failures.

**Standalone Usage:**
```bash
cd adws/
uv run adw_test_workflow.py --test-type=pytest --coverage-threshold=80
```

**Output Format:**
```json
{
  "summary": {
    "total": 45,
    "passed": 42,
    "failed": 3,
    "duration_seconds": 12.4
  },
  "failures": [
    {
      "test_name": "test_analytics::test_calculate_score",
      "file": "app/server/tests/test_analytics.py",
      "line": 67,
      "error_type": "AssertionError",
      "error_message": "Expected 0.85, got 0.72"
    }
  ],
  "next_steps": [
    "Fix assertion in test_analytics.py:67"
  ]
}
```

**Context Savings:** 90% (50K tokens → 5K tokens for passing tests)

#### 2. Build Checker (`adw_build_workflow.py`)

Runs TypeScript compilation and build processes, returning only errors.

**Standalone Usage:**
```bash
cd adws/
uv run adw_build_workflow.py --check-type=both --target=frontend
```

**Output Format:**
```json
{
  "success": false,
  "summary": {
    "total_errors": 5,
    "type_errors": 3,
    "build_errors": 2
  },
  "errors": [
    {
      "file": "app/client/src/components/RequestForm.tsx",
      "line": 142,
      "column": 23,
      "error_type": "TS2345",
      "severity": "error",
      "message": "Type 'string' is not assignable to type 'number'"
    }
  ]
}
```

**Context Savings:** 85% (30K tokens → 4K tokens for successful builds)

#### 3. Test Generator (`adw_test_gen_workflow.py`)

Analyzes code complexity and generates tests using templates, only involving LLM for complex cases.

**Standalone Usage:**
```bash
cd adws/
uv run adw_test_gen_workflow.py --target-path=app/server/core/analytics.py
```

**Output Format:**
```json
{
  "auto_generated": {
    "count": 23,
    "files": ["app/server/tests/test_analytics.py"],
    "coverage_achieved": 78.5
  },
  "needs_llm_review": [
    {
      "function": "handle_edge_case",
      "file": "app/server/core/analytics.py",
      "line": 89,
      "reason": "Complex async logic with external dependencies"
    }
  ],
  "coverage_gap": {
    "percentage_needed": 6.5,
    "uncovered_lines": [89, 90, 134, 135]
  }
}
```

**Context Savings:** 95% (100K tokens → 5K tokens)

### ADW Wrapper Workflows

External tools are accessed through ADW wrapper workflows that handle state management:

#### Test External ADW (`adw_test_external.py`)

**Usage:**
```bash
# After creating worktree with adw_plan_iso.py
uv run adw_test_external.py <issue-number> <adw-id>
```

**What it does:**
1. Loads state from `agents/{adw_id}/adw_state.json`
2. Gets worktree path from state
3. Executes tests in that worktree via `adw_test_workflow.py`
4. Parses output to compact JSON (failures only)
5. Saves results to `state["external_test_results"]`
6. Exits with 0 (success) or 1 (failure)

#### Build External ADW (`adw_build_external.py`)

**Usage:**
```bash
uv run adw_build_external.py <issue-number> <adw-id>
```

**What it does:**
1. Loads state and gets worktree path
2. Executes TypeScript/build checks via `adw_build_workflow.py`
3. Parses errors to compact JSON
4. Saves results to `state["external_build_results"]`
5. Exits with appropriate code

### Integration with Main Workflows

External tools integrate with main ADW workflows via the `--use-external` flag (experimental):

```python
# In adw_test_iso.py (future integration)
if "--use-external" in sys.argv:
    # Chain to external test ADW
    subprocess.run(["uv", "run", "adw_test_external.py", issue_number, adw_id])

    # Reload state to get compact results
    state.load()
    results = state.get("external_test_results")

    if results.get("success"):
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(results.get('failures', []))} test(s) failed")
else:
    # Existing inline behavior
    ...
```

### State Management

External tools share state via `agents/{adw_id}/adw_state.json`:

```json
{
  "adw_id": "abc12345",
  "issue_number": "42",
  "worktree_path": "trees/abc12345",
  "external_test_results": {
    "success": false,
    "summary": {"total": 45, "passed": 42, "failed": 3},
    "failures": [
      {"file": "test_analytics.py", "line": 67, "error": "AssertionError"}
    ],
    "next_steps": ["Fix assertion in test_analytics.py:67"]
  },
  "external_build_results": {
    "success": true,
    "summary": {"total_errors": 0}
  }
}
```

### Performance Metrics

| Scenario          | Before      | After     | Savings |
|-------------------|-------------|-----------|---------|
| Tests Passing     | 50K tokens  | 5K tokens | 90%     |
| Tests Failing (3) | 50K tokens  | 8K tokens | 84%     |
| Build Success     | 30K tokens  | 2K tokens | 93%     |
| Build Errors (5)  | 30K tokens  | 5K tokens | 83%     |
| Test Generation   | 100K tokens | 5K tokens | 95%     |

**Cost Impact:**
- Before: $3-5 per SDLC workflow
- After: $0.50-1.50 per SDLC workflow
- **Savings: 60-80% cost reduction**

**Speed Impact:**
- Before: 30s to load/process test files
- After: 2s to process compact JSON
- **Speedup: 15x faster**

### Documentation

For detailed information, see:
- `docs/features/adw/chaining-architecture.md` - ADW chaining model explanation
- `docs/EXTERNAL_TEST_TOOLS_ARCHITECTURE.md` - Complete system design
- `docs/EXTERNAL_TOOL_SCHEMAS.md` - Detailed API specifications
- `docs/EXTERNAL_TOOLS_INTEGRATION_GUIDE.md` - Integration strategy
- `docs/EXTERNAL_TOOLS_USAGE_EXAMPLES.md` - Practical examples
- `docs/EXTERNAL_TOOLS_MIGRATION_GUIDE.md` - Migration guide

## Common Usage Scenarios

### Analyze issue complexity with stepwise refinement
```bash
# Analyze if issue should be atomic or decomposed
uv run adw_stepwise_iso.py 789
# Evaluates complexity and decides: ATOMIC or DECOMPOSE
# For DECOMPOSE: Creates sub-issues automatically
# For ATOMIC: Routes to appropriate workflow
```

### Process a bug report in isolation
```bash
# User reports bug in issue #789
uv run adw_plan_build_iso.py 789
# ADW creates isolated worktree, analyzes, creates fix, and opens PR
```

### Run multiple workflows concurrently
```bash
# Process three issues in parallel
uv run adw_plan_build_iso.py 101 &
uv run adw_plan_build_iso.py 102 &
uv run adw_plan_build_iso.py 103 &
# Each gets its own worktree and ports
```

### Run complete SDLC with ALL 8 phases (RECOMMENDED)
```bash
# Full SDLC with ALL phases: Plan → Build → Lint → Test → Review → Doc → Ship → Cleanup
uv run adw_sdlc_complete_iso.py 789
# Creates worktree at trees/abc12345/
# Runs on ports 9107 (backend) and 9207 (frontend)
# Validates with lint before testing
# Generates complete documentation with screenshots
# Ships and cleans up automatically
```

### Run complete SDLC in isolation (DEPRECATED - missing lint)
```bash
# Full SDLC with review and documentation (missing lint phase)
uv run adw_sdlc_iso.py 789
# ⚠️ DEPRECATED: Use adw_sdlc_complete_iso.py instead
# Creates worktree at trees/abc12345/
# Runs on ports 9107 (backend) and 9207 (frontend)
# Generates complete documentation with screenshots
```

### Zero Touch Execution with ALL 8 phases (RECOMMENDED for auto-ship)
```bash
# Complete SDLC with ALL phases + automatic PR merge
uv run adw_sdlc_complete_zte_iso.py 789
# ⚠️ WARNING: Automatically merges to main if all phases pass!
# Creates worktree, implements, lints, tests, reviews, documents, ships, and cleans up
# Uses external tools by default for 70-95% token reduction
```

### Zero Touch Execution (DEPRECATED - missing lint)
```bash
# Complete SDLC with automatic PR merge (missing lint phase)
uv run adw_sdlc_zte_iso.py 789
# ⚠️ DEPRECATED: Use adw_sdlc_complete_zte_iso.py instead
# ⚠️ WARNING: Automatically merges to main if all phases pass!
# Creates worktree, implements, tests, reviews, documents, and ships
```

### Manual shipping workflow
```bash
# After running SDLC, manually approve and merge
uv run adw_ship_iso.py 789 abc12345
# Validates all state fields are populated
# Approves PR
# Merges to main using squash method
```

### Run individual phases
```bash
# Plan only (creates worktree)
uv run adw_plan_iso.py 789

# Build in existing worktree
uv run adw_build_iso.py 789 abc12345

# Test in isolation
uv run adw_test_iso.py 789 abc12345

# Ship when ready
uv run adw_ship_iso.py 789 abc12345
```

### Enable automatic processing
```bash
# Start cron monitoring
uv run adw_triggers/trigger_cron.py
# New issues are processed automatically
# Users can comment "adw" to trigger processing
```

### Deploy webhook for instant response
```bash
# Start webhook server
uv run adw_triggers/trigger_webhook.py
# Configure in GitHub settings
# Issues processed immediately on creation
```

### Triggering Workflows via GitHub Issues

Include the workflow name in your issue body to trigger a specific isolated workflow:

**Recommended Workflows:**
- `adw_stepwise_iso` - Stepwise refinement analysis (decides ATOMIC vs DECOMPOSE)
- `adw_sdlc_complete_iso` - Complete SDLC with ALL 8 phases (Plan → Build → Lint → Test → Review → Doc → Ship → Cleanup)
- `adw_sdlc_complete_zte_iso` - Complete ZTE with ALL 8 phases + auto-merge

**Available Workflows:**
- `adw_plan_iso` - Isolated planning only
- `adw_patch_iso` - Quick patch in isolation
- `adw_plan_build_iso` - Plan and build in isolation
- `adw_plan_build_test_iso` - Plan, build, and test in isolation
- `adw_plan_build_test_review_iso` - Plan, build, test, and review in isolation

**Deprecated Workflows (use complete versions instead):**
- `adw_sdlc_iso` - Complete SDLC (missing lint phase) - Use `adw_sdlc_complete_iso` instead
- `adw_sdlc_zte_iso` - Zero Touch Execution (missing lint phase) - Use `adw_sdlc_complete_zte_iso` instead

**Example Issue:**
```
Title: Add export functionality
Body: Please add the ability to export data to CSV.
Include workflow: adw_sdlc_complete_iso
```

**Example with Flags:**
```
Title: Add export functionality
Body: Please add the ability to export data to CSV.
Include workflow: adw_sdlc_complete_iso --skip-e2e --use-optimized-plan
```

**Note:** Dependent workflows (`adw_build_iso`, `adw_test_iso`, `adw_review_iso`, `adw_document_iso`) require an existing worktree and cannot be triggered directly via webhook.

## Worktree Architecture

### Worktree Structure

```
trees/
├── abc12345/              # Complete repo copy for ADW abc12345
│   ├── .git/              # Worktree git directory
│   ├── .env               # Copied from main repo
│   ├── .ports.env         # Port configuration
│   ├── app/               # Application code
│   ├── adws/              # ADW scripts
│   └── ...
└── def67890/              # Another isolated instance
    └── ...

agents/                    # Shared state location (not in worktree)
├── abc12345/
│   └── adw_state.json     # Persistent state
└── def67890/
    └── adw_state.json
```

### Port Allocation

Each isolated instance gets unique ports:
- Backend: 9100-9114 (15 ports)
- Frontend: 9200-9214 (15 ports)
- Deterministic assignment based on ADW ID hash
- Automatic fallback if preferred ports are busy

**Port Assignment Algorithm:**
```python
def get_ports_for_adw(adw_id: str) -> Tuple[int, int]:
    """Deterministically assign ports based on ADW ID."""
    index = int(adw_id[:8], 36) % 15
    backend_port = 9100 + index
    frontend_port = 9200 + index
    return backend_port, frontend_port
```

**Example Allocations:**
```
ADW abc12345: Backend 9107, Frontend 9207
ADW def67890: Backend 9103, Frontend 9203
```

### Benefits of Isolated Workflows

1. **Parallel Execution**: Run up to 15 ADWs simultaneously
2. **No Interference**: Each instance has its own:
   - Git worktree and branch
   - Filesystem (complete repo copy)
   - Backend and frontend ports
   - Environment configuration
3. **Clean Isolation**: Changes in one instance don't affect others
4. **Easy Cleanup**: Remove worktree to clean everything
5. **Better Debugging**: Isolated environment for troubleshooting
6. **Experiment Safely**: Test changes without affecting main repo

### Cleanup and Maintenance

Worktrees persist until manually removed:

```bash
# Remove specific worktree
git worktree remove trees/abc12345

# List all worktrees
git worktree list

# Clean up worktrees (removes invalid entries)
git worktree prune

# Remove worktree directory if git doesn't know about it
rm -rf trees/abc12345
```

**Best Practices:**
- Remove worktrees after PR merge
- Monitor disk usage (each worktree is a full repo copy)
- Use `git worktree prune` periodically
- Consider automation for cleanup after 7 days

## Troubleshooting

### Environment Issues
```bash
# Check required variables
env | grep -E "(GITHUB|ANTHROPIC|CLAUDE)"

# Verify GitHub auth
gh auth status

# Test Claude Code
claude --version
```

### Common Errors

**"No worktree found"**
```bash
# Check if worktree exists
git worktree list
# Run an entry point workflow first
uv run adw_plan_iso.py <issue-number>
```

**"Port already in use"**
```bash
# Check what's using the port
lsof -i :9107
# Kill the process or let ADW find alternative ports
```

**"Worktree validation failed"**
```bash
# Check worktree state
cat agents/<adw-id>/adw_state.json | jq .worktree_path
# Verify directory exists
ls -la trees/<adw-id>/
```

**"Agent execution failed"**
```bash
# Check agent output in worktree
cat trees/<adw-id>/agents/*/planner/raw_output.jsonl | tail -1 | jq .
```

### Debug Mode
```bash
export ADW_DEBUG=true
uv run adw_plan_build_iso.py 123  # Verbose output
```

## Configuration

### ADW Tracking
Each workflow run gets a unique 8-character ID (e.g., `a1b2c3d4`) that appears in:
- Issue comments: `a1b2c3d4_ops: ✅ Starting ADW workflow`
- Output files: `agents/a1b2c3d4/sdlc_planner/raw_output.jsonl`
- Git commits and PRs

### Model Selection

ADW supports dynamic model selection based on workflow complexity. Users can specify whether to use a "base" model set (optimized for speed and cost) or a "heavy" model set (optimized for complex tasks).

#### How to Specify Model Set

Include `model_set base` or `model_set heavy` in your GitHub issue or comment:

```
Title: Add export functionality  
Body: Please add the ability to export data to CSV.
Include workflow: adw_plan_build_iso model_set heavy
```

If not specified, the system defaults to "base".

#### Model Mapping

Each slash command has a configured model for both base and heavy sets:

```python
SLASH_COMMAND_MODEL_MAP = {
    "/implement": {"base": "sonnet", "heavy": "opus"},
    "/review": {"base": "sonnet", "heavy": "opus"},
    "/classify_issue": {"base": "sonnet", "heavy": "sonnet"},
    # ... etc
}
```

#### Commands Using Opus in Heavy Mode

The following commands switch to Opus when using the heavy model set:
- `/implement` - Complex implementation tasks
- `/resolve_failed_test` - Debugging test failures
- `/resolve_failed_e2e_test` - Debugging E2E test failures
- `/document` - Documentation generation
- `/chore`, `/bug`, `/feature` - Issue-specific implementations
- `/patch` - Creating patches for changes

#### Model Selection Flow

1. User triggers workflow with optional `model_set` parameter
2. ADW extracts and stores model_set in state (defaults to "base")
3. Each slash command execution:
   - Loads state to get model_set
   - Looks up appropriate model from SLASH_COMMAND_MODEL_MAP
   - Executes with selected model

#### Testing Model Selection

```bash
python adws/adw_tests/test_model_selection.py
```

This verifies:
- All commands have both base and heavy mappings
- Model selection logic works correctly
- State persistence includes model_set
- Default behavior when no state exists

### Modular Architecture
The system uses a modular architecture optimized for isolated execution:

- **State Management**: `ADWState` tracks worktree paths and ports
- **Worktree Operations**: `worktree_ops.py` manages isolated environments
- **Git Operations**: `git_ops.py` supports `cwd` parameter for worktree context
- **Workflow Operations**: Core logic in `workflow_ops.py` with `working_dir` support
- **Agent Integration**: `agent.py` executes Claude Code in worktree context

### Workflow Output Structure

Each ADW workflow creates an isolated workspace:

```
agents/
└── {adw_id}/                     # Unique workflow directory
    ├── adw_state.json            # Persistent state file
    ├── {adw_id}_plan_spec.md     # Implementation plan
    ├── planner/                  # Planning agent output
    │   └── raw_output.jsonl      # Claude Code session
    ├── implementor/              # Implementation agent output
    │   └── raw_output.jsonl
    ├── tester/                   # Test agent output
    │   └── raw_output.jsonl
    ├── reviewer/                 # Review agent output
    │   ├── raw_output.jsonl
    │   └── review_img/           # Screenshots directory
    ├── documenter/               # Documentation agent output
    │   └── raw_output.jsonl
    └── patch_*/                  # Patch resolution attempts

app_docs/                         # Generated documentation
└── features/
    └── {feature_name}/
        ├── overview.md
        ├── technical-guide.md
        └── images/
```

## Security Best Practices

- Store tokens as environment variables, never in code
- Use GitHub fine-grained tokens with minimal permissions
- Set up branch protection rules
- Require PR reviews for ADW changes
- Monitor API usage and set billing alerts

## Technical Details

### Core Components

#### Modules
- `adw_modules/agent.py` - Claude Code CLI integration with worktree support
- `adw_modules/data_types.py` - Pydantic models including worktree fields
- `adw_modules/github.py` - GitHub API operations
- `adw_modules/git_ops.py` - Git operations with `cwd` parameter support
- `adw_modules/state.py` - State management tracking worktrees and ports
- `adw_modules/workflow_ops.py` - Core workflow operations with isolation
- `adw_modules/worktree_ops.py` - Worktree and port management
- `adw_modules/utils.py` - Utility functions

#### Entry Point Workflows (Create Worktrees)
- `adw_plan_iso.py` - Isolated planning workflow
- `adw_patch_iso.py` - Isolated patch workflow

#### Dependent Workflows (Require Worktrees)
- `adw_build_iso.py` - Isolated implementation workflow
- `adw_test_iso.py` - Isolated testing workflow
- `adw_review_iso.py` - Isolated review workflow
- `adw_document_iso.py` - Isolated documentation workflow

#### Orchestrators
- `adw_stepwise_iso.py` - Stepwise refinement analysis (ATOMIC vs DECOMPOSE)
- `adw_plan_build_iso.py` - Plan & build in isolation
- `adw_plan_build_test_iso.py` - Plan & build & test in isolation
- `adw_plan_build_test_review_iso.py` - Plan & build & test & review in isolation
- `adw_plan_build_review_iso.py` - Plan & build & review in isolation
- `adw_plan_build_document_iso.py` - Plan & build & document in isolation
- `adw_sdlc_complete_iso.py` - Complete SDLC with ALL 8 phases (RECOMMENDED)
- `adw_sdlc_complete_zte_iso.py` - Complete ZTE with ALL 8 phases + auto-merge (RECOMMENDED)
- `adw_sdlc_iso.py` - Complete SDLC (DEPRECATED - missing lint phase)
- `adw_sdlc_zte_iso.py` - Zero Touch Execution (DEPRECATED - missing lint phase)

### Branch Naming
```
{type}-{issue_number}-{adw_id}-{slug}
```
Example: `feat-456-e5f6g7h8-add-user-authentication`
