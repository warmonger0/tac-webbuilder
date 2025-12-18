#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv"]
# ///

"""
GitHub API Rate Limit Module

Provides utilities for checking and handling GitHub API rate limits
to prevent workflow failures and optimize API usage.
"""

import subprocess
import json
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class RateLimitInfo:
    """Information about GitHub API rate limits."""

    def __init__(self, api_type: str, limit: int, remaining: int, reset_at: str):
        self.api_type = api_type  # "REST" or "GraphQL"
        self.limit = limit
        self.remaining = remaining
        self.reset_at = reset_at
        self.reset_datetime = datetime.fromisoformat(reset_at.replace('Z', '+00:00'))

    @property
    def usage_percent(self) -> float:
        """Return percentage of API quota used."""
        return ((self.limit - self.remaining) / self.limit) * 100

    @property
    def is_exhausted(self) -> bool:
        """Check if rate limit is exhausted."""
        return self.remaining == 0

    @property
    def seconds_until_reset(self) -> int:
        """Seconds until rate limit resets."""
        now = datetime.now(timezone.utc)
        delta = self.reset_datetime - now
        return max(0, int(delta.total_seconds()))

    def __str__(self) -> str:
        return f"{self.api_type}: {self.remaining}/{self.limit} remaining ({self.usage_percent:.1f}% used), resets in {self.seconds_until_reset}s"


class RateLimitError(Exception):
    """Exception raised when GitHub API rate limit is hit."""

    def __init__(self, rate_limit_info: RateLimitInfo):
        self.rate_limit_info = rate_limit_info
        super().__init__(str(rate_limit_info))


def check_rest_rate_limit() -> Optional[RateLimitInfo]:
    """
    Check GitHub REST API rate limit.

    Returns:
        RateLimitInfo if successful, None if gh CLI not available
    """
    try:
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

        # Convert Unix timestamp to ISO format
        reset_dt = datetime.fromtimestamp(core['reset'], tz=timezone.utc)
        reset_iso = reset_dt.isoformat()

        return RateLimitInfo(
            api_type="REST",
            limit=core['limit'],
            remaining=core['remaining'],
            reset_at=reset_iso
        )
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError, KeyError):
        return None


def check_graphql_rate_limit() -> Optional[RateLimitInfo]:
    """
    Check GitHub GraphQL API rate limit.

    Returns:
        RateLimitInfo if successful, None if gh CLI not available
    """
    try:
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

        return RateLimitInfo(
            api_type="GraphQL",
            limit=rate_limit['limit'],
            remaining=rate_limit['remaining'],
            reset_at=rate_limit['resetAt']
        )
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError, KeyError):
        return None


def check_all_rate_limits() -> Dict[str, Optional[RateLimitInfo]]:
    """
    Check both REST and GraphQL rate limits.

    Returns:
        Dictionary with 'rest' and 'graphql' keys containing RateLimitInfo or None
    """
    return {
        'rest': check_rest_rate_limit(),
        'graphql': check_graphql_rate_limit()
    }


def ensure_rate_limit_available(api_type: str = "graphql", min_remaining: int = 10, logger=None) -> None:
    """
    Ensure sufficient rate limit is available before making API calls.

    Args:
        api_type: "rest" or "graphql" (default: graphql)
        min_remaining: Minimum remaining requests required (default: 10)
        logger: Optional logger instance for logging warnings

    Raises:
        RateLimitError: If rate limit is below threshold
    """
    if api_type.lower() == "rest":
        info = check_rest_rate_limit()
    else:
        info = check_graphql_rate_limit()

    if info is None:
        if logger:
            logger.warning("Unable to check rate limit - proceeding with caution")
        return

    if logger:
        logger.info(f"Rate limit check: {info}")

    if info.remaining < min_remaining:
        if logger:
            logger.error(f"Rate limit critically low: {info}")
        raise RateLimitError(info)


def get_rate_limit_status_message(include_rest: bool = True, include_graphql: bool = True) -> str:
    """
    Get a formatted status message for rate limits.

    Args:
        include_rest: Include REST API status
        include_graphql: Include GraphQL API status

    Returns:
        Formatted string with rate limit status
    """
    lines = ["GitHub API Rate Limits:"]

    if include_rest:
        rest = check_rest_rate_limit()
        if rest:
            lines.append(f"  REST API: {rest.remaining}/{rest.limit} remaining ({rest.usage_percent:.1f}% used)")
            if rest.is_exhausted:
                lines.append(f"    ⚠️  EXHAUSTED - Resets in {rest.seconds_until_reset}s")
        else:
            lines.append("  REST API: Unable to check")

    if include_graphql:
        graphql = check_graphql_rate_limit()
        if graphql:
            lines.append(f"  GraphQL API: {graphql.remaining}/{graphql.limit} remaining ({graphql.usage_percent:.1f}% used)")
            if graphql.is_exhausted:
                lines.append(f"    ⚠️  EXHAUSTED - Resets in {graphql.seconds_until_reset}s")
        else:
            lines.append("  GraphQL API: Unable to check")

    return "\n".join(lines)


if __name__ == "__main__":
    # CLI tool for checking rate limits
    print(get_rate_limit_status_message())
