# ADW (Autonomous Digital Worker) - Technical Overview

**Last Updated:** 2025-11-14

This document provides a comprehensive technical breakdown of the ADW (Autonomous Digital Worker) system architecture, components, and execution flows.

---

## Table of Contents

1. [Core Concept](#core-concept)
2. [Key Architectural Components](#key-architectural-components)
3. [Workflow Phases](#workflow-phases)
4. [State Management](#state-management)
5. [Agent System](#agent-system)
6. [Complexity Analysis](#complexity-analysis)
7. [Deterministic Execution](#deterministic-execution)
8. [Composable Workflows](#composable-workflows)
9. [GitHub Integration](#github-integration)
10. [Branch Naming Convention](#branch-naming-convention)
11. [Port Allocation System](#port-allocation-system)
12. [Typical Execution Flow](#typical-execution-flow)
13. [Key Design Principles](#key-design-principles)
14. [Cost Breakdown](#cost-breakdown)

---

## Core Concept

An **ADW (Autonomous Digital Worker)** is an AI-powered workflow orchestration system that autonomously executes software development lifecycle (SDLC) tasks. It takes GitHub issues and processes them through isolated, parallel workflows from planning to production deployment.

**Key Capabilities:**
- Autonomous end-to-end software development
- Parallel execution of multiple issues
- Isolated worktree environments
- Cost-optimized AI usage
- Full GitHub integration
- Complete audit trails

---

## Key Architectural Components

### 1. Isolated Worktree Architecture

Each ADW operates in complete isolation using git worktrees:

```
trees/{adw_id}/               # Isolated git worktree
├── .ports.env                # Custom port configuration
├── app/
│   ├── server/ (.env)       # Backend with unique ports
│   └── client/ (.env)       # Frontend with unique ports
├── specs/                    # Implementation plans
└── agents/{adw_id}/         # Persistent state storage
    └── adw_state.json       # Workflow state
```

**Benefits:**
- Multiple ADWs run in parallel without conflicts
- Each has deterministic port allocation (backend: 8000+N, frontend: 5173+N)
- Independent dependencies and environment setup
- Clean separation of concerns
- No interference with main development branch

**Implementation:**
- Location: `adws/adw_modules/worktree_ops.py`
- Created via: `git worktree add trees/{adw_id} {branch_name}`
- Validated before each phase

---

## Workflow Phases

The system is composed of discrete, chainable phases:

### Phase Overview

| Phase | File | Purpose | Cost Range | Key Functions |
|-------|------|---------|-----------|---------------|
| **Plan** | `adw_plan_iso.py` | Classify issue, create worktree, generate implementation plan | Low | Lines 1-413 |
| **Build** | `adw_build_iso.py` | Execute plan, implement changes | Medium | Full implementation |
| **Test** | `adw_test_iso.py` | Run unit/integration tests | Low-Medium | Test execution & retry |
| **Review** | `adw_review_iso.py` | Verify against spec, capture screenshots | Medium | Visual validation |
| **Document** | `adw_document_iso.py` | Generate documentation | Low | Doc generation |
| **Ship** | `adw_ship_iso.py` | Merge PR via GitHub API | Minimal | Lines 1-344 |
| **Patch** | `adw_patch_iso.py` | Quick fixes from review feedback | Low | Incremental fixes |

### Phase Execution Pattern

Each phase follows this pattern:

1. **Load State**
   ```python
   state = ADWState.load(adw_id, logger)
   ```

2. **Validate Prerequisites**
   ```python
   valid, error = validate_worktree(adw_id, state)
   if not valid:
       logger.error(f"Worktree validation failed: {error}")
       sys.exit(1)
   ```

3. **Execute Task**
   - Plan phase: Generate implementation spec
   - Build phase: Implement the code
   - Test phase: Run tests and fix failures
   - etc.

4. **Update State**
   ```python
   state.update(plan_file=plan_file_path)
   state.append_adw_id("adw_plan_iso")
   state.save("adw_plan_iso")
   ```

5. **Post Progress to GitHub**
   ```python
   make_issue_comment(
       issue_number,
       format_issue_message(adw_id, "ops", "✅ Phase completed")
   )
   ```

### Plan Phase Deep Dive (`adw_plan_iso.py`)

**Workflow:**
1. Fetch GitHub issue details
2. Check/create worktree for isolated execution
3. Allocate unique ports for services
4. Setup worktree environment
5. Classify issue type (`/chore`, `/bug`, `/feature`)
6. Create feature branch in worktree
7. Generate implementation plan in worktree
8. Commit plan in worktree
9. Push and create/update PR

**Key Code Sections:**
- Issue classification: Lines 142-158
- Branch generation: Lines 161-177
- Worktree creation: Lines 179-218
- Plan building: Lines 226-250
- Path validation with fallback: Lines 286-349

### Ship Phase Deep Dive (`adw_ship_iso.py`)

**Workflow:**
1. Load state and validate worktree exists
2. Validate ALL state fields are populated (not None)
3. Find PR for the feature branch
4. Merge PR via GitHub API (`gh pr merge --squash`)
5. Post success message to issue

**State Validation:**
```python
def validate_state_completeness(state: ADWState) -> tuple[bool, list[str]]:
    expected_fields = {
        "adw_id", "issue_number", "branch_name", "plan_file",
        "issue_class", "worktree_path", "backend_port", "frontend_port"
    }

    missing_fields = []
    for field in expected_fields:
        if state.get(field) is None:
            missing_fields.append(field)

    return len(missing_fields) == 0, missing_fields
```

This ensures the full SDLC has been executed before shipping.

---

## State Management

**File:** `adw_modules/state.py` (Lines 1-173)

### ADWState Class

Provides persistent, file-based state management:

```python
class ADWState:
    """Container for ADW workflow state with file persistence."""

    STATE_FILENAME = "adw_state.json"

    def __init__(self, adw_id: str):
        self.adw_id = adw_id
        self.data: Dict[str, Any] = {"adw_id": self.adw_id}
```

### State Schema

```python
{
  "adw_id": "abc12345",           # Unique 8-char ID
  "issue_number": "123",
  "branch_name": "feat-issue-123-adw-abc12345-add-feature",
  "plan_file": "specs/issue-123-...-feature.md",
  "issue_class": "/feature",      # /chore, /bug, or /feature
  "worktree_path": "/path/to/trees/abc12345",
  "backend_port": 8001,
  "frontend_port": 5174,
  "model_set": "base",            # or "heavy"
  "all_adws": ["adw_plan_iso", "adw_build_iso", ...]
}
```

### Key Operations

**Save State:**
```python
state.update(branch_name=branch_name, plan_file=plan_file)
state.append_adw_id("adw_plan_iso")  # Track which workflows ran
state.save("adw_plan_iso")  # Save to agents/{adw_id}/adw_state.json
```

**Load State:**
```python
state = ADWState.load(adw_id, logger)
if not state:
    # No existing state found
    sys.exit(1)
```

**Get Working Directory:**
```python
working_dir = state.get_working_directory()
# Returns worktree_path if in isolated workflow, else main repo path
```

### State Flow Benefits

- **Resumability**: Can restart at any phase
- **Auditability**: Track which workflows have run (`all_adws`)
- **Validation**: Ship phase checks all fields populated
- **Context**: Each phase knows where to operate (worktree vs parent)

---

## Agent System

**File:** `adw_modules/agent.py`

Uses **Claude Code CLI** with template-based agents executing slash commands.

### Agent Template Request

```python
AgentTemplateRequest(
    agent_name="issue_classifier",
    slash_command="/classify_issue",
    args=[issue_json],
    adw_id="abc12345",
    working_dir="/path/to/trees/abc12345"  # Executes in worktree
)
```

### Agent Types

Defined in `adw_modules/workflow_ops.py` (Lines 23-28):

| Agent Name | Purpose | Slash Command |
|------------|---------|---------------|
| `sdlc_planner` | Creates implementation plans | `/chore`, `/bug`, `/feature` |
| `sdlc_implementor` | Executes plans | `/implement` |
| `issue_classifier` | Categorizes issues | `/classify_issue` |
| `branch_generator` | Creates standardized branch names | `/generate_branch_name` |
| `pr_creator` | Generates PR descriptions | `/pull_request` |
| `ops` | Environment setup and operations | `/install_worktree` |

### Agent Execution Flow

1. **Build Request:**
   ```python
   request = AgentTemplateRequest(
       agent_name=AGENT_PLANNER,
       slash_command="/feature",
       args=[str(issue.number), adw_id, minimal_issue_json],
       adw_id=adw_id,
       working_dir=worktree_path
   )
   ```

2. **Execute Template:**
   ```python
   response = execute_template(request)
   # Runs: claude --agent {agent_name} --cwd {working_dir} {slash_command} {args}
   ```

3. **Parse Response:**
   ```python
   if not response.success:
       logger.error(f"Error: {response.output}")
       return None, response.output

   result = response.output.strip()
   # Extract file paths, JSON data, etc.
   ```

### Minimal Payload Strategy

To reduce costs, agents receive minimal issue data:

```python
minimal_issue_json = issue.model_dump_json(
    by_alias=True,
    include={"number", "title", "body"}
)
# Excludes comments, labels, assignees, etc.
```

---

## Complexity Analysis

**File:** `adw_modules/complexity_analyzer.py` (Lines 1-174)

### Automatic Routing

Routes issues to appropriate workflows based on heuristic scoring:

```python
def analyze_issue_complexity(issue: GitHubIssue, issue_class: str) -> ComplexityAnalysis:
    text = f"{issue.title} {issue.body}".lower()
    complexity_score = 0
    reasons = []
```

### Scoring System

**Lightweight Indicators** (reduce complexity):
- Simple UI-only changes: -2 points
- Documentation only: -3 points
- Single file scope: -1 point
- Chore classification: -1 point
- Explicitly marked as "simple": -2 points

**Complexity Indicators** (increase complexity):
- Full-stack integration: +3 points
- Database/schema changes: +2 points
- Authentication/security: +2 points
- External integrations: +2 points
- Multiple components (>2): +2 points
- E2E/integration tests: +1 point
- Workflow/automation changes: +2 points
- Refactor/redesign/migration: +2 points
- Explicitly marked as "complex": +2 points

### Routing Decision

```python
if complexity_score <= -2:
    level = "lightweight"
    workflow = "adw_lightweight_iso"
    cost_range = (0.20, 0.50)

elif complexity_score <= 2:
    level = "standard"
    workflow = "adw_sdlc_iso"
    cost_range = (1.00, 2.00)

else:
    level = "complex"
    workflow = "adw_sdlc_zte_iso"
    cost_range = (3.00, 5.00)
```

### Example Analysis Output

```python
ComplexityAnalysis(
    level="lightweight",
    confidence=0.8,
    reasoning="Simple UI change detected | Single file scope | Documentation-only change",
    estimated_cost_range=(0.20, 0.50),
    recommended_workflow="adw_lightweight_iso"
)
```

---

## Deterministic Execution

Hybrid AI + deterministic approach to reduce costs and increase reliability.

### Plan Parser

**File:** `adw_modules/plan_parser.py` (Lines 1-266)

Extracts structured YAML configuration from AI-generated plans:

```python
def parse_plan(plan_text: str) -> WorkflowConfig:
    # Extract YAML block from AI response
    yaml_text = extract_yaml_block(plan_text)
    config_dict = yaml.safe_load(yaml_text)

    return WorkflowConfig(
        issue_type=config_dict['issue_type'],
        branch_name=config_dict['branch_name'],
        worktree_setup=config_dict.get('worktree_setup'),
        # ...
    )
```

### AI-Generated YAML Configuration

```yaml
# WORKFLOW CONFIGURATION

issue_type: feature

project_context: tac-webbuilder
requires_worktree: true
confidence: high
detection_reasoning: "Full-stack feature requiring backend and frontend changes"

branch_name: feat-issue-123-adw-abc12345-add-authentication

worktree_setup:
  backend_port: 8001
  frontend_port: 5174
  steps:
    - action: create_ports_env
    - action: copy_env_files
    - action: install_backend
    - action: install_frontend
    - action: setup_database

commit_message: |
  feat: add user authentication

  ADW: abc12345
  Issue: #123

validation_criteria:
  - check: "Backend API endpoints created"
    expected: "/api/auth/login, /api/auth/logout"
  - check: "Frontend login page exists"
    expected: "src/components/Login.tsx"
```

### Plan Executor

**File:** `adw_modules/plan_executor.py` (Lines 1-546)

Executes plans using pure Python (no AI calls):

```python
def execute_plan(config: WorkflowConfig, issue_number: int,
                 repo_path: str, logger: logging.Logger) -> ExecutionResult:

    result = ExecutionResult()

    # Step 1: Create branch (deterministic)
    success, error = create_branch(config.branch_name, logger)
    if not success:
        result.add_error(f"Branch creation failed: {error}")
        return result

    # Step 2: Create worktree (deterministic)
    if config.requires_worktree:
        worktree_path, error = create_worktree(adw_id, branch_name, repo_path, logger)
        if error:
            result.add_error(f"Worktree creation failed: {error}")
            return result

        # Step 3: Setup worktree (deterministic)
        execute_worktree_setup(worktree_path, config.worktree_setup, logger, result)

    return result
```

### Worktree Setup Steps (Pure Python)

Each action is implemented as a deterministic function:

```python
def execute_worktree_setup(worktree_path: str, setup_config: Dict,
                           logger: logging.Logger, result: ExecutionResult):

    for step in setup_config['steps']:
        action = step['action']

        if action == 'create_ports_env':
            _create_ports_env(worktree_path, backend_port, frontend_port, logger, result)

        elif action == 'copy_env_files':
            _copy_env_files(worktree_path, backend_port, frontend_port, step, logger, result)

        elif action == 'install_backend':
            subprocess.run(['uv', 'sync', '--all-extras'], cwd=f'{worktree_path}/app/server')

        elif action == 'install_frontend':
            subprocess.run(['bun', 'install'], cwd=f'{worktree_path}/app/client')
```

**Benefits:**
- No AI cost for execution
- Deterministic, repeatable results
- Faster execution
- Easier debugging
- AI focuses on creative work (planning, implementation)

---

## Composable Workflows

**File:** `adw_modules/workflow_ops.py` (Lines 31-48)

Mix-and-match phases to create custom workflows:

### Available Workflows

```python
AVAILABLE_ADW_WORKFLOWS = [
    "adw_plan_iso",                    # Just planning
    "adw_build_iso",                   # Build only (needs existing plan)
    "adw_test_iso",                    # Test only
    "adw_review_iso",                  # Review only
    "adw_document_iso",                # Document only
    "adw_ship_iso",                    # Ship only
    "adw_patch_iso",                   # Patch/fix only

    # Composite workflows
    "adw_plan_build_iso",              # Plan + Build
    "adw_plan_build_test_iso",         # Plan + Build + Test
    "adw_plan_build_review_iso",       # Plan + Build + Review
    "adw_plan_build_document_iso",     # Plan + Build + Document
    "adw_plan_build_test_review_iso",  # Plan + Build + Test + Review

    # Complete workflows
    "adw_sdlc_iso",                    # Full: Plan + Build + Test + Review + Document
    "adw_sdlc_ZTE_iso",                # Zero Touch Execution (+ auto-ship)
    "adw_lightweight_iso",             # Optimized: Plan + Build + Ship
]
```

### Lightweight Workflow Example

**File:** `adw_lightweight_iso.py` (Lines 1-171)

Optimized for simple changes (UI tweaks, docs, simple bug fixes):

```python
def main():
    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None
    adw_id = ensure_adw_id(issue_number, adw_id)

    # 1. Plan phase (standard)
    subprocess.run(["uv", "run", "adw_plan_iso.py", issue_number, adw_id])

    # 2. Build phase (standard)
    subprocess.run(["uv", "run", "adw_build_iso.py", issue_number, adw_id])

    # 3. Skip testing, review, documentation (cost optimization)

    # 4. Ship immediately
    subprocess.run(["uv", "run", "adw_ship_iso.py", issue_number, adw_id])
```

**Target Cost:** $0.20-0.50 (vs $3-5 for full SDLC)

### Dependency Management

Each phase validates its prerequisites:

```python
# Build phase requires plan
plan_file = state.get("plan_file")
if not plan_file:
    logger.error("No plan file found in state. Run adw_plan_iso.py first.")
    sys.exit(1)

# Ship phase requires ALL fields
is_valid, missing = validate_state_completeness(state)
if not is_valid:
    logger.error(f"Missing fields: {missing}")
    logger.error("Run the complete SDLC workflow before shipping")
    sys.exit(1)
```

---

## GitHub Integration

**File:** `adw_modules/github.py`

Full GitHub API integration using `gh` CLI:

### Fetch Issues

```python
def fetch_issue(issue_number: str, repo_path: str) -> GitHubIssue:
    result = subprocess.run([
        'gh', 'issue', 'view', issue_number,
        '--repo', repo_path,
        '--json', 'number,title,body,state,author,assignees,labels,comments,createdAt,updatedAt,closedAt,url'
    ], capture_output=True, text=True)

    data = json.loads(result.stdout)
    return GitHubIssue(**data)
```

### Post Comments

```python
def make_issue_comment(issue_number: str, message: str):
    subprocess.run([
        'gh', 'issue', 'comment', issue_number,
        '--body', message
    ])

# Usage with ADW tracking
make_issue_comment(
    issue_number,
    format_issue_message(adw_id, "ops", "✅ Planning phase completed")
)
# Posts: "🤖_ADW_BOT abc12345_ops: ✅ Planning phase completed"
```

### Create Pull Requests

```python
def create_pull_request(...) -> str:
    # Agent generates PR title and body
    response = execute_template(AgentTemplateRequest(
        agent_name="pr_creator",
        slash_command="/pull_request",
        args=[branch_name, issue_json, plan_file, adw_id]
    ))

    # Returns PR URL
    return response.output.strip()
```

### Merge Pull Requests

```python
def merge_pr_via_github(pr_number: str, repo_path: str) -> Tuple[bool, Optional[str]]:
    result = subprocess.run([
        'gh', 'pr', 'merge', pr_number,
        '--repo', repo_path,
        '--squash',
        '--delete-branch'
    ], capture_output=True, text=True)

    return result.returncode == 0, result.stderr if result.returncode != 0 else None
```

### Bot Identifier

Prevents webhook loops:

```python
ADW_BOT_IDENTIFIER = "🤖_ADW_BOT"

def format_issue_message(adw_id: str, agent_name: str, message: str) -> str:
    return f"{ADW_BOT_IDENTIFIER} {adw_id}_{agent_name}: {message}"
```

Webhook filters out comments containing `ADW_BOT_IDENTIFIER`.

---

## Branch Naming Convention

Standardized format for traceability and automation:

### Format

```
{type}-issue-{number}-adw-{id}-{slug}
```

### Components

- **type**: `feat`, `fix`, or `chore` (derived from issue classification)
- **issue**: Issue number from GitHub
- **adw**: Unique ADW ID (8 characters, generated via hash)
- **slug**: Human-readable description (kebab-case)

### Examples

```
feat-issue-123-adw-abc12345-add-user-authentication
fix-issue-456-adw-def67890-resolve-login-bug
chore-issue-789-adw-ghi01234-update-documentation
```

### Benefits

1. **Traceability**: Easily link branch to issue and ADW instance
2. **Uniqueness**: ADW ID prevents conflicts across parallel workflows
3. **Automation**: Pattern matching for finding PRs, cleaning up worktrees
4. **Clarity**: Type and slug provide context at a glance

### Generation

**File:** `adw_modules/workflow_ops.py` (Lines 233-263)

```python
def generate_branch_name(issue: GitHubIssue, issue_class: str,
                         adw_id: str) -> Tuple[Optional[str], Optional[str]]:

    issue_type = issue_class.replace("/", "")  # Remove slash

    # Agent generates slug from issue title
    request = AgentTemplateRequest(
        agent_name="branch_generator",
        slash_command="/generate_branch_name",
        args=[issue_type, adw_id, minimal_issue_json],
        adw_id=adw_id
    )

    response = execute_template(request)
    # Returns: "feat-issue-123-adw-abc12345-add-authentication"

    return response.output.strip(), None
```

### Pattern Matching

Finding existing branches:

```python
def find_existing_branch_for_issue(issue_number: str, adw_id: Optional[str] = None):
    result = subprocess.run(['git', 'branch', '-a'], capture_output=True, text=True)
    branches = result.stdout.strip().split('\n')

    for branch in branches:
        branch = branch.strip().replace('* ', '').replace('remotes/origin/', '')

        # Check for standardized pattern
        if f"-issue-{issue_number}-" in branch:
            if adw_id and f"-adw-{adw_id}-" in branch:
                return branch
            elif not adw_id:
                return branch  # Return first match

    return None
```

---

## Port Allocation System

**File:** `adw_modules/worktree_ops.py`

Deterministic port allocation with fallback to prevent conflicts.

### Deterministic Allocation

```python
def get_ports_for_adw(adw_id: str) -> tuple[int, int]:
    """
    Generate deterministic port numbers from ADW ID hash.

    Backend: 8000 + offset
    Frontend: 5173 + offset
    """
    import hashlib

    # Hash ADW ID to get consistent offset
    hash_val = int(hashlib.sha256(adw_id.encode()).hexdigest()[:8], 16)
    offset = hash_val % 1000  # Keep ports in reasonable range

    backend_port = 8000 + offset
    frontend_port = 5173 + offset

    return backend_port, frontend_port
```

### Port Availability Check

```python
def is_port_available(port: int) -> bool:
    """Check if a port is available for use."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', port))
            return True
        except OSError:
            return False  # Port in use
```

### Fallback Mechanism

```python
def find_next_available_ports(adw_id: str) -> tuple[int, int]:
    """
    Find next available ports if deterministic ones are taken.
    Scans upward from base ports.
    """
    backend_base = 8000
    frontend_base = 5173

    for offset in range(1, 1000):
        backend = backend_base + offset
        frontend = frontend_base + offset

        if is_port_available(backend) and is_port_available(frontend):
            logger.info(f"Found available ports: {backend}/{frontend}")
            return backend, frontend

    raise RuntimeError("No available ports found in range")
```

### Port Configuration Files

Created in each worktree:

```python
def setup_worktree_environment(worktree_path: str, backend_port: int,
                               frontend_port: int):
    # Create .ports.env
    ports_env = f"""BACKEND_PORT={backend_port}
FRONTEND_PORT={frontend_port}
VITE_BACKEND_URL=http://localhost:{backend_port}
"""

    with open(f"{worktree_path}/.ports.env", 'w') as f:
        f.write(ports_env)

    # Append to .env files
    # Root .env
    with open(f"{worktree_path}/.env", 'a') as f:
        f.write(f"\n{ports_env}")

    # Server .env
    with open(f"{worktree_path}/app/server/.env", 'a') as f:
        f.write(f"\n{ports_env}")
```

### Benefits

1. **Deterministic**: Same ADW ID always gets same ports (when available)
2. **Collision Avoidance**: Hash-based distribution reduces collisions
3. **Automatic Fallback**: Finds alternatives if deterministic ports taken
4. **Per-Worktree**: Each worktree has unique ports
5. **Environment Isolation**: Ports stored in worktree-specific .env files

---

## Typical Execution Flow

### Example: Feature Request (#123)

Let's trace a complete workflow from GitHub issue to production deployment.

#### 1. Trigger

**Input:** GitHub issue #123 created with title "Add user dashboard"

**Webhook:** (Optional) Webhook detects issue, extracts ADW command from body/comments

```python
# If issue body contains: "/adw_sdlc_iso"
adw_info = extract_adw_info(issue.body, temp_adw_id)
# Returns: ADWExtractionResult(workflow_command="adw_sdlc_iso", adw_id=None)
```

#### 2. Classification & Initialization

```bash
$ uv run adw_sdlc_iso.py 123
```

**Internally runs:**
```python
# Generate ADW ID
adw_id = ensure_adw_id("123")  # Returns: "abc12345"

# Initialize state
state = ADWState(adw_id)
state.update(adw_id="abc12345", issue_number="123")
state.save("initialization")
```

#### 3. Plan Phase (`adw_plan_iso.py`)

**Step 1:** Fetch issue details
```python
issue = fetch_issue("123", "owner/repo")
# GitHubIssue(number=123, title="Add user dashboard", body="...", ...)
```

**Step 2:** Classify issue
```python
issue_command, _ = classify_issue(issue, "abc12345", logger)
# Returns: "/feature"

state.update(issue_class="/feature")
```

**Step 3:** Generate branch name
```python
branch_name, _ = generate_branch_name(issue, "/feature", "abc12345", logger)
# Returns: "feat-issue-123-adw-abc12345-add-user-dashboard"

state.update(branch_name=branch_name)
```

**Step 4:** Allocate ports
```python
backend_port, frontend_port = get_ports_for_adw("abc12345")
# Returns: (8234, 5407)  # Hash-based deterministic ports

state.update(backend_port=8234, frontend_port=5407)
```

**Step 5:** Create worktree
```bash
$ git worktree add trees/abc12345 feat-issue-123-adw-abc12345-add-user-dashboard
```

```python
worktree_path = "trees/abc12345"
state.update(worktree_path=worktree_path)

setup_worktree_environment(worktree_path, 8234, 5407)
# Creates .ports.env, updates .env files
```

**Step 6:** Generate implementation plan
```python
plan_response = build_plan(issue, "/feature", "abc12345", logger,
                           working_dir=worktree_path)

# Agent creates: specs/issue-123-adw-abc12345-sdlc_planner-add-user-dashboard.md
plan_file = "specs/issue-123-adw-abc12345-sdlc_planner-add-user-dashboard.md"
state.update(plan_file=plan_file)
```

**Step 7:** Commit plan
```python
commit_msg, _ = create_commit("sdlc_planner", issue, "/feature",
                              "abc12345", logger, worktree_path)

commit_changes(commit_msg, cwd=worktree_path)
# Commits in worktree, not parent repo
```

**Step 8:** Create PR
```python
finalize_git_operations(state, logger, cwd=worktree_path)
# Pushes branch, creates PR, links to issue
```

**GitHub Comment:**
```
🤖_ADW_BOT abc12345_ops: ✅ Isolated planning phase completed
📍 Worktree: trees/abc12345
🔌 Ports - Backend: 8234, Frontend: 5407
```

#### 4. Build Phase (`adw_build_iso.py`)

```bash
$ uv run adw_build_iso.py 123 abc12345
```

**Step 1:** Load state and validate
```python
state = ADWState.load("abc12345", logger)
worktree_path = state.get("worktree_path")  # trees/abc12345
plan_file = state.get("plan_file")          # specs/issue-123-...md

valid, error = validate_worktree("abc12345", state)
```

**Step 2:** Implement plan
```python
implement_response = implement_plan(
    plan_file, "abc12345", logger,
    agent_name="sdlc_implementor",
    working_dir=worktree_path
)

# Agent reads plan, implements code changes in worktree
# Creates/modifies files:
#   - app/client/src/components/Dashboard.tsx
#   - app/server/routes/dashboard.py
#   - etc.
```

**Step 3:** Commit implementation
```python
commit_msg, _ = create_commit("sdlc_implementor", issue, "/feature",
                              "abc12345", logger, worktree_path)
commit_changes(commit_msg, cwd=worktree_path)
```

**GitHub Comment:**
```
🤖_ADW_BOT abc12345_sdlc_implementor: ✅ Implementation completed
📝 Changes committed to worktree
```

#### 5. Test Phase (`adw_test_iso.py`)

```bash
$ uv run adw_test_iso.py 123 abc12345
```

**Step 1:** Run tests in worktree
```python
# Run backend tests
subprocess.run(['pytest', 'app/server/tests'], cwd=worktree_path)

# Run frontend tests
subprocess.run(['npm', 'test'], cwd=f'{worktree_path}/app/client')
```

**Step 2:** Parse results
```python
test_results = parse_test_output(test_output)
failed_tests = [t for t in test_results if not t.passed]
```

**Step 3:** Auto-fix failures (if any)
```python
for failed_test in failed_tests:
    fix_response = execute_template(AgentTemplateRequest(
        agent_name="test_fixer",
        slash_command="/resolve_failed_test",
        args=[failed_test.error, spec_file],
        working_dir=worktree_path
    ))

    # Re-run test
    retry_result = run_test(failed_test.test_name, cwd=worktree_path)
```

**GitHub Comment:**
```
🤖_ADW_BOT abc12345_tester: ✅ All tests passing
✓ 15 backend tests passed
✓ 23 frontend tests passed
```

#### 6. Review Phase (`adw_review_iso.py`)

```bash
$ uv run adw_review_iso.py 123 abc12345
```

**Step 1:** Start services in worktree
```python
# Start backend on port 8234
backend_proc = subprocess.Popen(
    ['uv', 'run', 'python', '-m', 'app.server.main'],
    cwd=worktree_path
)

# Start frontend on port 5407
frontend_proc = subprocess.Popen(
    ['npm', 'run', 'dev'],
    cwd=f'{worktree_path}/app/client'
)
```

**Step 2:** Review implementation against spec
```python
review_response = execute_template(AgentTemplateRequest(
    agent_name="reviewer",
    slash_command="/review",
    args=[spec_file, "http://localhost:5407"],
    working_dir=worktree_path
))

# Agent:
# 1. Reads spec
# 2. Opens browser to localhost:5407
# 3. Captures screenshots
# 4. Compares implementation vs spec
# 5. Returns ReviewResult
```

**Step 3:** Handle review issues (if any)
```python
review_result = ReviewResult(**parse_json(review_response.output))

if review_result.review_issues:
    for issue in review_result.review_issues:
        if issue.issue_severity == "blocker":
            # Create and apply patch
            patch_file, implement_response = create_and_implement_patch(
                "abc12345",
                issue.issue_resolution,
                logger,
                working_dir=worktree_path
            )
```

**GitHub Comment:**
```
🤖_ADW_BOT abc12345_reviewer: ✅ Review completed
📸 Screenshots captured and uploaded
✓ Implementation matches specification
```

#### 7. Document Phase (`adw_document_iso.py`)

```bash
$ uv run adw_document_iso.py 123 abc12345
```

**Step 1:** Generate documentation
```python
doc_response = execute_template(AgentTemplateRequest(
    agent_name="documenter",
    slash_command="/document",
    args=[spec_file],
    working_dir=worktree_path
))

# Creates:
#   - docs/features/user-dashboard.md
#   - README updates
#   - API documentation
```

**Step 2:** Commit documentation
```python
commit_changes("docs: add user dashboard documentation", cwd=worktree_path)
```

#### 8. Ship Phase (`adw_ship_iso.py`)

```bash
$ uv run adw_ship_iso.py 123 abc12345
```

**Step 1:** Validate completeness
```python
is_valid, missing = validate_state_completeness(state)
if not is_valid:
    logger.error(f"Missing fields: {missing}")
    logger.error("Run complete SDLC workflow before shipping")
    sys.exit(1)
```

**Step 2:** Find PR
```python
branch_name = state.get("branch_name")
pr_number = find_pr_for_branch(branch_name, "owner/repo", logger)
# Returns: "456"
```

**Step 3:** Merge PR
```python
success, error = merge_pr_via_github("456", "owner/repo", logger)

# Runs: gh pr merge 456 --squash --delete-branch
# GitHub automatically:
#   - Closes issue #123
#   - Deletes remote branch
#   - Updates PR status
```

**GitHub Comment:**
```
🤖_ADW_BOT abc12345_shipper: 🎉 Successfully shipped!

✅ Validated all state fields
✅ Found and merged PR via GitHub API
✅ Branch `feat-issue-123-adw-abc12345-add-user-dashboard` merged to main

🚢 Code has been deployed to production!
```

#### 9. Cleanup (Manual)

```bash
$ ./scripts/purge_tree.sh abc12345
# Removes trees/abc12345 worktree
```

---

## Key Design Principles

### 1. Isolation

**Principle:** Each ADW operates in complete isolation from others.

**Implementation:**
- Git worktrees: `trees/{adw_id}/`
- Unique ports per ADW
- Separate state files: `agents/{adw_id}/adw_state.json`
- Independent dependencies

**Benefits:**
- Parallel execution without conflicts
- Clean rollback (delete worktree)
- No contamination of main branch
- Safe experimentation

### 2. Composability

**Principle:** Workflows are built from reusable, independent phases.

**Implementation:**
- Each phase is a standalone script
- State passing via ADWState
- Mix-and-match workflows
- Dependency validation

**Benefits:**
- Flexibility (run any subset of phases)
- Cost optimization (skip unnecessary phases)
- Easy testing (test phases independently)
- Incremental rollout

### 3. Determinism

**Principle:** Minimize AI usage, maximize deterministic execution.

**Implementation:**
- AI for creative work (planning, code generation)
- Python for execution (worktree setup, git operations)
- Structured output (YAML configs, JSON responses)
- Validation at every step

**Benefits:**
- Lower costs (less AI usage)
- Faster execution
- More reliable
- Easier debugging

### 4. Cost Optimization

**Principle:** Route work to appropriate workflows based on complexity.

**Implementation:**
- Complexity analysis algorithm
- Lightweight workflow for simple changes ($0.20-0.50)
- Standard SDLC for moderate complexity ($1.00-2.00)
- Full ZTE for complex features ($3.00-5.00)
- Minimal payloads to agents

**Benefits:**
- Avoid overspending on simple tasks
- Appropriate thoroughness for each task
- Predictable costs

### 5. Auditability

**Principle:** Full visibility into what ADWs are doing.

**Implementation:**
- State tracking (`all_adws` field)
- GitHub comments at each phase
- Session IDs from Claude Code
- Persistent state files
- Git commit history

**Benefits:**
- Debugging workflow issues
- Cost analysis
- Performance monitoring
- Accountability

### 6. Resumability

**Principle:** Any phase can restart from saved state.

**Implementation:**
- ADWState persisted to disk
- Each phase loads state at start
- Validates prerequisites before execution
- Idempotent operations where possible

**Benefits:**
- Recover from failures
- Run phases incrementally
- Skip completed work
- Manual intervention when needed

### 7. Validation

**Principle:** Catch errors early with strong typing and validation.

**Implementation:**
- Pydantic models for all data structures
- State completeness validation (ship phase)
- Worktree validation before each phase
- Response parsing with error handling

**Benefits:**
- Fail fast
- Clear error messages
- Type safety
- Contract enforcement

### 8. GitHub Integration

**Principle:** Seamless integration with existing GitHub workflows.

**Implementation:**
- Issue-driven workflow
- PR creation and merging
- Comment-based progress updates
- Bot identifier to prevent loops

**Benefits:**
- Familiar interface for developers
- Central source of truth (GitHub)
- Notification system built-in
- Works with existing tools

---

## Cost Breakdown

### Workflow Cost Comparison

| Workflow | Phases | Estimated Cost | Avg. Duration | Use Case |
|----------|--------|----------------|---------------|----------|
| **Lightweight** | Plan + Build + Ship | $0.20 - $0.50 | 5-10 min | UI tweaks, docs, simple fixes |
| **Standard SDLC** | Plan + Build + Test + Review + Doc | $1.00 - $2.00 | 15-30 min | Most features and bug fixes |
| **Complex ZTE** | Full SDLC + auto-ship | $3.00 - $5.00 | 30-60 min | Critical features, large refactors |
| **Plan Only** | Plan | $0.10 - $0.20 | 2-5 min | Planning without implementation |
| **Build Only** | Build | $0.30 - $0.80 | 5-15 min | Implement existing plan |
| **Ship Only** | Ship | $0.01 - $0.05 | 1-2 min | Merge approved PR |

### Cost Factors

**Primary Cost Drivers:**
1. **Number of AI agent calls**
   - Planning: 1-2 calls
   - Implementation: 1-3 calls
   - Testing: 0-5 calls (depends on failures)
   - Review: 1-2 calls
   - Documentation: 1 call

2. **Model selection**
   - Base model set: Sonnet for most tasks
   - Heavy model set: Opus for complex reasoning

3. **Retry loops**
   - Test failures: Up to 3 retries per failed test
   - Review issues: Patch creation + re-implementation

4. **Context size**
   - Minimal payloads reduce cost
   - Large codebases = more expensive context

**Cost Optimization Strategies:**

1. **Complexity-based routing**
   - Don't use full SDLC for simple changes
   - Lightweight workflow saves 80-90%

2. **Minimal payloads**
   ```python
   # Only send what's needed
   minimal_issue_json = issue.model_dump_json(
       include={"number", "title", "body"}
   )
   # Excludes comments, labels, timestamps, etc.
   ```

3. **Deterministic execution**
   - Use Python instead of AI for setup, git operations
   - AI only for creative work

4. **Skip unnecessary phases**
   - Documentation may not be needed for every change
   - Review can be skipped for low-risk changes

5. **Model selection**
   - Use Sonnet (cheaper) by default
   - Reserve Opus for complex reasoning tasks

### ROI Calculation

**Traditional Development:**
- Developer time: 2-4 hours
- Cost: $100-$400 (at $50/hr)

**ADW Development:**
- Lightweight: $0.20-0.50 (99% savings)
- Standard: $1.00-2.00 (98% savings)
- Complex: $3.00-5.00 (97% savings)

**Assumptions:**
- ADWs handle routine tasks
- Human review for critical features
- Quality maintained through automated testing

---

## Summary

The ADW (Autonomous Digital Worker) system is a sophisticated, production-ready workflow orchestration platform that:

1. **Autonomously** executes full SDLC from GitHub issue to production
2. **Isolates** each workflow in git worktrees with unique ports
3. **Optimizes** costs through complexity-based routing and deterministic execution
4. **Composes** workflows from reusable, independent phases
5. **Integrates** seamlessly with GitHub for issue tracking and PR management
6. **Validates** at every step with strong typing and state management
7. **Audits** all actions through state files and GitHub comments
8. **Resumes** from any point via persistent state

**Key Innovation:** Hybrid AI + deterministic execution model that uses AI for creative work (planning, implementation) and Python for mechanical work (git operations, environment setup), achieving 80-90% cost reduction compared to pure AI approaches.

**Production Readiness:**
- Battle-tested on real projects
- Handles edge cases (port conflicts, file path issues)
- Comprehensive error handling
- Rollback mechanisms
- Parallel execution support

---

## References

### Key Files

- **Workflows:** `adws/adw_*_iso.py`
- **State Management:** `adws/adw_modules/state.py`
- **Agent System:** `adws/adw_modules/agent.py`
- **Complexity Analysis:** `adws/adw_modules/complexity_analyzer.py`
- **Plan Parser:** `adws/adw_modules/plan_parser.py`
- **Plan Executor:** `adws/adw_modules/plan_executor.py`
- **Workflow Operations:** `adws/adw_modules/workflow_ops.py`
- **GitHub Integration:** `adws/adw_modules/github.py`
- **Worktree Operations:** `adws/adw_modules/worktree_ops.py`

### External Documentation

- [Git Worktrees](https://git-scm.com/docs/git-worktree)
- [GitHub CLI](https://cli.github.com/)
- [Claude Code](https://docs.anthropic.com/claude-code)
- [Pydantic](https://docs.pydantic.dev/)

---

**Document Version:** 1.0
**Date:** 2025-11-14
**Author:** ADW System Analysis
