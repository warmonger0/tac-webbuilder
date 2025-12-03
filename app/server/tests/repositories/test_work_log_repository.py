"""
Unit tests for WorkLogRepository.

Tests database operations for work log entries including:
- Creating entries
- Retrieving entries with pagination
- Filtering by session
- Deleting entries
- Database-agnostic placeholder handling
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from core.models.work_log import WorkLogEntry, WorkLogEntryCreate
from repositories.work_log_repository import WorkLogRepository


@pytest.fixture
def mock_adapter():
    """Create a mock database adapter."""
    adapter = MagicMock()
    adapter.placeholder.return_value = "?"
    adapter.get_db_type.return_value = "sqlite"
    return adapter


@pytest.fixture
def repository(mock_adapter):
    """Create a WorkLogRepository with mocked adapter."""
    with patch('repositories.work_log_repository.get_database_adapter', return_value=mock_adapter):
        return WorkLogRepository()


class TestWorkLogRepositoryCreate:
    """Test work log entry creation."""

    def test_create_entry_success_sqlite(self, repository, mock_adapter):
        """Test creating a work log entry with SQLite."""
        # Setup
        entry_create = WorkLogEntryCreate(
            session_id="test-session-123",
            summary="Implemented observability system",
            issue_number=42,
            workflow_id="adw-test",
            tags=["observability", "backend"]
        )

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_cursor.fetchone.return_value = MagicMock(
            __getitem__=lambda self, key: {
                0: 1,
                1: datetime(2025, 12, 2, 10, 30),
                2: datetime(2025, 12, 2, 10, 30)
            }[key]
        )
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        # Execute
        result = repository.create_entry(entry_create)

        # Assert
        assert isinstance(result, WorkLogEntry)
        assert result.id == 1
        assert result.session_id == "test-session-123"
        assert result.summary == "Implemented observability system"
        assert result.issue_number == 42
        assert result.workflow_id == "adw-test"
        assert result.tags == ["observability", "backend"]

        # Verify SQL used placeholder
        call_args = mock_cursor.execute.call_args_list[0]
        assert "?" in call_args[0][0]  # SQL query should have ? placeholders

    def test_create_entry_validates_summary_length(self, repository):
        """Test that summary length is validated at Pydantic level."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="at most 280 characters"):
            entry_create = WorkLogEntryCreate(
                session_id="test-session",
                summary="x" * 281,  # Over 280 character limit
                tags=[]
            )

    def test_create_entry_handles_empty_tags(self, repository, mock_adapter):
        """Test creating entry with empty tags list."""
        entry_create = WorkLogEntryCreate(
            session_id="test-session",
            summary="Test summary",
            tags=[]
        )

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_cursor.fetchone.return_value = MagicMock(
            __getitem__=lambda self, key: {
                0: 1,
                1: datetime.now(),
                2: datetime.now()
            }[key]
        )
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        result = repository.create_entry(entry_create)

        assert result.tags == []


class TestWorkLogRepositoryRetrieval:
    """Test work log entry retrieval."""

    def test_get_all_with_pagination(self, repository, mock_adapter):
        """Test retrieving work logs with pagination."""
        # Setup
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            0: 1,
            1: datetime(2025, 12, 2, 10, 30),
            2: "session-123",
            3: "Test summary",
            4: None,
            5: 42,
            6: "adw-123",
            7: json.dumps(["test"]),
            8: datetime(2025, 12, 2, 10, 30)
        }[key]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [mock_row]
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        # Execute
        entries = repository.get_all(limit=10, offset=0)

        # Assert
        assert len(entries) == 1
        assert entries[0].id == 1
        assert entries[0].summary == "Test summary"
        assert entries[0].tags == ["test"]

        # Verify SQL used placeholders
        call_args = mock_cursor.execute.call_args
        assert "?" in call_args[0][0]  # Should use ? placeholders
        assert call_args[0][1] == (10, 0)  # Check parameters

    def test_get_by_session(self, repository, mock_adapter):
        """Test retrieving work logs by session ID."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        entries = repository.get_by_session("test-session")

        assert isinstance(entries, list)
        # Verify SQL used placeholder
        call_args = mock_cursor.execute.call_args
        assert "?" in call_args[0][0]
        assert call_args[0][1] == ("test-session",)

    def test_get_count(self, repository, mock_adapter):
        """Test getting count of work log entries."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Mock sqlite3.Row object with named column access
        mock_row = {'count': 42}
        mock_cursor.fetchone.return_value = mock_row
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        count = repository.get_count()

        assert count == 42
        # Verify query uses named column
        call_args = mock_cursor.execute.call_args
        assert "AS count" in call_args[0][0]


class TestWorkLogRepositoryDelete:
    """Test work log entry deletion."""

    def test_delete_entry_success(self, repository, mock_adapter):
        """Test deleting an existing entry."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        result = repository.delete_entry(1)

        assert result is True
        # Verify SQL used placeholder
        call_args = mock_cursor.execute.call_args
        assert "?" in call_args[0][0]
        assert call_args[0][1] == (1,)

    def test_delete_entry_not_found(self, repository, mock_adapter):
        """Test deleting a non-existent entry."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        result = repository.delete_entry(999)

        assert result is False


class TestDatabaseAgnosticPlaceholders:
    """Test that repository uses database-agnostic placeholders."""

    def test_uses_adapter_placeholder(self, repository, mock_adapter):
        """Test that repository calls adapter.placeholder() for SQL."""
        mock_adapter.placeholder.return_value = "?"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

        repository.get_all(limit=5, offset=0)

        # Verify placeholder was called
        assert mock_adapter.placeholder.called

    def test_supports_postgresql_placeholders(self, mock_adapter):
        """Test that repository can work with PostgreSQL placeholders."""
        mock_adapter.placeholder.return_value = "%s"
        mock_adapter.get_db_type.return_value = "postgresql"

        with patch('repositories.work_log_repository.get_database_adapter', return_value=mock_adapter):
            repository = WorkLogRepository()

            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

            repository.get_all(limit=5, offset=0)

            # Verify SQL was built with %s placeholders
            call_args = mock_cursor.execute.call_args
            assert "%s" in call_args[0][0]
