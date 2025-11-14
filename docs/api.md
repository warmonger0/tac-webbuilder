# API Reference

Complete reference for the tac-webbuilder backend API.

## Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
- [WebSocket Protocol](#websocket-protocol)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

## Base URL

**Development:** `http://localhost:8002`
**Production:** Configure via `API_URL` environment variable

**API Documentation:** [http://localhost:8002/docs](http://localhost:8002/docs) (Swagger UI)

## Authentication

Currently, the API uses API keys configured in environment variables. Future versions may include OAuth or JWT authentication.

**Headers:**
```
X-API-Key: your-api-key-here
```

## Endpoints

### Health Check

Check if the API is running.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "0.1.0"
}
```

**cURL Example:**
```bash
curl http://localhost:8002/health
```

---

### Create Request

Submit a natural language request to create a GitHub issue.

**Endpoint:** `POST /api/request`

**Request Body:**
```json
{
  "request_text": "Add user authentication with email/password and OAuth",
  "project_path": "/path/to/project",
  "repository": "owner/repo",
  "labels": ["enhancement", "priority-high"],
  "auto_trigger": true
}
```

**Response:**
```json
{
  "success": true,
  "issue_number": 42,
  "issue_url": "https://github.com/owner/repo/issues/42",
  "repository": "owner/repo",
  "workflow_triggered": true,
  "metadata": {
    "framework": "React + Vite",
    "complexity": "medium",
    "estimated_time": "2-3 hours"
  }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8002/api/request \
  -H "Content-Type: application/json" \
  -d '{
    "request_text": "Add dark mode toggle",
    "repository": "owner/repo"
  }'
```

---

### Preview Issue

Generate a preview of the GitHub issue without posting it.

**Endpoint:** `POST /api/preview`

**Request Body:**
```json
{
  "request_text": "Add user authentication",
  "project_path": "/path/to/project",
  "repository": "owner/repo"
}
```

**Response:**
```json
{
  "title": "Add user authentication",
  "body": "# Feature Request\n\n## Description\n...",
  "labels": ["enhancement"],
  "metadata": {
    "framework": "React + Vite",
    "complexity": "medium",
    "files_affected": ["src/auth/", "src/api/"],
    "tests_required": true
  }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8002/api/preview \
  -H "Content-Type: application/json" \
  -d '{
    "request_text": "Add dark mode",
    "repository": "owner/repo"
  }'
```

---

### Confirm and Post

Confirm a previewed issue and post it to GitHub.

**Endpoint:** `POST /api/confirm`

**Request Body:**
```json
{
  "preview_id": "uuid-here",
  "title": "Modified title",
  "body": "Modified body",
  "labels": ["enhancement", "ui"]
}
```

**Response:**
```json
{
  "success": true,
  "issue_number": 43,
  "issue_url": "https://github.com/owner/repo/issues/43"
}
```

---

### Get Request History

Retrieve history of created requests.

**Endpoint:** `GET /api/history`

**Query Parameters:**
- `limit` - Number of results (default: 20, max: 100)
- `offset` - Pagination offset (default: 0)
- `repo` - Filter by repository
- `status` - Filter by status (open, closed, all)
- `search` - Search text in requests

**Response:**
```json
{
  "requests": [
    {
      "id": "uuid",
      "request_text": "Add user authentication",
      "issue_number": 42,
      "issue_url": "https://github.com/owner/repo/issues/42",
      "repository": "owner/repo",
      "status": "open",
      "created_at": "2024-01-15T10:30:00Z",
      "pr_number": null,
      "pr_url": null
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0
}
```

**cURL Example:**
```bash
curl "http://localhost:8002/api/history?limit=10&repo=owner/repo"
```

---

### Detect Project

Analyze a project and detect its framework and structure.

**Endpoint:** `POST /api/detect`

**Request Body:**
```json
{
  "project_path": "/path/to/project"
}
```

**Response:**
```json
{
  "framework": "React + Vite",
  "package_manager": "bun",
  "test_framework": "Vitest",
  "typescript": true,
  "structure": {
    "src": true,
    "tests": true,
    "public": true
  },
  "dependencies": {
    "react": "^18.3.1",
    "vite": "^5.3.1"
  }
}
```

---

### List Repositories

Get list of accessible GitHub repositories.

**Endpoint:** `GET /api/repos`

**Query Parameters:**
- `org` - Filter by organization
- `search` - Search by name
- `limit` - Number of results (default: 20)

**Response:**
```json
{
  "repositories": [
    {
      "name": "myapp",
      "full_name": "owner/myapp",
      "description": "My web application",
      "private": true,
      "default_branch": "main",
      "open_issues": 5,
      "url": "https://github.com/owner/myapp"
    }
  ],
  "total": 50
}
```

---

### Get Workflow Status

Get status of an ADW workflow for a specific issue.

**Endpoint:** `GET /api/workflow/{issue_number}`

**Path Parameters:**
- `issue_number` - GitHub issue number

**Query Parameters:**
- `repo` - Repository (owner/repo)

**Response:**
```json
{
  "issue_number": 42,
  "repository": "owner/repo",
  "status": "in_progress",
  "stage": "implementing",
  "progress": 65,
  "started_at": "2024-01-15T10:35:00Z",
  "estimated_completion": "2024-01-15T12:30:00Z",
  "pr_number": null,
  "logs": [
    {
      "timestamp": "2024-01-15T10:35:00Z",
      "level": "info",
      "message": "Starting implementation..."
    }
  ]
}
```

**cURL Example:**
```bash
curl "http://localhost:8002/api/workflow/42?repo=owner/myapp"
```

---

### Cancel Workflow

Cancel a running ADW workflow.

**Endpoint:** `POST /api/workflow/{issue_number}/cancel`

**Request Body:**
```json
{
  "repository": "owner/repo",
  "reason": "User requested cancellation"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Workflow cancelled successfully"
}
```

## WebSocket Protocol

Real-time updates via WebSocket connection.

**Endpoint:** `ws://localhost:8002/ws`

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8002/ws')

ws.onopen = () => {
  console.log('Connected')
  // Subscribe to events
  ws.send(JSON.stringify({
    type: 'subscribe',
    topics: ['workflow', 'issues']
  }))
}

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  console.log('Event:', data)
}
```

### Event Types

**Workflow Started:**
```json
{
  "type": "workflow.started",
  "issue_number": 42,
  "repository": "owner/repo",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

**Workflow Progress:**
```json
{
  "type": "workflow.progress",
  "issue_number": 42,
  "stage": "implementing",
  "progress": 45,
  "message": "Adding authentication logic...",
  "timestamp": "2024-01-15T10:40:00Z"
}
```

**Workflow Completed:**
```json
{
  "type": "workflow.completed",
  "issue_number": 42,
  "status": "success",
  "pr_number": 45,
  "pr_url": "https://github.com/owner/repo/pull/45",
  "timestamp": "2024-01-15T12:30:00Z"
}
```

**Issue Updated:**
```json
{
  "type": "issue.updated",
  "issue_number": 42,
  "status": "closed",
  "merged": true,
  "timestamp": "2024-01-15T13:00:00Z"
}
```

## Error Handling

All errors follow a consistent format:

**Error Response:**
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Request text is required",
    "details": {
      "field": "request_text",
      "reason": "Field is required"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Codes

- `INVALID_REQUEST` - Malformed or missing required fields
- `NOT_FOUND` - Resource not found
- `UNAUTHORIZED` - Authentication failed
- `FORBIDDEN` - Insufficient permissions
- `RATE_LIMITED` - Too many requests
- `INTERNAL_ERROR` - Server error
- `GITHUB_ERROR` - GitHub API error
- `WORKFLOW_ERROR` - ADW workflow error

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error
- `502` - Bad Gateway
- `503` - Service Unavailable

## Rate Limiting

API endpoints are rate-limited to prevent abuse.

**Limits:**
- 100 requests per minute per IP
- 1000 requests per hour per API key

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

**Rate Limit Exceeded Response:**
```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded. Try again in 42 seconds.",
    "details": {
      "retry_after": 42
    }
  }
}
```

## See Also

- [CLI Reference](cli.md) - Command-line interface
- [Web UI Guide](web-ui.md) - Web interface documentation
- [Examples](examples.md) - Example API calls
- [Troubleshooting](troubleshooting.md) - Common issues
