#!/usr/bin/env python3
"""
Tests for Integration Checklist Validator

Run with:
    cd adws
    uv run pytest tests/test_integration_validator.py -v
"""

import pytest
import os
import tempfile
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.integration_validator import (
    validate_integration_checklist,
    ValidationResult,
    ValidationReport,
    _check_api_endpoints_exist,
    _check_ui_components_exist,
    _check_migrations_exist,
    _check_tests_exist,
    _check_routes_registered,
    _check_service_layer_exists,
    _check_component_in_navigation,
    _check_repository_methods_exist,
    _check_docs_updated,
)


@pytest.fixture
def temp_worktree():
    """Create temporary worktree structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create directory structure
        os.makedirs(os.path.join(tmpdir, "app/server/routes"))
        os.makedirs(os.path.join(tmpdir, "app/server/services"))
        os.makedirs(os.path.join(tmpdir, "app/server/repositories"))
        os.makedirs(os.path.join(tmpdir, "app/server/db/migrations"))
        os.makedirs(os.path.join(tmpdir, "app/server/tests"))
        os.makedirs(os.path.join(tmpdir, "app/client/src/components"))
        os.makedirs(os.path.join(tmpdir, "docs"))

        # Create sample files
        with open(os.path.join(tmpdir, "app/server/routes/user_routes.py"), 'w') as f:
            f.write("@app.get('/users')\ndef get_users():\n    pass")

        with open(os.path.join(tmpdir, "app/server/main.py"), 'w') as f:
            f.write("app.include_router(user_router)")

        with open(os.path.join(tmpdir, "app/server/services/user_service.py"), 'w') as f:
            f.write("class UserService:\n    pass")

        with open(os.path.join(tmpdir, "app/server/repositories/user_repository.py"), 'w') as f:
            f.write("class UserRepository:\n    pass")

        with open(os.path.join(tmpdir, "app/client/src/components/UserProfile.tsx"), 'w') as f:
            f.write("export const UserProfile = () => {}")

        with open(os.path.join(tmpdir, "app/client/src/App.tsx"), 'w') as f:
            f.write("import { UserProfile } from './components/UserProfile'")

        with open(os.path.join(tmpdir, "app/server/db/migrations/001_users.sql"), 'w') as f:
            f.write("CREATE TABLE users (id INT);")

        with open(os.path.join(tmpdir, "app/server/tests/test_users.py"), 'w') as f:
            f.write("def test_users(): pass")

        with open(os.path.join(tmpdir, "docs/feature.md"), 'w') as f:
            f.write("# Feature Documentation")

        yield tmpdir


@pytest.fixture
def empty_worktree():
    """Create empty temporary worktree for failure testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create minimal directory structure but no files
        os.makedirs(os.path.join(tmpdir, "app/server"))
        os.makedirs(os.path.join(tmpdir, "app/client/src"))
        yield tmpdir


def test_validate_empty_checklist(temp_worktree):
    """Test validation with empty checklist."""
    checklist = {
        "backend": [],
        "frontend": [],
        "database": [],
        "documentation": [],
        "testing": []
    }

    report = validate_integration_checklist(checklist, temp_worktree)

    assert report.total_items == 0
    assert report.passed_items == 0
    assert report.failed_items == 0


def test_validate_backend_items(temp_worktree):
    """Test backend item validation."""
    checklist = {
        "backend": [
            {
                "description": "API endpoint implemented",
                "required": True,
                "detected_keywords": ["api", "endpoint"]
            },
            {
                "description": "API route registered in route configuration",
                "required": True,
                "detected_keywords": ["route"]
            },
            {
                "description": "Business logic implemented in service layer",
                "required": True,
                "detected_keywords": ["service", "logic"]
            }
        ],
        "frontend": [],
        "database": [],
        "documentation": [],
        "testing": []
    }

    report = validate_integration_checklist(checklist, temp_worktree)

    assert report.total_items == 3
    assert report.passed_items == 3
    assert report.failed_items == 0


def test_validate_frontend_items(temp_worktree):
    """Test frontend item validation."""
    checklist = {
        "backend": [],
        "frontend": [
            {
                "description": "UI component created",
                "required": True,
                "detected_keywords": ["component"]
            },
            {
                "description": "Component added to navigation/routing",
                "required": True,
                "detected_keywords": ["navigation"]
            }
        ],
        "database": [],
        "documentation": [],
        "testing": []
    }

    report = validate_integration_checklist(checklist, temp_worktree)

    assert report.total_items == 2
    assert report.passed_items == 2
    assert report.failed_items == 0


def test_validate_database_items(temp_worktree):
    """Test database item validation."""
    checklist = {
        "backend": [],
        "frontend": [],
        "database": [
            {
                "description": "Database migration created",
                "required": True,
                "detected_keywords": ["migration"]
            },
            {
                "description": "Repository methods implemented",
                "required": True,
                "detected_keywords": ["repository"]
            }
        ],
        "documentation": [],
        "testing": []
    }

    report = validate_integration_checklist(checklist, temp_worktree)

    assert report.total_items == 2
    assert report.passed_items == 2
    assert report.failed_items == 0


def test_validate_documentation_items(temp_worktree):
    """Test documentation item validation."""
    checklist = {
        "backend": [],
        "frontend": [],
        "database": [],
        "documentation": [
            {
                "description": "Feature documentation added",
                "required": True,
                "detected_keywords": ["docs"]
            }
        ],
        "testing": []
    }

    report = validate_integration_checklist(checklist, temp_worktree)

    assert report.total_items == 1
    assert report.passed_items == 1
    assert report.failed_items == 0


def test_validate_testing_items(temp_worktree):
    """Test testing item validation."""
    checklist = {
        "backend": [],
        "frontend": [],
        "database": [],
        "documentation": [],
        "testing": [
            {
                "description": "Unit tests added",
                "required": True,
                "detected_keywords": ["test"]
            }
        ]
    }

    report = validate_integration_checklist(checklist, temp_worktree)

    assert report.total_items == 1
    assert report.passed_items == 1
    assert report.failed_items == 0


def test_validate_missing_backend_items(empty_worktree):
    """Test validation with missing backend files."""
    checklist = {
        "backend": [
            {
                "description": "API endpoint implemented",
                "required": True,
                "detected_keywords": ["api"]
            }
        ],
        "frontend": [],
        "database": [],
        "documentation": [],
        "testing": []
    }

    report = validate_integration_checklist(checklist, empty_worktree)

    assert report.total_items == 1
    assert report.failed_items == 1
    assert report.required_failed == 1


def test_validate_missing_frontend_items(empty_worktree):
    """Test validation with missing frontend files."""
    checklist = {
        "backend": [],
        "frontend": [
            {
                "description": "UI component created",
                "required": True,
                "detected_keywords": ["component"]
            }
        ],
        "database": [],
        "documentation": [],
        "testing": []
    }

    report = validate_integration_checklist(checklist, empty_worktree)

    assert report.total_items == 1
    assert report.failed_items == 1


def test_validate_optional_items(temp_worktree):
    """Test validation with optional items."""
    checklist = {
        "backend": [],
        "frontend": [
            {
                "description": "State management configured (if needed)",
                "required": False,
                "detected_keywords": ["state"]
            }
        ],
        "database": [],
        "documentation": [],
        "testing": []
    }

    report = validate_integration_checklist(checklist, temp_worktree)

    assert report.total_items == 1
    # Optional item should pass even if not validated
    assert report.passed_items == 1


def test_markdown_formatting(temp_worktree):
    """Test markdown report formatting."""
    checklist = {
        "backend": [
            {
                "description": "API endpoint implemented",
                "required": True,
                "detected_keywords": ["api"]
            }
        ],
        "frontend": [],
        "database": [],
        "documentation": [],
        "testing": []
    }

    report = validate_integration_checklist(checklist, temp_worktree)
    markdown = report.to_markdown()

    assert "## ⚠️ Integration Checklist Validation" in markdown
    assert "Status:" in markdown
    assert "items validated" in markdown


def test_markdown_formatting_with_failures(empty_worktree):
    """Test markdown report formatting with failures."""
    checklist = {
        "backend": [
            {
                "description": "API endpoint implemented",
                "required": True,
                "detected_keywords": ["api"]
            }
        ],
        "frontend": [],
        "database": [],
        "documentation": [],
        "testing": []
    }

    report = validate_integration_checklist(checklist, empty_worktree)
    markdown = report.to_markdown()

    assert "## ⚠️ Integration Checklist Validation" in markdown
    assert "### ⚠️ Missing Items" in markdown
    assert "**[REQUIRED]**" in markdown


def test_check_api_endpoints_exist(temp_worktree):
    """Test API endpoint detection."""
    passed, warning, expected, actual = _check_api_endpoints_exist(temp_worktree)

    assert passed is True
    assert warning is None


def test_check_api_endpoints_missing(empty_worktree):
    """Test API endpoint detection with missing endpoints."""
    passed, warning, expected, actual = _check_api_endpoints_exist(empty_worktree)

    assert passed is False
    assert "not found" in warning.lower() or "no api" in warning.lower()


def test_check_routes_registered(temp_worktree):
    """Test route registration detection."""
    passed, warning, expected, actual = _check_routes_registered(temp_worktree)

    assert passed is True
    assert warning is None


def test_check_service_layer_exists(temp_worktree):
    """Test service layer detection."""
    passed, warning, expected, actual = _check_service_layer_exists(temp_worktree)

    assert passed is True
    assert warning is None


def test_check_ui_components_exist(temp_worktree):
    """Test UI component detection."""
    passed, warning, expected, actual = _check_ui_components_exist(temp_worktree)

    assert passed is True
    assert warning is None


def test_check_ui_components_missing(empty_worktree):
    """Test UI component detection with missing components."""
    passed, warning, expected, actual = _check_ui_components_exist(empty_worktree)

    assert passed is False


def test_check_component_in_navigation(temp_worktree):
    """Test component navigation detection."""
    passed, warning, expected, actual = _check_component_in_navigation(temp_worktree)

    assert passed is True
    assert warning is None


def test_check_migrations_exist(temp_worktree):
    """Test migration file detection."""
    passed, warning, expected, actual = _check_migrations_exist(temp_worktree)

    assert passed is True
    assert warning is None


def test_check_migrations_missing(empty_worktree):
    """Test migration file detection with missing migrations."""
    passed, warning, expected, actual = _check_migrations_exist(empty_worktree)

    assert passed is False


def test_check_repository_methods_exist(temp_worktree):
    """Test repository methods detection."""
    passed, warning, expected, actual = _check_repository_methods_exist(temp_worktree)

    assert passed is True
    assert warning is None


def test_check_docs_updated(temp_worktree):
    """Test documentation update detection."""
    passed, warning, expected, actual = _check_docs_updated(temp_worktree)

    assert passed is True
    assert warning is None


def test_check_tests_exist(temp_worktree):
    """Test test file detection."""
    passed, warning, expected, actual = _check_tests_exist(temp_worktree)

    assert passed is True
    assert warning is None


def test_check_tests_missing(empty_worktree):
    """Test test file detection with missing tests."""
    passed, warning, expected, actual = _check_tests_exist(empty_worktree)

    assert passed is False


def test_full_stack_validation(temp_worktree):
    """Test comprehensive validation with all categories."""
    checklist = {
        "backend": [
            {
                "description": "API endpoint implemented",
                "required": True,
                "detected_keywords": ["api"]
            },
            {
                "description": "API route registered in route configuration",
                "required": True,
                "detected_keywords": ["route"]
            }
        ],
        "frontend": [
            {
                "description": "UI component created",
                "required": True,
                "detected_keywords": ["component"]
            },
            {
                "description": "Component added to navigation/routing",
                "required": True,
                "detected_keywords": ["navigation"]
            }
        ],
        "database": [
            {
                "description": "Database migration created",
                "required": True,
                "detected_keywords": ["migration"]
            }
        ],
        "documentation": [
            {
                "description": "Feature documentation added",
                "required": True,
                "detected_keywords": ["docs"]
            }
        ],
        "testing": [
            {
                "description": "Unit tests added",
                "required": True,
                "detected_keywords": ["test"]
            }
        ]
    }

    report = validate_integration_checklist(checklist, temp_worktree)

    assert report.total_items == 7
    assert report.passed_items == 7
    assert report.failed_items == 0
    assert report.required_failed == 0


def test_partial_validation(temp_worktree):
    """Test validation with mix of passing and failing items."""
    # Remove some files to cause failures
    os.remove(os.path.join(temp_worktree, "app/server/routes/user_routes.py"))

    checklist = {
        "backend": [
            {
                "description": "API endpoint implemented",
                "required": True,
                "detected_keywords": ["api"]
            }
        ],
        "frontend": [
            {
                "description": "UI component created",
                "required": True,
                "detected_keywords": ["component"]
            }
        ],
        "database": [],
        "documentation": [],
        "testing": []
    }

    report = validate_integration_checklist(checklist, temp_worktree)

    assert report.total_items == 2
    # Backend should fail (no API endpoints), frontend should pass
    assert report.failed_items == 1
    assert report.passed_items == 1


def test_validation_result_dataclass():
    """Test ValidationResult dataclass creation."""
    result = ValidationResult(
        item_description="Test item",
        category="backend",
        required=True,
        passed=False,
        warning_message="Test warning",
        expected="Expected value",
        actual="Actual value"
    )

    assert result.item_description == "Test item"
    assert result.category == "backend"
    assert result.required is True
    assert result.passed is False
    assert result.warning_message == "Test warning"


def test_validation_report_dataclass():
    """Test ValidationReport dataclass creation."""
    results = [
        ValidationResult("Item 1", "backend", True, True),
        ValidationResult("Item 2", "frontend", False, False)
    ]

    report = ValidationReport(
        total_items=2,
        passed_items=1,
        failed_items=1,
        required_failed=0,
        optional_failed=1,
        results=results
    )

    assert report.total_items == 2
    assert report.passed_items == 1
    assert report.failed_items == 1
