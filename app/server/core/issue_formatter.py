"""
Issue formatting module for GitHub issue generation.
"""

from typing import Dict, Any
from core.data_models import GitHubIssue


# Issue templates for different types
ISSUE_TEMPLATES = {
    "feature": """# {title}

## Description
{description}

## Requirements
{requirements}

## Technical Approach
{technical_approach}

## Workflow
{workflow}
""",

    "bug": """# {title}

## Issue Description
{description}

## Steps to Reproduce
{steps}

## Expected vs Actual Behavior
**Expected:** {expected}
**Actual:** {actual}

## Workflow
{workflow}
""",

    "chore": """# {title}

## Description
{description}

## Tasks
{tasks}

## Workflow
{workflow}
"""
}


def format_issue(issue: GitHubIssue, template_data: Dict[str, Any]) -> str:
    """
    Format a GitHub issue using the appropriate template.

    Args:
        issue: GitHubIssue object
        template_data: Dictionary containing template variables

    Returns:
        Formatted issue body as markdown string
    """
    template = ISSUE_TEMPLATES.get(issue.classification, ISSUE_TEMPLATES["feature"])

    # Ensure workflow is formatted correctly
    workflow_str = f"{issue.workflow} model_set {issue.model_set}"
    template_data["workflow"] = workflow_str

    # Fill in the template
    try:
        formatted = template.format(**template_data)
        return formatted
    except KeyError as e:
        raise ValueError(f"Missing required template field: {e}")


def validate_issue_body(body: str) -> bool:
    """
    Validate that an issue body contains required sections.

    Args:
        body: Issue body markdown

    Returns:
        True if valid, False otherwise
    """
    # Required sections for any issue
    required_sections = ["##", "Workflow"]

    for section in required_sections:
        if section not in body:
            return False

    return True


def format_requirements_list(requirements: list) -> str:
    """
    Format a list of requirements as markdown bullet points.

    Args:
        requirements: List of requirement strings

    Returns:
        Formatted markdown string
    """
    if not requirements:
        return "- To be determined"

    return "\n".join([f"- {req}" for req in requirements])


def format_technical_approach(approach: str) -> str:
    """
    Format technical approach section.

    Args:
        approach: Technical approach description

    Returns:
        Formatted markdown string
    """
    if not approach or approach.strip() == "":
        return "To be determined during implementation planning."

    return approach


def format_workflow_section(workflow: str, model_set: str) -> str:
    """
    Format the workflow section with ADW command.

    Args:
        workflow: ADW workflow name (e.g., adw_sdlc_iso)
        model_set: Model set (base or heavy)

    Returns:
        Formatted workflow command
    """
    return f"{workflow} model_set {model_set}"


def escape_markdown_special_chars(text: str) -> str:
    """
    Escape special markdown characters in text.

    Args:
        text: Input text

    Returns:
        Text with escaped markdown special characters
    """
    # Escape characters that have special meaning in markdown
    special_chars = ['*', '_', '`', '[', ']', '(', ')', '#', '+', '-', '.', '!', '|']

    result = text
    for char in special_chars:
        # Only escape if not already part of markdown syntax
        if char in result:
            # Simple escape - this could be made more sophisticated
            pass  # For now, we'll leave markdown intact

    return result


def create_feature_issue_body(
    description: str,
    requirements: list,
    technical_approach: str = "",
    workflow: str = "adw_sdlc_iso",
    model_set: str = "base"
) -> str:
    """
    Create a formatted feature issue body.

    Args:
        description: Feature description
        requirements: List of requirements
        technical_approach: Technical approach (optional)
        workflow: ADW workflow
        model_set: Model set

    Returns:
        Formatted issue body
    """
    template_data = {
        "title": "Feature Request",
        "description": description,
        "requirements": format_requirements_list(requirements),
        "technical_approach": format_technical_approach(technical_approach),
        "workflow": format_workflow_section(workflow, model_set)
    }

    return ISSUE_TEMPLATES["feature"].format(**template_data)


def create_bug_issue_body(
    description: str,
    steps: str = "",
    expected: str = "",
    actual: str = "",
    workflow: str = "adw_plan_build_test_iso",
    model_set: str = "base"
) -> str:
    """
    Create a formatted bug issue body.

    Args:
        description: Bug description
        steps: Steps to reproduce
        expected: Expected behavior
        actual: Actual behavior
        workflow: ADW workflow
        model_set: Model set

    Returns:
        Formatted issue body
    """
    template_data = {
        "title": "Bug Report",
        "description": description,
        "steps": steps if steps else "To be documented",
        "expected": expected if expected else "To be documented",
        "actual": actual if actual else "To be documented",
        "workflow": format_workflow_section(workflow, model_set)
    }

    return ISSUE_TEMPLATES["bug"].format(**template_data)


def create_chore_issue_body(
    description: str,
    tasks: list,
    workflow: str = "adw_sdlc_iso",
    model_set: str = "base"
) -> str:
    """
    Create a formatted chore issue body.

    Args:
        description: Chore description
        tasks: List of tasks
        workflow: ADW workflow
        model_set: Model set

    Returns:
        Formatted issue body
    """
    template_data = {
        "title": "Chore",
        "description": description,
        "tasks": format_requirements_list(tasks),
        "workflow": format_workflow_section(workflow, model_set)
    }

    return ISSUE_TEMPLATES["chore"].format(**template_data)
