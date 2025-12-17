#!/usr/bin/env python3
"""
Test script for GitHub webhook handler.

Tests the /webhooks/github endpoint with sample payloads.
"""
import asyncio
import hashlib
import hmac
import json
import os

import httpx

# Webhook endpoint (use localhost for testing, or public URL for production)
WEBHOOK_URL = os.environ.get(
    "WEBHOOK_URL",
    "http://localhost:8002/api/v1/webhooks/github"
)
# Production URL: https://api.directmyagent.com/api/v1/webhooks/github

# Get webhook secret from environment (or use test secret)
WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "test_secret_123")


def generate_signature(payload: dict) -> str:
    """Generate GitHub webhook signature."""
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    hash_object = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"), msg=payload_bytes, digestmod=hashlib.sha256
    )
    return "sha256=" + hash_object.hexdigest()


async def test_issue_closed():
    """Test issue closed event."""
    print("\n=== Testing Issue Closed Event ===")

    payload = {
        "action": "closed",
        "issue": {
            "number": 123,
            "title": "Test Feature",
            "state": "closed",
            "labels": [{"name": "enhancement"}, {"name": "priority:high"}],
        },
    }

    signature = generate_signature(payload)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                WEBHOOK_URL,
                json=payload,
                headers={
                    "X-GitHub-Event": "issues",
                    "X-Hub-Signature-256": signature,
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")


async def test_issue_reopened():
    """Test issue reopened event."""
    print("\n=== Testing Issue Reopened Event ===")

    payload = {
        "action": "reopened",
        "issue": {
            "number": 123,
            "title": "Test Feature",
            "state": "open",
            "labels": [{"name": "enhancement"}],
        },
    }

    signature = generate_signature(payload)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                WEBHOOK_URL,
                json=payload,
                headers={
                    "X-GitHub-Event": "issues",
                    "X-Hub-Signature-256": signature,
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")


async def test_issue_labeled():
    """Test issue labeled event."""
    print("\n=== Testing Issue Labeled Event ===")

    payload = {
        "action": "labeled",
        "issue": {
            "number": 123,
            "title": "Test Feature",
            "state": "open",
            "labels": [
                {"name": "enhancement"},
                {"name": "priority:high"},
                {"name": "backend"},
            ],
        },
        "label": {"name": "backend"},
    }

    signature = generate_signature(payload)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                WEBHOOK_URL,
                json=payload,
                headers={
                    "X-GitHub-Event": "issues",
                    "X-Hub-Signature-256": signature,
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")


async def test_invalid_signature():
    """Test webhook with invalid signature (should be rejected)."""
    print("\n=== Testing Invalid Signature (Should Fail) ===")

    payload = {
        "action": "closed",
        "issue": {"number": 123, "title": "Test Feature", "state": "closed"},
    }

    # Use wrong signature
    invalid_signature = "sha256=invalid_signature_here"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                WEBHOOK_URL,
                json=payload,
                headers={
                    "X-GitHub-Event": "issues",
                    "X-Hub-Signature-256": invalid_signature,
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            print(f"Status: {response.status_code} (expected 401)")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")


async def test_nonexistent_issue():
    """Test webhook for issue not linked to any planned feature."""
    print("\n=== Testing Non-Existent Issue (Should Skip) ===")

    payload = {
        "action": "closed",
        "issue": {
            "number": 99999,  # Issue number that doesn't exist
            "title": "Unknown Feature",
            "state": "closed",
        },
    }

    signature = generate_signature(payload)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                WEBHOOK_URL,
                json=payload,
                headers={
                    "X-GitHub-Event": "issues",
                    "X-Hub-Signature-256": signature,
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("GitHub Webhook Handler Test Suite")
    print("=" * 60)
    print(f"Webhook URL: {WEBHOOK_URL}")
    print(f"Using secret: {'[SET]' if WEBHOOK_SECRET != 'test_secret_123' else '[DEFAULT]'}")

    # Run tests
    await test_issue_closed()
    await asyncio.sleep(1)

    await test_issue_reopened()
    await asyncio.sleep(1)

    await test_issue_labeled()
    await asyncio.sleep(1)

    await test_nonexistent_issue()
    await asyncio.sleep(1)

    await test_invalid_signature()

    print("\n" + "=" * 60)
    print("Tests Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
