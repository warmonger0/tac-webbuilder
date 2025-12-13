# Enhancement #88: E2E ADW Workflow Validation

## Context
Load: `/prime`

## Task
Create comprehensive E2E test validating complete ADW workflow with PostgreSQL.

**Scope**: Plan → Build → Complete cycle with real PostgreSQL (mocked external APIs).

## Workflow

### 1. Investigate (10 min)
```bash
# Check existing E2E tests
ls -la app/server/tests/e2e/
cat app/server/tests/e2e/test_workflow_journey.py | head -50

# Understand ADW phases
grep -n "class Phase" adws/*.py | head -10
```

### 2. Implement (35 min)

**Create**: `app/server/tests/e2e/test_adw_postgresql_e2e.py`

**Test structure**:
```python
@pytest.mark.e2e
class TestADWPostgreSQLEndToEnd:
    """E2E test for complete ADW workflow with PostgreSQL."""

    @pytest.fixture(autouse=True)
    def setup_postgresql_db(self):
        """Use actual PostgreSQL test database."""
        # Set env vars for PostgreSQL
        # Create test tables
        # Yield
        # Cleanup

    def test_complete_adw_workflow_lifecycle(self):
        """Test full ADW: request → plan → build → complete."""
        # 1. Create workflow request (via API or direct service call)
        # 2. Validate planning phase (check workflow_history, phase_queue)
        # 3. Simulate build phase (mock external calls, real DB writes)
        # 4. Validate completion (check all tables, state transitions)
        # 5. Verify WebSocket broadcasts (if applicable)
        # 6. Assert final state correct

    def test_workflow_state_persistence(self):
        """Verify state persists correctly across phases."""
        # Test adw_state.json → DB sync
        # Test branch_name, plan_file, issue_class extraction

    def test_phase_queue_transitions(self):
        """Validate phase queue state machine."""
        # Test status: pending → ready → active → completed

    def test_database_integrity(self):
        """Ensure referential integrity and constraints."""
        # Test foreign keys, not-null constraints
```

**Reference existing**: `tests/e2e/test_workflow_journey.py` for patterns

### 3. Test (10 min)
```bash
cd app/server

# Run E2E test
env POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder_test POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql .venv/bin/pytest tests/e2e/test_adw_postgresql_e2e.py -v

# Verify test database cleaned up
env POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder_test POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme PGPASSWORD=changeme psql -h localhost -U tac_user -d tac_webbuilder_test -c "\dt"
```

### 4. Quality (5 min)
```bash
ruff check tests/e2e/test_adw_postgresql_e2e.py --fix
mypy tests/e2e/test_adw_postgresql_e2e.py --ignore-missing-imports
env POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder_test POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql .venv/bin/pytest tests/e2e/ -v

# Plans Panel
curl -X PATCH http://localhost:8002/api/v1/planned-features/88 \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "actual_hours": 1.0, "completed_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "completion_notes": "E2E test validates full ADW workflow with PostgreSQL"}'

# Commit (NO AI references)
git add app/server/tests/e2e/test_adw_postgresql_e2e.py
git commit -m "test: Add E2E ADW workflow validation with PostgreSQL

Created comprehensive E2E test for complete ADW lifecycle.

Problem:
- No E2E test validating full ADW workflow with PostgreSQL
- Existing tests use temp DBs or mocks
- Missing coverage for cross-service integration

Solution:
- Created test_adw_postgresql_e2e.py (4 test cases)
- Tests plan → build → complete cycle
- Uses actual PostgreSQL test database
- Validates workflow_history, phase_queue, work_log
- Confirms state persistence and phase transitions

Result:
- Complete E2E coverage for ADW workflows
- PostgreSQL integration validated
- Smoke test for CI/CD pipeline

Location: app/server/tests/e2e/test_adw_postgresql_e2e.py"

# Update docs
/updatedocs
```

## Success Criteria
- ✅ E2E test passes with PostgreSQL
- ✅ Covers plan → build → complete cycle
- ✅ Validates database state at each phase
- ✅ Test cleanup works correctly
- ✅ All existing tests still pass

## Time: 1.0h (60 min)
