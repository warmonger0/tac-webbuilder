"""
Lightweight webhook signature validation.

Standalone module with no external dependencies beyond standard library.
Used by trigger_webhook.py to validate GitHub webhook signatures.
"""

import hmac
import hashlib
import os
from typing import Optional


class WebhookValidationError(Exception):
    """Raised when webhook validation fails."""
    pass


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
        return False

    if not signature_header.startswith("sha256="):
        return False

    # Get secret from environment if not provided
    if secret is None:
        secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
        if not secret:
            # No secret configured - fail validation
            return False

    # Compute expected signature
    hash_object = hmac.new(
        secret.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(signature_header, expected_signature)


async def validate_webhook(request) -> bytes:
    """Validate webhook request and return raw body.

    Args:
        request: FastAPI Request object

    Returns:
        Raw request body as bytes

    Raises:
        WebhookValidationError if signature validation fails
    """
    # Read raw body
    body = await request.body()

    # Get signature header
    signature_header = request.headers.get("X-Hub-Signature-256")

    # Verify signature
    if not verify_github_signature(body, signature_header):
        raise WebhookValidationError("Invalid webhook signature")

    return body
