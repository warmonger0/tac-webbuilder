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
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
