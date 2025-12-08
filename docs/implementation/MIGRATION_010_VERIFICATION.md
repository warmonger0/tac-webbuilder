# Migration 010 Verification & Application
## Verify Pattern Predictions Table in PostgreSQL

**Related Plan Item:** ID #62
**Priority:** High
**Estimated Effort:** 0.5 hours (30 minutes)
**Status:** Planned

---

## Executive Summary

Verify that Migration 010 (`pattern_predictions` table) has been applied to the PostgreSQL database. This migration is a prerequisite for the Pattern Validation Loop (Feature #63). The migration file exists at `app/server/db/migrations/010_add_pattern_predictions.sql` but may not have been applied during PostgreSQL setup.

**Why This Matters:**
- Required for Pattern Validation Loop implementation
- Enables closed-loop pattern accuracy tracking
- Missing table will cause validation system to fail

**Quick Check:**
```sql
-- In PostgreSQL, check if table exists
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name = 'pattern_predictions';
```

---

## Migration File Details

**File:** `app/server/db/migrations/010_add_pattern_predictions.sql`

**What It Creates:**

1. **operation_patterns table** (if not exists)
   - Stores pattern metadata
   - Tracks detection and prediction counts
   - Stores prediction accuracy metrics

2. **pattern_predictions table**
   - Links predictions to patterns
   - Stores confidence scores
   - **Critical:** `was_correct` field for validation results
   - **Critical:** `validated_at` timestamp

**Schema:**
```sql
CREATE TABLE pattern_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    pattern_id INTEGER NOT NULL,

    -- Prediction details
    confidence_score REAL NOT NULL,
    reasoning TEXT,
    predicted_at TEXT DEFAULT (datetime('now')),

    -- Validation (filled after workflow completes)
    was_correct INTEGER,  -- NULL = not validated, 1 = correct, 0 = incorrect
    validated_at TEXT,

    FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id)
);
```

**Indexes Created:**
```sql
CREATE INDEX idx_pattern_predictions_request ON pattern_predictions(request_id);
CREATE INDEX idx_pattern_predictions_pattern ON pattern_predictions(pattern_id);
CREATE INDEX idx_pattern_predictions_validated ON pattern_predictions(was_correct);
```

---

## Verification Steps

### Step 1: Check PostgreSQL Connection (2 min)

Verify we can connect to the PostgreSQL database:

```bash
# Test connection
cd app/server
POSTGRES_HOST=localhost \
POSTGRES_PORT=5432 \
POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user \
POSTGRES_PASSWORD=changeme \
DB_TYPE=postgresql \
.venv/bin/python3 << 'EOF'
from database import get_database_adapter

adapter = get_database_adapter()
with adapter.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"✅ Connected to PostgreSQL: {version}")
EOF
```

**Expected Output:**
```
✅ Connected to PostgreSQL: PostgreSQL 14.x on ...
```

**If Connection Fails:**
- Verify PostgreSQL is running: `docker ps | grep postgres` or `pg_isready`
- Check `.env` file has correct credentials
- Verify database exists: `psql -l | grep tac_webbuilder`

---

### Step 2: Check if Tables Exist (5 min)

**Query:** Check for both tables

```bash
cd app/server
POSTGRES_HOST=localhost \
POSTGRES_PORT=5432 \
POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user \
POSTGRES_PASSWORD=changeme \
DB_TYPE=postgresql \
.venv/bin/python3 << 'EOF'
from database import get_database_adapter

adapter = get_database_adapter()
with adapter.get_connection() as conn:
    cursor = conn.cursor()

    # Check for operation_patterns
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'operation_patterns'
    """)
    op_patterns_exists = cursor.fetchone() is not None

    # Check for pattern_predictions
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'pattern_predictions'
    """)
    predictions_exists = cursor.fetchone() is not None

    print(f"operation_patterns: {'✅ EXISTS' if op_patterns_exists else '❌ MISSING'}")
    print(f"pattern_predictions: {'✅ EXISTS' if predictions_exists else '❌ MISSING'}")

    if not predictions_exists:
        print("\n⚠️  Migration 010 NOT applied - need to apply it")
    else:
        print("\n✅ Migration 010 already applied")
EOF
```

**Possible Outcomes:**

1. **Both tables exist** → Migration already applied, go to Step 3 (verify schema)
2. **pattern_predictions missing** → Need to apply migration (go to Step 4)
3. **Both tables missing** → Need to apply migration (go to Step 4)

---

### Step 3: Verify Schema (If Tables Exist) (5 min)

If tables exist, verify they have the correct schema:

```bash
cd app/server
POSTGRES_HOST=localhost \
POSTGRES_PORT=5432 \
POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user \
POSTGRES_PASSWORD=changeme \
DB_TYPE=postgresql \
.venv/bin/python3 << 'EOF'
from database import get_database_adapter

adapter = get_database_adapter()
with adapter.get_connection() as conn:
    cursor = conn.cursor()

    # Check pattern_predictions schema
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'pattern_predictions'
        ORDER BY ordinal_position
    """)

    columns = cursor.fetchall()
    required_columns = {
        'id', 'request_id', 'pattern_id', 'confidence_score',
        'reasoning', 'predicted_at', 'was_correct', 'validated_at'
    }

    actual_columns = {row[0] for row in columns}

    print("pattern_predictions columns:")
    for col in columns:
        print(f"  {col[0]:20} {col[1]:15} {'NULL' if col[2] == 'YES' else 'NOT NULL'}")

    missing = required_columns - actual_columns
    extra = actual_columns - required_columns

    if missing:
        print(f"\n❌ Missing columns: {missing}")
    if extra:
        print(f"\n⚠️  Extra columns: {extra}")
    if not missing and not extra:
        print(f"\n✅ Schema correct - all required columns present")

    # Check indexes
    cursor.execute("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'pattern_predictions'
    """)

    indexes = cursor.fetchall()
    print(f"\nIndexes on pattern_predictions:")
    for idx in indexes:
        print(f"  {idx[0]}")

    expected_indexes = {
        'idx_pattern_predictions_request',
        'idx_pattern_predictions_pattern',
        'idx_pattern_predictions_validated'
    }

    actual_indexes = {idx[0] for idx in indexes if idx[0] in expected_indexes}
    missing_indexes = expected_indexes - actual_indexes

    if missing_indexes:
        print(f"\n⚠️  Missing indexes: {missing_indexes}")
    else:
        print(f"\n✅ All expected indexes present")
EOF
```

**Expected Output:**
```
pattern_predictions columns:
  id                   integer         NOT NULL
  request_id           text            NOT NULL
  pattern_id           integer         NOT NULL
  confidence_score     real            NOT NULL
  reasoning            text            NULL
  predicted_at         timestamp       NULL
  was_correct          integer         NULL
  validated_at         timestamp       NULL

✅ Schema correct - all required columns present

Indexes on pattern_predictions:
  pattern_predictions_pkey
  idx_pattern_predictions_request
  idx_pattern_predictions_pattern
  idx_pattern_predictions_validated

✅ All expected indexes present
```

**If Schema Mismatch:**
- May need to drop and recreate table
- Check if migration file was modified
- Review migration history

---

### Step 4: Apply Migration (If Needed) (10 min)

If migration not applied, apply it now:

**Option A: Manual Application (Recommended for visibility)**

```bash
cd app/server

# Read the migration file
cat db/migrations/010_add_pattern_predictions.sql

# Apply via Python (handles SQLite vs PostgreSQL differences)
POSTGRES_HOST=localhost \
POSTGRES_PORT=5432 \
POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user \
POSTGRES_PASSWORD=changeme \
DB_TYPE=postgresql \
.venv/bin/python3 << 'EOF'
from database import get_database_adapter
from pathlib import Path

# Read migration file
migration_file = Path('db/migrations/010_add_pattern_predictions.sql')
sql = migration_file.read_text()

# Note: Migration file uses SQLite syntax (AUTOINCREMENT, datetime('now'))
# Need to convert to PostgreSQL syntax

# PostgreSQL version of migration
pg_sql = """
-- Migration 010: Add pattern predictions tracking (PostgreSQL version)

-- Create operation_patterns table if it doesn't exist
CREATE TABLE IF NOT EXISTS operation_patterns (
    id SERIAL PRIMARY KEY,
    pattern_signature TEXT NOT NULL UNIQUE,
    pattern_type TEXT NOT NULL,
    automation_status TEXT DEFAULT 'detected',
    detection_count INTEGER DEFAULT 0,
    last_detected TIMESTAMP,
    prediction_count INTEGER DEFAULT 0,
    prediction_accuracy REAL DEFAULT 0.0,
    last_predicted TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_operation_patterns_signature ON operation_patterns(pattern_signature);
CREATE INDEX IF NOT EXISTS idx_operation_patterns_type ON operation_patterns(pattern_type);

-- Drop and recreate pattern_predictions table with proper foreign key
DROP TABLE IF EXISTS pattern_predictions;

CREATE TABLE pattern_predictions (
    id SERIAL PRIMARY KEY,
    request_id TEXT NOT NULL,
    pattern_id INTEGER NOT NULL,

    -- Prediction details
    confidence_score REAL NOT NULL,
    reasoning TEXT,
    predicted_at TIMESTAMP DEFAULT NOW(),

    -- Validation (filled after workflow completes)
    was_correct INTEGER,  -- NULL = not validated, 1 = correct, 0 = incorrect
    validated_at TIMESTAMP,

    FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id)
);

CREATE INDEX IF NOT EXISTS idx_pattern_predictions_request ON pattern_predictions(request_id);
CREATE INDEX IF NOT EXISTS idx_pattern_predictions_pattern ON pattern_predictions(pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_predictions_validated ON pattern_predictions(was_correct);
"""

adapter = get_database_adapter()
with adapter.get_connection() as conn:
    cursor = conn.cursor()

    # Execute migration
    try:
        cursor.execute(pg_sql)
        conn.commit()
        print("✅ Migration 010 applied successfully")

        # Verify
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = 'pattern_predictions'
        """)

        if cursor.fetchone():
            print("✅ Verified: pattern_predictions table exists")
        else:
            print("❌ Error: Table not created")

    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        conn.rollback()
EOF
```

**Option B: Use Migration Script (If exists)**

```bash
# Check if migration runner exists
ls scripts/run_migrations.py

# If exists, run it
POSTGRES_HOST=localhost \
POSTGRES_PORT=5432 \
POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user \
POSTGRES_PASSWORD=changeme \
DB_TYPE=postgresql \
python scripts/run_migrations.py --migration 010
```

---

### Step 5: Verify Migration Applied (5 min)

After applying migration, verify it worked:

```bash
cd app/server
POSTGRES_HOST=localhost \
POSTGRES_PORT=5432 \
POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user \
POSTGRES_PASSWORD=changeme \
DB_TYPE=postgresql \
.venv/bin/python3 << 'EOF'
from database import get_database_adapter

adapter = get_database_adapter()
with adapter.get_connection() as conn:
    cursor = conn.cursor()

    # Check tables exist
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name IN ('operation_patterns', 'pattern_predictions')
        ORDER BY table_name
    """)

    tables = cursor.fetchall()
    print("Tables created:")
    for table in tables:
        print(f"  ✅ {table[0]}")

    # Check can insert and query
    cursor.execute("""
        INSERT INTO operation_patterns (
            pattern_signature,
            pattern_type,
            automation_status
        ) VALUES (
            'test:verification:migration010',
            'test',
            'detected'
        )
        ON CONFLICT (pattern_signature) DO NOTHING
        RETURNING id
    """)

    pattern_id = cursor.fetchone()
    if pattern_id:
        pattern_id = pattern_id[0]
        print(f"\n✅ Can insert into operation_patterns (ID: {pattern_id})")

        # Test pattern_predictions insert
        cursor.execute("""
            INSERT INTO pattern_predictions (
                request_id,
                pattern_id,
                confidence_score,
                reasoning
            ) VALUES (
                'test-request-verification',
                %s,
                0.95,
                'Migration verification test'
            )
            RETURNING id
        """, (pattern_id,))

        pred_id = cursor.fetchone()[0]
        print(f"✅ Can insert into pattern_predictions (ID: {pred_id})")

        # Clean up test data
        cursor.execute("DELETE FROM pattern_predictions WHERE id = %s", (pred_id,))
        cursor.execute("DELETE FROM operation_patterns WHERE id = %s", (pattern_id,))
        conn.commit()
        print("\n✅ Migration 010 verified - ready for Pattern Validation Loop")
    else:
        print("\n⚠️  Test pattern already exists (may be from previous verification)")
EOF
```

**Expected Output:**
```
Tables created:
  ✅ operation_patterns
  ✅ pattern_predictions

✅ Can insert into operation_patterns (ID: 123)
✅ Can insert into pattern_predictions (ID: 456)

✅ Migration 010 verified - ready for Pattern Validation Loop
```

---

### Step 6: Document Migration Status (3 min)

Create a verification record:

```bash
cat > docs/migrations/MIGRATION_010_VERIFICATION.md << 'EOF'
# Migration 010 Verification Record

**Date:** $(date +%Y-%m-%d)
**Verified By:** Automated verification script
**Database:** PostgreSQL (tac_webbuilder)

## Verification Results

- ✅ `operation_patterns` table exists
- ✅ `pattern_predictions` table exists
- ✅ All required columns present
- ✅ All indexes created
- ✅ Foreign key constraint working
- ✅ Can insert and query data

## Schema

### operation_patterns
```sql
id SERIAL PRIMARY KEY
pattern_signature TEXT NOT NULL UNIQUE
pattern_type TEXT NOT NULL
automation_status TEXT DEFAULT 'detected'
detection_count INTEGER DEFAULT 0
last_detected TIMESTAMP
prediction_count INTEGER DEFAULT 0
prediction_accuracy REAL DEFAULT 0.0
last_predicted TIMESTAMP
created_at TIMESTAMP DEFAULT NOW()
```

### pattern_predictions
```sql
id SERIAL PRIMARY KEY
request_id TEXT NOT NULL
pattern_id INTEGER NOT NULL
confidence_score REAL NOT NULL
reasoning TEXT
predicted_at TIMESTAMP DEFAULT NOW()
was_correct INTEGER  -- NULL, 1, 0
validated_at TIMESTAMP
FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id)
```

## Next Steps

Migration verified and ready for:
- Pattern Validation Loop implementation (Feature #63, Session 18)
- Closed-loop pattern accuracy tracking
- Prediction performance analytics

## Migration File

Source: `app/server/db/migrations/010_add_pattern_predictions.sql`
Applied: $(date +%Y-%m-%d)
EOF

echo "✅ Verification document created"
```

---

## Troubleshooting

### Issue: "Table already exists" Error

**Cause:** Migration partially applied or table created manually

**Solution:**
1. Check table schema matches expected schema
2. If schema wrong, drop and recreate:
   ```sql
   DROP TABLE IF EXISTS pattern_predictions CASCADE;
   DROP TABLE IF EXISTS operation_patterns CASCADE;
   -- Then re-run migration
   ```

### Issue: "Column not found" Error in Queries

**Cause:** Schema mismatch (old version of table)

**Solution:**
1. Check which columns exist:
   ```sql
   SELECT column_name FROM information_schema.columns
   WHERE table_name = 'pattern_predictions';
   ```
2. Compare with expected schema
3. If mismatch, drop and recreate table

### Issue: Foreign Key Constraint Violation

**Cause:** Trying to insert prediction for non-existent pattern

**Solution:**
1. Ensure pattern exists in `operation_patterns` first
2. Check `pattern_id` value is valid
3. Use `ON CONFLICT` in pattern inserts

### Issue: Migration Works in SQLite but Fails in PostgreSQL

**Cause:** Syntax differences (AUTOINCREMENT vs SERIAL, datetime() vs NOW())

**Solution:**
- Use the PostgreSQL version of the migration (see Step 4)
- Don't run the SQLite migration file directly on PostgreSQL

---

## Success Criteria

**Verification Complete When:**

- [ ] PostgreSQL connection confirmed
- [ ] `operation_patterns` table exists
- [ ] `pattern_predictions` table exists
- [ ] All required columns present
- [ ] All indexes created
- [ ] Foreign key constraint working
- [ ] Test insert/query successful
- [ ] Verification document created

**Ready for Next Step:**
- ✅ Can proceed with Pattern Validation Loop implementation (Feature #63)

---

## Time Breakdown

- Step 1: PostgreSQL connection check - 2 min
- Step 2: Check table existence - 5 min
- Step 3: Verify schema (if exists) - 5 min
- Step 4: Apply migration (if needed) - 10 min
- Step 5: Verify migration applied - 5 min
- Step 6: Document verification - 3 min

**Total:** ~30 minutes (0.5 hours)

---

## Related Documentation

- Migration File: `app/server/db/migrations/010_add_pattern_predictions.sql`
- Pattern Validation Plan: `docs/implementation/PATTERN_VALIDATION_LOOP_IMPLEMENTATION.md`
- Pattern Recognition Plan: `docs/requests/complete_pattern_recognition_system.md`
- Planned Feature: #62 (this task), #63 (validation loop)

---

**Status:** Ready to execute
**Next Action:** Run Step 1 to begin verification
