# Architecture

High-level system design and architecture overview for tac-webbuilder.

For detailed technical documentation, see [docs/architecture.md](docs/architecture.md).

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Design Decisions](#design-decisions)

## Overview

tac-webbuilder is a natural language interface for web development that bridges human intent with automated development workflows (ADW). It enables users to describe what they want in plain English, and the system translates that into GitHub issues that trigger automated development cycles.

The system consists of three main interfaces:

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

## Project Structure

```
tac-webbuilder/
├── app/
│   ├── client/              # React + TypeScript frontend
│   │   ├── src/
│   │   │   ├── components/  # React components
│   │   │   ├── api/         # API client
│   │   │   ├── hooks/       # Custom React hooks
│   │   │   └── App.tsx      # Main app
│   │   └── vite.config.ts   # Vite configuration
│   └── server/              # FastAPI backend
│       ├── main.py          # FastAPI app entry
│       ├── core/            # Core business logic
│       │   ├── nl_processor.py      # Natural language processing
│       │   ├── github_poster.py     # GitHub API integration
│       │   ├── project_detector.py  # Framework detection
│       │   └── workflow_manager.py  # ADW workflow management
│       ├── routers/         # API route handlers
│       └── models/          # Pydantic data models
│
├── scripts/                 # Utility scripts
│   ├── start_cli.sh         # CLI launcher
│   └── copy_dot_env.sh      # Environment setup
│
├── adws/                    # ADW worktrees and state
│   ├── worktrees/           # Git worktrees for isolated work
│   └── state/               # Workflow state tracking
│
├── docs/                    # Technical documentation
│   ├── architecture.md      # Detailed architecture (this doc summarizes it)
│   ├── api.md               # API reference
│   ├── cli.md               # CLI reference
│   └── web-ui.md            # Web UI guide
│
├── app_docs/                # Feature documentation
│   ├── nl-processor.md      # Natural language processing
│   ├── github-integration.md # GitHub API integration
│   └── ...                  # Other feature docs
│
├── specs/                   # Planning specifications
│   └── patch/               # Patch-level specs
│
├── issues/                  # Issue tracking
│   ├── active/              # Currently worked on
│   ├── completed/           # Finished issues
│   └── planning/            # In planning phase
│
├── tests/                   # Test suites
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
│
└── README.md                # Getting started guide
```

## System Components

### 1. CLI (Command-Line Interface)

**Location:** `scripts/start_cli.sh`, `app/server/cli.py`

The CLI provides a developer-friendly command-line interface for creating requests.

**Key Features:**
- Interactive and non-interactive modes
- Request history management
- Configuration management (`~/.config/tac-webbuilder/`)
- Project detection and framework identification
- Template scaffolding

**Implementation:**
- Python with `click` library
- Direct API calls to backend
- Local SQLite for history
- Configuration file management

### 2. Web UI (Frontend)

**Location:** `app/client/`

A visual interface built with React and TypeScript that provides real-time feedback and workflow monitoring.

**Key Features:**
- Visual request form with validation
- Issue preview before posting to GitHub
- Real-time workflow monitoring via WebSocket
- History browsing and management
- Project detection and configuration

**Technology:**
- React 18 with TypeScript
- Vite for fast builds and HMR
- CSS Modules for scoped styling
- React Context + Hooks for state management
- Native WebSocket API for real-time updates

**Core Components:**
- `RequestForm.tsx` - Main request input interface
- `IssuePreview.tsx` - Preview generated issues
- `WorkflowMonitor.tsx` - Real-time progress tracking
- `History.tsx` - Request history browser

### 3. Backend API

**Location:** `app/server/`

The backend processes natural language requests, integrates with GitHub, and manages ADW workflows.

**Key Responsibilities:**
- Natural language processing
- GitHub API integration
- Project framework detection
- Request and history management
- WebSocket server for real-time updates
- ADW workflow triggering and monitoring

**Technology:**
- FastAPI (Python) for high-performance async API
- Uvicorn ASGI server
- SQLite (development) / PostgreSQL (production)
- asyncio for concurrent operations
- PyGithub for GitHub API integration

### 4. Natural Language Processor

**File:** `app/server/core/nl_processor.py`

Transforms natural language requests into structured GitHub issues.

**Process:**
1. Parse and tokenize the request
2. Extract intent and requirements
3. Identify technologies and constraints
4. Generate structured issue body
5. Determine complexity, labels, and estimates

### 5. GitHub Integration

**File:** `app/server/core/github_poster.py`

Handles all GitHub API interactions.

**Responsibilities:**
- Authentication with GitHub API
- Create issues with proper formatting
- Add labels and metadata
- Trigger webhooks for ADW
- Track issue and PR status

### 6. Project Detector

**File:** `app/server/core/project_detector.py`

Analyzes project structure to detect framework, tools, and dependencies.

**Detection:**
- Framework identification (React, Next.js, FastAPI, etc.)
- Package manager detection (npm, bun, uv, pip)
- Test framework identification
- Dependency extraction

### 7. ADW Workflow Manager

**File:** `app/server/core/workflow_manager.py`

Manages automated development workflows.

**Capabilities:**
- Trigger ADW workflows via GitHub issues
- Monitor workflow progress
- Stream logs to clients via WebSocket
- Handle workflow errors and cancellation
- Manage workflow state in git worktrees

## Data Flow

### Creating a Request

```
1. User Input (CLI or Web UI)
   └─> Natural language description

2. Backend Processing
   ├─> Natural Language Processing
   │   ├─> Parse request
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

4. Confirmation & Posting
   └─> Post issue to GitHub

5. ADW Trigger
   ├─> GitHub webhook fires
   ├─> ADW workflow starts
   └─> Real-time updates via WebSocket

6. Workflow Execution
   ├─> Planning stage (spec creation)
   ├─> Implementation stage (code changes)
   ├─> Testing stage (run tests, create new tests)
   ├─> Review stage (create PR)
   └─> Merge (after approval)

7. Completion
   ├─> PR merged
   ├─> Issue closed
   └─> Notification sent
```

### Real-time Updates Flow

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

## Technology Stack

### Frontend
- **React** 18.3 - UI framework
- **TypeScript** 5.5 - Type safety
- **Vite** 5.3 - Fast build tool with HMR
- **CSS Modules** - Scoped styling
- **WebSocket** - Real-time updates

### Backend
- **FastAPI** - Modern async web framework
- **Python** 3.10+ - Language
- **Uvicorn** - ASGI server
- **PyGithub** - GitHub API client
- **SQLite/PostgreSQL** - Database
- **asyncio** - Async operations

### Infrastructure
- **GitHub Actions** - CI/CD pipelines
- **Docker** - Containerization
- **Git Worktrees** - ADW workflow isolation
- **uv** - Fast Python package manager
- **bun/npm** - JavaScript package manager

## Design Decisions

### Why FastAPI?
- **Performance:** Built-in async support for concurrent operations
- **Type Safety:** Pydantic models for automatic validation
- **Documentation:** Auto-generated OpenAPI/Swagger docs
- **WebSocket:** Native WebSocket support
- **Modern:** Python 3.10+ with type hints

### Why React + Vite?
- **Developer Experience:** Fast HMR and build times
- **Type Safety:** First-class TypeScript integration
- **Ecosystem:** Rich library and component ecosystem
- **Performance:** Optimized production builds
- **Flexibility:** Easy to extend and customize

### Why Git Worktrees for ADW?
- **Isolation:** Each workflow runs in its own directory
- **Concurrency:** Multiple workflows can run in parallel
- **Clean State:** No branch conflicts or pollution
- **Reliable:** Atomic commits and pushes
- **Traceable:** Clear state management and history

### Why SQLite for History?
- **Simple:** No external database server required
- **Fast:** Local file-based storage
- **Portable:** Single file database
- **Reliable:** ACID compliance
- **Lightweight:** Minimal dependencies

### Why WebSocket for Real-time?
- **Bidirectional:** Server can push updates to clients
- **Efficient:** Persistent connection, low overhead
- **Real-time:** Instant notifications and updates
- **Standard:** Native browser support
- **Scalable:** Can handle many concurrent clients

## ADW Integration

The Automated Development Workflow (ADW) system executes development tasks through GitHub integration:

### Workflow Stages

1. **Planning** - Analyze issue, create technical specification
2. **Implementation** - Write code changes following project patterns
3. **Testing** - Run existing tests, write new tests, validate functionality
4. **Review** - Create pull request with description and documentation
5. **Merge** - Address feedback, merge to main branch, close issue

### Triggering ADW

Issues trigger ADW when they have:
- Specific labels (e.g., `adw-auto`, `enhancement`)
- Issue body format recognized by ADW
- Repository webhook properly configured

### Monitoring ADW

The backend monitors ADW progress by:
- Receiving GitHub webhook events
- Reading workflow logs from worktrees
- Tracking state files in `adws/` directory
- Streaming updates to clients via WebSocket

## See Also

- [README](README.md) - Getting started and quick reference
- [Technical Documentation](docs/) - Detailed technical guides
- [Feature Documentation](app_docs/) - Individual feature specs
- [API Reference](docs/api.md) - API endpoints and usage
- [CLI Reference](docs/cli.md) - CLI commands and options
- [Web UI Guide](docs/web-ui.md) - Web interface documentation
