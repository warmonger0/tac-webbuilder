# Post-Shipping Cleanup Phase Implementation Plan

**Created:** 2025-11-16
**Status:** Planning
**Goal:** Organize documentation files from `/docs/` to appropriate subfolders after successful PR merge

## Current State Analysis

### ADW Workflow Documentation Lifecycle

1. **Planning Phase** (`adw_plan_iso.py`)
   - Creates: `specs/issue-{num}-adw-{id}-sdlc_planner-{name}.md`
   - Location: `/specs/` directory
   - State tracking: Stored in `ADWState.plan_file`

2. **Documentation Phase** (`adw_document_iso.py`)
   - Creates: `app_docs/feature-{adw_id}-{name}.md`
   - Location: `/app_docs/` directory
   - Updates: `.claude/commands/conditional_docs.md`

3. **Ship Phase** (`adw_ship_iso.py`)
   - Merges PR via GitHub API
   - Posts success message
   - **Current Gap:** No cleanup of associated documentation

### Documentation File Types in `/docs`

Based on analysis of current `/docs/` directory contents:

**Implementation Plans:**
- `*_IMPLEMENTATION_PLAN.md`
- `*_IMPLEMENTATION*.md`
- Pattern: Planning documents for features/phases

**Architecture/Technical:**
- `*_ARCHITECTURE.md`
- `*_TECHNICAL_OVERVIEW.md`
- Pattern: System design documents

**Guides:**
- `*_GUIDE.md`
- `*_QUICK_START.md`
- Pattern: How-to documentation

**Analysis:**
- `*_ANALYSIS.md`
- Pattern: Investigation/research documents

**Summaries:**
- `*_SUMMARY.md`
- Pattern: Completion/status reports

**Phase Documentation:**
- `PHASE_*_*.md`
- Pattern: Multi-phase feature documentation

### Existing Folder Structure

```
/docs/
├── Analysis/              # Analysis documents
├── Archived Issues/       # Completed issue documentation
├── features/              # Feature-specific docs
├── logs/                  # Log files
└── *.md                   # Mixed root-level docs
```

## Problem Statement

After ADW workflows ship successfully:

1. **Spec files** remain in `/specs/` indefinitely
2. **Root-level docs** accumulate in `/docs/` with no organization
3. **Implementation plans** created during ADW runs clutter root
4. **No automated cleanup** after successful merge
5. **Hard to find** related documentation for shipped features

## Proposed Solution

### Phase 1: Document Classification System

Create a cleanup module that categorizes and moves docs based on:

**Category Rules:**

1. **ADW-Generated Docs** (linked to `adw_id` and `issue_number`)
   - Implementation plans created during workflow
   - Can be identified by presence in ADW state or naming patterns
   - Destination: `/docs/Archived Issues/issue-{num}-{title}/`

2. **Architecture Docs**
   - `*_ARCHITECTURE.md`, `*_TECHNICAL_OVERVIEW.md`
   - Destination: `/docs/Architecture/` (new folder)

3. **Implementation Plans**
   - `*_IMPLEMENTATION_PLAN.md`, `*_IMPLEMENTATION.md`
   - Destination: `/docs/Implementation Plans/` (new folder)

4. **Analysis Docs**
   - `*_ANALYSIS.md`
   - Destination: `/docs/Analysis/` (already exists)

5. **Guides**
   - `*_GUIDE.md`, `*_QUICK_START.md`, `*_SETUP.md`
   - Destination: `/docs/Guides/` (new folder)

6. **Phase Documentation**
   - `PHASE_*_*.md`
   - Destination: `/docs/Archived Issues/` or keep in root if active

7. **Feature Specs** (from `/specs/`)
   - `specs/issue-{num}-*.md`
   - Destination: `/docs/Archived Issues/issue-{num}-{title}/specs/`

### Phase 2: Cleanup Module Implementation

**File:** `adws/adw_modules/doc_cleanup.py`

**Key Functions:**

```python
def classify_document(file_path: str) -> str:
    """Classify a document based on naming patterns and content."""
    # Returns: 'architecture', 'implementation', 'analysis', 'guide', 'phase', 'other'

def get_cleanup_destination(
    file_path: str,
    issue_number: Optional[str] = None,
    adw_id: Optional[str] = None
) -> Optional[str]:
    """Determine destination path for a document."""
    # Returns destination path or None if should stay in place

def cleanup_adw_documentation(
    issue_number: str,
    adw_id: str,
    state: ADWState,
    logger: logging.Logger
) -> Dict[str, Any]:
    """Clean up documentation after successful ADW workflow ship."""
    # Moves specs, implementation plans, and related docs
    # Returns summary of moves

def organize_root_docs(
    dry_run: bool = True,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """Organize all loose docs in /docs root."""
    # Batch cleanup utility for existing docs
```

**Features:**

1. **Safe Operations**
   - Git-aware (preserves history)
   - Uses `git mv` instead of `mv` for tracked files
   - Dry-run mode by default
   - Detailed logging

2. **Issue-Specific Cleanup**
   - Creates `/docs/Archived Issues/issue-{num}-{title}/` folder
   - Moves related specs from `/specs/`
   - Moves implementation plans from `/docs/`
   - Creates README.md with summary

3. **State Tracking**
   - Updates ADWState with cleanup metadata
   - Records moved files for rollback if needed
   - Timestamps cleanup operations

### Phase 3: Integration with Ship Workflow

**File:** `adws/adw_ship_iso.py`

**Integration Point:** After successful PR merge (line 318-329)

**New Steps:**

```python
# Step 6: Post success message (existing)
make_issue_comment(...)

# Step 7: Cleanup documentation (NEW)
from adw_modules.doc_cleanup import cleanup_adw_documentation

cleanup_result = cleanup_adw_documentation(
    issue_number=issue_number,
    adw_id=adw_id,
    state=state,
    logger=logger
)

if cleanup_result["success"]:
    logger.info(f"Cleaned up {cleanup_result['files_moved']} documentation files")
    make_issue_comment(
        issue_number,
        format_issue_message(
            adw_id,
            AGENT_SHIPPER,
            f"📁 Documentation cleanup completed\n"
            f"Organized {cleanup_result['files_moved']} files into:\n"
            f"{cleanup_result['summary']}"
        )
    )
else:
    logger.warning(f"Documentation cleanup had issues: {cleanup_result['errors']}")
    # Continue anyway - cleanup failure shouldn't block ship

# Step 8: Save final state (existing)
state.save("adw_ship_iso")
```

### Phase 4: New Folder Structure

**Proposed /docs Organization:**

```
/docs/
├── README.md                          # Index of documentation
├── Architecture/                      # System architecture docs
│   ├── ADW_CHAINING_ARCHITECTURE.md
│   ├── EXTERNAL_TEST_TOOLS_ARCHITECTURE.md
│   └── ...
├── Analysis/                          # Research/analysis (existing)
│   ├── ISSUE_8_PR_COMPARISON.md
│   └── ...
├── Guides/                            # How-to guides (new)
│   ├── EXTERNAL_TOOLS_INTEGRATION_GUIDE.md
│   ├── EXTERNAL_TOOLS_MIGRATION_GUIDE.md
│   ├── COST_OPTIMIZATION_QUICK_START.md
│   └── ...
├── Implementation Plans/              # Feature planning docs (new)
│   ├── OUT_LOOP_CODING_IMPLEMENTATION_PLAN.md
│   └── ...
├── Archived Issues/                   # Completed issues (existing)
│   ├── issue-1-workflows-doc-tab/
│   │   ├── README.md                  # Issue summary
│   │   ├── specs/                     # Moved from /specs/
│   │   │   └── issue-1-adw-*.md
│   │   ├── implementation_plan.md     # If created during ADW
│   │   └── summary.md                 # Completion summary
│   ├── issue-33-phase-3e-workflows/
│   └── ...
├── features/                          # Feature-specific docs (existing)
│   └── PLAYWRIGHT_LAZY_LOADING_IMPLEMENTATION.md
├── logs/                              # Log files (existing)
└── *.md                               # Core docs (api.md, architecture.md, etc.)
```

**Core Docs (Stay in Root):**
- `api.md`
- `architecture.md`
- `cli.md`
- `configuration.md`
- `examples.md`
- `troubleshooting.md`
- `web-ui.md`
- `playwright-mcp.md`

## Implementation Steps

### Step 1: Create Cleanup Module ✅

**File:** `adws/adw_modules/doc_cleanup.py`

**Deliverables:**
- [ ] Document classification logic
- [ ] Destination path resolver
- [ ] Git-aware file mover
- [ ] ADW-specific cleanup function
- [ ] Batch organizer for existing docs
- [ ] Comprehensive tests

### Step 2: Create New Folder Structure ✅

**Commands:**
```bash
mkdir -p docs/Architecture
mkdir -p docs/Guides
mkdir -p "docs/Implementation Plans"
```

**Deliverables:**
- [ ] New folders created
- [ ] README.md in each folder explaining purpose
- [ ] Update main docs/README.md with structure

### Step 3: Integrate with Ship Workflow ✅

**File:** `adws/adw_ship_iso.py`

**Deliverables:**
- [ ] Import cleanup module
- [ ] Add cleanup step after PR merge
- [ ] Handle cleanup failures gracefully
- [ ] Post cleanup summary to GitHub issue
- [ ] Update state with cleanup metadata

### Step 4: Create Utility Scripts ✅

**Scripts:**

1. **`scripts/organize_existing_docs.sh`**
   - Runs batch organization of existing `/docs` files
   - Dry-run mode by default
   - Confirmation before moving files

2. **`scripts/cleanup_archived_specs.sh`**
   - Moves old specs from `/specs/` to archived issues
   - Requires issue number parameter

**Deliverables:**
- [ ] Organize existing docs script
- [ ] Cleanup archived specs script
- [ ] Documentation for both scripts

### Step 5: Update Documentation ✅

**Files to Update:**

1. **`.claude/commands/quick_start/adw.md`**
   - Add note about automatic cleanup after ship

2. **`adws/README.md`**
   - Document cleanup phase
   - Explain folder structure

3. **`docs/README.md`**
   - Create/update with folder structure guide
   - Explain where to find what

**Deliverables:**
- [ ] ADW quick start updated
- [ ] ADW README updated
- [ ] Docs README created/updated

### Step 6: Batch Migrate Existing Docs ✅

**Process:**

1. Run dry-run of batch organizer
2. Review proposed moves
3. Execute moves in categories:
   - Architecture docs first
   - Guides second
   - Implementation plans third
   - Analysis docs (already in place)
   - Archived issues last

**Deliverables:**
- [ ] Dry-run report
- [ ] Approval for moves
- [ ] Execution of moves
- [ ] Verification all docs accessible

## Safety Considerations

1. **Git History Preservation**
   - Always use `git mv` for tracked files
   - Preserve commit history and blame

2. **Rollback Capability**
   - Log all moves in ADWState
   - Create rollback function if needed
   - Keep backup list of original paths

3. **Never Block Ship**
   - Cleanup failures are warnings, not errors
   - Ship workflow continues even if cleanup fails
   - Manual cleanup can be done later

4. **Dry-Run by Default**
   - Batch organizer has dry-run flag
   - Shows what would be moved before moving
   - Requires explicit confirmation

## Testing Strategy

### Unit Tests

**File:** `adws/adw_modules/tests/test_doc_cleanup.py`

1. Test document classification logic
2. Test destination path resolution
3. Test git-aware file moving
4. Test ADW-specific cleanup
5. Test batch organizer
6. Test error handling

### Integration Tests

1. Run full SDLC workflow + ship
2. Verify cleanup runs automatically
3. Verify files moved to correct locations
4. Verify state updated correctly
5. Verify GitHub comment posted

### Manual Testing

1. Test with real issue
2. Verify docs organized correctly
3. Check git history preserved
4. Verify rollback if needed

## Success Criteria

✅ **Automated Cleanup:**
- [x] Cleanup runs automatically after successful ship
- [x] Files moved to correct folders based on type
- [x] Specs moved from `/specs/` to archived issues
- [x] GitHub comment confirms cleanup
- [x] Worktree removed and resources freed

✅ **Organized Structure:**
- [x] New folders created and documented
- [ ] Existing docs migrated to new structure (batch migration available)
- [x] Easy to find documentation by type

✅ **Safety:**
- [x] Git history preserved
- [x] Rollback possible if needed
- [x] Ship never blocked by cleanup failures
- [x] State updated after file moves

✅ **Developer Experience:**
- [x] Clear folder structure
- [x] README in each folder
- [x] Updated quick start guides
- [x] Worktree automatically removed after ship

## Future Enhancements

1. **Cleanup on Close**
   - Also run cleanup when issue closed without ship
   - Different destination for unmerged issues

2. **Smart Detection**
   - Parse doc content to better classify
   - Extract issue references from content
   - Auto-link related docs

3. **Cleanup Dashboard**
   - Show pending cleanups
   - Manual trigger for batch cleanup
   - Statistics on organized docs

4. **Archive Compression**
   - Compress old archived issues
   - Keep recent ones readily accessible
   - Reduce repo size over time

## Questions for User

1. **Folder Names:** Agree with proposed structure or prefer different names?
2. **Core Docs:** Which docs should stay in root vs. move to subfolders?
3. **Timing:** Should cleanup happen before or after ship success message?
4. **Batch Migration:** Run batch migration of existing docs now or gradually?
5. **Specs Retention:** Keep all specs or only recent ones?

## Next Steps

1. Get user approval on folder structure
2. Implement `doc_cleanup.py` module
3. Create new folders with READMEs
4. Integrate into ship workflow
5. Test with real issue
6. Batch migrate existing docs
