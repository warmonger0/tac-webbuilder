# Feature #104 Session 1: Basic Prompt Generator

## Context
Load template: `/prime` then `.claude/templates/IMPLEMENTATION_PROMPT_TEMPLATE.md`

## Task
Build MVP generator that queries `planned_features` DB and fills template placeholders.

**Scope**: Basic substitution only. NO codebase analysis (Session 2).

## Workflow

### 1. Investigate (5 min)
```bash
# Verify template exists
ls .claude/templates/IMPLEMENTATION_PROMPT_TEMPLATE.md

# Check planned_features service
python3 -c "
import sys; sys.path.insert(0, 'app/server')
from services.planned_features_service import PlannedFeaturesService
svc = PlannedFeaturesService()
print(f'{len(svc.get_all())} features')
print(svc.get_by_id(104).title if svc.get_by_id(104) else 'Not found')
"
```

### 2. Implement (30 min)

Create `scripts/generate_prompt.py`:
- Class: `PromptGenerator`
- Methods: `generate(feature_id)`, `list_features()`, `_fill_template()`
- Substitutions: `[Type]`, `[ID]`, `[Title]`, `[Priority]`, `[Hours]`
- Filename logic: `QUICK_WIN` if ≤2h else `TYPE_ID_slug.md`

**Template reference**: Lines 1-8 (Task Summary section)

**Key logic**:
```python
replacements = {
    "[Type]": feature.item_type.capitalize(),
    "[ID]": str(feature.id),
    "[Title]": feature.title,
    "[High/Medium/Low]": feature.priority or "Medium",
    "[X hours]": str(feature.estimated_hours) or "TBD"
}
```

### 3. Test (10 min)
```bash
python3 scripts/generate_prompt.py --list
python3 scripts/generate_prompt.py 49  # Bug (0.25h)
cat QUICK_WIN_49_*.md | head -20       # Verify structure
```

### 4. Quality (10 min)
```bash
ruff check scripts/generate_prompt.py --fix
mypy scripts/generate_prompt.py --ignore-missing-imports

# Mark in progress
curl -X PATCH http://localhost:8002/api/v1/planned-features/104 \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress", "started_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}'

# Commit (NO AI references)
git add scripts/generate_prompt.py
git commit -m "feat: Add basic prompt generator (Session 1/3)

MVP generator queries planned_features DB and fills template.

- Created scripts/generate_prompt.py (~150 lines)
- Queries PlannedFeaturesService by ID
- Basic template substitutions (type, ID, title, priority, hours)
- Filename generation (QUICK_WIN vs TYPE logic)
- CLI: --list and feature ID generation

Result: Working MVP, saves 5-10 min per prompt
Deferred: Codebase analysis (Session 2)

Location: scripts/generate_prompt.py"
```

## Success Criteria
- ✅ Generator creates valid prompts from DB
- ✅ Filename logic correct (QUICK_WIN ≤2h)
- ✅ Template structure preserved
- ✅ 0 linting/type errors
- ❌ Manual completion needed (Session 2 will automate)

## Time: 1.0h (55 min implementation + 5 min buffer)

## Next
Session 2: Add codebase analyzer for file/function discovery
