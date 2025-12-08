"""
Unit tests for PlannedFeaturesService.

Tests CRUD operations, filtering, statistics, and timestamp management for planned features.
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from core.models import PlannedFeature, PlannedFeatureCreate, PlannedFeatureUpdate
from services.planned_features_service import PlannedFeaturesService


@pytest.fixture
def mock_adapter():
    """Create a mock database adapter."""
    adapter = MagicMock()
    adapter.placeholder.return_value = "%s"  # PostgreSQL placeholder
    adapter.now_function.return_value = "NOW()"
    adapter.get_db_type.return_value = "postgresql"
    return adapter


@pytest.fixture
def service(mock_adapter):
    """Create PlannedFeaturesService with mocked adapter."""
    with patch(
        "services.planned_features_service.get_database_adapter",
        return_value=mock_adapter,
    ):
        return PlannedFeaturesService()


class TestPlannedFeaturesServiceCreate:
    """Test planned feature creation."""

    def test_create_feature_success(self, service, mock_adapter):
        """Test creating a new planned feature."""
        # Setup
        feature_create = PlannedFeatureCreate(
            item_type="session",
            title="Session 99: Test Session",
            description="Test description",
            status="planned",
            priority="high",
            estimated_hours=3.0,
            session_number=99,
            tags=["test", "session"],
        )

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            (1,),  # RETURNING id from INSERT
            {  # Full row from SELECT
                "id": 1,
                "item_type": "session",
                "title": "Session 99: Test Session",
                "description": "Test description",
                "status": "planned",
                "priority": "high",
                "estimated_hours": 3.0,
                "actual_hours": None,
                "session_number": 99,
                "github_issue_number": None,
                "parent_id": None,
                "tags": ["test", "session"],
                "completion_notes": None,
                "created_at": datetime(2025, 12, 7, 10, 0, 0),
                "updated_at": datetime(2025, 12, 7, 10, 0, 0),
                "started_at": None,
                "completed_at": None,
            },
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        # Execute
        result = service.create(feature_create)

        # Assert
        assert isinstance(result, PlannedFeature)
        assert result.id == 1
        assert result.title == "Session 99: Test Session"
        assert result.status == "planned"
        assert result.tags == ["test", "session"]
        assert mock_cursor.execute.call_count == 2  # INSERT + SELECT

    def test_create_feature_with_parent(self, service, mock_adapter):
        """Test creating a feature with parent_id."""
        feature_create = PlannedFeatureCreate(
            item_type="feature",
            title="Child Feature",
            description="Sub-feature",
            status="planned",
            parent_id=5,
            tags=["child"],
        )

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            (2,),
            {
                "id": 2,
                "item_type": "feature",
                "title": "Child Feature",
                "description": "Sub-feature",
                "status": "planned",
                "priority": None,
                "estimated_hours": None,
                "actual_hours": None,
                "session_number": None,
                "github_issue_number": None,
                "parent_id": 5,
                "tags": ["child"],
                "completion_notes": None,
                "created_at": datetime(2025, 12, 7, 10, 0, 0),
                "updated_at": datetime(2025, 12, 7, 10, 0, 0),
                "started_at": None,
                "completed_at": None,
            },
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        # Execute
        result = service.create(feature_create)

        # Assert
        assert result.parent_id == 5
        assert result.item_type == "feature"


class TestPlannedFeaturesServiceRead:
    """Test reading planned features."""

    def test_get_by_id_found(self, service, mock_adapter):
        """Test fetching feature by ID when it exists."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "item_type": "session",
            "title": "Test Session",
            "description": "Test",
            "status": "completed",
            "priority": "high",
            "estimated_hours": 3.0,
            "actual_hours": 2.5,
            "session_number": 1,
            "github_issue_number": 42,
            "parent_id": None,
            "tags": ["test"],
            "completion_notes": "All done",
            "created_at": datetime(2025, 12, 7, 10, 0, 0),
            "updated_at": datetime(2025, 12, 7, 11, 0, 0),
            "started_at": datetime(2025, 12, 7, 10, 15, 0),
            "completed_at": datetime(2025, 12, 7, 11, 0, 0),
        }
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        # Execute
        result = service.get_by_id(1)

        # Assert
        assert result is not None
        assert result.id == 1
        assert result.title == "Test Session"
        assert result.status == "completed"
        assert result.actual_hours == 2.5

    def test_get_by_id_not_found(self, service, mock_adapter):
        """Test fetching feature by ID when it doesn't exist."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        # Execute
        result = service.get_by_id(999)

        # Assert
        assert result is None

    def test_get_all_no_filters(self, service, mock_adapter):
        """Test fetching all features without filters."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "item_type": "session",
                "title": "Session 1",
                "description": None,
                "status": "in_progress",
                "priority": "high",
                "estimated_hours": 3.0,
                "actual_hours": None,
                "session_number": 1,
                "github_issue_number": None,
                "parent_id": None,
                "tags": ["session"],
                "completion_notes": None,
                "created_at": datetime(2025, 12, 7, 10, 0, 0),
                "updated_at": datetime(2025, 12, 7, 10, 0, 0),
                "started_at": datetime(2025, 12, 7, 10, 0, 0),
                "completed_at": None,
            },
            {
                "id": 2,
                "item_type": "feature",
                "title": "Feature 1",
                "description": None,
                "status": "planned",
                "priority": "medium",
                "estimated_hours": 5.0,
                "actual_hours": None,
                "session_number": None,
                "github_issue_number": None,
                "parent_id": None,
                "tags": ["feature"],
                "completion_notes": None,
                "created_at": datetime(2025, 12, 7, 9, 0, 0),
                "updated_at": datetime(2025, 12, 7, 9, 0, 0),
                "started_at": None,
                "completed_at": None,
            },
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        # Execute
        results = service.get_all()

        # Assert
        assert len(results) == 2
        assert results[0].title == "Session 1"
        assert results[1].title == "Feature 1"

    def test_get_all_with_filters(self, service, mock_adapter):
        """Test fetching features with status filter."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "item_type": "session",
                "title": "Completed Session",
                "description": None,
                "status": "completed",
                "priority": "high",
                "estimated_hours": 3.0,
                "actual_hours": 3.0,
                "session_number": 1,
                "github_issue_number": None,
                "parent_id": None,
                "tags": [],
                "completion_notes": "Done",
                "created_at": datetime(2025, 12, 7, 10, 0, 0),
                "updated_at": datetime(2025, 12, 7, 11, 0, 0),
                "started_at": datetime(2025, 12, 7, 10, 0, 0),
                "completed_at": datetime(2025, 12, 7, 11, 0, 0),
            }
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        # Execute
        results = service.get_all(status="completed", priority="high", limit=50)

        # Assert
        assert len(results) == 1
        assert results[0].status == "completed"


class TestPlannedFeaturesServiceUpdate:
    """Test updating planned features."""

    def test_update_title_and_description(self, service, mock_adapter):
        """Test updating feature title and description."""
        # Mock existing feature
        existing_feature = {
            "id": 1,
            "item_type": "session",
            "title": "Old Title",
            "description": "Old description",
            "status": "planned",
            "priority": "high",
            "estimated_hours": 3.0,
            "actual_hours": None,
            "session_number": 1,
            "github_issue_number": None,
            "parent_id": None,
            "tags": [],
            "completion_notes": None,
            "created_at": datetime(2025, 12, 7, 10, 0, 0),
            "updated_at": datetime(2025, 12, 7, 10, 0, 0),
            "started_at": None,
            "completed_at": None,
        }

        updated_feature = existing_feature.copy()
        updated_feature["title"] = "New Title"
        updated_feature["description"] = "New description"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [existing_feature, updated_feature]
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        update_data = PlannedFeatureUpdate(
            title="New Title", description="New description"
        )

        # Execute
        result = service.update(1, update_data)

        # Assert
        assert result.title == "New Title"
        assert result.description == "New description"

    def test_update_status_to_in_progress_sets_timestamp(self, service, mock_adapter):
        """Test that changing status to in_progress sets started_at."""
        existing_feature = {
            "id": 1,
            "item_type": "session",
            "title": "Test",
            "description": None,
            "status": "planned",
            "priority": "high",
            "estimated_hours": 3.0,
            "actual_hours": None,
            "session_number": 1,
            "github_issue_number": None,
            "parent_id": None,
            "tags": [],
            "completion_notes": None,
            "created_at": datetime(2025, 12, 7, 10, 0, 0),
            "updated_at": datetime(2025, 12, 7, 10, 0, 0),
            "started_at": None,
            "completed_at": None,
        }

        updated_feature = existing_feature.copy()
        updated_feature["status"] = "in_progress"
        updated_feature["started_at"] = datetime(2025, 12, 7, 10, 30, 0)

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [existing_feature, updated_feature]
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        update_data = PlannedFeatureUpdate(status="in_progress")

        # Execute
        result = service.update(1, update_data)

        # Assert
        assert result.status == "in_progress"
        assert result.started_at is not None

    def test_update_status_to_completed_sets_timestamp(self, service, mock_adapter):
        """Test that changing status to completed sets completed_at."""
        existing_feature = {
            "id": 1,
            "item_type": "session",
            "title": "Test",
            "description": None,
            "status": "in_progress",
            "priority": "high",
            "estimated_hours": 3.0,
            "actual_hours": None,
            "session_number": 1,
            "github_issue_number": None,
            "parent_id": None,
            "tags": [],
            "completion_notes": None,
            "created_at": datetime(2025, 12, 7, 10, 0, 0),
            "updated_at": datetime(2025, 12, 7, 10, 0, 0),
            "started_at": datetime(2025, 12, 7, 10, 0, 0),
            "completed_at": None,
        }

        updated_feature = existing_feature.copy()
        updated_feature["status"] = "completed"
        updated_feature["completed_at"] = datetime(2025, 12, 7, 11, 0, 0)

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [existing_feature, updated_feature]
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        update_data = PlannedFeatureUpdate(status="completed", actual_hours=2.5)

        # Execute
        result = service.update(1, update_data)

        # Assert
        assert result.status == "completed"
        assert result.completed_at is not None

    def test_update_nonexistent_feature_raises_error(self, service, mock_adapter):
        """Test that updating a nonexistent feature raises ValueError."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        update_data = PlannedFeatureUpdate(title="New Title")

        # Execute & Assert
        with pytest.raises(ValueError, match="Feature 999 not found"):
            service.update(999, update_data)


class TestPlannedFeaturesServiceDelete:
    """Test deleting planned features."""

    def test_delete_soft_deletes(self, service, mock_adapter):
        """Test that delete sets status to cancelled."""
        existing_feature = {
            "id": 1,
            "item_type": "session",
            "title": "Test",
            "description": None,
            "status": "planned",
            "priority": "high",
            "estimated_hours": 3.0,
            "actual_hours": None,
            "session_number": 1,
            "github_issue_number": None,
            "parent_id": None,
            "tags": [],
            "completion_notes": None,
            "created_at": datetime(2025, 12, 7, 10, 0, 0),
            "updated_at": datetime(2025, 12, 7, 10, 0, 0),
            "started_at": None,
            "completed_at": None,
        }

        deleted_feature = existing_feature.copy()
        deleted_feature["status"] = "cancelled"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [existing_feature, deleted_feature]
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        # Execute
        result = service.delete(1)

        # Assert
        assert result is True


class TestPlannedFeaturesServiceStatistics:
    """Test statistics calculations."""

    def test_get_statistics(self, service, mock_adapter):
        """Test getting statistics about planned features."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [("planned", 5), ("in_progress", 2), ("completed", 10)],  # by_status
            [("high", 3), ("medium", 8), ("low", 6)],  # by_priority
            [("session", 7), ("feature", 10)],  # by_type
        ]
        mock_cursor.fetchone.side_effect = [
            (45.5, 38.0),  # hours summary
            (58.8,),  # completion rate
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        # Execute
        stats = service.get_statistics()

        # Assert
        assert stats["by_status"]["planned"] == 5
        assert stats["by_status"]["completed"] == 10
        assert stats["by_priority"]["high"] == 3
        assert stats["by_type"]["session"] == 7
        assert stats["total_estimated_hours"] == 45.5
        assert stats["total_actual_hours"] == 38.0
        assert stats["completion_rate"] == 58.8
