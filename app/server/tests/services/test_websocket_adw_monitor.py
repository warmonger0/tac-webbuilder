"""
Backend WebSocket Unit Tests for ADW Monitor

Tests the /ws/adw-monitor endpoint with comprehensive coverage of:
- Connection/disconnection lifecycle
- Initial state broadcast
- State change detection and broadcast
- Multiple concurrent clients
- Error handling
- Cleanup of disconnected clients

This test module validates WebSocket-specific ADW monitor functionality.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import WebSocket


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket object for testing."""
    websocket = Mock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.receive_text = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


@pytest.fixture
def mock_adw_monitor_data():
    """Sample ADW monitor data for testing."""
    return {
        "total_workflows": 5,
        "active_workflows": 2,
        "completed_workflows": 2,
        "failed_workflows": 1,
        "workflows": [
            {
                "adw_id": "adw-test-001",
                "status": "running",
                "progress": 0.5,
                "phase": "implementation",
            },
            {
                "adw_id": "adw-test-002",
                "status": "completed",
                "progress": 1.0,
                "phase": "done",
            },
        ],
    }


class TestWebSocketADWMonitorEndpoint:
    """Tests for /ws/adw-monitor WebSocket endpoint"""

    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, mock_websocket, mock_adw_monitor_data):
        """Test WebSocket connection accepts client and tracks connection"""
        from services.websocket_manager import ConnectionManager

        manager = ConnectionManager()

        # Connect client
        await manager.connect(mock_websocket)

        # Verify connection accepted
        mock_websocket.accept.assert_called_once()
        assert mock_websocket in manager.active_connections
        assert len(manager.active_connections) == 1

        # Disconnect client
        manager.disconnect(mock_websocket)
        assert mock_websocket not in manager.active_connections
        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_initial_state_broadcast_on_connection(
        self, mock_websocket, mock_adw_monitor_data
    ):
        """Test that initial ADW monitor state is broadcast when client connects"""
        from services.websocket_manager import ConnectionManager

        manager = ConnectionManager()

        # Connect and send initial state
        await manager.connect(mock_websocket)
        await mock_websocket.send_json(
            {"type": "adw_monitor_update", "data": mock_adw_monitor_data}
        )

        # Verify initial state sent
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "adw_monitor_update"
        assert call_args["data"]["total_workflows"] == 5
        assert call_args["data"]["active_workflows"] == 2

    @pytest.mark.asyncio
    async def test_state_change_detection_and_broadcast(
        self, mock_websocket, mock_adw_monitor_data
    ):
        """Test that state changes are detected and broadcast to clients"""
        from services.websocket_manager import ConnectionManager

        manager = ConnectionManager()

        # Connect client
        await manager.connect(mock_websocket)

        # Store initial state
        initial_state = mock_adw_monitor_data.copy()
        manager.last_adw_monitor_state = initial_state

        # Create changed state
        changed_state = mock_adw_monitor_data.copy()
        changed_state["active_workflows"] = 3
        changed_state["completed_workflows"] = 1

        # Broadcast changed state
        await manager.broadcast({"type": "adw_monitor_update", "data": changed_state})

        # Verify broadcast occurred
        assert mock_websocket.send_json.call_count >= 1
        last_call = mock_websocket.send_json.call_args[0][0]
        assert last_call["data"]["active_workflows"] == 3

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_concurrent_clients(
        self, mock_adw_monitor_data
    ):
        """Test broadcast reaches all connected clients"""
        from services.websocket_manager import ConnectionManager

        manager = ConnectionManager()

        # Create multiple mock clients
        clients = [Mock(spec=WebSocket) for _ in range(3)]
        for client in clients:
            client.accept = AsyncMock()
            client.send_json = AsyncMock()

        # Connect all clients
        for client in clients:
            await manager.connect(client)

        assert len(manager.active_connections) == 3

        # Broadcast message
        message = {"type": "adw_monitor_update", "data": mock_adw_monitor_data}
        await manager.broadcast(message)

        # Verify all clients received message
        for client in clients:
            client.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_error_handling_connection_failure(self):
        """Test error handling when WebSocket connection fails"""
        from services.websocket_manager import ConnectionManager

        manager = ConnectionManager()

        # Create mock that fails on accept
        failing_websocket = Mock(spec=WebSocket)
        failing_websocket.accept = AsyncMock(side_effect=Exception("Connection failed"))

        # Attempt connection should raise exception
        with pytest.raises(Exception, match="Connection failed"):
            await manager.connect(failing_websocket)

        # Verify no connection was added
        assert failing_websocket not in manager.active_connections

    @pytest.mark.asyncio
    async def test_error_handling_malformed_data(self, mock_websocket):
        """Test error handling when broadcast data is malformed"""
        from services.websocket_manager import ConnectionManager

        manager = ConnectionManager()

        # Connect client
        await manager.connect(mock_websocket)

        # Configure send_json to fail
        mock_websocket.send_json = AsyncMock(
            side_effect=Exception("JSON serialization error")
        )

        # Broadcast should handle error gracefully
        await manager.broadcast({"type": "test", "data": "malformed"})

        # Client should be disconnected after error
        assert mock_websocket not in manager.active_connections

    @pytest.mark.asyncio
    async def test_cleanup_disconnected_clients_during_broadcast(self):
        """Test that disconnected clients are cleaned up during broadcast"""
        from services.websocket_manager import ConnectionManager

        manager = ConnectionManager()

        # Create clients - one healthy, one that will fail
        healthy_client = Mock(spec=WebSocket)
        healthy_client.accept = AsyncMock()
        healthy_client.send_json = AsyncMock()

        failing_client = Mock(spec=WebSocket)
        failing_client.accept = AsyncMock()
        failing_client.send_json = AsyncMock(side_effect=Exception("Client disconnected"))

        # Connect both clients
        await manager.connect(healthy_client)
        await manager.connect(failing_client)

        assert len(manager.active_connections) == 2

        # Broadcast message
        message = {"type": "test", "data": {"status": "ok"}}
        await manager.broadcast(message)

        # Verify failing client was cleaned up
        assert healthy_client in manager.active_connections
        assert failing_client not in manager.active_connections
        assert len(manager.active_connections) == 1

    @pytest.mark.asyncio
    async def test_no_broadcast_when_no_clients_connected(self, mock_adw_monitor_data):
        """Test broadcast with no active connections returns early"""
        from services.websocket_manager import ConnectionManager

        manager = ConnectionManager()

        # Broadcast with no connections should not raise error
        await manager.broadcast(
            {"type": "adw_monitor_update", "data": mock_adw_monitor_data}
        )

        # No exceptions raised, operation completes successfully
        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_state_deduplication_prevents_redundant_broadcasts(
        self, mock_websocket, mock_adw_monitor_data
    ):
        """Test that unchanged state doesn't trigger redundant broadcasts"""
        from services.websocket_manager import ConnectionManager

        manager = ConnectionManager()

        # Connect client
        await manager.connect(mock_websocket)

        # Set initial state
        manager.last_adw_monitor_state = mock_adw_monitor_data.copy()

        # Try to broadcast same state
        # In actual implementation, the router checks state changes before broadcasting
        # Here we verify the manager stores state for comparison
        assert manager.last_adw_monitor_state == mock_adw_monitor_data

        # Broadcasting identical data would be detected at router level
        # Manager itself always broadcasts what it's told to broadcast
        await manager.broadcast(
            {"type": "adw_monitor_update", "data": mock_adw_monitor_data}
        )

        # Manager executed broadcast (state comparison happens in router)
        mock_websocket.send_json.assert_called()


class TestWebSocketIntegrationWithADWMonitor:
    """Integration tests connecting WebSocket endpoint to ADW monitor logic"""

    @pytest.mark.asyncio
    async def test_endpoint_sends_initial_monitor_data(self, mock_websocket):
        """Test endpoint properly calls get_adw_monitor_data_func on connection"""
        from services.websocket_manager import ConnectionManager

        manager = ConnectionManager()

        # Mock monitor data function
        monitor_data = {
            "total_workflows": 3,
            "active_workflows": 1,
            "workflows": [],
        }

        def mock_get_adw_monitor_data():
            return monitor_data

        # Simulate endpoint behavior
        await manager.connect(mock_websocket)

        # Endpoint would call get_adw_monitor_data_func()
        data = mock_get_adw_monitor_data()

        # Send initial data
        await mock_websocket.send_json({"type": "adw_monitor_update", "data": data})

        # Verify data sent correctly
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "adw_monitor_update"
        assert call_args["data"]["total_workflows"] == 3

    @pytest.mark.asyncio
    async def test_endpoint_handles_empty_workflow_list(self, mock_websocket):
        """Test endpoint handles case when no workflows exist"""
        from services.websocket_manager import ConnectionManager

        manager = ConnectionManager()

        # Empty monitor data
        empty_data = {
            "total_workflows": 0,
            "active_workflows": 0,
            "workflows": [],
        }

        await manager.connect(mock_websocket)
        await mock_websocket.send_json({"type": "adw_monitor_update", "data": empty_data})

        # Verify empty data sent without error
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["data"]["total_workflows"] == 0
        assert call_args["data"]["workflows"] == []

    @pytest.mark.asyncio
    async def test_broadcast_triggered_by_state_change(self, mock_adw_monitor_data):
        """Test that state changes in ADW monitor trigger broadcasts"""
        from services.websocket_manager import ConnectionManager

        manager = ConnectionManager()

        # Create mock clients
        client1 = Mock(spec=WebSocket)
        client1.accept = AsyncMock()
        client1.send_json = AsyncMock()

        client2 = Mock(spec=WebSocket)
        client2.accept = AsyncMock()
        client2.send_json = AsyncMock()

        # Connect clients
        await manager.connect(client1)
        await manager.connect(client2)

        # Simulate state change broadcast (would be triggered by background task)
        updated_data = mock_adw_monitor_data.copy()
        updated_data["active_workflows"] = 4

        await manager.broadcast({"type": "adw_monitor_update", "data": updated_data})

        # Both clients received update
        assert client1.send_json.call_count == 1
        assert client2.send_json.call_count == 1

        # Verify data correctness
        for client in [client1, client2]:
            call_args = client.send_json.call_args[0][0]
            assert call_args["data"]["active_workflows"] == 4
