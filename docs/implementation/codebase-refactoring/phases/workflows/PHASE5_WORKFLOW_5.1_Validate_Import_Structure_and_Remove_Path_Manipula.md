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
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
