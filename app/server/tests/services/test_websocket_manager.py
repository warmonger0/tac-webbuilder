"""
Tests for the WebSocket Connection Manager.

This module contains comprehensive unit tests for the ConnectionManager class,
which handles WebSocket connection lifecycle management, message broadcasting,
and automatic cleanup of disconnected clients.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from services.websocket_manager import ConnectionManager


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket object for testing."""
    websocket = Mock()
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    return websocket


@pytest.fixture
def connection_manager():
    """Create a fresh ConnectionManager instance for each test."""
    return ConnectionManager()


class TestConnectionManager:
    """Test suite for the ConnectionManager class."""

    # Tests for connect() method
    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, connection_manager, mock_websocket):
        """Test that connect() accepts the websocket connection."""
        await connection_manager.connect(mock_websocket)
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_adds_to_active_connections(self, connection_manager, mock_websocket):
        """Test that connect() adds websocket to active connections."""
        await connection_manager.connect(mock_websocket)
        assert mock_websocket in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_connect_increases_connection_count(self, connection_manager, mock_websocket):
        """Test that connection count increases correctly."""
        assert len(connection_manager.active_connections) == 0
        await connection_manager.connect(mock_websocket)
        assert len(connection_manager.active_connections) == 1

    @pytest.mark.asyncio
    async def test_connect_multiple_connections(self, connection_manager):
        """Test connecting multiple websockets."""
        websocket1 = Mock()
        websocket1.accept = AsyncMock()
        websocket2 = Mock()
        websocket2.accept = AsyncMock()
        websocket3 = Mock()
        websocket3.accept = AsyncMock()

        await connection_manager.connect(websocket1)
        await connection_manager.connect(websocket2)
        await connection_manager.connect(websocket3)

        assert len(connection_manager.active_connections) == 3
        assert websocket1 in connection_manager.active_connections
        assert websocket2 in connection_manager.active_connections
        assert websocket3 in connection_manager.active_connections

    # Tests for disconnect() method
    def test_disconnect_removes_from_active_connections(self, connection_manager, mock_websocket):
        """Test that disconnect() removes websocket from active connections."""
        # First add the websocket
        connection_manager.active_connections.add(mock_websocket)
        assert mock_websocket in connection_manager.active_connections

        # Then disconnect it
        connection_manager.disconnect(mock_websocket)
        assert mock_websocket not in connection_manager.active_connections

    def test_disconnect_decreases_connection_count(self, connection_manager, mock_websocket):
        """Test that connection count decreases correctly."""
        connection_manager.active_connections.add(mock_websocket)
        assert len(connection_manager.active_connections) == 1

        connection_manager.disconnect(mock_websocket)
        assert len(connection_manager.active_connections) == 0

    def test_disconnect_handles_non_existent_websocket(self, connection_manager, mock_websocket):
        """Test that disconnect() handles removing non-existent websockets gracefully."""
        # Should not raise an error when disconnecting a websocket that was never connected
        connection_manager.disconnect(mock_websocket)
        assert len(connection_manager.active_connections) == 0

    def test_disconnect_multiple_calls_same_websocket(self, connection_manager, mock_websocket):
        """Test that multiple disconnect calls on same websocket don't cause errors."""
        connection_manager.active_connections.add(mock_websocket)
        connection_manager.disconnect(mock_websocket)
        connection_manager.disconnect(mock_websocket)  # Second call should not error
        assert len(connection_manager.active_connections) == 0

    # Tests for broadcast() method
    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_connections(self, connection_manager):
        """Test that broadcast sends messages to all connected clients."""
        websocket1 = Mock()
        websocket1.send_json = AsyncMock()
        websocket2 = Mock()
        websocket2.send_json = AsyncMock()
        websocket3 = Mock()
        websocket3.send_json = AsyncMock()

        connection_manager.active_connections.add(websocket1)
        connection_manager.active_connections.add(websocket2)
        connection_manager.active_connections.add(websocket3)

        message = {"type": "test", "data": "hello"}
        await connection_manager.broadcast(message)

        websocket1.send_json.assert_called_once_with(message)
        websocket2.send_json.assert_called_once_with(message)
        websocket3.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_with_single_connection(self, connection_manager, mock_websocket):
        """Test broadcast with a single connection."""
        connection_manager.active_connections.add(mock_websocket)

        message = {"type": "update", "status": "running"}
        await connection_manager.broadcast(message)

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_with_empty_connection_set(self, connection_manager):
        """Test broadcast with no connected clients."""
        message = {"type": "test", "data": "hello"}
        # Should not raise an error and should return early
        await connection_manager.broadcast(message)
        assert len(connection_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast_json_message_format(self, connection_manager, mock_websocket):
        """Test that broadcast sends messages in correct JSON format."""
        connection_manager.active_connections.add(mock_websocket)

        message = {
            "type": "workflow_update",
            "data": {
                "status": "completed",
                "progress": 100
            }
        }
        await connection_manager.broadcast(message)

        mock_websocket.send_json.assert_called_once_with(message)

    # Tests for broadcast error handling
    @pytest.mark.asyncio
    async def test_broadcast_continues_on_client_failure(self, connection_manager):
        """Test that broadcast continues to other clients when one fails."""
        websocket1 = Mock()
        websocket1.send_json = AsyncMock(side_effect=Exception("Connection error"))
        websocket2 = Mock()
        websocket2.send_json = AsyncMock()
        websocket3 = Mock()
        websocket3.send_json = AsyncMock()

        connection_manager.active_connections.add(websocket1)
        connection_manager.active_connections.add(websocket2)
        connection_manager.active_connections.add(websocket3)

        message = {"type": "test", "data": "hello"}
        await connection_manager.broadcast(message)

        # All three should have been attempted
        websocket1.send_json.assert_called_once_with(message)
        websocket2.send_json.assert_called_once_with(message)
        websocket3.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_removes_disconnected_clients(self, connection_manager):
        """Test that disconnected clients are removed during broadcast."""
        websocket1 = Mock()
        websocket1.send_json = AsyncMock(side_effect=Exception("Disconnected"))
        websocket2 = Mock()
        websocket2.send_json = AsyncMock()

        connection_manager.active_connections.add(websocket1)
        connection_manager.active_connections.add(websocket2)

        assert len(connection_manager.active_connections) == 2

        message = {"type": "test", "data": "hello"}
        await connection_manager.broadcast(message)

        # websocket1 should be removed, websocket2 should remain
        assert websocket1 not in connection_manager.active_connections
        assert websocket2 in connection_manager.active_connections
        assert len(connection_manager.active_connections) == 1

    @pytest.mark.asyncio
    async def test_broadcast_handles_multiple_failures(self, connection_manager):
        """Test broadcast with multiple client failures during single operation."""
        websocket1 = Mock()
        websocket1.send_json = AsyncMock(side_effect=Exception("Error 1"))
        websocket2 = Mock()
        websocket2.send_json = AsyncMock(side_effect=Exception("Error 2"))
        websocket3 = Mock()
        websocket3.send_json = AsyncMock()

        connection_manager.active_connections.add(websocket1)
        connection_manager.active_connections.add(websocket2)
        connection_manager.active_connections.add(websocket3)

        assert len(connection_manager.active_connections) == 3

        message = {"type": "test", "data": "hello"}
        await connection_manager.broadcast(message)

        # Failed connections should be removed, successful one remains
        assert websocket1 not in connection_manager.active_connections
        assert websocket2 not in connection_manager.active_connections
        assert websocket3 in connection_manager.active_connections
        assert len(connection_manager.active_connections) == 1

    @pytest.mark.asyncio
    async def test_broadcast_all_clients_fail(self, connection_manager):
        """Test broadcast when all clients fail."""
        websocket1 = Mock()
        websocket1.send_json = AsyncMock(side_effect=Exception("Error 1"))
        websocket2 = Mock()
        websocket2.send_json = AsyncMock(side_effect=Exception("Error 2"))

        connection_manager.active_connections.add(websocket1)
        connection_manager.active_connections.add(websocket2)

        message = {"type": "test", "data": "hello"}
        await connection_manager.broadcast(message)

        # All connections should be cleaned up
        assert len(connection_manager.active_connections) == 0

    # Tests for state tracking
    def test_state_tracking_initialization(self, connection_manager):
        """Test that state tracking attributes initialize to None."""
        assert connection_manager.last_workflow_state is None
        assert connection_manager.last_routes_state is None
        assert connection_manager.last_history_state is None

    def test_state_tracking_can_be_set(self, connection_manager):
        """Test that state tracking attributes can be set."""
        workflow_state = {"status": "running", "progress": 50}
        routes_state = {"routes": ["/api/v1/test"]}
        history_state = {"entries": []}

        connection_manager.last_workflow_state = workflow_state
        connection_manager.last_routes_state = routes_state
        connection_manager.last_history_state = history_state

        assert connection_manager.last_workflow_state == workflow_state
        assert connection_manager.last_routes_state == routes_state
        assert connection_manager.last_history_state == history_state

    def test_state_tracking_independent_from_connections(self, connection_manager, mock_websocket):
        """Test that state tracking doesn't interfere with connection management."""
        # Set some state
        connection_manager.last_workflow_state = {"status": "running"}

        # Add connection
        connection_manager.active_connections.add(mock_websocket)
        assert len(connection_manager.active_connections) == 1

        # State should remain unchanged
        assert connection_manager.last_workflow_state == {"status": "running"}

        # Disconnect
        connection_manager.disconnect(mock_websocket)
        assert len(connection_manager.active_connections) == 0

        # State should still remain unchanged
        assert connection_manager.last_workflow_state == {"status": "running"}

    @pytest.mark.asyncio
    async def test_state_tracking_during_broadcast(self, connection_manager, mock_websocket):
        """Test that state tracking persists during broadcast operations."""
        connection_manager.last_workflow_state = {"status": "completed"}
        connection_manager.active_connections.add(mock_websocket)

        message = {"type": "update", "data": "test"}
        await connection_manager.broadcast(message)

        # State should remain unchanged after broadcast
        assert connection_manager.last_workflow_state == {"status": "completed"}

    # Integration test for concurrent operations
    @pytest.mark.asyncio
    async def test_concurrent_connect_disconnect_broadcast(self, connection_manager):
        """Test concurrent operations: connect, disconnect, and broadcast."""
        websocket1 = Mock()
        websocket1.accept = AsyncMock()
        websocket1.send_json = AsyncMock()
        websocket2 = Mock()
        websocket2.accept = AsyncMock()
        websocket2.send_json = AsyncMock()
        websocket3 = Mock()
        websocket3.accept = AsyncMock()
        websocket3.send_json = AsyncMock()

        # Connect three clients
        await connection_manager.connect(websocket1)
        await connection_manager.connect(websocket2)
        await connection_manager.connect(websocket3)
        assert len(connection_manager.active_connections) == 3

        # Broadcast to all
        message1 = {"type": "test1", "data": "first"}
        await connection_manager.broadcast(message1)

        # Disconnect one client
        connection_manager.disconnect(websocket2)
        assert len(connection_manager.active_connections) == 2

        # Broadcast to remaining clients
        message2 = {"type": "test2", "data": "second"}
        await connection_manager.broadcast(message2)

        # Verify websocket1 and websocket3 received both messages
        assert websocket1.send_json.call_count == 2
        assert websocket3.send_json.call_count == 2

        # Verify websocket2 only received first message
        assert websocket2.send_json.call_count == 1
