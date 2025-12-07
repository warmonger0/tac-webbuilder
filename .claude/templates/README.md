# Session Prompt Templates

This directory contains reusable templates for creating compact, focused session prompts.

## Problem

Original session prompts were **1,000-1,300 lines** with:
- Full code implementations (~600 lines)
- Complete test files (~200 lines)
- Detailed bash commands (~150 lines)
- Extensive troubleshooting (~100 lines)

This made sessions:
- ❌ Hard to read (5+ minutes just to scan)
- ❌ Difficult to execute (too many details to track)
- ❌ Copy-paste heavy (mostly duplicated boilerplate)
- ❌ Growing complexity (each session bigger than last)

## Solution

**Template-based prompts: ~300-400 lines** (3x smaller)

Templates provide:
- ✅ Reusable boilerplate code structures
- ✅ Standard patterns across sessions
- ✅ Quick reference (not full implementation)
- ✅ Focus on session-specific details only

## Available Templates

| Template | Purpose | Use When |
|----------|---------|----------|
| `DATABASE_MIGRATION.md` | SQL table creation, indexes, triggers | Adding new database tables |
| `SERVICE_LAYER.md` | Repository pattern, CRUD operations | Creating business logic services |
| `CLI_TOOL.md` | Argparse, interactive prompts, output formatting | Building command-line tools |
| `PYTEST_TESTS.md` | Fixtures, mocking, assertions, patterns | Writing pytest tests |
| `SESSION_PROMPT_TEMPLATE.md` | Complete session structure | Creating new session prompts |

## How to Use

### For Session Prompt Creators (Claude)

**Instead of:**
```markdown
Create file: service.py

```python
# 200 lines of boilerplate code
class MyService:
    def __init__(self):
        # 50 lines of standard setup
    def get_all(self):
        # 30 lines of standard CRUD
```
```

**Do this:**
```markdown
Create: `app/server/services/my_service.py`

**Template:** See `.claude/templates/SERVICE_LAYER.md`

**Specifics for this session:**
- Service name: `MyService`
- Additional methods:
  - `get_by_status(status)` - Filter by status
  - `calculate_metrics()` - Custom business logic
```

### For Session Executors (Claude in Execution Chat)

**When you see:**
```markdown
**Template:** See `.claude/templates/SERVICE_LAYER.md`
```

**You should:**
1. Read the referenced template file
2. Use the template structure as foundation
3. Apply the session-specific customizations listed
4. Fill in the blanks with domain-specific logic

## Template Usage Examples

### Example 1: Database Migration

**Prompt says:**
```markdown
### Step 1: Database Migration (30 min)

**Create:** `app/server/db/migrations/016_add_pattern_approvals.sql`

**Template:** `.claude/templates/DATABASE_MIGRATION.md`

**Specifics:**
- Table: `pattern_approvals`
- Columns: pattern_id, status, reviewed_by, confidence_score
- Index: `idx_pattern_approvals_status` on `status`
```

**You do:**
1. Read `DATABASE_MIGRATION.md` template
2. Copy the standard structure
3. Replace placeholders:
   - `<table_name>` → `pattern_approvals`
   - Add the 4 specified columns
   - Add the status index
4. Run migration commands from template

### Example 2: Service Layer

**Prompt says:**
```markdown
### Step 2: Service Layer (60 min)

**Create:** `app/server/services/pattern_review_service.py`

**Template:** `.claude/templates/SERVICE_LAYER.md`

**Specifics:**
- Model: `PatternReviewItem`
- Methods: `get_pending_patterns()`, `approve_pattern()`, `reject_pattern()`
```

**You do:**
1. Read `SERVICE_LAYER.md` template
2. Use the dataclass + service class structure
3. Rename classes to `PatternReviewItem` and `PatternReviewService`
4. Implement the 3 specific methods (not the template's CRUD)
5. Keep the template's patterns for logging, connection handling, etc.

### Example 3: CLI Tool

**Prompt says:**
```markdown
### Step 3: CLI Tool (90 min)

**Create:** `scripts/review_patterns.py`

**Template:** `.claude/templates/CLI_TOOL.md`

**Custom interactive prompts:**
```python
print("Actions: [a]pprove, [r]eject, [s]kip")
# Handle a/r/s choices
```
```

**You do:**
1. Read `CLI_TOOL.md` template
2. Use the argparse structure
3. Replace generic action with approve/reject/skip logic
4. Keep template's error handling, help text, etc.

## Benefits

### Before Templates (Session 5: 1,336 lines)

```markdown
# 200 lines of context
# 600 lines of full code implementation
# 200 lines of complete test code
# 150 lines of bash commands
# 100 lines of troubleshooting
# 86 lines of completion template
```

**Problems:**
- Takes 10+ minutes to read
- Overwhelming amount of code
- Hard to find session-specific logic

### After Templates (Estimated ~400 lines)

```markdown
# 100 lines of context
# 150 lines of template references + specifics
# 50 lines of tests (reference template)
# 50 lines of integration steps
# 50 lines of completion template
```

**Benefits:**
- Takes 2-3 minutes to read
- Focus on what's unique to this session
- Templates handle the boilerplate

## Creating New Templates

When you notice a pattern repeating across 3+ sessions:

1. **Extract the pattern** into `.claude/templates/<PATTERN_NAME>.md`
2. **Include:**
   - Standard structure with placeholders
   - Common usage patterns
   - Testing/verification steps
   - Quick reference commands
3. **Update this README** with new template entry
4. **Reference in future prompts** instead of duplicating code

## Template Maintenance

Templates should be:
- ✅ **General** - Work across multiple use cases
- ✅ **Well-commented** - Explain why, not just what
- ✅ **Self-contained** - Include usage examples
- ✅ **Tested** - Based on working code from previous sessions

Update templates when:
- Better patterns emerge from new sessions
- Common bugs/issues are discovered
- PostgreSQL/SQLite differences are found

## Sessions Using Templates

- ✅ Session 6: Pattern Review System (converted to template-based)
- 📋 Session 7+: Will use templates from creation

## Estimated Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Prompt size | 1,300 lines | 400 lines | **3x smaller** |
| Read time | 10 min | 3 min | **3x faster** |
| Focus on specifics | 20% | 80% | **4x clearer** |
| Maintenance burden | High | Low | **Reusable** |

---

**Result:** More focused, maintainable, and efficient session prompts. 🎯
