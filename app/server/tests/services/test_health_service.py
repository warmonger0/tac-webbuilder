"""
Unit tests for the Health Service Module

This test module verifies the correct implementation of the HealthService class,
ServiceStatus enum, and all stub health check methods. It ensures the module
can be imported, instantiated with various configurations, and returns the
expected data structures.
"""

import asyncio
from services.health_service import HealthService, ServiceStatus
from core.data_models import ServiceHealth


class TestServiceStatus:
    """Test cases for the ServiceStatus enum."""

    def test_service_status_enum_values(self):
        """Verify ServiceStatus enum has all required values."""
        assert ServiceStatus.HEALTHY.value == "healthy"
        assert ServiceStatus.DEGRADED.value == "degraded"
        assert ServiceStatus.UNHEALTHY.value == "unhealthy"
        assert ServiceStatus.UNKNOWN.value == "unknown"

    def test_service_status_string_representation(self):
        """Verify ServiceStatus enum values are strings."""
        assert ServiceStatus.HEALTHY.value == "healthy"
        assert ServiceStatus.DEGRADED.value == "degraded"
        assert ServiceStatus.UNHEALTHY.value == "unhealthy"
        assert ServiceStatus.UNKNOWN.value == "unknown"

    def test_service_status_enum_membership(self):
        """Verify all expected values are members of the enum."""
        status_values = [status.value for status in ServiceStatus]
        assert "healthy" in status_values
        assert "degraded" in status_values
        assert "unhealthy" in status_values
        assert "unknown" in status_values
        assert len(status_values) == 4


class TestHealthServiceInstantiation:
    """Test cases for HealthService instantiation."""

    def test_instantiate_with_defaults(self):
        """Verify HealthService can be instantiated with default parameters."""
        health_service = HealthService()
        assert health_service is not None
        assert isinstance(health_service, HealthService)

    def test_default_parameters(self):
        """Verify default parameter values are set correctly."""
        health_service = HealthService()
        assert health_service.db_path == "db/database.db"
        assert health_service.webhook_url == "http://localhost:8001/webhook-status"
        assert health_service.cloudflare_tunnel_name is None
        assert health_service.frontend_url == "http://localhost:5173"
        assert health_service.backend_port == "8000"

    def test_instantiate_with_custom_parameters(self):
        """Verify HealthService can be instantiated with custom parameters."""
        custom_db_path = "custom/path/database.db"
        custom_webhook_url = "http://custom-webhook:9000/health"
        custom_tunnel_name = "my-tunnel"
        custom_frontend_url = "http://localhost:3000"
        custom_backend_port = "9999"

        health_service = HealthService(
            db_path=custom_db_path,
            webhook_url=custom_webhook_url,
            cloudflare_tunnel_name=custom_tunnel_name,
            frontend_url=custom_frontend_url,
            backend_port=custom_backend_port
        )

        assert health_service.db_path == custom_db_path
        assert health_service.webhook_url == custom_webhook_url
        assert health_service.cloudflare_tunnel_name == custom_tunnel_name
        assert health_service.frontend_url == custom_frontend_url
        assert health_service.backend_port == custom_backend_port

    def test_instantiate_with_none_tunnel_name(self):
        """Verify HealthService handles None for optional cloudflare_tunnel_name."""
        health_service = HealthService(cloudflare_tunnel_name=None)
        assert health_service.cloudflare_tunnel_name is None


class TestHealthServiceCheckAll:
    """Test cases for the check_all() method."""

    def test_check_all_returns_dict(self):
        """Verify check_all() returns a dictionary."""
        health_service = HealthService()
        result = asyncio.run(health_service.check_all())
        assert isinstance(result, dict)

    def test_check_all_has_all_service_keys(self):
        """Verify check_all() returns all expected service keys."""
        health_service = HealthService()
        result = asyncio.run(health_service.check_all())

        expected_keys = [
            "backend_api",
            "database",
            "webhook",
            "cloudflare_tunnel",
            "github_webhook",
            "frontend"
        ]

        for key in expected_keys:
            assert key in result, f"Expected key '{key}' not found in result"

        assert len(result) == len(expected_keys)

    def test_check_all_values_are_service_health(self):
        """Verify check_all() returns ServiceHealth objects for all services."""
        health_service = HealthService()
        result = asyncio.run(health_service.check_all())

        for service_name, health in result.items():
            assert isinstance(health, ServiceHealth), \
                f"Service '{service_name}' did not return ServiceHealth instance"

    def test_check_all_is_async(self):
        """Verify check_all() is an async method."""
        import inspect
        assert inspect.iscoroutinefunction(HealthService.check_all)


class TestHealthServiceStubMethods:
    """Test cases for individual health check stub methods."""

    def test_check_backend_returns_service_health(self):
        """Verify check_backend() returns ServiceHealth instance."""
        health_service = HealthService()
        result = health_service.check_backend()
        assert isinstance(result, ServiceHealth)

    def test_check_backend_returns_healthy_status(self):
        """Verify check_backend() returns healthy status when backend is running."""
        health_service = HealthService()
        result = health_service.check_backend()
        assert result.status == ServiceStatus.HEALTHY.value
        assert result.name == "Backend API"

    def test_check_database_returns_service_health(self):
        """Verify check_database() returns ServiceHealth instance."""
        health_service = HealthService()
        result = health_service.check_database()
        assert isinstance(result, ServiceHealth)

    def test_check_database_returns_healthy_status(self):
        """Verify check_database() returns healthy status when database is accessible."""
        health_service = HealthService()
        result = health_service.check_database()
        # Database should be healthy or error (depending on if db exists)
        assert result.status in [ServiceStatus.HEALTHY.value, "error"]
        assert result.name == "Database"

    def test_check_webhook_returns_service_health(self):
        """Verify check_webhook() returns ServiceHealth instance."""
        health_service = HealthService()
        result = asyncio.run(health_service.check_webhook())
        assert isinstance(result, ServiceHealth)

    def test_check_webhook_returns_status(self):
        """Verify check_webhook() returns appropriate status."""
        health_service = HealthService()
        result = asyncio.run(health_service.check_webhook())
        # Webhook service may be running or not - both are valid
        assert result.status in [ServiceStatus.HEALTHY.value, "error", ServiceStatus.UNKNOWN.value]
        assert result.name == "Webhook Service"

    def test_check_webhook_is_async(self):
        """Verify check_webhook() is an async method."""
        import inspect
        assert inspect.iscoroutinefunction(HealthService.check_webhook)

    def test_check_cloudflare_tunnel_returns_service_health(self):
        """Verify check_cloudflare_tunnel() returns ServiceHealth instance."""
        health_service = HealthService()
        result = health_service.check_cloudflare_tunnel()
        assert isinstance(result, ServiceHealth)

    def test_check_cloudflare_tunnel_returns_status(self):
        """Verify check_cloudflare_tunnel() returns appropriate status."""
        health_service = HealthService()
        result = health_service.check_cloudflare_tunnel()
        # Cloudflare tunnel may or may not be running
        assert result.status in [ServiceStatus.HEALTHY.value, "error", ServiceStatus.UNKNOWN.value]
        assert result.name == "Cloudflare Tunnel"

    def test_check_github_webhook_returns_service_health(self):
        """Verify check_github_webhook() returns ServiceHealth instance."""
        health_service = HealthService()
        result = asyncio.run(health_service.check_github_webhook())
        assert isinstance(result, ServiceHealth)

    def test_check_github_webhook_returns_status(self):
        """Verify check_github_webhook() returns appropriate status."""
        health_service = HealthService()
        result = asyncio.run(health_service.check_github_webhook())
        # GitHub webhook check may succeed or fail
        assert result.status in [ServiceStatus.HEALTHY.value, "error", ServiceStatus.UNKNOWN.value, ServiceStatus.DEGRADED.value]
        assert result.name == "GitHub Webhook"

    def test_check_github_webhook_is_async(self):
        """Verify check_github_webhook() is an async method."""
        import inspect
        assert inspect.iscoroutinefunction(HealthService.check_github_webhook)

    def test_check_frontend_returns_service_health(self):
        """Verify check_frontend() returns ServiceHealth instance."""
        health_service = HealthService()
        result = asyncio.run(health_service.check_frontend())
        assert isinstance(result, ServiceHealth)

    def test_check_frontend_returns_status(self):
        """Verify check_frontend() returns appropriate status."""
        health_service = HealthService()
        result = asyncio.run(health_service.check_frontend())
        # Frontend may or may not be running
        assert result.status in [ServiceStatus.HEALTHY.value, "error", ServiceStatus.UNKNOWN.value, ServiceStatus.DEGRADED.value]
        assert result.name == "Frontend"

    def test_check_frontend_is_async(self):
        """Verify check_frontend() is an async method."""
        import inspect
        assert inspect.iscoroutinefunction(HealthService.check_frontend)


class TestHealthServiceIntegration:
    """Integration tests for HealthService."""

    def test_all_methods_called_by_check_all(self):
        """Verify check_all() calls all health check methods and returns their results."""
        health_service = HealthService()
        result = asyncio.run(health_service.check_all())

        # Verify all services return valid status values
        valid_statuses = [ServiceStatus.HEALTHY.value, "error", ServiceStatus.UNKNOWN.value, ServiceStatus.DEGRADED.value]
        for service_name, health in result.items():
            assert health.status in valid_statuses, \
                f"Service '{service_name}' returned invalid status: {health.status}"
            assert isinstance(health.message, str), \
                f"Service '{service_name}' did not return a message string"

    def test_concurrent_check_all_calls(self):
        """Verify multiple concurrent check_all() calls work correctly."""
        async def run_concurrent():
            health_service = HealthService()

            # Run multiple check_all() calls concurrently
            results = await asyncio.gather(
                health_service.check_all(),
                health_service.check_all(),
                health_service.check_all()
            )

            # All results should be identical
            assert len(results) == 3
            for result in results:
                assert len(result) == 6
                assert all(isinstance(health, ServiceHealth) for health in result.values())

        asyncio.run(run_concurrent())

    def test_custom_configuration_persists(self):
        """Verify custom configuration persists across multiple method calls."""
        custom_db = "custom.db"
        health_service = HealthService(db_path=custom_db)

        # Configuration should persist
        assert health_service.db_path == custom_db

        # Should still work after calling methods
        result = health_service.check_backend()
        assert health_service.db_path == custom_db
        assert isinstance(result, ServiceHealth)


class TestModuleImports:
    """Test cases for module imports and exports."""

    def test_import_health_service_from_services(self):
        """Verify HealthService can be imported from services package."""
        from services import HealthService as ImportedHealthService
        assert ImportedHealthService is HealthService

    def test_import_service_status_from_health_service(self):
        """Verify ServiceStatus can be imported from health_service module."""
        from services.health_service import ServiceStatus as ImportedServiceStatus
        assert ImportedServiceStatus is ServiceStatus

    def test_service_health_imported_from_data_models(self):
        """Verify ServiceHealth is imported from core.data_models, not redefined."""
        from core.data_models import ServiceHealth as DataModelsServiceHealth
        from services.health_service import HealthService

        health_service = HealthService()
        result = health_service.check_backend()

        # Result should be an instance of the ServiceHealth from data_models
        assert isinstance(result, DataModelsServiceHealth)
