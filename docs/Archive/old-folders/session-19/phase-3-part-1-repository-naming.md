# Task: Standardize Repository Method Naming Conventions

## Context
I'm working on the tac-webbuilder project. The architectural consistency analysis (Session 19) identified 4 different repository naming conventions causing confusion and maintenance burden. This task standardizes all repository methods to consistent CRUD patterns.

## Objective
Align all repositories to a consistent naming convention, making the codebase more maintainable and reducing cognitive load for developers.

## Background Information
- **Phase:** Session 19 - Phase 3, Part 1/4
- **Files Affected:** 4 repository files + all their callers (services, routes, tests)
- **Current Problem:** 4 different naming conventions across repositories
- **Target:** Single standardized CRUD convention
- **Risk Level:** Medium (many callers to update, but well-tested)
- **Estimated Time:** 6 hours
- **Dependencies:** None (can execute independently)

## Current Problem - Inconsistent Naming

### PhaseQueueRepository
```python
insert_phase(item)      # Should be: create(item)
find_by_id(id)          # Should be: get_by_id(id)
find_by_parent(parent)  # Should be: get_all_by_parent_issue(parent)
find_all()              # Should be: get_all(limit, offset)
delete_phase(id)        # Should be: delete(id)
```

### WorkLogRepository
```python
create_entry(item)      # Should be: create(item)
get_all()               # Should be: get_all(limit, offset)
delete_entry(id)        # Should be: delete(id)
```

### TaskLogRepository & UserPromptRepository
- Mostly correct (already use `create()`)
- Need minor adjustments for consistency

**Issue:** Developers must remember different method names for same operation across repos.

## Target Solution - Standardized Convention

### Standard CRUD Methods
```python
create(item: ModelCreate) -> Model
get_by_id(id: int) -> Optional[Model]
get_by_<field>(value: Any) -> Optional[Model]
get_all_by_<field>(value: Any, limit: int = 100) -> List[Model]
get_all(limit: int = 100, offset: int = 0) -> List[Model]
update(id: int, data: ModelUpdate) -> Optional[Model]
delete(id: int) -> bool
find_<custom_criteria>(...) -> List[Model]  # For complex queries
```

**Benefits:**
- Single convention to learn
- Easy to predict method names
- Consistent across all repositories
- Clear distinction: `get_*` for reads, `create/update/delete` for writes

---

## Step-by-Step Instructions

### Step 1: Create Repository Standards Documentation

**File:** `docs/backend/repository-standards.md` (NEW)

Create comprehensive documentation defining the standard naming convention:

```markdown
# Repository Naming Standards

All repository classes MUST follow this naming convention for consistency and maintainability.

## Standard Method Names

### Create
```python
def create(self, item: ModelCreate) -> Model:
    """Create a new record.

    Args:
        item: Pydantic model with creation data

    Returns:
        Created model with ID populated
    """
```

### Read (Single Record)
```python
def get_by_id(self, id: int) -> Optional[Model]:
    """Get single record by primary key.

    Args:
        id: Primary key value

    Returns:
        Model if found, None otherwise
    """
```

### Read (By Field)
```python
def get_by_<field>(self, value: Any) -> Optional[Model]:
    """Get single record by unique field.

    Args:
        value: Field value to search for

    Returns:
        Model if found, None otherwise
    """

# For one-to-many relationships
def get_all_by_<field>(self, value: Any, limit: int = 100) -> List[Model]:
    """Get all records matching field value.

    Args:
        value: Field value to filter by
        limit: Maximum records to return

    Returns:
        List of matching models
    """
```

### Read (All)
```python
def get_all(self, limit: int = 100, offset: int = 0) -> List[Model]:
    """Get all records with pagination.

    Args:
        limit: Maximum records to return
        offset: Number of records to skip

    Returns:
        List of models
    """
```

### Update
```python
def update(self, id: int, data: ModelUpdate) -> Optional[Model]:
    """Update existing record.

    Args:
        id: Primary key of record to update
        data: Pydantic model with update data

    Returns:
        Updated model if found, None otherwise
    """
```

### Delete
```python
def delete(self, id: int) -> bool:
    """Delete record by primary key.

    Args:
        id: Primary key of record to delete

    Returns:
        True if deleted, False if not found
    """
```

### Custom Queries
```python
def find_<custom_criteria>(self, ...) -> List[Model]:
    """Custom query with descriptive name.

    Use 'find_' prefix for complex queries that don't fit
    standard patterns.

    Examples:
    - find_ready_phases()
    - find_pending_with_priority()
    - find_expired_sessions()
    """
```

## Migration Checklist

When renaming methods:
1. ✅ Update repository method name
2. ✅ Update all service callers
3. ✅ Update all route callers
4. ✅ Update tests
5. ✅ Run full test suite
6. ✅ Commit with clear migration message
```

Save this file, it will guide all future repository development.

### Step 2: Search for All Method Callers

Before renaming, find all places that call the old method names:

```bash
cd app/server

# PhaseQueueRepository method callers
echo "=== insert_phase callers ==="
grep -r "insert_phase" services/ routes/ tests/ --include="*.py"

echo "=== find_by_id (phase_queue context) callers ==="
grep -r "phase_queue.*find_by_id\|find_by_id.*phase_queue" services/ routes/ tests/ --include="*.py"

echo "=== find_by_parent callers ==="
grep -r "find_by_parent" services/ routes/ tests/ --include="*.py"

echo "=== find_all (phase_queue context) callers ==="
grep -r "phase_queue.*find_all\|find_all.*phase_queue" services/ routes/ tests/ --include="*.py"

echo "=== delete_phase callers ==="
grep -r "delete_phase" services/ routes/ tests/ --include="*.py"

# WorkLogRepository method callers
echo "=== create_entry callers ==="
grep -r "create_entry" services/ routes/ tests/ --include="*.py"

echo "=== delete_entry callers ==="
grep -r "delete_entry" services/ routes/ tests/ --include="*.py"
```

**Action:** Take note of all files found. You'll update these in Steps 4-5.

### Step 3: Rename PhaseQueueRepository Methods

**File:** `app/server/repositories/phase_queue_repository.py`

Make these renames:

1. **insert_phase → create**
```python
# Before
def insert_phase(self, item: PhaseQueueItem) -> int:
    """Insert new phase queue item."""
    # ... implementation ...
    return queue_id

# After
def create(self, item: PhaseQueueItem) -> PhaseQueueItem:
    """Create new phase queue item.

    Args:
        item: Phase queue item to create

    Returns:
        Created item with queue_id populated
    """
    # ... same implementation ...
    item.queue_id = queue_id
    return item
```

2. **find_by_id → get_by_id**
```python
# Before
def find_by_id(self, queue_id: int) -> Optional[PhaseQueueItem]:
    """Find phase queue item by queue_id."""
    # ... implementation ...

# After
def get_by_id(self, queue_id: int) -> Optional[PhaseQueueItem]:
    """Get phase queue item by queue_id.

    Args:
        queue_id: Primary key to search for

    Returns:
        PhaseQueueItem if found, None otherwise
    """
    # ... same implementation ...
```

3. **find_by_parent → get_all_by_parent_issue**
```python
# Before
def find_by_parent(self, parent_issue: str) -> List[PhaseQueueItem]:
    """Find all phases for parent issue."""
    # ... implementation ...

# After
def get_all_by_parent_issue(self, parent_issue: str, limit: int = 100) -> List[PhaseQueueItem]:
    """Get all phases for parent issue.

    Args:
        parent_issue: Parent issue number to filter by
        limit: Maximum records to return

    Returns:
        List of matching phase queue items
    """
    # ... implementation with LIMIT added ...
```

4. **find_all → get_all**
```python
# Before
def find_all(self) -> List[PhaseQueueItem]:
    """Find all phase queue items."""
    # ... implementation ...

# After
def get_all(self, limit: int = 100, offset: int = 0) -> List[PhaseQueueItem]:
    """Get all phase queue items with pagination.

    Args:
        limit: Maximum records to return
        offset: Number of records to skip

    Returns:
        List of phase queue items
    """
    # ... implementation with LIMIT/OFFSET added ...
```

5. **delete_phase → delete**
```python
# Before
def delete_phase(self, queue_id: int) -> bool:
    """Delete phase queue item."""
    # ... implementation ...

# After
def delete(self, queue_id: int) -> bool:
    """Delete phase queue item by queue_id.

    Args:
        queue_id: Primary key of item to delete

    Returns:
        True if deleted, False if not found
    """
    # ... same implementation ...
```

### Step 4: Update Service Callers

**Files to update:**
- `app/server/services/phase_queue_service.py`
- `app/server/services/phase_dependency_tracker.py`
- Any other services that use PhaseQueueRepository

**Update pattern:**
```python
# Before
queue_id = self.repository.insert_phase(item)

# After
created_item = self.repository.create(item)
queue_id = created_item.queue_id
```

```python
# Before
item = self.repository.find_by_id(queue_id)

# After
item = self.repository.get_by_id(queue_id)
```

```python
# Before
phases = self.repository.find_by_parent(parent_issue)

# After
phases = self.repository.get_all_by_parent_issue(parent_issue)
```

**Action:** Update all service files found in Step 2.

### Step 5: Update Route Callers

**Files to update:**
- `app/server/routes/queue_routes.py`
- Any other routes that use PhaseQueueRepository

**Update pattern:** Same as Step 4, but in route handlers.

### Step 6: Update Tests

**Files to update:**
- `app/server/tests/repositories/test_phase_queue_repository.py`
- `app/server/tests/services/test_phase_queue_service.py`
- Any other test files found in Step 2

**Update test assertions:**
```python
# Before
def test_insert_phase():
    queue_id = repository.insert_phase(item)
    assert queue_id > 0

# After
def test_create():
    created_item = repository.create(item)
    assert created_item.queue_id > 0
    assert created_item.issue_number == item.issue_number
```

### Step 7: Rename WorkLogRepository Methods

**File:** `app/server/repositories/work_log_repository.py`

1. **create_entry → create**
2. **delete_entry → delete**
3. Ensure **get_all** has pagination parameters

Follow same pattern as Step 3.

### Step 8: Update WorkLog Callers

Search for and update all callers:
```bash
grep -r "create_entry\|delete_entry" services/ routes/ tests/ --include="*.py"
```

Update each file found.

### Step 9: Run Full Test Suite

```bash
cd app/server

# Run all tests
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql .venv/bin/pytest -v

# Should see: All tests PASSED
```

**If tests fail:**
- Check that you updated ALL callers (re-run greps from Step 2)
- Verify return types match (create now returns Model, not just ID)
- Check test assertions for new return values

### Step 10: Verify No Old Names Remain

```bash
cd app/server

# These should return NO results:
grep -r "insert_phase" services/ routes/ --include="*.py"
grep -r "create_entry" services/ routes/ --include="*.py"
grep -r "delete_phase" services/ routes/ --include="*.py"
grep -r "delete_entry" services/ routes/ --include="*.py"

# If any results found, update those files
```

### Step 11: Commit Changes

```bash
git add app/server/repositories/
git add app/server/services/
git add app/server/routes/
git add app/server/tests/
git add docs/backend/repository-standards.md

git commit -m "$(cat <<'EOF'
refactor: Standardize repository method naming conventions

Aligned all repositories to consistent CRUD naming pattern for better
maintainability and reduced cognitive load.

Standard Methods (NEW):
- create(item) - Create new record
- get_by_id(id) - Get by primary key
- get_by_<field>(value) - Get by unique field
- get_all_by_<field>(value, limit) - Get multiple by field
- get_all(limit, offset) - Get all with pagination
- update(id, data) - Update existing
- delete(id) - Delete by ID
- find_<criteria>() - Custom queries

Renamed Methods:
PhaseQueueRepository:
  - insert_phase() → create()
  - find_by_id() → get_by_id()
  - find_by_parent() → get_all_by_parent_issue()
  - find_all() → get_all()
  - delete_phase() → delete()

WorkLogRepository:
  - create_entry() → create()
  - delete_entry() → delete()

Updated Files:
- 2 repository files (renamed 7 methods total)
- 5+ service files (all callers updated)
- 3+ route files (all callers updated)
- 8+ test files (all test cases updated)

Created Documentation:
- docs/backend/repository-standards.md (future reference)

Benefits:
- Single convention across all repositories
- Predictable method names
- Easier onboarding for new developers
- Reduced context switching
- Clear CRUD semantics

Test Results: 878/878 PASSED

Session 19 - Phase 3, Part 1/4
EOF
)"
```

---

## Success Criteria

- ✅ docs/backend/repository-standards.md created and complete
- ✅ PhaseQueueRepository: All 5 methods renamed
- ✅ WorkLogRepository: All 2 methods renamed
- ✅ TaskLogRepository: Verified consistent (no changes needed)
- ✅ UserPromptRepository: Verified consistent (no changes needed)
- ✅ All service callers updated (5+ files)
- ✅ All route callers updated (3+ files)
- ✅ All test files updated (8+ files)
- ✅ Full test suite passing (878/878 PASS)
- ✅ No old method names remain in codebase
- ✅ Changes committed with descriptive message

## Verification Commands

```bash
# Test suite
cd app/server
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql .venv/bin/pytest -v

# Check for old names (should return empty)
grep -r "insert_phase\|create_entry\|delete_phase\|delete_entry\|find_by_id" app/server/services/ app/server/routes/ --include="*.py" | grep -v "# " | grep -v get_by_id

# Count renamed methods
grep -r "def create\|def get_by_id\|def get_all\|def delete" app/server/repositories/ --include="*.py" | wc -l
```

## Files Modified

**Created (1):**
- `docs/backend/repository-standards.md`

**Modified (~18 files):**
- `app/server/repositories/phase_queue_repository.py` (5 method renames)
- `app/server/repositories/work_log_repository.py` (2 method renames)
- `app/server/services/phase_queue_service.py` (caller updates)
- `app/server/services/phase_dependency_tracker.py` (caller updates)
- `app/server/services/work_log_service.py` (caller updates)
- `app/server/routes/queue_routes.py` (caller updates)
- `app/server/routes/work_log_routes.py` (caller updates)
- `app/server/tests/repositories/test_phase_queue_repository.py` (test updates)
- `app/server/tests/services/test_phase_queue_service.py` (test updates)
- `app/server/tests/routes/test_queue_routes.py` (test updates)
- (And others as found in Step 2)

## Troubleshooting

### Issue: Tests fail with "object has no attribute 'queue_id'"
**Cause:** Some callers expect `create()` to return just an ID, not the full object
**Fix:** Update caller to extract ID: `queue_id = created_item.queue_id`

### Issue: Grep finds old method names after renaming
**Cause:** Missed some callers in services/routes/tests
**Fix:** Update the files shown by grep

### Issue: Import errors after renaming
**Cause:** Repository class might be cached by Python
**Fix:** Restart Python process or server

---

## Return Summary to Main Chat

After completing this task, copy this summary back to the Session 19 coordination chat:

```
# Phase 3, Part 1 Complete: Repository Naming Standardization

## ✅ Completed Tasks
- Created repository naming standards documentation
- Renamed PhaseQueueRepository methods (5 changes):
  - insert_phase → create
  - find_by_id → get_by_id
  - find_by_parent → get_all_by_parent_issue
  - find_all → get_all
  - delete_phase → delete
- Renamed WorkLogRepository methods (2 changes):
  - create_entry → create
  - delete_entry → delete
- Updated all service callers (5 files)
- Updated all route callers (3 files)
- Updated all test files (8 files)

## 📊 Test Results
- Backend tests: **878/878 PASSED**
- No old method names remain in codebase
- All repositories now use consistent CRUD convention

## 📁 Files Modified
- Created: 1 (docs/backend/repository-standards.md)
- Modified: 18 files (repositories, services, routes, tests)
- Total commit: 1

## 🎯 Impact
- Single naming convention across all repositories
- Reduced cognitive load for developers
- Easier to predict method names
- Future repositories will follow standard

## ⚠️ Issues Encountered
[List any issues and resolutions, or "None"]

## ✅ Ready for Next Part
Part 1 complete. Ready to proceed with **Part 2: Data Fetching Migration** (3 hours).

**Session 19 - Phase 3, Part 1/4 COMPLETE**
```

---

**Ready to copy into a new chat!** This task is independent and can be started immediately.
