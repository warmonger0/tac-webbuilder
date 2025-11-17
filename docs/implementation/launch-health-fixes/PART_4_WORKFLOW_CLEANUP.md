# Part 4: Workflow Cleanup

**Priority: LOW**
**Duration: 20 minutes**
**Impact: Eliminates GitHub API warnings for invalid workflows**

---

## 🎯 Objective

Remove old workflow directories with invalid issue numbers (test data, deleted issues) to eliminate GitHub API warnings during synchronization.

---

## 📊 Current Problem

### What's Happening
```bash
# Current sync output
[WARNING] Could not check status for issue #999
[WARNING] Could not check status for issue #6
[WARNING] Could not check status for issue #13
[WARNING] Skipping workflow 3358badd with invalid issue_number: base
```

### Why It's Happening
- Old test workflows exist with fake issue numbers (999)
- Workflows reference deleted GitHub issues (6, 13)
- Some workflows have invalid issue numbers ("base" instead of integer)
- These directories persist even after issues are closed/deleted

### Impact
- Warning messages during every sync
- Health check tries to validate invalid workflows
- Confusing diagnostic output
- Database contains stale records

---

## 🔧 Technical Details

### Workflow Directory Structure
```
agents/
├── adw-c8499e43-workflow-history-panel/
│   ├── adw_state.json               # Contains issue_number
│   ├── raw_output.jsonl
│   └── ...
├── adw-32658917-workflow-history-panel/
│   ├── adw_state.json
│   └── ...
└── adw-test-999-debug/              # Invalid (issue #999)
    ├── adw_state.json               # {"issue_number": 999}
    └── ...
```

### Valid vs Invalid Workflows

**Valid Workflow:**
```json
// agents/adw-c8499e43-*/adw_state.json
{
  "adw_id": "c8499e43",
  "issue_number": 8,
  "status": "completed",
  "created_at": "2025-11-16T10:30:00"
}
```

**Invalid Workflow (Test Data):**
```json
// agents/adw-test-999-*/adw_state.json
{
  "adw_id": "test-999",
  "issue_number": 999,  // Doesn't exist in GitHub
  "status": "completed"
}
```

**Invalid Workflow (Non-numeric):**
```json
// agents/adw-3358badd-*/adw_state.json
{
  "adw_id": "3358badd",
  "issue_number": "base",  // Not a number!
  "status": "completed"
}
```

### Sync Process

**File:** `app/server/core/workflow_history.py:150-170`
```python
def sync_workflow_to_db(adw_state_path):
    # Read adw_state.json
    state = json.load(open(adw_state_path))
    issue_num = state.get("issue_number")

    # Try to verify issue exists
    try:
        gh_issue = check_github_issue(issue_num)  # <- Fails for invalid
    except:
        logger.warning(f"Could not check status for issue #{issue_num}")
```

---

## 📝 Implementation

### Create Cleanup Script

**File:** `/Users/Warmonger0/tac/tac-webbuilder/scripts/cleanup_invalid_workflows.sh`

```bash
#!/bin/bash
# Clean up workflow directories with invalid issue numbers

set -euo pipefail

AGENTS_DIR="/Users/Warmonger0/tac/tac-webbuilder/agents"
REMOVED_COUNT=0
KEPT_COUNT=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Workflow Directory Cleanup ===${NC}\n"

# Check if agents directory exists
if [ ! -d "$AGENTS_DIR" ]; then
    echo -e "${RED}Error: agents/ directory not found${NC}"
    exit 1
fi

# Find all ADW directories
for adw_dir in "$AGENTS_DIR"/adw-*; do
    if [ ! -d "$adw_dir" ]; then
        continue
    fi

    dir_name=$(basename "$adw_dir")
    state_file="$adw_dir/adw_state.json"

    # Check if state file exists
    if [ ! -f "$state_file" ]; then
        echo -e "${YELLOW}⚠️  No state file: $dir_name${NC}"
        echo -e "   ${YELLOW}Removing (no state file)${NC}"
        rm -rf "$adw_dir"
        REMOVED_COUNT=$((REMOVED_COUNT + 1))
        continue
    fi

    # Extract issue number
    issue_num=$(jq -r '.issue_number // empty' "$state_file" 2>/dev/null || echo "")

    # Validate issue number
    is_invalid=false

    # Check 1: Empty or missing
    if [ -z "$issue_num" ]; then
        echo -e "${RED}❌ Invalid (no issue_number): $dir_name${NC}"
        is_invalid=true

    # Check 2: Not a number
    elif ! [[ "$issue_num" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}❌ Invalid (non-numeric: $issue_num): $dir_name${NC}"
        is_invalid=true

    # Check 3: Known test numbers
    elif [ "$issue_num" = "999" ] || [ "$issue_num" = "6" ] || [ "$issue_num" = "13" ]; then
        echo -e "${RED}❌ Invalid (test/deleted issue #$issue_num): $dir_name${NC}"
        is_invalid=true

    # Check 4: Verify with GitHub (optional)
    # Uncomment to enable GitHub API validation
    # elif ! gh issue view "$issue_num" >/dev/null 2>&1; then
    #     echo -e "${RED}❌ Invalid (issue #$issue_num not found in GitHub): $dir_name${NC}"
    #     is_invalid=true
    fi

    # Remove if invalid
    if [ "$is_invalid" = true ]; then
        echo -e "   ${YELLOW}Removing: $adw_dir${NC}"
        rm -rf "$adw_dir"
        REMOVED_COUNT=$((REMOVED_COUNT + 1))
    else
        echo -e "${GREEN}✅ Valid (issue #$issue_num): $dir_name${NC}"
        KEPT_COUNT=$((KEPT_COUNT + 1))
    fi
done

# Summary
echo -e "\n${YELLOW}=== Cleanup Summary ===${NC}"
echo -e "${GREEN}✅ Kept: $KEPT_COUNT workflows${NC}"
echo -e "${RED}❌ Removed: $REMOVED_COUNT workflows${NC}"

# Update database (remove orphaned records)
if [ $REMOVED_COUNT -gt 0 ]; then
    echo -e "\n${YELLOW}Cleaning up database records...${NC}"
    sqlite3 app/server/db/workflow_history.db << EOF
DELETE FROM workflow_history
WHERE adw_id NOT IN (
    SELECT json_extract(json(adw_state), '$.adw_id')
    FROM (
        SELECT readfile(path || '/adw_state.json') as adw_state
        FROM (
            SELECT '$AGENTS_DIR/' || name || '/' as path, name
            FROM (
                SELECT name FROM pragma_file_list('$AGENTS_DIR')
                WHERE type = 'dir' AND name LIKE 'adw-%'
            )
        )
    )
);
EOF
    echo -e "${GREEN}✅ Database cleaned up${NC}"
fi

echo -e "\n${GREEN}Cleanup complete!${NC}"
```

---

## 🛠️ Step-by-Step Instructions

### Step 1: Create Cleanup Script
```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Create script (use the code above)
cat > scripts/cleanup_invalid_workflows.sh << 'EOF'
#!/bin/bash
# ... (paste the full script from above)
EOF
```

### Step 2: Make Script Executable
```bash
chmod +x scripts/cleanup_invalid_workflows.sh
```

### Step 3: Verify Script
```bash
# Check script syntax
bash -n scripts/cleanup_invalid_workflows.sh
echo "Syntax OK: $?"
```

### Step 4: Dry Run (Preview)
```bash
# See what would be removed (without actually removing)
# Modify script to add echo before rm -rf
```

### Step 5: Run Cleanup
```bash
# Execute cleanup
./scripts/cleanup_invalid_workflows.sh
```

Expected output:
```
=== Workflow Directory Cleanup ===

❌ Invalid (test/deleted issue #999): adw-test-999-debug
   Removing: /Users/.../agents/adw-test-999-debug
❌ Invalid (test/deleted issue #6): adw-old-6-feature
   Removing: /Users/.../agents/adw-old-6-feature
❌ Invalid (non-numeric: base): adw-3358badd-base-branch
   Removing: /Users/.../agents/adw-3358badd-base-branch
✅ Valid (issue #8): adw-c8499e43-workflow-history-panel

=== Cleanup Summary ===
✅ Kept: 20 workflows
❌ Removed: 3 workflows

Cleaning up database records...
✅ Database cleaned up

Cleanup complete!
```

### Step 6: Verify Cleanup
```bash
# List remaining workflows
ls -la agents/

# Check for invalid issue numbers
for dir in agents/adw-*; do
    if [ -f "$dir/adw_state.json" ]; then
        issue=$(jq -r '.issue_number' "$dir/adw_state.json")
        echo "$(basename $dir): Issue #$issue"
    fi
done
```

### Step 7: Test Sync
```bash
# Restart backend to trigger sync
cd app/server
pkill -f "python server.py"
uv run python server.py 2>&1 | grep -i warning

# Should show NO GitHub warnings
```

---

## ✅ Verification

### Expected Results
```bash
# No warnings during sync
./scripts/start.sh 2>&1 | grep -E "WARNING.*issue|invalid issue"
# Should return empty (no matches)
```

### Verify Database
```bash
# Check workflow count
sqlite3 app/server/db/workflow_history.db \
  "SELECT COUNT(*) as total FROM workflow_history;"

# Check for invalid issue numbers
sqlite3 app/server/db/workflow_history.db \
  "SELECT adw_id, issue_number FROM workflow_history
   WHERE issue_number IN (999, 6, 13) OR issue_number IS NULL;"
# Should return empty
```

### Verify GitHub API Calls
```bash
# Monitor GitHub API calls during sync
./scripts/start.sh 2>&1 | grep "Could not check status"
# Should be empty
```

---

## 🧪 Testing

### Unit Test: Issue Number Validation
```bash
# Test validation logic
issue_num="999"
if [[ "$issue_num" =~ ^[0-9]+$ ]]; then
    echo "✅ Numeric"
else
    echo "❌ Not numeric"
fi

# Test with invalid
issue_num="base"
if [[ "$issue_num" =~ ^[0-9]+$ ]]; then
    echo "✅ Numeric"
else
    echo "❌ Not numeric"  # Should print this
fi
```

### Integration Test: Full Cleanup
```bash
# Create test workflow
mkdir -p agents/adw-test-999-debug
echo '{"adw_id": "test-999", "issue_number": 999}' > \
  agents/adw-test-999-debug/adw_state.json

# Run cleanup
./scripts/cleanup_invalid_workflows.sh

# Verify removed
[ ! -d agents/adw-test-999-debug ] && echo "✅ Test workflow removed"
```

### Regression Test: Keep Valid Workflows
```bash
# Count workflows before
before=$(ls -d agents/adw-* 2>/dev/null | wc -l)

# Run cleanup
./scripts/cleanup_invalid_workflows.sh

# Count workflows after
after=$(ls -d agents/adw-* 2>/dev/null | wc -l)

# Verify valid workflows kept
echo "Before: $before, After: $after"
# After should be less than or equal to before
```

---

## 🐛 Troubleshooting

### jq Command Not Found
**Symptom:** `jq: command not found`

**Fix:**
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt install jq

# Verify installation
jq --version
```

---

### Script Removes Valid Workflows
**Symptom:** Accidentally removed workflows for active issues

**Prevention:**
```bash
# Before running cleanup, backup agents directory
cp -r agents agents.backup.$(date +%Y%m%d_%H%M%S)
```

**Recovery:**
```bash
# Restore from backup
rm -rf agents
cp -r agents.backup.20251117_143000 agents
```

---

### Database Still Has Invalid Records
**Symptom:** `SELECT * FROM workflow_history` shows invalid issue numbers

**Fix:**
```bash
# Manually clean up database
sqlite3 app/server/db/workflow_history.db << EOF
DELETE FROM workflow_history
WHERE issue_number IN (999, 6, 13)
   OR issue_number IS NULL
   OR typeof(issue_number) != 'integer';
EOF

# Verify cleanup
sqlite3 app/server/db/workflow_history.db \
  "SELECT COUNT(*) FROM workflow_history;"
```

---

### Warnings Still Appear After Cleanup
**Symptom:** GitHub API warnings persist

**Diagnosis:**
```bash
# Check if invalid workflows still exist
ls agents/ | grep -E "999|test|debug"

# Check state files
for dir in agents/adw-*; do
    if [ -f "$dir/adw_state.json" ]; then
        issue=$(jq -r '.issue_number' "$dir/adw_state.json" 2>/dev/null)
        if [ "$issue" = "999" ]; then
            echo "Found invalid: $dir"
        fi
    fi
done
```

**Fix:**
```bash
# Re-run cleanup script
./scripts/cleanup_invalid_workflows.sh

# Restart backend
pkill -f "python server.py"
cd app/server && uv run python server.py
```

---

## 📊 Before/After Comparison

### Before
```bash
# agents/ directory
agents/
├── adw-c8499e43-workflow-history-panel/    # Valid
├── adw-32658917-workflow-history-panel/    # Valid
├── adw-test-999-debug/                     # Invalid (test)
├── adw-old-6-feature/                      # Invalid (deleted issue)
├── adw-3358badd-base-branch/               # Invalid (non-numeric)
└── ... (20 valid workflows)

# Sync output
[WARNING] Could not check status for issue #999
[WARNING] Could not check status for issue #6
[WARNING] Skipping workflow 3358badd with invalid issue_number: base
```

### After
```bash
# agents/ directory
agents/
├── adw-c8499e43-workflow-history-panel/    # Valid
├── adw-32658917-workflow-history-panel/    # Valid
└── ... (20 valid workflows)

# Sync output
[SYNC] Synchronized 20 workflows successfully
# No warnings!
```

---

## 🎓 Learning Points

### Workflow Lifecycle Management

**Creation:**
1. ADW triggered by GitHub issue
2. Directory created: `agents/adw-{id}-{description}/`
3. State file written: `adw_state.json`
4. Synced to database

**Completion:**
1. Workflow finishes (success/failure)
2. Results written to `raw_output.jsonl`
3. GitHub issue updated
4. Directory remains for history

**Cleanup:**
1. Old workflows accumulate over time
2. Test workflows pollute production data
3. Deleted issues leave orphaned directories
4. Manual/automated cleanup needed

### Best Practices

**1. Use Meaningful Issue Numbers**
- Production: Real GitHub issues (1, 2, 3, ...)
- Test: Use issue #0 or negative numbers (-1, -2, ...)
- Development: Use local-only mode (no GitHub sync)

**2. Cleanup Strategies**
- **Immediate:** Delete failed/test workflows on completion
- **Scheduled:** Weekly/monthly cleanup script
- **Retention:** Keep last 30 days, archive older
- **Manual:** Cleanup before major releases

**3. Database Consistency**
- Sync filesystem → database regularly
- Detect orphaned records (in DB but not in filesystem)
- Detect missing records (in filesystem but not in DB)
- Automated reconciliation

---

## 📚 Code References

### Workflow Synchronization
- `app/server/core/workflow_history.py:150-170` - Sync logic
- `app/server/core/workflow_history.py:180-200` - GitHub issue validation
- `app/server/core/workflow_history.py:250` - Sync summary logging

### ADW State Management
- `adws/adw_sdlc_iso.py:50-80` - State file creation
- `adws/adw_sdlc_iso.py:200-230` - State updates

### Database Schema
- `app/server/db/migrations/001_initial_workflow_history.sql` - workflow_history table

---

## ✅ Success Criteria

- [ ] Cleanup script created and executable
- [ ] Script validates issue numbers correctly
- [ ] Invalid workflows removed from `agents/` directory
- [ ] Database cleaned up (orphaned records removed)
- [ ] No GitHub API warnings during sync
- [ ] Valid workflows preserved
- [ ] Cleanup can be run safely multiple times (idempotent)
- [ ] Summary shows removed vs kept counts

---

## 🎯 Next Steps

After completing this cleanup:

1. **Schedule regular cleanup** - Add to cron or maintenance tasks
2. **Improve validation** - Add issue number validation in ADW creation
3. **Archive old workflows** - Move completed workflows to archive/
4. **Document process** - Update troubleshooting guide

---

## 🔄 Future Improvements

### Automated Cleanup Schedule

**Add to crontab:**
```bash
# Run cleanup weekly on Sunday at 2 AM
0 2 * * 0 /Users/Warmonger0/tac/tac-webbuilder/scripts/cleanup_invalid_workflows.sh >> /tmp/cleanup.log 2>&1
```

### Archive Strategy

**Create archive script:**
```bash
#!/bin/bash
# Archive workflows older than 30 days

CUTOFF_DATE=$(date -d '30 days ago' +%Y-%m-%d)
ARCHIVE_DIR="agents/archive/$CUTOFF_DATE"

mkdir -p "$ARCHIVE_DIR"

for dir in agents/adw-*; do
    created=$(jq -r '.created_at' "$dir/adw_state.json")
    if [[ "$created" < "$CUTOFF_DATE" ]]; then
        mv "$dir" "$ARCHIVE_DIR/"
    fi
done
```

### Improved Validation

**Add to ADW creation:**
```python
# adws/adw_sdlc_iso.py
def create_adw_workflow(issue_number):
    # Validate issue number
    if not isinstance(issue_number, int):
        raise ValueError(f"Invalid issue_number: {issue_number}")

    if issue_number <= 0:
        raise ValueError(f"Issue number must be positive: {issue_number}")

    # Verify issue exists in GitHub
    try:
        gh_issue = check_github_issue(issue_number)
    except:
        raise ValueError(f"Issue #{issue_number} not found in GitHub")

    # Proceed with workflow creation
    ...
```

---

**This cleanup ensures a clean workflow directory and eliminates confusing warning messages.**

---

**Last Updated:** 2025-11-17
**Status:** Ready for Implementation
**Priority:** LOW
