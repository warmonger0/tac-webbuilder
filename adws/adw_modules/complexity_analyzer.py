"""
Complexity Analyzer for ADW Workflows

Analyzes GitHub issues to determine complexity level and route to appropriate workflow:
- LIGHTWEIGHT: Simple, isolated changes (~$0.20-0.50)
- STANDARD: Moderate complexity (~$1.00-2.00)
- COMPLEX: Full-stack, integrated features (~$3.00-5.00)
"""

from typing import Tuple, Literal
from dataclasses import dataclass
from .data_types import GitHubIssue

ComplexityLevel = Literal["lightweight", "standard", "complex"]


@dataclass
class ComplexityAnalysis:
    """Result of complexity analysis"""
    level: ComplexityLevel
    confidence: float  # 0.0 to 1.0
    reasoning: str
    estimated_cost_range: Tuple[float, float]
    recommended_workflow: str

    @property
    def is_lightweight(self) -> bool:
        return self.level == "lightweight"

    @property
    def is_standard(self) -> bool:
        return self.level == "standard"

    @property
    def is_complex(self) -> bool:
        return self.level == "complex"


def analyze_issue_complexity(issue: GitHubIssue, issue_class: str) -> ComplexityAnalysis:
    """
    Analyze issue complexity using heuristics to determine workflow routing.

    Returns:
        ComplexityAnalysis with routing recommendation
    """
    text = f"{issue.title} {issue.body}".lower()

    # Scoring system (higher = more complex)
    complexity_score = 0
    reasons = []

    # === LIGHTWEIGHT INDICATORS (reduces complexity) ===

    # Simple UI-only changes
    ui_only_keywords = [
        'add button', 'change color', 'update text', 'rename', 'label',
        'tooltip', 'icon', 'display', 'show', 'hide', 'toggle',
        'styling', 'css', 'layout adjustment'
    ]
    if any(kw in text for kw in ui_only_keywords):
        complexity_score -= 2
        reasons.append("Simple UI change detected")

    # Documentation only
    if any(kw in text for kw in ['docs', 'documentation', 'readme', 'comment']):
        if not any(kw in text for kw in ['implement', 'feature', 'backend']):
            complexity_score -= 3
            reasons.append("Documentation-only change")

    # Single file mentions
    if text.count('.tsx') == 1 or text.count('.ts') == 1 or text.count('.py') == 1:
        complexity_score -= 1
        reasons.append("Single file scope")

    # Chore/cleanup tasks
    if issue_class == '/chore':
        complexity_score -= 1
        reasons.append("Chore classification (typically simpler)")

    # === COMPLEXITY INDICATORS (increases complexity) ===

    # Backend + Frontend integration
    if ('backend' in text or 'server' in text or 'api' in text) and \
       ('frontend' in text or 'client' in text or 'ui' in text):
        complexity_score += 3
        reasons.append("Full-stack integration required")

    # Database/state changes
    if any(kw in text for kw in ['database', 'migration', 'schema', 'model', 'orm']):
        complexity_score += 2
        reasons.append("Database changes required")

    # Authentication/security
    if any(kw in text for kw in ['auth', 'security', 'permission', 'access control']):
        complexity_score += 2
        reasons.append("Security-sensitive changes")

    # External integrations
    if any(kw in text for kw in ['api integration', 'third-party', 'webhook', 'external service']):
        complexity_score += 2
        reasons.append("External integration required")

    # Multiple components
    component_count = text.count('component') + text.count('module') + text.count('service')
    if component_count > 2:
        complexity_score += 2
        reasons.append(f"Multiple components affected ({component_count})")

    # Testing requirements
    if 'e2e' in text or 'integration test' in text:
        complexity_score += 1
        reasons.append("Complex testing required")

    # Workflow/process changes
    if any(kw in text for kw in ['workflow', 'pipeline', 'automation', 'ci/cd']):
        complexity_score += 2
        reasons.append("Workflow/automation changes")

    # Large scope indicators
    if any(kw in text for kw in ['refactor', 'redesign', 'overhaul', 'migration']):
        complexity_score += 2
        reasons.append("Large-scale changes indicated")

    # Explicit complexity markers
    if 'simple' in text or 'quick' in text or 'minor' in text:
        complexity_score -= 2
        reasons.append("Explicitly marked as simple")

    if 'complex' in text or 'major' in text or 'significant' in text:
        complexity_score += 2
        reasons.append("Explicitly marked as complex")

    # === DETERMINE COMPLEXITY LEVEL ===

    if complexity_score <= -2:
        level = "lightweight"
        confidence = min(1.0, abs(complexity_score) / 5.0)
        cost_range = (0.20, 0.50)
        workflow = "adw_lightweight_iso"

    elif complexity_score <= 2:
        level = "standard"
        confidence = 0.7
        cost_range = (1.00, 2.00)
        workflow = "adw_sdlc_iso"

    else:
        level = "complex"
        confidence = min(1.0, complexity_score / 6.0)
        cost_range = (3.00, 5.00)
        workflow = "adw_sdlc_zte_iso"

    reasoning = " | ".join(reasons) if reasons else "Default classification based on issue type"

    return ComplexityAnalysis(
        level=level,
        confidence=confidence,
        reasoning=reasoning,
        estimated_cost_range=cost_range,
        recommended_workflow=workflow
    )


def get_complexity_summary(analysis: ComplexityAnalysis) -> str:
    """Generate human-readable summary of complexity analysis"""
    return f"""
**Complexity Analysis:**
- **Level:** {analysis.level.upper()}
- **Confidence:** {analysis.confidence:.0%}
- **Estimated Cost:** ${analysis.estimated_cost_range[0]:.2f} - ${analysis.estimated_cost_range[1]:.2f}
- **Recommended Workflow:** `{analysis.recommended_workflow}`
- **Reasoning:** {analysis.reasoning}
"""
