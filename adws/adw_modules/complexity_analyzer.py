"""
Complexity Analyzer for ADW Workflows

Analyzes GitHub issues to determine complexity level and route to appropriate workflow:
- LIGHTWEIGHT: Simple, isolated changes (~$0.20-0.50)
- STANDARD: Moderate complexity (~$1.00-2.00)
- COMPLEX: Full-stack, integrated features (~$3.00-5.00)

Supports learning from historical data to improve accuracy over time.
"""

from typing import Tuple, Literal, Dict, Optional
from dataclasses import dataclass, field
from .data_types import GitHubIssue
import json
import os
from pathlib import Path

ComplexityLevel = Literal["lightweight", "standard", "complex"]


@dataclass
class ComplexityAnalysis:
    """Result of complexity analysis"""
    level: ComplexityLevel
    confidence: float  # 0.0 to 1.0
    reasoning: str
    estimated_cost_range: Tuple[float, float]
    estimated_cost_total: float  # Midpoint of cost range
    recommended_workflow: str
    cost_breakdown_estimate: Dict[str, float] = field(default_factory=dict)  # Per-phase estimates

    @property
    def is_lightweight(self) -> bool:
        return self.level == "lightweight"

    @property
    def is_standard(self) -> bool:
        return self.level == "standard"

    @property
    def is_complex(self) -> bool:
        return self.level == "complex"


def _load_learning_weights() -> Dict[str, float]:
    """Load learned keyword weights from historical data."""
    weights_file = Path("app/db/cost_estimation_weights.json")
    if weights_file.exists():
        try:
            with open(weights_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}  # Empty dict means use default weights


def _estimate_phase_costs(total_cost: float, workflow: str) -> Dict[str, float]:
    """
    Estimate per-phase costs based on total estimated cost and workflow type.

    Different workflows have different phase distributions:
    - lightweight: No planning phase, mostly implementation
    - standard: Balanced across phases
    - complex: Heavier planning and testing phases
    """
    phase_distributions = {
        "adw_lightweight_iso": {
            "build": 1.0,  # 100% in build phase
        },
        "adw_sdlc_iso": {
            "plan": 0.15,   # 15%
            "build": 0.45,  # 45%
            "test": 0.20,   # 20%
            "review": 0.10, # 10%
            "document": 0.10,  # 10%
        },
        "adw_sdlc_zte_iso": {
            "plan": 0.20,   # 20%
            "build": 0.35,  # 35%
            "test": 0.25,   # 25%
            "review": 0.10, # 10%
            "document": 0.10,  # 10%
        },
    }

    distribution = phase_distributions.get(workflow, phase_distributions["adw_sdlc_iso"])
    return {phase: total_cost * percentage for phase, percentage in distribution.items()}


def analyze_issue_complexity(issue: GitHubIssue, issue_class: str) -> ComplexityAnalysis:
    """
    Analyze issue complexity using heuristics to determine workflow routing.

    Uses learned weights from historical data when available.

    Returns:
        ComplexityAnalysis with routing recommendation and per-phase cost estimates
    """
    text = f"{issue.title} {issue.body}".lower()
    learned_weights = _load_learning_weights()

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
    ui_weight = learned_weights.get('ui_only', -2.0)
    if any(kw in text for kw in ui_only_keywords):
        complexity_score += ui_weight
        reasons.append("Simple UI change detected")

    # Documentation only
    doc_weight = learned_weights.get('documentation', -3.0)
    if any(kw in text for kw in ['docs', 'documentation', 'readme', 'comment']):
        if not any(kw in text for kw in ['implement', 'feature', 'backend']):
            complexity_score += doc_weight
            reasons.append("Documentation-only change")

    # Single file mentions
    single_file_weight = learned_weights.get('single_file', -1.0)
    if text.count('.tsx') == 1 or text.count('.ts') == 1 or text.count('.py') == 1:
        complexity_score += single_file_weight
        reasons.append("Single file scope")

    # Chore/cleanup tasks
    chore_weight = learned_weights.get('chore', -1.0)
    if issue_class == '/chore':
        complexity_score += chore_weight
        reasons.append("Chore classification (typically simpler)")

    # === COMPLEXITY INDICATORS (increases complexity) ===

    # Backend + Frontend integration
    fullstack_weight = learned_weights.get('fullstack', 3.0)
    if ('backend' in text or 'server' in text or 'api' in text) and \
       ('frontend' in text or 'client' in text or 'ui' in text):
        complexity_score += fullstack_weight
        reasons.append("Full-stack integration required")

    # Database/state changes
    database_weight = learned_weights.get('database', 2.0)
    if any(kw in text for kw in ['database', 'migration', 'schema', 'model', 'orm']):
        complexity_score += database_weight
        reasons.append("Database changes required")

    # Authentication/security
    security_weight = learned_weights.get('security', 2.0)
    if any(kw in text for kw in ['auth', 'security', 'permission', 'access control']):
        complexity_score += security_weight
        reasons.append("Security-sensitive changes")

    # External integrations
    integration_weight = learned_weights.get('integration', 2.0)
    if any(kw in text for kw in ['api integration', 'third-party', 'webhook', 'external service']):
        complexity_score += integration_weight
        reasons.append("External integration required")

    # Multiple components
    component_count = text.count('component') + text.count('module') + text.count('service')
    multi_component_weight = learned_weights.get('multi_component', 2.0)
    if component_count > 2:
        complexity_score += multi_component_weight
        reasons.append(f"Multiple components affected ({component_count})")

    # Testing requirements
    testing_weight = learned_weights.get('complex_testing', 1.0)
    if 'e2e' in text or 'integration test' in text:
        complexity_score += testing_weight
        reasons.append("Complex testing required")

    # Workflow/process changes
    workflow_weight = learned_weights.get('workflow_automation', 2.0)
    if any(kw in text for kw in ['workflow', 'pipeline', 'automation', 'ci/cd']):
        complexity_score += workflow_weight
        reasons.append("Workflow/automation changes")

    # Large scope indicators
    large_scope_weight = learned_weights.get('large_scope', 2.0)
    if any(kw in text for kw in ['refactor', 'redesign', 'overhaul', 'migration']):
        complexity_score += large_scope_weight
        reasons.append("Large-scale changes indicated")

    # Explicit complexity markers
    explicit_simple_weight = learned_weights.get('explicit_simple', -2.0)
    if 'simple' in text or 'quick' in text or 'minor' in text:
        complexity_score += explicit_simple_weight
        reasons.append("Explicitly marked as simple")

    explicit_complex_weight = learned_weights.get('explicit_complex', 2.0)
    if 'complex' in text or 'major' in text or 'significant' in text:
        complexity_score += explicit_complex_weight
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

    # Calculate total cost (midpoint of range)
    estimated_cost_total = (cost_range[0] + cost_range[1]) / 2.0

    # Estimate per-phase costs
    cost_breakdown_estimate = _estimate_phase_costs(estimated_cost_total, workflow)

    return ComplexityAnalysis(
        level=level,
        confidence=confidence,
        reasoning=reasoning,
        estimated_cost_range=cost_range,
        estimated_cost_total=estimated_cost_total,
        recommended_workflow=workflow,
        cost_breakdown_estimate=cost_breakdown_estimate
    )


def learn_from_actual_cost(
    issue: GitHubIssue,
    issue_class: str,
    estimated_cost: float,
    actual_cost: float,
    learning_rate: float = 0.1
) -> None:
    """
    Update keyword weights based on prediction accuracy.

    Uses simple gradient descent: if we underestimated, increase weights
    for detected keywords. If we overestimated, decrease them.

    Args:
        issue: The GitHub issue that was completed
        issue_class: Issue classification (/feature, /bug, /chore)
        estimated_cost: What we predicted
        actual_cost: What it actually cost
        learning_rate: How aggressively to adjust (0.0 to 1.0)
    """
    text = f"{issue.title} {issue.body}".lower()
    error = actual_cost - estimated_cost

    # Only learn if error is significant (> 20% off)
    if abs(error / max(estimated_cost, 0.01)) < 0.2:
        return

    # Load current weights
    weights_file = Path("app/db/cost_estimation_weights.json")
    weights = _load_learning_weights()

    # Adjust weights for keywords that matched
    adjustment = learning_rate * error

    # UI keywords
    ui_only_keywords = [
        'add button', 'change color', 'update text', 'rename', 'label',
        'tooltip', 'icon', 'display', 'show', 'hide', 'toggle',
        'styling', 'css', 'layout adjustment'
    ]
    if any(kw in text for kw in ui_only_keywords):
        weights['ui_only'] = weights.get('ui_only', -2.0) + adjustment

    # Documentation
    if any(kw in text for kw in ['docs', 'documentation', 'readme', 'comment']):
        if not any(kw in text for kw in ['implement', 'feature', 'backend']):
            weights['documentation'] = weights.get('documentation', -3.0) + adjustment

    # Single file
    if text.count('.tsx') == 1 or text.count('.ts') == 1 or text.count('.py') == 1:
        weights['single_file'] = weights.get('single_file', -1.0) + adjustment

    # Chore
    if issue_class == '/chore':
        weights['chore'] = weights.get('chore', -1.0) + adjustment

    # Full-stack
    if ('backend' in text or 'server' in text or 'api' in text) and \
       ('frontend' in text or 'client' in text or 'ui' in text):
        weights['fullstack'] = weights.get('fullstack', 3.0) + adjustment

    # Database
    if any(kw in text for kw in ['database', 'migration', 'schema', 'model', 'orm']):
        weights['database'] = weights.get('database', 2.0) + adjustment

    # Security
    if any(kw in text for kw in ['auth', 'security', 'permission', 'access control']):
        weights['security'] = weights.get('security', 2.0) + adjustment

    # Integration
    if any(kw in text for kw in ['api integration', 'third-party', 'webhook', 'external service']):
        weights['integration'] = weights.get('integration', 2.0) + adjustment

    # Multi-component
    component_count = text.count('component') + text.count('module') + text.count('service')
    if component_count > 2:
        weights['multi_component'] = weights.get('multi_component', 2.0) + adjustment

    # Complex testing
    if 'e2e' in text or 'integration test' in text:
        weights['complex_testing'] = weights.get('complex_testing', 1.0) + adjustment

    # Workflow automation
    if any(kw in text for kw in ['workflow', 'pipeline', 'automation', 'ci/cd']):
        weights['workflow_automation'] = weights.get('workflow_automation', 2.0) + adjustment

    # Large scope
    if any(kw in text for kw in ['refactor', 'redesign', 'overhaul', 'migration']):
        weights['large_scope'] = weights.get('large_scope', 2.0) + adjustment

    # Explicit markers
    if 'simple' in text or 'quick' in text or 'minor' in text:
        weights['explicit_simple'] = weights.get('explicit_simple', -2.0) + adjustment

    if 'complex' in text or 'major' in text or 'significant' in text:
        weights['explicit_complex'] = weights.get('explicit_complex', 2.0) + adjustment

    # Save updated weights
    weights_file.parent.mkdir(parents=True, exist_ok=True)
    with open(weights_file, 'w') as f:
        json.dump(weights, f, indent=2)


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
