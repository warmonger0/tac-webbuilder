#!/usr/bin/env python3
"""
GitHub API Call Monitor

Tracks and logs all GitHub API calls to help identify rate limit exhaustion causes.
Provides visibility into which operations are consuming quota.

Usage:
    from adw_modules.gh_api_monitor import GHMonitor

    monitor = GHMonitor()
    monitor.run_gh_command(["gh", "issue", "list"])

    # View summary
    monitor.print_summary()
"""

import subprocess
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class GHAPICall:
    """Record of a single GitHub API call."""
    timestamp: str
    command: List[str]
    api_type: str  # "REST" or "GraphQL"
    success: bool
    duration_ms: int
    rate_limit_before: Optional[Dict[str, Any]] = None
    rate_limit_after: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class GHMonitor:
    """
    Monitor and track GitHub API calls to diagnose rate limit issues.

    Features:
    - Logs every gh CLI call with timing
    - Checks rate limits before/after calls
    - Tracks quota consumption per call
    - Generates usage reports
    - Warns when approaching limits
    """

    def __init__(self, log_file: Optional[Path] = None):
        """
        Initialize GitHub API monitor.

        Args:
            log_file: Optional path to log file for persistent tracking
        """
        self.calls: List[GHAPICall] = []
        self.log_file = log_file or Path("/tmp/gh_api_calls.jsonl")

    def check_rate_limit(self, api_type: str = "graphql") -> Optional[Dict[str, Any]]:
        """
        Check current rate limit status.

        Args:
            api_type: "rest" or "graphql"

        Returns:
            Dict with limit info or None if check failed
        """
        try:
            if api_type.lower() == "rest":
                result = subprocess.run(
                    ["gh", "api", "rate_limit"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode != 0:
                    return None

                data = json.loads(result.stdout)
                core = data['resources']['core']

                return {
                    "api_type": "REST",
                    "limit": core['limit'],
                    "remaining": core['remaining'],
                    "reset": core['reset'],
                }

            else:  # GraphQL
                result = subprocess.run(
                    ["gh", "api", "graphql", "-f", "query=query { rateLimit { limit remaining resetAt } }"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode != 0:
                    return None

                data = json.loads(result.stdout)
                rate_limit = data['data']['rateLimit']

                return {
                    "api_type": "GraphQL",
                    "limit": rate_limit['limit'],
                    "remaining": rate_limit['remaining'],
                    "reset_at": rate_limit['resetAt'],
                }

        except Exception as e:
            logger.warning(f"Failed to check rate limit: {e}")
            return None

    def detect_api_type(self, command: List[str]) -> str:
        """
        Detect whether command uses REST or GraphQL API.

        Args:
            command: gh CLI command

        Returns:
            "REST", "GraphQL", or "Unknown"
        """
        cmd_str = " ".join(command)

        # GraphQL indicators
        if "graphql" in cmd_str or "-f query=" in cmd_str:
            return "GraphQL"

        # REST API indicators
        if "gh api" in cmd_str and "graphql" not in cmd_str:
            return "REST"

        # High-level commands that use GraphQL by default
        graphql_commands = ["gh issue list", "gh pr list", "gh repo view"]
        if any(cmd in cmd_str for cmd in graphql_commands):
            return "GraphQL"

        # REST API commands
        rest_commands = ["gh api repos/", "gh api rate_limit"]
        if any(cmd in cmd_str for cmd in rest_commands):
            return "REST"

        return "Unknown"

    def run_gh_command(
        self,
        command: List[str],
        check_limits: bool = True,
        warn_threshold: int = 100
    ) -> subprocess.CompletedProcess:
        """
        Run gh CLI command with monitoring.

        Args:
            command: gh CLI command to run
            check_limits: Whether to check rate limits before/after
            warn_threshold: Warn if remaining quota below this

        Returns:
            subprocess.CompletedProcess result
        """
        start_time = datetime.now(timezone.utc)
        api_type = self.detect_api_type(command)

        # Check rate limit before call
        rate_limit_before = None
        if check_limits:
            rate_limit_before = self.check_rate_limit(api_type.lower())

            if rate_limit_before and rate_limit_before["remaining"] < warn_threshold:
                logger.warning(
                    f"⚠️  {api_type} API quota LOW: {rate_limit_before['remaining']}/{rate_limit_before['limit']} remaining"
                )

        # Execute command
        success = True
        error_message = None

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                success = False
                error_message = result.stderr[:500] if result.stderr else "Command failed"

        except subprocess.TimeoutExpired:
            success = False
            error_message = "Command timeout (30s)"
            result = subprocess.CompletedProcess(command, 1, "", "Timeout")

        except Exception as e:
            success = False
            error_message = str(e)[:500]
            result = subprocess.CompletedProcess(command, 1, "", str(e))

        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Check rate limit after call
        rate_limit_after = None
        if check_limits:
            rate_limit_after = self.check_rate_limit(api_type.lower())

        # Record the call
        call_record = GHAPICall(
            timestamp=start_time.isoformat(),
            command=command,
            api_type=api_type,
            success=success,
            duration_ms=duration_ms,
            rate_limit_before=rate_limit_before,
            rate_limit_after=rate_limit_after,
            error_message=error_message
        )

        self.calls.append(call_record)

        # Log to file
        self._log_to_file(call_record)

        # Calculate quota consumed
        if rate_limit_before and rate_limit_after:
            consumed = rate_limit_before["remaining"] - rate_limit_after["remaining"]
            if consumed > 0:
                logger.info(
                    f"📊 {api_type} API call consumed {consumed} quota: {' '.join(command[:3])}..."
                )

        return result

    def _log_to_file(self, call: GHAPICall):
        """Append call record to log file."""
        try:
            with open(self.log_file, "a") as f:
                record = {
                    "timestamp": call.timestamp,
                    "command": call.command,
                    "api_type": call.api_type,
                    "success": call.success,
                    "duration_ms": call.duration_ms,
                    "rate_limit_before": call.rate_limit_before,
                    "rate_limit_after": call.rate_limit_after,
                    "error_message": call.error_message,
                }
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning(f"Failed to log gh API call to file: {e}")

    def print_summary(self):
        """Print summary of all tracked calls."""
        if not self.calls:
            print("No GitHub API calls tracked yet.")
            return

        print("\n" + "=" * 60)
        print("GitHub API Call Summary")
        print("=" * 60)

        total_calls = len(self.calls)
        successful_calls = sum(1 for c in self.calls if c.success)
        failed_calls = total_calls - successful_calls

        print(f"Total calls: {total_calls}")
        print(f"Successful: {successful_calls}")
        print(f"Failed: {failed_calls}")

        # Breakdown by API type
        rest_calls = sum(1 for c in self.calls if c.api_type == "REST")
        graphql_calls = sum(1 for c in self.calls if c.api_type == "GraphQL")
        unknown_calls = sum(1 for c in self.calls if c.api_type == "Unknown")

        print(f"\nAPI Type Breakdown:")
        print(f"  REST API: {rest_calls}")
        print(f"  GraphQL API: {graphql_calls}")
        print(f"  Unknown: {unknown_calls}")

        # Show quota consumption
        total_rest_consumed = 0
        total_graphql_consumed = 0

        for call in self.calls:
            if call.rate_limit_before and call.rate_limit_after:
                consumed = call.rate_limit_before["remaining"] - call.rate_limit_after["remaining"]
                if call.api_type == "REST":
                    total_rest_consumed += consumed
                elif call.api_type == "GraphQL":
                    total_graphql_consumed += consumed

        print(f"\nQuota Consumed:")
        print(f"  REST API: {total_rest_consumed}")
        print(f"  GraphQL API: {total_graphql_consumed}")

        # Show recent errors
        errors = [c for c in self.calls if not c.success]
        if errors:
            print(f"\n⚠️  Recent Errors ({len(errors)}):")
            for call in errors[-5:]:
                print(f"  - {' '.join(call.command[:3])}...")
                print(f"    Error: {call.error_message}")

        print("=" * 60 + "\n")


# Global monitor instance for convenience
_global_monitor = GHMonitor()


def run_gh_monitored(command: List[str], **kwargs) -> subprocess.CompletedProcess:
    """
    Convenience function to run gh command with monitoring.

    Usage:
        from adw_modules.gh_api_monitor import run_gh_monitored
        result = run_gh_monitored(["gh", "issue", "list"])
    """
    return _global_monitor.run_gh_command(command, **kwargs)


def get_monitor() -> GHMonitor:
    """Get the global monitor instance."""
    return _global_monitor


if __name__ == "__main__":
    # CLI tool for checking current usage
    monitor = GHMonitor()

    print("Checking current GitHub API rate limits...\n")

    rest_limit = monitor.check_rate_limit("rest")
    if rest_limit:
        remaining_pct = (rest_limit["remaining"] / rest_limit["limit"]) * 100
        print(f"REST API: {rest_limit['remaining']}/{rest_limit['limit']} ({remaining_pct:.1f}% remaining)")

    graphql_limit = monitor.check_rate_limit("graphql")
    if graphql_limit:
        remaining_pct = (graphql_limit["remaining"] / graphql_limit["limit"]) * 100
        print(f"GraphQL API: {graphql_limit['remaining']}/{graphql_limit['limit']} ({remaining_pct:.1f}% remaining)")

    # Show log file location
    print(f"\n📝 API calls logged to: {monitor.log_file}")
    print(f"📊 View logs: tail -f {monitor.log_file} | jq .")
