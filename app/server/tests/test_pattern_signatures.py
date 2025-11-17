"""
Comprehensive test suite for pattern signature generation system.

Tests cover all 6 categories (test, build, format, git, deps, docs),
subcategory detection, target detection, validation, normalization,
and edge cases.
"""

import pytest
from core.pattern_signatures import (
    generate_signature,
    detect_category,
    detect_subcategory,
    detect_target,
    validate_signature,
    normalize_signature,
    parse_signature,
)


class TestCategoryDetection:
    """Test detection of all 6 operation categories."""

    def test_detect_test_category_pytest(self):
        """Test detection of test category with pytest keyword."""
        assert detect_category("run pytest tests") == "test"

    def test_detect_test_category_vitest(self):
        """Test detection of test category with vitest keyword."""
        assert detect_category("run vitest tests") == "test"

    def test_detect_test_category_jest(self):
        """Test detection of test category with jest keyword."""
        assert detect_category("run jest tests") == "test"

    def test_detect_test_category_generic(self):
        """Test detection of test category with generic test keyword."""
        assert detect_category("run tests") == "test"
        assert detect_category("test suite") == "test"
        assert detect_category("testing") == "test"

    def test_detect_build_category_build(self):
        """Test detection of build category with build keyword."""
        assert detect_category("build the project") == "build"

    def test_detect_build_category_compile(self):
        """Test detection of build category with compile keyword."""
        assert detect_category("compile typescript") == "build"

    def test_detect_build_category_typecheck(self):
        """Test detection of build category with typecheck keyword."""
        assert detect_category("typecheck the code") == "build"
        assert detect_category("type check frontend") == "build"

    def test_detect_format_category_format(self):
        """Test detection of format category with format keyword."""
        assert detect_category("format code") == "format"
        assert detect_category("formatting") == "format"

    def test_detect_format_category_lint(self):
        """Test detection of format category with lint keyword."""
        assert detect_category("lint the code") == "format"

    def test_detect_format_category_prettier(self):
        """Test detection of format category with prettier keyword."""
        assert detect_category("run prettier") == "format"

    def test_detect_git_category_diff(self):
        """Test detection of git category with diff keyword."""
        assert detect_category("git diff") == "git"
        assert detect_category("show diff") == "git"

    def test_detect_git_category_commit(self):
        """Test detection of git category with commit keyword."""
        assert detect_category("git commit") == "git"
        assert detect_category("commit changes") == "git"

    def test_detect_git_category_status(self):
        """Test detection of git category with status keyword."""
        assert detect_category("git status") == "git"

    def test_detect_deps_category_npm(self):
        """Test detection of deps category with npm install keyword."""
        assert detect_category("npm install") == "deps"

    def test_detect_deps_category_pip(self):
        """Test detection of deps category with pip install keyword."""
        assert detect_category("pip install packages") == "deps"

    def test_detect_deps_category_dependencies(self):
        """Test detection of deps category with dependencies keyword."""
        assert detect_category("update dependencies") == "deps"
        assert detect_category("install packages") == "deps"

    def test_detect_docs_category_documentation(self):
        """Test detection of docs category with documentation keyword."""
        assert detect_category("update documentation") == "docs"
        assert detect_category("write docs") == "docs"

    def test_detect_docs_category_readme(self):
        """Test detection of docs category with readme keyword."""
        assert detect_category("update readme") == "docs"

    def test_detect_no_category(self):
        """Test that unrecognized input returns None."""
        assert detect_category("fix the bug") is None
        assert detect_category("implement feature") is None
        assert detect_category("random text") is None


class TestSubcategoryDetection:
    """Test detection of subcategories for each category."""

    def test_detect_test_subcategory_pytest(self):
        """Test detection of pytest subcategory."""
        assert detect_subcategory("run pytest tests", "test") == "pytest"

    def test_detect_test_subcategory_vitest(self):
        """Test detection of vitest subcategory."""
        assert detect_subcategory("run vitest tests", "test") == "vitest"

    def test_detect_test_subcategory_jest(self):
        """Test detection of jest subcategory."""
        assert detect_subcategory("run jest tests", "test") == "jest"

    def test_detect_test_subcategory_generic(self):
        """Test detection of generic test subcategory."""
        assert detect_subcategory("run tests", "test") == "generic"

    def test_detect_build_subcategory_typecheck(self):
        """Test detection of typecheck subcategory."""
        assert detect_subcategory("typecheck code", "build") == "typecheck"
        assert detect_subcategory("type check", "build") == "typecheck"

    def test_detect_build_subcategory_compile(self):
        """Test detection of compile subcategory."""
        assert detect_subcategory("compile typescript", "build") == "compile"

    def test_detect_build_subcategory_npm(self):
        """Test detection of npm subcategory."""
        assert detect_subcategory("npm build", "build") == "npm"

    def test_detect_format_subcategory_prettier(self):
        """Test detection of prettier subcategory."""
        assert detect_subcategory("format with prettier", "format") == "prettier"

    def test_detect_format_subcategory_eslint(self):
        """Test detection of eslint subcategory."""
        assert detect_subcategory("run eslint", "format") == "eslint"

    def test_detect_format_subcategory_black(self):
        """Test detection of black subcategory."""
        assert detect_subcategory("format with black", "format") == "black"

    def test_detect_git_subcategory_diff(self):
        """Test detection of diff subcategory."""
        assert detect_subcategory("show diff", "git") == "diff"

    def test_detect_git_subcategory_commit(self):
        """Test detection of commit subcategory."""
        assert detect_subcategory("commit changes", "git") == "commit"

    def test_detect_git_subcategory_status(self):
        """Test detection of status subcategory."""
        assert detect_subcategory("check status", "git") == "status"

    def test_detect_deps_subcategory_npm(self):
        """Test detection of npm subcategory."""
        assert detect_subcategory("npm install", "deps") == "npm"

    def test_detect_deps_subcategory_pip(self):
        """Test detection of pip subcategory."""
        assert detect_subcategory("pip install", "deps") == "pip"

    def test_detect_deps_subcategory_update(self):
        """Test detection of update subcategory."""
        assert detect_subcategory("update packages", "deps") == "update"

    def test_detect_docs_subcategory_readme(self):
        """Test detection of readme subcategory."""
        assert detect_subcategory("update readme", "docs") == "readme"

    def test_detect_docs_subcategory_api(self):
        """Test detection of api subcategory."""
        assert detect_subcategory("write api docs", "docs") == "api"


class TestTargetDetection:
    """Test detection of operation targets."""

    def test_detect_target_backend(self):
        """Test detection of backend target."""
        assert detect_target("run backend tests") == "backend"
        assert detect_target("test server code") == "backend"
        assert detect_target("python tests") == "backend"

    def test_detect_target_frontend(self):
        """Test detection of frontend target."""
        assert detect_target("run frontend tests") == "frontend"
        assert detect_target("test client code") == "frontend"
        assert detect_target("react tests") == "frontend"

    def test_detect_target_both(self):
        """Test detection of both target."""
        assert detect_target("test both frontend and backend") == "both"
        assert detect_target("test backend and frontend") == "both"
        assert detect_target("test both") == "both"

    def test_detect_target_all_default(self):
        """Test that all is the default target."""
        assert detect_target("run tests") == "all"
        assert detect_target("format code") == "all"

    def test_detect_target_both_when_both_mentioned(self):
        """Test that both is detected when both keywords present."""
        assert detect_target("test backend and frontend code") == "both"


class TestSignatureGeneration:
    """Test full signature generation from natural language."""

    def test_generate_signature_test_pytest_backend(self):
        """Test generation of test:pytest:backend signature."""
        sig = generate_signature("run pytest tests on backend")
        assert sig == "test:pytest:backend"

    def test_generate_signature_test_vitest_frontend(self):
        """Test generation of test:vitest:frontend signature."""
        sig = generate_signature("run vitest tests on frontend")
        assert sig == "test:vitest:frontend"

    def test_generate_signature_build_typecheck_both(self):
        """Test generation of build:typecheck:both signature."""
        sig = generate_signature("typecheck both frontend and backend")
        assert sig == "build:typecheck:both"

    def test_generate_signature_format_prettier_all(self):
        """Test generation of format:prettier:all signature."""
        sig = generate_signature("format code with prettier")
        assert sig == "format:prettier:all"

    def test_generate_signature_git_diff_all(self):
        """Test generation of git:diff:all signature."""
        sig = generate_signature("show git diff")
        assert sig == "git:diff:all"

    def test_generate_signature_deps_npm_all(self):
        """Test generation of deps:npm:all signature."""
        sig = generate_signature("npm install dependencies")
        assert sig == "deps:npm:all"

    def test_generate_signature_docs_readme_all(self):
        """Test generation of docs:readme:all signature."""
        sig = generate_signature("update readme documentation")
        assert sig == "docs:readme:all"

    def test_generate_signature_test_generic(self):
        """Test generation with generic subcategory."""
        sig = generate_signature("run tests on backend")
        assert sig == "test:generic:backend"


class TestValidation:
    """Test signature validation functions."""

    def test_validate_valid_signature(self):
        """Test that valid signatures pass validation."""
        assert validate_signature("test:pytest:backend") is True
        assert validate_signature("build:typecheck:frontend") is True
        assert validate_signature("format:prettier:all") is True

    def test_validate_invalid_format_missing_part(self):
        """Test that signatures with missing parts fail validation."""
        assert validate_signature("test:pytest") is False
        assert validate_signature("test") is False

    def test_validate_invalid_category(self):
        """Test that signatures with invalid category fail validation."""
        assert validate_signature("invalid:pytest:backend") is False

    def test_validate_invalid_subcategory(self):
        """Test that signatures with invalid subcategory fail validation."""
        assert validate_signature("test:invalid:backend") is False

    def test_validate_invalid_target(self):
        """Test that signatures with invalid target fail validation."""
        assert validate_signature("test:pytest:invalid") is False

    def test_validate_wrong_separator(self):
        """Test that signatures with wrong separator fail validation."""
        assert validate_signature("test-pytest-backend") is False

    def test_validate_empty_or_none(self):
        """Test that empty or None input fails validation."""
        assert validate_signature("") is False
        assert validate_signature(None) is False


class TestNormalization:
    """Test signature normalization functions."""

    def test_normalize_uppercase(self):
        """Test normalization converts uppercase to lowercase."""
        normalized = normalize_signature("Test:Pytest:Backend")
        assert normalized == "test:pytest:backend"

    def test_normalize_mixed_case(self):
        """Test normalization handles mixed case."""
        normalized = normalize_signature("BUILD:NPM:FRONTEND")
        assert normalized == "build:npm:frontend"

    def test_normalize_whitespace(self):
        """Test normalization trims whitespace."""
        normalized = normalize_signature("  test:pytest:backend  ")
        assert normalized == "test:pytest:backend"

    def test_normalize_invalid_returns_none(self):
        """Test that invalid signatures return None after normalization."""
        assert normalize_signature("invalid:foo:bar") is None
        assert normalize_signature("test:pytest") is None


class TestParsing:
    """Test signature parsing functions."""

    def test_parse_valid_signature(self):
        """Test parsing a valid signature."""
        parsed = parse_signature("test:pytest:backend")
        assert parsed == {
            "category": "test",
            "subcategory": "pytest",
            "target": "backend",
        }

    def test_parse_another_valid_signature(self):
        """Test parsing another valid signature."""
        parsed = parse_signature("build:typecheck:frontend")
        assert parsed == {
            "category": "build",
            "subcategory": "typecheck",
            "target": "frontend",
        }

    def test_parse_invalid_signature(self):
        """Test that invalid signatures return None."""
        assert parse_signature("invalid") is None
        assert parse_signature("test:pytest") is None

    def test_parse_empty_or_none(self):
        """Test that empty or None input returns None."""
        assert parse_signature("") is None
        assert parse_signature(None) is None


class TestEdgeCases:
    """Test edge cases and complex inputs."""

    def test_complex_multi_step_task_returns_none(self):
        """Test that complex multi-step tasks return None."""
        sig = generate_signature("implement authentication with JWT, add tests, and update docs")
        assert sig is None

    def test_refactor_task_returns_none(self):
        """Test that refactor tasks return None."""
        sig = generate_signature("refactor the entire backend architecture")
        assert sig is None

    def test_implement_task_returns_none(self):
        """Test that implement tasks return None."""
        sig = generate_signature("implement user authentication feature")
        assert sig is None

    def test_empty_input_returns_none(self):
        """Test that empty input returns None."""
        assert generate_signature("") is None
        assert generate_signature("   ") is None

    def test_none_input_returns_none(self):
        """Test that None input returns None."""
        assert generate_signature(None) is None

    def test_ambiguous_input_returns_none(self):
        """Test that ambiguous input returns None."""
        sig = generate_signature("fix the thing")
        assert sig is None

    def test_multiple_operations_with_and_returns_none(self):
        """Test that multiple operations with 'and' return None."""
        sig = generate_signature("run tests and build the project")
        assert sig is None

    def test_case_insensitive_detection(self):
        """Test that detection is case-insensitive."""
        sig1 = generate_signature("Run Pytest Tests")
        sig2 = generate_signature("run pytest tests")
        assert sig1 == sig2
        assert sig1 == "test:pytest:all"
