# Session 19 - Phase 1, Part 2: Webhook Signature Validation

## Context
**Project**: tac-webbuilder - AI-powered GitHub automation platform
**Database**: PostgreSQL (production)
**Main Ports**: Backend 8002, Frontend 5173
**Issue**: Webhooks have NO signature validation - anyone can trigger ADW workflows via POST requests.

## Objective
Implement HMAC-SHA256 signature validation for both GitHub webhook (external) and workflow completion webhook (internal).

## Background
- **Files**:
  - `adws/adw_triggers/trigger_webhook.py` (external webhook)
  - `app/server/routes/queue_routes.py` (internal webhook, lines 594-720)
- **Security Risk**: CRITICAL - Unauthorized workflow execution
- **Time**: 3 hours
- **Risk**: Medium (could break webhook flow if misconfigured)

## Current Problem

**External Webhook** (`trigger_webhook.py`):
- NO GitHub webhook signature verification (X-Hub-Signature-256)
- Accepts any POST request without authentication

**Internal Webhook** (`queue_routes.py`):
- NO authentication on workflow_complete endpoint
- Any client can mark phases complete

**Attack Vector**: Anyone can send POST requests to trigger expensive AI workflows.

## Target Solution

- Implement HMAC-SHA256 validation using X-Hub-Signature-256 header
- Create shared validation utility for both webhooks
- Reject requests with invalid signatures (401 Unauthorized)
- Use constant-time comparison to prevent timing attacks

## Implementation Steps

### Step 1: Create Webhook Security Utility

**Create new file**: `app/server/utils/webhook_security.py`

```python
"""Webhook security utilities for signature validation."""
import hmac
import hashlib
import os
from typing import Optional
from fastapi import Request, HTTPException
import logging

logger = logging.getLogger(__name__)


def get_webhook_secret(webhook_type: str = "github") -> str:
    """Get webhook secret from environment."""
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
        HTTPException 401 if signature validation fails
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
```

### Step 2: Update External Webhook

**File**: `adws/adw_triggers/trigger_webhook.py`

**Add imports** at top:
```python
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../app/server"))
from utils.webhook_security import validate_webhook_request
```

**Update POST handler** (around line 540-687):
```python
@app.post("/gh-webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle GitHub webhook events (with signature validation)."""

    # VALIDATE SIGNATURE FIRST (before any processing)
    try:
        body = await validate_webhook_request(request, webhook_type="github")
    except HTTPException as e:
        logger.error(f"[WEBHOOK] Signature validation failed: {e.detail}")
        return {"status": "error", "message": "Unauthorized"}

    # Get event type
    event_type = request.headers.get("X-GitHub-Event", "")

    # Parse payload (already validated)
    try:
        payload = json.loads(body.decode('utf-8'))
    except Exception as e:
        logger.error(f"[WEBHOOK] Failed to parse payload: {e}")
        return {"status": "error", "message": "Invalid payload"}

    # ... rest of existing logic ...
```

### Step 3: Update Internal Webhook

**File**: `app/server/routes/queue_routes.py`

**Add import**:
```python
from utils.webhook_security import validate_webhook_request
```

**Update endpoint** (around line 594-720):
```python
@router.post("/workflow-complete")
async def workflow_complete(
    request: Request,  # Add this parameter
    workflow_request: WorkflowCompleteRequest,
    background_tasks: BackgroundTasks
) -> WorkflowCompleteResponse:
    """Handle workflow completion webhook (with signature validation)."""

    # VALIDATE SIGNATURE
    try:
        await validate_webhook_request(request, webhook_type="internal")
    except HTTPException:
        logger.warning("[WEBHOOK] Internal webhook signature validation failed")
        # For internal webhooks, log and continue (or enforce with: raise)

    # ... rest of existing logic ...
```

### Step 4: Configure Environment Variables

**Create**: `.env.webhook.secrets` (add to .gitignore)

```bash
# GitHub webhook secret (set in GitHub repo settings)
GITHUB_WEBHOOK_SECRET=your-github-webhook-secret-here

# Internal webhook secret (for workflow-complete endpoint)
INTERNAL_WEBHOOK_SECRET=your-internal-webhook-secret-here
```

**Add to `.gitignore`**:
```
.env.webhook.secrets
```

**Set in GitHub**:
1. Go to repo Settings → Webhooks
2. Edit existing webhook or create new
3. Set "Secret" field to match GITHUB_WEBHOOK_SECRET value
4. Save

### Step 5: Test Signature Validation

```bash
# Test with invalid signature (should be rejected)
curl -X POST http://localhost:8001/gh-webhook \
  -H "X-GitHub-Event: ping" \
  -H "X-Hub-Signature-256: sha256=invalid" \
  -d '{"zen":"test"}'

# Expected: {"status": "error", "message": "Unauthorized"}
```

**Create unit tests**: `app/server/tests/utils/test_webhook_security.py`

```python
import pytest
from utils.webhook_security import verify_github_signature
import hmac
import hashlib


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
```

Run tests:
```bash
cd app/server
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql \
.venv/bin/pytest tests/utils/test_webhook_security.py -v
```

### Step 6: Commit Changes

```bash
git add app/server/utils/webhook_security.py
git add app/server/tests/utils/test_webhook_security.py
git add adws/adw_triggers/trigger_webhook.py
git add app/server/routes/queue_routes.py
git add .gitignore

git commit -m "security: Add HMAC-SHA256 signature validation to webhooks

Implemented GitHub webhook signature verification to prevent unauthorized
workflow execution.

Changes:
- Created utils/webhook_security.py with signature validation utilities
- Added validation to external webhook (trigger_webhook.py)
- Added validation to internal webhook (queue_routes.py)
- Uses X-Hub-Signature-256 header with HMAC-SHA256
- Constant-time comparison prevents timing attacks
- Unit tests for signature validation

Security Impact:
- Prevents unauthorized POST requests from triggering ADW workflows
- Validates webhook authenticity before processing
- Configurable via environment variables

Configuration Required:
- Set GITHUB_WEBHOOK_SECRET in environment
- Set INTERNAL_WEBHOOK_SECRET in environment
- Configure matching secret in GitHub repo webhook settings

Session 19 - Phase 1, Part 2/4"
```

## Success Criteria

- ✅ Signature validation utility created with unit tests
- ✅ External webhook validates X-Hub-Signature-256
- ✅ Internal webhook validates signatures
- ✅ Invalid signatures return 401 Unauthorized
- ✅ Environment variables configured
- ✅ Unit tests passing
- ✅ Manual webhook test confirms rejection of invalid signatures

## Security Impact

**Before**: Anyone can trigger workflows via POST
**After**: Only authenticated requests with valid HMAC signatures accepted
**Protection**: Constant-time comparison prevents timing attacks

## Summary Template

After completing, provide this summary:

```
# Part 2 Complete: Webhook Signature Validation

## Changes Made
- Created: app/server/utils/webhook_security.py
- Created: app/server/tests/utils/test_webhook_security.py
- Modified: adws/adw_triggers/trigger_webhook.py
- Modified: app/server/routes/queue_routes.py
- Modified: .gitignore

## Environment Configuration
- GITHUB_WEBHOOK_SECRET: [Configured/Pending]
- INTERNAL_WEBHOOK_SECRET: [Configured/Pending]
- GitHub webhook settings: [Updated/Pending]

## Test Results
- Unit tests (webhook_security): X/X passing
- Manual invalid signature test: [PASS/FAIL]
- All existing tests: [PASS/FAIL]

## Issues Encountered
- [List any issues OR "None"]

## Files Modified
- app/server/utils/webhook_security.py (new)
- app/server/tests/utils/test_webhook_security.py (new)
- adws/adw_triggers/trigger_webhook.py
- app/server/routes/queue_routes.py
- .gitignore

## Commit Hash
- [Paste commit hash]

## Ready for Part 3
✅ Part 2 complete. Webhooks now validate signatures.
Ready for idempotency protection.
```

---

**Estimated Time**: 3 hours
**Dependencies**: None
**Next**: Part 3 - Webhook Idempotency Protection
