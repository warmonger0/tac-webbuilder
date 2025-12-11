import pytest
from repositories.webhook_event_repository import WebhookEventRepository
import time
import uuid


@pytest.fixture(autouse=True)
def cleanup_test_webhooks():
    """Clean up test webhook events after each test."""
    yield
    # Cleanup after test - remove all test webhooks
    try:
        repo = WebhookEventRepository()
        repo.cleanup_old_events(days=0)
    except Exception:
        # Cleanup may fail if database isn't available, but don't fail the test
        pass


def test_is_duplicate_returns_false_for_new_webhook():
    """Test that new webhook is not marked as duplicate."""
    repo = WebhookEventRepository()

    webhook_id = f"test-webhook-{uuid.uuid4()}"
    assert repo.is_duplicate(webhook_id) is False


def test_is_duplicate_returns_true_for_recent_webhook():
    """Test that recently processed webhook is marked as duplicate."""
    repo = WebhookEventRepository()

    webhook_id = f"test-webhook-{uuid.uuid4()}"

    # Record webhook
    repo.record_webhook(webhook_id, "workflow_complete", "adw-123", 100)

    # Should be detected as duplicate
    assert repo.is_duplicate(webhook_id, window_seconds=30) is True


def test_is_duplicate_with_different_windows():
    """Test that duplicate detection respects the time window."""
    repo = WebhookEventRepository()

    webhook_id = f"test-webhook-{uuid.uuid4()}"

    # Record webhook
    repo.record_webhook(webhook_id, "workflow_complete", "adw-123", 100)

    # Should be detected as duplicate with 30-second window
    assert repo.is_duplicate(webhook_id, window_seconds=30) is True

    # Should still be detected with 60-second window
    assert repo.is_duplicate(webhook_id, window_seconds=60) is True


def test_record_webhook_creates_entry():
    """Test that record_webhook creates database entry."""
    repo = WebhookEventRepository()

    webhook_id = f"test-webhook-{uuid.uuid4()}"
    event_id = repo.record_webhook(
        webhook_id=webhook_id,
        webhook_type="github_issue",
        adw_id="adw-999",
        issue_number=200
    )

    assert event_id > 0


def test_record_webhook_prevents_duplicates():
    """Test that recording same webhook twice returns -1 on second call."""
    repo = WebhookEventRepository()

    webhook_id = f"test-webhook-{uuid.uuid4()}"

    # First call should succeed
    event_id_1 = repo.record_webhook(webhook_id, "workflow_complete", "adw-123", 100)
    assert event_id_1 > 0

    # Second call should return -1 (duplicate)
    event_id_2 = repo.record_webhook(webhook_id, "workflow_complete", "adw-123", 100)
    assert event_id_2 == -1


def test_cleanup_old_events():
    """Test that cleanup function executes without errors."""
    repo = WebhookEventRepository()

    webhook_id_1 = f"old-webhook-{uuid.uuid4()}"
    webhook_id_2 = f"old-webhook-{uuid.uuid4()}"

    # Create some events
    repo.record_webhook(webhook_id_1, "workflow_complete", "adw-1", 1)
    repo.record_webhook(webhook_id_2, "workflow_complete", "adw-2", 2)

    # Cleanup with very long retention (shouldn't delete recent events)
    deleted = repo.cleanup_old_events(days=7)

    # Should execute successfully (may delete 0 since events are recent)
    assert deleted >= 0

    # Verify the webhooks still exist (not deleted because they're recent)
    assert repo.is_duplicate(webhook_id_1, window_seconds=30) is True
    assert repo.is_duplicate(webhook_id_2, window_seconds=30) is True
