"""Pytest configuration for regression tests."""

import sqlite3
import sys
from pathlib import Path

import pytest

# ============================================================================
# Python Path Setup for Regression Tests
# ============================================================================

# Ensure app/server directory is in Python path
server_root = Path(__file__).parent.parent.parent
if str(server_root) not in sys.path:
    sys.path.insert(0, str(server_root))


@pytest.fixture
def db_connection():
    """Provide a database connection for regression tests."""
    db_path = Path(__file__).parent.parent.parent / "db" / "tac_webbuilder.db"
    conn = sqlite3.connect(str(db_path))
    yield conn
    conn.close()


@pytest.fixture
def clean_test_db(tmp_path):
    """Provide a clean test database."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))

    # Initialize schema from schema.sql
    schema_path = Path(__file__).parent.parent.parent / "db" / "schema.sql"

    if schema_path.exists():
        with open(schema_path) as f:
            schema = f.read()
            conn.executescript(schema)

    yield conn
    conn.close()
