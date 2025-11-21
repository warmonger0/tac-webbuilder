# ADW Quick Start

## What is ADW?
AI Developer Workflow - Automated development via isolated git worktrees + Claude Code CLI

## Architecture
- **Isolation:** Each workflow runs in `trees/{adw_id}/` (complete repo copy)
- **Ports:** Backend 9100-9114, Frontend 9200-9214 (supports 15 concurrent)
- **State:** `agents/{adw_id}/adw_state.json` tracks progress
- **Phases (Complete):** Plan → Validate → Build → Lint → Test → Review → Doc → Ship → Cleanup (ALL 9)
- **Phases (Legacy):** Plan → Build → Test → Review → Document (5 only - missing validate, lint, ship, cleanup)

## New Features in Complete Workflows
- **Validate Phase (Nov 2025):** Pre-build validation detects inherited errors from main branch
- **Lint Phase:** TypeScript/ESLint validation prevents deploying broken code
- **Ship Phase:** Automatic PR approval and merge (in ZTE workflows)
- **Cleanup Phase:** Automatic worktree removal and artifact organization
- **External Tools:** Enabled by default for 70-95% token reduction
- **Optimized Plan:** Optional flag for faster planning workflow
- **Flag Support:** --skip-e2e, --skip-resolution, --no-external, --use-optimized-plan

## Cost Optimization
- **Lightweight:** $0.20-0.50 for simple changes (CSS, text, single-file)
- **Standard:** $3-5 for features (full SDLC)
- **Heavy:** $8-12 for complex features (Opus model)

Auto-routing via `adw_modules/complexity_analyzer.py`

## Quick Workflow Selection

### Recommended Workflows (Production-Ready)
```bash
cd adws/

# Stepwise refinement - analyzes issue complexity (ATOMIC vs DECOMPOSE)
uv run adw_stepwise_iso.py <issue-number>

# Complete SDLC with ALL 9 phases (Plan → Validate → Build → Lint → Test → Review → Doc → Ship → Cleanup)
uv run adw_sdlc_complete_iso.py <issue-number> [--skip-e2e] [--skip-resolution] [--no-external] [--use-optimized-plan]

# Zero Touch Execution with ALL 9 phases + auto-merge (⚠️ auto-merges to main!)
uv run adw_sdlc_complete_zte_iso.py <issue-number> [--skip-e2e] [--skip-resolution] [--no-external] [--use-optimized-plan]
```

### Entry Points (Create Worktrees)
```bash
cd adws/

# Planning only
uv run adw_plan_iso.py <issue-number>

# Quick patch
uv run adw_patch_iso.py <issue-number>

# Lightweight (simple changes)
uv run adw_lightweight_iso.py <issue-number>
```

### Complete Workflows
```bash
# Plan + Build only
uv run adw_plan_build_iso.py <issue-number>
```

### Deprecated Workflows (Use Complete Versions)
```bash
# DEPRECATED: Missing lint phase - use adw_sdlc_complete_iso.py instead
# uv run adw_sdlc_iso.py <issue-number>

# DEPRECATED: Missing lint phase - use adw_sdlc_complete_zte_iso.py instead
# uv run adw_sdlc_zte_iso.py <issue-number>
```

### Dependent Phases (Need Existing Worktree)
```bash
uv run adw_build_iso.py <issue-number> <adw-id>
uv run adw_test_iso.py <issue-number> <adw-id>
uv run adw_review_iso.py <issue-number> <adw-id>
uv run adw_ship_iso.py <issue-number> <adw-id>
uv run adw_cleanup_iso.py <issue-number> <adw-id>
```

## Trigger Systems
```bash
# Real-time webhook
uv run adw_triggers/trigger_webhook.py  # Port 8001

# Polling monitor (20s)
uv run adw_triggers/trigger_cron.py
```

## Key Modules
- `adw_modules/agent.py` - Claude Code CLI integration
- `adw_modules/workflow_ops.py` - Core workflow logic
- `adw_modules/worktree_ops.py` - Worktree management
- `adw_modules/state.py` - State persistence
- `adw_modules/complexity_analyzer.py` - Auto-routing

## Common Tasks

### Workflow Selection
Quick reference: `.claude/commands/references/adw_workflows.md` (1,500 tokens)
Full details: `adws/README.md` (3,900 tokens)

### Debugging
Check: `agents/{adw_id}/adw_state.json`
Logs: `agents/{adw_id}/{phase}/raw_output.jsonl`

### Cleanup
```bash
# Automatic cleanup after ship (in ZTE workflow)
# - Organizes docs to appropriate folders
# - Removes worktree and frees resources
# - 100% Python, zero LLM calls

# Manual cleanup
uv run adw_cleanup_iso.py <issue-number> <adw-id>
./scripts/cleanup_archived_issue.sh <issue-number> <adw-id>

# Programmatic cleanup
python3 -c "from adw_modules.cleanup_operations import cleanup_shipped_issue; \
  cleanup_shipped_issue('33', '88405eb3')"
```

## New Validate Phase (Nov 2025)

All complete workflows now include a Validate phase:

```
OLD: Plan → Build → Lint → Test → Review → Doc → Ship → Cleanup (8 phases)
NEW: Plan → Validate → Build → Lint → Test → Review → Doc → Ship → Cleanup (9 phases)
```

**Purpose**: Detect inherited errors BEFORE implementation to prevent false positives

**How it Works**:
1. **Validate Phase**: Runs build check on UNMODIFIED worktree, captures baseline errors
2. **Build Phase**: Runs build check on MODIFIED worktree, calculates differential errors
3. **Result**: Only NEW errors introduced by your changes will block the workflow

**Benefits**:
- ✅ Work on issues even when main branch has errors
- ✅ No false positives from inherited errors
- ✅ Get credit for fixing inherited errors
- ✅ Maintains clean code standards

**Usage**: Automatic in all `adw_sdlc_complete_*.py` workflows

**Manual**: `uv run adw_validate_iso.py <issue-number> <adw-id>`

**Best Practices**: See `docs/ADW_WORKFLOW_BEST_PRACTICES.md` for complete guide

## When to Load Full Docs
- **Complete ADW guide:** `adws/README.md` (3,900 tokens)
- **All workflows:** `.claude/commands/references/adw_workflows.md` (1,500 tokens)
- **Architecture:** `.claude/commands/references/architecture_overview.md` (900 tokens)
- **Best Practices:** `docs/ADW_WORKFLOW_BEST_PRACTICES.md` (workflow troubleshooting)
