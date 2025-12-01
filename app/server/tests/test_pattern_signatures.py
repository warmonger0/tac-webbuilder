"""
Unit tests for pattern signature generation.
"""

import pytest
from core.pattern_signatures import (
    extract_operation_signature,
    normalize_signature,
    validate_signature,
)


class TestTestOperations:
    """Test signature generation for testing operations."""

    def test_pytest_backend(self):
        workflow = {
            "nl_input": "Run the backend test suite with pytest",
            "workflow_template": "adw_test_iso"
        }
        sig = extract_operation_signature(workflow)
        assert sig == "test:pytest:backend"

    def test_pytest_explicit(self):
        workflow = {
            "nl_input": "Run pytest on server code",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "test:pytest:backend"

    def test_vitest_frontend(self):
        workflow = {
            "nl_input": "Run frontend tests using vitest",
            "workflow_template": "adw_test_iso"
        }
        sig = extract_operation_signature(workflow)
        assert sig == "test:vitest:frontend"

    def test_jest_ui(self):
        workflow = {
            "nl_input": "Test UI components with jest",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "test:jest:frontend"

    def test_generic_all(self):
        workflow = {
            "nl_input": "Run all tests",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "test:generic:all"


class TestBuildOperations:
    """Test signature generation for build operations."""

    def test_typecheck_backend(self):
        workflow = {
            "nl_input": "Run typecheck on backend",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "build:typecheck:backend"

    def test_typecheck_all(self):
        workflow = {
            "nl_input": "Run typecheck on entire project",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "build:typecheck:all"

    def test_compile_backend(self):
        workflow = {
            "nl_input": "Compile the backend code",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "build:compile:backend"

    def test_bundle_frontend(self):
        workflow = {
            "nl_input": "Bundle frontend with vite",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "build:bundle:frontend"


class TestFormatOperations:
    """Test signature generation for formatting operations."""

    def test_prettier(self):
        workflow = {
            "nl_input": "Format code with prettier",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "format:prettier:all"

    def test_black(self):
        workflow = {
            "nl_input": "Run black formatter on Python files",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "format:black:all"

    def test_eslint(self):
        workflow = {
            "nl_input": "Lint with eslint",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "format:eslint:all"


class TestGitOperations:
    """Test signature generation for git operations."""

    def test_git_diff(self):
        workflow = {
            "nl_input": "Show me the git diff",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "git:diff:summary"

    def test_git_status(self):
        workflow = {
            "nl_input": "Check git status",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "git:status:summary"

    def test_git_log(self):
        workflow = {
            "nl_input": "View git log",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "git:log:summary"


class TestDependencyOperations:
    """Test signature generation for dependency operations."""

    def test_npm_update(self):
        workflow = {
            "nl_input": "Update npm dependencies",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "deps:npm:update"

    def test_pip_install(self):
        workflow = {
            "nl_input": "Install Python packages with pip",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "deps:pip:update"


class TestDocumentationOperations:
    """Test signature generation for documentation operations."""

    def test_generate_docs(self):
        workflow = {
            "nl_input": "Generate documentation",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "docs:generate:all"

    def test_update_readme(self):
        workflow = {
            "nl_input": "Update the README file",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert sig == "docs:generate:all"


class TestNonPatterns:
    """Test that complex tasks don't generate signatures."""

    def test_feature_implementation(self):
        workflow = {
            "nl_input": "Implement user authentication with JWT",
            "workflow_template": "adw_plan_iso"
        }
        sig = extract_operation_signature(workflow)
        assert sig is None

    def test_bug_fix(self):
        workflow = {
            "nl_input": "Fix the login bug in the authentication system",
            "workflow_template": "adw_sdlc_iso"
        }
        sig = extract_operation_signature(workflow)
        assert sig is None

    def test_planning(self):
        workflow = {
            "nl_input": "Plan the implementation of the new feature",
            "workflow_template": "adw_plan_iso"
        }
        sig = extract_operation_signature(workflow)
        assert sig is None


class TestSignatureValidation:
    """Test signature validation and normalization."""

    def test_valid_signature(self):
        assert validate_signature("test:pytest:backend") is True
        assert validate_signature("build:typecheck:frontend") is True
        assert validate_signature("format:prettier:all") is True

    def test_invalid_format(self):
        assert validate_signature("test:pytest") is False  # Missing target
        assert validate_signature("test") is False  # Missing parts
        assert validate_signature("") is False  # Empty
        assert validate_signature("test:pytest:backend:extra") is False  # Too many parts

    def test_invalid_category(self):
        assert validate_signature("invalid:pytest:backend") is False

    def test_normalize_signature(self):
        assert normalize_signature("TEST:PYTEST:BACKEND") == "test:pytest:backend"
        assert normalize_signature("  test:pytest:backend  ") == "test:pytest:backend"

    def test_normalize_invalid(self):
        with pytest.raises(ValueError, match=r".*"):
            normalize_signature("invalid")


class TestTargetDetection:
    """Test target detection logic."""

    def test_explicit_backend(self):
        workflow = {
            "nl_input": "Run tests on the backend server",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert "backend" in sig

    def test_explicit_frontend(self):
        workflow = {
            "nl_input": "Run tests on the frontend UI",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert "frontend" in sig

    def test_explicit_both(self):
        workflow = {
            "nl_input": "Run tests on both frontend and backend",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert "both" in sig

    def test_infer_from_template(self):
        workflow = {
            "nl_input": "Run tests",
            "workflow_template": "adw_test_backend"
        }
        sig = extract_operation_signature(workflow)
        assert "backend" in sig

    def test_default_all(self):
        workflow = {
            "nl_input": "Run tests",
            "workflow_template": None
        }
        sig = extract_operation_signature(workflow)
        assert "all" in sig
