# Database Snapshot Strategy (Local Only)

## Overview
Database snapshots are kept **locally only** (not pushed to GitHub) to keep the repository clean and fast.

## Current Snapshots

- `workflow_history.db` - Current active database
- `workflow_history.db.session5` - After Session 5 (Verify phase complete)
- `workflow_history.db.session10` - After Session 10 (Analytics complete) - *future*
- `workflow_history.db.session14` - After Session 14 (Final state) - *future*
- `workflow_history.db.baseline` - Clean initial state - *create when needed*

## Creating Snapshots

**After completing a major session milestone:**
```bash
cp app/server/db/workflow_history.db app/server/db/workflow_history.db.sessionX
```

**Create baseline (clean state with no data):**
```bash
cp app/server/db/workflow_history.db app/server/db/workflow_history.db.baseline
```

## Restoring from Snapshot

```bash
# Restore to Session 5 state
cp app/server/db/workflow_history.db.session5 app/server/db/workflow_history.db

# Verify
sqlite3 app/server/db/workflow_history.db "SELECT COUNT(*) FROM workflow_history"
```

## Backup Strategy

**Local Snapshots are NOT backed up to GitHub.**

Recommended backup methods:
1. **Time Machine** - Automatic macOS backups
2. **iCloud Drive** - Manual copy to iCloud
3. **External Drive** - Weekly sync

**Weekly Backup to External Drive:**
```bash
# One-time setup
mkdir -p /Volumes/Backup/tac-webbuilder-db-snapshots/

# Weekly sync (run this every week)
rsync -av app/server/db/*.session* /Volumes/Backup/tac-webbuilder-db-snapshots/
rsync -av app/server/db/*.baseline /Volumes/Backup/tac-webbuilder-db-snapshots/
```

## Why Local Only?

- **Fast GitHub operations** - Clone, pull, push remain fast
- **No size limits** - Can store unlimited snapshots
- **Solo project** - Only collaborator is Claude
- **Privacy** - DB may contain API usage data

## Snapshot Schedule

Create snapshots at these milestones:
- ✅ Session 5: Verify phase complete (60MB)
- 📋 Session 10: Analytics complete (~70MB estimated)
- 📋 Session 14: Final observability state (~80MB estimated)
- 📋 Baseline: Clean state with sample data (~10MB)

**Total storage: ~220MB** (easily fits on laptop)

## Comparing Snapshots

```bash
# Check size differences
ls -lh app/server/db/*.session*

# Compare data counts
for db in app/server/db/*.session*; do
    echo "=== $db ==="
    sqlite3 "$db" "SELECT COUNT(*) FROM workflow_history"
    sqlite3 "$db" "SELECT COUNT(*) FROM pattern_occurrences"
done
```

## Recovery from Loss

If laptop dies and snapshots are lost:
- **Code:** Recoverable from GitHub ✅
- **Snapshots:** LOST ❌ (unless backed up externally)

**Mitigation:** Run weekly backup to external drive (see above)
