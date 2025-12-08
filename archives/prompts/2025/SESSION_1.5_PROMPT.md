# Task: Fix Pattern Detection System & Extract Real Orchestration Patterns

## Context
I'm working on the tac-webbuilder project. Session 1 audit revealed that the pattern detection system created a meaningless pattern (`sdlc:full:all`) that treats entire ADW workflows as patterns, resulting in inflated savings estimates and 78,167 duplicate database rows.

## Objective
Clean up the pattern detection system and implement proper pattern detection that identifies **deterministic tool orchestration sequences** within ADW phases, not the workflows themselves.

## Background Information
- **Database:** `app/server/db/workflow_history.db`
- **Pattern Tables:** `operation_patterns`, `pattern_occurrences`, `hook_events`
- **Current State:**
  - 78,167 junk rows in `pattern_occurrences` (3,257 duplicates per workflow)
  - 1 meaningless pattern: `sdlc:full:all`
  - 39,132 unprocessed hook events with real pattern data
  - No UNIQUE constraint on `(pattern_id, workflow_id)`
- **Files to Fix:**
  - `app/server/core/pattern_detector.py` (lines 144-149)
  - `app/server/db/migrations/` (new migration needed)
  - `scripts/` (new analysis script needed)

## What Patterns SHOULD Detect

**CORRECT:** Deterministic tool orchestration sequences within ADW phases

### Example 1: Test-Fix-Retry Pattern
```
Hook event sequence seen 50 times:
1. Bash → "pytest" → FAILED (missing import)
2. Read → test file
3. Grep → find import section
4. Edit → add missing import
5. Bash → "pytest" → PASSED

Pattern: "orchestration:test_import_fix:pytest"
Deterministic? YES - Same sequence, same error type, same fix
Value: Skip LLM orchestration, use direct function
```

### Example 2: Type Error Auto-Fix Pattern
```
Hook event sequence seen 30 times:
1. Bash → "tsc --noEmit" → Property 'X' missing in type 'Y'
2. Read → type definition file
3. Edit → add missing property
4. Bash → "tsc --noEmit" → PASSED

Pattern: "orchestration:type_missing_property:typescript"
Deterministic? YES - Same tool sequence, same resolution
Value: Auto-fix without LLM intervention
```

### Example 3: Lint Error Pattern
```
Hook event sequence seen 100 times:
1. Bash → "ruff check" → E501 line too long
2. Read → file with long line
3. Edit → break line at appropriate point
4. Bash → "ruff check" → PASSED

Pattern: "orchestration:lint_line_length:python"
Deterministic? YES - Same error, same fix strategy
Value: Add to pre-lint auto-fix step
```

**INCORRECT:** Entire workflows or phases
```
❌ "sdlc:full:all" - ADW workflows are not patterns
❌ "test:full:phase" - Test phase is not a pattern
❌ "build:complete:workflow" - Workflow is not a pattern
```

**Key Insight:** We're looking for deterministic sub-operations that waste LLM tokens on predictable orchestration. If the LLM is just routing between tools in a repeatable way, that's a pattern worth extracting.

---

## Step-by-Step Instructions

### Step 1: Clean Database - Remove Junk Pattern (10 min)

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Connect to database
sqlite3 db/workflow_history.db
```

```sql
-- Verify the junk pattern exists
SELECT
    id,
    pattern_signature,
    occurrence_count,
    potential_monthly_savings
FROM operation_patterns
WHERE pattern_signature = 'sdlc:full:all';

-- Expected: id=1, occurrence_count=78167, savings=$183844

-- Delete pattern (CASCADE will remove occurrences)
DELETE FROM operation_patterns
WHERE pattern_signature = 'sdlc:full:all';

-- Verify cleanup
SELECT COUNT(*) FROM operation_patterns;  -- Should be 0
SELECT COUNT(*) FROM pattern_occurrences; -- Should be 0

-- Exit
.quit
```

### Step 2: Add Schema Protection (15 min)

Create migration to prevent future duplicates:

```bash
cd app/server/db/migrations
```

Create file: `015_add_pattern_unique_constraint.sql`

```sql
-- Migration 015: Add unique constraint to pattern_occurrences
-- Prevents duplicate pattern detections for same workflow

-- Add unique index on (pattern_id, workflow_id)
CREATE UNIQUE INDEX IF NOT EXISTS idx_pattern_occurrence_unique
ON pattern_occurrences(pattern_id, workflow_id);

-- Verify index created
SELECT sql FROM sqlite_master
WHERE type = 'index'
AND name = 'idx_pattern_occurrence_unique';
```

Apply migration:

```bash
# Test migration on backup
cp db/workflow_history.db db/workflow_history.db.backup

# Apply migration
sqlite3 db/workflow_history.db < db/migrations/015_add_pattern_unique_constraint.sql

# Verify
sqlite3 db/workflow_history.db ".schema pattern_occurrences"
# Should show: CREATE UNIQUE INDEX idx_pattern_occurrence_unique...
```

### Step 3: Fix Pattern Detector Logic (20 min)

**File:** `app/server/core/pattern_detector.py`

**Current code (lines 144-149):**
```python
elif "sdlc" in template_lower or "zte" in template_lower:
    # SDLC and Zero-Touch workflows are full lifecycle
    return "sdlc:full:all"
elif "patch" in template_lower or "lightweight" in template_lower:
    # Quick fix workflows
    return "patch:quick:all"
```

**Replace with:**
```python
elif "patch" in template_lower or "lightweight" in template_lower:
    # Quick fix workflows - only if they represent specific operations
    # Don't return full workflow patterns
    return None
# Remove sdlc:full:all pattern completely
# ADW workflows are not patterns - patterns exist WITHIN workflows
```

**Rationale:**
- Full workflows/phases are not patterns
- Patterns are deterministic tool sequences within phases
- Template-based patterns should only detect specific operations (test, build, format)
- Not entire orchestration flows

**After editing, verify:**
```bash
cd app/server
grep -n "sdlc:full:all" core/pattern_detector.py
# Should return no results
```

### Step 4: Analyze Hook Events for Real Patterns (60-90 min)

Create pattern sequence analyzer:

**File:** `scripts/analyze_hook_sequences.py`

```python
#!/usr/bin/env python3
"""
Analyze hook events to detect repeated tool orchestration patterns.

Identifies deterministic sequences where LLM is just routing between tools
predictably, wasting tokens on orchestration that could be code.
"""

import sys
import sqlite3
from pathlib import Path
from collections import defaultdict, Counter
import json

project_root = Path(__file__).parent.parent
db_path = project_root / "app" / "server" / "db" / "workflow_history.db"


def extract_tool_sequences(events):
    """
    Extract tool call sequences from hook events.

    Returns sequences grouped by session/workflow.
    """
    sequences = defaultdict(list)

    for event in events:
        session_id = event['session_id'] or event['workflow_id'] or 'unknown'
        tool_name = event['tool_name']
        event_type = event['event_type']

        if tool_name and event_type in ('PreToolUse', 'PostToolUse'):
            sequences[session_id].append({
                'tool': tool_name,
                'type': event_type,
                'timestamp': event['timestamp'],
                'payload': json.loads(event['payload']) if event['payload'] else {}
            })

    return sequences


def find_common_sequences(sequences, min_length=3, min_occurrences=5):
    """
    Find tool sequences that occur frequently.

    Args:
        sequences: Dict of session_id -> list of tool events
        min_length: Minimum sequence length to consider
        min_occurrences: Minimum times a sequence must occur

    Returns:
        List of (sequence_pattern, count, example_sessions)
    """
    # Extract tool-only sequences
    tool_patterns = []

    for session_id, events in sequences.items():
        # Get just the tool names in order
        tools = [e['tool'] for e in events]

        # Extract subsequences of various lengths
        for length in range(min_length, min(len(tools) + 1, 10)):
            for i in range(len(tools) - length + 1):
                subseq = tuple(tools[i:i+length])
                tool_patterns.append((subseq, session_id))

    # Count occurrences
    pattern_counts = Counter([p[0] for p in tool_patterns])

    # Filter by min_occurrences
    common_patterns = []
    for pattern, count in pattern_counts.items():
        if count >= min_occurrences:
            # Find example sessions
            examples = [s for p, s in tool_patterns if p == pattern][:3]
            common_patterns.append((pattern, count, examples))

    # Sort by frequency
    common_patterns.sort(key=lambda x: x[1], reverse=True)

    return common_patterns


def analyze_pattern_context(pattern_tuple, sequences, example_sessions):
    """
    Analyze context around a pattern to determine if it's deterministic.

    Returns dict with:
    - success_rate: How often does this sequence lead to success?
    - common_errors: What errors typically trigger this sequence?
    - common_files: What files are typically involved?
    """
    contexts = []

    for session_id in example_sessions:
        events = sequences[session_id]

        # Find where pattern occurs in this session
        tools = [e['tool'] for e in events]
        pattern_str = [str(t) for t in pattern_tuple]

        # Extract context (errors, file patterns, outcomes)
        context = {
            'session': session_id,
            'tools_before': [],
            'tools_after': [],
            'bash_outputs': [],
            'files_touched': []
        }

        for event in events:
            if event['tool'] == 'Bash':
                payload = event['payload']
                if 'result' in payload:
                    context['bash_outputs'].append(payload['result'])
            elif event['tool'] in ('Read', 'Edit', 'Write'):
                payload = event['payload']
                if 'file_path' in payload:
                    context['files_touched'].append(payload['file_path'])

        contexts.append(context)

    return contexts


def main():
    print("🔍 Analyzing hook events for orchestration patterns...")
    print()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all hook events
    cursor.execute("""
        SELECT
            event_id,
            event_type,
            session_id,
            workflow_id,
            timestamp,
            tool_name,
            payload
        FROM hook_events
        WHERE event_type IN ('PreToolUse', 'PostToolUse')
        ORDER BY timestamp ASC
    """)

    events = [dict(row) for row in cursor.fetchall()]
    total = len(events)

    print(f"📊 Total hook events: {total:,}")
    print()

    # Extract sequences
    print("🔄 Extracting tool sequences...")
    sequences = extract_tool_sequences(events)
    print(f"   Found {len(sequences):,} unique sessions")
    print()

    # Find common patterns
    print("🎯 Finding repeated patterns (min 5 occurrences, min length 3)...")
    patterns = find_common_sequences(sequences, min_length=3, min_occurrences=5)
    print(f"   Found {len(patterns):,} repeated patterns")
    print()

    # Display top patterns
    print("=" * 80)
    print("TOP 20 ORCHESTRATION PATTERNS")
    print("=" * 80)
    print()

    for i, (pattern, count, examples) in enumerate(patterns[:20], 1):
        print(f"{i:2}. Pattern (occurs {count} times):")
        print(f"    Sequence: {' → '.join(pattern)}")
        print(f"    Example sessions: {', '.join(examples[:3])}")

        # Analyze context
        contexts = analyze_pattern_context(pattern, sequences, examples[:3])

        # Try to detect what this pattern does
        tools_involved = set(pattern)

        if 'Bash' in tools_involved and any(t in tools_involved for t in ['Read', 'Edit']):
            print(f"    ⚡ Likely: Test/Build/Lint failure → fix → retry pattern")
        elif 'Grep' in tools_involved and 'Edit' in tools_involved:
            print(f"    ⚡ Likely: Search → modify pattern")
        elif pattern.count('Bash') >= 2:
            print(f"    ⚡ Likely: Command → verify → rerun pattern")

        print()

    print("=" * 80)
    print()

    # Suggest pattern candidates
    print("💡 PATTERN CANDIDATES FOR AUTOMATION:")
    print()

    high_value = [
        p for p in patterns
        if p[1] >= 10  # Occurs at least 10 times
        and len(p[0]) >= 3  # At least 3 tools
        and 'Bash' in p[0]  # Involves external command
    ]

    for pattern, count, examples in high_value[:10]:
        print(f"   🎯 {' → '.join(pattern)}")
        print(f"      Occurrences: {count}")
        print(f"      Potential savings: ~{count * 2000} tokens (est.)")
        print()

    conn.close()

    print("✅ Analysis complete!")
    print()
    print("NEXT STEPS:")
    print("1. Review pattern candidates above")
    print("2. For each high-value pattern:")
    print("   - Examine hook event details to understand context")
    print("   - Verify it's deterministic (same input → same output)")
    print("   - Estimate token savings (LLM orchestration vs direct function)")
    print("   - Create pattern definition in operation_patterns")
    print("3. Implement deterministic handlers for approved patterns")


if __name__ == "__main__":
    main()
```

**Run the analyzer:**

```bash
cd /Users/Warmonger0/tac/tac-webbuilder
chmod +x scripts/analyze_hook_sequences.py
python3 scripts/analyze_hook_sequences.py
```

**Expected output:**
- List of repeated tool sequences
- Frequency counts
- Pattern candidates for automation
- Estimated token savings per pattern

### Step 5: Manual Pattern Review (30 min)

For each pattern candidate from Step 4:

1. **Examine hook event details:**
   ```sql
   -- Find sessions with this pattern
   SELECT session_id, workflow_id, tool_name, timestamp, payload
   FROM hook_events
   WHERE session_id IN ('<example_session_id>')
   ORDER BY timestamp;
   ```

2. **Verify determinism:**
   - Same tool sequence? ✓
   - Same error/context? ✓
   - Same resolution? ✓
   - Success rate > 90%? ✓

3. **Calculate value:**
   - Token cost with LLM orchestration: ~2,000 per occurrence
   - Token cost with deterministic function: ~0
   - Monthly savings: occurrences × 2,000 × token_cost

4. **Create pattern definition:**
   ```python
   # Example pattern for manual testing
   pattern = {
       'signature': 'orchestration:test_import_fix:pytest',
       'type': 'orchestration',
       'tool_sequence': ['Bash', 'Read', 'Grep', 'Edit', 'Bash'],
       'trigger_context': {
           'bash_output_contains': 'ModuleNotFoundError',
           'file_pattern': 'test_*.py'
       },
       'deterministic_handler': 'handlers/test_import_fix.py',
       'estimated_savings_per_occurrence': 2000  # tokens
   }
   ```

### Step 6: Update Documentation (15 min)

**File:** `docs/features/observability-and-logging.md`

Add section after "Pattern Detection" heading:

```markdown
### What Patterns Represent

Patterns are **deterministic tool orchestration sequences** that occur within ADW phases. When the LLM repeatedly performs the same tool routing for the same type of problem, that's a pattern worth extracting.

#### Example Patterns

**Test-Import-Fix Pattern:**
```
Sequence: Bash(pytest) → Read(test_file) → Grep(imports) → Edit(add_import) → Bash(pytest)
Trigger: ModuleNotFoundError in pytest output
Handler: Auto-add missing import from common libraries
Savings: ~2,000 tokens per occurrence (skip LLM orchestration)
```

**Type-Annotation Pattern:**
```
Sequence: Bash(tsc) → Read(type_file) → Edit(add_property) → Bash(tsc)
Trigger: "Property 'X' is missing in type 'Y'"
Handler: Auto-add missing property with inferred type
Savings: ~1,500 tokens per occurrence
```

**Lint-Line-Length Pattern:**
```
Sequence: Bash(ruff) → Read(file) → Edit(break_line) → Bash(ruff)
Trigger: E501 line too long error
Handler: Auto-format long lines (already handled by pre-commit)
Savings: ~500 tokens per occurrence
```

#### What Patterns Are NOT

- ❌ Full ADW workflows (e.g., "sdlc:full:all")
- ❌ Individual phases (e.g., "test:complete:phase")
- ❌ Single tool calls (e.g., "bash:pytest:run")
- ❌ Non-deterministic sequences (different resolution each time)

Patterns must be:
- Repeatable (same sequence)
- Deterministic (same input → same output)
- Valuable (saves significant tokens)
- Automatable (can be a function, not requiring LLM reasoning)
```

**File:** `SESSION_1_AUDIT_REPORT.md`

Update the findings section:

```markdown
## CORRECTED FINDINGS (After User Clarification)

**Pattern Detection Bug:**
- System created meaningless "sdlc:full:all" pattern
- Treated entire ADW workflows as patterns (wrong)
- All 78,167 occurrences are junk data
- Savings estimate of $183K is completely invalid

**What Patterns Should Be:**
- Deterministic tool orchestration sequences WITHIN phases
- Example: Bash→Read→Edit→Bash (test fail → fix import → rerun)
- LLM just routing between tools predictably = pattern opportunity
- Extract to deterministic function, skip LLM orchestration

**Actual State:**
- Real patterns: Unknown (need to analyze 39K hook events)
- Junk patterns: 1 (sdlc:full:all - now deleted)
- Pattern detection logic: Fixed to prevent future junk patterns
- Hook events ready for analysis: 39,132 unprocessed events
```

---

## Success Criteria

- ✅ Pattern `sdlc:full:all` deleted from database
- ✅ All 78,167 junk rows removed from `pattern_occurrences`
- ✅ UNIQUE constraint added: `idx_pattern_occurrence_unique`
- ✅ Pattern detector fixed: No more full-workflow patterns
- ✅ Hook sequence analyzer created and run
- ✅ Top 10-20 pattern candidates identified
- ✅ Documentation updated with correct pattern definition
- ✅ Session 1 audit report corrected

**Bonus:**
- ✅ At least 3 high-value orchestration patterns identified
- ✅ Estimated token savings calculated for each pattern
- ✅ Pattern handler stubs created for top patterns

---

## Files Expected to Change

**Modified:**
- `app/server/core/pattern_detector.py` - Remove sdlc:full:all logic
- `docs/features/observability-and-logging.md` - Add pattern definition
- `SESSION_1_AUDIT_REPORT.md` - Correct findings

**Created:**
- `app/server/db/migrations/015_add_pattern_unique_constraint.sql` - Schema fix
- `scripts/analyze_hook_sequences.py` - Pattern sequence analyzer
- `docs/patterns/` - Pattern definitions directory (optional)

**Database Changes:**
- `operation_patterns`: 1 row → 0 rows (delete junk)
- `pattern_occurrences`: 78,167 rows → 0 rows (cascade delete)
- `pattern_occurrences`: New UNIQUE index on (pattern_id, workflow_id)

---

## Troubleshooting

### If database is locked:
```bash
# Find process using database
lsof | grep workflow_history.db

# Kill if needed (gracefully)
kill <PID>
```

### If migration fails:
```bash
# Restore backup
cp app/server/db/workflow_history.db.backup app/server/db/workflow_history.db

# Check for existing index
sqlite3 app/server/db/workflow_history.db \
  "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_pattern_occurrence_unique';"

# Drop if exists, then retry
sqlite3 app/server/db/workflow_history.db \
  "DROP INDEX IF EXISTS idx_pattern_occurrence_unique;"
```

### If hook events are empty:
```bash
# Check hook events exist
sqlite3 app/server/db/workflow_history.db \
  "SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM hook_events;"

# If 0 rows: Hook event collection not running
# Solution: Start backend with hook collection enabled
```

### If no patterns found:
This is actually GOOD - it means:
- ADW workflows are already optimized with external tools
- LLM isn't wasting tokens on predictable orchestration
- Pattern system is working as designed (no false positives)

Consider:
- Analyzing non-ADW workflows if they exist
- Waiting for more hook events to accumulate
- Pattern detection may not be valuable for this codebase (and that's okay!)

---

## Estimated Time

- Step 1 (Clean DB): 10 min
- Step 2 (Schema): 15 min
- Step 3 (Fix detector): 20 min
- Step 4 (Analyze hooks): 60-90 min
- Step 5 (Review): 30 min
- Step 6 (Docs): 15 min

**Total: 2.5 - 3 hours**

---

## Next Steps

After Session 1.5 complete, report back with:
- "✅ Session 1.5 complete - Pattern system cleaned and analyzed"
- Number of real orchestration patterns found
- Top 3 pattern candidates with estimated savings
- Recommendation: Proceed with Session 2 (Port Pool) or investigate patterns further

**Next session:** Session 2 - Port Pool Implementation (3-4 hours)

---

**Ready to copy into a new chat!**

This fixes the fundamental misunderstanding of what patterns should represent and sets up proper orchestration pattern detection.
