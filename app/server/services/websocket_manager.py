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

import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts messages to all active clients.

    This class maintains a set of active WebSocket connections and provides methods
    for connecting new clients, disconnecting clients, and broadcasting messages to
    all connected clients. It also tracks the last known state for workflows, routes,
    and history to prevent redundant broadcasts when state hasn't changed.

    Additionally, this class supports event subscription for internal listeners
    (e.g., PhaseCoordinator) to receive event notifications without WebSocket connections.

    Attributes:
        active_connections: Set of currently active WebSocket connections
        last_workflow_state: Last broadcast workflow state (used to prevent redundant broadcasts)
        last_routes_state: Last broadcast routes state (used to prevent redundant broadcasts)
        last_history_state: Last broadcast history state (used to prevent redundant broadcasts)
        last_adw_monitor_state: Last broadcast ADW monitor state (used to prevent redundant broadcasts)
        event_subscribers: Dict mapping event types to lists of async handler callables

    Example:
        >>> manager = ConnectionManager()
        >>> await manager.connect(websocket)
        >>> await manager.broadcast({"type": "update", "data": "Hello"})
        >>> manager.disconnect(websocket)
        >>> # Event subscription
        >>> async def my_handler(event_data: dict):
        ...     print(f"Event: {event_data}")
        >>> manager.subscribe("workflow_completed", my_handler)
    """

    def __init__(self):
        """Initialize the ConnectionManager with empty connection set and state tracking."""
        self.active_connections: set[WebSocket] = set()
        self.last_workflow_state: dict | None = None
        self.last_routes_state: dict | None = None
        self.last_history_state: dict | None = None
        self.last_adw_monitor_state: str | None = None

        # Event subscription system for internal listeners (e.g., PhaseCoordinator)
        self.event_subscribers: dict[str, list[callable]] = {}

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
        logger.debug(f"[WS] Client connected. Total connections: {len(self.active_connections)}")

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
        logger.debug(f"[WS] Client disconnected. Total connections: {len(self.active_connections)}")

    def subscribe(self, event_type: str, handler: callable) -> None:
        """
        Subscribe a handler to an event type.

        This method registers an async callable to be invoked whenever an event
        of the specified type is broadcast. Multiple handlers can subscribe to
        the same event type. Handlers receive the event data dict as their only
        parameter.

        Args:
            event_type: Event type to subscribe to (e.g., "workflow_completed")
            handler: Async callable that receives event data dict

        Example:
            >>> async def my_handler(event_data: dict):
            ...     print(f"Received: {event_data}")
            >>> manager.subscribe("workflow_completed", my_handler)
            [WS] Handler subscribed to 'workflow_completed' events
        """
        if event_type not in self.event_subscribers:
            self.event_subscribers[event_type] = []

        self.event_subscribers[event_type].append(handler)
        logger.info(
            f"[WS] Handler '{handler.__name__}' subscribed to '{event_type}' events. "
            f"Total subscribers for '{event_type}': {len(self.event_subscribers[event_type])}"
        )

    async def broadcast(self, message: dict) -> None:
        """
        Broadcast a message to all active WebSocket connections AND event subscribers.

        This method attempts to send the provided message to all connected clients.
        If a send operation fails (e.g., due to a disconnected client), the error
        is logged and the problematic connection is tracked for cleanup. After
        attempting to send to all clients, any disconnected clients are automatically
        removed from the active connections set.

        Additionally, the message is dispatched to any registered event subscribers
        based on the message type.

        Args:
            message: Dictionary containing the message to broadcast (will be sent as JSON)

        Example:
            >>> await manager.broadcast({"type": "workflow_completed", "data": {...}})
            [WS] Broadcasting message to 3 clients
            [WS] Dispatching to 2 workflow_completed subscribers
            [WS] Broadcast successful to 3 clients

        Note:
            - Failed connections are automatically cleaned up
            - Individual client errors don't prevent broadcasts to other clients
            - All exceptions during broadcast are logged with full details
            - Event subscribers are called asynchronously and errors are logged
        """
        # 1. Broadcast to WebSocket clients (existing logic)
        if self.active_connections:
            logger.debug(f"[WS] Broadcasting message to {len(self.active_connections)} clients")
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
                logger.debug(f"[WS] Broadcast successful to {len(self.active_connections)} clients")

        # 2. Dispatch to event subscribers
        event_type = message.get("type")

        if event_type and event_type in self.event_subscribers:
            subscribers = self.event_subscribers[event_type]
            logger.debug(f"[WS] Dispatching to {len(subscribers)} '{event_type}' subscribers")

            event_data = message.get("data", {})
            for handler in subscribers:
                try:
                    await handler(event_data)
                except Exception as e:
                    logger.error(
                        f"[WS] Event handler error for '{event_type}': {e}",
                        exc_info=True
                    )


# Global singleton instance
# This ensures all imports use the same instance across module reloads
_global_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """
    Get or create the global ConnectionManager singleton.

    Returns:
        The global ConnectionManager instance

    Example:
        >>> from services.websocket_manager import get_connection_manager
        >>> manager = get_connection_manager()
        >>> manager.subscribe("my_event", handler)
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = ConnectionManager()
        logger.info("[WS] Created global ConnectionManager singleton")
    return _global_manager
