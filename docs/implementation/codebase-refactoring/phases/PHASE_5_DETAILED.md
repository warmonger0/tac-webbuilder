# Phase 5: Fix Import Structure - Detailed Implementation Plan

**Status:** Not Started
**Duration:** 1-2 days (5 atomic workflows)
**Priority:** MEDIUM
**Risk:** Low

## Overview

Eliminate path manipulation in imports and create a shared package for types used by both `app/server/` and `adws/`. This phase establishes proper dependency hierarchy and prevents circular dependency issues.

**Success Criteria:**
- ✅ No `sys.path.insert()` manipulation in any file
- ✅ Shared package created with common types
- ✅ Proper dependency hierarchy established (Layer 0-4)
- ✅ All imports resolve correctly without path hacks
- ✅ No circular dependencies detected
- ✅ All existing functionality preserved

---

## Current Problem

**Path Manipulation in server.py (lines 82-83):**
```python
# BAD: Path manipulation to import from outside package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'adws'))
from adw_modules.complexity_analyzer import analyze_issue_complexity
from adw_modules.data_types import GitHubIssue as ADWGitHubIssue
```

**Issues:**
- Violates proper Python package structure
- Creates tight coupling between `app/server` and `adws`
- Violates dependency inversion principle
- Makes it harder to refactor either module
- Can cause import conflicts
- Risk of circular dependencies

---

## Dependency Hierarchy

This phase establishes a clean 5-layer architecture:

```
Layer 4: API Routes (server.py, routes/)
  ↓ can import from
Layer 3: Services (app/server/services/)
  ↓ can import from
Layer 2: Core Business Logic (app/server/core/, adws/adw_modules/)
  ↓ can import from
Layer 1: Data Models & Utilities (shared/models/, shared/utils/)
  ↓ can import from
Layer 0: External Dependencies (fastapi, anthropic, etc.)
```

**Rules:**
- Higher layers can import from lower layers
- Lower layers CANNOT import from higher layers
- Same-layer imports should be minimal
- Use dependency injection for cross-layer communication

---

## Hierarchical Decomposition

### Level 1: Major Components
1. Create Shared Package Structure (1 workflow)
2. Move Shared Types to shared/models/ (1 workflow)
3. Update app/server/ Imports (1 workflow)
4. Update adws/ Imports (1 workflow)
5. Validation and Cleanup (1 workflow)

### Level 2: Atomic Workflow Units

---

## 1. Create Shared Package Structure (1 workflow)

### Workflow 1.1: Create Shared Package Directory Structure
**Estimated Time:** 30 minutes
**Complexity:** Low
**Dependencies:** None

**Input Files:**
- None (creating new structure)

**Output Files:**
- `shared/__init__.py` (new)
- `shared/models/__init__.py` (new)
- `shared/services/__init__.py` (new)
- `shared/utils/__init__.py` (new)

**Tasks:**
1. Create `shared/` directory at project root
2. Create `shared/models/` subdirectory for shared data types
3. Create `shared/services/` subdirectory for shared services
4. Create `shared/utils/` subdirectory for shared utilities
5. Add `__init__.py` files to make them proper Python packages
6. Add docstrings to each `__init__.py` explaining purpose

**Directory Structure:**
```
shared/
├── __init__.py                 # Root shared package
├── models/                     # Shared data models
│   └── __init__.py
├── services/                   # Shared services
│   └── __init__.py
└── utils/                      # Shared utilities
    └── __init__.py
```

**Implementation:**

```python
# shared/__init__.py
"""
Shared package for types and utilities used by both app/server and adws.

This package sits at Layer 1 in the dependency hierarchy and contains
types and utilities that are shared across different parts of the codebase.
"""

__version__ = "1.0.0"
```

```python
# shared/models/__init__.py
"""
Shared data models used across app/server and adws.

These models represent core domain concepts that are used by multiple
parts of the application without creating circular dependencies.
"""

from .github_issue import GitHubIssue
from .complexity import ComplexityLevel, ComplexityAnalysis

__all__ = [
    'GitHubIssue',
    'ComplexityLevel',
    'ComplexityAnalysis'
]
```

```python
# shared/services/__init__.py
"""
Shared services used across app/server and adws.

These services provide common functionality that is needed by multiple
parts of the application.
"""

from .complexity_analyzer import analyze_issue_complexity

__all__ = [
    'analyze_issue_complexity'
]
```

```python
# shared/utils/__init__.py
"""
Shared utility functions used across app/server and adws.
"""

__all__ = []
```

**Acceptance Criteria:**
- [ ] Directory structure created
- [ ] All `__init__.py` files present with docstrings
- [ ] Packages can be imported without errors
- [ ] No circular import issues

**Verification Commands:**
```bash
# Verify directory structure
ls -la shared/
ls -la shared/models/
ls -la shared/services/
ls -la shared/utils/

# Verify packages can be imported
python -c "import shared; print('shared package OK')"
python -c "import shared.models; print('shared.models package OK')"
python -c "import shared.services; print('shared.services package OK')"
python -c "import shared.utils; print('shared.utils package OK')"
```

---

## 2. Move Shared Types to shared/models/ (1 workflow)

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

---

## 3. Update app/server/ Imports (1 workflow)

### Workflow 3.1: Update server.py and Core Modules
**Estimated Time:** 1-2 hours
**Complexity:** Medium
**Dependencies:** Workflow 2.1

**Input Files:**
- `app/server/server.py`
- `app/server/core/*.py` (any files importing from adws)

**Output Files:**
- `app/server/server.py` (modified)
- `app/server/core/*.py` (modified if needed)

**Tasks:**
1. Remove `sys.path.insert()` from server.py
2. Update GitHubIssue imports to use shared.models
3. Update complexity analyzer imports to use shared.services
4. Search for any other adws imports in app/server/
5. Update all found imports to use shared package
6. Remove any ADWGitHubIssue aliases (use GitHubIssue directly)
7. Test all endpoints that use these imports

**Code Changes:**

```python
# app/server/server.py
# BEFORE:
import sys
import os

# BAD: Path manipulation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'adws'))
from adw_modules.complexity_analyzer import analyze_issue_complexity
from adw_modules.data_types import GitHubIssue as ADWGitHubIssue

@app.post("/api/github-webhook")
async def handle_github_webhook(request: Request):
    # ... parse webhook data ...
    issue = ADWGitHubIssue(
        number=issue_data["number"],
        title=issue_data["title"],
        # ...
    )
    complexity = analyze_issue_complexity(issue)
    # ...

# AFTER:
# Clean imports - no path manipulation needed
from shared.models.github_issue import GitHubIssue
from shared.services.complexity_analyzer import analyze_issue_complexity

@app.post("/api/github-webhook")
async def handle_github_webhook(request: Request):
    # ... parse webhook data ...
    issue = GitHubIssue(  # No more alias needed
        number=issue_data["number"],
        title=issue_data["title"],
        # ...
    )
    complexity = analyze_issue_complexity(issue)
    # ...
```

**Search for Other Imports:**
```bash
# Find all imports from adws in app/server
grep -r "from adw" app/server/ --include="*.py"

# Find all sys.path manipulations
grep -r "sys.path" app/server/ --include="*.py"
```

**Acceptance Criteria:**
- [ ] No `sys.path.insert()` in any app/server file
- [ ] All GitHubIssue imports use shared.models
- [ ] All complexity analyzer imports use shared.services
- [ ] No imports from adws/adw_modules in app/server
- [ ] All webhook endpoints work correctly
- [ ] All tests pass

**Verification Commands:**
```bash
# Verify no path manipulation
grep -r "sys.path.insert" app/server/ --include="*.py" || echo "✅ No path manipulation found"

# Verify no adws imports
grep -r "from adw" app/server/ --include="*.py" || echo "✅ No adws imports found"

# Verify shared package imports
grep -r "from shared" app/server/ --include="*.py" | head -5

# Start server and test webhook endpoint
cd app/server && python server.py &
sleep 2
curl -X POST http://localhost:8000/api/github-webhook -H "Content-Type: application/json" -d '{"action": "opened", "issue": {"number": 1, "title": "Test", "body": "", "state": "open", "user": {"login": "test"}, "labels": [], "created_at": "2025-01-01", "updated_at": "2025-01-01", "html_url": "https://github.com/test/test/issues/1"}}'
```

---

## 4. Update adws/ Imports (1 workflow)

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

---

## 5. Validation and Cleanup (1 workflow)

### Workflow 5.1: Validate Import Structure and Remove Path Manipulation
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** Workflows 3.1, 4.1

**Input Files:**
- All Python files in project

**Output Files:**
- None (validation and cleanup)

**Tasks:**
1. Run comprehensive grep searches for path manipulation
2. Verify no circular dependencies exist
3. Test all Python imports resolve correctly
4. Run full test suite
5. Test webhook processing end-to-end
6. Test workflow creation end-to-end
7. Verify dependency hierarchy is correct
8. Document the new import structure
9. Update any relevant documentation

**Validation Checks:**

```bash
# 1. Check for any remaining path manipulation
echo "=== Checking for sys.path manipulation ==="
grep -r "sys.path.insert" . --include="*.py" --exclude-dir=venv --exclude-dir=node_modules || echo "✅ No path manipulation found"

# 2. Check for any remaining adws imports in app/server
echo "=== Checking for adws imports in app/server ==="
grep -r "from adw" app/server/ --include="*.py" || echo "✅ No adws imports in app/server"

# 3. Check for any remaining direct imports of moved types
echo "=== Checking for old import patterns ==="
grep -r "from adw_modules.data_types import GitHubIssue" . --include="*.py" || echo "✅ No old GitHubIssue imports"

# 4. Verify shared package structure
echo "=== Verifying shared package structure ==="
python -c "
import shared
import shared.models
import shared.services
from shared.models.github_issue import GitHubIssue
from shared.models.complexity import ComplexityLevel, ComplexityAnalysis
from shared.services.complexity_analyzer import analyze_issue_complexity
print('✅ All shared packages import correctly')
"

# 5. Check for circular dependencies
echo "=== Checking for circular dependencies ==="
python -c "
import sys
import importlib
import pkgutil

def check_circular_deps(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError as e:
        if 'circular' in str(e).lower():
            print(f'❌ Circular dependency in {module_name}: {e}')
            return False
        raise

modules = ['shared', 'shared.models', 'shared.services', 'app.server.server']
all_ok = all(check_circular_deps(m) for m in modules)
if all_ok:
    print('✅ No circular dependencies detected')
"

# 6. Verify dependency hierarchy
echo "=== Verifying dependency hierarchy ==="
python -c "
# Layer 1 (shared) should not import from Layers 2-4
import ast
import os
from pathlib import Path

def check_imports_in_file(filepath):
    with open(filepath, 'r') as f:
        try:
            tree = ast.parse(f.read())
        except:
            return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports

# Check shared/ doesn't import from app/ or adws/
violations = []
for py_file in Path('shared').rglob('*.py'):
    imports = check_imports_in_file(py_file)
    for imp in imports:
        if imp.startswith('app.') or imp.startswith('adws.'):
            violations.append(f'{py_file}: imports {imp}')

if violations:
    print('❌ Dependency hierarchy violations:')
    for v in violations:
        print(f'  {v}')
else:
    print('✅ Dependency hierarchy correct')
"

# 7. Test all imports resolve
echo "=== Testing import resolution ==="
python -m pytest --collect-only -q 2>&1 | grep -i "error" && echo "❌ Import errors found" || echo "✅ All imports resolve"

# 8. Run test suite
echo "=== Running test suite ==="
cd app/server && pytest -xvs

# 9. Test webhook endpoint
echo "=== Testing webhook endpoint ==="
cd app/server && python server.py &
SERVER_PID=$!
sleep 3

curl -X POST http://localhost:8000/api/github-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "action": "opened",
    "issue": {
      "number": 1,
      "title": "Test Import Structure",
      "body": "Testing the new shared package structure",
      "state": "open",
      "user": {"login": "test"},
      "labels": [{"name": "bug"}],
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z",
      "html_url": "https://github.com/test/test/issues/1"
    }
  }' && echo "✅ Webhook endpoint works"

kill $SERVER_PID
```

**Documentation Updates:**

Create/update documentation explaining the new structure:

```markdown
# Import Structure Documentation

## Layer Architecture

The codebase follows a 5-layer architecture to prevent circular dependencies:

**Layer 4: API Routes**
- `app/server/server.py`
- `app/server/routes/`
- Can import from: Layers 0-3

**Layer 3: Services**
- `app/server/services/`
- Can import from: Layers 0-2

**Layer 2: Core Business Logic**
- `app/server/core/`
- `adws/adw_modules/`
- Can import from: Layers 0-1

**Layer 1: Shared Models & Utilities**
- `shared/models/`
- `shared/services/`
- `shared/utils/`
- Can import from: Layer 0 only

**Layer 0: External Dependencies**
- `fastapi`, `anthropic`, `sqlite3`, etc.

## Shared Package Structure

```
shared/
├── models/                    # Shared data models
│   ├── github_issue.py       # GitHubIssue model
│   └── complexity.py         # Complexity types
├── services/                  # Shared services
│   └── complexity_analyzer.py # Complexity analysis
└── utils/                     # Shared utilities
    └── (future utilities)
```

## Import Guidelines

### ✅ DO:
- Import from lower layers
- Use absolute imports
- Import from shared package for common types

### ❌ DON'T:
- Use `sys.path.insert()`
- Import from higher layers
- Create circular dependencies
- Duplicate type definitions

## Example Imports

```python
# Layer 4 (routes) can import from shared (Layer 1)
from shared.models.github_issue import GitHubIssue
from shared.services.complexity_analyzer import analyze_issue_complexity

# Layer 2 (core) can import from shared (Layer 1)
from shared.models.github_issue import GitHubIssue

# Layer 1 (shared) can only import from external deps (Layer 0)
from anthropic import Anthropic
from dataclasses import dataclass
```
```

**Acceptance Criteria:**
- [ ] No `sys.path.insert()` anywhere in codebase
- [ ] No imports from adws in app/server
- [ ] No imports from app/server or adws in shared/
- [ ] All imports resolve correctly
- [ ] No circular dependencies
- [ ] Full test suite passes
- [ ] Webhook processing works end-to-end
- [ ] Workflow creation works end-to-end
- [ ] Documentation updated

**Verification Commands:**
See validation checks above.

---

## Summary Statistics

**Total Workflows:** 5 atomic units
**Total Estimated Time:** 5-8 hours (1-2 days)
**Parallelization Potential:** Low (workflows must be sequential)

**Workflow Dependencies:**
```
1.1 → 2.1 → 3.1 ↘
              → 5.1
       2.1 → 4.1 ↗
```

**Optimal Execution Order:**
- **Hour 1:** Workflow 1.1 - Create shared package structure
- **Hours 2-3:** Workflow 2.1 - Move types to shared
- **Hours 4-5:** Workflow 3.1 - Update app/server imports
- **Hours 6-7:** Workflow 4.1 - Update adws imports
- **Hour 8:** Workflow 5.1 - Validation and cleanup

---

## Expected Impact

### Before Phase 5:
```python
# app/server/server.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'adws'))
from adw_modules.data_types import GitHubIssue as ADWGitHubIssue
```

### After Phase 5:
```python
# app/server/server.py
from shared.models.github_issue import GitHubIssue
```

### Benefits:
- ✅ Clean, predictable imports
- ✅ Proper dependency hierarchy
- ✅ No circular dependency risk
- ✅ Easier refactoring in future
- ✅ Better IDE support
- ✅ Clearer module boundaries

---

## Risk Mitigation

**Risk:** Breaking existing code that depends on current import structure
**Mitigation:** Maintain backwards compatibility by re-exporting from original locations

**Risk:** Import conflicts or circular dependencies
**Mitigation:** Strict layer enforcement and validation checks

**Risk:** Tests fail after import changes
**Mitigation:** Comprehensive test suite run after each workflow

**Risk:** Missed imports during migration
**Mitigation:** Automated grep searches and import validation

---

## Next Steps

1. Review this detailed plan
2. Create feature branch: `refactor/phase5-fix-imports`
3. Execute Workflow 1.1 - Create shared package structure
4. Commit and verify
5. Execute Workflow 2.1 - Move shared types
6. Commit and verify
7. Execute Workflow 3.1 - Update app/server imports
8. Commit and verify
9. Execute Workflow 4.1 - Update adws imports
10. Commit and verify
11. Execute Workflow 5.1 - Final validation
12. Merge to main

---

**Document Status:** Ready for Implementation
**Created:** 2025-11-17
**Last Updated:** 2025-11-17
**Related:** [REFACTORING_PLAN.md](../REFACTORING_PLAN.md), [REFACTORING_ANALYSIS.md](../REFACTORING_ANALYSIS.md)
