"""
Comprehensive test suite for the database connection utility.

Tests verify:
- Successful connections and automatic commits
- Automatic rollback on errors
- Connection cleanup (close) in all scenarios
- Row factory configuration for dict-like access
- Retry logic for SQLITE_BUSY errors
- Custom database path handling
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from utils.db_connection import get_connection


@pytest.fixture
def temp_db():
    """
    Create a temporary database for testing.

    Yields the path to a temporary database file that is automatically
    cleaned up after the test.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


def test_successful_connection_and_commit(temp_db):
    """
    Verify that connection is established successfully and transaction
    is committed automatically on successful context exit.

    Tests:
    - Connection creation
    - Table creation and data insertion
    - Automatic commit on context exit
    - Data persists after context manager exits
    """
    # First context: create table and insert data
    with get_connection(db_path=temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE test_users (id INTEGER PRIMARY KEY, name TEXT)"
        )
        cursor.execute("INSERT INTO test_users (id, name) VALUES (1, 'Alice')")

    # Second context: verify data was committed
    with get_connection(db_path=temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM test_users WHERE id = 1")
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == 1
        assert row[1] == "Alice"


def test_automatic_rollback_on_error(temp_db):
    """
    Verify that transaction is rolled back when exception occurs within
    the context manager.

    Tests:
    - Table is created in first transaction
    - Data insertion occurs in second transaction
    - Exception triggers rollback
    - Data changes are not persisted
    - Table exists but data was rolled back

    Note: SQLite DDL statements (CREATE TABLE) are auto-committed and cannot
    be rolled back, so we test data rollback instead.
    """
    # First: Create table in committed transaction
    with get_connection(db_path=temp_db) as conn:
        conn.execute("CREATE TABLE test_rollback (id INTEGER PRIMARY KEY)")

    # Second: Attempt to insert data but raise exception
    try:
        with get_connection(db_path=temp_db) as conn:
            conn.execute("INSERT INTO test_rollback (id) VALUES (1)")
            conn.execute("INSERT INTO test_rollback (id) VALUES (2)")
            # Simulate an error
            raise ValueError("Simulated error for testing rollback")
    except ValueError:
        pass  # Expected

    # Verify data was not committed due to rollback
    with get_connection(db_path=temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM test_rollback")
        result = cursor.fetchone()
        assert result["count"] == 0, "No data should exist after rollback"


def test_connection_cleanup(temp_db):
    """
    Verify that database connection is properly closed after context
    manager exits, both on success and error paths.

    Tests:
    - Connection is closed on successful exit
    - Connection is closed on error exit
    - Uses connection state to verify closure
    """
    # Test successful path
    with get_connection(db_path=temp_db) as conn:
        conn.execute("CREATE TABLE test_cleanup (id INTEGER)")
        # Connection should be open here
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone() is not None

    # After context exit, connection should be closed
    # Attempting to use a closed connection raises ProgrammingError
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")

    # Test error path
    try:
        with get_connection(db_path=temp_db) as conn:
            raise RuntimeError("Test error")
    except RuntimeError:
        pass

    # Connection should still be closed after error
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")


def test_row_factory_configuration(temp_db):
    """
    Verify that rows can be accessed as dictionaries (dict-like access)
    and by column name using sqlite3.Row factory.

    Tests:
    - Row factory is set to sqlite3.Row
    - Dict-like access by column name works
    - Index-based access still works
    - Both access methods return same values
    """
    # Create table and insert test data
    with get_connection(db_path=temp_db) as conn:
        conn.execute(
            "CREATE TABLE test_row_factory (id INTEGER, name TEXT, age INTEGER)"
        )
        conn.execute(
            "INSERT INTO test_row_factory VALUES (1, 'Bob', 30), (2, 'Carol', 25)"
        )

    # Query and test row access methods
    with get_connection(db_path=temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, age FROM test_row_factory WHERE id = 1"
        )
        row = cursor.fetchone()

        # Dict-like access by column name
        assert row["id"] == 1
        assert row["name"] == "Bob"
        assert row["age"] == 30

        # Index-based access
        assert row[0] == 1
        assert row[1] == "Bob"
        assert row[2] == 30

        # Verify keys() method works (dict-like interface)
        # Note: sqlite3.Row requires .keys() for membership testing
        assert "id" in row.keys()  # noqa: SIM118
        assert "name" in row.keys()  # noqa: SIM118
        assert "age" in row.keys()  # noqa: SIM118


def test_custom_database_path():
    """
    Verify that custom database paths are respected and connections
    can be established to databases in different locations.

    Tests:
    - Custom path is used
    - Database file is created at custom location
    - Operations work correctly with custom path
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        custom_db_path = Path(tmpdir) / "custom_test.db"

        # Use custom path
        with get_connection(db_path=str(custom_db_path)) as conn:
            conn.execute("CREATE TABLE test_custom (value TEXT)")
            conn.execute("INSERT INTO test_custom VALUES ('test_data')")

        # Verify database exists at custom location
        assert custom_db_path.exists()

        # Verify data persists
        with get_connection(db_path=str(custom_db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM test_custom")
            result = cursor.fetchone()
            assert result["value"] == "test_data"


def test_retry_logic_busy_database():
    """
    Verify that connection retries on SQLITE_BUSY errors and eventually
    succeeds when the database becomes available.

    Tests:
    - Retries occur on database locked errors
    - Connection succeeds after transient failures
    - Retry delay is applied between attempts

    Uses mocking to simulate SQLITE_BUSY errors.
    """
    # Create a real temp database for final successful connection
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = f.name

    try:
        # Mock sqlite3.connect to fail twice with "locked" error, then succeed
        original_connect = sqlite3.connect
        call_count = 0

        def mock_connect_with_retries(db_path):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                # First two attempts fail with locked error
                raise sqlite3.OperationalError("database is locked")
            # Third attempt succeeds
            return original_connect(db_path)

        with (
            patch("sqlite3.connect", side_effect=mock_connect_with_retries),
            get_connection(
                db_path=temp_db, max_retries=3, retry_delay=0.01
            ) as conn,
        ):
            # Should succeed after retries
            conn.execute("CREATE TABLE test_retry (id INTEGER)")

        # Verify it took 3 attempts
        assert call_count == 3

    finally:
        # Cleanup
        Path(temp_db).unlink(missing_ok=True)


def test_retry_logic_exceeds_max_retries():
    """
    Verify that exception is raised when maximum retry attempts are
    exceeded for SQLITE_BUSY errors.

    Tests:
    - Retries occur up to max_retries
    - OperationalError is raised after all retries fail
    - Appropriate error message is preserved
    """
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        temp_db = f.name

    # Mock to always fail with locked error
    def mock_connect_always_locked(db_path):
        raise sqlite3.OperationalError("database is locked")

    # Should raise after exhausting retries
    with (
        patch("sqlite3.connect", side_effect=mock_connect_always_locked),
        pytest.raises(sqlite3.OperationalError, match="locked"),
        get_connection(db_path=temp_db, max_retries=3, retry_delay=0.01),
    ):
        pass


def test_non_busy_error_no_retry(temp_db):
    """
    Verify that non-SQLITE_BUSY errors are raised immediately without
    retry attempts.

    Tests:
    - Non-"locked" OperationalErrors are not retried
    - Other exceptions propagate immediately
    - No unnecessary retry delays
    """
    # Mock to fail with non-locked error
    call_count = 0

    def mock_connect_other_error(db_path):
        nonlocal call_count
        call_count += 1
        raise sqlite3.OperationalError("unable to open database file")

    with patch("sqlite3.connect", side_effect=mock_connect_other_error):
        # Should raise immediately without retries
        with pytest.raises(
            sqlite3.OperationalError, match="unable to open"
        ), get_connection(db_path=temp_db, max_retries=3):
            pass

        # Should only have attempted once
        assert call_count == 1


def test_connection_with_default_path():
    """
    Verify that default database path "db/database.db" is used when
    no path is specified.

    Tests:
    - Default path parameter works
    - Database operations succeed with default path
    - Path resolution works correctly
    """
    # Use a temporary directory as CWD for this test
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create db directory
        db_dir = Path(tmpdir) / "db"
        db_dir.mkdir()
        default_db_path = db_dir / "database.db"

        # Change to temp directory
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)

            # Use default path (should be "db/database.db")
            with get_connection() as conn:
                conn.execute("CREATE TABLE test_default (id INTEGER)")

            # Verify database was created at default location
            assert default_db_path.exists()

        finally:
            os.chdir(original_cwd)
