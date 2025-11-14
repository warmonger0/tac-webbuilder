"""
Plan parser for ADW workflows.

Extracts structured YAML configuration from AI-generated comprehensive plans.
"""

import re
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class WorkflowConfig:
    """Parsed workflow configuration from comprehensive plan."""

    # Issue classification
    issue_type: str  # feature, bug, or chore

    # Project detection
    project_context: str  # tac-7-root or tac-webbuilder
    requires_worktree: bool
    confidence: str  # high, medium, low
    detection_reasoning: str

    # Branch naming
    branch_name: str

    # Worktree setup (optional)
    worktree_setup: Optional[Dict[str, Any]] = None

    # Commit message
    commit_message: str = ""

    # Validation criteria
    validation_criteria: list = None

    # Plan file path
    plan_file_path: str = ""

    def __post_init__(self):
        if self.validation_criteria is None:
            self.validation_criteria = []


def extract_yaml_block(text: str) -> Optional[str]:
    """
    Extract YAML configuration block from AI response.

    Looks for:
    ```yaml
    ...
    ```

    Returns the YAML content without the fence markers.
    """
    # Pattern to match ```yaml ... ```
    pattern = r'```yaml\s*\n(.*?)\n```'
    match = re.search(pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()

    # Fallback: look for WORKFLOW CONFIGURATION header
    pattern = r'# WORKFLOW CONFIGURATION.*?\n(.*?)(?=\n#[^#]|\n```|\Z)'
    match = re.search(pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()

    return None


def extract_plan_file_path(text: str) -> Optional[str]:
    """
    Extract plan file path from AI response.

    Looks for patterns like:
    - "Plan file: specs/issue-123-adw-abc12345-sdlc_planner-feature-name.md"
    - Created file at specs/...
    - Saved to specs/...
    """
    patterns = [
        r'Plan file:\s*`?([^`\n]+\.md)`?',
        r'Created file at\s*`?([^`\n]+\.md)`?',
        r'Saved to\s*`?([^`\n]+\.md)`?',
        r'specs/issue-\d+-adw-[a-f0-9]+-sdlc_planner-[^\.]+\.md'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if pattern == patterns[-1]:
                # Full match
                return match.group(0)
            else:
                # Capture group
                return match.group(1).strip()

    return None


def parse_plan(plan_text: str) -> WorkflowConfig:
    """
    Parse comprehensive plan from AI response.

    Extracts YAML configuration block and creates WorkflowConfig object.

    Args:
        plan_text: Full text response from AI agent

    Returns:
        WorkflowConfig object with all parsed configuration

    Raises:
        ValueError: If YAML block is missing or invalid
    """
    # Extract YAML block
    yaml_text = extract_yaml_block(plan_text)

    if not yaml_text:
        raise ValueError(
            "No YAML configuration block found in plan. "
            "Expected ```yaml ... ``` block at start of response."
        )

    # Parse YAML
    try:
        config_dict = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML syntax in configuration block: {e}")

    # Extract plan file path
    plan_file_path = extract_plan_file_path(plan_text)

    # Build WorkflowConfig
    try:
        workflow_config = WorkflowConfig(
            issue_type=config_dict.get('issue_type', 'chore'),
            project_context=config_dict.get('project_context', 'tac-7-root'),
            requires_worktree=config_dict.get('requires_worktree', False),
            confidence=config_dict.get('confidence', 'low'),
            detection_reasoning=config_dict.get('detection_reasoning', 'No reasoning provided'),
            branch_name=config_dict.get('branch_name', ''),
            worktree_setup=config_dict.get('worktree_setup'),
            commit_message=config_dict.get('commit_message', ''),
            validation_criteria=config_dict.get('validation_criteria', []),
            plan_file_path=plan_file_path or ""
        )
    except Exception as e:
        raise ValueError(f"Error building WorkflowConfig: {e}\n\nConfig dict: {config_dict}")

    # Validate required fields
    if not workflow_config.branch_name:
        raise ValueError("branch_name is required but not found in YAML configuration")

    if not workflow_config.issue_type:
        raise ValueError("issue_type is required but not found in YAML configuration")

    return workflow_config


def validate_workflow_config(config: WorkflowConfig) -> list[str]:
    """
    Validate workflow configuration for correctness.

    Returns list of validation errors (empty if valid).
    """
    errors = []

    # Validate issue_type
    if config.issue_type not in ['feature', 'bug', 'chore']:
        errors.append(f"Invalid issue_type: {config.issue_type}. Must be feature, bug, or chore.")

    # Validate project_context
    if config.project_context not in ['tac-7-root', 'tac-webbuilder']:
        errors.append(
            f"Invalid project_context: {config.project_context}. "
            f"Must be tac-7-root or tac-webbuilder."
        )

    # Validate confidence
    if config.confidence not in ['high', 'medium', 'low']:
        errors.append(f"Invalid confidence: {config.confidence}. Must be high, medium, or low.")

    # Validate branch name format
    branch_pattern = r'^(feat|fix|chore)-issue-\d+-adw-[a-f0-9]{8}-.+$'
    if not re.match(branch_pattern, config.branch_name):
        errors.append(
            f"Invalid branch_name format: {config.branch_name}. "
            f"Expected: {{type}}-issue-{{num}}-adw-{{id}}-{{slug}}"
        )

    # Validate worktree_setup if requires_worktree is True
    if config.requires_worktree:
        if not config.worktree_setup:
            errors.append("requires_worktree is true but worktree_setup is missing")
        else:
            # Check required fields
            if 'backend_port' not in config.worktree_setup:
                errors.append("worktree_setup missing required field: backend_port")
            if 'frontend_port' not in config.worktree_setup:
                errors.append("worktree_setup missing required field: frontend_port")
            if 'steps' not in config.worktree_setup:
                errors.append("worktree_setup missing required field: steps")

    return errors


# Example usage and testing
if __name__ == "__main__":
    # Test with sample YAML
    sample_plan = """
Here's the comprehensive plan:

```yaml
# WORKFLOW CONFIGURATION

issue_type: feature

project_context: tac-7-root
requires_worktree: false
confidence: high
detection_reasoning: "Issue mentions scripts/ directory"

branch_name: feat-issue-123-adw-abc12345-add-logging

commit_message: |
  feat: add logging to ADW workflow

  ADW: abc12345
  Issue: #123

validation_criteria:
  - check: "Branch created"
    expected: "feat-issue-123-adw-abc12345-add-logging"
```

# Feature: Add Logging

... rest of plan ...

Plan file: specs/issue-123-adw-abc12345-sdlc_planner-add-logging.md
"""

    try:
        config = parse_plan(sample_plan)
        print("✓ Parsed successfully!")
        print(f"  Issue type: {config.issue_type}")
        print(f"  Project context: {config.project_context}")
        print(f"  Branch name: {config.branch_name}")
        print(f"  Requires worktree: {config.requires_worktree}")
        print(f"  Plan file: {config.plan_file_path}")

        # Validate
        errors = validate_workflow_config(config)
        if errors:
            print("\n✗ Validation errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("\n✓ Validation passed!")

    except ValueError as e:
        print(f"✗ Parse error: {e}")
