import os
import json
from typing import Tuple, List
from anthropic import Anthropic
from core.data_models import GitHubIssue, ProjectContext


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


def extract_requirements(nl_input: str, intent: dict) -> List[str]:
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


def suggest_adw_workflow(issue_type: str, complexity: str) -> Tuple[str, str]:
    """
    Recommend ADW workflow and model set based on issue type and complexity.

    This function implements a rule-based workflow recommendation system:
    - Bugs always use adw_plan_build_test_iso with base model (need thorough testing)
    - Chores use simpler adw_sdlc_iso with base model (less complexity)
    - Features are tiered by complexity:
      * Low complexity: adw_sdlc_iso with base model
      * Medium complexity: adw_plan_build_test_iso with base model
      * High complexity: adw_plan_build_test_iso with heavy model (more powerful)

    Args:
        issue_type: "feature", "bug", or "chore"
        complexity: "low", "medium", or "high"

    Returns:
        Tuple of (workflow, model_set) where:
        - workflow: ADW workflow identifier (e.g., "adw_sdlc_iso")
        - model_set: "base" or "heavy"
    """
    # Workflow recommendation logic based on complexity and type
    if issue_type == "bug":
        return ("adw_plan_build_test_iso", "base")
    elif issue_type == "chore":
        return ("adw_sdlc_iso", "base")
    else:  # feature
        if complexity == "high":
            return ("adw_plan_build_test_iso", "heavy")
        elif complexity == "medium":
            return ("adw_plan_build_test_iso", "base")
        else:  # low
            return ("adw_sdlc_iso", "base")


async def process_request(nl_input: str, project_context: ProjectContext) -> GitHubIssue:
    """
    Main orchestration function that converts natural language to GitHub issue.

    This is the primary entry point for the NL processing pipeline. It coordinates
    all the steps needed to transform a natural language description into a complete,
    properly formatted GitHub issue with ADW workflow recommendations.

    Processing Pipeline:
    1. Analyze intent using Claude API
    2. Extract technical requirements from the input
    3. Classify issue type (feature/bug/chore)
    4. Suggest appropriate ADW workflow based on type and complexity
    5. Generate issue title from summary
    6. Assemble issue body with description and requirements
    7. Create labels based on classification and project context
    8. Return complete GitHubIssue object

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
        # Step 1: Analyze intent
        intent = await analyze_intent(nl_input)

        # Step 2: Extract requirements
        requirements = extract_requirements(nl_input, intent)

        # Step 3: Classify issue type
        classification = classify_issue_type(intent)

        # Step 4: Suggest workflow based on complexity
        workflow, model_set = suggest_adw_workflow(classification, project_context.complexity)

        # Step 5: Generate title
        title = intent.get("summary", nl_input[:100])

        # Step 6: Generate issue body (will be formatted by issue_formatter)
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
            f"{workflow} model_set {model_set}"
        ])

        body = "\n".join(body_parts)

        # Step 7: Generate labels
        labels = [classification, intent.get('technical_area', 'general').lower()]
        if project_context.framework:
            labels.append(project_context.framework)

        # Step 8: Create GitHubIssue object
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
