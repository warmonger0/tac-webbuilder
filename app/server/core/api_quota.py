"""
API Quota Monitoring for ADW Workflows

Monitors Claude API usage and provides quota checking functionality
to prevent ADW workflows from starting when quota is exhausted.
"""

import os
import logging
from typing import Optional, Tuple
from datetime import datetime
from anthropic import Anthropic, RateLimitError, APIError

logger = logging.getLogger(__name__)

# Initialize Anthropic client
try:
    anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    ANTHROPIC_AVAILABLE = True
except Exception as e:
    logger.warning(f"[API Quota] Could not initialize Anthropic client: {e}")
    ANTHROPIC_AVAILABLE = False


def check_anthropic_quota() -> Tuple[bool, Optional[str]]:
    """
    Check if Anthropic API quota is available by making a minimal test call.

    Returns:
        Tuple of (quota_available: bool, error_message: Optional[str])
    """
    if not ANTHROPIC_AVAILABLE:
        return False, "Anthropic client not initialized (missing API key?)"

    try:
        # Make minimal API call to check quota
        # Using smallest model and minimal tokens to conserve quota
        anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "ping"}]
        )

        logger.info("[API Quota] Anthropic quota check: AVAILABLE")
        return True, None

    except RateLimitError as e:
        error_msg = str(e)
        logger.error(f"[API Quota] Anthropic quota EXHAUSTED: {error_msg}")

        # Extract reset time from error message if available
        if "regain access" in error_msg:
            return False, error_msg
        else:
            return False, "API quota exhausted. Please check your Anthropic dashboard."

    except APIError as e:
        logger.error(f"[API Quota] Anthropic API error during quota check: {e}")
        return False, f"API error: {str(e)}"

    except Exception as e:
        logger.error(f"[API Quota] Unexpected error during quota check: {e}")
        return False, f"Unexpected error: {str(e)}"


def can_start_adw() -> Tuple[bool, Optional[str]]:
    """
    Determine if an ADW workflow can be started based on API quota availability.

    Returns:
        Tuple of (can_start: bool, reason: Optional[str])
    """
    # Check Anthropic quota
    anthropic_ok, anthropic_error = check_anthropic_quota()

    if not anthropic_ok:
        logger.warning(
            f"[API Quota] Cannot start ADW workflow - "
            f"Anthropic quota unavailable: {anthropic_error}"
        )
        return False, f"Anthropic API quota unavailable: {anthropic_error}"

    logger.info("[API Quota] All API quotas available - ADW can start")
    return True, None


def get_quota_status() -> dict:
    """
    Get current API quota status for monitoring/debugging.

    Returns:
        Dictionary with quota status information
    """
    anthropic_ok, anthropic_msg = check_anthropic_quota()

    return {
        "anthropic": {
            "available": anthropic_ok,
            "message": anthropic_msg,
            "checked_at": datetime.utcnow().isoformat()
        }
    }


def should_skip_e2e_tests() -> Tuple[bool, Optional[str]]:
    """
    Determine if E2E tests should be skipped due to quota constraints.

    E2E tests may require API access for browser automation and Claude Code.
    If quota is low/exhausted, skip E2E tests to preserve quota for core functionality.

    Returns:
        Tuple of (should_skip: bool, reason: Optional[str])
    """
    anthropic_ok, anthropic_error = check_anthropic_quota()

    if not anthropic_ok:
        logger.warning(
            f"[API Quota] Skipping E2E tests due to quota constraints: {anthropic_error}"
        )
        return True, f"E2E tests skipped: {anthropic_error}"

    return False, None


def log_quota_warning() -> None:
    """
    Log a warning about current quota status for operator awareness.
    """
    status = get_quota_status()

    if not status['anthropic']['available']:
        logger.warning(
            f"⚠️  [API Quota] Anthropic quota unavailable: {status['anthropic']['message']}"
        )
    else:
        logger.info("✅ [API Quota] All quotas available")


# Convenience function for ADW workflow scripts
def ensure_quota_available() -> bool:
    """
    Convenience function for ADW scripts to check quota before starting.

    Returns:
        True if quota available, False otherwise (with appropriate logging)
    """
    can_start, reason = can_start_adw()

    if not can_start:
        logger.error(f"❌ [API Quota] Cannot proceed: {reason}")
        print("\n❌ API Quota Unavailable\n")
        print(f"Reason: {reason}\n")
        print("ADW workflow cannot start. Please wait for quota reset or upgrade your plan.\n")

    return can_start
