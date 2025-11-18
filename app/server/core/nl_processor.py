import json
import os
import re

from anthropic import Anthropic

from core.data_models import GitHubIssue, ProjectContext
from core.template_router import detect_characteristics, route_by_template


async def analyze_intent(nl_input: str) -> dict:
    """
    Use Claude API to understand what user wants to build.

    This function sends the natural language input to Claude API with a structured
    prompt that instructs the model to classify the request and extract key information.
    The response is parsed as JSON containing intent classification and metadata.

    Args:
        nl_input: Natural language description of the desired feature/bug/chore

    Returns:
        Dictionary containing:
        - intent_type: "feature", "bug", or "chore"
        - summary: Brief summary of the intent
        - technical_area: Technical area (e.g., "authentication", "UI", "database")

    Raises:
        ValueError: If ANTHROPIC_API_KEY environment variable is not set
        Exception: If Claude API call fails or response cannot be parsed
    """
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        client = Anthropic(api_key=api_key)

        prompt = f"""Analyze this natural language request and extract the intent:

Request: "{nl_input}"

Provide your analysis as a JSON object with the following fields:
- intent_type: Must be one of "feature", "bug", or "chore"
- summary: A brief one-sentence summary of what the user wants
- technical_area: The primary technical area (e.g., "UI", "authentication", "database", "API", "testing")

Guidelines:
- "feature": New functionality or enhancement to existing functionality
- "bug": Something that's broken or not working as expected
- "chore": Maintenance tasks, refactoring, documentation, setup

Return ONLY the JSON object, no explanations."""

        response = client.messages.create(
            model="claude-sonnet-4-0",
            max_tokens=300,
            temperature=0.1,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        result_text = response.content[0].text.strip()

        # Clean up markdown code blocks if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        return json.loads(result_text.strip())

    except Exception as e:
        raise Exception(f"Error analyzing intent with Anthropic: {str(e)}")


def extract_requirements(nl_input: str, intent: dict) -> list[str]:
    """
    Extract technical requirements from the natural language request.

    This function uses Claude API to break down the user's request into concrete,
    actionable technical requirements. The requirements are returned as a JSON array
    of strings, each representing a specific implementation step.

    Args:
        nl_input: Natural language description
        intent: Intent analysis dictionary from analyze_intent()

    Returns:
        List of technical requirements (strings)

    Raises:
        ValueError: If ANTHROPIC_API_KEY environment variable is not set
        Exception: If Claude API call fails or response cannot be parsed
    """
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        client = Anthropic(api_key=api_key)

        prompt = f"""Based on this request and its intent analysis, extract specific technical requirements:

Request: "{nl_input}"
Intent: {json.dumps(intent, indent=2)}

Extract a list of specific, actionable technical requirements. Each requirement should be:
- Concrete and testable
- Focused on implementation details
- Written in clear, technical language

Return your answer as a JSON array of strings. Example format:
["Implement user authentication with JWT tokens", "Create login form with email/password fields", "Add password hashing with bcrypt"]

Return ONLY the JSON array, no explanations."""

        response = client.messages.create(
            model="claude-sonnet-4-0",
            max_tokens=500,
            temperature=0.2,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        result_text = response.content[0].text.strip()

        # Clean up markdown code blocks if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        return json.loads(result_text.strip())

    except Exception as e:
        raise Exception(f"Error extracting requirements with Anthropic: {str(e)}")


def classify_issue_type(intent: dict) -> str:
    """
    Determine issue classification based on intent analysis.

    Args:
        intent: Intent analysis dictionary

    Returns:
        Issue classification: "feature", "bug", or "chore"
    """
    return intent.get("intent_type", "feature")


def extract_explicit_workflow(text: str) -> tuple[str, str] | None:
    """
    Extract explicit workflow specification from text if present.

    This function checks if the user has explicitly specified a workflow in their text,
    allowing them to override automatic pattern-based classification.

    Looks for patterns like:
    - "Workflow: adw_sdlc_iso"
    - "Execution: uv run adw_sdlc_complete_zte_iso.py"
    - "adw_plan_build_test_iso with base model"
    - "Use adw_lightweight_iso"

    Args:
        text: Input text that may contain workflow specification

    Returns:
        Tuple of (workflow, model_set) if found, None otherwise
    """
    text_lower = text.lower()

    # List of all valid workflows (synchronized with adws/adw_modules/workflow_ops.py)
    valid_workflows = [
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
        "adw_lightweight_iso",
        "adw_plan_build_iso",
        "adw_plan_build_test_iso",
        "adw_plan_build_test_review_iso",
        "adw_plan_build_document_iso",
        "adw_plan_build_review_iso",
        "adw_stepwise_iso",
        # Full SDLC workflows
        "adw_sdlc_iso",
        "adw_sdlc_complete_iso",
        "adw_sdlc_zte_iso",
        "adw_sdlc_complete_zte_iso",
    ]

    for workflow in valid_workflows:
        workflow_lower = workflow.lower()

        # Pattern: workflow name with optional .py extension, optional --flags, and optional model specification
        # Examples:
        # - "adw_sdlc_complete_zte_iso.py --use-optimized-plan"
        # - "adw_plan_build_test_iso with base model"
        # - "Workflow: adw_sdlc_iso"
        pattern = rf'{re.escape(workflow_lower)}(?:\.py)?(?:\s+--[\w-]+)*(?:\s+with\s+(\w+)\s+model)?'
        match = re.search(pattern, text_lower)

        if match:
            # Extract model_set if specified, default to "base"
            model_set = match.group(1) if match.group(1) else "base"
            return (workflow, model_set)

    return None


def suggest_adw_workflow(issue_type: str, complexity: str, characteristics: dict = None) -> tuple[str, str]:
    """
    Recommend ADW workflow and model set based on issue type, complexity, and characteristics.

    This function implements a rule-based workflow recommendation system with lightweight
    optimization:

    Lightweight workflow ($0.20-0.50):
    - UI-only changes (1-2 files)
    - Documentation updates
    - Simple chores without testing needs
    - Single-file modifications

    Standard SDLC ($3-5):
    - Low complexity features (multi-file)
    - Chores requiring some validation

    Plan-Build-Test ($3-5):
    - Bugs (need thorough testing)
    - Medium complexity features

    Plan-Build-Test with heavy model ($5-10):
    - High complexity features

    Args:
        issue_type: "feature", "bug", or "chore"
        complexity: "low", "medium", or "high"
        characteristics: Optional dict with:
            - ui_only: bool
            - backend_changes: bool
            - testing_needed: bool
            - docs_only: bool
            - file_count_estimate: int

    Returns:
        Tuple of (workflow, model_set) where:
        - workflow: ADW workflow identifier (e.g., "adw_lightweight_iso")
        - model_set: "base" or "heavy"
    """
    characteristics = characteristics or {}

    # Check for lightweight patterns first (cost optimization)
    is_ui_only = characteristics.get("ui_only", False)
    is_docs_only = characteristics.get("docs_only", False)
    file_count = characteristics.get("file_count_estimate", 2)
    needs_testing = characteristics.get("testing_needed", False)
    has_backend = characteristics.get("backend_changes", False)

    # Lightweight criteria:
    # - 1-2 files
    # - No backend changes
    # - UI or docs only
    # - No testing needed
    if (file_count <= 2 and
        not has_backend and
        not needs_testing and
        (is_ui_only or is_docs_only)):
        return ("adw_lightweight_iso", "base")

    # Lightweight for simple chores
    if issue_type == "chore" and complexity == "low" and not needs_testing:
        return ("adw_lightweight_iso", "base")

    # Bugs always need testing
    if issue_type == "bug":
        return ("adw_plan_build_test_iso", "base")

    # Chores without special characteristics
    elif issue_type == "chore":
        return ("adw_sdlc_iso", "base")

    # Features tiered by complexity
    else:  # feature
        if complexity == "high":
            return ("adw_plan_build_test_iso", "heavy")
        elif complexity == "medium":
            return ("adw_plan_build_test_iso", "base")
        else:  # low
            # Low complexity features still use SDLC unless they match lightweight criteria
            return ("adw_sdlc_iso", "base")


async def process_request(nl_input: str, project_context: ProjectContext) -> GitHubIssue:
    """
    Main orchestration function that converts natural language to GitHub issue.

    This is the primary entry point for the NL processing pipeline. It coordinates
    all the steps needed to transform a natural language description into a complete,
    properly formatted GitHub issue with ADW workflow recommendations.

    Processing Pipeline (Optimized):
    0. Try template matching first (fast, free, deterministic)
       - If matched: Skip Claude API calls, use template routing
       - If not matched: Continue to structured prompts
    1. Analyze intent using Claude API (if needed)
    2. Extract technical requirements from the input (if needed)
    3. Classify issue type (feature/bug/chore)
    4. Detect characteristics (ui_only, backend_changes, etc.)
    5. Suggest appropriate ADW workflow based on type, complexity, and characteristics
    6. Generate issue title from summary
    7. Assemble issue body with description and requirements
    8. Create labels based on classification and project context
    9. Return complete GitHubIssue object

    Args:
        nl_input: Natural language description of the desired feature/bug/chore
        project_context: Project context information from detect_project_context()

    Returns:
        GitHubIssue object with all fields populated:
        - title: Brief summary of the request
        - body: Formatted markdown with description and requirements
        - labels: List of relevant labels (classification, technical area, framework)
        - classification: "feature", "bug", or "chore"
        - workflow: Recommended ADW workflow identifier
        - model_set: "base" or "heavy"

    Raises:
        Exception: If any step of the pipeline fails (intent analysis, requirement
                  extraction, or issue generation)
    """
    try:
        # Step 0: Check for explicit workflow specification FIRST (user override)
        explicit_workflow = extract_explicit_workflow(nl_input)

        if explicit_workflow:
            # User explicitly specified a workflow - honor their choice
            workflow, model_set = explicit_workflow

            # Infer classification from workflow name (simple heuristic)
            if "lightweight" in workflow or "patch" in workflow:
                classification = "chore"
            elif "test" in workflow or "fix" in nl_input.lower():
                classification = "bug"
            else:
                classification = "feature"

            # Generate simplified issue for explicit workflow specs
            title = nl_input[:100]
            requirements = [nl_input]

            body_parts = [
                "## Description",
                f"{nl_input}",
                "",
                "## Classification",
                f"Explicit workflow: `{workflow}` (user specified)",
                "",
                "## Workflow",
                f"{workflow} with {model_set} model"
            ]

            body = "\n".join(body_parts)
            labels = [classification, "explicit-workflow"]

        else:
            # No explicit workflow - try template matching (cost optimization)
            template_match = route_by_template(nl_input)

            if template_match.matched:
                # Template matched! Skip Claude API calls
                classification = template_match.classification
                workflow = template_match.workflow
                model_set = template_match.model_set

                # Generate simplified issue for template matches
                # (we don't have detailed intent/requirements, but that's ok for simple requests)
                title = nl_input[:100]  # Use truncated input as title
                requirements = [nl_input]  # Use full input as single requirement

                body_parts = [
                    "## Description",
                    f"{nl_input}",
                    "",
                    "## Classification",
                    f"Pattern matched: `{template_match.pattern_name}` (confidence: {template_match.confidence:.0%})",
                    "",
                    "## Workflow",
                    f"{workflow} with {model_set} model"
                ]

                body = "\n".join(body_parts)
                labels = [classification, "auto-routed"]

            else:
                # No template match - use structured prompts (Claude API)
                # Step 1: Analyze intent
                intent = await analyze_intent(nl_input)

                # Step 2: Extract requirements
                requirements = extract_requirements(nl_input, intent)

                # Step 3: Classify issue type
                classification = classify_issue_type(intent)

                # Step 4: Detect characteristics for routing
                characteristics = detect_characteristics(nl_input)

                # Step 5: Suggest workflow based on complexity and characteristics
                workflow, model_set = suggest_adw_workflow(
                    classification,
                    project_context.complexity,
                    characteristics
                )

                # Step 6: Generate title
                title = intent.get("summary", nl_input[:100])

                # Step 7: Generate issue body (will be formatted by issue_formatter)
                # For now, create a basic structure
                body_parts = [
                    "## Description",
                    f"{intent.get('summary', nl_input)}",
                    "",
                    "## Requirements",
                ]

                for req in requirements:
                    body_parts.append(f"- {req}")

                body_parts.extend([
                    "",
                    "## Technical Area",
                    f"{intent.get('technical_area', 'General')}",
                    "",
                    "## Workflow",
                    f"{workflow} with {model_set} model"
                ])

                body = "\n".join(body_parts)

                # Step 8: Generate labels
                labels = [classification, intent.get('technical_area', 'general').lower()]
                if project_context.framework:
                    labels.append(project_context.framework)

        # Step 9: Create GitHubIssue object
        return GitHubIssue(
            title=title,
            body=body,
            labels=labels,
            classification=classification,
            workflow=workflow,
            model_set=model_set
        )

    except Exception as e:
        raise Exception(f"Error processing NL request: {str(e)}")
