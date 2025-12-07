# Task: Validate Integration Checklist in Ship Phase

## Context
I'm working on the tac-webbuilder project. Session 3 implemented integration checklist generation in the Plan phase. This session adds checklist validation to the Ship phase to verify that planned integration points were actually implemented before shipping.

## Objective
Modify `adw_ship_iso.py` to validate integration checklist items before shipping. Validation should **warn only** (not block) since the Review phase has already validated code quality. Warnings will be added to PR comments to alert developers of potentially missing integration points.

## Background Information

### Session 3 Outputs
- **Integration checklist stored in state:** `agents/{adw_id}/adw_state.json`
- **5 categories:** Backend, Frontend, Database, Documentation, Testing
- **Required vs optional items:** Context-aware flagging
- **Markdown format:** Ready for PR comments

### Validation Strategy
- **Check file existence:** Verify files exist at expected paths
- **Grep for patterns:** Search for API endpoints, component imports, route registrations
- **Verify migrations:** Check database migration files exist
- **Test coverage:** Confirm tests exist for integration points
- **Warn only:** Don't block shipping, just add warnings to PR

### Error Handling
- **Warn only, don't fail:** Ship phase should not fail due to missing checklist items
- **Informative messages:** Clear warnings about what's missing
- **PR comment integration:** Add checklist status to PR description or comment

### Output Format
```markdown
## ⚠️ Integration Checklist Validation

### ✅ Passed Items (8/12)
- [x] API endpoint implemented
- [x] UI component created
- [x] Database migration created
...

### ⚠️ Missing Items (4/12)
- [ ] **API route registered in route configuration**
  - Expected: Route import in `app/server/main.py` or route files
  - Not found: Could not verify route registration
- [ ] **Component added to navigation/routing**
  - Expected: Component import in navigation file
  - Not found: No import found in `App.tsx` or routing files
...

**Note:** These are warnings only. The Review phase has already validated code quality.
```

---

## Step-by-Step Instructions

### Step 1: Understand Current Ship Phase (20 min)

Read the existing ship phase to understand where to insert validation:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws
```

**Read these files:**
1. `adw_ship_iso.py` - Main ship phase workflow
2. Look for where PR is approved and merged
3. Find where to insert validation logic (before approval)
4. Understand state loading and access patterns

**Document:**
- Where PR approval happens
- State file loading mechanism
- Where to insert validation logic
- Return values and error handling

### Step 2: Create Integration Validator Module (60-90 min)

Create new file: `adws/adw_modules/integration_validator.py`

```python
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
        result = subprocess.run(
            ["grep", "-r", "@app\\.\\(get\\|post\\|put\\|delete\\|patch\\)",
             os.path.join(worktree_path, "app/server")],
            capture_output=True,
            text=True
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
```

### Step 3: Create Tests (60 min)

Create new file: `adws/tests/test_integration_validator.py`

```python
#!/usr/bin/env python3
"""
Tests for Integration Checklist Validator

Run with:
    cd adws
    pytest tests/test_integration_validator.py -v
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
            }
        ],
        "frontend": [],
        "database": [],
        "documentation": [],
        "testing": []
    }

    report = validate_integration_checklist(checklist, temp_worktree)

    assert report.total_items == 2
    assert report.passed_items == 2
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
            }
        ],
        "documentation": [],
        "testing": []
    }

    report = validate_integration_checklist(checklist, temp_worktree)

    assert report.total_items == 1
    assert report.passed_items == 1
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


def test_validate_missing_items():
    """Test validation with missing files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Empty directory - no files
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

        report = validate_integration_checklist(checklist, tmpdir)

        assert report.total_items == 1
        # Should fail because no API endpoints exist
        # (depends on implementation - might pass with warning)


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


def test_check_api_endpoints_exist(temp_worktree):
    """Test API endpoint detection."""
    passed, warning, expected, actual = _check_api_endpoints_exist(temp_worktree)

    assert passed is True
    assert warning is None


def test_check_ui_components_exist(temp_worktree):
    """Test UI component detection."""
    passed, warning, expected, actual = _check_ui_components_exist(temp_worktree)

    assert passed is True
    assert warning is None


def test_check_migrations_exist(temp_worktree):
    """Test migration file detection."""
    passed, warning, expected, actual = _check_migrations_exist(temp_worktree)

    assert passed is True
    assert warning is None


def test_check_tests_exist(temp_worktree):
    """Test test file detection."""
    passed, warning, expected, actual = _check_tests_exist(temp_worktree)

    assert passed is True
    assert warning is None
```

### Step 4: Integrate with Ship Phase (45 min)

**Modify `adws/adw_ship_iso.py`:**

Add validation before PR approval:

```python
# Add import at top of file
from adw_modules.integration_validator import validate_integration_checklist

# ... in the main ship function, before PR approval ...

# Validate integration checklist (if exists)
integration_checklist = state.get("integration_checklist")
if integration_checklist:
    logger.info("[Ship] Validating integration checklist...")
    validation_report = validate_integration_checklist(
        checklist=integration_checklist,
        worktree_path=worktree_path
    )

    # Log validation results
    logger.info(
        f"[Ship] Checklist validation: "
        f"{validation_report.passed_items}/{validation_report.total_items} passed"
    )

    if validation_report.failed_items > 0:
        logger.warning(
            f"[Ship] {validation_report.required_failed} required items failed validation"
        )

    # Post validation report as PR comment
    validation_markdown = validation_report.to_markdown()
    make_issue_comment(
        issue_number,
        f"{adw_id}_ship: {validation_markdown}"
    )

    # Optional: Add to PR description
    # (would require PR update logic)
else:
    logger.info("[Ship] No integration checklist found in state - skipping validation")

# Continue with PR approval and merge
# (existing code)
```

### Step 5: Run Tests (20 min)

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws

# Run integration validator tests
uv run pytest tests/test_integration_validator.py -v

# Expected output:
# test_validate_empty_checklist PASSED
# test_validate_backend_items PASSED
# test_validate_frontend_items PASSED
# test_validate_database_items PASSED
# test_validate_documentation_items PASSED
# test_validate_testing_items PASSED
# test_markdown_formatting PASSED
# test_check_api_endpoints_exist PASSED
# test_check_ui_components_exist PASSED
# test_check_migrations_exist PASSED
# test_check_tests_exist PASSED
# ================== 11 passed ==================
```

### Step 6: Manual Integration Test (30 min)

Test validation with various scenarios:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws

# Test 1: Validate empty checklist
uv run python -c "
from adw_modules.integration_validator import validate_integration_checklist

checklist = {'backend': [], 'frontend': [], 'database': [], 'documentation': [], 'testing': []}
report = validate_integration_checklist(checklist, '/path/to/worktree')
print(report.to_markdown())
"

# Test 2: Validate real checklist with missing items
# (create test worktree with missing files)

# Test 3: Validate complete checklist
# (create test worktree with all files present)
```

### Step 7: Update Documentation (15 min)

**Update `adws/README.md`:**

Update the Integration Checklist section with Ship phase validation information:

```markdown
### Ship Phase Validation

During the Ship phase (before PR approval), the system validates that all checklist items were implemented:

**Validation Process:**
1. Loads checklist from state file
2. Checks backend items (API endpoints, routes, services)
3. Checks frontend items (components, navigation)
4. Checks database items (migrations, repositories)
5. Checks documentation items (docs files)
6. Checks testing items (test files)
7. Generates validation report
8. Posts warnings to PR as GitHub comment

**Validation Methods:**
- **File existence checks:** Verifies expected files exist
- **Pattern matching:** Greps for API decorators, imports, registrations
- **Directory scanning:** Counts components, migrations, tests
- **Warning only:** Does not block PR approval or merge

**Example Validation Report:**
```markdown
## ⚠️ Integration Checklist Validation

**Status:** 8/12 items validated

### ✅ Passed Items (8)
- [x] API endpoint implemented
- [x] UI component created
...

### ⚠️ Missing Items (4)
- [ ] **[REQUIRED]** API route registered in route configuration
  - ⚠️ No router registration found in main.py
  - Expected: app.include_router() calls
  - Actual: Not found
...

**Note:** These are warnings only. The Review phase has already validated code quality.
```

**Running Validation Manually:**
```bash
cd adws
uv run python -c "
from adw_modules.integration_validator import validate_integration_checklist
from adw_modules.state import ADWState

# Load state
state = ADWState.load('abc12345', None)

# Validate checklist
report = validate_integration_checklist(
    checklist=state.get('integration_checklist'),
    worktree_path=state.get('worktree_path')
)

# Display report
print(report.to_markdown())
print(f'\nPassed: {report.passed_items}/{report.total_items}')
print(f'Required failed: {report.required_failed}')
"
```
```

---

## Success Criteria

- ✅ Integration validator module created with validation logic
- ✅ Validation handles all 5 integration categories
- ✅ File existence checks implemented
- ✅ Pattern matching for API endpoints, components, routes
- ✅ Warning-only approach (doesn't block shipping)
- ✅ Markdown formatting for PR comments
- ✅ All 11 tests passing
- ✅ Integration with adw_ship_iso.py complete
- ✅ Validation report posted to PR comments
- ✅ Documentation updated with validation details

---

## Files Expected to Change

**Created (2):**
- `adws/adw_modules/integration_validator.py` (~600 lines)
- `adws/tests/test_integration_validator.py` (~200 lines)

**Modified (2):**
- `adws/adw_ship_iso.py` (add validation before PR approval, ~30 lines added)
- `adws/README.md` (add Ship phase validation section)

---

## Troubleshooting

### Import Errors

```bash
# If "ModuleNotFoundError: No module named 'adw_modules'"
cd adws
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/test_integration_validator.py -v
```

### Validation Always Passes

If validation always passes even with missing files:
- Check validation logic in helper functions
- Verify file paths are correct
- Review grep patterns for API endpoints
- Check directory existence checks

### Tests Fail on File System Checks

```bash
# Verify temp directory structure
ls -R /tmp/pytest-*/
# Check that test fixture creates necessary directories
```

---

## Estimated Time

- Step 1 (Understand ship phase): 20 min
- Step 2 (Create validator module): 60-90 min
- Step 3 (Create tests): 60 min
- Step 4 (Integration): 45 min
- Step 5 (Run tests): 20 min
- Step 6 (Manual test): 30 min
- Step 7 (Documentation): 15 min

**Total: 3.5-4 hours**

---

## Session Completion Instructions

When you finish this session, provide a completion summary in the **EXACT FORMAT** from Session 3:

```markdown
## ✅ Session 4 Complete - Integration Checklist (Ship Phase)

**Duration:** ~X hours
**Status:** Complete ✅
**Next:** Ready for Session 5 (...)

### What Was Done
[Details of what was implemented]

### Key Results
[Major achievements and features]

### Files Changed
[List of created/modified files]

### Test Results
[Test output]

### Manual Testing Results
[Scenarios tested]

### Next Session
[Preview of Session 5]
```

---

## Next Session Prompt Instructions

After providing the completion summary, create the prompt for **Session 5** (if applicable). Potential topics:
- **Verify Phase:** Operational validation (does the feature actually work end-to-end?)
- **Enhanced Detection:** More sophisticated pattern matching for validation
- **Coverage Analysis:** Integrate with test coverage tools
- **Auto-remediation:** Suggest fixes for missing integration points

---

**Ready to copy into a new chat!**

Run `/prime` first, then paste this entire prompt.
