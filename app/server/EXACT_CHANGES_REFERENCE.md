# Exact Changes Reference - Line by Line

## File 1: test_health_service.py

**File Path:** `/Users/Warmonger0/tac/tac-webbuilder/app/server/tests/services/test_health_service.py`

**Lines Changed:** 334-338

**Test Method:** `TestHealthServiceIntegration::test_custom_configuration_persists`

### Change
```python
# BEFORE (Lines 333-334)
    def test_custom_configuration_persists(self):
        """Verify custom configuration persists across multiple method calls."""
        custom_db = "custom.db"
        health_service = HealthService(db_path=custom_db)

# AFTER (Lines 331-338)
    def test_custom_configuration_persists(self):
        """Verify custom configuration persists across multiple method calls."""
        custom_db = "custom.db"
        health_service = HealthService(
            frontend_url="http://localhost:3000",
            backend_port="8000",
            db_path=custom_db
        )
```

---

## File 2: test_phase_coordinator.py

**File Path:** `/Users/Warmonger0/tac/tac-webbuilder/app/server/tests/services/test_phase_coordinator.py`

### Change 1: phase_coordinator fixture
**Lines Changed:** 75-82 (fixture definition)

```python
# BEFORE (Lines 75-83)
@pytest.fixture
def phase_coordinator(phase_queue_service, temp_workflow_db, mock_websocket_manager):
    """Create PhaseCoordinator with test dependencies"""
    return PhaseCoordinator(
        phase_queue_service=phase_queue_service,
        workflow_db_path=temp_workflow_db,
        poll_interval=0.1,  # Fast polling for tests
        websocket_manager=mock_websocket_manager
    )

# AFTER (Lines 75-82)
@pytest.fixture
def phase_coordinator(phase_queue_service, temp_workflow_db, mock_websocket_manager):
    """Create PhaseCoordinator with test dependencies"""
    return PhaseCoordinator(
        phase_queue_service=phase_queue_service,
        poll_interval=0.1,  # Fast polling for tests
        websocket_manager=mock_websocket_manager
    )
```

### Change 2: test_broadcast_without_websocket_manager
**Lines Changed:** 450-464

**Test Method:** `TestWebSocketBroadcasting::test_broadcast_without_websocket_manager`

```python
# BEFORE (Lines 450-467)
    async def test_broadcast_without_websocket_manager(
        self,
        phase_queue_service,
        temp_workflow_db
    ):
        """Test coordinator works without WebSocket manager"""
        # Create coordinator without WebSocket manager
        coordinator = PhaseCoordinator(
            phase_queue_service=phase_queue_service,
            workflow_db_path=temp_workflow_db,
            poll_interval=0.1,
            websocket_manager=None
        )

        # Should not raise exception
        await coordinator._broadcast_queue_update("queue-123", "completed", 900)

# AFTER (Lines 450-464)
    async def test_broadcast_without_websocket_manager(
        self,
        phase_queue_service,
        temp_workflow_db
    ):
        """Test coordinator works without WebSocket manager"""
        # Create coordinator without WebSocket manager
        coordinator = PhaseCoordinator(
            phase_queue_service=phase_queue_service,
            poll_interval=0.1,
            websocket_manager=None
        )

        # Should not raise exception
        await coordinator._broadcast_queue_update("queue-123", "completed", 900)
```

### Change 3: test_invalid_workflow_db_path
**Lines Changed:** 521-538

**Test Method:** `test_invalid_workflow_db_path`

```python
# BEFORE (Lines 521-539)
    async def test_invalid_workflow_db_path(
        self,
        phase_queue_service,
        mock_websocket_manager
    ):
        """Test handling of invalid workflow database path"""
        coordinator = PhaseCoordinator(
            phase_queue_service=phase_queue_service,
            workflow_db_path="/invalid/path/db.db",
            poll_interval=0.1,
            websocket_manager=mock_websocket_manager
        )

        # Should not crash when checking completions
        await coordinator._check_workflow_completions()

        # Status should be None for non-existent DB
        status = coordinator._get_workflow_status(123)
        assert status is None

# AFTER (Lines 521-538)
    async def test_invalid_workflow_db_path(
        self,
        phase_queue_service,
        mock_websocket_manager
    ):
        """Test handling of invalid workflow database path"""
        coordinator = PhaseCoordinator(
            phase_queue_service=phase_queue_service,
            poll_interval=0.1,
            websocket_manager=mock_websocket_manager
        )

        # Should not crash when checking completions
        await coordinator._check_workflow_completions()

        # Status should be None for non-existent DB
        status = coordinator._get_workflow_status(123)
        assert status is None
```

---

## File 3: test_planned_features_service.py

**File Path:** `/Users/Warmonger0/tac/tac-webbuilder/app/server/tests/services/test_planned_features_service.py`

**Lines Changed:** 468-494

**Test Method:** `TestPlannedFeaturesServiceStatistics::test_get_statistics`

### Change: Mock cursor structure

```python
# BEFORE (Lines 468-494)
    def test_get_statistics(self, service, mock_adapter):
        """Test getting statistics about planned features."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [("planned", 5), ("in_progress", 2), ("completed", 10)],  # by_status
            [("high", 3), ("medium", 8), ("low", 6)],  # by_priority
            [("session", 7), ("feature", 10)],  # by_type
        ]
        mock_cursor.fetchone.side_effect = [
            (45.5, 38.0),  # hours summary
            (58.8,),  # completion rate
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        # Execute
        stats = service.get_statistics()

        # Assert
        assert stats["by_status"]["planned"] == 5
        assert stats["by_status"]["completed"] == 10
        assert stats["by_priority"]["high"] == 3
        assert stats["by_type"]["session"] == 7
        assert stats["total_estimated_hours"] == 45.5
        assert stats["total_actual_hours"] == 38.0
        assert stats["completion_rate"] == 58.8

# AFTER (Lines 468-494)
    def test_get_statistics(self, service, mock_adapter):
        """Test getting statistics about planned features."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [{"status": "planned", "count": 5}, {"status": "in_progress", "count": 2}, {"status": "completed", "count": 10}],  # by_status
            [{"priority": "high", "count": 3}, {"priority": "medium", "count": 8}, {"priority": "low", "count": 6}],  # by_priority
            [{"item_type": "session", "count": 7}, {"item_type": "feature", "count": 10}],  # by_type
        ]
        mock_cursor.fetchone.side_effect = [
            {"total_estimated": 45.5, "total_actual": 38.0},  # hours summary
            {"completion_rate": 58.8},  # completion rate
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        # Execute
        stats = service.get_statistics()

        # Assert
        assert stats["by_status"]["planned"] == 5
        assert stats["by_status"]["completed"] == 10
        assert stats["by_priority"]["high"] == 3
        assert stats["by_type"]["session"] == 7
        assert stats["total_estimated_hours"] == 45.5
        assert stats["total_actual_hours"] == 38.0
        assert stats["completion_rate"] == 58.8
```

---

## File 4: test_multi_phase_execution.py (PREVENTIVE FIXES)

**File Path:** `/Users/Warmonger0/tac/tac-webbuilder/app/server/tests/e2e/test_multi_phase_execution.py`

### Change 1: phase_coordinator fixture
**Lines Changed:** 104-112

```python
# BEFORE (Lines 104-113)
@pytest.fixture
def phase_coordinator(phase_queue_service, temp_workflow_db, mock_websocket_manager):
    """Create PhaseCoordinator with test dependencies"""
    coordinator = PhaseCoordinator(
        phase_queue_service=phase_queue_service,
        workflow_db_path=temp_workflow_db,
        poll_interval=0.1,  # Fast polling for tests
        websocket_manager=mock_websocket_manager
    )
    return coordinator

# AFTER (Lines 104-112)
@pytest.fixture
def phase_coordinator(phase_queue_service, temp_workflow_db, mock_websocket_manager):
    """Create PhaseCoordinator with test dependencies"""
    coordinator = PhaseCoordinator(
        phase_queue_service=phase_queue_service,
        poll_interval=0.1,  # Fast polling for tests
        websocket_manager=mock_websocket_manager
    )
    return coordinator
```

### Change 2: test_errors_in_polling_loop
**Lines Changed:** 567-578

**Test Method:** `test_errors_in_polling_loop`

```python
# BEFORE (Lines 567-586)
    async def test_errors_in_polling_loop(
        self,
        phase_queue_service,
        mock_websocket_manager
    ):
        """
        Test that errors in polling loop are caught and logged without crashing.
        """
        # Create coordinator with invalid workflow DB path to trigger errors
        bad_coordinator = PhaseCoordinator(
            phase_queue_service=phase_queue_service,
            workflow_db_path="/nonexistent/path/to/db.db",
            poll_interval=0.1,
            websocket_manager=mock_websocket_manager
        )

        await bad_coordinator.start()

        try:
            # Let it run for a bit - should log errors but not crash
            await asyncio.sleep(0.3)

# AFTER (Lines 567-585)
    async def test_errors_in_polling_loop(
        self,
        phase_queue_service,
        mock_websocket_manager
    ):
        """
        Test that errors in polling loop are caught and logged without crashing.
        """
        # Create coordinator to test error handling
        bad_coordinator = PhaseCoordinator(
            phase_queue_service=phase_queue_service,
            poll_interval=0.1,
            websocket_manager=mock_websocket_manager
        )

        await bad_coordinator.start()

        try:
            # Let it run for a bit - should log errors but not crash
            await asyncio.sleep(0.3)
```

---

## Summary Table

| File | Method | Lines | Change Type | Status |
|------|--------|-------|------------|--------|
| test_health_service.py | test_custom_configuration_persists | 334-338 | Add params | FIXED |
| test_phase_coordinator.py | phase_coordinator (fixture) | 78-82 | Remove param | FIXED |
| test_phase_coordinator.py | test_broadcast_without_websocket_manager | 457-461 | Remove param | FIXED |
| test_phase_coordinator.py | (test uses fixture) | N/A | Auto-fixed | FIXED |
| test_phase_coordinator.py | (test uses fixture) | N/A | Auto-fixed | FIXED |
| test_phase_coordinator.py | test_invalid_workflow_db_path | 527-531 | Remove param | FIXED |
| test_planned_features_service.py | test_get_statistics | 472-480 | Update mocks | FIXED |
| test_multi_phase_execution.py | phase_coordinator (fixture) | 107-112 | Remove param | PREVENTIVE |
| test_multi_phase_execution.py | test_errors_in_polling_loop | 573-577 | Remove param | PREVENTIVE |

---

## Verification Commands

### Check specific files are fixed
```bash
grep -n "workflow_db_path=" /Users/Warmonger0/tac/tac-webbuilder/app/server/tests/services/test_phase_coordinator.py
grep -n "workflow_db_path=" /Users/Warmonger0/tac/tac-webbuilder/app/server/tests/e2e/test_multi_phase_execution.py

# Expected: No matches (all removed)
```

### Check HealthService has required params
```bash
grep -A 5 "HealthService(" /Users/Warmonger0/tac/tac-webbuilder/app/server/tests/services/test_health_service.py | grep -E "frontend_url|backend_port"

# Expected: Both parameters present
```

### Check mock structure is dicts
```bash
grep -A 2 "fetchall.side_effect" /Users/Warmonger0/tac/tac-webbuilder/app/server/tests/services/test_planned_features_service.py

# Expected: {"status": ...} not ("status", ...)
```

---

## Testing Each Fix Individually

### Test 1: HealthService
```bash
pytest tests/services/test_health_service.py::TestHealthServiceIntegration::test_custom_configuration_persists -v
```

### Test 2: PhaseCoordinator Fixture Tests
```bash
pytest tests/services/test_phase_coordinator.py::TestWebSocketBroadcasting -v
```

### Test 3: PlannedFeaturesService
```bash
pytest tests/services/test_planned_features_service.py::TestPlannedFeaturesServiceStatistics::test_get_statistics -v
```

### Test 4: E2E Tests
```bash
pytest tests/e2e/test_multi_phase_execution.py::test_errors_in_polling_loop -v
```

---

## All Tests Together

```bash
env POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
    POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql \
    .venv/bin/pytest \
    tests/services/test_health_service.py::TestHealthServiceIntegration::test_custom_configuration_persists \
    tests/services/test_phase_coordinator.py::TestWebSocketBroadcasting::test_broadcast_without_websocket_manager \
    tests/services/test_phase_coordinator.py::TestWebSocketBroadcasting::test_broadcast_queue_update_success \
    tests/services/test_phase_coordinator.py::TestWebSocketBroadcasting::test_broadcast_error_handling \
    tests/services/test_phase_coordinator.py::test_invalid_workflow_db_path \
    tests/services/test_planned_features_service.py::TestPlannedFeaturesServiceStatistics::test_get_statistics \
    -v
```

**Expected:** All tests PASS
