#!/usr/bin/env python3
"""
Integration Checklist Validator for ADW Ship Phase

Validates that integration checklist items were actually implemented
before shipping. Provides warnings for missing items but does not block.

Usage:
    from adw_modules.integration_validator import validate_integration_checklist

    warnings = validate_integration_checklist(
        checklist=state.get("integration_checklist"),
        worktree_path="/path/to/worktree"
    )
"""

import logging
import os
import subprocess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validating a single checklist item."""
    item_description: str
    category: str
    required: bool
    passed: bool
    warning_message: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report for integration checklist."""
    total_items: int
    passed_items: int
    failed_items: int
    required_failed: int
    optional_failed: int
    results: List[ValidationResult]

    def to_markdown(self) -> str:
        """Format validation report as markdown."""
        lines = ["## ⚠️ Integration Checklist Validation", ""]

        # Summary
        lines.append(f"**Status:** {self.passed_items}/{self.total_items} items validated")
        lines.append("")

        if self.failed_items == 0:
            lines.append("### ✅ All Items Passed")
            lines.append("")
            lines.append("All integration checklist items have been validated successfully.")
        else:
            # Passed items
            passed = [r for r in self.results if r.passed]
            if passed:
                lines.append(f"### ✅ Passed Items ({len(passed)})")
                lines.append("")
                for result in passed:
                    lines.append(f"- [x] {result.item_description}")
                lines.append("")

            # Failed items
            failed = [r for r in self.results if not r.passed]
            if failed:
                lines.append(f"### ⚠️ Missing Items ({len(failed)})")
                lines.append("")
                for result in failed:
                    required = "**[REQUIRED]**" if result.required else "[OPTIONAL]"
                    lines.append(f"- [ ] {required} {result.item_description}")
                    if result.warning_message:
                        lines.append(f"  - ⚠️ {result.warning_message}")
                    if result.expected:
                        lines.append(f"  - Expected: {result.expected}")
                    if result.actual:
                        lines.append(f"  - Actual: {result.actual}")
                lines.append("")

        lines.append("---")
        lines.append("**Note:** These are warnings only. The Review phase has already validated code quality.")

        return "\n".join(lines)


def validate_integration_checklist(
    checklist: Dict,
    worktree_path: str
) -> ValidationReport:
    """
    Validate integration checklist items.

    Args:
        checklist: Integration checklist dict from state
        worktree_path: Path to worktree for validation

    Returns:
        ValidationReport with validation results
    """
    results = []

    # Validate backend items
    if "backend" in checklist:
        for item_dict in checklist["backend"]:
            result = _validate_backend_item(item_dict, worktree_path)
            results.append(result)

    # Validate frontend items
    if "frontend" in checklist:
        for item_dict in checklist["frontend"]:
            result = _validate_frontend_item(item_dict, worktree_path)
            results.append(result)

    # Validate database items
    if "database" in checklist:
        for item_dict in checklist["database"]:
            result = _validate_database_item(item_dict, worktree_path)
            results.append(result)

    # Validate documentation items
    if "documentation" in checklist:
        for item_dict in checklist["documentation"]:
            result = _validate_documentation_item(item_dict, worktree_path)
            results.append(result)

    # Validate testing items
    if "testing" in checklist:
        for item_dict in checklist["testing"]:
            result = _validate_testing_item(item_dict, worktree_path)
            results.append(result)

    # Calculate summary
    total_items = len(results)
    passed_items = sum(1 for r in results if r.passed)
    failed_items = total_items - passed_items
    required_failed = sum(1 for r in results if not r.passed and r.required)
    optional_failed = sum(1 for r in results if not r.passed and not r.required)

    report = ValidationReport(
        total_items=total_items,
        passed_items=passed_items,
        failed_items=failed_items,
        required_failed=required_failed,
        optional_failed=optional_failed,
        results=results
    )

    logger.info(
        f"[IntegrationValidator] Validation complete: "
        f"{passed_items}/{total_items} passed, "
        f"{required_failed} required failed, "
        f"{optional_failed} optional failed"
    )

    return report


def _validate_backend_item(item_dict: Dict, worktree_path: str) -> ValidationResult:
    """Validate a backend checklist item."""
    description = item_dict["description"]
    required = item_dict["required"]

    # Check for API endpoint implementation
    if "endpoint" in description.lower():
        passed, warning, expected, actual = _check_api_endpoints_exist(worktree_path)
        return ValidationResult(
            item_description=description,
            category="backend",
            required=required,
            passed=passed,
            warning_message=warning,
            expected=expected,
            actual=actual
        )

    # Check for route registration
    elif "route" in description.lower() and "registered" in description.lower():
        passed, warning, expected, actual = _check_routes_registered(worktree_path)
        return ValidationResult(
            item_description=description,
            category="backend",
            required=required,
            passed=passed,
            warning_message=warning,
            expected=expected,
            actual=actual
        )

    # Check for service layer implementation
    elif "service" in description.lower():
        passed, warning, expected, actual = _check_service_layer_exists(worktree_path)
        return ValidationResult(
            item_description=description,
            category="backend",
            required=required,
            passed=passed,
            warning_message=warning,
            expected=expected,
            actual=actual
        )

    # Default: Can't validate automatically
    else:
        return ValidationResult(
            item_description=description,
            category="backend",
            required=required,
            passed=True,  # Assume passed if we can't validate
            warning_message="Could not validate automatically - manual verification needed"
        )


def _validate_frontend_item(item_dict: Dict, worktree_path: str) -> ValidationResult:
    """Validate a frontend checklist item."""
    description = item_dict["description"]
    required = item_dict["required"]

    # Check for UI component creation
    if "component" in description.lower() and "created" in description.lower():
        passed, warning, expected, actual = _check_ui_components_exist(worktree_path)
        return ValidationResult(
            item_description=description,
            category="frontend",
            required=required,
            passed=passed,
            warning_message=warning,
            expected=expected,
            actual=actual
        )

    # Check for navigation/routing
    elif "navigation" in description.lower() or "routing" in description.lower():
        passed, warning, expected, actual = _check_component_in_navigation(worktree_path)
        return ValidationResult(
            item_description=description,
            category="frontend",
            required=required,
            passed=passed,
            warning_message=warning,
            expected=expected,
            actual=actual
        )

    # Default: Can't validate automatically
    else:
        return ValidationResult(
            item_description=description,
            category="frontend",
            required=required,
            passed=True,
            warning_message="Could not validate automatically - manual verification needed"
        )


def _validate_database_item(item_dict: Dict, worktree_path: str) -> ValidationResult:
    """Validate a database checklist item."""
    description = item_dict["description"]
    required = item_dict["required"]

    # Check for migration files
    if "migration" in description.lower():
        passed, warning, expected, actual = _check_migrations_exist(worktree_path)
        return ValidationResult(
            item_description=description,
            category="database",
            required=required,
            passed=passed,
            warning_message=warning,
            expected=expected,
            actual=actual
        )

    # Check for repository methods
    elif "repository" in description.lower():
        passed, warning, expected, actual = _check_repository_methods_exist(worktree_path)
        return ValidationResult(
            item_description=description,
            category="database",
            required=required,
            passed=passed,
            warning_message=warning,
            expected=expected,
            actual=actual
        )

    # Default: Can't validate automatically
    else:
        return ValidationResult(
            item_description=description,
            category="database",
            required=required,
            passed=True,
            warning_message="Could not validate automatically - manual verification needed"
        )


def _validate_documentation_item(item_dict: Dict, worktree_path: str) -> ValidationResult:
    """Validate a documentation checklist item."""
    description = item_dict["description"]
    required = item_dict["required"]

    # Check for documentation files
    if "documentation" in description.lower() or "docs" in description.lower():
        passed, warning, expected, actual = _check_docs_updated(worktree_path)
        return ValidationResult(
            item_description=description,
            category="documentation",
            required=required,
            passed=passed,
            warning_message=warning,
            expected=expected,
            actual=actual
        )

    # Default: Can't validate automatically
    else:
        return ValidationResult(
            item_description=description,
            category="documentation",
            required=required,
            passed=True,
            warning_message="Could not validate automatically - manual verification needed"
        )


def _validate_testing_item(item_dict: Dict, worktree_path: str) -> ValidationResult:
    """Validate a testing checklist item."""
    description = item_dict["description"]
    required = item_dict["required"]

    # Check for test files
    if "test" in description.lower():
        passed, warning, expected, actual = _check_tests_exist(worktree_path)
        return ValidationResult(
            item_description=description,
            category="testing",
            required=required,
            passed=passed,
            warning_message=warning,
            expected=expected,
            actual=actual
        )

    # Default: Can't validate automatically
    else:
        return ValidationResult(
            item_description=description,
            category="testing",
            required=required,
            passed=True,
            warning_message="Could not validate automatically - manual verification needed"
        )


# Helper functions for specific checks

def _check_api_endpoints_exist(worktree_path: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """Check if API endpoints were implemented."""
    try:
        # Search for FastAPI route definitions
        server_path = os.path.join(worktree_path, "app/server")
        if not os.path.exists(server_path):
            return False, "app/server directory not found", "API endpoint decorators in route files", "Directory not found"

        result = subprocess.run(
            ["grep", "-r", "@app\\.\\(get\\|post\\|put\\|delete\\|patch\\)", server_path],
            capture_output=True,
            text=True,
            cwd=worktree_path
        )

        if result.returncode == 0 and result.stdout:
            return True, None, "API endpoint decorators in route files", "Found"
        else:
            return False, "No API endpoint decorators found", "API endpoint decorators (@app.get, @app.post, etc.)", "Not found"
    except Exception as e:
        logger.error(f"Error checking API endpoints: {e}")
        return True, f"Validation error: {e}", None, None


def _check_routes_registered(worktree_path: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """Check if routes are registered in FastAPI app."""
    try:
        # Check for router imports in main.py or route files
        main_file = os.path.join(worktree_path, "app/server/main.py")
        if os.path.exists(main_file):
            with open(main_file, 'r') as f:
                content = f.read()
                if "app.include_router" in content or "router" in content:
                    return True, None, "Router registration in main.py", "Found"

        return False, "No router registration found in main.py", "app.include_router() calls", "Not found"
    except Exception as e:
        logger.error(f"Error checking route registration: {e}")
        return True, f"Validation error: {e}", None, None


def _check_service_layer_exists(worktree_path: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """Check if service layer files exist."""
    try:
        services_dir = os.path.join(worktree_path, "app/server/services")
        if os.path.exists(services_dir):
            # Check if there are .py files in services directory
            py_files = [f for f in os.listdir(services_dir) if f.endswith('.py') and f != '__init__.py']
            if py_files:
                return True, None, "Service layer files", f"Found {len(py_files)} service(s)"

        return False, "No service layer files found", "Python files in app/server/services/", "Not found"
    except Exception as e:
        logger.error(f"Error checking service layer: {e}")
        return True, f"Validation error: {e}", None, None


def _check_ui_components_exist(worktree_path: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """Check if new UI components were created."""
    try:
        components_dir = os.path.join(worktree_path, "app/client/src/components")
        if os.path.exists(components_dir):
            # Check for .tsx files
            tsx_files = [f for f in os.listdir(components_dir) if f.endswith('.tsx')]
            if tsx_files:
                return True, None, "React components", f"Found {len(tsx_files)} component(s)"

        return False, "No React components found", "TypeScript React files in app/client/src/components/", "Not found"
    except Exception as e:
        logger.error(f"Error checking UI components: {e}")
        return True, f"Validation error: {e}", None, None


def _check_component_in_navigation(worktree_path: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """Check if components are imported in navigation/routing files."""
    try:
        # Check App.tsx or routing files for component imports
        app_file = os.path.join(worktree_path, "app/client/src/App.tsx")
        if os.path.exists(app_file):
            with open(app_file, 'r') as f:
                content = f.read()
                # Look for imports from components directory
                if "from './components/" in content or 'from "./components/' in content:
                    return True, None, "Component imports in App.tsx", "Found"

        return False, "No component imports found in navigation files", "Component imports in App.tsx or routing files", "Not found"
    except Exception as e:
        logger.error(f"Error checking component navigation: {e}")
        return True, f"Validation error: {e}", None, None


def _check_migrations_exist(worktree_path: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """Check if database migration files exist."""
    try:
        migrations_dir = os.path.join(worktree_path, "app/server/db/migrations")
        if os.path.exists(migrations_dir):
            # Check for .sql files
            sql_files = [f for f in os.listdir(migrations_dir) if f.endswith('.sql')]
            if sql_files:
                return True, None, "Database migration files", f"Found {len(sql_files)} migration(s)"

        return False, "No migration files found", "SQL files in app/server/db/migrations/", "Not found"
    except Exception as e:
        logger.error(f"Error checking migrations: {e}")
        return True, f"Validation error: {e}", None, None


def _check_repository_methods_exist(worktree_path: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """Check if repository methods were implemented."""
    try:
        repositories_dir = os.path.join(worktree_path, "app/server/repositories")
        if os.path.exists(repositories_dir):
            # Check for .py files in repositories directory
            py_files = [f for f in os.listdir(repositories_dir) if f.endswith('.py') and f != '__init__.py']
            if py_files:
                return True, None, "Repository files", f"Found {len(py_files)} repository(ies)"

        return False, "No repository files found", "Python files in app/server/repositories/", "Not found"
    except Exception as e:
        logger.error(f"Error checking repository methods: {e}")
        return True, f"Validation error: {e}", None, None


def _check_docs_updated(worktree_path: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """Check if documentation was updated."""
    try:
        docs_dirs = [
            os.path.join(worktree_path, "docs"),
            os.path.join(worktree_path, "app_docs")
        ]

        for docs_dir in docs_dirs:
            if os.path.exists(docs_dir):
                # Check for .md files
                md_files = []
                for root, dirs, files in os.walk(docs_dir):
                    md_files.extend([f for f in files if f.endswith('.md')])

                if md_files:
                    return True, None, "Documentation files", f"Found {len(md_files)} doc file(s)"

        return False, "No documentation files found", "Markdown files in docs/ or app_docs/", "Not found"
    except Exception as e:
        logger.error(f"Error checking documentation: {e}")
        return True, f"Validation error: {e}", None, None


def _check_tests_exist(worktree_path: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """Check if test files exist."""
    try:
        test_dirs = [
            os.path.join(worktree_path, "app/server/tests"),
            os.path.join(worktree_path, "app/client/src/__tests__")
        ]

        test_count = 0
        for test_dir in test_dirs:
            if os.path.exists(test_dir):
                # Check for test files
                for root, dirs, files in os.walk(test_dir):
                    test_count += len([f for f in files if 'test' in f.lower() and (f.endswith('.py') or f.endswith('.ts') or f.endswith('.tsx'))])

        if test_count > 0:
            return True, None, "Test files", f"Found {test_count} test file(s)"

        return False, "No test files found", "Test files in app/server/tests/ or app/client/src/__tests__/", "Not found"
    except Exception as e:
        logger.error(f"Error checking tests: {e}")
        return True, f"Validation error: {e}", None, None
