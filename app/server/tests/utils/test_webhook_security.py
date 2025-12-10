"""Unit tests for webhook security utilities."""
import pytest
from utils.webhook_security import verify_github_signature, get_webhook_secret
import hmac
import hashlib
import os


def test_verify_github_signature_valid():
    """Test valid signature verification."""
    secret = "test-secret"
    payload = b'{"test": "data"}'

    # Generate valid signature
    hash_object = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    signature = "sha256=" + hash_object.hexdigest()

    assert verify_github_signature(payload, signature, secret) is True


def test_verify_github_signature_invalid():
    """Test invalid signature rejection."""
    secret = "test-secret"
    payload = b'{"test": "data"}'
    signature = "sha256=invalid"

    assert verify_github_signature(payload, signature, secret) is False


def test_verify_github_signature_missing():
    """Test missing signature rejection."""
    assert verify_github_signature(b"data", "", "secret") is False
    assert verify_github_signature(b"data", None, "secret") is False


def test_verify_github_signature_wrong_format():
    """Test signature with wrong format (not sha256=)."""
    secret = "test-secret"
    payload = b'{"test": "data"}'
    signature = "md5=somehash"

    assert verify_github_signature(payload, signature, secret) is False


def test_verify_github_signature_different_payload():
    """Test signature mismatch when payload is modified."""
    secret = "test-secret"
    original_payload = b'{"test": "data"}'
    modified_payload = b'{"test": "modified"}'

    # Generate valid signature for original payload
    hash_object = hmac.new(secret.encode(), msg=original_payload, digestmod=hashlib.sha256)
    signature = "sha256=" + hash_object.hexdigest()

    # Verify with modified payload should fail
    assert verify_github_signature(modified_payload, signature, secret) is False


def test_verify_github_signature_different_secret():
    """Test signature mismatch when secret is different."""
    secret1 = "test-secret-1"
    secret2 = "test-secret-2"
    payload = b'{"test": "data"}'

    # Generate signature with secret1
    hash_object = hmac.new(secret1.encode(), msg=payload, digestmod=hashlib.sha256)
    signature = "sha256=" + hash_object.hexdigest()

    # Verify with secret2 should fail
    assert verify_github_signature(payload, signature, secret2) is False


def test_get_webhook_secret_github():
    """Test getting GitHub webhook secret from environment."""
    # Set environment variable
    os.environ["GITHUB_WEBHOOK_SECRET"] = "test-github-secret"

    secret = get_webhook_secret("github")
    assert secret == "test-github-secret"

    # Clean up
    del os.environ["GITHUB_WEBHOOK_SECRET"]


def test_get_webhook_secret_internal():
    """Test getting internal webhook secret from environment."""
    # Set environment variable
    os.environ["INTERNAL_WEBHOOK_SECRET"] = "test-internal-secret"

    secret = get_webhook_secret("internal")
    assert secret == "test-internal-secret"

    # Clean up
    del os.environ["INTERNAL_WEBHOOK_SECRET"]


def test_get_webhook_secret_missing():
    """Test error when webhook secret is not configured."""
    # Ensure env var is not set
    if "GITHUB_WEBHOOK_SECRET" in os.environ:
        del os.environ["GITHUB_WEBHOOK_SECRET"]

    with pytest.raises(ValueError, match="Webhook secret not configured"):
        get_webhook_secret("github")


def test_verify_github_signature_without_secret_env():
    """Test signature verification when secret is not in environment."""
    # Ensure env var is not set
    if "GITHUB_WEBHOOK_SECRET" in os.environ:
        del os.environ["GITHUB_WEBHOOK_SECRET"]

    payload = b'{"test": "data"}'
    signature = "sha256=somehash"

    # Should return False when secret is not configured
    assert verify_github_signature(payload, signature, secret=None) is False


def test_verify_github_signature_empty_payload():
    """Test signature verification with empty payload."""
    secret = "test-secret"
    payload = b''

    # Generate valid signature for empty payload
    hash_object = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    signature = "sha256=" + hash_object.hexdigest()

    assert verify_github_signature(payload, signature, secret) is True


def test_verify_github_signature_large_payload():
    """Test signature verification with large payload."""
    secret = "test-secret"
    payload = b'{"test": "' + (b'x' * 10000) + b'"}'

    # Generate valid signature for large payload
    hash_object = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    signature = "sha256=" + hash_object.hexdigest()

    assert verify_github_signature(payload, signature, secret) is True
