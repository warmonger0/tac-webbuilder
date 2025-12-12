# PostgreSQL Pattern Predictions Migration

**ADW ID:** 77c90e61 (Issue #170)
**Date:** 2025-12-11
**Specification:** trees/77c90e61/specs/issue-170-adw-77c90e61-sdlc_planner-new-request-1-description-verify-migration-010-app.md

## Overview

This feature adds PostgreSQL support for the Pattern Predictions tracking system by creating a PostgreSQL-compatible version of Migration 010. The migration establishes two critical tables (`operation_patterns` and `pattern_predictions`) that enable closed-loop pattern accuracy tracking and validation for the ADW automation system.

## What Was Built

- **PostgreSQL Migration 010** - Database schema for pattern predictions tracking
- **Migration Application Script** - Helper tool to apply the migration to PostgreSQL
- **Verification Script** - Comprehensive testing tool to validate migration success

## Technical Implementation

### Files Modified

- `app/server/db/migrations/010_add_pattern_predictions_postgres.sql`: PostgreSQL version of migration 010 with proper syntax conversion from SQLite
- `app/server/apply_migration_010.py`: Python helper script to apply the migration using the database adapter
- `app/server/verify_migration_010.py`: Verification script that checks table existence, schema, indexes, and foreign keys

### Key Changes

**Migration 010 PostgreSQL Conversion:**
- Converted `INTEGER PRIMARY KEY AUTOINCREMENT` to `SERIAL PRIMARY KEY`
- Converted `datetime('now')` to `NOW()`
- Converted TEXT datetime columns to `TIMESTAMP` type
- Maintained all indexes and foreign key constraints from original SQLite migration

**Tables Created:**

1. **operation_patterns** - Stores detected automation patterns
   - Tracks pattern metadata (signature, type, status)
   - Records detection and prediction counts
   - Monitors prediction accuracy over time

2. **pattern_predictions** - Links predictions to patterns with validation
   - Associates predictions with specific requests
   - Stores confidence scores and reasoning
   - Tracks validation results (correct/incorrect)
   - Foreign key relationship to operation_patterns

**Indexes Created:**
- `idx_operation_patterns_signature` - Fast lookup by pattern signature
- `idx_operation_patterns_type` - Filter by pattern type
- `idx_pattern_predictions_request` - Query predictions by request_id
- `idx_pattern_predictions_pattern` - Join with operation_patterns
- `idx_pattern_predictions_validated` - Filter by validation status

## How to Use

### Applying the Migration

1. Ensure PostgreSQL is running and accessible:
   ```bash
   docker ps | grep postgres
   ```

2. Set environment variables:
   ```bash
   export DB_TYPE=postgresql
   export POSTGRES_HOST=localhost
   export POSTGRES_PORT=5432
   export POSTGRES_DB=tac_webbuilder
   export POSTGRES_USER=tac_user
   export POSTGRES_PASSWORD=changeme
   ```

3. Apply the migration:
   ```bash
   cd app/server
   .venv/bin/python3 apply_migration_010.py
   ```

### Verifying the Migration

Run the verification script to confirm successful application:

```bash
cd app/server
.venv/bin/python3 verify_migration_010.py
```

Expected output:
```
✓ Table 'operation_patterns' exists
  Columns: id, pattern_signature, pattern_type, ...
  ✓ All expected columns present
  Indexes: operation_patterns_pkey, idx_operation_patterns_signature, ...

✓ Table 'pattern_predictions' exists
  Columns: id, request_id, pattern_id, ...
  ✓ All expected columns present
  Indexes: pattern_predictions_pkey, idx_pattern_predictions_request, ...

✓ All migration 010 tables verified successfully!
```

## Configuration

### Environment Variables

Required PostgreSQL connection settings (configured in `app/server/.env`):

- `DB_TYPE=postgresql` - Must be set to use PostgreSQL adapter
- `POSTGRES_HOST` - Database host (default: localhost)
- `POSTGRES_PORT` - Database port (default: 5432)
- `POSTGRES_DB` - Database name (default: tac_webbuilder)
- `POSTGRES_USER` - Database user (default: tac_user)
- `POSTGRES_PASSWORD` - Database password (required, no default)

### Database Adapter

The migration uses the PostgreSQL adapter from `app/server/database/factory.py` which automatically selects PostgreSQL when `DB_TYPE=postgresql` is set or when all PostgreSQL environment variables are present.

## Testing

### Backend API Health Check

Verify the migration through the backend preflight checks:

```bash
curl -s http://localhost:8002/api/v1/preflight-checks | jq '.checks_run[] | select(.check == "observability_database")'
```

Expected response:
```json
{
  "check": "observability_database",
  "status": "pass",
  "duration_ms": 6,
  "details": "PostgreSQL connected, 3 tables"
}
```

### Direct Database Verification

Check tables directly in PostgreSQL:

```bash
docker exec tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder -c "
  SELECT tablename FROM pg_catalog.pg_tables
  WHERE schemaname = 'public'
  AND tablename IN ('pattern_predictions', 'operation_patterns')
  ORDER BY tablename;"
```

### Test Pattern Predictions Access

Run the pattern predictions test script:

```bash
cd app/server
.venv/bin/python3 test_pattern_predictions.py
```

This verifies:
- Table accessibility through database adapter
- Foreign key relationships
- Query operations

## Notes

### Schema Differences from SQLite

The PostgreSQL migration differs from the SQLite version in these key areas:

| SQLite | PostgreSQL |
|--------|------------|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL PRIMARY KEY` |
| `datetime('now')` | `NOW()` |
| `TEXT` (for timestamps) | `TIMESTAMP` |
| `IF NOT EXISTS` (for operations_patterns) | `IF NOT EXISTS` (kept for safety) |

### Existing operation_patterns Table

The `operation_patterns` table may already exist from the observability migration with an enhanced schema. The migration uses `CREATE TABLE IF NOT EXISTS` to safely handle this case. The existing table has additional columns beyond migration 010's requirements:
- `first_detected`, `last_seen`, `occurrence_count`
- `typical_input_pattern`, `typical_operations`, `typical_files_accessed`
- Cost and token tracking columns
- Review and audit columns

This is expected and does not affect the pattern_predictions functionality.

### Prerequisites for Pattern Validation Loop

With this migration applied, the system is ready for:
- Feature #63: Pattern Validation Loop implementation
- Closed-loop pattern accuracy tracking
- Automated pattern detection and validation
- ROI metrics for automation patterns

### Future Work

The `workflow_history.db` SQLite database (60MB) is still used by `core/workflow_history_utils` module and needs a separate PostgreSQL migration in a future session.
