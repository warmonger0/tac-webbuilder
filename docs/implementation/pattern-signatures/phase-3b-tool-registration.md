# Phase 3B: Tool Registration & Activation

**Duration:** 1 day
**Dependencies:** Phase 3A complete (pattern matcher working)
**Priority:** HIGH - Bridges patterns to executable tools
**Status:** Ready to implement

---

## Overview

Set up the tool registry system that connects detected patterns to executable Python scripts. This phase creates the infrastructure for:
1. Registering specialized tools in the database
2. Linking patterns to their corresponding tools
3. Activating patterns for automatic routing

**This phase does NOT include:**
- Pattern matching logic (that's Phase 3A - already done)
- Tool execution (that's Phase 3C)
- ADW integration (that's Phase 3C)

**Why separate this?** Tool registration is a one-time setup task that can be tested independently before integrating with the routing system.

---

## Goals

- ✅ Create tool registration system
- ✅ Register existing external tools (test, build)
- ✅ Link patterns to tools automatically
- ✅ Implement pattern activation workflow
- ✅ Validate tool metadata in database

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  STEP 1: REGISTER TOOLS                                  │
│  scripts/register_tools.py                               │
│                                                           │
│  INSERT INTO adw_tools:                                  │
│  - run_test_workflow                                     │
│  - run_build_workflow                                    │
│  - generate_tests (experimental)                         │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 2: LINK PATTERNS TO TOOLS                          │
│  scripts/link_patterns_to_tools.py                       │
│                                                           │
│  UPDATE operation_patterns SET                           │
│    tool_name = 'run_test_workflow',                      │
│    tool_script_path = 'adws/adw_test_workflow.py'       │
│  WHERE pattern_signature = 'test:pytest:backend'         │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 3: ACTIVATE PATTERNS                               │
│  scripts/activate_patterns.py                            │
│                                                           │
│  UPDATE operation_patterns SET                           │
│    automation_status = 'active'                          │
│  WHERE confidence_score >= 70                            │
│    AND occurrence_count >= 3                             │
│    AND tool_name IS NOT NULL                             │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  RESULT: Patterns Ready for Auto-Routing                 │
│                                                           │
│  operation_patterns table:                               │
│  - test:pytest:backend → run_test_workflow (ACTIVE)      │
│  - build:typecheck:both → run_build_workflow (ACTIVE)    │
│  - test:vitest:frontend → run_test_workflow (ACTIVE)     │
└──────────────────────────────────────────────────────────┘
```

---

## Implementation

### Script 1: Tool Registration

**File:** `scripts/register_tools.py`

```python
#!/usr/bin/env python3
"""
Register ADW tools in the database.

Populates the adw_tools table with metadata for specialized tools.

Usage:
    python scripts/register_tools.py
"""

import sys
import sqlite3
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
db_path = project_root / "app" / "server" / "db" / "workflow_history.db"


def register_tool(
    cursor,
    tool_name: str,
    description: str,
    script_path: str,
    input_patterns: list,
    tool_schema: dict = None,
    output_format: dict = None,
    status: str = 'active'
):
    """
    Register a tool in the database.

    Args:
        cursor: Database cursor
        tool_name: Unique tool identifier
        description: Human-readable description
        script_path: Path to tool script (relative to project root)
        input_patterns: List of trigger keywords
        tool_schema: JSON schema for tool inputs
        output_format: JSON schema for tool outputs
        status: 'active' or 'experimental'
    """
    tool_schema = tool_schema or {
        "type": "object",
        "properties": {
            "issue_number": {"type": "integer"},
            "adw_id": {"type": "string"}
        },
        "required": ["issue_number", "adw_id"]
    }

    output_format = output_format or {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "data": {"type": "object"}
        },
        "required": ["success"]
    }

    cursor.execute("""
        INSERT OR REPLACE INTO adw_tools (
            tool_name,
            description,
            tool_schema,
            script_path,
            input_patterns,
            output_format,
            status,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        tool_name,
        description,
        json.dumps(tool_schema),
        script_path,
        json.dumps(input_patterns),
        json.dumps(output_format),
        status
    ))

    print(f"✓ Registered: {tool_name}")


def main():
    """Register all available tools."""
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return 1

    print("=" * 60)
    print("ADW TOOL REGISTRATION")
    print("=" * 60)
    print()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # ========================================================================
    # TEST WORKFLOW TOOL
    # ========================================================================
    register_tool(
        cursor,
        tool_name='run_test_workflow',
        description='Run project test suite (pytest/vitest) and return failures only. Saves ~95% tokens.',
        script_path='adws/adw_test_workflow.py',
        input_patterns=[
            'run tests',
            'test suite',
            'pytest',
            'vitest',
            'execute tests',
            'run all tests',
            'run backend tests',
            'run frontend tests',
            'test the code',
            'run unit tests',
            'run integration tests'
        ],
        status='active'
    )

    # ========================================================================
    # BUILD WORKFLOW TOOL
    # ========================================================================
    register_tool(
        cursor,
        tool_name='run_build_workflow',
        description='Run build/typecheck and return errors only. Saves ~97% tokens.',
        script_path='adws/adw_build_workflow.py',
        input_patterns=[
            'build',
            'typecheck',
            'type check',
            'compile',
            'tsc',
            'check types',
            'run build',
            'build project',
            'verify types',
            'typescript check'
        ],
        status='active'
    )

    # ========================================================================
    # TEST GENERATION TOOL (EXPERIMENTAL)
    # ========================================================================
    register_tool(
        cursor,
        tool_name='generate_tests',
        description='Auto-generate tests from templates. Saves ~90% tokens.',
        script_path='adws/adw_test_gen_workflow.py',
        input_patterns=[
            'generate tests',
            'create tests',
            'add tests',
            'write tests for',
            'generate unit tests',
            'create test suite'
        ],
        status='experimental'  # Not yet activated for auto-routing
    )

    conn.commit()

    # ========================================================================
    # SHOW REGISTERED TOOLS
    # ========================================================================
    print()
    print("=" * 60)
    print("REGISTERED TOOLS")
    print("=" * 60)
    print()

    cursor.execute("""
        SELECT tool_name, status, description, input_patterns
        FROM adw_tools
        ORDER BY status DESC, tool_name
    """)

    for row in cursor.fetchall():
        tool_name, status, description, input_patterns_json = row
        patterns = json.loads(input_patterns_json)

        status_icon = "✓" if status == 'active' else "⚠"
        print(f"{status_icon} {tool_name} ({status})")
        print(f"  {description}")
        print(f"  Triggers: {', '.join(patterns[:3])}{'...' if len(patterns) > 3 else ''}")
        print()

    conn.close()

    print("=" * 60)
    print("✅ Tool registration complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

### Script 2: Link Patterns to Tools

**File:** `scripts/link_patterns_to_tools.py`

```python
#!/usr/bin/env python3
"""
Link detected patterns to their corresponding tools.

Updates operation_patterns.tool_name based on pattern_signature.

Usage:
    python scripts/link_patterns_to_tools.py
"""

import sys
import sqlite3
from pathlib import Path

project_root = Path(__file__).parent.parent
db_path = project_root / "app" / "server" / "db" / "workflow_history.db"


def link_patterns():
    """Link patterns to tools based on pattern signatures."""
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # ========================================================================
    # PATTERN TO TOOL MAPPING
    # ========================================================================
    # Maps pattern signatures to their corresponding tool names
    pattern_tool_map = {
        # Test patterns
        'test:pytest:backend': 'run_test_workflow',
        'test:pytest:frontend': 'run_test_workflow',
        'test:pytest:all': 'run_test_workflow',
        'test:vitest:frontend': 'run_test_workflow',
        'test:vitest:backend': 'run_test_workflow',
        'test:generic:all': 'run_test_workflow',
        'test:unit:backend': 'run_test_workflow',
        'test:unit:frontend': 'run_test_workflow',
        'test:integration:all': 'run_test_workflow',

        # Build patterns
        'build:typecheck:backend': 'run_build_workflow',
        'build:typecheck:frontend': 'run_build_workflow',
        'build:typecheck:both': 'run_build_workflow',
        'build:compile:all': 'run_build_workflow',
        'build:build:all': 'run_build_workflow',
        'build:tsc:backend': 'run_build_workflow',
        'build:tsc:frontend': 'run_build_workflow',

        # Test generation patterns (experimental - won't activate yet)
        'generate:tests:backend': 'generate_tests',
        'generate:tests:frontend': 'generate_tests',
    }

    print("=" * 60)
    print("LINKING PATTERNS TO TOOLS")
    print("=" * 60)
    print()

    updated = 0
    skipped = 0
    errors = 0

    for pattern_sig, tool_name in pattern_tool_map.items():
        # Check if pattern exists
        cursor.execute("""
            SELECT id, occurrence_count, confidence_score
            FROM operation_patterns
            WHERE pattern_signature = ?
        """, (pattern_sig,))

        pattern_row = cursor.fetchone()

        if not pattern_row:
            print(f"  ⊘ Pattern not found: {pattern_sig}")
            skipped += 1
            continue

        # Check if tool exists
        cursor.execute("""
            SELECT tool_name, script_path, status
            FROM adw_tools
            WHERE tool_name = ?
        """, (tool_name,))

        tool_row = cursor.fetchone()

        if not tool_row:
            print(f"  ❌ Tool not found: {tool_name} (for {pattern_sig})")
            errors += 1
            continue

        # Link pattern to tool
        cursor.execute("""
            UPDATE operation_patterns
            SET
                tool_name = ?,
                tool_script_path = ?
            WHERE pattern_signature = ?
        """, (tool_name, tool_row['script_path'], pattern_sig))

        tool_status = tool_row['status']
        status_icon = "✓" if tool_status == 'active' else "⚠"

        print(f"  {status_icon} Linked: {pattern_sig} → {tool_name}")
        print(f"     Occurrences: {pattern_row['occurrence_count']}, "
              f"Confidence: {pattern_row['confidence_score']:.1f}%")

        updated += 1

    conn.commit()
    conn.close()

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  ✓ Linked: {updated}")
    print(f"  ⊘ Skipped (pattern not found): {skipped}")
    print(f"  ❌ Errors (tool not found): {errors}")
    print("=" * 60)

    if updated > 0:
        print()
        print("✅ Pattern linking complete!")
        print()
        print("Next step: Run scripts/activate_patterns.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

### Script 3: Activate Patterns

**File:** `scripts/activate_patterns.py`

```python
#!/usr/bin/env python3
"""
Activate patterns that meet criteria for automation.

Changes automation_status from 'detected' to 'active' for patterns with:
- confidence_score >= 70
- occurrence_count >= 3
- tool_name is set

Usage:
    python scripts/activate_patterns.py [--auto] [--min-confidence=70]
"""

import sys
import sqlite3
import argparse
from pathlib import Path

project_root = Path(__file__).parent.parent
db_path = project_root / "app" / "server" / "db" / "workflow_history.db"


def activate_patterns(min_confidence: float = 70.0, auto: bool = False):
    """
    Activate eligible patterns.

    Args:
        min_confidence: Minimum confidence score required
        auto: If True, activate without user confirmation
    """
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # ========================================================================
    # FIND ELIGIBLE PATTERNS
    # ========================================================================
    cursor.execute("""
        SELECT
            p.id,
            p.pattern_signature,
            p.confidence_score,
            p.occurrence_count,
            p.tool_name,
            t.status as tool_status,
            t.description as tool_description
        FROM operation_patterns p
        LEFT JOIN adw_tools t ON t.tool_name = p.tool_name
        WHERE p.automation_status = 'detected'
        AND p.confidence_score >= ?
        AND p.occurrence_count >= 3
        AND p.tool_name IS NOT NULL
        AND t.status = 'active'
        ORDER BY p.confidence_score DESC, p.occurrence_count DESC
    """, (min_confidence,))

    eligible = cursor.fetchall()

    if not eligible:
        print("=" * 60)
        print("NO PATTERNS ELIGIBLE FOR ACTIVATION")
        print("=" * 60)
        print()
        print("Patterns must meet these criteria:")
        print(f"  • confidence_score >= {min_confidence}%")
        print("  • occurrence_count >= 3")
        print("  • tool_name is set")
        print("  • tool status = 'active'")
        print()
        print("Run scripts/link_patterns_to_tools.py first if needed.")
        return 0

    # ========================================================================
    # SHOW ELIGIBLE PATTERNS
    # ========================================================================
    print("=" * 60)
    print(f"PATTERNS ELIGIBLE FOR ACTIVATION ({len(eligible)})")
    print("=" * 60)
    print()

    for pattern in eligible:
        print(f"  • {pattern['pattern_signature']}")
        print(f"    Confidence: {pattern['confidence_score']:.1f}%")
        print(f"    Occurrences: {pattern['occurrence_count']}")
        print(f"    Tool: {pattern['tool_name']}")
        print(f"    Description: {pattern['tool_description']}")
        print()

    # ========================================================================
    # CONFIRM ACTIVATION
    # ========================================================================
    if not auto:
        print("=" * 60)
        response = input("Activate these patterns? (yes/no): ").strip().lower()
        print()

        if response != 'yes':
            print("❌ Activation cancelled.")
            return 0

    # ========================================================================
    # ACTIVATE PATTERNS
    # ========================================================================
    print("Activating patterns...")
    print()

    for pattern in eligible:
        cursor.execute("""
            UPDATE operation_patterns
            SET automation_status = 'active'
            WHERE id = ?
        """, (pattern['id'],))

        print(f"  ✓ Activated: {pattern['pattern_signature']}")

    conn.commit()

    # ========================================================================
    # SHOW FINAL STATUS
    # ========================================================================
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM operation_patterns
        WHERE automation_status = 'active'
    """)

    active_count = cursor.fetchone()['total']

    conn.close()

    print()
    print("=" * 60)
    print("✅ ACTIVATION COMPLETE")
    print("=" * 60)
    print(f"  Total active patterns: {active_count}")
    print()
    print("These patterns will now trigger automatic tool routing.")
    print()
    print("Next step: Proceed to Phase 3C for ADW integration")

    return 0


def main():
    """Parse arguments and activate patterns."""
    parser = argparse.ArgumentParser(
        description="Activate patterns for automatic tool routing"
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Activate without user confirmation'
    )
    parser.add_argument(
        '--min-confidence',
        type=float,
        default=70.0,
        help='Minimum confidence score (default: 70.0)'
    )

    args = parser.parse_args()

    return activate_patterns(
        min_confidence=args.min_confidence,
        auto=args.auto
    )


if __name__ == "__main__":
    sys.exit(main())
```

---

## Execution Instructions

### Step 1: Register Tools

```bash
# Make scripts executable
chmod +x scripts/register_tools.py
chmod +x scripts/link_patterns_to_tools.py
chmod +x scripts/activate_patterns.py

# Register tools
python scripts/register_tools.py
```

Expected output:
```
============================================================
ADW TOOL REGISTRATION
============================================================

✓ Registered: run_test_workflow
✓ Registered: run_build_workflow
✓ Registered: generate_tests

============================================================
REGISTERED TOOLS
============================================================

✓ run_test_workflow (active)
  Run project test suite (pytest/vitest) and return failures only. Saves ~95% tokens.
  Triggers: run tests, test suite, pytest...

✓ run_build_workflow (active)
  Run build/typecheck and return errors only. Saves ~97% tokens.
  Triggers: build, typecheck, type check...

⚠ generate_tests (experimental)
  Auto-generate tests from templates. Saves ~90% tokens.
  Triggers: generate tests, create tests, add tests...

============================================================
✅ Tool registration complete!
============================================================
```

### Step 2: Link Patterns to Tools

```bash
python scripts/link_patterns_to_tools.py
```

Expected output:
```
============================================================
LINKING PATTERNS TO TOOLS
============================================================

  ✓ Linked: test:pytest:backend → run_test_workflow
     Occurrences: 10, Confidence: 85.0%
  ✓ Linked: build:typecheck:both → run_build_workflow
     Occurrences: 15, Confidence: 90.0%
  ⊘ Pattern not found: test:integration:all

============================================================
SUMMARY
============================================================
  ✓ Linked: 8
  ⊘ Skipped (pattern not found): 4
  ❌ Errors (tool not found): 0
============================================================

✅ Pattern linking complete!

Next step: Run scripts/activate_patterns.py
```

### Step 3: Activate Patterns

```bash
# Interactive mode (recommended for first time)
python scripts/activate_patterns.py

# Automatic mode (for scripts)
python scripts/activate_patterns.py --auto

# Custom confidence threshold
python scripts/activate_patterns.py --min-confidence=80
```

Expected output:
```
============================================================
PATTERNS ELIGIBLE FOR ACTIVATION (3)
============================================================

  • test:pytest:backend
    Confidence: 85.0%
    Occurrences: 10
    Tool: run_test_workflow
    Description: Run project test suite (pytest/vitest) and return failures only. Saves ~95% tokens.

  • build:typecheck:both
    Confidence: 90.0%
    Occurrences: 15
    Tool: run_build_workflow
    Description: Run build/typecheck and return errors only. Saves ~97% tokens.

============================================================
Activate these patterns? (yes/no): yes

Activating patterns...

  ✓ Activated: test:pytest:backend
  ✓ Activated: build:typecheck:both

============================================================
✅ ACTIVATION COMPLETE
============================================================
  Total active patterns: 3

These patterns will now trigger automatic tool routing.

Next step: Proceed to Phase 3C for ADW integration
```

---

## Validation

### Verify Tools Registered

```bash
sqlite3 app/server/db/workflow_history.db "
SELECT tool_name, status, script_path
FROM adw_tools
ORDER BY status DESC, tool_name;
"
```

Expected output:
```
run_build_workflow|active|adws/adw_build_workflow.py
run_test_workflow|active|adws/adw_test_workflow.py
generate_tests|experimental|adws/adw_test_gen_workflow.py
```

### Verify Patterns Linked

```bash
sqlite3 app/server/db/workflow_history.db "
SELECT
    pattern_signature,
    tool_name,
    automation_status,
    confidence_score
FROM operation_patterns
WHERE tool_name IS NOT NULL
ORDER BY confidence_score DESC;
"
```

Expected output:
```
build:typecheck:both|run_build_workflow|active|90.0
test:pytest:backend|run_test_workflow|active|85.0
test:vitest:frontend|run_test_workflow|active|78.0
```

### Verify Active Patterns Count

```bash
sqlite3 app/server/db/workflow_history.db "
SELECT
    COUNT(*) as total,
    automation_status
FROM operation_patterns
GROUP BY automation_status;
"
```

Expected output:
```
3|active
7|detected
```

---

## Success Criteria

- [ ] ✅ `register_tools.py` script created and working
- [ ] ✅ `link_patterns_to_tools.py` script created and working
- [ ] ✅ `activate_patterns.py` script created and working
- [ ] ✅ At least 2 tools registered in adw_tools table
- [ ] ✅ At least 2 patterns linked to tools
- [ ] ✅ At least 2 patterns activated (status = 'active')
- [ ] ✅ All scripts executable and properly formatted
- [ ] ✅ Database queries return expected results

---

## Troubleshooting

### No Patterns Found to Link

**Problem:** `link_patterns_to_tools.py` shows all patterns skipped

**Solution:**
```bash
# Check if Phase 1 pattern detection ran
sqlite3 app/server/db/workflow_history.db "
SELECT COUNT(*) FROM operation_patterns;
"

# If 0, run Phase 1 first
python scripts/backfill_pattern_learning.py
```

### No Tools Registered

**Problem:** `register_tools.py` fails silently

**Solution:**
```bash
# Check if adw_tools table exists
sqlite3 app/server/db/workflow_history.db "
.schema adw_tools
"

# If table missing, apply migration 004
cd app/server
uv run alembic upgrade head
```

### Pattern Activation Fails

**Problem:** `activate_patterns.py` shows no eligible patterns

**Possible Causes:**
1. Patterns not linked to tools → Run `link_patterns_to_tools.py`
2. Confidence scores too low → Lower threshold with `--min-confidence=60`
3. Occurrence count too low → Need more historical data
4. Tool status is 'experimental' → Change to 'active' in register_tools.py

---

## Next Steps

After completing Phase 3B:

1. **Verify all scripts ran successfully**
2. **Confirm database state** - Tools registered, patterns linked and activated
3. **Review active patterns** - Ensure they make sense for your workflow
4. **Proceed to Phase 3C** - ADW Integration & Routing

---

## Deliverables Checklist

- [ ] `scripts/register_tools.py` created (~150 lines)
- [ ] `scripts/link_patterns_to_tools.py` created (~100 lines)
- [ ] `scripts/activate_patterns.py` created (~150 lines)
- [ ] All scripts executable (chmod +x)
- [ ] Tools registered in database
- [ ] Patterns linked to tools
- [ ] Patterns activated
- [ ] Database validated

**Total Lines of Code:** ~400 lines

---

## Dependencies for Next Phase

Phase 3C will need:
- ✅ Pattern matcher working (Phase 3A)
- ✅ Tools registered in database (Phase 3B - this phase)
- ✅ Patterns activated (Phase 3B - this phase)
- ❌ Tool execution logic (created in 3C)
- ❌ ADW integration (created in 3C)

Once Phase 3B is complete, proceed to Phase 3C for full routing integration.
