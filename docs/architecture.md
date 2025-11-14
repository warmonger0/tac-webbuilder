# Architecture Documentation

System architecture and design of tac-webbuilder.

## Table of Contents

- [Overview](#overview)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [ADW Integration](#adw-integration)
- [Technology Stack](#technology-stack)
- [Design Decisions](#design-decisions)

## Overview

tac-webbuilder is a natural language interface for web development that bridges human intent with automated development workflows (ADW). It consists of three main components:

1. **CLI** - Command-line interface for developers
2. **Web UI** - Visual interface for non-technical users
3. **Backend API** - Core processing and GitHub integration

```
┌─────────────┐     ┌─────────────┐
│     CLI     │     │   Web UI    │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └───────┬───────────┘
               │
        ┌──────▼──────┐
        │  Backend API │
        └──────┬──────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐  ┌──▼──┐  ┌────▼────┐
│GitHub │  │ ADW │  │ Project │
│  API  │  │     │  │Detection│
└───────┘  └─────┘  └─────────┘
```

## System Components

### 1. CLI (Command-Line Interface)

**Location:** `scripts/start_cli.sh`, `app/server/cli.py`

**Responsibilities:**
- Parse command-line arguments
- Read natural language requests
- Call backend API
- Display results and progress
- Manage local history

**Key Features:**
- Interactive and non-interactive modes
- Request history management
- Configuration management
- Project detection
- Template scaffolding

**Implementation:**
- Python with `click` library
- Direct API calls to backend
- Local SQLite for history
- Configuration in `~/.config/tac-webbuilder/`

### 2. Web UI (Frontend)

**Location:** `app/client/`

**Responsibilities:**
- Visual request form
- Issue preview
- Real-time workflow monitoring
- History browsing
- Project management

**Technology:**
- **Framework:** React 18 with TypeScript
- **Build Tool:** Vite
- **Styling:** CSS Modules
- **State Management:** React Context + Hooks
- **WebSocket:** Native WebSocket API
- **HTTP Client:** Fetch API

**Key Components:**
```
src/
├── components/
│   ├── RequestForm.tsx      # Main request input
│   ├── IssuePreview.tsx     # Preview generated issue
│   ├── WorkflowMonitor.tsx  # Real-time progress
│   └── History.tsx          # Request history
├── api/
│   ├── client.ts            # API client
│   └── websocket.ts         # WebSocket client
├── hooks/
│   ├── useWebSocket.ts      # WebSocket hook
│   └── useProject.ts        # Project detection hook
└── App.tsx                  # Main app component
```

### 3. Backend API

**Location:** `app/server/`

**Responsibilities:**
- Natural language processing
- GitHub API integration
- Project detection
- Request management
- WebSocket server
- ADW workflow triggering

**Technology:**
- **Framework:** FastAPI (Python)
- **HTTP Server:** Uvicorn
- **WebSocket:** FastAPI WebSocket support
- **Database:** SQLite (development), PostgreSQL (production)
- **Async:** asyncio for concurrent operations

**Core Modules:**

```
app/server/
├── main.py                  # FastAPI app
├── core/
│   ├── nl_processor.py      # Natural language processing
│   ├── github_poster.py     # GitHub API integration
│   ├── project_detector.py  # Framework detection
│   └── workflow_manager.py  # ADW workflow management
├── routers/
│   ├── request.py           # Request endpoints
│   ├── history.py           # History endpoints
│   └── websocket.py         # WebSocket endpoint
└── models/
    ├── request.py           # Request models
    └── history.py           # History models
```

### 4. Natural Language Processor

**File:** `app/server/core/nl_processor.py`

**Responsibilities:**
- Parse natural language requests
- Extract intent and requirements
- Generate GitHub issue title and body
- Determine complexity and labels
- Identify affected files

**Process:**
1. **Tokenization** - Break request into sentences
2. **Intent Recognition** - Identify what user wants
3. **Entity Extraction** - Extract technologies, features, constraints
4. **Structure Generation** - Create formatted issue body
5. **Metadata Generation** - Add labels, complexity, estimates

**Uses:**
- Pattern matching for common requests
- Keyword extraction for technologies
- Template filling for issue structure
- Claude API for complex analysis (optional)

### 5. GitHub Poster

**File:** `app/server/core/github_poster.py`

**Responsibilities:**
- Authenticate with GitHub API
- Create issues with proper formatting
- Add labels and metadata
- Trigger webhooks
- Track issue status

**Implementation:**
- Uses `PyGithub` library
- Token authentication
- Rate limit handling
- Error recovery
- Webhook integration

### 6. Project Detector

**File:** `app/server/core/project_detector.py`

**Responsibilities:**
- Analyze project directory structure
- Detect framework and tools
- Identify package manager
- Find test framework
- Extract dependencies

**Detection Logic:**
```python
def detect_framework(project_path):
    if has_file("package.json"):
        if has_dependency("next"):
            return "Next.js"
        elif has_dependency("react"):
            if has_dependency("vite"):
                return "React + Vite"
            return "React (CRA)"
    elif has_file("requirements.txt"):
        if has_dependency("fastapi"):
            return "FastAPI"
    return "Unknown"
```

### 7. ADW Workflow Manager

**File:** `app/server/core/workflow_manager.py`

**Responsibilities:**
- Trigger ADW workflows
- Monitor workflow progress
- Stream logs to clients
- Handle workflow errors
- Manage workflow state

**Integration:**
- Creates GitHub issues with ADW labels
- Monitors issue events via webhooks
- Tracks PR creation and status
- Reports progress via WebSocket
- Handles workflow cancellation

## Data Flow

### Creating a Request

```
1. User Input
   ├─> CLI: Command line argument
   └─> Web UI: Text area input

2. Backend Processing
   ├─> Natural Language Processing
   │   ├─> Parse request text
   │   ├─> Extract requirements
   │   └─> Generate issue structure
   ├─> Project Detection
   │   ├─> Analyze project files
   │   ├─> Detect framework
   │   └─> Find dependencies
   └─> Issue Generation
       ├─> Format title and body
       ├─> Add labels
       └─> Calculate complexity

3. Preview (Optional)
   └─> Return formatted issue to client

4. Confirmation
   └─> Post issue to GitHub

5. ADW Trigger
   ├─> GitHub webhook fires
   ├─> ADW workflow starts
   └─> Real-time updates via WebSocket

6. Workflow Execution
   ├─> Planning stage
   ├─> Implementation stage
   ├─> Testing stage
   ├─> Review stage
   └─> PR creation

7. Completion
   ├─> PR merged
   ├─> Issue closed
   └─> Notification sent
```

### Real-time Updates

```
WebSocket Connection:
   Client ──connect──> Server
   Client <──ack────── Server

Subscription:
   Client ──subscribe──> Server
   (topics: workflow, issues)

Events:
   Workflow Progress:
      Server ──event──> Client
      (stage, progress, logs)

   Issue Updates:
      GitHub ──webhook──> Server
      Server ──event───> Client
```

## ADW Integration

### Workflow Stages

**1. Planning**
- Read issue description
- Analyze project structure
- Create technical specification
- Identify files to modify

**2. Implementation**
- Write code changes
- Follow project patterns
- Use appropriate technologies
- Maintain code quality

**3. Testing**
- Run existing tests
- Write new tests
- Validate functionality
- Check for regressions
- Execute E2E tests via Playwright MCP (browser automation)
- Capture screenshots for visual validation

**4. Review**
- Create pull request
- Add description
- Request review
- Link to issue

**5. Merge**
- Address review comments
- Update based on feedback
- Merge to main branch
- Close issue

### Triggering ADW

Issues trigger ADW when they have:
- Specific labels (e.g., `adw-auto`, `enhancement`)
- Issue body format recognized by ADW
- Repository webhook configured

### Monitoring ADW

Backend monitors ADW by:
- Polling GitHub API for PR status
- Receiving webhook events
- Reading workflow logs from worktrees
- Tracking state files in `adws/` directory

## Technology Stack

### Frontend
- **React** 18.3 - UI framework
- **TypeScript** 5.5 - Type safety
- **Vite** 5.3 - Build tool
- **CSS Modules** - Scoped styling
- **WebSocket** - Real-time updates

### Backend
- **FastAPI** - Web framework
- **Python** 3.10+ - Language
- **Uvicorn** - ASGI server
- **PyGithub** - GitHub API client
- **SQLite/PostgreSQL** - Database
- **asyncio** - Async operations

### Infrastructure
- **GitHub Actions** - CI/CD
- **Docker** - Containerization
- **Git Worktrees** - ADW isolation
- **uv** - Python package manager
- **bun/npm** - JavaScript package manager

## Design Decisions

### Why FastAPI?

- **Performance:** Async support for concurrent operations
- **Type Safety:** Pydantic models for validation
- **Documentation:** Auto-generated API docs
- **WebSocket:** Built-in WebSocket support
- **Modern:** Python 3.10+ with type hints

### Why React + Vite?

- **Developer Experience:** Fast HMR and build times
- **Type Safety:** TypeScript integration
- **Ecosystem:** Rich component libraries
- **Performance:** Optimized production builds
- **Flexibility:** Easy to extend and customize

### Why Git Worktrees for ADW?

- **Isolation:** Each workflow in separate directory
- **Concurrent:** Multiple workflows in parallel
- **Clean:** No branch conflicts
- **Reliable:** Atomic commits and pushes
- **Traceable:** Clear state management

### Why SQLite for History?

- **Simple:** No external database required
- **Fast:** Local file-based storage
- **Portable:** Single file database
- **Reliable:** ACID compliance
- **Lightweight:** Minimal dependencies

### Why WebSocket for Real-time?

- **Bidirectional:** Server can push updates
- **Efficient:** Persistent connection
- **Real-time:** Instant notifications
- **Standard:** Native browser support
- **Scalable:** Can handle many clients

## Scalability Considerations

### Current Limitations

- Single backend instance
- SQLite for persistence (not suitable for high concurrency)
- No load balancing
- Limited to one ADW workflow per repo

### Future Improvements

- **Database:** Migrate to PostgreSQL
- **Caching:** Add Redis for sessions and real-time data
- **Queue:** Use Celery for background tasks
- **Load Balancer:** Support multiple backend instances
- **CDN:** Serve static assets from CDN
- **Monitoring:** Add observability (Prometheus, Grafana)

## Security Considerations

### Authentication

- GitHub token stored in environment variables
- API keys for backend access
- No passwords stored in database

### Authorization

- GitHub permissions checked before operations
- Repository access validated
- User permissions enforced

### Data Protection

- No sensitive data in logs
- API keys not exposed to frontend
- HTTPS for production (configured externally)
- CORS properly configured

### Best Practices

- Input validation on all endpoints
- Rate limiting to prevent abuse
- Error messages don't leak internals
- Dependencies kept up-to-date

## See Also

- [CLI Reference](cli.md) - CLI usage
- [Web UI Guide](web-ui.md) - Web interface
- [API Reference](api.md) - API documentation
- [Examples](examples.md) - Usage examples
