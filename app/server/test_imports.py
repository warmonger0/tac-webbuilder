#!/usr/bin/env python
"""
Quick test to verify imports work correctly after changes.
"""
import sys
from pathlib import Path

# Add server to path
server_root = Path(__file__).parent
sys.path.insert(0, str(server_root))

print("Testing imports...")

# Test 1: Import SQLiteAdapter
try:
    from database.sqlite_adapter import SQLiteAdapter  # noqa: F401
    print("✓ Successfully imported SQLiteAdapter from database.sqlite_adapter")
except ImportError as e:
    print(f"✗ Failed to import SQLiteAdapter: {e}")
    sys.exit(1)

# Test 2: Import HopperSorter
try:
    from services.hopper_sorter import HopperSorter
    print("✓ Successfully imported HopperSorter")
except ImportError as e:
    print(f"✗ Failed to import HopperSorter: {e}")
    sys.exit(1)

# Test 3: Import PhaseQueueService
try:
    from services.phase_queue_service import PhaseQueueService
    print("✓ Successfully imported PhaseQueueService")
except ImportError as e:
    print(f"✗ Failed to import PhaseQueueService: {e}")
    sys.exit(1)

# Test 4: Import PhaseQueueRepository
try:
    from repositories.phase_queue_repository import PhaseQueueRepository
    print("✓ Successfully imported PhaseQueueRepository")
except ImportError as e:
    print(f"✗ Failed to import PhaseQueueRepository: {e}")
    sys.exit(1)

# Test 5: Verify HopperSorter accepts db_path parameter
try:
    import inspect
    sig = inspect.signature(HopperSorter.__init__)
    params = list(sig.parameters.keys())
    if 'db_path' in params:
        print("✓ HopperSorter.__init__ accepts db_path parameter")
    else:
        print(f"✗ HopperSorter.__init__ missing db_path parameter. Parameters: {params}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error checking HopperSorter signature: {e}")
    sys.exit(1)

# Test 6: Verify PhaseQueueService accepts db_path parameter
try:
    sig = inspect.signature(PhaseQueueService.__init__)
    params = list(sig.parameters.keys())
    if 'db_path' in params:
        print("✓ PhaseQueueService.__init__ accepts db_path parameter")
    else:
        print(f"✗ PhaseQueueService.__init__ missing db_path parameter. Parameters: {params}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error checking PhaseQueueService signature: {e}")
    sys.exit(1)

# Test 7: Verify PhaseQueueRepository accepts db_path parameter
try:
    sig = inspect.signature(PhaseQueueRepository.__init__)
    params = list(sig.parameters.keys())
    if 'db_path' in params:
        print("✓ PhaseQueueRepository.__init__ accepts db_path parameter")
    else:
        print(f"✗ PhaseQueueRepository.__init__ missing db_path parameter. Parameters: {params}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error checking PhaseQueueRepository signature: {e}")
    sys.exit(1)

print("\n✓ All imports and signatures verified successfully!")
