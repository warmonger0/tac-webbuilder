# Task: Auto-Archiving System

## Context
I'm working on the tac-webbuilder project. After 14 sessions, numerous session prompts and reports have accumulated. This final session implements an auto-archiving system that automatically organizes completed session documentation, cleans up old files, and maintains a clean documentation structure without manual intervention.

## Objective
Create an automated archiving system that detects completed sessions, moves documentation to appropriate archives, maintains an archive index, and keeps the project root clean while preserving historical records.

## Background Information
- **Current State:** Session prompts, reports, and tracking docs accumulate in project root
- **Problem:** Manual archiving is tedious and easy to forget
- **Solution:** Automated system triggered after session completion
- **Output:** Organized archive structure, clean project root, searchable index

---

## Implementation Steps

### Step 1: Archive Directory Structure (20 min)

**Create directory structure:**
```bash
mkdir -p archives/sessions/{2025,2026}
mkdir -p archives/reports/{2025,2026}
mkdir -p archives/prompts/{2025,2026}
mkdir -p archives/tracking
```

**Structure:**
```
archives/
├── sessions/
│   └── 2025/
│       ├── SESSION_1_2025-12-06.md
│       ├── SESSION_1.5_2025-12-06.md
│       └── ...
├── reports/
│   └── 2025/
│       ├── SESSION_1_AUDIT_REPORT_2025-12-06.md
│       └── ...
├── prompts/
│   └── 2025/
│       ├── SESSION_1_PROMPT_2025-12-06.md
│       └── ...
├── tracking/
│   ├── TRACKING_HANDOFF_SESSION3_2025-12-07.md
│   └── ...
└── ARCHIVE_INDEX.md
```

---

### Step 2: Archiving Service (60 min)

**Create:** `scripts/archive_sessions.py` (~300 lines)

**Template:** See `.claude/templates/CLI_TOOL.md`

**Key Functions:**
```python
class SessionArchiver:
    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.archive_root = self.root / 'archives'

    def scan_for_archivable_files(self) -> List[Path]
    def categorize_file(self, filepath: Path) -> str
    def archive_file(self, filepath: Path, category: str)
    def update_archive_index(self)
    def generate_archive_report(self) -> str
```

**File Detection:**
```python
def scan_for_archivable_files(self) -> List[Path]:
    """Find session files in project root."""
    patterns = [
        'SESSION_*.md',
        'TRACKING_*.md',
        '*_PROMPT.md',
        '*_REPORT.md',
        '*_COMPLETION*.md',
        '*_ANALYSIS*.md'
    ]

    archivable = []
    for pattern in patterns:
        archivable.extend(self.root.glob(pattern))

    # Filter out current tracking and active session prompts
    return [f for f in archivable if self._is_archivable(f)]

def _is_archivable(self, filepath: Path) -> bool:
    """Check if file should be archived."""
    # Don't archive current tracking document
    if 'TRACKING_HANDOFF' in filepath.name and not self._is_old_tracking(filepath):
        return False

    # Don't archive session prompts for incomplete sessions
    if 'PROMPT' in filepath.name and self._is_incomplete_session(filepath):
        return False

    return True
```

**File Categorization:**
```python
def categorize_file(self, filepath: Path) -> str:
    """Determine archive category."""
    name = filepath.name

    if name.startswith('SESSION_') and 'PROMPT' in name:
        return 'prompts'
    elif name.startswith('SESSION_') and 'REPORT' in name:
        return 'reports'
    elif name.startswith('SESSION_'):
        return 'sessions'
    elif name.startswith('TRACKING_'):
        return 'tracking'
    else:
        return 'misc'
```

**Archiving Logic:**
```python
def archive_file(self, filepath: Path, category: str):
    """Move file to appropriate archive location."""
    # Extract date from filename or use file modification time
    file_date = self._extract_date(filepath)
    year = file_date.year

    # Determine destination
    dest_dir = self.archive_root / category / str(year)
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Add date suffix if not present
    if not re.search(r'\d{4}-\d{2}-\d{2}', filepath.name):
        new_name = filepath.stem + f'_{file_date.strftime("%Y-%m-%d")}' + filepath.suffix
    else:
        new_name = filepath.name

    dest_file = dest_dir / new_name

    # Move file
    shutil.move(str(filepath), str(dest_file))
    return dest_file
```

---

### Step 3: Archive Index (30 min)

**Auto-generate:** `archives/ARCHIVE_INDEX.md`

**Index Structure:**
```markdown
# Session Archive Index

Last updated: 2025-12-08 15:30:00

## Sessions by Year

### 2025 (8 sessions)

#### Session 1: Pattern Detection Audit
- **Date:** 2025-12-06
- **Duration:** 2 hours
- **Files:**
  - Session: [SESSION_1_2025-12-06.md](sessions/2025/SESSION_1_2025-12-06.md)
  - Report: [SESSION_1_AUDIT_REPORT_2025-12-06.md](reports/2025/SESSION_1_AUDIT_REPORT_2025-12-06.md)
  - Prompt: [SESSION_1_PROMPT_2025-12-06.md](prompts/2025/SESSION_1_PROMPT_2025-12-06.md)

... (similar entries for other sessions)

## Statistics

- Total sessions archived: 14
- Total files archived: 42
- Date range: 2025-12-06 to 2025-12-08
- Total session time: 49 hours

## Search

To find specific content:
```bash
grep -r "pattern detection" archives/
```
```

**Index Generation:**
```python
def update_archive_index(self):
    """Generate ARCHIVE_INDEX.md with all archived files."""
    index_content = "# Session Archive Index\n\n"
    index_content += f"Last updated: {datetime.now()}\n\n"

    # Group files by year and category
    archived_files = self._scan_archive()
    sessions = self._extract_session_info(archived_files)

    # Generate index sections
    index_content += self._generate_year_sections(sessions)
    index_content += self._generate_statistics(sessions)
    index_content += self._generate_search_guide()

    # Write index
    index_file = self.archive_root / 'ARCHIVE_INDEX.md'
    index_file.write_text(index_content)
```

---

### Step 4: CLI Interface (30 min)

**Arguments:**
```python
parser.add_argument('--scan', action='store_true',
                   help='Scan for archivable files')
parser.add_argument('--archive', action='store_true',
                   help='Archive files (moves to archives/)')
parser.add_argument('--dry-run', action='store_true',
                   help='Show what would be archived')
parser.add_argument('--update-index', action='store_true',
                   help='Update ARCHIVE_INDEX.md')
parser.add_argument('--session', type=int,
                   help='Archive specific session number')
```

**Output Format:**
```
================================================================================
SESSION ARCHIVING SCAN
================================================================================

ARCHIVABLE FILES (12 found)

Prompts (4):
  - SESSION_1_PROMPT.md → archives/prompts/2025/
  - SESSION_1.5_PROMPT.md → archives/prompts/2025/
  - SESSION_2_PROMPT.md → archives/prompts/2025/
  - SESSION_3_PROMPT.md → archives/prompts/2025/

Reports (3):
  - SESSION_1_AUDIT_REPORT.md → archives/reports/2025/
  - SESSION_1.5_PATTERN_ANALYSIS_REPORT.md → archives/reports/2025/
  - SESSION_3_COMPLETION_SUMMARY.md → archives/reports/2025/

Tracking (2):
  - TRACKING_HANDOFF_SESSION1.md → archives/tracking/
  - TRACKING_HANDOFF_SESSION2.md → archives/tracking/

NOT ARCHIVING (active):
  - TRACKING_HANDOFF_SESSION3.md (current tracking)
  - SESSION_9_PROMPT.md (incomplete session)
  - SESSION_10_PROMPT.md (incomplete session)

Run with --archive to move files
```

---

### Step 5: Post-Session Hook (30 min)

**Create:** `scripts/post_session_hook.sh` (~80 lines)

**Hook triggers after session completion:**
```bash
#!/bin/bash
# Post-Session Hook - Auto-archive after completion
# Called when a session is marked complete in the database

set -e

SESSION_NUMBER=$1

if [ -z "$SESSION_NUMBER" ]; then
    echo "Usage: $0 <session_number>"
    exit 1
fi

PROJECT_ROOT="/path/to/tac-webbuilder"
cd "$PROJECT_ROOT"

echo "Post-session hook triggered for Session $SESSION_NUMBER"

# Archive session files
echo "Archiving session files..."
python scripts/archive_sessions.py --session "$SESSION_NUMBER" --archive

# Update archive index
echo "Updating archive index..."
python scripts/archive_sessions.py --update-index

# Commit changes (optional)
if [ -d ".git" ]; then
    git add archives/
    git commit -m "Archive Session $SESSION_NUMBER documentation"
fi

echo "Session $SESSION_NUMBER archived successfully"
```

**Integration with PlannedFeaturesService:**
```python
# In planned_features_service.py, when status changes to 'completed'
def update(self, feature_id: int, update_data: PlannedFeatureUpdate):
    # ... existing update logic ...

    # Trigger post-session hook if session completed
    if update_data.status == 'completed' and feature.session_number:
        self._trigger_post_session_hook(feature.session_number)

def _trigger_post_session_hook(self, session_number: int):
    """Trigger archiving after session completion."""
    import subprocess
    hook_path = Path(__file__).parent.parent.parent / 'scripts' / 'post_session_hook.sh'
    if hook_path.exists():
        subprocess.run([str(hook_path), str(session_number)], check=False)
```

---

### Step 6: Archive Cleanup Rules (20 min)

**Add to archive_sessions.py:**

**Cleanup Policy:**
```python
KEEP_IN_ROOT = [
    'README.md',
    'CLAUDE.md',
    '.claude/',
    'docs/',
    'app/',
    'scripts/',
    'archives/',
    # Current tracking (latest)
    'TRACKING_HANDOFF_SESSION*.md'  # Only keep latest
]

def cleanup_old_files(self, days_old=30):
    """Remove old files from root after archiving."""
    # Find old archived files still in root
    # (files that were archived but not deleted)
    cutoff_date = datetime.now() - timedelta(days=days_old)

    for filepath in self.root.glob('SESSION_*.md'):
        if filepath.stat().st_mtime < cutoff_date.timestamp():
            if self._is_archived(filepath):
                print(f"Removing old archived file: {filepath}")
                filepath.unlink()
```

---

### Step 7: Tests (30 min)

**Create:** `scripts/tests/test_archive_sessions.py` (~100 lines)

**Template:** See `.claude/templates/PYTEST_TESTS.md`

**Test Cases:**
1. `test_scan_for_archivable_files` - File detection
2. `test_categorize_file` - Category assignment
3. `test_archive_file` - File movement
4. `test_update_archive_index` - Index generation
5. `test_dry_run` - No files moved in dry-run mode

**Run tests:**
```bash
pytest scripts/tests/test_archive_sessions.py -v
```

---

### Step 8: Documentation (20 min)

**Create:** `docs/maintenance/archiving.md` (~150 lines)

**Sections:**
- Overview and archive structure
- Automatic archiving process
- Manual archiving with CLI
- Archive index usage
- Search and retrieval
- Cleanup policies

---

## Success Criteria

- ✅ Archive directory structure created
- ✅ Archiving script detects and categorizes session files
- ✅ Archive index auto-generates with file listings
- ✅ Post-session hook triggers automatic archiving
- ✅ CLI supports manual archiving and dry-run
- ✅ Old files cleaned up after archiving
- ✅ Tests passing (5/5)
- ✅ Documentation complete

---

## Files Expected to Change

**Created (6):**
- `scripts/archive_sessions.py` (~300 lines)
- `scripts/post_session_hook.sh` (~80 lines)
- `scripts/tests/test_archive_sessions.py` (~100 lines)
- `archives/ARCHIVE_INDEX.md` (auto-generated)
- `docs/maintenance/archiving.md` (~150 lines)

**Modified (1):**
- `app/server/services/planned_features_service.py` (add post-session hook trigger)

**Archive Structure Created:**
- `archives/sessions/{year}/`
- `archives/reports/{year}/`
- `archives/prompts/{year}/`
- `archives/tracking/`

---

## Quick Reference

**Run CLI:**
```bash
# Scan for archivable files
python scripts/archive_sessions.py --scan

# Dry run (show what would be archived)
python scripts/archive_sessions.py --archive --dry-run

# Archive all eligible files
python scripts/archive_sessions.py --archive

# Archive specific session
python scripts/archive_sessions.py --session 7 --archive

# Update index
python scripts/archive_sessions.py --update-index
```

**Manual archive:**
```bash
# Archive specific session manually
bash scripts/post_session_hook.sh 7
```

**Search archive:**
```bash
grep -r "pattern detection" archives/
find archives/ -name "*SESSION_7*"
```

**Run tests:**
```bash
pytest scripts/tests/test_archive_sessions.py -v
```

---

## Estimated Time

- Step 1 (Directory Structure): 20 min
- Step 2 (Archiving Service): 60 min
- Step 3 (Archive Index): 30 min
- Step 4 (CLI Interface): 30 min
- Step 5 (Post-Session Hook): 30 min
- Step 6 (Cleanup Rules): 20 min
- Step 7 (Tests): 30 min
- Step 8 (Docs): 20 min

**Total: 2-3 hours**

---

## Session Completion Template

```markdown
## ✅ Session 14 Complete - Auto-Archiving System

**Duration:** ~X hours
**Status:** Complete ✅
**Next:** All 14 sessions complete! 🎉

### What Was Done
- Auto-archiving system with post-session hooks
- Archive directory structure (sessions, reports, prompts, tracking)
- Archive index with searchable file listings
- CLI tool for manual and automatic archiving
- Post-session hook integration
- 5/5 tests passing

### Key Results
- Archived X session files
- Archive index generated with Y entries
- Post-session hook triggers automatic archiving
- Project root cleaned up
- Historical documentation preserved and organized

### Files Changed
**Created (6):**
- scripts/archive_sessions.py
- scripts/post_session_hook.sh
- scripts/tests/test_archive_sessions.py
- archives/ARCHIVE_INDEX.md
- docs/maintenance/archiving.md

**Modified (1):**
- services/planned_features_service.py

### 🎉 Roadmap Complete!

All 14 sessions completed:
1. ✅ Pattern Audit
2. ✅ Pattern Cleanup
3. ✅ Port Pool
4. ✅ Integration Checklist (Plan)
5. ✅ Integration Validator (Ship)
6. ✅ Verify Phase
7. ✅ Pattern Review System
8. ✅ Daily Pattern Analysis
9. ✅ Plans Panel Migration (8A + 8B)
10. ✅ Cost Attribution Analytics
11. ✅ Error Analytics
12. ✅ Latency Analytics
13. ✅ Closed-Loop ROI Tracking
14. ✅ Confidence Updating System
15. ✅ Auto-Archiving System

**Total time:** ~49 hours across 14 sessions
**System status:** Production-ready with full observability and automation
```
