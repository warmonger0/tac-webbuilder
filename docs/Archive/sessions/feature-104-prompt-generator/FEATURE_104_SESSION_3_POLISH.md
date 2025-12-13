# Feature #104 Session 3: Polish & Complete

## Context
Load template: `/prime`

**Depends on**: Sessions 1 & 2 complete

## Task
Add shell wrapper, update docs, mark feature complete.

## Workflow

### 1. Shell Wrapper (5 min)

Create `scripts/gen_prompt.sh`:
```bash
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

export POSTGRES_HOST=localhost POSTGRES_PORT=5432
export POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user
export POSTGRES_PASSWORD=changeme DB_TYPE=postgresql

python3 scripts/generate_prompt.py "$@"
```

```bash
chmod +x scripts/gen_prompt.sh
./scripts/gen_prompt.sh --list
./scripts/gen_prompt.sh 49
```

### 2. Finalize (10 min)
```bash
# Update Plans Panel (completed)
curl -X PATCH http://localhost:8002/api/v1/planned-features/104 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "actual_hours": 2.0,
    "completed_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "completion_notes": "All 3 sessions complete. Generator saves 15-18 min/prompt."
  }'

# Commit (NO AI references)
git add scripts/gen_prompt.sh
git commit -m "feat: Shell wrapper for prompt generator (Session 3/3)

Complete Plan-to-Prompt Generator feature.

- Created gen_prompt.sh (auto-sets env vars)
- Simplifies usage: ./scripts/gen_prompt.sh 49

All sessions: Basic generator + Codebase analyzer + Polish
Result: 15-18 min saved per prompt

Location: scripts/gen_prompt.sh"

# Update docs
/updatedocs
```

## Success Criteria
- ✅ `./scripts/gen_prompt.sh 49` works
- ✅ Plans Panel #104 marked completed
- ✅ Documentation updated

## Time: 0.25h (15 min)

## Done!
Feature complete. Use generator for remaining 44 features.
