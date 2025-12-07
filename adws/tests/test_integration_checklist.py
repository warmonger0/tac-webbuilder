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
