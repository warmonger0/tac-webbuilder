# Feature #104 Session 2: Codebase Analyzer

## Context
Load template: `/prime`

**Depends on**: Session 1 complete (basic generator working)

## Task
Add intelligent codebase analysis to auto-discover relevant files/functions.

**Scope**: Backend/frontend file search, function discovery, test suggestions.

## Workflow

### 1. Investigate (5 min)
```bash
# Verify Session 1 works
./scripts/generate_prompt.py 66
cat QUICK_WIN_66_*.md | grep "TODO:"  # Should see manual completion notes
```

### 2. Implement (35 min)

**Create module**: `app/server/utils/codebase_analyzer/`
- `__init__.py`
- `analyzer.py` (~200 lines)

**Class**: `CodebaseAnalyzer`

**Methods**:
1. `find_relevant_files(feature)` → dict with backend/frontend/test files
2. `_extract_keywords(title, desc)` → remove stopwords, top 10 keywords
3. `_search_python_files(keywords)` → relevance-scored matches
4. `_search_ts_files(keywords)` → frontend matches
5. `_find_functions(keywords)` → function names matching keywords
6. `_suggest_locations(feature, context)` → where to implement

**Integration**:
Modify `scripts/generate_prompt.py`:
```python
# Add to __init__
self.analyzer = CodebaseAnalyzer(project_root)

# In generate()
context = self.analyzer.find_relevant_files(feature)
prompt = self._fill_template(feature, context)  # Pass context

# New method
def _generate_codebase_section(feature, context):
    # Build markdown with backend/frontend files, functions, suggestions
    return "\n".join(sections)
```

### 3. Test (10 min)
```bash
# Test analyzer directly
python3 -c "
import sys; sys.path.insert(0, 'app/server')
from utils.codebase_analyzer.analyzer import CodebaseAnalyzer
from services.planned_features_service import PlannedFeaturesService

analyzer = CodebaseAnalyzer()
feature = PlannedFeaturesService().get_by_id(66)
context = analyzer.find_relevant_files(feature)

print(f'Backend: {len(context[\"backend_files\"])}')
print(f'Frontend: {len(context[\"frontend_files\"])}')
print(f'Functions: {len(context[\"related_functions\"])}')
"

# Test integrated
./scripts/generate_prompt.py 66
cat QUICK_WIN_66_*.md | grep -A5 "Relevant Backend Files"
```

### 4. Quality (10 min)
```bash
ruff check app/server/utils/codebase_analyzer/ --fix
ruff check scripts/generate_prompt.py --fix
mypy app/server/utils/codebase_analyzer/analyzer.py --ignore-missing-imports

# Commit (NO AI references)
git add app/server/utils/codebase_analyzer/ scripts/generate_prompt.py
git commit -m "feat: Add codebase analyzer (Session 2/3)

Intelligent file/function discovery for automated prompt context.

- Created utils/codebase_analyzer module (~200 lines)
- Keyword extraction, backend/frontend detection
- File search with relevance scoring
- Function discovery, test suggestions
- Integrated with Session 1 generator

Result: +10 min savings per prompt (15-18 min total)
Next: Session 3 (shell wrapper, docs)

Location: app/server/utils/codebase_analyzer/analyzer.py"
```

## Success Criteria
- ✅ Analyzer finds relevant files for multiple feature types
- ✅ Generated prompts include codebase context
- ✅ Keyword extraction works (removes stopwords)
- ✅ 0 linting/type errors

## Time: 0.75h (45 min)

## Next
Session 3: Shell wrapper + /updatedocs + mark complete
