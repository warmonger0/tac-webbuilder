# Task: Implement Port Pool for ADW Worktree Management

## Context
I'm working on the tac-webbuilder project. Currently, ADW worktrees use a deterministic port allocation system (9100-9114 backend, 9200-9214 frontend) which limits concurrent workflows to 15 and creates collision risk. This session implements a 100-slot port pool with reservation/release management.

## Objective
Create a robust port pool system that:
- Supports up to 100 concurrent ADW workflows
- Prevents port collisions via reservation system
- Persists allocations across restarts
- Provides clear debugging when pool is exhausted

## Background Information
- **Current System:**
  - Backend ports: 9100-9114 (15 slots)
  - Frontend ports: 9200-9214 (15 slots)
  - Deterministic allocation: hash(adw_id) % 15
  - Problem: Collisions when >15 concurrent workflows

- **New System:**
  - Backend ports: 9100-9199 (100 slots)
  - Frontend ports: 9200-9299 (100 slots)
  - Reservation-based allocation
  - Persistence: agents/port_allocations.json
  - Auto-release on ADW completion

- **Files to Create:**
  - `adws/adw_modules/port_pool.py` - PortPool class
  - `adws/tests/test_port_pool.py` - Comprehensive tests
  - `agents/port_allocations.json` - Persistence file (created automatically)

- **Files to Modify:**
  - `adws/adw_modules/worktree_setup.py` - Use PortPool instead of deterministic hash
  - Potentially: ADW workflow files that call worktree_setup

---

## Step-by-Step Instructions

### Step 1: Understand Current Port Allocation (15 min)

Read the current implementation to understand what we're replacing:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws/adw_modules
```

**Read these files:**
1. `worktree_setup.py` - Current port allocation logic
2. Find where ports are assigned (look for 9100, 9200, hash, or port calculation)
3. Understand the signature of functions that allocate ports

**Document:**
- Current function signature
- How ports are currently calculated
- Where ports are used (backend_port, frontend_port variables)
- Return values expected by calling code

### Step 2: Create Port Pool Module (45-60 min)

Create new file: `adws/adw_modules/port_pool.py`

```python
#!/usr/bin/env python3
"""
Port Pool Management for ADW Worktrees

Manages allocation and release of backend/frontend port pairs for concurrent ADW workflows.
Prevents port collisions via reservation system with persistence.

Architecture:
- Backend pool: 9100-9199 (100 slots)
- Frontend pool: 9200-9299 (100 slots)
- Persistence: agents/port_allocations.json
- Auto-cleanup on workflow completion

Usage:
    from adw_modules.port_pool import PortPool

    pool = PortPool()
    backend_port, frontend_port = pool.reserve("adw-abc123")

    # ... use ports ...

    pool.release("adw-abc123")
"""

import json
import logging
import threading
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class PortPool:
    """
    Thread-safe port pool for ADW worktree isolation.

    Manages 100 backend/frontend port pairs with automatic persistence.
    """

    # Port ranges
    BACKEND_PORT_START = 9100
    BACKEND_PORT_END = 9199
    FRONTEND_PORT_START = 9200
    FRONTEND_PORT_END = 9299

    # Persistence
    PROJECT_ROOT = Path(__file__).parent.parent.parent  # tac-webbuilder/
    PERSISTENCE_FILE = PROJECT_ROOT / "agents" / "port_allocations.json"

    def __init__(self):
        """Initialize port pool and load existing allocations."""
        self._lock = threading.Lock()
        self._allocations: Dict[str, Dict] = {}  # adw_id -> {"backend": int, "frontend": int, "allocated_at": str}
        self._load_allocations()

    def reserve(self, adw_id: str) -> Tuple[int, int]:
        """
        Reserve a backend/frontend port pair for an ADW workflow.

        Args:
            adw_id: Unique ADW identifier (e.g., "adw-abc123")

        Returns:
            Tuple of (backend_port, frontend_port)

        Raises:
            RuntimeError: If pool is exhausted (all 100 slots allocated)

        Thread-safe: Yes
        """
        with self._lock:
            # Check if already allocated
            if adw_id in self._allocations:
                allocation = self._allocations[adw_id]
                logger.debug(
                    f"[PortPool] ADW {adw_id} already has ports: "
                    f"backend={allocation['backend']}, frontend={allocation['frontend']}"
                )
                return allocation["backend"], allocation["frontend"]

            # Find available slot
            used_backend_ports = {a["backend"] for a in self._allocations.values()}

            for slot in range(100):
                backend_port = self.BACKEND_PORT_START + slot
                frontend_port = self.FRONTEND_PORT_START + slot

                if backend_port not in used_backend_ports:
                    # Reserve this slot
                    self._allocations[adw_id] = {
                        "backend": backend_port,
                        "frontend": frontend_port,
                        "allocated_at": datetime.now().isoformat()
                    }

                    self._save_allocations()

                    logger.info(
                        f"[PortPool] Reserved ports for {adw_id}: "
                        f"backend={backend_port}, frontend={frontend_port} "
                        f"(slot {slot}/100)"
                    )

                    return backend_port, frontend_port

            # Pool exhausted
            raise RuntimeError(
                f"Port pool exhausted! All 100 slots allocated. "
                f"Current allocations: {list(self._allocations.keys())}"
            )

    def release(self, adw_id: str) -> bool:
        """
        Release ports allocated to an ADW workflow.

        Args:
            adw_id: ADW identifier to release

        Returns:
            True if ports were released, False if not allocated

        Thread-safe: Yes
        """
        with self._lock:
            if adw_id not in self._allocations:
                logger.warning(f"[PortPool] Attempted to release {adw_id} but not allocated")
                return False

            allocation = self._allocations.pop(adw_id)
            self._save_allocations()

            logger.info(
                f"[PortPool] Released ports for {adw_id}: "
                f"backend={allocation['backend']}, frontend={allocation['frontend']}"
            )

            return True

    def get_allocation(self, adw_id: str) -> Optional[Tuple[int, int]]:
        """
        Get current port allocation for an ADW workflow.

        Args:
            adw_id: ADW identifier

        Returns:
            Tuple of (backend_port, frontend_port) or None if not allocated

        Thread-safe: Yes
        """
        with self._lock:
            if adw_id in self._allocations:
                allocation = self._allocations[adw_id]
                return allocation["backend"], allocation["frontend"]
            return None

    def get_pool_status(self) -> Dict:
        """
        Get current pool utilization statistics.

        Returns:
            Dict with keys: allocated, available, total, allocations

        Thread-safe: Yes
        """
        with self._lock:
            allocated = len(self._allocations)
            total = 100
            available = total - allocated

            return {
                "allocated": allocated,
                "available": available,
                "total": total,
                "utilization_percent": (allocated / total) * 100,
                "allocations": dict(self._allocations)  # Deep copy
            }

    def cleanup_stale(self, max_age_hours: int = 24) -> int:
        """
        Clean up allocations older than max_age_hours.

        Useful for clearing leaked allocations from crashed workflows.

        Args:
            max_age_hours: Maximum age in hours before considering stale

        Returns:
            Number of stale allocations removed

        Thread-safe: Yes
        """
        with self._lock:
            from datetime import timedelta

            now = datetime.now()
            cutoff = now - timedelta(hours=max_age_hours)

            stale_adw_ids = []
            for adw_id, allocation in self._allocations.items():
                allocated_at = datetime.fromisoformat(allocation["allocated_at"])
                if allocated_at < cutoff:
                    stale_adw_ids.append(adw_id)

            for adw_id in stale_adw_ids:
                allocation = self._allocations.pop(adw_id)
                logger.warning(
                    f"[PortPool] Cleaned up stale allocation: {adw_id} "
                    f"(allocated {allocation['allocated_at']}, "
                    f"ports: {allocation['backend']}/{allocation['frontend']})"
                )

            if stale_adw_ids:
                self._save_allocations()

            return len(stale_adw_ids)

    def _load_allocations(self):
        """Load allocations from persistence file."""
        if not self.PERSISTENCE_FILE.exists():
            logger.debug(f"[PortPool] No persistence file found at {self.PERSISTENCE_FILE}")
            return

        try:
            with open(self.PERSISTENCE_FILE, 'r') as f:
                self._allocations = json.load(f)

            logger.info(
                f"[PortPool] Loaded {len(self._allocations)} allocations from "
                f"{self.PERSISTENCE_FILE}"
            )
        except Exception as e:
            logger.error(f"[PortPool] Failed to load allocations: {e}")
            self._allocations = {}

    def _save_allocations(self):
        """Save allocations to persistence file."""
        try:
            # Ensure directory exists
            self.PERSISTENCE_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Write with pretty formatting for debugging
            with open(self.PERSISTENCE_FILE, 'w') as f:
                json.dump(self._allocations, f, indent=2, sort_keys=True)

            logger.debug(
                f"[PortPool] Saved {len(self._allocations)} allocations to "
                f"{self.PERSISTENCE_FILE}"
            )
        except Exception as e:
            logger.error(f"[PortPool] Failed to save allocations: {e}")


# Singleton instance
_pool_instance: Optional[PortPool] = None
_pool_lock = threading.Lock()


def get_port_pool() -> PortPool:
    """
    Get the global PortPool singleton instance.

    Thread-safe singleton pattern.

    Returns:
        PortPool instance
    """
    global _pool_instance

    if _pool_instance is None:
        with _pool_lock:
            if _pool_instance is None:
                _pool_instance = PortPool()

    return _pool_instance
```

### Step 3: Create Comprehensive Tests (45 min)

Create new file: `adws/tests/test_port_pool.py`

```python
#!/usr/bin/env python3
"""
Tests for Port Pool Management

Run with:
    cd adws
    pytest tests/test_port_pool.py -v
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.port_pool import PortPool, get_port_pool


@pytest.fixture
def temp_persistence_dir():
    """Create temporary directory for persistence file."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def port_pool(temp_persistence_dir):
    """Create PortPool instance with temporary persistence."""
    with patch.object(PortPool, 'PERSISTENCE_FILE', temp_persistence_dir / "port_allocations.json"):
        pool = PortPool()
        yield pool


def test_basic_reservation(port_pool):
    """Test basic port reservation."""
    backend, frontend = port_pool.reserve("adw-test1")

    assert backend >= 9100
    assert backend <= 9199
    assert frontend >= 9200
    assert frontend <= 9299
    assert frontend - backend == 100  # Offset of 100


def test_idempotent_reservation(port_pool):
    """Test that reserving same ADW returns same ports."""
    backend1, frontend1 = port_pool.reserve("adw-test1")
    backend2, frontend2 = port_pool.reserve("adw-test1")

    assert backend1 == backend2
    assert frontend1 == frontend2


def test_unique_allocations(port_pool):
    """Test that different ADWs get different ports."""
    backend1, frontend1 = port_pool.reserve("adw-test1")
    backend2, frontend2 = port_pool.reserve("adw-test2")

    assert backend1 != backend2
    assert frontend1 != frontend2


def test_release(port_pool):
    """Test port release."""
    backend, frontend = port_pool.reserve("adw-test1")

    # Should return True when releasing existing allocation
    assert port_pool.release("adw-test1") is True

    # Should return False when releasing non-existent allocation
    assert port_pool.release("adw-test1") is False


def test_reuse_after_release(port_pool):
    """Test that released ports can be reused."""
    backend1, frontend1 = port_pool.reserve("adw-test1")
    port_pool.release("adw-test1")

    backend2, frontend2 = port_pool.reserve("adw-test2")

    # Should reuse the released slot (first available)
    assert backend2 == backend1
    assert frontend2 == frontend1


def test_get_allocation(port_pool):
    """Test getting current allocation."""
    backend, frontend = port_pool.reserve("adw-test1")

    allocation = port_pool.get_allocation("adw-test1")
    assert allocation == (backend, frontend)

    # Non-existent should return None
    assert port_pool.get_allocation("adw-nonexistent") is None


def test_pool_status(port_pool):
    """Test pool status reporting."""
    status = port_pool.get_pool_status()

    assert status["allocated"] == 0
    assert status["available"] == 100
    assert status["total"] == 100
    assert status["utilization_percent"] == 0.0

    # Allocate some
    port_pool.reserve("adw-test1")
    port_pool.reserve("adw-test2")

    status = port_pool.get_pool_status()
    assert status["allocated"] == 2
    assert status["available"] == 98
    assert status["utilization_percent"] == 2.0


def test_pool_exhaustion(port_pool):
    """Test that pool correctly reports exhaustion."""
    # Allocate all 100 slots
    for i in range(100):
        port_pool.reserve(f"adw-test{i}")

    # 101st should raise RuntimeError
    with pytest.raises(RuntimeError, match="Port pool exhausted"):
        port_pool.reserve("adw-test-overflow")


def test_persistence_save(port_pool, temp_persistence_dir):
    """Test that allocations are persisted to file."""
    port_pool.reserve("adw-test1")
    port_pool.reserve("adw-test2")

    persistence_file = temp_persistence_dir / "port_allocations.json"
    assert persistence_file.exists()

    with open(persistence_file, 'r') as f:
        data = json.load(f)

    assert "adw-test1" in data
    assert "adw-test2" in data
    assert data["adw-test1"]["backend"] >= 9100
    assert "allocated_at" in data["adw-test1"]


def test_persistence_load(temp_persistence_dir):
    """Test that allocations are loaded from file on init."""
    persistence_file = temp_persistence_dir / "port_allocations.json"

    # Create persistence file manually
    allocations = {
        "adw-existing": {
            "backend": 9105,
            "frontend": 9205,
            "allocated_at": datetime.now().isoformat()
        }
    }

    persistence_file.parent.mkdir(parents=True, exist_ok=True)
    with open(persistence_file, 'w') as f:
        json.dump(allocations, f)

    # Create new pool - should load existing allocations
    with patch.object(PortPool, 'PERSISTENCE_FILE', persistence_file):
        pool = PortPool()

    allocation = pool.get_allocation("adw-existing")
    assert allocation == (9105, 9205)


def test_cleanup_stale(port_pool):
    """Test cleanup of stale allocations."""
    # Allocate some ports
    port_pool.reserve("adw-fresh")
    port_pool.reserve("adw-stale")

    # Manually set allocated_at for stale one
    old_time = datetime.now() - timedelta(hours=25)
    port_pool._allocations["adw-stale"]["allocated_at"] = old_time.isoformat()

    # Cleanup stale (>24 hours)
    removed = port_pool.cleanup_stale(max_age_hours=24)

    assert removed == 1
    assert port_pool.get_allocation("adw-fresh") is not None
    assert port_pool.get_allocation("adw-stale") is None


def test_singleton_pattern():
    """Test that get_port_pool returns same instance."""
    pool1 = get_port_pool()
    pool2 = get_port_pool()

    assert pool1 is pool2


def test_thread_safety():
    """Test thread-safe concurrent operations."""
    import threading

    pool = PortPool()
    results = {}
    errors = []

    def reserve_port(adw_id):
        try:
            backend, frontend = pool.reserve(adw_id)
            results[adw_id] = (backend, frontend)
        except Exception as e:
            errors.append((adw_id, e))

    # Start 20 threads reserving ports
    threads = []
    for i in range(20):
        t = threading.Thread(target=reserve_port, args=(f"adw-thread{i}",))
        threads.append(t)
        t.start()

    # Wait for all
    for t in threads:
        t.join()

    # Should have no errors
    assert len(errors) == 0

    # Should have 20 unique allocations
    assert len(results) == 20

    # All should be unique
    backends = [b for b, f in results.values()]
    assert len(backends) == len(set(backends))  # No duplicates
```

### Step 4: Integrate with Worktree Setup (30 min)

**Read current implementation:**

```bash
grep -n "9100\|9200\|port" adws/adw_modules/worktree_setup.py
```

**Modify `worktree_setup.py`:**

Find the function that allocates ports (likely `setup_worktree` or similar) and replace the deterministic hash logic with PortPool:

```python
# OLD CODE (find and replace):
# backend_port = 9100 + (hash(adw_id) % 15)
# frontend_port = 9200 + (hash(adw_id) % 15)

# NEW CODE:
from adw_modules.port_pool import get_port_pool

def setup_worktree(..., adw_id, ...):
    # ... existing code ...

    # Reserve ports from pool
    port_pool = get_port_pool()
    backend_port, frontend_port = port_pool.reserve(adw_id)

    logger.info(f"Allocated ports for {adw_id}: backend={backend_port}, frontend={frontend_port}")

    # ... rest of existing code using backend_port and frontend_port ...
```

**Add cleanup on workflow completion:**

Find ADW workflow completion handlers (likely in cleanup phase or main workflow files) and add:

```python
from adw_modules.port_pool import get_port_pool

def cleanup_workflow(adw_id):
    # ... existing cleanup ...

    # Release ports back to pool
    port_pool = get_port_pool()
    port_pool.release(adw_id)

    # ... rest of cleanup ...
```

### Step 5: Run Tests (15 min)

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws

# Run port pool tests
pytest tests/test_port_pool.py -v

# Expected output:
# test_basic_reservation PASSED
# test_idempotent_reservation PASSED
# test_unique_allocations PASSED
# test_release PASSED
# test_reuse_after_release PASSED
# test_get_allocation PASSED
# test_pool_status PASSED
# test_pool_exhaustion PASSED
# test_persistence_save PASSED
# test_persistence_load PASSED
# test_cleanup_stale PASSED
# test_singleton_pattern PASSED
# test_thread_safety PASSED
# ================== 13 passed ==================
```

If tests fail:
- Check import paths
- Verify PERSISTENCE_FILE path is correct
- Check threading logic
- Review error messages

### Step 6: Manual Integration Test (20 min)

Test with a real ADW workflow:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Check pool status before
python3 -c "from adws.adw_modules.port_pool import get_port_pool; print(get_port_pool().get_pool_status())"

# Run a test ADW workflow (use smallest one)
cd adws
# Find a quick workflow to test - check adws/ directory for simplest one
ls -la *.py | grep -i plan

# Or manually test reservation
python3 -c "
from adw_modules.port_pool import get_port_pool
pool = get_port_pool()
backend, frontend = pool.reserve('adw-manual-test')
print(f'Reserved: backend={backend}, frontend={frontend}')
print(f'Pool status: {pool.get_pool_status()}')
pool.release('adw-manual-test')
print(f'After release: {pool.get_pool_status()}')
"
```

**Verify persistence:**

```bash
cat /Users/Warmonger0/tac/tac-webbuilder/agents/port_allocations.json
```

Should show JSON with current allocations.

### Step 7: Document Port Pool Usage (15 min)

Create or update documentation explaining the port pool system.

**Add to `adws/README.md`:**

```markdown
## Port Management

ADW workflows use a port pool system to prevent collisions:

- **Backend Ports:** 9100-9199 (100 slots)
- **Frontend Ports:** 9200-9299 (100 slots)
- **Persistence:** `agents/port_allocations.json`
- **Capacity:** Up to 100 concurrent ADW workflows

### How It Works

1. **Reservation:** When an ADW workflow starts, it reserves a backend/frontend port pair
2. **Persistence:** Allocations are saved to JSON file (survives restarts)
3. **Release:** When workflow completes, ports are released back to pool
4. **Cleanup:** Stale allocations (>24 hours) can be cleaned up manually

### Usage

Ports are automatically managed by the ADW system. No manual intervention needed.

**Check pool status:**
```bash
python3 -c "from adws.adw_modules.port_pool import get_port_pool; print(get_port_pool().get_pool_status())"
```

**Cleanup stale allocations:**
```bash
python3 -c "from adws.adw_modules.port_pool import get_port_pool; print(f'Cleaned {get_port_pool().cleanup_stale()} stale allocations')"
```

**Manual port release:**
```bash
python3 -c "from adws.adw_modules.port_pool import get_port_pool; get_port_pool().release('adw-abc123')"
```
```

---

## Success Criteria

- ✅ PortPool class created with all methods (reserve, release, get_allocation, get_pool_status, cleanup_stale)
- ✅ Singleton pattern implemented (get_port_pool function)
- ✅ Thread-safe operations (all methods use locking)
- ✅ Persistence working (agents/port_allocations.json created and loaded)
- ✅ All 13 tests passing
- ✅ Integration with worktree_setup.py complete
- ✅ Port release on workflow completion implemented
- ✅ Documentation updated
- ✅ Manual test confirms reservation/release cycle works

---

## Files Expected to Change

**Created (3):**
- `adws/adw_modules/port_pool.py` (~250 lines)
- `adws/tests/test_port_pool.py` (~200 lines)
- `agents/port_allocations.json` (auto-created on first reservation)

**Modified (2-3):**
- `adws/adw_modules/worktree_setup.py` (replace hash-based allocation with PortPool)
- `adws/README.md` (add Port Management section)
- Potentially: ADW workflow cleanup handlers (add port release)

---

## Troubleshooting

### Import Errors

```bash
# If "ModuleNotFoundError: No module named 'adw_modules'"
cd adws
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/test_port_pool.py -v
```

### Permission Errors

```bash
# If cannot write to agents/port_allocations.json
ls -la agents/
chmod 755 agents/
```

### Persistence File Not Found

```bash
# Check if agents directory exists
mkdir -p agents/
```

### Port Still In Use

```bash
# If port conflict detected
lsof -i :9100
kill <PID>

# Or use port pool cleanup
python3 -c "from adws.adw_modules.port_pool import get_port_pool; get_port_pool().cleanup_stale(max_age_hours=0)"
```

### Tests Fail on Thread Safety

This usually indicates:
- Missing lock acquisition
- Shared state modification outside lock
- Review `_lock` usage in all methods

---

## Estimated Time

- Step 1 (Understand current): 15 min
- Step 2 (Create PortPool): 45-60 min
- Step 3 (Create tests): 45 min
- Step 4 (Integration): 30 min
- Step 5 (Run tests): 15 min
- Step 6 (Manual test): 20 min
- Step 7 (Documentation): 15 min

**Total: 3-3.5 hours**

---

## Session Completion Instructions

When you finish this session, provide a completion summary in this **EXACT FORMAT:**

```markdown
## ✅ Session 2 Complete - Port Pool Implementation

**Duration:** ~X hours
**Status:** Complete ✅
**Next:** Ready for Session 3 (Integration Checklist - Plan Phase)

### What Was Done

1. **Port Pool Module Created**
   - Created adws/adw_modules/port_pool.py (~250 lines)
   - Singleton pattern with get_port_pool() function
   - Thread-safe operations with _lock
   - 100-slot pool (9100-9199 backend, 9200-9299 frontend)

2. **Persistence Implemented**
   - Saves to agents/port_allocations.json
   - Auto-loads on initialization
   - Survives restarts

3. **Comprehensive Tests**
   - Created adws/tests/test_port_pool.py (13 tests)
   - All tests passing ✅
   - Coverage: basic reservation, idempotency, release, persistence, thread-safety

4. **Integration Complete**
   - Modified worktree_setup.py to use PortPool
   - Added port release on workflow completion
   - Tested with manual reservation/release cycle

5. **Documentation Updated**
   - Added Port Management section to adws/README.md
   - Included usage examples and troubleshooting

### Key Results

- ✅ Supports 100 concurrent ADW workflows (up from 15)
- ✅ Eliminates port collision risk
- ✅ Allocations persist across restarts
- ✅ Thread-safe for concurrent operations
- ✅ Stale allocation cleanup available

### Files Changed

**Created (3):**
- adws/adw_modules/port_pool.py
- adws/tests/test_port_pool.py
- agents/port_allocations.json

**Modified (2):**
- adws/adw_modules/worktree_setup.py
- adws/README.md

### Test Results

```
pytest tests/test_port_pool.py -v
================== 13 passed ==================
```

### Next Session

Session 3: Integration Checklist - Plan Phase (2-3 hours)
```

---

## Next Session Prompt Instructions

After providing the completion summary above, create the prompt for **Session 3: Integration Checklist - Plan Phase** using this template:

### Template for SESSION_3_PROMPT.md

```markdown
# Task: Generate Integration Checklist in Plan Phase

## Context
I'm working on the tac-webbuilder project. Features are sometimes built but not wired up (missing API routes, UI components not integrated, etc.). This session adds integration checklist generation to the Plan phase, which will be validated in the Ship phase (Session 4).

## Objective
Modify `adw_plan_iso.py` to generate an integration checklist when planning new features, ensuring all necessary integration points are identified upfront.

## Background Information
- **Problem:** Features built but missing integration (e.g., Pattern Detection UI schema exists but no UI component)
- **Solution:** Generate checklist in Plan phase → Validate in Ship phase (Session 4)
- **Checklist Items:**
  - [ ] API endpoint created
  - [ ] UI component created
  - [ ] Database migration added (if needed)
  - [ ] Documentation updated
  - [ ] Routing configured (backend + frontend)
  - [ ] Tests added

[... continue with full session structure similar to Session 2 ...]

## Session Completion Instructions
[Same format as Session 2]

## Next Session Prompt Instructions
[Same template structure]
```

**Save this prompt as:** `/Users/Warmonger0/tac/tac-webbuilder/SESSION_3_PROMPT.md`

---

**Ready to copy into a new chat!**

Run `/prime` first, then paste this entire prompt.
