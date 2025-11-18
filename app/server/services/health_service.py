"""
Health Service Module

This module provides centralized health checking for all critical system services.
It monitors Backend API, Database, Webhook Service, Cloudflare Tunnel, GitHub Webhook,
and Frontend to provide real-time system status information.

The HealthService class encapsulates all health check logic that was previously
embedded in server.py, making it reusable, testable, and maintainable. It uses
async methods for non-blocking health checks and returns standardized ServiceHealth
objects for consistent status reporting.

Usage:
    from services.health_service import HealthService, ServiceStatus

    # Initialize with default configuration
    health_service = HealthService()

    # Initialize with custom configuration
    health_service = HealthService(
        db_path="custom/path/database.db",
        webhook_url="http://localhost:9000/webhook-status",
        frontend_url="http://localhost:3000"
    )

    # Check all services
    health_status = await health_service.check_all()
    for service_name, health in health_status.items():
        print(f"{service_name}: {health.status}")
"""

import logging
from enum import Enum

from core.data_models import ServiceHealth

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """
    Standard status values for service health checks.

    This enum provides consistent status values across all health checks,
    making it easier to aggregate and compare service health states.

    Values:
        HEALTHY: Service is operating normally with no issues
        DEGRADED: Service is operational but experiencing issues or reduced performance
        UNHEALTHY: Service is not operational or experiencing critical failures
        UNKNOWN: Service status cannot be determined (e.g., timeout, unreachable)

    Example:
        >>> status = ServiceStatus.HEALTHY
        >>> print(status)
        healthy
        >>> print(status.value)
        healthy
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthService:
    """
    Centralized health checking service for all system components.

    This service provides methods to check the health of all critical system
    services including backend API, database, webhook service, Cloudflare tunnel,
    GitHub webhook endpoint, and frontend. Each check returns a ServiceHealth
    object with status, message, and optional details.

    The service is designed to be used by the /api/system-status endpoint but
    can also be used by CLI tools, monitoring scripts, or other parts of the
    system that need health information.

    Attributes:
        db_path: Path to the SQLite database file
        webhook_url: URL of the webhook service to check
        cloudflare_tunnel_name: Name of the Cloudflare tunnel (optional)
        frontend_url: URL of the frontend application
        backend_port: Port number for the backend API

    Example:
        >>> health_service = HealthService()
        >>> results = await health_service.check_all()
        >>> print(results["backend_api"].status)
        healthy

        >>> # Custom configuration
        >>> health_service = HealthService(
        ...     db_path="/custom/db.db",
        ...     webhook_url="http://webhook:8001/health"
        ... )
    """

    def __init__(
        self,
        db_path: str = "db/database.db",
        webhook_url: str = "http://localhost:8001/webhook-status",
        cloudflare_tunnel_name: str | None = None,
        frontend_url: str = "http://localhost:5173",
        backend_port: str = "8000"
    ):
        """
        Initialize the HealthService with configuration for all health check targets.

        Args:
            db_path: Path to the SQLite database file (default: "db/database.db")
            webhook_url: URL of the webhook service health endpoint
                        (default: "http://localhost:8001/webhook-status")
            cloudflare_tunnel_name: Name of the Cloudflare tunnel to check, or None
                                   if no tunnel is configured (default: None)
            frontend_url: URL of the frontend application
                         (default: "http://localhost:5173")
            backend_port: Port number for the backend API (default: "8000")

        Example:
            >>> # Development environment
            >>> hs = HealthService()

            >>> # Production environment
            >>> hs = HealthService(
            ...     db_path="/var/lib/tac/database.db",
            ...     webhook_url="https://webhook.example.com/health",
            ...     cloudflare_tunnel_name="tac-production",
            ...     frontend_url="https://app.example.com",
            ...     backend_port="8000"
            ... )
        """
        self.db_path = db_path
        self.webhook_url = webhook_url
        self.cloudflare_tunnel_name = cloudflare_tunnel_name
        self.frontend_url = frontend_url
        self.backend_port = backend_port
        logger.info(
            f"HealthService initialized with db_path={db_path}, "
            f"webhook_url={webhook_url}, frontend_url={frontend_url}"
        )

    async def check_all(self) -> dict[str, ServiceHealth]:
        """
        Check the health of all system services.

        This method performs health checks on all configured services and returns
        a dictionary mapping service names to their health status. The checks are
        performed concurrently where possible to minimize total check time.

        Returns:
            Dictionary mapping service names to ServiceHealth objects. Keys include:
            - "backend_api": Backend FastAPI service
            - "database": SQLite database
            - "webhook": Webhook service
            - "cloudflare_tunnel": Cloudflare tunnel (if configured)
            - "github_webhook": GitHub webhook endpoint
            - "frontend": React frontend application

        Example:
            >>> health_service = HealthService()
            >>> results = await health_service.check_all()
            >>> for service_name, health in results.items():
            ...     print(f"{service_name}: {health.status} - {health.message}")
            backend_api: unknown - Health check not yet implemented
            database: unknown - Health check not yet implemented
            ...

        Note:
            In this initial implementation, all checks return "unknown" status.
            Actual health check logic will be implemented in subsequent workflows.
        """
        logger.debug("Running health checks for all services")

        return {
            "backend_api": self.check_backend(),
            "database": self.check_database(),
            "webhook": await self.check_webhook(),
            "cloudflare_tunnel": self.check_cloudflare_tunnel(),
            "github_webhook": await self.check_github_webhook(),
            "frontend": await self.check_frontend()
        }

    def check_backend(self) -> ServiceHealth:
        """
        Check the health of the Backend API service.

        This method will verify that the FastAPI backend is running and responsive
        by checking if it's listening on the configured port and responding to
        health check requests.

        Returns:
            ServiceHealth object with status "unknown" (stub implementation)

        Note:
            Actual implementation will be added in Workflow 4.2. This stub allows
            the service structure to be tested without the full health check logic.
        """
        logger.debug("Checking backend API health (stub)")
        return ServiceHealth(
            name="Backend API",
            status=ServiceStatus.UNKNOWN.value,
            message="Health check not yet implemented"
        )

    def check_database(self) -> ServiceHealth:
        """
        Check the health of the SQLite database.

        This method will verify that the database file exists, is accessible,
        and can be queried successfully. It may also check for database locks
        or corruption issues.

        Returns:
            ServiceHealth object with status "unknown" (stub implementation)

        Note:
            Actual implementation will be added in Workflow 4.2. This stub allows
            the service structure to be tested without the full health check logic.
        """
        logger.debug("Checking database health (stub)")
        return ServiceHealth(
            name="Database",
            status=ServiceStatus.UNKNOWN.value,
            message="Health check not yet implemented"
        )

    async def check_webhook(self) -> ServiceHealth:
        """
        Check the health of the Webhook Service.

        This async method will send an HTTP request to the webhook service's
        health endpoint to verify it is running and responsive. It will handle
        timeouts, connection errors, and invalid responses.

        Returns:
            ServiceHealth object with status "unknown" (stub implementation)

        Note:
            Actual implementation will be added in Workflow 4.2. This stub allows
            the service structure to be tested without the full health check logic.
            The method is async to support non-blocking HTTP requests.
        """
        logger.debug("Checking webhook service health (stub)")
        return ServiceHealth(
            name="Webhook Service",
            status=ServiceStatus.UNKNOWN.value,
            message="Health check not yet implemented"
        )

    def check_cloudflare_tunnel(self) -> ServiceHealth:
        """
        Check the health of the Cloudflare Tunnel.

        This method will verify that the Cloudflare tunnel (if configured) is
        running and properly connected. It checks the cloudflared process status
        and tunnel connectivity.

        Returns:
            ServiceHealth object with status "unknown" (stub implementation)

        Note:
            Actual implementation will be added in Workflow 4.2. This stub allows
            the service structure to be tested without the full health check logic.
            If no tunnel is configured (cloudflare_tunnel_name is None), this will
            return a "healthy" status indicating the tunnel is not required.
        """
        logger.debug("Checking Cloudflare tunnel health (stub)")
        return ServiceHealth(
            name="Cloudflare Tunnel",
            status=ServiceStatus.UNKNOWN.value,
            message="Health check not yet implemented"
        )

    async def check_github_webhook(self) -> ServiceHealth:
        """
        Check the health of the GitHub Webhook endpoint.

        This async method will verify that the GitHub webhook endpoint is accessible
        from the internet and properly configured. It may send a test request to
        verify the endpoint is reachable.

        Returns:
            ServiceHealth object with status "unknown" (stub implementation)

        Note:
            Actual implementation will be added in Workflow 4.2. This stub allows
            the service structure to be tested without the full health check logic.
            The method is async to support non-blocking HTTP requests.
        """
        logger.debug("Checking GitHub webhook health (stub)")
        return ServiceHealth(
            name="GitHub Webhook",
            status=ServiceStatus.UNKNOWN.value,
            message="Health check not yet implemented"
        )

    async def check_frontend(self) -> ServiceHealth:
        """
        Check the health of the Frontend application.

        This async method will verify that the React frontend is accessible and
        serving content correctly. It sends an HTTP request to the frontend URL
        and checks for a successful response.

        Returns:
            ServiceHealth object with status "unknown" (stub implementation)

        Note:
            Actual implementation will be added in Workflow 4.2. This stub allows
            the service structure to be tested without the full health check logic.
            The method is async to support non-blocking HTTP requests.
        """
        logger.debug("Checking frontend health (stub)")
        return ServiceHealth(
            name="Frontend",
            status=ServiceStatus.UNKNOWN.value,
            message="Health check not yet implemented"
        )
