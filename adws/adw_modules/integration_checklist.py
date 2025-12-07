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
