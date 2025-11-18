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
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
