# ADW Refactoring Examples

This document shows practical examples of using the new Phase 1 Python modules for worktree setup, app lifecycle, and commit generation.

## Table of Contents

1. [Worktree Setup Examples](#worktree-setup-examples)
2. [App Lifecycle Examples](#app-lifecycle-examples)
3. [Commit Generation Examples](#commit-generation-examples)
4. [Manual Slash Command Usage](#manual-slash-command-usage)

---

## Worktree Setup Examples

### Example 1: Complete Worktree Setup (ADW Workflow)

```python
from adw_modules.worktree_setup import setup_worktree_complete
from adw_modules.worktree_ops import create_worktree, get_ports_for_adw
from adw_modules.utils import setup_logger

# Setup
adw_id = "abc12345"
branch_name = "feature-issue-42-adw-abc12345-add-authentication"
logger = setup_logger(adw_id, "setup_example")

# Get deterministic ports
backend_port, frontend_port = get_ports_for_adw(adw_id)
# backend_port = 9100, frontend_port = 9200

# Create the worktree
worktree_path, error = create_worktree(adw_id, branch_name, logger)

if error:
    logger.error(f"Failed to create worktree: {error}")
    exit(1)

# Setup complete environment (replaces /install_worktree)
success, error = setup_worktree_complete(
    worktree_path=worktree_path,
    backend_port=backend_port,
    frontend_port=frontend_port,
    logger=logger
)

if not success:
    logger.error(f"Setup failed: {error}")
    exit(1)

logger.info("✅ Worktree ready!")
# Output:
# Created .ports.env
# Copied and merged .env files
# Configured MCP with absolute paths
# Installed backend dependencies
# Installed frontend dependencies
# Setup database
# ✅ Worktree ready!
```

### Example 2: Manual Worktree Setup (Debugging)

For debugging or one-off setup, you can still use the slash command:

```bash
# Interactive AI-powered setup
claude -p "/install_worktree /Users/me/project/trees/abc12345 9100 9200"

# The AI will:
# - Explain each step
# - Handle edge cases interactively
# - Provide detailed feedback
# - Useful for troubleshooting
```

---

## App Lifecycle Examples

### Example 3: Prepare App for Review (ADW Workflow)

```python
from adw_modules.app_lifecycle import prepare_application_for_review
from adw_modules.utils import setup_logger

# Setup
adw_id = "abc12345"
worktree_path = "/Users/me/project/trees/abc12345"
logger = setup_logger(adw_id, "review_example")

# Prepare application (replaces /prepare_app)
success, info = prepare_application_for_review(
    working_dir=worktree_path,
    logger=logger
)

if not success:
    logger.error(f"App preparation failed: {info.get('error')}")
    exit(1)

# App is ready!
print(f"Backend: {info['backend_url']}")    # http://localhost:9100
print(f"Frontend: {info['frontend_url']}")  # http://localhost:9200

# Output:
# Resetting database...
# Database reset complete
# Starting application...
# Application started in background
# Waiting for application health check...
# ✅ Backend healthy at http://localhost:9100/api/health
# ✅ Frontend healthy at http://localhost:9200
# ✅ Application ready for review/testing
# Backend: http://localhost:9100
# Frontend: http://localhost:9200
```

### Example 4: Manual Start/Stop (Development)

```python
from adw_modules.app_lifecycle import (
    start_application,
    stop_application,
    detect_port_configuration
)

# Detect ports from .ports.env or use defaults
backend_port, frontend_port = detect_port_configuration()
print(f"Ports: {backend_port}, {frontend_port}")

# Start application
success, info = start_application(wait_for_health=True)

if success:
    print(f"App running at {info['frontend_url']}")

# Do your work...

# Stop application
success, error = stop_application()
if success:
    print("App stopped")
```

### Example 5: Manual App Preparation (Interactive)

```bash
# Interactive AI-powered app startup
claude -p "/prepare_app"

# The AI will:
# - Detect port configuration
# - Reset database
# - Start services
# - Wait for health checks
# - Explain what's happening
# - Useful for debugging startup issues
```

---

## Commit Generation Examples

### Example 6: Generate Commit Message (ADW Workflow)

```python
from adw_modules.commit_generator import generate_commit_message
from adw_modules.data_types import GitHubIssue

# Setup
agent_name = "sdlc_planner"
issue_type = "/feature"  # or "feature", slash optional
issue = GitHubIssue(
    number=42,
    title="Add user authentication system",
    body="Implement JWT-based authentication..."
)

# Generate commit message
commit_message = generate_commit_message(
    agent_name=agent_name,
    issue_type=issue_type,
    issue=issue
)

print(commit_message)
# Output: "sdlc_planner: feature: add user authentication system"
```

### Example 7: Generate and Commit in One Step

```python
from adw_modules.commit_generator import generate_and_commit
from adw_modules.data_types import GitHubIssue
from adw_modules.utils import setup_logger

# Setup
logger = setup_logger("abc12345", "commit_example")
worktree_path = "/Users/me/project/trees/abc12345"

issue = GitHubIssue(
    number=42,
    title="Fix login validation error",
    body="Users can bypass validation..."
)

# Generate message and create commit
success, commit_message, error = generate_and_commit(
    agent_name="sdlc_implementor",
    issue_type="/bug",
    issue=issue,
    working_dir=worktree_path,
    logger=logger
)

if success:
    print(f"✅ Committed: {commit_message}")
else:
    print(f"❌ Failed: {error}")

# Output:
# Generated commit message (Python): sdlc_implementor: bug: fix login validation error
# ✅ Commit created: sdlc_implementor: bug: fix login validation error
# ✅ Committed: sdlc_implementor: bug: fix login validation error
```

### Example 8: Manual Commit Message (Interactive)

```bash
# Interactive AI-powered commit message
claude -p '/commit sdlc_planner feature {"number": 42, "title": "Add user auth", "body": "..."}'

# The AI will:
# - Analyze git diff
# - Generate contextual message
# - Stage and commit changes
# - Useful for complex commits needing context
```

---

## Manual Slash Command Usage

All slash commands are still available for manual/interactive use. Here's when to use each:

### When to Use Python Modules (Automated)

✅ **Use in ADW workflows** - Fast, cheap, deterministic
✅ **Use in scripts** - Programmatic access
✅ **Use for production** - Reliable, testable

```python
# Automated workflow
from adw_modules.worktree_setup import setup_worktree_complete
success, error = setup_worktree_complete(path, port1, port2, logger)
```

### When to Use Slash Commands (Manual)

✅ **Debugging** - AI can explain issues
✅ **One-off tasks** - Quick interactive setup
✅ **Learning** - See how things work
✅ **Edge cases** - AI handles unusual situations

```bash
# Interactive debugging
claude -p "/install_worktree /path/to/worktree 9100 9200"
```

---

## Complete ADW Workflow Example

Here's a complete example showing Phase 1 improvements in a full workflow:

```python
from adw_modules.worktree_ops import create_worktree, get_ports_for_adw
from adw_modules.worktree_setup import setup_worktree_complete
from adw_modules.app_lifecycle import prepare_application_for_review
from adw_modules.commit_generator import generate_and_commit
from adw_modules.github import fetch_issue
from adw_modules.utils import setup_logger

# Configuration
issue_number = "42"
adw_id = "abc12345"
branch_name = "feature-issue-42-adw-abc12345-add-auth"

# Setup logging
logger = setup_logger(adw_id, "complete_workflow")

# Step 1: Get deterministic ports
backend_port, frontend_port = get_ports_for_adw(adw_id)
logger.info(f"Ports: Backend={backend_port}, Frontend={frontend_port}")

# Step 2: Create worktree
logger.info("Creating worktree...")
worktree_path, error = create_worktree(adw_id, branch_name, logger)
if error:
    logger.error(f"Failed: {error}")
    exit(1)

# Step 3: Setup worktree environment (PHASE 1 IMPROVEMENT)
logger.info("Setting up worktree (Python, no AI)...")
success, error = setup_worktree_complete(
    worktree_path, backend_port, frontend_port, logger
)
if not success:
    logger.error(f"Failed: {error}")
    exit(1)
# ✅ Saved $0.15 + 40s vs /install_worktree

# Step 4: Implement feature (would use agent here)
logger.info("Feature implementation would happen here...")

# Step 5: Prepare app for review (PHASE 1 IMPROVEMENT)
logger.info("Preparing app for review (Python, no AI)...")
success, info = prepare_application_for_review(worktree_path, logger)
if not success:
    logger.error(f"Failed: {info.get('error')}")
    exit(1)
# ✅ Saved $0.10 + 27s vs /prepare_app

# Step 6: Run review (would use agent here)
logger.info("Review would happen here...")

# Step 7: Create commit (PHASE 1 IMPROVEMENT)
issue = fetch_issue(issue_number, "owner/repo")
success, message, error = generate_and_commit(
    agent_name="sdlc_implementor",
    issue_type="/feature",
    issue=issue,
    working_dir=worktree_path,
    logger=logger
)
if not success:
    logger.error(f"Failed: {error}")
    exit(1)
# ✅ Saved $0.05 + 19s vs /commit

logger.info("✅ Complete workflow finished!")
# Total Phase 1 savings: $0.30 + 86 seconds
```

---

## Performance Comparison

### Before Phase 1 (AI Slash Commands)

```python
# Worktree setup: /install_worktree
# Cost: $0.15, Time: 45s, Tokens: 8,000

# App preparation: /prepare_app
# Cost: $0.10, Time: 30s, Tokens: 5,000

# Commit: /commit
# Cost: $0.05, Time: 20s, Tokens: 3,000

# Total: $0.30, 95s, 16,000 tokens
```

### After Phase 1 (Python Functions)

```python
# Worktree setup: setup_worktree_complete()
# Cost: $0.00, Time: 5s, Tokens: 0

# App preparation: prepare_application_for_review()
# Cost: $0.00, Time: 3s, Tokens: 0

# Commit: generate_and_commit()
# Cost: $0.00, Time: 1s, Tokens: 0

# Total: $0.00, 9s, 0 tokens
# Savings: $0.30, 86s, 16,000 tokens per workflow
```

---

## Next Steps

- Review [PHASE_2_PATH_PRECOMPUTATION.md](./PHASE_2_PATH_PRECOMPUTATION.md) for next optimization
- See [README.md](./README.md) for complete refactoring roadmap
- Check [PHASE_1_COMPLETE.md](./PHASE_1_COMPLETE.md) for implementation details
