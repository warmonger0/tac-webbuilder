"""
Pytest configuration and shared fixtures for ADW module tests.

This file provides:
- Pytest configuration (markers, plugins setup)
- Shared fixtures for test data
- Mock helpers for common operations
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock
import tempfile
import shutil


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (uses real subprocesses)"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "external: marks tests as requiring external ADW workflow scripts"
    )


# ============================================================================
# Path Fixtures
# ============================================================================


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def project_structure(temp_directory):
    """Create a realistic project structure."""
    structure = {
        "app": {
            "server": {},
            "client": {},
        },
        "tests": {},
        "src": {},
    }

    def create_structure(base_path, structure_dict):
        for key, value in structure_dict.items():
            path = base_path / key
            if isinstance(value, dict):
                path.mkdir(exist_ok=True)
                create_structure(path, value)

    create_structure(temp_directory, structure)
    return temp_directory


# ============================================================================
# Report Fixtures
# ============================================================================


@pytest.fixture
def minimal_pytest_report():
    """Minimal pytest report with no tests."""
    return {
        "summary": {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
        },
        "duration": 0.0,
        "tests": [],
    }


@pytest.fixture
def complex_pytest_report():
    """Complex pytest report with various test outcomes."""
    return {
        "summary": {
            "total": 20,
            "passed": 15,
            "failed": 3,
            "skipped": 2,
        },
        "duration": 12.5,
        "tests": [
            {
                "nodeid": "tests/test_auth.py::TestAuth::test_login_success",
                "outcome": "passed",
                "call": {"longrepr": ""},
            },
            {
                "nodeid": "tests/test_auth.py::TestAuth::test_login_invalid",
                "outcome": "failed",
                "call": {
                    "longrepr": """tests/test_auth.py:45: AssertionError
>   assert response.status_code == 401
E   AssertionError: assert 200 == 401"""
                },
            },
            {
                "nodeid": "tests/test_auth.py::test_password_hash",
                "outcome": "passed",
                "call": {"longrepr": ""},
            },
            {
                "nodeid": "tests/test_db.py::test_connection",
                "outcome": "error",
                "call": {
                    "longrepr": """tests/test_db.py:20: RuntimeError
E   RuntimeError: Could not connect to database"""
                },
            },
            {
                "nodeid": "tests/test_utils.py::test_parse_json",
                "outcome": "failed",
                "call": {
                    "longrepr": """tests/test_utils.py:60: ValueError
>   assert parse_json(invalid) == expected
E   ValueError: Invalid JSON format"""
                },
            },
        ] + [
            {
                "nodeid": f"tests/test_module.py::test_{i}",
                "outcome": "passed",
                "call": {"longrepr": ""},
            }
            for i in range(10, 20)
        ],
    }


@pytest.fixture
def minimal_vitest_report():
    """Minimal vitest report."""
    return {
        "numTotalTests": 0,
        "numPassedTests": 0,
        "numFailedTests": 0,
        "numPendingTests": 0,
        "testResults": [],
    }


@pytest.fixture
def complex_vitest_report():
    """Complex vitest report with various test outcomes."""
    return {
        "numTotalTests": 12,
        "numPassedTests": 9,
        "numFailedTests": 2,
        "numPendingTests": 1,
        "testResults": [
            {
                "name": "tests/Button.test.tsx",
                "assertionResults": [
                    {
                        "title": "renders button",
                        "status": "passed",
                        "failureMessages": [],
                    },
                    {
                        "title": "handles click",
                        "status": "passed",
                        "failureMessages": [],
                    },
                    {
                        "title": "applies custom className",
                        "status": "failed",
                        "location": {"line": 35},
                        "failureMessages": [
                            "AssertionError: expected 'btn' to include 'custom-class'"
                        ],
                    },
                ],
                "perfStats": {"runtime": 2500},
            },
            {
                "name": "tests/Form.test.tsx",
                "assertionResults": [
                    {
                        "title": "renders form inputs",
                        "status": "passed",
                        "failureMessages": [],
                    },
                    {
                        "title": "validates email",
                        "status": "failed",
                        "location": {"line": 52},
                        "failureMessages": [
                            "TypeError: Cannot read property 'value' of null"
                        ],
                    },
                    {
                        "title": "submits data",
                        "status": "pending",
                        "failureMessages": [],
                    },
                ],
                "perfStats": {"runtime": 1800},
            },
            {
                "name": "tests/utils.test.ts",
                "assertionResults": [
                    {
                        "title": "formats date",
                        "status": "passed",
                        "failureMessages": [],
                    },
                    {
                        "title": "parses JSON",
                        "status": "passed",
                        "failureMessages": [],
                    },
                    {
                        "title": "validates email",
                        "status": "passed",
                        "failureMessages": [],
                    },
                    {
                        "title": "sanitizes HTML",
                        "status": "passed",
                        "failureMessages": [],
                    },
                ],
                "perfStats": {"runtime": 1200},
            },
        ],
    }


@pytest.fixture
def comprehensive_coverage_report():
    """Comprehensive coverage report."""
    return {
        "totals": {
            "num_statements": 1000,
            "covered_lines": 850,
            "percent_covered": 85.0,
        },
        "files": {
            "src/auth.py": {
                "summary": {"percent_covered": 95},
            },
            "src/database.py": {
                "summary": {"percent_covered": 75},
            },
            "src/utils.py": {
                "summary": {"percent_covered": 100},
            },
            "src/legacy/old_code.py": {
                "summary": {"percent_covered": 0},
            },
            "src/legacy/deprecated.py": {
                "summary": {"percent_covered": 0},
            },
            "src/migrations/migration_001.py": {
                "summary": {"percent_covered": 50},
            },
        },
    }


# ============================================================================
# Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_subprocess_run():
    """Create a reusable mock for subprocess.run."""
    from unittest.mock import Mock
    return Mock()


@pytest.fixture
def mock_file_operations(mocker):
    """Mock file I/O operations."""
    mock_open = mocker.patch("builtins.open", create=True)
    mock_exists = mocker.patch("pathlib.Path.exists")
    return {
        "open": mock_open,
        "exists": mock_exists,
    }


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_test_failure():
    """Sample test failure object."""
    from adw_modules.test_runner import TestFailure

    return TestFailure(
        test_name="tests/test_module.py::test_something",
        file="tests/test_module.py",
        line=42,
        error_type="AssertionError",
        error_message="assert 1 == 2",
        stack_trace="""tests/test_module.py:42: AssertionError
>   assert 1 == 2
E   AssertionError: assert 1 == 2""",
    )


@pytest.fixture
def sample_test_summary():
    """Sample test summary object."""
    from adw_modules.test_runner import TestSummary

    return TestSummary(
        total=10,
        passed=8,
        failed=2,
        skipped=0,
        duration_seconds=5.23,
    )


@pytest.fixture
def sample_coverage():
    """Sample coverage object."""
    from adw_modules.test_runner import Coverage

    return Coverage(
        percentage=85.5,
        lines_covered=1710,
        lines_total=2000,
        missing_files=["src/legacy.py"],
    )


@pytest.fixture
def sample_test_result(sample_test_summary, sample_coverage, sample_test_failure):
    """Sample test result object."""
    from adw_modules.test_runner import TestResult

    return TestResult(
        success=False,
        summary=sample_test_summary,
        failures=[sample_test_failure],
        coverage=sample_coverage,
        next_steps=[
            "Fix test failure in tests/test_module.py:42 - AssertionError",
            "Verify all 2 test failures are resolved",
        ],
    )


# ============================================================================
# Markers and Configuration
# ============================================================================


@pytest.fixture
def unit_test_marker():
    """Marker for unit tests."""
    return pytest.mark.unit


@pytest.fixture
def integration_test_marker():
    """Marker for integration tests."""
    return pytest.mark.integration


@pytest.fixture
def slow_test_marker():
    """Marker for slow tests."""
    return pytest.mark.slow


# ============================================================================
# Integration Test Fixtures (for external workflow tests)
# ============================================================================


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory (tac-webbuilder)."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def temp_worktree(tmp_path: Path, project_root: Path) -> Path:
    """
    Create a mock worktree structure for integration testing.

    This simulates a git worktree with the necessary project structure
    for running tests and builds in isolation.
    """
    worktree_path = tmp_path / "test_worktree"
    worktree_path.mkdir(exist_ok=True)

    # Create minimal project structure
    (worktree_path / "app").mkdir(exist_ok=True)
    (worktree_path / "app" / "server").mkdir(exist_ok=True)
    (worktree_path / "app" / "client").mkdir(exist_ok=True)

    # Create minimal pytest structure
    server_path = worktree_path / "app" / "server"
    (server_path / "core").mkdir(exist_ok=True)
    (server_path / "routers").mkdir(exist_ok=True)
    (server_path / "tests").mkdir(exist_ok=True)

    # Create a simple passing test
    test_file = server_path / "tests" / "test_sample.py"
    test_file.write_text("""
import pytest

def test_sample_passing():
    '''Simple passing test for integration testing.'''
    assert True

def test_another_passing():
    '''Another passing test.'''
    assert 1 + 1 == 2
""")

    # Create a simple failing test (for error scenario testing)
    failing_test_file = server_path / "tests" / "test_failing.py"
    failing_test_file.write_text("""
import pytest

def test_sample_failing():
    '''Simple failing test for error scenarios.'''
    assert False, "Expected failure for testing"
""")

    # Create minimal package files
    (server_path / "core" / "__init__.py").write_text("")
    (server_path / "routers" / "__init__.py").write_text("")
    (server_path / "tests" / "__init__.py").write_text("")

    # Create pytest.ini
    pytest_ini = server_path / "pytest.ini"
    pytest_ini.write_text("""[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
""")

    # Create minimal TypeScript files for build testing
    client_path = worktree_path / "app" / "client"

    # Create tsconfig.json
    import json as json_module
    tsconfig = client_path / "tsconfig.json"
    tsconfig.write_text(json_module.dumps({
        "compilerOptions": {
            "target": "ES2020",
            "module": "ESNext",
            "lib": ["ES2020", "DOM"],
            "strict": True,
            "noEmit": True
        },
        "include": ["src/**/*"]
    }, indent=2))

    # Create minimal TypeScript file
    (client_path / "src").mkdir(exist_ok=True)
    ts_file = client_path / "src" / "sample.ts"
    ts_file.write_text("""
export function greet(name: string): string {
    return `Hello, ${name}!`;
}
""")

    # Create TypeScript file with type error (for error testing)
    ts_error_file = client_path / "src" / "error.ts"
    ts_error_file.write_text("""
export function badFunction(): number {
    return "not a number";  // Type error
}
""")

    # Create package.json
    package_json = client_path / "package.json"
    package_json.write_text(json_module.dumps({
        "name": "test-client",
        "version": "1.0.0",
        "scripts": {
            "typecheck": "tsc --noEmit",
            "build": "echo 'Build would run here'"
        },
        "devDependencies": {
            "typescript": "^5.0.0"
        }
    }, indent=2))

    return worktree_path


@pytest.fixture
def adw_state_fixture(tmp_path: Path, temp_worktree: Path, project_root: Path):
    """
    Create a sample ADW state with worktree path configured.

    This simulates the state after adw_plan_iso.py has created a worktree.
    Automatically cleans up after test execution.
    """
    import json as json_module
    from adw_modules.state import ADWState
    from adw_modules.data_types import ADWStateData

    adw_id = "TEST1234"

    # Create agents directory structure
    agents_dir = project_root / "agents" / adw_id
    agents_dir.mkdir(parents=True, exist_ok=True)

    # Create and save state
    state = ADWState(adw_id)
    state.data.update({
        "adw_id": adw_id,
        "issue_number": "42",
        "branch_name": "feature/test-branch",
        "plan_file": f"agents/{adw_id}/plan.md",
        "issue_class": "/feature",
        "worktree_path": str(temp_worktree),
        "backend_port": 8765,
        "frontend_port": 5173,
        "model_set": "base",
        "all_adws": [adw_id]
    })

    # Save state to file
    state_path = state.get_state_path()
    os.makedirs(os.path.dirname(state_path), exist_ok=True)

    state_data = ADWStateData(
        adw_id=state.data["adw_id"],
        issue_number=state.data["issue_number"],
        branch_name=state.data["branch_name"],
        plan_file=state.data["plan_file"],
        issue_class=state.data["issue_class"],
        worktree_path=state.data["worktree_path"],
        backend_port=state.data["backend_port"],
        frontend_port=state.data["frontend_port"],
        model_set=state.data["model_set"],
        all_adws=state.data["all_adws"]
    )

    with open(state_path, "w") as f:
        json_module.dump(state_data.model_dump(), f, indent=2)

    yield state

    # Cleanup
    import shutil
    if agents_dir.exists():
        shutil.rmtree(agents_dir)


@pytest.fixture
def sample_test_results():
    """Sample test results for validation."""
    return {
        "success": True,
        "summary": {
            "total": 10,
            "passed": 10,
            "failed": 0,
            "skipped": 0,
            "duration_seconds": 2.5
        },
        "failures": [],
        "coverage": {
            "percentage": 85.0,
            "lines_covered": 170,
            "lines_total": 200,
            "missing_files": []
        },
        "next_steps": ["All tests passed!"]
    }


@pytest.fixture
def sample_build_results():
    """Sample build results for validation."""
    return {
        "success": True,
        "summary": {
            "total_errors": 0,
            "type_errors": 0,
            "build_errors": 0,
            "warnings": 0,
            "duration_seconds": 1.8
        },
        "errors": [],
        "next_steps": ["All checks passed!"]
    }


@pytest.fixture
def cleanup_test_adw_states(project_root: Path):
    """
    Cleanup test ADW states after test execution.

    Use this fixture when your test creates ADW state files that need cleanup.
    Returns a function to register ADW IDs for cleanup.
    """
    created_adw_ids = []

    def register_adw_id(adw_id: str):
        """Register an ADW ID for cleanup."""
        created_adw_ids.append(adw_id)

    yield register_adw_id

    # Cleanup
    import shutil
    for adw_id in created_adw_ids:
        agents_dir = project_root / "agents" / adw_id
        if agents_dir.exists():
            shutil.rmtree(agents_dir)
