"""
Service Controller for managing external services and subprocesses.

This module provides a centralized controller for managing external services like
webhook service, Cloudflare tunnel, and GitHub webhook operations.

Responsibilities:
- Start/stop/restart external service processes
- Check service health and status
- Provide diagnostic information
- Handle subprocess lifecycle management
"""

import json
import logging
import os
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any

from utils.process_runner import ProcessRunner

logger = logging.getLogger(__name__)


class ServiceController:
    """
    Manages external service processes and health checks.

    This controller provides methods to:
    - Start and manage the webhook service
    - Restart the Cloudflare tunnel
    - Check GitHub webhook health
    - Redeliver failed GitHub webhooks

    All methods return dictionaries with status information suitable for API responses.
    """

    def __init__(
        self,
        webhook_port: int = 8001,
        webhook_script_path: str | None = None,
        cloudflare_tunnel_token: str | None = None,
        github_pat: str | None = None,
        github_repo: str = "warmonger0/tac-webbuilder",
        github_webhook_id: str | None = None
    ):
        """
        Initialize the ServiceController.

        Args:
            webhook_port: Port for the webhook service (default: 8001)
            webhook_script_path: Path to webhook script relative to adws directory
            cloudflare_tunnel_token: Cloudflare tunnel token (or None to use env var)
            github_pat: GitHub Personal Access Token (or None to use env var)
            github_repo: GitHub repository in format "owner/repo"
            github_webhook_id: GitHub webhook ID (or None to use env var/default)
        """
        self.webhook_port = webhook_port
        self.webhook_script_path = webhook_script_path or "adw_triggers/trigger_webhook.py"
        self.cloudflare_tunnel_token = cloudflare_tunnel_token or os.environ.get("CLOUDFLARED_TUNNEL_TOKEN")
        self.github_pat = github_pat or os.environ.get("GITHUB_PAT")
        self.github_repo = github_repo
        self.github_webhook_id = github_webhook_id or os.environ.get("GITHUB_WEBHOOK_ID", "580534779")

    def start_webhook_service(self) -> dict[str, Any]:
        """
        Start the webhook service on the configured port.

        Checks if the service is already running before attempting to start it.
        Verifies that the service started successfully by checking its health endpoint.

        Returns:
            dict: Status information with keys:
                - status: "already_running", "started", or "error"
                - message: Human-readable status message
        """
        try:
            # Check if already running
            if self._is_process_running(self.webhook_port):
                return {
                    "status": "already_running",
                    "message": f"Webhook service is already running on port {self.webhook_port}"
                }

            # Get the adws directory path
            server_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(server_dir))
            adws_dir = os.path.join(project_root, "adws")

            # Start the webhook service in background
            subprocess.Popen(
                ["uv", "run", self.webhook_script_path],
                cwd=adws_dir,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Wait a moment for service to start
            time.sleep(2)

            # Verify it started
            try:
                with urllib.request.urlopen(f"http://localhost:{self.webhook_port}/health", timeout=3) as response:
                    if response.status == 200:
                        return {
                            "status": "started",
                            "message": f"Webhook service started successfully on port {self.webhook_port}"
                        }
            except Exception:
                pass

            return {
                "status": "started",
                "message": f"Webhook service start command issued (port {self.webhook_port})"
            }
        except Exception as e:
            logger.error(f"Failed to start webhook service: {e}")
            return {
                "status": "error",
                "message": f"Failed to start webhook service: {str(e)}"
            }

    def restart_cloudflare_tunnel(self) -> dict[str, Any]:
        """
        Restart the Cloudflare tunnel.

        Kills any existing cloudflared processes and starts a new tunnel with
        the configured token. Verifies that the tunnel is running after restart.

        Returns:
            dict: Status information with keys:
                - status: "restarted", "started", or "error"
                - message: Human-readable status message
        """
        try:
            # Check if CLOUDFLARED_TUNNEL_TOKEN is set
            if not self.cloudflare_tunnel_token:
                return {
                    "status": "error",
                    "message": "CLOUDFLARED_TUNNEL_TOKEN environment variable not set"
                }

            # Kill existing cloudflared process
            ProcessRunner.run(
                ["pkill", "-f", "cloudflared tunnel run"]
            )

            # Wait a moment
            time.sleep(1)

            # Start new tunnel in background
            subprocess.Popen(
                ["cloudflared", "tunnel", "run", "--token", self.cloudflare_tunnel_token],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            time.sleep(2)

            # Verify it's running
            result = ProcessRunner.run(["ps", "aux"])
            if "cloudflared tunnel run" in result.stdout:
                return {
                    "status": "restarted",
                    "message": "Cloudflare tunnel restarted successfully"
                }

            return {
                "status": "started",
                "message": "Cloudflare tunnel restart command issued"
            }
        except Exception as e:
            logger.error(f"Failed to restart Cloudflare tunnel: {e}")
            return {
                "status": "error",
                "message": f"Failed to restart Cloudflare tunnel: {str(e)}"
            }

    def get_github_webhook_health(self) -> dict[str, Any]:
        """
        Check GitHub webhook health by examining recent deliveries.

        Uses the GitHub API to check the status of recent webhook deliveries.
        Falls back to pinging the webhook endpoint directly if API access fails.

        Returns:
            dict: Health information with keys:
                - status: "healthy", "degraded", "error", or "unknown"
                - message: Human-readable health message
                - webhook_url: The webhook endpoint URL (if available)
                - recent_deliveries: List of recent delivery information (if available)
                - webhook_id: The webhook ID being monitored (if available)
        """
        try:
            # Get GitHub PAT
            if not self.github_pat:
                return {
                    "status": "error",
                    "message": "GITHUB_PAT not configured"
                }

            # Check recent webhook deliveries using gh CLI
            result = ProcessRunner.run_gh_command(
                ["api", f"repos/{self.github_repo}/hooks/{self.github_webhook_id}/deliveries",
                 "--jq", ".[0:5] | .[] | {id: .id, status: .status_code, delivered_at: .delivered_at}"],
                timeout=5
            )

            if result.success:
                deliveries_output = result.stdout.strip()
                if deliveries_output:
                    # Parse the deliveries
                    deliveries = []
                    for line in deliveries_output.split('\n'):
                        if line.strip():
                            try:
                                delivery = json.loads(line)
                                deliveries.append(delivery)
                            except json.JSONDecodeError:
                                pass

                    # Check if most recent delivery was successful
                    if deliveries:
                        latest = deliveries[0]
                        status_code = latest.get('status', 0)

                        if status_code == 200:
                            status = "healthy"
                            message = f"Latest delivery successful (HTTP {status_code})"
                        elif status_code >= 500:
                            status = "error"
                            message = f"Latest delivery failed with HTTP {status_code} (Server Error)"
                        elif status_code >= 400:
                            status = "degraded"
                            message = f"Latest delivery failed with HTTP {status_code} (Client Error)"
                        else:
                            status = "unknown"
                            message = f"Latest delivery status: HTTP {status_code}"

                        return {
                            "status": status,
                            "message": message,
                            "webhook_url": "https://webhook.directmyagent.com",
                            "recent_deliveries": deliveries[:3],
                            "webhook_id": self.github_webhook_id
                        }

            # Fallback: try to ping the webhook endpoint directly
            try:
                with urllib.request.urlopen("https://webhook.directmyagent.com/health", timeout=3) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "message": "Webhook endpoint is accessible",
                            "webhook_url": "https://webhook.directmyagent.com"
                        }
            except Exception:
                pass

            return {
                "status": "unknown",
                "message": "Unable to verify webhook health"
            }
        except Exception as e:
            logger.error(f"Failed to check GitHub webhook health: {e}")
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}"
            }

    def redeliver_github_webhook(self) -> dict[str, Any]:
        """
        Redeliver the most recent failed GitHub webhook with intelligent diagnostics.

        This method:
        1. Checks if webhook and tunnel services are healthy
        2. Automatically restarts services if they're down (best effort)
        3. Redelivers the most recent failed webhook delivery
        4. Provides detailed diagnostics about any issues

        Returns:
            dict: Redelivery information with keys:
                - status: "success", "warning", "error", or "info"
                - message: Human-readable status message
                - diagnostics: List of diagnostic messages
                - delivery_id: The webhook delivery ID that was redelivered (if applicable)
                - recommendations: List of recommended actions (if applicable)
        """
        try:
            diagnostics = []
            auto_fix_attempted = False

            # Step 1: Check webhook service health
            webhook_healthy = False
            try:
                with urllib.request.urlopen(f"http://localhost:{self.webhook_port}/webhook-status", timeout=2) as response:
                    webhook_healthy = response.status == 200
                    diagnostics.append(f"✓ Webhook service is running (port {self.webhook_port})")
            except urllib.error.URLError:
                diagnostics.append(f"✗ Webhook service is DOWN (port {self.webhook_port})")
                auto_fix_attempted = True
                # Attempt to restart webhook service
                try:
                    server_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root = os.path.dirname(os.path.dirname(server_dir))
                    adws_dir = os.path.join(project_root, "adws")
                    restart_result = ProcessRunner.run_shell(
                        f"cd {adws_dir} && uv run {self.webhook_script_path} &",
                        timeout=3
                    )
                    diagnostics.append("⚙ Attempted to restart webhook service")
                except Exception:
                    diagnostics.append("✗ Failed to restart webhook service automatically")

            # Step 2: Check Cloudflare tunnel health
            tunnel_healthy = False
            try:
                result = ProcessRunner.run(["ps", "aux"], timeout=2)
                tunnel_healthy = "cloudflared tunnel run" in result.stdout
                if tunnel_healthy:
                    diagnostics.append("✓ Cloudflare tunnel is running")
                else:
                    diagnostics.append("✗ Cloudflare tunnel is DOWN")
            except Exception:
                diagnostics.append("? Unable to check Cloudflare tunnel status")

            # Step 3: Check public webhook endpoint
            public_endpoint_healthy = False
            try:
                with urllib.request.urlopen("https://webhook.directmyagent.com/webhook-status", timeout=3) as response:
                    public_endpoint_healthy = response.status == 200
                    diagnostics.append("✓ Public webhook endpoint is accessible")
            except Exception as e:
                diagnostics.append(f"✗ Public webhook endpoint failed: {str(e)[:50]}")

            # Step 4: Get webhook info and attempt redelivery
            # Get most recent failed delivery
            result = ProcessRunner.run_gh_command(
                ["api", f"repos/{self.github_repo}/hooks/{self.github_webhook_id}/deliveries",
                 "--jq", '.[] | select(.status_code != 200) | .id'],
                timeout=5
            )

            if result.success and result.stdout.strip():
                delivery_id = result.stdout.strip().split('\n')[0]
                diagnostics.append(f"Found failed delivery: {delivery_id}")

                # Only attempt redelivery if services are healthy
                if not webhook_healthy or not tunnel_healthy:
                    return {
                        "status": "warning",
                        "message": "Services need attention before redelivery",
                        "diagnostics": diagnostics,
                        "recommendations": [
                            "Webhook service is down - restart it" if not webhook_healthy else None,
                            "Cloudflare tunnel is down - restart it" if not tunnel_healthy else None,
                        ]
                    }

                # Redeliver
                redeliver_result = ProcessRunner.run_gh_command(
                    ["api", "-X", "POST",
                     f"repos/{self.github_repo}/hooks/{self.github_webhook_id}/deliveries/{delivery_id}/attempts"],
                    timeout=5
                )

                if redeliver_result.success:
                    return {
                        "status": "success",
                        "message": "Webhook redelivered successfully",
                        "diagnostics": diagnostics,
                        "delivery_id": delivery_id
                    }
                else:
                    diagnostics.append(f"✗ Redelivery failed: {redeliver_result.stderr}")
                    return {
                        "status": "error",
                        "message": "Failed to redeliver webhook",
                        "diagnostics": diagnostics
                    }

            diagnostics.append("No failed deliveries found to redeliver")
            return {
                "status": "info",
                "message": "No failed deliveries to redeliver (all recent deliveries succeeded)",
                "diagnostics": diagnostics
            }
        except Exception as e:
            logger.error(f"Failed to redeliver webhook: {e}")
            return {
                "status": "error",
                "message": f"Redelivery failed: {str(e)}",
                "diagnostics": diagnostics if 'diagnostics' in locals() else []
            }

    # Private helper methods

    def _is_process_running(self, port: int) -> bool:
        """
        Check if a process is running on the given port.

        Args:
            port: Port number to check

        Returns:
            bool: True if a process is listening on the port, False otherwise
        """
        try:
            result = ProcessRunner.run(["lsof", "-i", f":{port}"])
            return result.success
        except Exception as e:
            logger.warning(f"Failed to check if port {port} is in use: {e}")
            return False

    def _kill_process_on_port(self, port: int) -> None:
        """
        Kill the process running on the given port.

        Args:
            port: Port number of the process to kill
        """
        try:
            # Get PID of process on port
            result = ProcessRunner.run(["lsof", "-ti", f":{port}"])
            if result.success and result.stdout.strip():
                pid = result.stdout.strip()
                ProcessRunner.run(["kill", "-9", pid])
                logger.info(f"Killed process {pid} on port {port}")
        except Exception as e:
            logger.warning(f"Failed to kill process on port {port}: {e}")
