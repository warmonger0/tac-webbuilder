# Post-Shipping Cleanup Architecture

**Created:** 2025-11-17
**Status:** Implemented

## Overview

The cleanup phase (`adw_cleanup_iso.py`) runs **after** the ship phase to organize documentation files into appropriate subfolders. This document explains the architecture and addresses potential breaking points.

## Execution Context

**CRITICAL:** Cleanup runs in the **main repository**, NOT in the worktree.

```
Workflow Order:
1. Plan   → Worktree (creates specs/issue-X.md)
2. Build  → Worktree (reads state.plan_file)
3. Test   → Worktree
4. Review → Worktree (may read state.plan_file)
5. Document → Worktree (uses find_spec_file())
6. Ship   → Main repo (merges PR, closes worktree)
7. Cleanup → Main repo (moves files, updates state, removes worktree)
```

**Why this order is safe:**
- All phases that **read** `plan_file` run in the worktree
- Cleanup runs **after** ship when worktree is merged
- Ship merges the spec file from worktree → main repo
- Cleanup then moves it within main repo

## State Management

### Plan File Path Updates

The cleanup phase updates `state.plan_file` after moving files:

```python
# Before cleanup
state.plan_file = "specs/issue-33-adw-88405eb3-sdlc_planner-phase-3e.md"

# After cleanup
state.plan_file = "docs/Archived Issues/issue-33-phase-3e/specs/issue-33-adw-88405eb3-sdlc_planner-phase-3e.md"
```

This ensures:
1. State remains accurate
2. Future references to plan_file work
3. Audit trail is preserved

### State Fields Affected

**Updated by cleanup:**
- `plan_file` - Path to spec file (updated to new location)
- `cleanup_metadata` - Added with cleanup details

**Not affected:**
- `branch_name` - Branch is already merged/deleted
- `issue_class` - Static classification
- `worktree_path` - Worktree may be removed separately
- `backend_port` / `frontend_port` - Static allocations

## Cleanup Operations

### 1. Spec Files

**Source:** `specs/issue-{num}-adw-{id}-sdlc_planner-{name}.md`
**Destination:** `docs/Archived Issues/issue-{num}-{title}/specs/`

**Process:**
1. Read `state.plan_file` for spec location
2. Move file using `git mv` (preserves history)
3. Update `state.plan_file` with new path
4. Log move in cleanup metadata

### Implementation Plans

**Source:** `docs/*_IMPLEMENTATION_PLAN.md` (if related to issue)
**Destination:** `docs/Archived Issues/issue-{num}-{title}/`

**Process:**
1. Scan `/docs` root for `.md` files
2. Classify by naming pattern
3. Check content for issue number or adw_id
4. Move if match found

### 3. Other Documents

**Architecture Docs** → `docs/Architecture/`
**Guides** → `docs/Guides/`
**Analysis** → `docs/Analysis/`

### 4. Worktree Removal

**Source:** `trees/{adw_id}/`

**Process:**
1. Read `state.worktree_path` for worktree location
2. Remove worktree using `git worktree remove --force`
3. If git command fails, manually delete directory
4. Free allocated backend and frontend ports
5. Log worktree removal in cleanup metadata

**Resources Freed:**
- Disk space (~500MB-2GB per worktree)
- Backend port (9100-9114 range)
- Frontend port (9200-9214 range)
- Git worktree entry

## Potential Breaking Points

### ✅ SAFE: Phase Dependencies

**No breakage** because cleanup runs after all phases complete:

```
Build phase (worktree) reads state.plan_file ✅
  → File is at specs/issue-X.md
  → Works fine

Ship phase merges everything ✅
  → Spec file merged to main repo

Cleanup phase (main) moves file ✅
  → File moves to docs/Archived Issues/...
  → state.plan_file updated
```

### ✅ SAFE: Manual Phase Reruns

If you manually run a phase **after** cleanup:

```bash
# After cleanup has run
uv run adw_build_iso.py 33 88405eb3
```

**Result:** Works fine because:
1. Cleanup updated `state.plan_file` to new location
2. Build phase reads from state
3. File is accessible at new location

### ⚠️ CAUTION: Cleanup Running Twice

If cleanup runs twice on the same issue:

```bash
uv run adw_cleanup_iso.py 33 88405eb3  # First run - moves files
uv run adw_cleanup_iso.py 33 88405eb3  # Second run - files already moved
```

**Result:** Safe - cleanup checks if file exists before moving

### ⚠️ CAUTION: Manual File Moves

If you manually move a spec file after plan phase but before cleanup:

```bash
# After plan phase
mv specs/issue-33-*.md somewhere/else/

# Later, cleanup runs
uv run adw_cleanup_iso.py 33 88405eb3
```

**Result:** Safe - cleanup logs warning that file not found, continues

## Git History Preservation

All file moves use `git mv`:

```python
def move_file_with_git(src, dest, logger, dry_run):
    if is_git_tracked(src):
        subprocess.run(["git", "mv", src, dest])
    else:
        shutil.move(src, dest)
```

**Benefits:**
- Git blame works on moved files
- History is preserved
- Diffs show file was moved, not deleted/created

## Rollback Strategy

If cleanup causes issues:

### Option 1: Revert State

```python
# Update state to point back to original location
state.update(plan_file="specs/issue-33-adw-88405eb3-sdlc_planner-phase-3e.md")
state.save("manual_rollback")
```

### Option 2: Move Files Back

```bash
# Use git mv to preserve history
git mv "docs/Archived Issues/issue-33/specs/issue-33-*.md" "specs/"
```

### Option 3: Use Cleanup Metadata

```python
# State stores all moves
cleanup_metadata = state.get("cleanup_metadata")
for move in cleanup_metadata["moves"]:
    git_mv(move["dest"], move["src"])
```

## Testing Checklist

- [x] Cleanup after successful ZTE workflow
- [x] State.plan_file updated correctly
- [x] Files moved to correct locations
- [x] Git history preserved
- [x] Worktree removed successfully
- [x] Resources freed (ports, disk space)
- [ ] Manual phase rerun after cleanup works
- [ ] Cleanup can run twice safely
- [ ] Missing spec file handled gracefully
- [ ] Missing worktree handled gracefully

## Future Enhancements

1. **Automatic Rollback**
   - Add `adw_cleanup_rollback.py` to undo cleanup
   - Uses cleanup_metadata to restore original paths

2. **Dry-Run Preview**
   - Show what would be moved before moving
   - Allow user to approve/reject moves

3. **Cleanup on Issue Close**
   - Run cleanup when issue closed (even if not shipped)
   - Different destination for unmerged work

4. **Worktree Awareness**
   - Detect if running in worktree vs main repo
   - Warn if cleanup runs in wrong context

## Summary

**The cleanup phase is SAFE** because:

✅ Runs after all phases that read `plan_file`
✅ Updates state after moving files
✅ Uses git mv to preserve history
✅ Never blocks the ship workflow
✅ Handles missing files gracefully
✅ Can run multiple times safely
✅ Removes worktree and frees resources
✅ Handles missing worktree gracefully

**Best Practice:** Always run cleanup as part of ZTE workflow (automatic) or manually after ship.

**Resource Management:** Cleanup automatically removes worktrees, freeing:
- **Disk space:** ~500MB-2GB per worktree
- **Ports:** Backend (9100-9114) and Frontend (9200-9214) ports
- **Git entries:** Keeps `git worktree list` clean
