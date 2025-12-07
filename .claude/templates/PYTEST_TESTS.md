# Template: Pytest Tests

## File Location
- Service tests: `app/server/tests/services/test_<service>_service.py`
- Script tests: `scripts/tests/test_<script>.py`
- Integration tests: `app/server/tests/integration/test_<feature>.py`

## Standard Structure

```python
#!/usr/bin/env python3
"""
Tests for <Component Name>

Run with:
    cd <directory>
    pytest tests/test_<name>.py -v
    pytest tests/test_<name>.py -v -k "test_specific"
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from <module> import <ClassToTest>


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_path = temp_file.name
    temp_file.close()

    # Create schema
    conn = sqlite3.connect(temp_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE <table_name> (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column1 TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

    yield temp_path

    # Cleanup
    Path(temp_path).unlink()


@pytest.fixture
def service(temp_db, monkeypatch):
    """Create service instance with temp database."""
    def mock_get_connection():
        return sqlite3.connect(temp_db)

    monkeypatch.setattr(
        '<module>.get_connection',
        mock_get_connection
    )

    return <ClassToTest>()


def test_basic_functionality(service):
    """Test basic operation."""
    result = service.basic_method()
    assert result is not None


def test_with_mock_data(service, temp_db):
    """Test with pre-populated data."""
    # Insert test data
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO <table> (column1) VALUES (?)",
        ('test_value',)
    )
    conn.commit()
    conn.close()

    # Test
    result = service.get_all()
    assert len(result) == 1
    assert result[0].column1 == 'test_value'


def test_edge_case_empty(service):
    """Test with empty dataset."""
    result = service.get_all()
    assert len(result) == 0


def test_error_handling(service):
    """Test error handling."""
    with pytest.raises(ValueError):
        service.invalid_operation()


@patch('<module>.external_dependency')
def test_with_mock(mock_external, service):
    """Test with mocked external dependency."""
    mock_external.return_value = {'key': 'value'}

    result = service.method_using_external()
    assert result is not None
    mock_external.assert_called_once()
```

## Running Tests

```bash
# Run all tests
pytest tests/test_<name>.py -v

# Run specific test
pytest tests/test_<name>.py::test_basic_functionality -v

# Run with coverage
pytest tests/test_<name>.py --cov=<module> --cov-report=html

# Run with verbose output
pytest tests/test_<name>.py -vv -s
```

## Common Fixtures

**Temp Directory:**
```python
@pytest.fixture
def temp_dir():
    import tempfile
    import shutil
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)
```

**Mock Environment Variables:**
```python
@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv('DB_TYPE', 'sqlite')
    monkeypatch.setenv('API_KEY', 'test-key')
```

**Mock Time:**
```python
@pytest.fixture
def freeze_time():
    from datetime import datetime
    fixed_time = datetime(2025, 1, 1, 12, 0, 0)
    with patch('module.datetime') as mock_dt:
        mock_dt.now.return_value = fixed_time
        yield mock_dt
```

## Test Patterns

**Parametrize Multiple Inputs:**
```python
@pytest.mark.parametrize("input_val,expected", [
    (1, 'one'),
    (2, 'two'),
    (3, 'three'),
])
def test_conversion(input_val, expected):
    assert convert(input_val) == expected
```

**Test Exception Messages:**
```python
def test_specific_error_message():
    with pytest.raises(ValueError, match="Invalid input"):
        service.validate('bad_input')
```

**Test Logging:**
```python
def test_logging_output(caplog):
    import logging
    with caplog.at_level(logging.INFO):
        service.operation()
    assert "Expected log message" in caplog.text
```

**Test File I/O:**
```python
def test_file_creation(temp_dir):
    output_file = temp_dir / "output.txt"
    service.write_file(output_file)

    assert output_file.exists()
    assert output_file.read_text() == "expected content"
```

## Assertions

**Basic:**
```python
assert result == expected
assert result is not None
assert len(items) == 5
assert 'key' in dictionary
```

**Approximate:**
```python
assert result == pytest.approx(3.14, rel=0.01)  # Within 1%
```

**Collections:**
```python
assert set(result) == {'a', 'b', 'c'}
assert all(x > 0 for x in numbers)
assert any(x == 'target' for x in items)
```

**Type Checking:**
```python
assert isinstance(result, list)
assert type(result) == dict
```

## Mocking Patterns

**Mock Function Return:**
```python
@patch('module.function')
def test_with_mock(mock_func):
    mock_func.return_value = 'mocked'
    result = service.use_function()
    assert result == 'mocked'
```

**Mock Class:**
```python
@patch('module.ExternalClass')
def test_with_class_mock(MockClass):
    mock_instance = MockClass.return_value
    mock_instance.method.return_value = 'result'

    service = ServiceUsingExternal()
    result = service.operation()

    MockClass.assert_called_once()
    mock_instance.method.assert_called()
```

**Mock Side Effect:**
```python
mock.side_effect = [result1, result2, Exception("error")]
# First call returns result1, second returns result2, third raises exception
```

## Database Test Patterns

**Setup/Teardown:**
```python
def setup_test_data(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO table VALUES (...)")
    conn.commit()
    conn.close()

@pytest.fixture
def populated_db(temp_db):
    setup_test_data(temp_db)
    yield temp_db
```

**Transaction Rollback:**
```python
@pytest.fixture
def db_session():
    conn = get_connection()
    conn.execute("BEGIN")
    yield conn
    conn.execute("ROLLBACK")
    conn.close()
```
