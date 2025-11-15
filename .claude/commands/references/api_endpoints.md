# API Endpoints Reference

## Base URL
- **Development:** `http://localhost:8000` (or `BACKEND_PORT`)
- **Production:** Configure via environment

## Health & Status

### GET /api/health
Health check with database status.

**Response:**
```json
{
  "status": "healthy",
  "uptime": "2h 15m 30s",
  "database": "connected",
  "tables": 5
}
```

## File Management

### POST /api/upload
Upload CSV, JSON, or JSONL file to create SQLite table.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (CSV/JSON/JSONL)

**Response:**
```json
{
  "message": "File uploaded successfully",
  "table_name": "users",
  "row_count": 150,
  "columns": ["id", "name", "email", "created_at"]
}
```

**Security:**
- Table name sanitized (alphanumeric + underscore only)
- SQL keywords blocked
- Identifier validation applied

### DELETE /api/table/{table_name}
Delete a table from the database.

**Response:**
```json
{
  "message": "Table 'users' deleted successfully"
}
```

## Query Processing

### POST /api/query
Convert natural language to SQL and execute.

**Request:**
```json
{
  "query": "Show me all users who signed up last week",
  "provider": "anthropic"  // or "openai"
}
```

**Response:**
```json
{
  "sql": "SELECT * FROM users WHERE created_at >= date('now', '-7 days')",
  "results": [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "created_at": "2025-01-06"},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "created_at": "2025-01-07"}
  ],
  "row_count": 2,
  "execution_time": 0.015
}
```

**Error Response:**
```json
{
  "error": "SQL injection attempt detected",
  "details": "Dangerous operation blocked: DROP"
}
```

## Schema & Insights

### GET /api/schema
Get database schema and table information.

**Response:**
```json
{
  "tables": [
    {
      "name": "users",
      "row_count": 150,
      "columns": [
        {"name": "id", "type": "INTEGER"},
        {"name": "name", "type": "TEXT"},
        {"name": "email", "type": "TEXT"},
        {"name": "created_at", "type": "TEXT"}
      ]
    }
  ]
}
```

### POST /api/insights
Generate statistical insights for table columns.

**Request:**
```json
{
  "table_name": "users"
}
```

**Response:**
```json
{
  "table": "users",
  "insights": [
    {
      "column": "email",
      "unique_count": 150,
      "null_count": 0,
      "sample_values": ["alice@example.com", "bob@example.com"]
    },
    {
      "column": "created_at",
      "unique_count": 45,
      "null_count": 0,
      "min": "2024-01-01",
      "max": "2025-01-13"
    }
  ]
}
```

### GET /api/generate-random-query
Generate a random SQL query based on database schema.

**Response:**
```json
{
  "query": "Show me the top 5 users by creation date",
  "sql": "SELECT * FROM users ORDER BY created_at DESC LIMIT 5"
}
```

## Export

### POST /api/export/table
Export table as CSV.

**Request:**
```json
{
  "table_name": "users"
}
```

**Response:**
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename="users.csv"`
- Body: CSV file

### POST /api/export/query
Export query results as CSV.

**Request:**
```json
{
  "sql": "SELECT * FROM users WHERE created_at >= date('now', '-7 days')"
}
```

**Response:**
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename="query_results.csv"`
- Body: CSV file

## Web UI Endpoints (Frontend Integration)

These endpoints are expected by the React frontend but may not be fully implemented:

### POST /api/request
Submit natural language request for processing.

**Request:**
```json
{
  "nl_input": "Add a dark mode toggle to the settings page",
  "project_path": "/path/to/project",
  "auto_post": true
}
```

**Response:**
```json
{
  "request_id": "req_abc123",
  "status": "processing"
}
```

### GET /api/preview/{request_id}
Get preview of generated GitHub issue.

**Response:**
```json
{
  "title": "Add dark mode toggle",
  "body": "## Description\n...",
  "labels": ["enhancement", "ui"],
  "classification": "/feature",
  "workflow": "adw_sdlc_iso",
  "model_set": "base"
}
```

### POST /api/confirm/{request_id}
Confirm and post issue to GitHub.

**Response:**
```json
{
  "issue_number": 123,
  "issue_url": "https://github.com/owner/repo/issues/123",
  "workflow_triggered": true
}
```

### GET /api/workflows
List active ADW workflows.

**Response:**
```json
{
  "workflows": [
    {
      "adw_id": "abc12345",
      "issue_number": 123,
      "status": "building",
      "phase": "implementation",
      "progress": 60
    }
  ]
}
```

### GET /api/history
Get request history.

**Response:**
```json
{
  "requests": [
    {
      "request_id": "req_abc123",
      "timestamp": "2025-01-13T10:30:00Z",
      "nl_input": "Add dark mode toggle",
      "issue_number": 123,
      "status": "completed"
    }
  ]
}
```

### GET /api/routes
Get API route information (via routes_analyzer.py).

**Response:**
```json
{
  "routes": [
    {
      "path": "/api/health",
      "method": "GET",
      "module": "server",
      "description": "Health check"
    }
  ]
}
```

## Workflow History Management

### GET /api/workflow-history
Get workflow history with filtering, sorting, and pagination.

**Query Parameters:**
- `limit` (optional): Maximum number of records (default: 20)
- `offset` (optional): Number of records to skip (default: 0)
- `status` (optional): Filter by status (pending, running, completed, failed)
- `model` (optional): Filter by model
- `template` (optional): Filter by workflow template
- `start_date` (optional): Filter by start date (ISO format)
- `end_date` (optional): Filter by end date (ISO format)
- `search` (optional): Search in ADW ID, nl_input, or github_url
- `sort_by` (optional): Field to sort by (default: created_at)
- `sort_order` (optional): Sort order ASC or DESC (default: DESC)

**Response:**
```json
{
  "workflows": [
    {
      "id": 1,
      "adw_id": "abc12345",
      "issue_number": 123,
      "status": "completed",
      "actual_cost_total": 0.45,
      "total_tokens": 125000,
      "cache_efficiency_percent": 35.5,
      "duration_seconds": 180,
      "created_at": "2025-01-13T10:30:00Z"
    }
  ],
  "total_count": 50,
  "analytics": {
    "total_workflows": 50,
    "completed_workflows": 45,
    "failed_workflows": 3,
    "avg_duration_seconds": 165.5,
    "success_rate_percent": 90.0,
    "avg_cost": 0.42,
    "total_cost": 21.00
  }
}
```

### POST /api/workflow-history/resync
Manually resync workflow history cost data from source files.

**Query Parameters:**
- `adw_id` (optional): ADW ID to resync single workflow
- `force` (optional): Clear existing cost data before resync (default: false)

**Use Cases:**
- Repair corrupted historical cost data
- Force recalculation after cost file updates
- Verify cost data integrity
- Bulk update all completed workflows

**Examples:**

**Single Workflow Resync:**
```bash
curl -X POST "http://localhost:8000/api/workflow-history/resync?adw_id=abc12345"
```

**Bulk Resync All Completed Workflows:**
```bash
curl -X POST "http://localhost:8000/api/workflow-history/resync"
```

**Force Resync (Clear and Recalculate):**
```bash
curl -X POST "http://localhost:8000/api/workflow-history/resync?adw_id=abc12345&force=true"
```

**Response (Success):**
```json
{
  "resynced_count": 1,
  "workflows": [
    {
      "adw_id": "abc12345",
      "cost_updated": true
    }
  ],
  "errors": [],
  "message": "Successfully resynced workflow abc12345"
}
```

**Response (Bulk Success):**
```json
{
  "resynced_count": 15,
  "workflows": [
    {"adw_id": "w1", "status": "completed", "cost_updated": true},
    {"adw_id": "w2", "status": "completed", "cost_updated": true},
    {"adw_id": "w3", "status": "failed", "cost_updated": true}
  ],
  "errors": [],
  "message": "Bulk resync completed: 15 workflows updated, 0 errors"
}
```

**Response (Error):**
```json
{
  "resynced_count": 0,
  "workflows": [],
  "errors": ["Workflow not found: abc12345"],
  "message": "Failed to resync workflow abc12345"
}
```

**Response (Partial Success):**
```json
{
  "resynced_count": 12,
  "workflows": [
    {"adw_id": "w1", "status": "completed", "cost_updated": true},
    {"adw_id": "w2", "status": "completed", "cost_updated": false}
  ],
  "errors": ["w3: Cost files not found", "w4: Invalid cost data"],
  "message": "Bulk resync completed: 12 workflows updated, 2 errors"
}
```

**Notes:**
- This is an administrative endpoint - use with caution in production
- Cost data is read from authoritative source files: `agents/<adw_id>/costs/*.jsonl`
- Force mode clears existing cost data before recalculation
- Bulk resync only processes completed and failed workflows (not running workflows)
- The endpoint is idempotent - running multiple times produces consistent results
- Requires completed workflows with valid cost files to exist

## Error Codes

### 400 Bad Request
- Invalid input data
- SQL injection attempt
- Missing required fields

### 404 Not Found
- Table not found
- Request ID not found

### 500 Internal Server Error
- Database connection error
- LLM API error
- Unexpected server error

## Security

### SQL Injection Protection
All endpoints using SQL implement:
1. Identifier validation (table/column names)
2. Parameterized queries
3. Dangerous operation blocking
4. DDL permission checks

### CORS
- Development: `http://localhost:{FRONTEND_PORT}`
- Production: Configure via environment

### Rate Limiting
Currently not implemented - consider for production.

## Configuration

### Environment Variables
- `BACKEND_PORT` - Backend port (default: 8000)
- `ANTHROPIC_API_KEY` - Anthropic API key
- `OPENAI_API_KEY` - OpenAI API key (optional)
- `DATABASE_PATH` - SQLite database path (default: `db/database.db`)

## Testing

### Manual Testing
```bash
# Health check
curl http://localhost:8000/api/health

# Upload file
curl -X POST -F "file=@users.csv" http://localhost:8000/api/upload

# Query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show all users", "provider": "anthropic"}'

# Schema
curl http://localhost:8000/api/schema
```

### E2E Tests
See `.claude/commands/e2e/` for Playwright-based tests:
- `test_basic_query.md`
- `test_export_functionality.md`
- `test_sql_injection.md`
