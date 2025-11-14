# Plan Complete Workflow

Create a COMPREHENSIVE workflow plan that includes ALL decisions and setup steps needed for this ADW. This is the ONLY AI call with full context - make all decisions upfront.

## Variables
issue_number: $1
adw_id: $2
issue_json: $3

## Instructions

This is a **comprehensive planning phase** where you make ALL decisions that would normally require separate AI calls:

1. **Classify the issue** (feature/bug/chore)
2. **Detect project context** (tac-7-root vs tac-webbuilder)
3. **Generate branch name**
4. **Plan worktree setup** (if needed)
5. **Create implementation plan**
6. **Define validation criteria**

After this planning phase, execution will be **deterministic Python** with **zero AI calls**.

## Output Format

Generate your plan in TWO parts:

### Part 1: Workflow Configuration (YAML)

At the START of your response, output a YAML block with workflow decisions:

```yaml
# ============================================
# WORKFLOW CONFIGURATION
# ============================================

# Issue Classification
issue_type: feature  # feature, bug, or chore

# Project Detection
project_context: tac-7-root  # tac-7-root or tac-webbuilder
requires_worktree: false
confidence: high  # high, medium, low
detection_reasoning: "Issue mentions scripts/ directory and bash automation"

# Branch Naming
branch_name: feat-issue-{issue_number}-adw-{adw_id}-add-authentication-system

# Worktree Setup (only if requires_worktree: true)
worktree_setup:
  backend_port: 8001  # Use get_ports_for_adw() logic: base 8000 + (hash(adw_id) % 1000)
  frontend_port: 5174  # Use base 5173 + (hash(adw_id) % 1000)
  steps:
    - action: create_ports_env
      description: "Create .ports.env with BACKEND_PORT and FRONTEND_PORT"
    - action: copy_env_files
      description: "Copy .env and app/server/.env from parent repo"
      fallback: "Use .env.sample if .env doesn't exist"
    - action: copy_mcp_files
      description: "Copy .mcp.json and playwright-mcp-config.json"
      path_updates:
        - file: .mcp.json
          update: "Replace ./playwright-mcp-config.json with absolute path"
        - file: playwright-mcp-config.json
          update: "Replace ./videos with absolute path, create videos/ dir"
    - action: install_backend
      command: "cd app/server && uv sync --all-extras"
      working_dir: app/server
    - action: install_frontend
      command: "cd app/client && bun install"
      working_dir: app/client
    - action: setup_database
      command: "./scripts/reset_db.sh"
      working_dir: "."

# Commit Message
commit_message: |
  {issue_type}: {brief_description}

  ADW: {adw_id}
  Issue: #{issue_number}

# Validation Criteria
validation_criteria:
  - check: "Branch created with correct name"
    expected: "{branch_name}"
  - check: "Plan file exists"
    expected: "specs/issue-{issue_number}-adw-{adw_id}-sdlc_planner-*.md"
  - check: "Worktree created (if required)"
    expected: "trees/{adw_id}/ exists or N/A"
  - check: "Dependencies installed (if worktree)"
    expected: "node_modules and .venv exist in worktree or N/A"
```

### Part 2: Implementation Plan (Markdown)

After the YAML block, create the implementation plan using the existing format based on issue type:

**For features**: Use the format from `.claude/commands/feature.md`
**For bugs**: Use the format from `.claude/commands/bug.md`
**For chores**: Use the format from `.claude/commands/chore.md`

## Decision Making Guidelines

### 1. Issue Classification

Analyze the issue title and body:
- **Feature**: "add", "implement", "create", "build", "new"
- **Bug**: "fix", "broken", "error", "bug", "issue", "not working"
- **Chore**: "update", "refactor", "cleanup", "improve", "reorganize"

### 2. Project Context Detection

Use these signals (in order of confidence):

**HIGH confidence indicators:**
- Explicit marker: `**Project**: tac-7 (NOT tac-webbuilder)` → tac-7-root
- Explicit marker: `**Project**: tac-webbuilder` → tac-webbuilder
- Working directory: `/Users/.../tac-7/projects/tac-webbuilder` → tac-webbuilder
- Working directory: `/Users/.../tac-7` (not in projects/) → tac-7-root

**MEDIUM confidence indicators:**
- File paths mentioned:
  - `app/server/`, `app/client/`, `interfaces/` → tac-webbuilder
  - `scripts/`, `adws/`, `.github/`, `agents/` → tac-7-root
- Technology stack:
  - "FastAPI", "React", "Vite", "database", "API" → tac-webbuilder
  - "workflow", "automation", "bash", "ADW", "worktree" → tac-7-root

**DEFAULT**: If uncertain, choose `tac-7-root` (safer, less overhead)

### 3. Branch Naming

Format: `{type}-issue-{num}-adw-{id}-{slug}`

- `{type}`: feat, fix, or chore
- `{num}`: issue number
- `{id}`: adw_id (8 chars)
- `{slug}`: 3-6 words from title, lowercase, hyphens only

Example: `feat-issue-123-adw-abc12345-add-user-authentication`

### 4. Worktree Decision

**Require worktree if:**
- project_context is `tac-webbuilder`
- Issue explicitly requests isolated environment

**Skip worktree if:**
- project_context is `tac-7-root`
- Simple script/tool development
- No dependencies to install

### 5. Port Allocation (if worktree needed)

Use deterministic port assignment to avoid conflicts:
```python
# Backend: 8000 + (hash(adw_id) % 1000)
# Frontend: 5173 + (hash(adw_id) % 1000)
```

For this plan, calculate ports based on adw_id hash.

## Relevant Files

Focus on these files based on project context:

**For tac-webbuilder tasks:**
- `README.md` - Project overview
- `app/server/**` - Backend server
- `app/client/**` - Frontend client
- `interfaces/` - CLI and Web interfaces
- `.claude/commands/conditional_docs.md` - Additional docs

**For tac-7-root tasks:**
- `README.md` - Project overview (minimal)
- `scripts/` - Bash scripts
- `adws/` - ADW workflows
- `.github/` - GitHub workflows
- Specific directories mentioned in issue

## Important Notes

- **Be thorough**: This is your ONLY chance to load context and make decisions
- **Be explicit**: Execution phase has NO AI - every step must be clear
- **YAML first**: Always output YAML configuration block before markdown plan
- **Valid YAML**: Ensure proper indentation and syntax
- **Deterministic**: All decisions must be reproducible and clear

## Report

Return BOTH:
1. YAML configuration block (wrapped in ```yaml)
2. Full implementation plan in markdown format
3. End with: `Plan file: specs/issue-{issue_number}-adw-{adw_id}-sdlc_planner-{descriptive-name}.md`
