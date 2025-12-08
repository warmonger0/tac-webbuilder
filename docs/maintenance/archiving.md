# Session Archiving System

**Status:** ✅ Implemented
**Version:** 1.0
**Last Updated:** 2025-12-08

## Overview

The Session Archiving System automatically organizes completed session documentation, moves files to appropriate archives, maintains a searchable archive index, and keeps the project root clean while preserving historical records.

## Key Features

- **Automatic Archiving**: Triggered when sessions are marked complete in Plans Panel
- **Smart Detection**: Identifies session files based on naming patterns and completion status
- **Organized Structure**: Year-based organization with separate categories
- **Archive Index**: Auto-generated searchable index of all archived sessions
- **Cleanup**: Removes old files from root after successful archiving
- **Manual Control**: CLI for manual archiving and dry-run testing

## Architecture

### Directory Structure

```
archives/
├── sessions/           # Session documentation
│   ├── 2025/
│   │   ├── SESSION_1_2025-12-06.md
│   │   ├── SESSION_1.5_2025-12-06.md
│   │   └── ...
│   └── 2026/
├── reports/           # Reports, summaries, audits
│   ├── 2025/
│   │   ├── SESSION_1_AUDIT_REPORT_2025-12-06.md
│   │   ├── SESSION_3_COMPLETION_SUMMARY_2025-12-07.md
│   │   └── ...
│   └── 2026/
├── prompts/           # Session prompts
│   ├── 2025/
│   │   ├── SESSION_1_PROMPT_2025-12-06.md
│   │   └── ...
│   └── 2026/
├── tracking/          # Tracking handoff documents
│   ├── TRACKING_HANDOFF_SESSION1_2025-12-06.md
│   └── TRACKING_HANDOFF_SESSION2_2025-12-07.md
└── ARCHIVE_INDEX.md   # Auto-generated index
```

### Components

#### 1. SessionArchiver Class (`scripts/archive_sessions.py`)

Main archiving engine with the following responsibilities:

- **File Detection**: Scans project root for archivable session files
- **Categorization**: Determines correct archive location based on file type
- **Archiving**: Moves files with date suffix if needed
- **Index Generation**: Creates searchable ARCHIVE_INDEX.md
- **Cleanup**: Removes old files after successful archiving

#### 2. Post-Session Hook (`scripts/post_session_hook.sh`)

Bash script triggered automatically when a session is marked complete:

- Archives session files
- Updates archive index
- Commits changes to git (optional)

#### 3. PlannedFeaturesService Integration

`app/server/services/planned_features_service.py` triggers the post-session hook when:
- Status changes to `completed`
- Feature type is `session`
- Session number is present

## File Detection Rules

### Archivable Patterns

Files matching these patterns are candidates for archiving:

- `SESSION_*.md` - Session documentation
- `TRACKING_*.md` - Tracking handoff documents
- `*_PROMPT.md` - Session prompts
- `*_REPORT.md` - Session reports
- `*_COMPLETION*.md` - Completion summaries
- `*_ANALYSIS*.md` - Analysis documents
- `*_SUMMARY*.md` - Summary documents
- `*_AUDIT*.md` - Audit reports

### Exclusion Rules

Files are **NOT** archived if:

1. **Keep in Root**: Listed in `KEEP_IN_ROOT` patterns
   - `README.md`, `CLAUDE.md`
   - Directories: `.claude/`, `docs/`, `app/`, etc.

2. **Current Tracking**: Most recent `TRACKING_HANDOFF*.md` file (stays active)

3. **Incomplete Sessions**: Session prompts without corresponding completion reports

### Categorization Logic

```python
if 'PROMPT' in filename:
    category = 'prompts'
elif any(kw in filename for kw in ['REPORT', 'COMPLETION', 'SUMMARY', 'AUDIT', 'ANALYSIS']):
    category = 'reports'
elif filename.startswith('SESSION_'):
    category = 'sessions'
elif filename.startswith('TRACKING_'):
    category = 'tracking'
else:
    category = 'misc'
```

## Automatic Archiving

### Trigger Flow

```
User marks session complete in Plans Panel (Panel 5)
    ↓
PlannedFeaturesService.update() called with status='completed'
    ↓
_trigger_post_session_hook() spawns background process
    ↓
scripts/post_session_hook.sh executes
    ↓
1. Archive session files (--session N --archive)
2. Update archive index (--update-index)
3. Commit changes to git (optional)
```

### Example

```bash
# User marks Session 7 complete in UI
# System automatically:
1. Archives all SESSION_7_*.md files
2. Moves TRACKING_HANDOFF_SESSION7.md to archives/tracking/
3. Updates ARCHIVE_INDEX.md
4. Commits: "Archive Session 7 documentation"
```

## Manual Archiving

### CLI Usage

```bash
# Scan for archivable files
python scripts/archive_sessions.py --scan

# Dry run (show what would be archived)
python scripts/archive_sessions.py --archive --dry-run

# Archive all eligible files
python scripts/archive_sessions.py --archive

# Archive specific session
python scripts/archive_sessions.py --session 7 --archive

# Update archive index only
python scripts/archive_sessions.py --update-index

# Cleanup old files (30+ days)
python scripts/archive_sessions.py --cleanup 30
```

### CLI Output Example

```
================================================================================
SESSION ARCHIVING SCAN
================================================================================

ARCHIVABLE FILES (12 found)

Prompts (4):
  - SESSION_7_PROMPT.md → archives/prompts/2025/
  - SESSION_8_PROMPT.md → archives/prompts/2025/

Reports (3):
  - SESSION_7_COMPLETION_SUMMARY.md → archives/reports/2025/
  - SESSION_8_AUDIT_REPORT.md → archives/reports/2025/

Tracking (2):
  - TRACKING_HANDOFF_SESSION7.md → archives/tracking/

NOT ARCHIVING (active):
  - TRACKING_HANDOFF_SESSION9.md (current tracking)
  - SESSION_10_PROMPT.md (incomplete session)

Run with --archive to move files
```

## Archive Index

### ARCHIVE_INDEX.md Structure

Auto-generated index with:

1. **Last Updated**: Timestamp of index generation
2. **Sessions by Year**: Organized list of all archived sessions
3. **Statistics**: Totals and date ranges
4. **Search Guide**: Examples of how to search archives

### Example Index Entry

```markdown
#### Session 7: Pattern Review System
- **Date:** 2025-12-07
- **Files:**
  - Sessions: [SESSION_7_2025-12-07.md](sessions/2025/SESSION_7_2025-12-07.md)
  - Reports: [SESSION_7_COMPLETION_SUMMARY_2025-12-07.md](reports/2025/SESSION_7_COMPLETION_SUMMARY_2025-12-07.md)
  - Prompts: [SESSION_7_PROMPT_2025-12-07.md](prompts/2025/SESSION_7_PROMPT_2025-12-07.md)
```

## Searching Archives

### Command-Line Search

```bash
# Full-text search across all archives
grep -r "pattern detection" archives/

# Find files for specific session
find archives/ -name "*SESSION_7*"

# List all files in a year
ls archives/sessions/2025/

# Search within specific category
grep -r "ADW" archives/reports/2025/

# Case-insensitive search
grep -ri "observability" archives/
```

### Search by Date Range

```bash
# Files from December 2025
find archives/ -name "*2025-12-*"

# Files modified in last 30 days
find archives/ -mtime -30 -type f
```

## Cleanup Policy

### Automatic Cleanup

Old files are removed from project root if:

1. File is older than specified days (default: 30)
2. File has been successfully archived
3. File matches archivable patterns

### Manual Cleanup

```bash
# Remove archived files older than 30 days from root
python scripts/archive_sessions.py --cleanup 30

# Dry-run to see what would be removed
python scripts/archive_sessions.py --cleanup 30 --dry-run
```

## Date Handling

### Date Extraction

Dates are extracted in priority order:

1. **From Filename**: `YYYY-MM-DD` pattern in filename
2. **From File Metadata**: File modification time

### Date Suffix Addition

Files without dates in filename get date suffix added during archiving:

```
Before: SESSION_7_PROMPT.md
After:  SESSION_7_PROMPT_2025-12-07.md
```

## Error Handling

### Non-Blocking Operations

- Post-session hook runs in background (non-blocking)
- Hook failures don't prevent session completion
- Errors logged but don't crash service

### Name Conflicts

If file with same name exists in archive:

```python
# Original
SESSION_1_REPORT_2025-12-06.md

# Conflict - adds counter
SESSION_1_REPORT_2025-12-06_1.md
```

### Missing Completion Reports

Sessions without completion reports are flagged as incomplete:

```
NOT ARCHIVING (active):
  - SESSION_10_PROMPT.md (incomplete session)
```

## Testing

### Test Suite

Location: `scripts/tests/test_archive_sessions.py`

**Coverage:**
- File detection and scanning
- Categorization logic
- Date extraction
- Archiving (dry-run and actual)
- Index generation
- Cleanup operations
- Current tracking detection
- Incomplete session detection

### Running Tests

```bash
# Run all archiving tests
pytest scripts/tests/test_archive_sessions.py -v

# Run specific test
pytest scripts/tests/test_archive_sessions.py::TestSessionArchiver::test_scan_for_archivable_files -v
```

## Git Integration

### Automatic Commits

When post-session hook runs with git repository:

```bash
git add archives/
git commit -m "Archive Session N documentation

Automatically archived by post-session hook:
- Session documents moved to archives/
- Archive index updated

Session: N
Date: YYYY-MM-DD HH:MM:SS"
```

### Manual Commits

```bash
# After manual archiving
git add archives/
git commit -m "Archive sessions 7-9 documentation"
```

## Monitoring and Logs

### Service Logs

PlannedFeaturesService logs hook triggers:

```
[PlannedFeaturesService] Triggering post-session hook for session 7
[PlannedFeaturesService] Post-session hook triggered successfully
```

### Hook Output

Post-session hook provides detailed output:

```
==========================================
Post-Session Hook: Session 7
==========================================

📦 Archiving session files...
✅ Session files archived successfully

📝 Updating archive index...
✅ Archive index updated

🔍 Checking for git changes...
📝 Committing archive changes...
✅ Changes committed to git

==========================================
✅ Session 7 archived successfully
==========================================
```

## Best Practices

### 1. Regular Index Updates

Update archive index after manual file moves:

```bash
python scripts/archive_sessions.py --update-index
```

### 2. Dry-Run Before Archiving

Always test with dry-run first:

```bash
python scripts/archive_sessions.py --archive --dry-run
```

### 3. Backup Before Cleanup

Backup archives before running cleanup:

```bash
tar -czf archives_backup_$(date +%Y%m%d).tar.gz archives/
python scripts/archive_sessions.py --cleanup 30
```

### 4. Keep Current Tracking

Never manually archive the most recent `TRACKING_HANDOFF*.md`:
- System automatically excludes current tracking
- Archive previous tracking documents only

### 5. Session Completion Workflow

1. Complete session work
2. Create completion report/summary
3. Mark session complete in Plans Panel
4. System automatically archives
5. Verify in `archives/ARCHIVE_INDEX.md`

## Troubleshooting

### Issue: Files Not Archived

**Check:**
1. Is session marked complete?
2. Does completion report exist?
3. Is file in project root?
4. Does filename match patterns?

**Solution:**
```bash
# Scan to see what's detected
python scripts/archive_sessions.py --scan

# Force archive specific session
python scripts/archive_sessions.py --session 7 --archive
```

### Issue: Hook Not Triggering

**Check:**
1. Is `scripts/post_session_hook.sh` executable?
2. Is path correct in service?
3. Check service logs for errors

**Solution:**
```bash
# Make hook executable
chmod +x scripts/post_session_hook.sh

# Test manually
./scripts/post_session_hook.sh 7
```

### Issue: Index Not Updating

**Check:**
1. Are files actually in archives/?
2. Permissions on ARCHIVE_INDEX.md?

**Solution:**
```bash
# Manually update index
python scripts/archive_sessions.py --update-index
```

### Issue: Duplicate Files

**Check:**
1. Files archived multiple times
2. Name conflicts

**Solution:**
- System automatically adds counters
- Review and remove duplicates manually

## Future Enhancements

### Potential Features

1. **Archive Compression**: Compress older archives (>1 year)
2. **Search UI**: Web interface for searching archives
3. **Export**: Export archives to external storage
4. **Analytics**: Statistics on session durations, patterns
5. **Auto-Tagging**: Extract and tag topics from session content
6. **Archive Expiry**: Automatically move very old files to cold storage

### Configuration File

Future: `archives/config.yaml`

```yaml
archiving:
  auto_archive: true
  cleanup_days: 30
  git_commit: true
  date_format: "%Y-%m-%d"

categories:
  - prompts
  - reports
  - sessions
  - tracking

exclusions:
  - TRACKING_HANDOFF_SESSION*  # Keep latest
  - SESSION_*_PROMPT.md         # If incomplete
```

## Related Documentation

- [Plans Panel](../features/plans-panel.md) - Session management UI
- [Observability](../features/observability-and-logging.md) - Logging and monitoring
- [Pattern Review System](../features/pattern-review.md) - Pattern learning integration

## Summary

The Session Archiving System provides:

✅ **Automatic Organization** - Files archived when sessions complete
✅ **Clean Project Root** - Documentation moved to structured archives
✅ **Searchable History** - Archive index for easy navigation
✅ **Manual Control** - CLI for manual archiving and testing
✅ **Git Integration** - Automatic commits of archived files
✅ **Non-Blocking** - Archiving doesn't slow down development

This ensures a clean, organized project while preserving all historical session documentation for future reference.
