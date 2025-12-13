# Task: Generate Integration Checklist in Plan Phase

## Context
I'm working on the tac-webbuilder project. A recurring issue is that features are built correctly but not fully integrated - API endpoints exist but routes aren't wired up, UI components are created but not added to navigation, database schemas exist but no UI displays the data. This session adds integration checklist generation to the Plan phase to identify all integration points upfront.

## Objective
Modify `adw_plan_iso.py` to automatically generate an integration checklist when planning new features. The checklist will be validated in the Ship phase (Session 4) to ensure features are fully wired up before deployment.

## Background Information
- **Problem Examples:**
  - Pattern Detection: Schema exists, no UI component created
  - Cost Tracking: Tools registered, but usage not logged
  - Average Cost Metric: Backend implemented, frontend visual not rendering

- **Root Cause:** No systematic verification that all integration points are addressed

- **Solution Architecture:**
  - **Plan Phase (Session 3):** Generate integration checklist based on issue analysis
  - **Ship Phase (Session 4):** Validate checklist items exist (warn only, don't block)
  - **Verify Phase (Future):** Confirm operational functionality

- **Checklist Categories:**
  1. **Backend Integration:** API endpoints, routes, business logic
  2. **Frontend Integration:** UI components, routing, state management
  3. **Database Integration:** Migrations, schema updates, data flow
  4. **Documentation Integration:** API docs, feature docs, user guides
  5. **Testing Integration:** Unit tests, integration tests, E2E tests

- **Files to Modify:**
  - `adws/adw_plan_iso.py` - Add checklist generation
  - Potentially: ADW state management to persist checklist

- **Files to Create:**
  - `adws/adw_modules/integration_checklist.py` - Checklist generation logic
  - `adws/tests/test_integration_checklist.py` - Tests for checklist generator

---

## Step-by-Step Instructions

### Step 1: Understand Current Plan Phase (20 min)

Read the existing plan phase to understand where to insert checklist generation:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws
```

**Read these files:**
1. `adw_plan_iso.py` - Main plan phase workflow
2. Look for where the plan is generated and stored
3. Find the state file structure (usually JSON in `agents/` or workflow-specific directory)
4. Understand what information is available (nl_input, issue details, etc.)

**Document:**
- Where plan output is generated
- State file location and format
- What context is available for checklist generation
- Return values and data structures

### Step 2: Create Integration Checklist Module (45-60 min)

Create new file: `adws/adw_modules/integration_checklist.py`

```python
#!/usr/bin/env python3
"""
Integration Checklist Generator for ADW Plan Phase

Analyzes feature requirements and generates comprehensive integration checklist
to ensure all components are properly wired up.

Usage:
    from adw_modules.integration_checklist import generate_integration_checklist

    checklist = generate_integration_checklist(
        nl_input="Add user authentication to API",
        issue_body="Implement JWT-based authentication...",
        issue_labels=["backend", "security"]
    )
"""

import logging
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ChecklistItem:
    """Single integration checklist item."""
    category: str  # backend, frontend, database, docs, testing
    description: str
    required: bool
    detected_keywords: List[str]
    notes: Optional[str] = None


@dataclass
class IntegrationChecklist:
    """Complete integration checklist for a feature."""
    backend_items: List[ChecklistItem]
    frontend_items: List[ChecklistItem]
    database_items: List[ChecklistItem]
    documentation_items: List[ChecklistItem]
    testing_items: List[ChecklistItem]

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'backend': [asdict(item) for item in self.backend_items],
            'frontend': [asdict(item) for item in self.frontend_items],
            'database': [asdict(item) for item in self.database_items],
            'documentation': [asdict(item) for item in self.documentation_items],
            'testing': [asdict(item) for item in self.testing_items]
        }

    def get_all_items(self) -> List[ChecklistItem]:
        """Get flat list of all checklist items."""
        return (
            self.backend_items +
            self.frontend_items +
            self.database_items +
            self.documentation_items +
            self.testing_items
        )

    def get_required_items(self) -> List[ChecklistItem]:
        """Get only required checklist items."""
        return [item for item in self.get_all_items() if item.required]


def generate_integration_checklist(
    nl_input: str,
    issue_body: str = "",
    issue_labels: List[str] = None
) -> IntegrationChecklist:
    """
    Generate integration checklist based on feature requirements.

    Args:
        nl_input: Natural language input describing the feature
        issue_body: GitHub issue body with additional details
        issue_labels: GitHub issue labels (e.g., ["backend", "frontend"])

    Returns:
        IntegrationChecklist with categorized items

    Example:
        >>> checklist = generate_integration_checklist(
        ...     nl_input="Add user profile page",
        ...     issue_labels=["frontend", "backend"]
        ... )
        >>> len(checklist.backend_items) > 0
        True
    """
    if issue_labels is None:
        issue_labels = []

    # Combine text for analysis
    full_text = f"{nl_input} {issue_body}".lower()

    # Detect feature type
    is_backend = _is_backend_feature(full_text, issue_labels)
    is_frontend = _is_frontend_feature(full_text, issue_labels)
    is_database = _is_database_feature(full_text, issue_labels)
    is_api = _is_api_feature(full_text)
    is_ui_component = _is_ui_component(full_text)

    # Generate checklist items
    backend_items = []
    frontend_items = []
    database_items = []
    documentation_items = []
    testing_items = []

    # Backend Integration
    if is_backend or is_api:
        backend_items.extend([
            ChecklistItem(
                category="backend",
                description="API endpoint implemented",
                required=True,
                detected_keywords=_extract_keywords(full_text, ["api", "endpoint", "route"])
            ),
            ChecklistItem(
                category="backend",
                description="API route registered in route configuration",
                required=True,
                detected_keywords=["route", "api"]
            ),
            ChecklistItem(
                category="backend",
                description="Business logic implemented in service layer",
                required=True,
                detected_keywords=_extract_keywords(full_text, ["service", "logic", "business"])
            ),
        ])

    # Frontend Integration
    if is_frontend or is_ui_component:
        frontend_items.extend([
            ChecklistItem(
                category="frontend",
                description="UI component created",
                required=True,
                detected_keywords=_extract_keywords(full_text, ["component", "ui", "page", "panel"])
            ),
            ChecklistItem(
                category="frontend",
                description="Component added to navigation/routing",
                required=True,
                detected_keywords=["navigation", "route", "menu"]
            ),
            ChecklistItem(
                category="frontend",
                description="State management configured (if needed)",
                required=False,
                detected_keywords=_extract_keywords(full_text, ["state", "store", "context"])
            ),
        ])

    # Database Integration
    if is_database:
        database_items.extend([
            ChecklistItem(
                category="database",
                description="Database migration created",
                required=True,
                detected_keywords=_extract_keywords(full_text, ["migration", "schema", "table"])
            ),
            ChecklistItem(
                category="database",
                description="Pydantic model updated (if applicable)",
                required=False,
                detected_keywords=["model", "pydantic", "schema"]
            ),
            ChecklistItem(
                category="database",
                description="Repository methods implemented",
                required=True,
                detected_keywords=["repository", "query", "database"]
            ),
        ])

    # Documentation Integration
    if is_backend or is_frontend or is_database:
        documentation_items.extend([
            ChecklistItem(
                category="documentation",
                description="API documentation updated (if backend changes)",
                required=is_backend or is_api,
                detected_keywords=["api", "docs"]
            ),
            ChecklistItem(
                category="documentation",
                description="Feature documentation added",
                required=True,
                detected_keywords=["docs", "documentation"]
            ),
            ChecklistItem(
                category="documentation",
                description="README updated (if user-facing feature)",
                required=is_frontend,
                detected_keywords=["readme", "user", "guide"]
            ),
        ])

    # Testing Integration
    testing_items.extend([
        ChecklistItem(
            category="testing",
            description="Unit tests added",
            required=True,
            detected_keywords=["test", "unit"]
        ),
        ChecklistItem(
            category="testing",
            description="Integration tests added (if multiple components)",
            required=is_backend and is_frontend,
            detected_keywords=["integration", "test"]
        ),
        ChecklistItem(
            category="testing",
            description="E2E tests added (if user-facing workflow)",
            required=is_frontend and is_api,
            detected_keywords=["e2e", "test", "workflow"]
        ),
    ])

    # Always add these baseline items
    if not backend_items and not frontend_items:
        # Generic feature - add minimal checklist
        documentation_items.append(
            ChecklistItem(
                category="documentation",
                description="Code changes documented",
                required=True,
                detected_keywords=[]
            )
        )
        testing_items.append(
            ChecklistItem(
                category="testing",
                description="Changes tested",
                required=True,
                detected_keywords=[]
            )
        )

    checklist = IntegrationChecklist(
        backend_items=backend_items,
        frontend_items=frontend_items,
        database_items=database_items,
        documentation_items=documentation_items,
        testing_items=testing_items
    )

    logger.info(
        f"[IntegrationChecklist] Generated checklist: "
        f"{len(backend_items)} backend, {len(frontend_items)} frontend, "
        f"{len(database_items)} database, {len(documentation_items)} docs, "
        f"{len(testing_items)} testing items"
    )

    return checklist


def _is_backend_feature(text: str, labels: List[str]) -> bool:
    """Detect if feature involves backend work."""
    backend_keywords = ["api", "endpoint", "route", "server", "backend", "service", "database"]
    return "backend" in labels or any(kw in text for kw in backend_keywords)


def _is_frontend_feature(text: str, labels: List[str]) -> bool:
    """Detect if feature involves frontend work."""
    frontend_keywords = ["ui", "component", "page", "panel", "frontend", "client", "interface"]
    return "frontend" in labels or any(kw in text for kw in frontend_keywords)


def _is_database_feature(text: str, labels: List[str]) -> bool:
    """Detect if feature involves database changes."""
    db_keywords = ["database", "migration", "schema", "table", "sql", "query"]
    return "database" in labels or any(kw in text for kw in db_keywords)


def _is_api_feature(text: str) -> bool:
    """Detect if feature is API-related."""
    api_keywords = ["api", "endpoint", "route", "rest", "graphql"]
    return any(kw in text for kw in api_keywords)


def _is_ui_component(text: str) -> bool:
    """Detect if feature involves UI component."""
    ui_keywords = ["component", "page", "panel", "view", "ui", "interface", "dashboard"]
    return any(kw in text for kw in ui_keywords)


def _extract_keywords(text: str, keyword_list: List[str]) -> List[str]:
    """Extract keywords found in text."""
    return [kw for kw in keyword_list if kw in text]


def format_checklist_markdown(checklist: IntegrationChecklist) -> str:
    """
    Format checklist as Markdown for GitHub PR/Issue comments.

    Args:
        checklist: Integration checklist to format

    Returns:
        Markdown-formatted checklist string
    """
    lines = ["## 🔗 Integration Checklist", ""]

    def format_section(title: str, items: List[ChecklistItem]) -> List[str]:
        if not items:
            return []

        section = [f"### {title}", ""]
        for item in items:
            required = "**[REQUIRED]**" if item.required else "[OPTIONAL]"
            section.append(f"- [ ] {required} {item.description}")
            if item.notes:
                section.append(f"  - Note: {item.notes}")
        section.append("")
        return section

    lines.extend(format_section("🔧 Backend Integration", checklist.backend_items))
    lines.extend(format_section("🎨 Frontend Integration", checklist.frontend_items))
    lines.extend(format_section("💾 Database Integration", checklist.database_items))
    lines.extend(format_section("📚 Documentation Integration", checklist.documentation_items))
    lines.extend(format_section("🧪 Testing Integration", checklist.testing_items))

    lines.append("---")
    lines.append("*This checklist will be validated before shipping.*")

    return "\n".join(lines)
```

### Step 3: Create Tests (45 min)

Create new file: `adws/tests/test_integration_checklist.py`

```python
#!/usr/bin/env python3
"""
Tests for Integration Checklist Generator

Run with:
    cd adws
    pytest tests/test_integration_checklist.py -v
"""

import pytest
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.integration_checklist import (
    generate_integration_checklist,
    format_checklist_markdown,
    ChecklistItem,
    IntegrationChecklist
)


def test_backend_feature_detection():
    """Test that backend features generate appropriate checklist."""
    checklist = generate_integration_checklist(
        nl_input="Add new API endpoint for user authentication",
        issue_labels=["backend"]
    )

    assert len(checklist.backend_items) > 0
    assert any("endpoint" in item.description.lower() for item in checklist.backend_items)
    assert any("route" in item.description.lower() for item in checklist.backend_items)


def test_frontend_feature_detection():
    """Test that frontend features generate appropriate checklist."""
    checklist = generate_integration_checklist(
        nl_input="Create user profile page component",
        issue_labels=["frontend"]
    )

    assert len(checklist.frontend_items) > 0
    assert any("component" in item.description.lower() for item in checklist.frontend_items)
    assert any("navigation" in item.description.lower() for item in checklist.frontend_items)


def test_database_feature_detection():
    """Test that database features generate appropriate checklist."""
    checklist = generate_integration_checklist(
        nl_input="Add migration for user_profiles table schema",
        issue_labels=["database"]
    )

    assert len(checklist.database_items) > 0
    assert any("migration" in item.description.lower() for item in checklist.database_items)


def test_full_stack_feature():
    """Test full-stack feature generates comprehensive checklist."""
    checklist = generate_integration_checklist(
        nl_input="Add user dashboard with analytics API",
        issue_body="Create new dashboard page that displays user analytics from backend API",
        issue_labels=["frontend", "backend"]
    )

    # Should have items in multiple categories
    assert len(checklist.backend_items) > 0
    assert len(checklist.frontend_items) > 0
    assert len(checklist.testing_items) > 0
    assert len(checklist.documentation_items) > 0


def test_required_vs_optional_items():
    """Test that required items are properly flagged."""
    checklist = generate_integration_checklist(
        nl_input="Add API endpoint",
        issue_labels=["backend"]
    )

    required_items = checklist.get_required_items()
    all_items = checklist.get_all_items()

    assert len(required_items) > 0
    assert len(required_items) < len(all_items)  # Some should be optional


def test_minimal_feature():
    """Test minimal feature generates baseline checklist."""
    checklist = generate_integration_checklist(
        nl_input="Fix typo in README",
        issue_labels=[]
    )

    # Even minimal features should have some checklist items
    all_items = checklist.get_all_items()
    assert len(all_items) > 0


def test_checklist_to_dict():
    """Test serialization to dictionary."""
    checklist = generate_integration_checklist(
        nl_input="Test feature",
        issue_labels=["backend"]
    )

    data = checklist.to_dict()

    assert 'backend' in data
    assert 'frontend' in data
    assert 'database' in data
    assert 'documentation' in data
    assert 'testing' in data

    # Should be JSON-serializable
    import json
    json_str = json.dumps(data)
    assert len(json_str) > 0


def test_markdown_formatting():
    """Test Markdown formatting of checklist."""
    checklist = IntegrationChecklist(
        backend_items=[
            ChecklistItem(
                category="backend",
                description="Create API endpoint",
                required=True,
                detected_keywords=["api"]
            )
        ],
        frontend_items=[
            ChecklistItem(
                category="frontend",
                description="Create UI component",
                required=True,
                detected_keywords=["ui"]
            )
        ],
        database_items=[],
        documentation_items=[],
        testing_items=[]
    )

    markdown = format_checklist_markdown(checklist)

    assert "## 🔗 Integration Checklist" in markdown
    assert "### 🔧 Backend Integration" in markdown
    assert "### 🎨 Frontend Integration" in markdown
    assert "[REQUIRED]" in markdown
    assert "- [ ]" in markdown  # Checkbox format


def test_keyword_extraction():
    """Test that keywords are properly extracted."""
    checklist = generate_integration_checklist(
        nl_input="Add API endpoint for user authentication with JWT tokens",
        issue_labels=["backend"]
    )

    # Should detect "api" keyword in backend items
    backend_items_with_api = [
        item for item in checklist.backend_items
        if "api" in item.detected_keywords
    ]
    assert len(backend_items_with_api) > 0


def test_api_plus_ui_requires_integration_test():
    """Test that API + UI features require integration tests."""
    checklist = generate_integration_checklist(
        nl_input="Add user profile API and profile page",
        issue_labels=["backend", "frontend"]
    )

    # Should have integration test as required
    integration_test_items = [
        item for item in checklist.testing_items
        if item.required and "integration" in item.description.lower()
    ]
    assert len(integration_test_items) > 0
```

### Step 4: Integrate with Plan Phase (45 min)

**Modify `adws/adw_plan_iso.py`:**

Find the section where the plan is generated and state is saved. Add checklist generation:

```python
# Add import at top of file
from adw_modules.integration_checklist import (
    generate_integration_checklist,
    format_checklist_markdown
)

# ... in the main plan function ...

def plan_implementation(nl_input, issue_number, issue_body, issue_labels, ...):
    # ... existing planning logic ...

    # Generate integration checklist
    logger.info("[Plan] Generating integration checklist...")
    integration_checklist = generate_integration_checklist(
        nl_input=nl_input,
        issue_body=issue_body,
        issue_labels=issue_labels
    )

    # Format as markdown for PR comment
    checklist_markdown = format_checklist_markdown(integration_checklist)

    # Save to state file
    state = {
        # ... existing state fields ...
        'integration_checklist': integration_checklist.to_dict(),
        'integration_checklist_markdown': checklist_markdown
    }

    # Save state (existing code handles this)
    save_state(state)

    # Log summary
    required_items = integration_checklist.get_required_items()
    logger.info(
        f"[Plan] Integration checklist generated: "
        f"{len(required_items)} required items, "
        f"{len(integration_checklist.get_all_items())} total items"
    )

    # Optionally: Post checklist as GitHub comment on issue/PR
    # (This would be added in Ship phase to PR description)

    return state
```

**Find state file location:**

```bash
# Search for where state is saved
grep -rn "save.*state\|write.*state\|json.dump" adw_plan_iso.py

# Or look for existing state management
grep -rn "state\[" adw_plan_iso.py | head -20
```

### Step 5: Run Tests (15 min)

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws

# Run integration checklist tests
uv run pytest tests/test_integration_checklist.py -v

# Expected output:
# test_backend_feature_detection PASSED
# test_frontend_feature_detection PASSED
# test_database_feature_detection PASSED
# test_full_stack_feature PASSED
# test_required_vs_optional_items PASSED
# test_minimal_feature PASSED
# test_checklist_to_dict PASSED
# test_markdown_formatting PASSED
# test_keyword_extraction PASSED
# test_api_plus_ui_requires_integration_test PASSED
# ================== 10 passed ==================
```

If tests fail:
- Check import paths
- Verify keyword detection logic
- Review dataclass serialization
- Check markdown formatting

### Step 6: Manual Integration Test (20 min)

Test checklist generation with various scenarios:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws

# Test 1: Backend feature
uv run python -c "
from adw_modules.integration_checklist import generate_integration_checklist, format_checklist_markdown

checklist = generate_integration_checklist(
    nl_input='Add user authentication API endpoint',
    issue_labels=['backend']
)

print(format_checklist_markdown(checklist))
print(f'\nTotal items: {len(checklist.get_all_items())}')
print(f'Required items: {len(checklist.get_required_items())}')
"

# Test 2: Full-stack feature
uv run python -c "
from adw_modules.integration_checklist import generate_integration_checklist, format_checklist_markdown

checklist = generate_integration_checklist(
    nl_input='Add user profile page with API backend',
    issue_labels=['frontend', 'backend']
)

print(format_checklist_markdown(checklist))
"

# Test 3: Database feature
uv run python -c "
from adw_modules.integration_checklist import generate_integration_checklist, format_checklist_markdown

checklist = generate_integration_checklist(
    nl_input='Add migration for workflow_analytics table',
    issue_labels=['database']
)

print(format_checklist_markdown(checklist))
"
```

**Verify output:**
- Backend features should generate API endpoint, route, service items
- Frontend features should generate component, navigation items
- Full-stack features should generate integration test items
- All features should have documentation and testing items

### Step 7: Test with Real ADW Workflow (Optional - 15 min)

If you want to test with an actual ADW run:

```bash
# Create a test issue (or use existing one)
cd /Users/Warmonger0/tac/tac-webbuilder

# Run plan phase only (if such a workflow exists)
# Or run full SDLC and check state file after plan phase

# Check state file for checklist
cat agents/<adw-id>/state.json | grep -A 20 "integration_checklist"
```

### Step 8: Update Documentation (15 min)

**Update `adws/README.md`:**

Add section about Integration Checklist:

```markdown
## Integration Checklist

ADW workflows automatically generate integration checklists during the Plan phase to ensure all components are properly wired up.

### Checklist Categories

1. **Backend Integration**
   - API endpoints implemented
   - Routes registered
   - Business logic in service layer

2. **Frontend Integration**
   - UI components created
   - Navigation/routing configured
   - State management setup

3. **Database Integration**
   - Migrations created
   - Models updated
   - Repository methods implemented

4. **Documentation Integration**
   - API documentation updated
   - Feature documentation added
   - README updated (if user-facing)

5. **Testing Integration**
   - Unit tests added
   - Integration tests added
   - E2E tests added (if applicable)

### How It Works

1. **Plan Phase:** Analyzes feature requirements and generates checklist
2. **Implementation:** Developer builds feature (checklist serves as reminder)
3. **Ship Phase (Session 4):** Validates checklist items exist (warns if missing)
4. **Verify Phase (Future):** Confirms operational functionality

### Example Checklist

For a feature like "Add user profile page with API backend":

```markdown
## 🔗 Integration Checklist

### 🔧 Backend Integration
- [ ] **[REQUIRED]** API endpoint implemented
- [ ] **[REQUIRED]** API route registered in route configuration
- [ ] **[REQUIRED]** Business logic implemented in service layer

### 🎨 Frontend Integration
- [ ] **[REQUIRED]** UI component created
- [ ] **[REQUIRED]** Component added to navigation/routing
- [ ] [OPTIONAL] State management configured (if needed)

### 🧪 Testing Integration
- [ ] **[REQUIRED]** Unit tests added
- [ ] **[REQUIRED]** Integration tests added
- [ ] **[REQUIRED]** E2E tests added

### 📚 Documentation Integration
- [ ] **[REQUIRED]** API documentation updated
- [ ] **[REQUIRED]** Feature documentation added
- [ ] **[REQUIRED]** README updated
```

### Manual Checklist Generation

```bash
# Generate checklist for a feature
cd adws
uv run python -c "
from adw_modules.integration_checklist import generate_integration_checklist, format_checklist_markdown

checklist = generate_integration_checklist(
    nl_input='Your feature description',
    issue_labels=['backend', 'frontend']
)

print(format_checklist_markdown(checklist))
"
```
```

---

## Success Criteria

- ✅ IntegrationChecklist module created with dataclasses
- ✅ Checklist generation logic handles backend, frontend, database, docs, testing
- ✅ Required vs optional items properly flagged
- ✅ Markdown formatting for GitHub comments
- ✅ All 10 tests passing
- ✅ Integration with adw_plan_iso.py complete
- ✅ Checklist saved to state file for Ship phase validation
- ✅ Documentation updated with examples

---

## Files Expected to Change

**Created (2):**
- `adws/adw_modules/integration_checklist.py` (~300 lines)
- `adws/tests/test_integration_checklist.py` (~150 lines)

**Modified (2):**
- `adws/adw_plan_iso.py` (add checklist generation, ~20 lines added)
- `adws/README.md` (add Integration Checklist section)

---

## Troubleshooting

### Import Errors

```bash
# If "ModuleNotFoundError: No module named 'adw_modules'"
cd adws
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/test_integration_checklist.py -v
```

### Checklist Too Generic

If checklist doesn't detect feature type correctly:
- Add more keywords to detection functions
- Check issue_labels are being passed correctly
- Review _is_backend_feature, _is_frontend_feature logic

### State File Not Found

```bash
# Check where state files are saved
find . -name "state.json" -o -name "*.state"

# Or check adw_plan_iso.py for state save location
grep -n "state" adw_plan_iso.py | grep -i save
```

### Tests Fail on Markdown Formatting

This usually indicates:
- String escaping issues
- Missing sections in format_checklist_markdown
- Check expected vs actual output carefully

---

## Estimated Time

- Step 1 (Understand plan phase): 20 min
- Step 2 (Create checklist module): 45-60 min
- Step 3 (Create tests): 45 min
- Step 4 (Integration): 45 min
- Step 5 (Run tests): 15 min
- Step 6 (Manual test): 20 min
- Step 7 (Real workflow test): 15 min (optional)
- Step 8 (Documentation): 15 min

**Total: 2.5-3 hours**

---

## Session Completion Instructions

When you finish this session, provide a completion summary in this **EXACT FORMAT:**

```markdown
## ✅ Session 3 Complete - Integration Checklist (Plan Phase)

**Duration:** ~X hours
**Status:** Complete ✅
**Next:** Ready for Session 4 (Integration Checklist - Ship Phase)

### What Was Done

1. **Integration Checklist Module Created**
   - Created adw_modules/integration_checklist.py (~300 lines)
   - Dataclass-based checklist with 5 categories
   - Smart feature detection (backend, frontend, database, API, UI)
   - Required vs optional item flagging

2. **Comprehensive Tests**
   - Created tests/test_integration_checklist.py (10 tests)
   - All tests passing ✅
   - Coverage: backend, frontend, database, full-stack, minimal features

3. **Plan Phase Integration**
   - Modified adw_plan_iso.py to generate checklist
   - Checklist saved to state file (JSON format)
   - Markdown formatting for GitHub PR comments

4. **Documentation Updated**
   - Added Integration Checklist section to adws/README.md
   - Included examples and manual generation instructions

### Key Results

- ✅ Automatic checklist generation for all feature types
- ✅ 5 integration categories (backend, frontend, database, docs, testing)
- ✅ Required/optional distinction for validation flexibility
- ✅ Markdown-formatted output for GitHub integration
- ✅ Persisted to state file for Ship phase validation (Session 4)

### Files Changed

**Created (2):**
- adws/adw_modules/integration_checklist.py
- adws/tests/test_integration_checklist.py

**Modified (2):**
- adws/adw_plan_iso.py
- adws/README.md

### Test Results

```
pytest tests/test_integration_checklist.py -v
================== 10 passed ==================
```

### Example Output

Backend feature checklist:
- [x] Backend: API endpoint implemented (REQUIRED)
- [x] Backend: API route registered (REQUIRED)
- [x] Backend: Business logic in service layer (REQUIRED)
- [x] Testing: Unit tests added (REQUIRED)
- [x] Documentation: API documentation updated (REQUIRED)

### Next Session

Session 4: Integration Checklist - Ship Phase (2-3 hours)
- Modify adw_ship_iso.py to validate checklist items
- Check: API endpoint exists, UI component exists, routes configured
- Warn only (don't block) - Review phase already validated code quality
- Add warnings to PR comments with checklist status
```

---

## Next Session Prompt Instructions

After providing the completion summary above, create the prompt for **Session 4: Integration Checklist - Ship Phase** using this template:

### Template for SESSION_4_PROMPT.md

```markdown
# Task: Validate Integration Checklist in Ship Phase

## Context
I'm working on the tac-webbuilder project. Session 3 implemented integration checklist generation in the Plan phase. This session adds checklist validation to the Ship phase to verify that planned integration points were actually implemented.

## Objective
Modify `adw_ship_iso.py` to validate integration checklist items before shipping. Validation should **warn only** (not block) since the Review phase has already validated code quality. Warnings will be added to PR comments to alert developers of potentially missing integration.

## Background Information
- **Session 3 Output:** Integration checklist stored in state file with 5 categories
- **Validation Strategy:** Check for file existence, grep for patterns, verify routes
- **Error Handling:** Warn only - don't fail the workflow
- **Output:** Add warnings to PR comment with checklist status

[... continue with full session structure ...]

## Session Completion Instructions
[Same format as Session 3]

## Next Session Prompt Instructions
[Continue the chain with Session 5...]
```

**Save this prompt as:** `/Users/Warmonger0/tac/tac-webbuilder/SESSION_4_PROMPT.md`

---

**Ready to copy into a new chat!**

Run `/prime` first, then paste this entire prompt.
