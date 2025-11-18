# ADW Workflow Reference

## Workflow Categories

### Entry Point Workflows (Create Worktrees)

#### adw_plan_iso.py
- **Purpose:** Generate implementation plan in isolated worktree
- **Creates:** Worktree, allocates ports, sets up environment
- **Output:** `agents/{adw_id}/{adw_id}_plan_spec.md`
- **Usage:** `uv run adw_plan_iso.py <issue-number> [adw-id]`

#### adw_patch_iso.py
- **Purpose:** Quick patch workflow for targeted fixes
- **Trigger:** Issue/comment contains "adw_patch" keyword
- **Creates:** Worktree with patch-specific plan
- **Usage:** `uv run adw_patch_iso.py <issue-number> [adw-id]`

#### adw_lightweight_iso.py
- **Purpose:** Cost-optimized workflow for simple changes
- **Target cost:** $0.20-0.50 (90% savings vs standard)
- **Use cases:** CSS, text updates, simple refactors
- **Routing:** Auto-selected by complexity analyzer
- **Usage:** `uv run adw_lightweight_iso.py <issue-number> [adw-id]`

#### adw_stepwise_iso.py (NEW)
- **Purpose:** Stepwise refinement analysis for issue decomposition
- **Analyzes:** Issue complexity to decide ATOMIC vs DECOMPOSE
- **Output:** GitHub comment with analysis + sub-issues (if DECOMPOSE)
- **Routing:** For DECOMPOSE: Creates numbered sub-issues; For ATOMIC: Routes to workflow
- **Usage:** `uv run adw_stepwise_iso.py <issue-number> [adw-id]`
- **Decision criteria:** File count, cross-cutting concerns, testing needs, integration complexity

### Dependent Workflows (Require Existing Worktree)

#### adw_build_iso.py
- **Purpose:** Implement solution from plan
- **Requires:** Existing worktree + plan file
- **Agent:** `sdlc_implementor`
- **Usage:** `uv run adw_build_iso.py <issue-number> <adw-id>`

#### adw_test_iso.py
- **Purpose:** Run tests and auto-resolve failures
- **Features:** Unit tests, E2E tests (optional), auto-fix
- **Flags:** `--skip-e2e`
- **Usage:** `uv run adw_test_iso.py <issue-number> <adw-id> [--skip-e2e]`

#### adw_review_iso.py
- **Purpose:** Validate implementation against spec
- **Features:** Screenshot capture, blocker resolution
- **Flags:** `--skip-resolution`
- **Usage:** `uv run adw_review_iso.py <issue-number> <adw-id> [--skip-resolution]`

#### adw_document_iso.py
- **Purpose:** Generate feature documentation
- **Output:** `app_docs/feature-{id}-{slug}.md`
- **Includes:** Overview, technical guide, screenshots
- **Usage:** `uv run adw_document_iso.py <issue-number> <adw-id>`

#### adw_ship_iso.py
- **Purpose:** Approve and merge PR to main
- **Validation:** Checks all ADWState fields populated
- **Method:** Squash merge
- **Usage:** `uv run adw_ship_iso.py <issue-number> <adw-id>`

### Orchestrator Workflows

#### adw_sdlc_complete_iso.py (NEW - RECOMMENDED)
- **Purpose:** Complete SDLC with ALL 8 phases (Plan → Build → Lint → Test → Review → Doc → Ship → Cleanup)
- **Phases:** Includes lint validation (was missing in adw_sdlc_iso.py)
- **Flags:** `--skip-e2e`, `--skip-resolution`, `--no-external`, `--use-optimized-plan`
- **External tools:** Uses external test/build tools by default (70-95% token reduction)
- **Usage:** `uv run adw_sdlc_complete_iso.py <issue-number> [adw-id]`
- **Key improvements:** Added lint phase, ship phase, cleanup phase

#### adw_sdlc_complete_zte_iso.py (NEW - RECOMMENDED)
- **Purpose:** Zero Touch Execution with ALL 8 phases + Auto-ship
- **Phases:** Includes lint validation and cleanup (was missing in adw_sdlc_zte_iso.py)
- **⚠️ WARNING:** Automatically merges to main if all phases pass
- **Flags:** `--skip-e2e`, `--skip-resolution`, `--no-external`, `--use-optimized-plan`
- **External tools:** Uses external test/build tools by default (70-95% token reduction)
- **Usage:** `uv run adw_sdlc_complete_zte_iso.py <issue-number> [adw-id]`
- **Key improvements:** Added lint phase, cleanup phase, prevents auto-merging broken code

#### adw_sdlc_iso.py (DEPRECATED)
- **Purpose:** Complete SDLC (Plan → Build → Test → Review → Document)
- **⚠️ DEPRECATED:** Use `adw_sdlc_complete_iso.py` instead - missing lint phase
- **Flags:** `--skip-e2e`, `--skip-resolution`
- **Usage:** `uv run adw_sdlc_iso.py <issue-number> [adw-id]`
- **Missing:** Lint validation, ship phase, cleanup phase

#### adw_sdlc_zte_iso.py (DEPRECATED)
- **Purpose:** Zero Touch Execution - Complete SDLC + Auto-ship
- **⚠️ DEPRECATED:** Use `adw_sdlc_complete_zte_iso.py` instead - missing lint phase
- **⚠️ WARNING:** Can auto-merge broken code (no lint validation)
- **Flags:** `--skip-e2e`, `--skip-resolution`
- **Usage:** `uv run adw_sdlc_zte_iso.py <issue-number> [adw-id]`
- **Missing:** Lint validation, cleanup phase

#### adw_plan_build_iso.py
- **Purpose:** Plan + Build only
- **Usage:** `uv run adw_plan_build_iso.py <issue-number> [adw-id]`

#### adw_plan_build_test_iso.py
- **Purpose:** Plan + Build + Test
- **Usage:** `uv run adw_plan_build_test_iso.py <issue-number> [adw-id]`

#### adw_plan_build_test_review_iso.py
- **Purpose:** Plan + Build + Test + Review
- **Usage:** `uv run adw_plan_build_test_review_iso.py <issue-number> [adw-id]`

#### adw_plan_build_review_iso.py
- **Purpose:** Plan + Build + Review (skip tests)
- **Usage:** `uv run adw_plan_build_review_iso.py <issue-number> [adw-id]`

#### adw_plan_build_document_iso.py
- **Purpose:** Plan + Build + Document
- **Usage:** `uv run adw_plan_build_document_iso.py <issue-number> [adw-id]`

## Trigger Systems

### trigger_webhook.py
- **Purpose:** Real-time GitHub webhook server
- **Port:** 8001 (default)
- **Endpoints:** `/gh-webhook`, `/health`
- **Events:** Issues, Issue comments
- **Security:** GitHub signature validation via `GITHUB_WEBHOOK_SECRET`
- **Usage:** `uv run adw_triggers/trigger_webhook.py`

### trigger_cron.py
- **Purpose:** Polling monitor for GitHub
- **Interval:** 20 seconds
- **Triggers on:**
  - New issues with no comments
  - Latest comment is exactly "adw"
- **Usage:** `uv run adw_triggers/trigger_cron.py`

## Workflow Selection

### Via Issue Body Keywords
Include workflow name in issue body:
```
Title: Add export functionality
Body: Please add CSV export.
Include workflow: adw_sdlc_complete_iso
```

**Recommended keywords:**
- `adw_stepwise_iso` - Stepwise refinement analysis
- `adw_sdlc_complete_iso` - Complete SDLC with ALL 8 phases
- `adw_sdlc_complete_zte_iso` - Complete ZTE with ALL 8 phases + auto-merge

**Available keywords:**
- `adw_plan_iso`
- `adw_patch_iso`
- `adw_lightweight_iso`
- `adw_plan_build_iso`
- `adw_plan_build_test_iso`
- `adw_plan_build_test_review_iso`

**Deprecated keywords (use complete versions):**
- `adw_sdlc_iso` - Use `adw_sdlc_complete_iso` instead
- `adw_sdlc_zte_iso` - Use `adw_sdlc_complete_zte_iso` instead

### Via Model Set
Specify model complexity:
```
Include workflow: adw_sdlc_iso model_set heavy
```

**Model sets:**
- `base` - Sonnet for all operations (default, cost-optimized)
- `heavy` - Opus for complex operations (implement, debug, document)

### Via Complexity Analyzer
Automatic routing based on issue analysis:
- **Simple:** → `adw_lightweight_iso` ($0.20-0.50)
- **Standard:** → `adw_sdlc_iso` ($3-5)
- **Complex:** → `adw_sdlc_iso` with heavy model set ($8-12)

**Complexity scoring:**
- Simple UI changes: -2 points
- Documentation only: -3 points
- Single file: -1 point
- Full-stack integration: +3 points
- Database changes: +2 points

## ADW State Management

### ADWState Fields
```json
{
  "adw_id": "a1b2c3d4",
  "issue_number": "123",
  "branch_name": "feat-123-a1b2c3d4-feature-name",
  "plan_file": "/path/to/plan_spec.md",
  "issue_class": "/feature",
  "worktree_path": "/Users/.../trees/a1b2c3d4",
  "backend_port": 9107,
  "frontend_port": 9207,
  "model_set": "base",
  "adw_ids": ["adw_plan_iso", "adw_build_iso"]
}
```

### State Persistence
- **Location:** `agents/{adw_id}/adw_state.json`
- **Purpose:** Share data between workflow phases
- **Lifecycle:** Created in plan phase, updated throughout, cleaned after ship

## Port Allocation

### Algorithm
```python
def get_ports_for_adw(adw_id: str) -> Tuple[int, int]:
    index = int(adw_id[:8], 36) % 15
    backend_port = 9100 + index
    frontend_port = 9200 + index
    return backend_port, frontend_port
```

### Port Ranges
- **Backend:** 9100-9114 (15 ports)
- **Frontend:** 9200-9214 (15 ports)
- **Deterministic:** Same ADW ID always gets same ports
- **Fallback:** Auto-find alternative if preferred ports busy

## Worktree Structure

```
trees/
├── abc12345/              # Complete repo copy for ADW abc12345
│   ├── .git/              # Worktree git directory
│   ├── .env               # Copied from main repo
│   ├── .ports.env         # BACKEND_PORT=9107, FRONTEND_PORT=9207
│   ├── app/               # Application code
│   ├── adws/              # ADW scripts
│   └── ...

agents/                    # Shared state location (not in worktree)
├── abc12345/
│   ├── adw_state.json     # Persistent state
│   ├── abc12345_plan_spec.md
│   ├── planner/
│   │   └── raw_output.jsonl
│   ├── implementor/
│   │   └── raw_output.jsonl
│   └── reviewer/
│       ├── raw_output.jsonl
│       └── review_img/
```

## Cleanup

### Remove Worktree
```bash
git worktree remove trees/abc12345
```

### List Worktrees
```bash
git worktree list
```

### Prune Invalid Entries
```bash
git worktree prune
```

### Force Delete Directory
```bash
rm -rf trees/abc12345
```

## Common Usage Patterns

### Stepwise Refinement Analysis (RECOMMENDED for complex issues)
```bash
uv run adw_stepwise_iso.py 123
# Analyzes and decides: ATOMIC or DECOMPOSE
```

### Single Issue, Full SDLC (RECOMMENDED)
```bash
uv run adw_sdlc_complete_iso.py 123
# ALL 8 phases: Plan → Build → Lint → Test → Review → Doc → Ship → Cleanup
```

### Single Issue, Full SDLC (DEPRECATED)
```bash
uv run adw_sdlc_iso.py 123
# ⚠️ DEPRECATED: Missing lint phase - use adw_sdlc_complete_iso.py
```

### Batch Processing with ZTE (RECOMMENDED)
```bash
# Use complete ZTE workflow
uv run adw_sdlc_complete_zte_iso.py 123
# ALL 8 phases with auto-merge
```

### Batch Processing with ZTE (DEPRECATED)
```bash
scripts/zte_hopper.sh
# ⚠️ May use deprecated workflows - update to use adw_sdlc_complete_zte_iso.py
```

### Manual Phase-by-Phase
```bash
uv run adw_plan_iso.py 123
# Review plan, then:
uv run adw_build_iso.py 123 abc12345
uv run adw_test_iso.py 123 abc12345
uv run adw_ship_iso.py 123 abc12345
```

### Parallel Workflows
```bash
uv run adw_sdlc_complete_iso.py 101 &
uv run adw_sdlc_complete_iso.py 102 &
uv run adw_sdlc_complete_iso.py 103 &
# Each gets isolated worktree and ports
```

## Model Selection per Command

Commands using **Opus in heavy mode:**
- `/implement`
- `/resolve_failed_test`
- `/resolve_failed_e2e_test`
- `/document`
- `/chore`, `/bug`, `/feature`
- `/patch`

Commands always using **Sonnet:**
- `/classify_issue`
- `/generate_branch_name`
- `/commit`
- `/pull_request`
- `/review` (base mode)
- `/test`, `/test_e2e`

## Workflow Output

### Planning Phase
- `agents/{adw_id}/{adw_id}_plan_spec.md`
- `agents/{adw_id}/planner/raw_output.jsonl`

### Implementation Phase
- Code changes in worktree
- `agents/{adw_id}/implementor/raw_output.jsonl`

### Testing Phase
- Test execution logs
- `agents/{adw_id}/tester/raw_output.jsonl`

### Review Phase
- Screenshots in `agents/{adw_id}/reviewer/review_img/`
- Uploaded to R2 (if configured)
- `agents/{adw_id}/reviewer/raw_output.jsonl`

### Documentation Phase
- `app_docs/feature-{id}-{slug}.md`
- Screenshots in `app_docs/assets/`
- `agents/{adw_id}/documenter/raw_output.jsonl`

### Ship Phase
- PR approved and merged
- Worktree can be cleaned up
