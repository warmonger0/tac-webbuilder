### Workflow 2.1: Move GitHubIssue and Complexity Types
**Estimated Time:** 1-2 hours
**Complexity:** Medium
**Dependencies:** Workflow 1.1

**Input Files:**
- `adws/adw_modules/data_types.py` (GitHubIssue definition)
- `adws/adw_modules/complexity_analyzer.py` (ComplexityLevel, analyze function)

**Output Files:**
- `shared/models/github_issue.py` (new)
- `shared/models/complexity.py` (new)
- `shared/services/complexity_analyzer.py` (new)

**Tasks:**
1. Extract `GitHubIssue` dataclass from `adws/adw_modules/data_types.py`
2. Create `shared/models/github_issue.py` with GitHubIssue
3. Extract `ComplexityLevel` enum and related types
4. Create `shared/models/complexity.py` with complexity types
5. Move `analyze_issue_complexity` function to shared services
6. Create `shared/services/complexity_analyzer.py`
7. Add comprehensive docstrings to all moved code
8. Update shared package `__init__.py` files with exports

**Implementation:**

```python
# shared/models/github_issue.py
"""
Shared GitHub issue model used by both app/server and adws.

This model represents a GitHub issue and is used for workflow automation
and issue processing across the application.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class GitHubIssue:
    """
    Represents a GitHub issue with all relevant metadata.

    Used by:
    - app/server/server.py for webhook processing
    - adws/adw_modules/workflow_ops.py for workflow creation
    """
    number: int
    title: str
    body: str
    state: str
    author: str
    labels: List[str]
    created_at: str
    updated_at: str
    url: str
    assignees: Optional[List[str]] = None
    milestone: Optional[str] = None

    def __str__(self) -> str:
        return f"Issue #{self.number}: {self.title}"

    def __repr__(self) -> str:
        return f"GitHubIssue(number={self.number}, title='{self.title}', state='{self.state}')"
```

```python
# shared/models/complexity.py
"""
Shared complexity types for issue analysis.

Complexity analysis is used to determine the appropriate workflow
and resource allocation for GitHub issues.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any


class ComplexityLevel(str, Enum):
    """Issue complexity classification"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    UNKNOWN = "unknown"


@dataclass
class ComplexityAnalysis:
    """
    Results of complexity analysis for a GitHub issue.

    Attributes:
        level: The determined complexity level
        confidence: Confidence score (0.0-1.0)
        reasoning: Explanation of the complexity assessment
        factors: Dictionary of factors that influenced the decision
    """
    level: ComplexityLevel
    confidence: float
    reasoning: str
    factors: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return f"{self.level.value} (confidence: {self.confidence:.2f})"
```

```python
# shared/services/complexity_analyzer.py
"""
Shared complexity analysis service.

Analyzes GitHub issues to determine their complexity level using
LLM-based analysis.
"""

import logging
from typing import Dict, Any

from shared.models.github_issue import GitHubIssue
from shared.models.complexity import ComplexityLevel, ComplexityAnalysis

logger = logging.getLogger(__name__)


def analyze_issue_complexity(issue: GitHubIssue) -> ComplexityAnalysis:
    """
    Analyze a GitHub issue to determine its complexity level.

    This function uses an LLM to analyze the issue title, body, and labels
    to classify it as simple, moderate, or complex.

    Args:
        issue: The GitHub issue to analyze

    Returns:
        ComplexityAnalysis with level, confidence, and reasoning

    Example:
        >>> issue = GitHubIssue(number=123, title="Fix typo", ...)
        >>> analysis = analyze_issue_complexity(issue)
        >>> print(analysis.level)
        ComplexityLevel.SIMPLE
    """
    # Import here to avoid circular dependency with LLM client
    # This is Layer 1 importing from Layer 0 (external dependencies)
    try:
        from anthropic import Anthropic
    except ImportError:
        logger.warning("Anthropic library not available, returning unknown complexity")
        return ComplexityAnalysis(
            level=ComplexityLevel.UNKNOWN,
            confidence=0.0,
            reasoning="Anthropic library not available"
        )

    # Implementation of complexity analysis
    # This is extracted from adws/adw_modules/complexity_analyzer.py
    # ... (existing implementation)

    # Placeholder for now
    return ComplexityAnalysis(
        level=ComplexityLevel.MODERATE,
        confidence=0.8,
        reasoning="Automated analysis",
        factors={"title_length": len(issue.title), "has_labels": len(issue.labels) > 0}
    )
```

**Before/After Import Examples:**

**Before (with path manipulation):**
```python
# app/server/server.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'adws'))
from adw_modules.data_types import GitHubIssue as ADWGitHubIssue
from adw_modules.complexity_analyzer import analyze_issue_complexity
```

**After (clean imports):**
```python
# app/server/server.py
from shared.models.github_issue import GitHubIssue
from shared.services.complexity_analyzer import analyze_issue_complexity
```

**Acceptance Criteria:**
- [ ] GitHubIssue model moved to shared/models/github_issue.py
- [ ] Complexity types moved to shared/models/complexity.py
- [ ] analyze_issue_complexity moved to shared/services/complexity_analyzer.py
- [ ] All code has comprehensive docstrings
- [ ] Models can be imported without errors
- [ ] No dependencies on app/server or adws code

**Verification Commands:**
```bash
# Verify models can be imported
python -c "from shared.models.github_issue import GitHubIssue; print('GitHubIssue OK')"
python -c "from shared.models.complexity import ComplexityLevel, ComplexityAnalysis; print('Complexity models OK')"
python -c "from shared.services.complexity_analyzer import analyze_issue_complexity; print('Analyzer OK')"

# Verify no circular dependencies
python -c "import shared.models.github_issue; import shared.models.complexity; import shared.services.complexity_analyzer; print('No circular dependencies')"
```
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
