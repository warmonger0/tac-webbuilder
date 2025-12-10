"""Webhook security utilities for signature validation."""
import hmac
import hashlib
import os
from typing import Optional
from fastapi import Request, HTTPException
import logging

logger = logging.getLogger(__name__)


def get_webhook_secret(webhook_type: str = "github") -> str:
    """Get webhook secret from environment.

    Args:
        webhook_type: Type of webhook ('github' or 'internal')

    Returns:
        Webhook secret string

    Raises:
        ValueError: If webhook secret is not configured
    """
    env_var = f"{webhook_type.upper()}_WEBHOOK_SECRET"
    secret = os.environ.get(env_var)
    if not secret:
        raise ValueError(f"Webhook secret not configured. Set {env_var} environment variable.")
    return secret


def verify_github_signature(
    payload_body: bytes,
    signature_header: str,
    secret: Optional[str] = None
) -> bool:
    """Verify GitHub webhook HMAC-SHA256 signature.

    Args:
        payload_body: Raw request body as bytes
        signature_header: Value of X-Hub-Signature-256 header
        secret: Webhook secret (defaults to GITHUB_WEBHOOK_SECRET env var)

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature_header:
        logger.warning("[WEBHOOK_SECURITY] No signature header provided")
        return False

    if not signature_header.startswith("sha256="):
        logger.warning("[WEBHOOK_SECURITY] Invalid signature format")
        return False

    # Get secret
    if secret is None:
        try:
            secret = get_webhook_secret("github")
        except ValueError as e:
            logger.error(f"[WEBHOOK_SECURITY] {e}")
            return False

    # Compute expected signature
    hash_object = hmac.new(
        secret.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()

    # Constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(signature_header, expected_signature)

    if not is_valid:
        logger.warning("[WEBHOOK_SECURITY] Signature mismatch detected")

    return is_valid


async def validate_webhook_request(
    request: Request,
    webhook_type: str = "github"
) -> bytes:
    """Validate webhook request and return raw body.

    Args:
        request: FastAPI Request object
        webhook_type: Type of webhook ('github' or 'internal')

    Returns:
        Raw request body as bytes

    Raises:
        HTTPException: 401 if signature validation fails
    """
    # Read raw body
    body = await request.body()

    # Get signature header
    signature_header = request.headers.get("X-Hub-Signature-256")

    # Verify signature
    if not verify_github_signature(body, signature_header):
        logger.error(f"[WEBHOOK_SECURITY] Invalid signature for {webhook_type} webhook")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    logger.info(f"[WEBHOOK_SECURITY] Valid signature for {webhook_type} webhook")
    return body
