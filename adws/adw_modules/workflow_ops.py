"""Shared AI Developer Workflow (ADW) operations."""

import glob
import json
import logging
import os
import subprocess
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime
from typing import Tuple, Optional, Dict, Any, List
from adw_modules.data_types import (
    AgentTemplateRequest,
    GitHubIssue,
    AgentPromptResponse,
    IssueClassSlashCommand,
    ADWExtractionResult,
)
from adw_modules.agent import execute_template
from adw_modules.github import get_repo_url, extract_repo_path, ADW_BOT_IDENTIFIER
from adw_modules.state import ADWState
from adw_modules.utils import parse_json


def validate_issue_number(issue_number: str) -> int:
    """Validate and convert issue_number to integer.

    Args:
        issue_number: The issue number as a string

    Returns:
        The validated issue number as an integer

    Raises:
        ValueError: If issue_number is not a valid positive integer
    """
    try:
        issue_num = int(issue_number)
        if issue_num <= 0:
            raise ValueError(f"Issue number must be a positive integer, got: {issue_number}")
        return issue_num
    except (ValueError, TypeError) as e:
        if isinstance(e, ValueError) and "positive integer" in str(e):
            raise
        raise ValueError(
            f"Invalid issue number '{issue_number}'. Expected a positive integer (e.g., 39), "
            f"not '{issue_number}'. If you need help, use --help flag."
        )


def trigger_cost_sync(adw_id: str, logger: Optional[logging.Logger] = None) -> bool:
    """
    Trigger cost synchronization for a completed workflow.

    Calls the backend API to resync cost data from raw_output.jsonl files.

    Args:
        adw_id: The ADW workflow identifier
        logger: Optional logger instance

    Returns:
        True if sync was successful, False otherwise
    """
    backend_port = os.environ.get("BACKEND_PORT", "8000")
    api_url = f"http://localhost:{backend_port}/api/workflow-history/resync"

    try:
        # Create request payload
        payload = json.dumps({"adw_id": adw_id, "force": False}).encode('utf-8')

        # Make POST request
        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))

            if result.get("success"):
                if logger:
                    logger.info(f"✅ Cost sync successful for {adw_id}")
                else:
                    print(f"✅ Cost sync successful for {adw_id}")
                return True
            else:
                if logger:
                    logger.warning(f"⚠️ Cost sync returned success=False for {adw_id}")
                else:
                    print(f"⚠️ Cost sync returned success=False for {adw_id}")
                return False

    except urllib.error.URLError as e:
        if logger:
            logger.debug(f"Cost sync API not available: {e}")
        else:
            print(f"Note: Cost sync skipped (API not available): {e}")
        return False
    except Exception as e:
        if logger:
            logger.debug(f"Cost sync failed: {e}")
        else:
            print(f"Note: Cost sync failed: {e}")
        return False


# Agent name constants
AGENT_PLANNER = "sdlc_planner"
AGENT_IMPLEMENTOR = "sdlc_implementor"
AGENT_CLASSIFIER = "issue_classifier"
AGENT_BRANCH_GENERATOR = "branch_generator"
AGENT_PR_CREATOR = "pr_creator"

# Available ADW workflows for runtime validation
AVAILABLE_ADW_WORKFLOWS = [
    # Single-phase workflows
    "adw_plan_iso",
    "adw_plan_iso_optimized",
    "adw_patch_iso",
    "adw_build_iso",
    "adw_test_iso",
    "adw_review_iso",
    "adw_document_iso",
    "adw_ship_iso",
    "adw_cleanup_iso",
    "adw_lint_iso",

    # Multi-phase workflows
    "adw_lightweight_iso",  # Optimized for simple changes ($0.20-0.50)
    "adw_plan_build_iso",
    "adw_plan_build_test_iso",
    "adw_plan_build_test_review_iso",
    "adw_plan_build_document_iso",
    "adw_plan_build_review_iso",
    "adw_stepwise_iso",

    # Full SDLC workflows
    "adw_sdlc_iso",
    "adw_sdlc_complete_iso",
    "adw_sdlc_ZTE_iso",  # Zero Touch Execution workflow
    "adw_sdlc_complete_zte_iso",  # Complete Zero Touch Execution with optimized plan
]


def format_issue_message(
    adw_id: str, agent_name: str, message: str, session_id: Optional[str] = None
) -> str:
    """Format a message for issue comments with ADW tracking and bot identifier."""
    # Always include ADW_BOT_IDENTIFIER to prevent webhook loops
    if session_id:
        return f"{ADW_BOT_IDENTIFIER} {adw_id}_{agent_name}_{session_id}: {message}"
    return f"{ADW_BOT_IDENTIFIER} {adw_id}_{agent_name}: {message}"


def create_context_file(
    worktree_path: str,
    adw_id: str,
    context_data: Dict[str, Any],
    logger: Optional[logging.Logger] = None
) -> str:
    """Create a .adw-context.json file in the worktree root with runtime context.

    This file provides pre-computed paths and context to agents, eliminating the need
    for agents to run git commands or discover files themselves.

    Args:
        worktree_path: Absolute path to the worktree root
        adw_id: ADW workflow ID
        context_data: Dictionary of context to write (will be merged with defaults)
        logger: Optional logger instance

    Returns:
        Absolute path to the created context file

    Example:
        create_context_file(
            "/path/to/trees/adw-12345678",
            "adw-12345678",
            {
                "spec_file": "/abs/path/to/spec.md",
                "changed_files": ["file1.py", "file2.tsx"],
                "patch_file_path": "specs/patch/patch-adw-12345678.md"
            }
        )
    """
    # Ensure worktree_path is absolute
    if not os.path.isabs(worktree_path):
        worktree_path = os.path.abspath(worktree_path)

    # Build context with defaults
    context = {
        "adw_id": adw_id,
        "worktree_path": worktree_path,
        "created_at": datetime.now().isoformat(),
    }

    # Merge with provided context
    context.update(context_data)

    # Write to worktree root as hidden file
    context_file = os.path.join(worktree_path, ".adw-context.json")

    with open(context_file, "w") as f:
        json.dump(context, f, indent=2)

    if logger:
        logger.info(f"Created context file: {context_file}")
        logger.debug(f"Context data: {json.dumps(context, indent=2)}")

    return context_file


def extract_adw_info_simple(text: str) -> ADWExtractionResult:
    """Fast regex-based extraction - no AI needed.

    Patterns supported:
    - adw_plan_iso
    - adw_plan_iso with base model
    - adw_plan_iso with advanced model
    - adw_build_iso adw-12345678
    - adw_build_iso adw-12345678 with advanced model
    """
    # Pattern: (adw_<workflow>) [adw-<id>] [with <model_set> model]
    # Make it case-insensitive and flexible with whitespace
    pattern = r'(adw_\w+)(?:\s+(adw-[a-f0-9]{8}))?(?:\s+with\s+(\w+)\s+model)?'

    matches = list(re.finditer(pattern, text.lower()))

    if matches:
        # Use first match
        match = matches[0]
        workflow_lower = match.group(1)
        adw_id = match.group(2)  # Optional, may be None
        model_set = match.group(3) or "base"  # Default to base

        # Validate workflow exists (case-insensitive match)
        matching_workflow = None
        for workflow in AVAILABLE_ADW_WORKFLOWS:
            if workflow_lower == workflow.lower():
                matching_workflow = workflow
                break

        if matching_workflow:
            return ADWExtractionResult(
                workflow_command=matching_workflow,
                adw_id=adw_id,
                model_set=model_set,
                has_workflow=True
            )

    return ADWExtractionResult()  # No match


def extract_adw_info(text: str, temp_adw_id: str) -> ADWExtractionResult:
    """Extract ADW workflow, ID, and model_set from text.

    Uses fast regex extraction first, falls back to AI classifier if needed.
    Returns ADWExtractionResult with workflow_command, adw_id, and model_set.
    """

    # Try fast regex extraction first (99% of cases)
    result = extract_adw_info_simple(text)
    if result.has_workflow:
        print(f"✅ Fast extraction found: {result.workflow_command} (model_set: {result.model_set})")
        return result

    # Fall back to AI classifier for complex/ambiguous cases
    print(f"⚠️ Fast extraction failed, falling back to AI classifier...")

    # Use classify_adw to extract structured info
    request = AgentTemplateRequest(
        agent_name="adw_classifier",
        slash_command="/classify_adw",
        args=[text],
        adw_id=temp_adw_id,
    )

    try:
        response = execute_template(request)  # No logger available in this function

        if not response.success:
            print(f"Failed to classify ADW: {response.output}")
            return ADWExtractionResult()  # Empty result

        # Parse JSON response using utility that handles markdown
        try:
            data = parse_json(response.output, dict)
            adw_command = data.get("adw_slash_command", "").replace(
                "/", ""
            )  # Remove slash
            adw_id = data.get("adw_id")
            model_set = data.get("model_set", "base")  # Default to "base"

            # Validate command (case-insensitive)
            if adw_command:
                # Check if command matches any workflow (case-insensitive)
                matching_workflow = None
                for workflow in AVAILABLE_ADW_WORKFLOWS:
                    if adw_command.lower() == workflow.lower():
                        matching_workflow = workflow
                        break

                if matching_workflow:
                    return ADWExtractionResult(
                        workflow_command=matching_workflow,  # Use canonical form
                        adw_id=adw_id,
                        model_set=model_set
                    )

            return ADWExtractionResult()  # Empty result

        except ValueError as e:
            print(f"Failed to parse classify_adw response: {e}")
            return ADWExtractionResult()  # Empty result

    except Exception as e:
        print(f"Error calling classify_adw: {e}")
        return ADWExtractionResult()  # Empty result


def classify_issue(
    issue: GitHubIssue, adw_id: str, logger: logging.Logger
) -> Tuple[Optional[IssueClassSlashCommand], Optional[str]]:
    """Classify GitHub issue and return appropriate slash command.
    Returns (command, error_message) tuple."""

    # Use the classify_issue slash command template with minimal payload
    # Only include the essential fields: number, title, body
    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    request = AgentTemplateRequest(
        agent_name=AGENT_CLASSIFIER,
        slash_command="/classify_issue",
        args=[minimal_issue_json],
        adw_id=adw_id,
    )

    logger.debug(f"Classifying issue: {issue.title}")

    response = execute_template(request)

    logger.debug(
        f"Classification response: {response.model_dump_json(indent=2, by_alias=True)}"
    )

    if not response.success:
        return None, response.output

    # Extract the classification from the response
    output = response.output.strip()

    # Look for the classification pattern in the output
    # Claude might add explanation, so we need to extract just the command
    classification_match = re.search(r"(/chore|/bug|/feature|0)", output)

    if classification_match:
        issue_command = classification_match.group(1)
    else:
        issue_command = output

    if issue_command == "0":
        return None, f"No command selected: {response.output}"

    if issue_command not in ["/chore", "/bug", "/feature"]:
        return None, f"Invalid command selected: {response.output}"

    return issue_command, None  # type: ignore


def build_plan(
    issue: GitHubIssue,
    command: str,
    adw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
    plan_file_path: Optional[str] = None,
    state: Optional[ADWState] = None,
) -> AgentPromptResponse:
    """Build implementation plan for the issue using the specified command."""
    # Use minimal payload like classify_issue does
    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    # Optionally create context file for planning (minimal - just worktree info)
    worktree_path = working_dir or os.getcwd()
    context_data = {}

    if state:
        if state.get("backend_port"):
            context_data["backend_port"] = state.get("backend_port")
        if state.get("frontend_port"):
            context_data["frontend_port"] = state.get("frontend_port")

    # Only create context file if we have useful data
    if context_data:
        create_context_file(worktree_path, adw_id, context_data, logger)

    # Build args list - include plan_file_path if provided
    args = [str(issue.number), adw_id, minimal_issue_json]
    if plan_file_path:
        args.append(plan_file_path)

    issue_plan_template_request = AgentTemplateRequest(
        agent_name=AGENT_PLANNER,
        slash_command=command,
        args=args,
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"issue_plan_template_request: {issue_plan_template_request.model_dump_json(indent=2, by_alias=True)}"
    )

    issue_plan_response = execute_template(issue_plan_template_request)

    logger.debug(
        f"issue_plan_response: {issue_plan_response.model_dump_json(indent=2, by_alias=True)}"
    )

    return issue_plan_response


def implement_plan(
    plan_file: str,
    adw_id: str,
    logger: logging.Logger,
    agent_name: Optional[str] = None,
    working_dir: Optional[str] = None,
    state: Optional[ADWState] = None,
) -> AgentPromptResponse:
    """Implement the plan using the /implement command."""
    # Use provided agent_name or default to AGENT_IMPLEMENTOR
    implementor_name = agent_name or AGENT_IMPLEMENTOR

    # Create context file with available information
    worktree_path = working_dir or os.getcwd()
    context_data = {}

    # Add state information if available
    if state:
        if state.get("spec_file"):
            context_data["spec_file"] = state.get("spec_file")
        if state.get("backend_port"):
            context_data["backend_port"] = state.get("backend_port")
        if state.get("frontend_port"):
            context_data["frontend_port"] = state.get("frontend_port")

    # Pre-compute changed files if in a git repository
    try:
        result = subprocess.run(
            ["git", "diff", "origin/main", "--name-only"],
            capture_output=True,
            text=True,
            cwd=worktree_path,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            context_data["changed_files"] = result.stdout.strip().split('\n')
    except Exception as e:
        logger.debug(f"Could not get changed files: {e}")

    # Only create context file if we have data
    if context_data:
        create_context_file(worktree_path, adw_id, context_data, logger)

    implement_template_request = AgentTemplateRequest(
        agent_name=implementor_name,
        slash_command="/implement",
        args=[plan_file],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"implement_template_request: {implement_template_request.model_dump_json(indent=2, by_alias=True)}"
    )

    implement_response = execute_template(implement_template_request)

    logger.debug(
        f"implement_response: {implement_response.model_dump_json(indent=2, by_alias=True)}"
    )

    return implement_response


def generate_branch_name(
    issue: GitHubIssue,
    issue_class: IssueClassSlashCommand,
    adw_id: str,
    logger: logging.Logger,
) -> Tuple[Optional[str], Optional[str]]:
    """Generate a git branch name for the issue.
    Returns (branch_name, error_message) tuple."""
    # Remove the leading slash from issue_class for the branch name
    issue_type = issue_class.replace("/", "")

    # Use minimal payload like classify_issue does
    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    request = AgentTemplateRequest(
        agent_name=AGENT_BRANCH_GENERATOR,
        slash_command="/generate_branch_name",
        args=[issue_type, adw_id, minimal_issue_json],
        adw_id=adw_id,
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    branch_name = response.output.strip()
    logger.info(f"Generated branch name: {branch_name}")
    return branch_name, None


def create_commit(
    agent_name: str,
    issue: GitHubIssue,
    issue_class: IssueClassSlashCommand,
    adw_id: str,
    logger: logging.Logger,
    working_dir: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a git commit with a properly formatted message using deterministic Python.

    DEPRECATED AI CALL: This function now uses commit_generator.py instead of /commit command.
    Returns (commit_message, error_message) tuple.
    """
    # Import here to avoid circular imports
    from adw_modules.commit_generator import generate_commit_message

    # Remove the leading slash from issue_class
    issue_type = issue_class.replace("/", "")

    # Generate commit message using Python template
    commit_message = generate_commit_message(agent_name, issue_type, issue)

    logger.info(f"Generated commit message (Python): {commit_message}")
    return commit_message, None


def create_pull_request(
    branch_name: str,
    issue: Optional[GitHubIssue],
    state: ADWState,
    logger: logging.Logger,
    working_dir: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a pull request for the implemented changes.
    Returns (pr_url, error_message) tuple."""

    # Get plan file from state (may be None for test runs)
    plan_file = state.get("plan_file") or "No plan file (test run)"
    adw_id = state.get("adw_id")

    # PRE-COMPUTE PR context (deterministic Python, no AI needed)
    # Get changed files
    result = subprocess.run(
        ["git", "diff", "origin/main...HEAD", "--name-only"],
        capture_output=True,
        text=True,
        cwd=working_dir,
        timeout=5
    )
    changed_files = result.stdout.strip().split('\n') if result.returncode == 0 and result.stdout.strip() else []

    # Get commits
    result = subprocess.run(
        ["git", "log", "origin/main..HEAD", "--oneline"],
        capture_output=True,
        text=True,
        cwd=working_dir,
        timeout=5
    )
    commits = []
    if result.returncode == 0 and result.stdout.strip():
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split(' ', 1)
                sha = parts[0]
                message = parts[1] if len(parts) > 1 else ""
                commits.append({"sha": sha, "message": message})

    # Create context file with PR data
    context_data = {
        "branch_name": branch_name,
        "changed_files": changed_files,
        "commits": commits,
        "plan_file": plan_file,
    }

    # Add issue data to context
    if not issue:
        issue_data = state.get("issue", {})
        context_data["issue"] = issue_data if issue_data else {}
    elif isinstance(issue, dict):
        context_data["issue"] = issue
    else:
        # Use mode='json' to properly serialize datetime fields to ISO strings
        context_data["issue"] = issue.model_dump(by_alias=True, mode='json')

    # Create context file
    create_context_file(working_dir, adw_id, context_data, logger)

    # Simplified request - agent reads everything from context
    request = AgentTemplateRequest(
        agent_name=AGENT_PR_CREATOR,
        slash_command="/pull_request",
        args=[adw_id],  # Just need ADW ID!
        adw_id=adw_id,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    pr_url = response.output.strip()
    logger.info(f"Created pull request: {pr_url}")
    return pr_url, None


def ensure_plan_exists(state: ADWState, issue_number: str) -> str:
    """Find or error if no plan exists for issue.
    Used by isolated build workflows in standalone mode."""
    # Check if plan file is in state
    if state.get("plan_file"):
        return state.get("plan_file")

    # Check current branch
    from adw_modules.git_ops import get_current_branch

    branch = get_current_branch()

    # Look for plan in branch name
    if f"-{issue_number}-" in branch:
        # Look for plan file
        plans = glob.glob(f"specs/*{issue_number}*.md")
        if plans:
            return plans[0]

    # No plan found
    raise ValueError(
        f"No plan found for issue {issue_number}. Run adw_plan_iso.py first."
    )


def ensure_adw_id(
    issue_number: str,
    adw_id: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Get ADW ID or create a new one and initialize state.

    Args:
        issue_number: The issue number to find/create ADW ID for
        adw_id: Optional existing ADW ID to use
        logger: Optional logger instance

    Returns:
        The ADW ID (existing or newly created)

    Raises:
        ValueError: If issue_number is not a valid positive integer
    """
    # Validate issue_number first
    try:
        validated_issue_number = validate_issue_number(issue_number)
        issue_number_str = str(validated_issue_number)
    except ValueError as e:
        if logger:
            logger.error(str(e))
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
        raise

    # If ADW ID provided, check if state exists
    if adw_id:
        state = ADWState.load(adw_id, logger)
        if state:
            if logger:
                logger.info(f"Found existing ADW state for ID: {adw_id}")
            else:
                print(f"Found existing ADW state for ID: {adw_id}")
            return adw_id
        # ADW ID provided but no state exists, create state
        state = ADWState(adw_id)
        state.update(adw_id=adw_id, issue_number=issue_number_str)
        state.save("ensure_adw_id")
        if logger:
            logger.info(f"Created new ADW state for provided ID: {adw_id}")
        else:
            print(f"Created new ADW state for provided ID: {adw_id}")
        return adw_id

    # No ADW ID provided, create new one with state
    from adw_modules.utils import make_adw_id

    new_adw_id = make_adw_id()
    state = ADWState(new_adw_id)
    state.update(adw_id=new_adw_id, issue_number=issue_number_str)
    state.save("ensure_adw_id")
    if logger:
        logger.info(f"Created new ADW ID and state: {new_adw_id}")
    else:
        print(f"Created new ADW ID and state: {new_adw_id}")
    return new_adw_id


def find_existing_branch_for_issue(
    issue_number: str, adw_id: Optional[str] = None, cwd: Optional[str] = None
) -> Optional[str]:
    """Find an existing branch for the given issue number.
    Returns branch name if found, None otherwise."""
    # List all branches
    result = subprocess.run(
        ["git", "branch", "-a"], capture_output=True, text=True, cwd=cwd
    )

    if result.returncode != 0:
        return None

    branches = result.stdout.strip().split("\n")

    # Look for branch with standardized pattern: *-issue-{issue_number}-adw-{adw_id}-*
    for branch in branches:
        branch = branch.strip().replace("* ", "").replace("remotes/origin/", "")
        # Check for the standardized pattern
        if f"-issue-{issue_number}-" in branch:
            if adw_id and f"-adw-{adw_id}-" in branch:
                return branch
            elif not adw_id:
                # Return first match if no adw_id specified
                return branch

    return None


def create_or_find_branch(
    issue_number: str,
    issue: GitHubIssue,
    state: ADWState,
    logger: logging.Logger,
    cwd: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    """Create or find a branch for the given issue.

    1. First checks state for existing branch name
    2. Then looks for existing branches matching the issue
    3. If none found, classifies the issue and creates a new branch

    Returns (branch_name, error_message) tuple.
    """
    # 1. Check state for branch name
    branch_name = state.get("branch_name") or state.get("branch", {}).get("name")
    if branch_name:
        logger.info(f"Found branch in state: {branch_name}")
        # Check if we need to checkout
        from adw_modules.git_ops import get_current_branch

        current = get_current_branch(cwd=cwd)
        if current != branch_name:
            result = subprocess.run(
                ["git", "checkout", branch_name],
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            if result.returncode != 0:
                # Branch might not exist locally, try to create from remote
                result = subprocess.run(
                    ["git", "checkout", "-b", branch_name, f"origin/{branch_name}"],
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                )
                if result.returncode != 0:
                    return "", f"Failed to checkout branch: {result.stderr}"
        return branch_name, None

    # 2. Look for existing branch
    adw_id = state.get("adw_id")
    existing_branch = find_existing_branch_for_issue(issue_number, adw_id, cwd=cwd)
    if existing_branch:
        logger.info(f"Found existing branch: {existing_branch}")
        # Checkout the branch
        result = subprocess.run(
            ["git", "checkout", existing_branch],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        if result.returncode != 0:
            return "", f"Failed to checkout branch: {result.stderr}"
        state.update(branch_name=existing_branch)
        return existing_branch, None

    # 3. Create new branch - classify issue first
    logger.info("No existing branch found, creating new one")

    # Classify the issue
    issue_command, error = classify_issue(issue, adw_id, logger)
    if error:
        return "", f"Failed to classify issue: {error}"

    state.update(issue_class=issue_command)

    # Generate branch name
    branch_name, error = generate_branch_name(issue, issue_command, adw_id, logger)
    if error:
        return "", f"Failed to generate branch name: {error}"

    # Create the branch
    from adw_modules.git_ops import create_branch

    success, error = create_branch(branch_name, cwd=cwd)
    if not success:
        return "", f"Failed to create branch: {error}"

    state.update(branch_name=branch_name)
    logger.info(f"Created and checked out new branch: {branch_name}")

    return branch_name, None


def find_spec_file(state: ADWState, logger: logging.Logger) -> Optional[str]:
    """Find the spec file from state - fail fast if not present.

    For isolated workflows, automatically uses worktree_path from state.
    """
    worktree_path = state.get("worktree_path")
    spec_file = state.get("plan_file")

    if not spec_file:
        raise ValueError("No plan_file in state - run planning phase first")

    # Make absolute if needed
    if worktree_path and not os.path.isabs(spec_file):
        spec_file = os.path.join(worktree_path, spec_file)

    if not os.path.exists(spec_file):
        raise ValueError(f"Spec file not found: {spec_file}")

    logger.info(f"Using spec file from state: {spec_file}")
    return spec_file


def create_and_implement_patch(
    adw_id: str,
    review_change_request: str,
    logger: logging.Logger,
    agent_name_planner: str,
    agent_name_implementor: str,
    spec_path: Optional[str] = None,
    issue_screenshots: Optional[str] = None,
    target_files: Optional[list] = None,
    working_dir: Optional[str] = None,
) -> Tuple[Optional[str], AgentPromptResponse]:
    """Create a patch plan and implement it.
    Returns (patch_file_path, implement_response) tuple."""

    # PRE-COMPUTE patch file path (deterministic, no parsing needed)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    issue_slug = re.sub(r'[^a-z0-9]+', '-', review_change_request[:30].lower()).strip('-')
    expected_patch_file = f"specs/patch/patch-adw-{adw_id}-{timestamp}-{issue_slug}.md"

    logger.info(f"Pre-computed patch file path: {expected_patch_file}")

    # Create context file with pre-computed paths
    worktree_path = working_dir or os.getcwd()
    context_data = {
        "patch_file_path": expected_patch_file,
    }

    if spec_path:
        context_data["spec_file"] = spec_path

    if issue_screenshots:
        context_data["issue_screenshots"] = issue_screenshots.split(',') if isinstance(issue_screenshots, str) else issue_screenshots

    if target_files:
        context_data["target_files"] = target_files

    create_context_file(worktree_path, adw_id, context_data, logger)

    # Create patch plan using /patch command (simplified args)
    args = [adw_id, review_change_request]

    request = AgentTemplateRequest(
        agent_name=agent_name_planner,
        slash_command="/patch",
        args=args,
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"Patch plan request: {request.model_dump_json(indent=2, by_alias=True)}"
    )

    response = execute_template(request)

    logger.debug(
        f"Patch plan response: {response.model_dump_json(indent=2, by_alias=True)}"
    )

    if not response.success:
        logger.error(f"Error creating patch plan: {response.output}")
        return None, AgentPromptResponse(
            output=f"Failed to create patch plan: {response.output}", success=False
        )

    # Use pre-computed path - no parsing needed!
    patch_file_path = expected_patch_file
    logger.info(f"Using pre-computed patch file: {patch_file_path}")

    # Now implement the patch plan using the provided implementor agent name
    implement_response = implement_plan(
        patch_file_path, adw_id, logger, agent_name_implementor, working_dir=working_dir
    )

    return patch_file_path, implement_response
