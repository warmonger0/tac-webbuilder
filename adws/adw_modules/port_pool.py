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
    from adw_modules.port_pool import get_port_pool

    pool = get_port_pool()
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
            Dict with keys: allocated, available, total, utilization_percent, allocations

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
