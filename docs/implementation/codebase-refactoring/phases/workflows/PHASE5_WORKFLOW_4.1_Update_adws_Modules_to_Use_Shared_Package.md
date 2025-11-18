### Workflow 4.1: Update adws Modules to Use Shared Package
**Estimated Time:** 1-2 hours
**Complexity:** Medium
**Dependencies:** Workflow 2.1

**Input Files:**
- `adws/adw_modules/data_types.py`
- `adws/adw_modules/workflow_ops.py`
- `adws/adw_modules/complexity_analyzer.py`
- `adws/adw_triggers/trigger_webhook.py`

**Output Files:**
- `adws/adw_modules/data_types.py` (modified - remove GitHubIssue)
- `adws/adw_modules/workflow_ops.py` (modified)
- `adws/adw_modules/complexity_analyzer.py` (modified - remove analyze function)
- `adws/adw_triggers/trigger_webhook.py` (modified)

**Tasks:**
1. Update data_types.py to import GitHubIssue from shared
2. Add re-export in data_types.py for backwards compatibility
3. Update workflow_ops.py to import from shared
4. Update complexity_analyzer.py to import from shared
5. Update trigger_webhook.py if it uses these types
6. Search for any other uses of these types in adws/
7. Test workflow creation and processing

**Code Changes:**

```python
# adws/adw_modules/data_types.py
# BEFORE:
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class GitHubIssue:
    number: int
    title: str
    body: str
    # ... (full definition)

# AFTER (for backwards compatibility):
"""
Data types for ADW modules.

Note: GitHubIssue and complexity types have been moved to the shared package.
This module now re-exports them for backwards compatibility.
"""

# Import from shared package
from shared.models.github_issue import GitHubIssue
from shared.models.complexity import ComplexityLevel, ComplexityAnalysis

# Re-export for backwards compatibility
__all__ = [
    'GitHubIssue',
    'ComplexityLevel',
    'ComplexityAnalysis'
]

# Any other data types that are specific to adws stay here
```

```python
# adws/adw_modules/workflow_ops.py
# BEFORE:
from adw_modules.data_types import GitHubIssue
from adw_modules.complexity_analyzer import analyze_issue_complexity

def create_workflow_from_issue(issue: GitHubIssue) -> str:
    complexity = analyze_issue_complexity(issue)
    # ...

# AFTER (direct import from shared):
from shared.models.github_issue import GitHubIssue
from shared.services.complexity_analyzer import analyze_issue_complexity

def create_workflow_from_issue(issue: GitHubIssue) -> str:
    complexity = analyze_issue_complexity(issue)
    # ...
```

```python
# adws/adw_modules/complexity_analyzer.py
# BEFORE:
from anthropic import Anthropic
from adw_modules.data_types import GitHubIssue, ComplexityLevel

def analyze_issue_complexity(issue: GitHubIssue) -> ComplexityLevel:
    # ... (implementation)

# AFTER (re-export from shared):
"""
Complexity analyzer module.

Note: The analyze_issue_complexity function has been moved to shared.services.
This module now re-exports it for backwards compatibility.
"""

from shared.services.complexity_analyzer import analyze_issue_complexity
from shared.models.complexity import ComplexityLevel, ComplexityAnalysis

__all__ = [
    'analyze_issue_complexity',
    'ComplexityLevel',
    'ComplexityAnalysis'
]
```

**Backwards Compatibility Strategy:**

By re-exporting from the shared package in the original locations, we maintain backwards compatibility so existing code in adws/ can continue to work without immediate changes. This allows for gradual migration.

**Search for Other Uses:**
```bash
# Find all imports of GitHubIssue in adws
grep -r "GitHubIssue" adws/ --include="*.py"

# Find all imports of complexity analyzer
grep -r "complexity_analyzer" adws/ --include="*.py"
```

**Acceptance Criteria:**
- [ ] data_types.py imports from shared and re-exports
- [ ] workflow_ops.py uses shared imports
- [ ] complexity_analyzer.py re-exports from shared
- [ ] All adws modules can import these types
- [ ] Backwards compatibility maintained
- [ ] Workflow creation works correctly

**Verification Commands:**
```bash
# Verify adws can still import from local modules (backwards compat)
python -c "from adws.adw_modules.data_types import GitHubIssue; print('✅ Backwards compat OK')"

# Verify adws can import directly from shared
python -c "from shared.models.github_issue import GitHubIssue; print('✅ Direct import OK')"

# Verify no duplicate definitions
python -c "
from adws.adw_modules.data_types import GitHubIssue as LocalIssue
from shared.models.github_issue import GitHubIssue as SharedIssue
assert LocalIssue is SharedIssue, 'Should be same class'
print('✅ No duplicate definitions')
"

# Test workflow operations
python -c "
from shared.models.github_issue import GitHubIssue
from shared.services.complexity_analyzer import analyze_issue_complexity

issue = GitHubIssue(
    number=1,
    title='Test Issue',
    body='Test body',
    state='open',
    author='test',
    labels=[],
    created_at='2025-01-01',
    updated_at='2025-01-01',
    url='https://github.com/test/test/issues/1'
)

analysis = analyze_issue_complexity(issue)
print(f'✅ Analysis: {analysis}')
"
```
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
