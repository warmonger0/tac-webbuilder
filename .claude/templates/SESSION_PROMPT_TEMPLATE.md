# Template: Session Prompt (Compact)

This template shows how to create compact session prompts using reusable templates.

---

# Task: <Session Title>

## Context
I'm working on the tac-webbuilder project. <Brief 2-3 sentence context about what exists and what's needed>

## Objective
<1-2 sentence clear objective>

## Background Information
- **Current State:** <What exists now>
- **Problem:** <What needs to be solved>
- **Solution:** <High-level approach>

---

## Implementation Steps

### Step 1: Database Migration (30 min)

**Create:** `app/server/db/migrations/XXX_<name>.sql`

**Template:** See `.claude/templates/DATABASE_MIGRATION.md`

**Specifics for this session:**
- Table name: `<table_name>`
- Columns:
  - `id` - Primary key
  - `column1 TEXT NOT NULL`
  - `column2 INTEGER`
  - `status TEXT CHECK(status IN ('value1', 'value2'))`
- Indexes:
  - `idx_<table>_status` on `status`
  - `idx_<table>_created` on `created_at`

**Run migration:**
```bash
sqlite3 app/server/db/workflow_history.db < app/server/db/migrations/XXX_<name>.sql
```

---

### Step 2: Service Layer (60 min)

**Create:** `app/server/services/<name>_service.py`

**Template:** See `.claude/templates/SERVICE_LAYER.md`

**Specifics for this session:**
- Service name: `<Name>Service`
- Data model: `<ModelName>`
- Methods needed:
  - `get_all(limit)` - Get all items
  - `get_by_status(status)` - Filter by status
  - `create(data)` - Create new item
  - `update_status(id, status)` - Update status

**Additional business logic:**
```python
def custom_method(self, param: str) -> Result:
    """<Description>"""
    # Implementation specific to this feature
    pass
```

**Reference similar patterns in:**
- `app/server/services/workflow_service.py` for workflow patterns
- `app/server/services/pattern_review_service.py` for approval patterns

---

### Step 3: CLI Tool (90 min)

**Create:** `scripts/<name>.py`

**Template:** See `.claude/templates/CLI_TOOL.md`

**Specifics for this session:**
- Tool name: `<Name>CLI`
- Commands:
  - `--stats` - Show statistics
  - `--action` - Perform main action
  - `--interactive` - Interactive mode

**Custom interactive prompts:**
```python
def interactive_mode(self):
    print("Actions: [a]pprove, [r]eject, [s]kip, [q]uit")

    while True:
        choice = input("Your choice: ").lower()

        if choice == 'a':
            # Approval logic
        elif choice == 'r':
            # Rejection logic
        # ... etc
```

---

### Step 4: Tests (45 min)

**Create:** `scripts/tests/test_<name>.py` or `app/server/tests/services/test_<name>_service.py`

**Template:** See `.claude/templates/PYTEST_TESTS.md`

**Test cases needed:**
1. Test basic operations (CRUD)
2. Test edge cases (empty data, invalid input)
3. Test business logic specific to this feature
4. Test error handling

**Specific assertions:**
```python
def test_custom_behavior(service):
    """Test <specific behavior>."""
    result = service.custom_method('input')
    assert result.field == 'expected_value'
    assert result.status == 'success'
```

---

### Step 5: Integration & Documentation (30 min)

**Modify existing files:**
- `<file_to_modify>.py` - Add integration code
- `docs/features/<doc>.md` - Update documentation

**Integration points:**
```python
# In existing file
from app.server.services.<name>_service import <Name>Service

# Use the service
service = <Name>Service()
result = service.method()
```

**Documentation section:**
Add to `docs/features/<doc>.md`:
```markdown
## <Feature Name>

### Overview
<Brief description>

### Usage
<How to use the feature>

### Example
<Code or CLI example>
```

---

## Success Criteria

- ✅ Migration creates all required tables
- ✅ Service implements all CRUD operations
- ✅ CLI tool provides interactive interface
- ✅ All tests passing (X/X)
- ✅ Integration with existing code complete
- ✅ Documentation updated

---

## Files Expected to Change

**Created (X):**
- `app/server/db/migrations/XXX_<name>.sql` (~XX lines)
- `app/server/services/<name>_service.py` (~XX lines)
- `scripts/<name>.py` (~XX lines)
- `scripts/tests/test_<name>.py` (~XX lines)

**Modified (X):**
- `<file1>.py` (add integration)
- `docs/features/<doc>.md` (add documentation)

---

## Quick Reference

**Templates used:**
- DATABASE_MIGRATION.md - Standard SQL migration structure
- SERVICE_LAYER.md - Repository + business logic pattern
- CLI_TOOL.md - Interactive CLI with argparse
- PYTEST_TESTS.md - Test fixtures and patterns

**Run tests:**
```bash
pytest scripts/tests/test_<name>.py -v
```

**Manual test:**
```bash
python scripts/<name>.py --stats
python scripts/<name>.py --interactive
```

---

## Estimated Time

- Step 1 (Migration): 30 min
- Step 2 (Service): 60 min
- Step 3 (CLI): 90 min
- Step 4 (Tests): 45 min
- Step 5 (Integration): 30 min

**Total: 3-4 hours**

---

## Session Completion Template

When done, provide summary in this format:

```markdown
## ✅ Session X Complete - <Title>

**Duration:** ~X hours
**Status:** Complete ✅
**Next:** Ready for Session Y

### What Was Done
[Bullet points]

### Key Results
[Achievements]

### Files Changed
**Created (X):**
- file1.py
- file2.sql

**Modified (X):**
- file3.py

### Test Results
```
pytest ...
X/X passed
```

### Next Session
Session Y: <Title> (X hours)
```
