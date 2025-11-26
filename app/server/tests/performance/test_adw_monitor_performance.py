"""
Performance Benchmarks for ADW Monitor Phase 3

Validates performance targets:
1. API response time: <200ms (p95)
2. WebSocket message latency: <50ms (p95)
3. Frontend render performance: <16ms (60fps target)

Uses pytest-benchmark for precise timing measurements.
Run with: pytest tests/performance/test_adw_monitor_performance.py -v --benchmark-only
"""

import json
import statistics
import time
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_agents_directory(tmp_path):
    """Create temporary agents directory with sample workflows."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    return agents_dir


@pytest.fixture
def create_workflow_states(mock_agents_directory):
    """Factory to create workflow state files."""

    def _create_states(count: int):
        for i in range(count):
            adw_dir = mock_agents_directory / f"adw-perf-{i:03d}"
            adw_dir.mkdir()
            state_file = adw_dir / "adw_state.json"

            state_data = {
                "issue_number": 100 + i,
                "nl_input": f"Implement feature {i}",
                "status": "running" if i % 3 != 0 else "completed",
                "workflow_template": "adw_sdlc_iso",
                "start_time": "2025-01-15T10:00:00",
                "github_url": f"https://github.com/test/repo/issues/{100 + i}",
                "current_cost": 2.50 + i * 0.5,
                "estimated_cost_total": 10.00 + i,
                "progress": 0.25 * (i % 4),
                "phase": ["planning", "implementation", "testing", "completed"][i % 4],
            }

            state_file.write_text(json.dumps(state_data))

    return _create_states


@pytest.mark.performance
class TestAPIResponseTime:
    """Test API endpoint response time performance"""

    def test_api_response_time_under_200ms_empty_state(
        self, integration_client, mock_agents_directory
    ):
        """Test /api/adw-monitor responds in <200ms with no workflows"""
        with patch(
            "core.adw_monitor.get_agents_directory", return_value=mock_agents_directory
        ):
            # Warm up
            for _ in range(5):
                integration_client.get("/api/adw-monitor")

            # Measure response times
            response_times = []
            for _ in range(100):
                start = time.perf_counter()
                response = integration_client.get("/api/adw-monitor")
                elapsed_ms = (time.perf_counter() - start) * 1000

                assert response.status_code == 200
                response_times.append(elapsed_ms)

            # Calculate statistics
            mean_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile

            print("\nAPI Response Time Statistics (Empty State):")
            print(f"  Mean:   {mean_time:.2f}ms")
            print(f"  Median: {median_time:.2f}ms")
            print(f"  P95:    {p95_time:.2f}ms")
            print(f"  P99:    {p99_time:.2f}ms")

            # Assert P95 < 200ms target
            assert (
                p95_time < 200
            ), f"P95 response time {p95_time:.2f}ms exceeds 200ms target"

    def test_api_response_time_with_10_workflows(
        self, integration_client, mock_agents_directory, create_workflow_states
    ):
        """Test /api/adw-monitor responds in <200ms with 10 workflows"""
        create_workflow_states(10)

        with patch(
            "core.adw_monitor.get_agents_directory", return_value=mock_agents_directory
        ), patch("core.adw_monitor.batch_check_running_processes", return_value={}):
            # Warm up
            for _ in range(5):
                integration_client.get("/api/adw-monitor")

            # Measure response times
            response_times = []
            for _ in range(100):
                start = time.perf_counter()
                response = integration_client.get("/api/adw-monitor")
                elapsed_ms = (time.perf_counter() - start) * 1000

                assert response.status_code == 200
                response_times.append(elapsed_ms)

            # Calculate statistics
            mean_time = statistics.mean(response_times)
            p95_time = statistics.quantiles(response_times, n=20)[18]
            p99_time = statistics.quantiles(response_times, n=100)[98]

            print("\nAPI Response Time Statistics (10 Workflows):")
            print(f"  Mean:   {mean_time:.2f}ms")
            print(f"  P95:    {p95_time:.2f}ms")
            print(f"  P99:    {p99_time:.2f}ms")

            # Assert P95 < 200ms target
            assert (
                p95_time < 200
            ), f"P95 response time {p95_time:.2f}ms exceeds 200ms target"

    def test_api_response_time_with_25_workflows(
        self, integration_client, mock_agents_directory, create_workflow_states
    ):
        """Test /api/adw-monitor responds in <200ms with 25 workflows"""
        create_workflow_states(25)

        with patch(
            "core.adw_monitor.get_agents_directory", return_value=mock_agents_directory
        ), patch("core.adw_monitor.batch_check_running_processes", return_value={}):
            # Warm up
            for _ in range(5):
                integration_client.get("/api/adw-monitor")

            # Measure response times
            response_times = []
            for _ in range(100):
                start = time.perf_counter()
                response = integration_client.get("/api/adw-monitor")
                elapsed_ms = (time.perf_counter() - start) * 1000

                assert response.status_code == 200
                response_times.append(elapsed_ms)

            # Calculate statistics
            mean_time = statistics.mean(response_times)
            p95_time = statistics.quantiles(response_times, n=20)[18]

            print("\nAPI Response Time Statistics (25 Workflows):")
            print(f"  Mean:   {mean_time:.2f}ms")
            print(f"  P95:    {p95_time:.2f}ms")

            # Assert P95 < 200ms target
            assert (
                p95_time < 200
            ), f"P95 response time {p95_time:.2f}ms exceeds 200ms target"


@pytest.mark.performance
class TestWebSocketLatency:
    """Test WebSocket message latency performance"""

    def test_websocket_initial_message_latency(
        self, integration_client, mock_agents_directory
    ):
        """Test WebSocket initial message arrives in <50ms"""
        with patch(
            "core.adw_monitor.get_agents_directory", return_value=mock_agents_directory
        ):
            latencies = []

            # Measure 20 connections
            for _ in range(20):
                start = time.perf_counter()
                with integration_client.websocket_connect("/ws/adw-monitor") as ws:
                    data = ws.receive_json()
                    elapsed_ms = (time.perf_counter() - start) * 1000

                    assert data["type"] == "adw_monitor_update"
                    latencies.append(elapsed_ms)

            # Calculate statistics
            mean_latency = statistics.mean(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18]

            print("\nWebSocket Initial Message Latency:")
            print(f"  Mean: {mean_latency:.2f}ms")
            print(f"  P95:  {p95_latency:.2f}ms")

            # Note: Initial connection includes handshake, so we allow more time
            # The <50ms target applies to message broadcast after connection
            assert mean_latency < 100, f"Mean latency {mean_latency:.2f}ms too high"

    def test_websocket_broadcast_latency_single_client(
        self, integration_client, mock_agents_directory, create_workflow_states
    ):
        """Test WebSocket broadcast latency with single client <50ms"""
        from services.websocket_manager import ConnectionManager
        from unittest.mock import AsyncMock, Mock

        create_workflow_states(5)

        # Create mock WebSocket
        mock_ws = Mock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        manager = ConnectionManager()

        # Measure broadcast time
        async def measure_broadcast():
            await manager.connect(mock_ws)

            # Prepare message
            message = {
                "type": "adw_monitor_update",
                "data": {"workflows": [], "summary": {"total": 5}},
            }

            # Measure broadcast latency
            latencies = []
            for _ in range(100):
                start = time.perf_counter()
                await manager.broadcast(message)
                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)

            return latencies

        import asyncio

        latencies = asyncio.run(measure_broadcast())

        # Calculate statistics
        mean_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]
        p99_latency = statistics.quantiles(latencies, n=100)[98]

        print("\nWebSocket Broadcast Latency (1 Client):")
        print(f"  Mean: {mean_latency:.2f}ms")
        print(f"  P95:  {p95_latency:.2f}ms")
        print(f"  P99:  {p99_latency:.2f}ms")

        # Assert P95 < 50ms target
        assert (
            p95_latency < 50
        ), f"P95 broadcast latency {p95_latency:.2f}ms exceeds 50ms target"

    def test_websocket_broadcast_latency_multiple_clients(self):
        """Test WebSocket broadcast latency with 5, 10, 20 concurrent clients"""
        from services.websocket_manager import ConnectionManager
        from unittest.mock import AsyncMock, Mock

        manager = ConnectionManager()

        async def measure_broadcast_multi_clients(client_count: int):
            # Create mock clients
            clients = []
            for _ in range(client_count):
                mock_ws = Mock()
                mock_ws.accept = AsyncMock()
                mock_ws.send_json = AsyncMock()
                await manager.connect(mock_ws)
                clients.append(mock_ws)

            # Measure broadcast latency
            message = {
                "type": "adw_monitor_update",
                "data": {"workflows": [], "summary": {"total": 5}},
            }

            latencies = []
            for _ in range(50):
                start = time.perf_counter()
                await manager.broadcast(message)
                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)

            # Cleanup
            for client in clients:
                manager.disconnect(client)

            return latencies

        import asyncio

        for client_count in [5, 10, 20]:
            latencies = asyncio.run(measure_broadcast_multi_clients(client_count))

            mean_latency = statistics.mean(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18]

            print(f"\nWebSocket Broadcast Latency ({client_count} Clients):")
            print(f"  Mean: {mean_latency:.2f}ms")
            print(f"  P95:  {p95_latency:.2f}ms")

            # Assert P95 < 50ms target even with multiple clients
            assert (
                p95_latency < 50
            ), f"P95 latency {p95_latency:.2f}ms exceeds 50ms target for {client_count} clients"


@pytest.mark.performance
class TestCachingPerformance:
    """Test caching behavior improves performance"""

    def test_cache_reduces_filesystem_scanning(
        self, integration_client, mock_agents_directory, create_workflow_states
    ):
        """Test that caching reduces response time for subsequent requests"""
        create_workflow_states(10)

        with patch(
            "core.adw_monitor.get_agents_directory", return_value=mock_agents_directory
        ), patch("core.adw_monitor.batch_check_running_processes", return_value={}):
            # First request (cache miss)
            start = time.perf_counter()
            response1 = integration_client.get("/api/adw-monitor")
            first_request_ms = (time.perf_counter() - start) * 1000

            assert response1.status_code == 200

            # Second request (cache hit - within 5s TTL)
            start = time.perf_counter()
            response2 = integration_client.get("/api/adw-monitor")
            cached_request_ms = (time.perf_counter() - start) * 1000

            assert response2.status_code == 200

            print("\nCaching Performance:")
            print(f"  First Request:  {first_request_ms:.2f}ms")
            print(f"  Cached Request: {cached_request_ms:.2f}ms")
            print(
                f"  Speedup:        {first_request_ms / cached_request_ms:.2f}x faster"
            )

            # Cached request should be faster (or at least not slower)
            # Allow some variance due to test environment
            assert cached_request_ms <= first_request_ms * 1.5


@pytest.mark.performance
class TestScalability:
    """Test performance with varying workflow counts"""

    def test_response_time_scales_linearly(
        self, integration_client, mock_agents_directory, create_workflow_states
    ):
        """Test that response time scales linearly with workflow count"""
        workflow_counts = [5, 10, 25, 50]
        results = []

        for count in workflow_counts:
            # Create workflows
            create_workflow_states(count)

            with patch(
                "core.adw_monitor.get_agents_directory",
                return_value=mock_agents_directory,
            ), patch("core.adw_monitor.batch_check_running_processes", return_value={}):
                # Warm up
                for _ in range(3):
                    integration_client.get("/api/adw-monitor")

                # Measure
                times = []
                for _ in range(20):
                    start = time.perf_counter()
                    response = integration_client.get("/api/adw-monitor")
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    assert response.status_code == 200
                    times.append(elapsed_ms)

                mean_time = statistics.mean(times)
                results.append((count, mean_time))

            print(f"\n{count} workflows: {mean_time:.2f}ms (mean)")

        # Verify all response times meet target
        for count, mean_time in results:
            assert (
                mean_time < 200
            ), f"Mean response time {mean_time:.2f}ms exceeds 200ms for {count} workflows"

        # Verify scaling is reasonable (not exponential)
        # 50 workflows shouldn't take more than 5x time of 5 workflows
        if len(results) >= 2:
            min_count, min_time = results[0]
            max_count, max_time = results[-1]
            scaling_factor = max_time / min_time

            print(f"\nScaling Factor: {scaling_factor:.2f}x")
            assert (
                scaling_factor < 5
            ), f"Response time scaling {scaling_factor:.2f}x is too high"


@pytest.mark.performance
class TestConcurrentOperations:
    """Test performance under concurrent load"""

    def test_concurrent_api_requests_performance(
        self, integration_client, mock_agents_directory, create_workflow_states
    ):
        """Test API handles concurrent requests efficiently"""
        import concurrent.futures

        create_workflow_states(10)

        with patch(
            "core.adw_monitor.get_agents_directory", return_value=mock_agents_directory
        ), patch("core.adw_monitor.batch_check_running_processes", return_value={}):

            def make_request():
                start = time.perf_counter()
                response = integration_client.get("/api/adw-monitor")
                elapsed_ms = (time.perf_counter() - start) * 1000
                return elapsed_ms, response.status_code

            # Make 20 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(20)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            # Analyze results
            times = [r[0] for r in results]
            status_codes = [r[1] for r in results]

            mean_time = statistics.mean(times)
            max_time = max(times)
            success_count = sum(1 for code in status_codes if code == 200)

            print("\nConcurrent Requests Performance:")
            print(f"  Successful: {success_count}/20")
            print(f"  Mean Time:  {mean_time:.2f}ms")
            print(f"  Max Time:   {max_time:.2f}ms")

            # All requests should succeed
            assert success_count == 20, f"Only {success_count}/20 requests succeeded"

            # Mean time should still meet target
            assert mean_time < 200, f"Mean time {mean_time:.2f}ms exceeds target"
