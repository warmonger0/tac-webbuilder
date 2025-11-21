"""Pytest configuration for regression tests."""

import pytest
import sqlite3
from pathlib import Path


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
        with open(schema_path, 'r') as f:
            schema = f.read()
            conn.executescript(schema)

    yield conn
    conn.close()
