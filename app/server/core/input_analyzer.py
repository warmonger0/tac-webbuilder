"""
Input Size Analyzer - Detect when issues should be split for cost efficiency.

This module analyzes GitHub issue inputs to determine if they're too large
and should be broken into smaller, focused tasks for better cost efficiency.

PROBLEM:
- Large, multi-concern issues create expensive workflows
- Splitting too small adds overhead from multiple workflows
- Need to find the sweet spot

SOLUTION:
- Analyze word count, concerns, complexity
- Recommend splits only when net benefit exists
- Provide specific split suggestions
"""

import re
from dataclasses import dataclass


@dataclass
class SplitRecommendation:
    """Recommendation for splitting an issue."""
    should_split: bool
    reason: str
    suggested_splits: list[dict[str, str]]
    estimated_savings: float
    confidence_score: float


# Optimal ranges based on workflow analytics
OPTIMAL_RANGES = {
    "word_count": (50, 300),      # From nl_input_clarity_score
    "concerns": (1, 2),           # Single or dual-concern is ideal
    "estimated_duration": (300, 1800),  # 5-30 minutes
}

# Keywords to detect different technical concerns
CONCERN_KEYWORDS = {
    "frontend": ["ui", "component", "react", "vue", "styling", "css", "html", "frontend", "client", "interface"],
    "backend": ["api", "endpoint", "server", "backend", "database", "query", "schema", "migration"],
    "testing": ["test", "testing", "coverage", "unit test", "integration test", "e2e", "validation"],
    "documentation": ["docs", "documentation", "readme", "guide", "comment", "docstring"],
    "infrastructure": ["deploy", "deployment", "ci/cd", "docker", "kubernetes", "ci", "pipeline", "build"],
    "security": ["auth", "authentication", "authorization", "security", "encryption", "token"],
    "performance": ["performance", "optimization", "caching", "speed", "latency", "benchmark"],
    "database": ["database", "db", "sql", "migration", "schema", "query", "index"]
}


def analyze_input(nl_input: str, metadata: dict = None) -> SplitRecommendation:
    """
    Analyze if an issue should be split into multiple smaller issues.

    Args:
        nl_input: Natural language input from GitHub issue
        metadata: Optional additional context (labels, milestone, etc.)

    Returns:
        SplitRecommendation with decision and suggestions
    """
    if not nl_input:
        return SplitRecommendation(
            should_split=False,
            reason="Input is empty",
            suggested_splits=[],
            estimated_savings=0.0,
            confidence_score=0.0
        )

    metadata = metadata or {}

    # Calculate metrics
    word_count = len(nl_input.split())
    concerns = detect_concerns(nl_input)
    num_concerns = len(concerns)
    bullet_points = count_bullet_points(nl_input)
    estimated_complexity = estimate_complexity(nl_input, num_concerns, bullet_points)

    # Decision logic
    should_split = False
    reason = ""
    suggested_splits = []
    estimated_savings = 0.0
    confidence_score = 0.0

    # Case 1: Too small - don't split
    if word_count < 30:
        return SplitRecommendation(
            should_split=False,
            reason=f"Input too small ({word_count} words) - splitting would add overhead",
            suggested_splits=[],
            estimated_savings=0.0,
            confidence_score=90.0
        )

    # Case 2: Large with multiple concerns - strong split candidate
    if word_count > 300 and num_concerns > 2:
        should_split = True
        reason = f"Large input ({word_count} words) with {num_concerns} distinct concerns"
        suggested_splits = generate_split_suggestions(nl_input, concerns, bullet_points)
        estimated_savings = calculate_split_savings(estimated_complexity, num_concerns)
        confidence_score = 90.0

    # Case 3: Moderate size but many bullet points - consider splitting
    elif word_count > 200 and bullet_points > 5:
        should_split = True
        reason = f"Multiple tasks ({bullet_points} bullet points) detected"
        suggested_splits = generate_split_suggestions_from_bullets(nl_input)
        estimated_savings = calculate_split_savings(estimated_complexity, min(bullet_points, 4))
        confidence_score = 75.0

    # Case 4: Multiple high-effort concerns even if moderate length
    elif num_concerns >= 3 and any(c in ["backend", "frontend", "database"] for c in concerns):
        should_split = True
        reason = f"Multiple high-effort concerns ({', '.join(concerns)}) detected"
        suggested_splits = generate_split_suggestions(nl_input, concerns, bullet_points)
        estimated_savings = calculate_split_savings(estimated_complexity, num_concerns)
        confidence_score = 80.0

    # Case 5: Optimal range - don't split
    else:
        should_split = False
        reason = f"Input is in optimal range ({word_count} words, {num_concerns} concern(s))"
        confidence_score = 85.0

    return SplitRecommendation(
        should_split=should_split,
        reason=reason,
        suggested_splits=suggested_splits,
        estimated_savings=estimated_savings,
        confidence_score=confidence_score
    )


def detect_concerns(nl_input: str) -> list[str]:
    """
    Detect technical concerns mentioned in input.

    Returns:
        List of concern types (e.g., ["frontend", "backend", "testing"])
    """
    input_lower = nl_input.lower()
    detected = []

    for concern_type, keywords in CONCERN_KEYWORDS.items():
        if any(keyword in input_lower for keyword in keywords):
            detected.append(concern_type)

    return detected


def count_bullet_points(text: str) -> int:
    """Count bullet points/numbered lists in text."""
    # Match common bullet formats: -, *, •, 1., 2., etc.
    patterns = [
        r'^\s*[-*•]\s+',  # Dash, asterisk, bullet
        r'^\s*\d+\.\s+',  # Numbered (1., 2., etc.)
        r'^\s*\[\s*\]\s+',  # Checkboxes [ ]
    ]

    count = 0
    for line in text.split('\n'):
        for pattern in patterns:
            if re.match(pattern, line):
                count += 1
                break

    return count


def estimate_complexity(nl_input: str, num_concerns: int, bullet_points: int) -> str:
    """
    Estimate overall complexity of the request.

    Returns:
        "simple", "medium", or "complex"
    """
    word_count = len(nl_input.split())

    # Complexity scoring
    complexity_score = 0

    if word_count > 300:
        complexity_score += 2
    elif word_count > 150:
        complexity_score += 1

    if num_concerns > 3:
        complexity_score += 2
    elif num_concerns > 1:
        complexity_score += 1

    if bullet_points > 5:
        complexity_score += 2
    elif bullet_points > 2:
        complexity_score += 1

    # Map to complexity levels
    if complexity_score <= 1:
        return "simple"
    elif complexity_score <= 3:
        return "medium"
    else:
        return "complex"


def generate_split_suggestions(
    nl_input: str,
    concerns: list[str],
    bullet_points: int
) -> list[dict[str, str]]:
    """
    Generate suggested issue splits based on concerns.

    Returns:
        List of dicts with "title" and "description" for each split
    """
    splits = []

    # Strategy: One issue per major concern
    concern_priority = ["backend", "frontend", "database", "testing", "documentation", "infrastructure"]

    for concern in concern_priority:
        if concern in concerns:
            splits.append({
                "title": generate_split_title(concern, nl_input),
                "concern": concern,
                "description": f"Handle {concern}-related work from the original issue"
            })

    # If no clear concerns, fall back to bullet point splitting
    if not splits and bullet_points > 0:
        return generate_split_suggestions_from_bullets(nl_input)

    return splits[:4]  # Max 4 splits to avoid over-fragmentation


def generate_split_suggestions_from_bullets(nl_input: str) -> list[dict[str, str]]:
    """Generate splits based on bullet points/tasks in the input."""
    splits = []
    lines = nl_input.split('\n')

    bullet_pattern = r'^\s*[-*•\d+\.]\s+'
    current_group = []

    for line in lines:
        if re.match(bullet_pattern, line):
            if current_group:
                # Create split from previous group
                splits.append({
                    "title": extract_task_title(current_group[0]),
                    "concern": "task",
                    "description": "\n".join(current_group)
                })
            current_group = [line]
        elif current_group:
            current_group.append(line)

    # Add last group
    if current_group:
        splits.append({
            "title": extract_task_title(current_group[0]),
            "concern": "task",
            "description": "\n".join(current_group)
        })

    return splits[:4]  # Max 4 splits


def extract_task_title(bullet_line: str) -> str:
    """Extract clean title from bullet point line."""
    # Remove bullet markers
    clean = re.sub(r'^\s*[-*•\d+\.\[\]]\s+', '', bullet_line)
    # Take first 80 chars
    if len(clean) > 80:
        clean = clean[:77] + "..."
    return clean.strip()


def generate_split_title(concern: str, nl_input: str) -> str:
    """Generate a descriptive title for a split issue."""
    # Extract first sentence or first 100 chars
    first_sentence = nl_input.split('.')[0]
    if len(first_sentence) > 100:
        first_sentence = first_sentence[:97] + "..."

    return f"{concern.title()}: {first_sentence}"


def calculate_split_savings(complexity: str, num_splits: int) -> float:
    """
    Estimate cost savings from splitting.

    Args:
        complexity: "simple", "medium", or "complex"
        num_splits: Number of issues to split into

    Returns:
        Estimated dollar savings
    """
    # Base workflow costs (from workflow_analytics data)
    BASE_COSTS = {
        "simple": 0.30,
        "medium": 0.60,
        "complex": 1.50
    }

    # Overhead per workflow (account for splitting overhead)
    WORKFLOW_OVERHEAD = 0.10

    # Calculate monolithic cost
    monolithic_cost = BASE_COSTS.get(complexity, 0.60)

    # Calculate split cost
    # When splitting complex → multiple simpler tasks
    if complexity == "complex" or complexity == "medium":
        split_complexity = "simple"
    else:
        # Already simple, splitting adds overhead
        return -0.20  # Negative savings = cost increase

    per_split_cost = BASE_COSTS[split_complexity] + WORKFLOW_OVERHEAD
    total_split_cost = per_split_cost * num_splits

    # Calculate savings
    savings = monolithic_cost - total_split_cost

    return round(savings, 2)


def format_recommendation_for_github(recommendation: SplitRecommendation) -> str:
    """
    Format recommendation as GitHub comment Markdown.

    Args:
        recommendation: SplitRecommendation object

    Returns:
        Markdown string for GitHub comment
    """
    if not recommendation.should_split:
        return None  # Don't comment if no split recommended

    md = "## 💡 Cost Optimization Suggestion\n\n"
    md += f"**Analysis:** {recommendation.reason}\n\n"
    md += f"**Confidence:** {recommendation.confidence_score:.0f}%\n"

    if recommendation.estimated_savings > 0:
        md += f"**Estimated Savings:** ${recommendation.estimated_savings:.2f}\n\n"

    md += "### Suggested Split\n\n"
    md += "Consider breaking this into the following issues:\n\n"

    for i, split in enumerate(recommendation.suggested_splits, 1):
        md += f"{i}. **{split['title']}**\n"
        if split.get('description'):
            md += f"   - {split['description']}\n"

    md += "\n### Why Split?\n\n"
    md += "- Smaller, focused tasks are easier for ADWs to execute\n"
    md += "- Reduces context size and LLM costs\n"
    md += "- Allows parallel execution\n"
    md += "- Easier to review and test\n\n"

    md += "*This is an automated suggestion. You can choose to keep this as a single issue if preferred.*\n"

    return md


# Example usage for testing
if __name__ == "__main__":
    # Test case 1: Large multi-concern issue
    test_input_1 = """
    Add user authentication system with JWT tokens. Need to:
    - Create backend API endpoints for login, register, logout
    - Update database schema with users table and sessions
    - Build frontend login form with React and validation
    - Add password hashing with bcrypt
    - Write integration tests for auth flow
    - Document the authentication API in OpenAPI spec
    - Update deployment scripts for JWT_SECRET env var
    - Add rate limiting to prevent brute force attacks
    """

    result = analyze_input(test_input_1)
    print("Test 1 - Large multi-concern:")
    print(f"Should split: {result.should_split}")
    print(f"Reason: {result.reason}")
    print(f"Savings: ${result.estimated_savings}")
    print(f"Splits: {len(result.suggested_splits)}")
    print()

    # Test case 2: Optimal size
    test_input_2 = """
    Add a dark mode toggle button to the settings page.
    The button should save preference to localStorage.
    """

    result2 = analyze_input(test_input_2)
    print("Test 2 - Optimal size:")
    print(f"Should split: {result2.should_split}")
    print(f"Reason: {result2.reason}")
    print()
