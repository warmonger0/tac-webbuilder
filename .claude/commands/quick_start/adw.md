# ADW Quick Start

## What is ADW?
AI Developer Workflow - Automated development via isolated git worktrees + Claude Code CLI

## Architecture
- **Isolation:** Each workflow runs in `trees/{adw_id}/` (complete repo copy)
- **Ports:** Backend 9100-9114, Frontend 9200-9214 (supports 15 concurrent)
- **State:** `agents/{adw_id}/adw_state.json` tracks progress
- **Phases:** Plan → Build → Test → Review → Document → Ship

## Cost Optimization
- **Lightweight:** $0.20-0.50 for simple changes (CSS, text, single-file)
- **Standard:** $3-5 for features (full SDLC)
- **Heavy:** $8-12 for complex features (Opus model)

Auto-routing via `adw_modules/complexity_analyzer.py`

## Quick Workflow Selection

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
# Full SDLC
uv run adw_sdlc_iso.py <issue-number>

# Zero Touch (auto-merge ⚠️)
uv run adw_sdlc_zte_iso.py <issue-number>

# Plan + Build only
uv run adw_plan_build_iso.py <issue-number>
```

### Dependent Phases (Need Existing Worktree)
```bash
uv run adw_build_iso.py <issue-number> <adw-id>
uv run adw_test_iso.py <issue-number> <adw-id>
uv run adw_review_iso.py <issue-number> <adw-id>
uv run adw_ship_iso.py <issue-number> <adw-id>
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
git worktree list                # List worktrees
git worktree remove trees/{adw_id}  # Remove worktree
```

## When to Load Full Docs
- **Complete ADW guide:** `adws/README.md` (3,900 tokens)
- **All workflows:** `.claude/commands/references/adw_workflows.md` (1,500 tokens)
- **Architecture:** `.claude/commands/references/architecture_overview.md` (900 tokens)
