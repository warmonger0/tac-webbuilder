# Architecture Overview

## System Components

### 1. NL SQL Interface (Original Feature)
- **Purpose:** Convert natural language queries to SQL and execute on uploaded data
- **Tech Stack:** FastAPI + React + SQLite + OpenAI/Anthropic
- **Entry Points:**
  - Backend: `app/server/server.py` (port 8000)
  - Frontend: `app/client/src/main.tsx` (port 5173)

### 2. NL → GitHub Issue Generator (Core Workflow)
- **Purpose:** Convert natural language requests into structured GitHub issues
- **Pipeline:** NL Input → Claude Analysis → Issue Formatting → GitHub Posting → ADW Trigger
- **Key Modules:**
  - `app/server/core/nl_processor.py` - Intent analysis
  - `app/server/core/issue_formatter.py` - Issue generation
  - `app/server/core/project_detector.py` - Tech stack detection
  - `app/server/core/github_poster.py` - GitHub integration

### 3. ADW Automation System (Development Engine)
- **Purpose:** Automated software development via isolated git worktrees
- **Architecture:** Worktree-based isolation with Claude Code CLI integration
- **Capacity:** Up to 15 concurrent workflows
- **Phases:** Plan → Build → Test → Review → Document → Ship

## Data Flow

```
User Input (NL)
  ↓
React Frontend (TanStack Query + Zustand)
  ↓
FastAPI Backend
  ↓
NL Processor (Claude API)
  ↓
GitHub Issue (via gh CLI)
  ↓
Webhook/Cron Trigger
  ↓
ADW Workflow (Isolated Worktree @ trees/{adw_id}/)
  ↓
Claude Code Agent (Sonnet/Opus)
  ↓
Git Commit + PR
  ↓
Auto-merge (optional ZTE mode)
```

## Worktree Isolation Architecture

Each ADW workflow runs in:
- **Isolated git worktree:** `trees/{adw_id}/` (complete repo copy)
- **Dedicated ports:** Backend 9100-9114, Frontend 9200-9214
- **Deterministic allocation:** Hash-based port assignment from ADW ID
- **State persistence:** `agents/{adw_id}/adw_state.json`

## Cost Optimization Framework

### Complexity-Based Routing
- **Lightweight workflow:** $0.20-0.50 for simple changes
- **Standard SDLC:** $3-5 for complex features
- **Analyzer:** `adws/adw_modules/complexity_analyzer.py`

### Context Reduction
- **Enhanced .claudeignore:** 70% token reduction (3M+ → 900K)
- **Conditional docs:** Load documentation only when needed
- **Progressive estimation:** Track costs per phase

### Model Selection
- **Base set:** Sonnet for most operations (cost-optimized)
- **Heavy set:** Opus for complex tasks (implement, debug, document)
- **Per-command mapping:** 35+ commands with individual model assignments

## Security Architecture

### SQL Injection Prevention (Multi-Layer)
1. **Identifier validation:** Whitelist pattern matching
2. **Parameterized queries:** All user values use `?` placeholders
3. **Query validation:** Block dangerous operations (DROP, DELETE, etc.)
4. **DDL blocking:** Require explicit permission for schema changes

**Module:** `app/server/core/sql_security.py`
**Test Coverage:** 30+ security tests in `tests/test_sql_injection.py`

## Frontend Architecture (React Migration)

### Component Structure
- **App.tsx** - Main shell with tab navigation
- **RequestForm.tsx** - NL input and workflow triggering
- **WorkflowDashboard.tsx** - Real-time ADW monitoring
- **HistoryView.tsx** - Request history browser
- **RoutesView.tsx** - API route visualization

### State Management
- **Zustand** - Global state management
- **TanStack Query** - Server state, caching, refetching
- **WebSocket** - Real-time workflow updates via `useWebSocket` hook

### Styling
- **Tailwind CSS 3.4** - Utility-first styling
- **CSS Modules** - Scoped component styles
- **Custom theme** - Via `tailwind.config.js`

## Backend Architecture

### Core Modules
- **server.py** - FastAPI application entry point
- **core/llm_processor.py** - AI model integration (OpenAI + Anthropic)
- **core/nl_processor.py** - Natural language processing
- **core/sql_processor.py** - SQL execution
- **core/sql_security.py** - Security layer
- **core/file_processor.py** - File upload handling
- **core/export_utils.py** - CSV export utilities
- **core/data_models.py** - Pydantic models (20+ models)

### Database
- **SQLite** - Development database
- **Dynamic schema** - Tables created from uploaded files
- **Location:** `app/server/db/database.db`

## Integration Points

### GitHub
- **CLI Integration:** `gh` command via subprocess
- **Webhook Server:** `adws/adw_triggers/trigger_webhook.py` (port 8001)
- **Polling Monitor:** `adws/adw_triggers/trigger_cron.py` (20s interval)

### Claude Code CLI
- **Programmatic mode:** JSONL output streaming
- **Slash commands:** 35+ custom commands in `.claude/commands/`
- **Worktree context:** Executes in isolated directories
- **Model routing:** Dynamic Sonnet/Opus selection

### Cloudflare R2
- **Screenshot uploads:** Review phase captures
- **Public URLs:** Embedded in GitHub comments
- **Optional:** Falls back to local paths

### Playwright MCP
- **Browser automation:** E2E testing
- **Screenshot/video:** Capture capabilities
- **Configuration:** `playwright-mcp-config.json`

## Recent Innovations

### 1. Complexity Analyzer (NEW)
- **File:** `adws/adw_modules/complexity_analyzer.py`
- **Purpose:** Route to lightweight vs standard workflows
- **Impact:** 90%+ cost reduction for simple changes

### 2. Lightweight Workflow (NEW)
- **File:** `adws/adw_lightweight_iso.py`
- **Target cost:** $0.20-0.50 (vs $3-5 standard)
- **Use cases:** CSS changes, text updates, simple refactors

### 3. ZTE Hopper Queue (NEW)
- **File:** `scripts/zte_hopper.sh`
- **Purpose:** Batch process multiple GitHub issues
- **Features:** Auto-validation, FIFO ordering, unattended execution

### 4. Routes Visualization (NEW)
- **File:** `app/server/core/routes_analyzer.py`
- **Purpose:** AST-based API route discovery
- **UI:** RoutesView component with filtering

### 5. React Migration (COMPLETE)
- **From:** Vanilla TypeScript
- **To:** React 18.3 + TanStack Query + Zustand
- **Benefits:** Component reusability, better state management

## Documentation Structure

- **`docs/`** - Technical documentation (13 files)
  - `architecture.md` - System design (465 lines)
  - `api.md`, `cli.md`, `web-ui.md` - Interface docs
  - `playwright-mcp.md` - E2E testing
  - `adw-optimization.md` - Cost optimization
- **`app_docs/`** - Feature specifications (8 files)
- **`.claude/commands/`** - Slash commands (35 files)
- **`.claude/commands/references/`** - Detailed reference docs
