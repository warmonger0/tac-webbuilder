"""
WebSocket Connection Manager Module

This module provides centralized management of WebSocket connections for real-time
communication between the server and clients. It handles connection lifecycle,
message broadcasting, and automatic cleanup of disconnected clients.

Usage:
    from services.websocket_manager import ConnectionManager

    manager = ConnectionManager()

    # In WebSocket endpoint
    await manager.connect(websocket)
    try:
        # ... handle messages ...
    finally:
        manager.disconnect(websocket)

    # Broadcasting updates
    await manager.broadcast({"type": "workflow_update", "data": {...}})
"""

from fastapi import WebSocket
from typing import Set, Optional
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts messages to all active clients.

    This class maintains a set of active WebSocket connections and provides methods
    for connecting new clients, disconnecting clients, and broadcasting messages to
    all connected clients. It also tracks the last known state for workflows, routes,
    and history to prevent redundant broadcasts when state hasn't changed.

    Attributes:
        active_connections: Set of currently active WebSocket connections
        last_workflow_state: Last broadcast workflow state (used to prevent redundant broadcasts)
        last_routes_state: Last broadcast routes state (used to prevent redundant broadcasts)
        last_history_state: Last broadcast history state (used to prevent redundant broadcasts)

    Example:
        >>> manager = ConnectionManager()
        >>> await manager.connect(websocket)
        >>> await manager.broadcast({"type": "update", "data": "Hello"})
        >>> manager.disconnect(websocket)
    """

    def __init__(self):
        """Initialize the ConnectionManager with empty connection set and state tracking."""
        self.active_connections: Set[WebSocket] = set()
        self.last_workflow_state: Optional[dict] = None
        self.last_routes_state: Optional[dict] = None
        self.last_history_state: Optional[dict] = None

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.

        This method accepts the WebSocket connection and adds it to the set of
        active connections. It also logs the connection event with the current
        total number of active connections.

        Args:
            websocket: The WebSocket connection to accept and register

        Example:
            >>> await manager.connect(websocket)
            [WS] Client connected. Total connections: 1
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"[WS] Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Safely remove a WebSocket connection from the active set.

        This method uses discard() instead of remove() to safely handle cases
        where the WebSocket might not be in the set. It also logs the disconnection
        event with the remaining number of active connections.

        Args:
            websocket: The WebSocket connection to remove

        Example:
            >>> manager.disconnect(websocket)
            [WS] Client disconnected. Total connections: 0
        """
        self.active_connections.discard(websocket)
        logger.info(f"[WS] Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict) -> None:
        """
        Broadcast a message to all active WebSocket connections.

        This method attempts to send the provided message to all connected clients.
        If a send operation fails (e.g., due to a disconnected client), the error
        is logged and the problematic connection is tracked for cleanup. After
        attempting to send to all clients, any disconnected clients are automatically
        removed from the active connections set.

        Args:
            message: Dictionary containing the message to broadcast (will be sent as JSON)

        Example:
            >>> await manager.broadcast({"type": "workflow_update", "status": "running"})
            [WS] Broadcasting message to 3 clients
            [WS] Broadcast successful to 3 clients

        Note:
            - Failed connections are automatically cleaned up
            - Individual client errors don't prevent broadcasts to other clients
            - All exceptions during broadcast are logged with full details
        """
        if not self.active_connections:
            return

        logger.info(f"[WS] Broadcasting message to {len(self.active_connections)} clients")
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"[WS] Error broadcasting to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

        if not disconnected:
            logger.info(f"[WS] Broadcast successful to {len(self.active_connections)} clients")
