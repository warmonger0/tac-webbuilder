# Conditional Documentation Guide

**Goal:** Load only the documentation you need. Use progressive loading to minimize context.

## Instructions
1. Identify your task category below
2. Check if conditions match
3. Load ONLY matching docs (prefer quick references over full docs)

---

## Quick Routing (Start Here)

**Not sure which docs to load?** Follow this decision tree:

### Step 1: Identify Your Domain

**Are you working with code?**

- **Frontend** (app/client/) → Read `.claude/commands/quick_start/frontend.md`
- **Backend** (app/server/) → Read `.claude/commands/quick_start/backend.md`
- **ADW** (adws/) → Read `.claude/commands/quick_start/adw.md`
- **Documentation** → Read `.claude/commands/quick_start/docs.md`
- **Not sure?** → Continue to Step 2

### Step 2: Choose Reference Level

**Quick Reference (900-1,700 tokens)** - Fast loading, covers 80% of needs:
- **Architecture/Integration:** `references/architecture_overview.md` [900 tokens]
- **API Endpoints:** `references/api_endpoints.md` [1,700 tokens]
- **ADW Workflows:** `references/adw_workflows.md` [1,500 tokens]

**Full Documentation (2,000-4,000 tokens)** - Comprehensive details:
- **Complete Setup:** `README.md` [1,300 tokens]
- **System Architecture:** `docs/architecture.md` [2,300 tokens]
- **API Details:** `docs/api.md` [2,400 tokens]
- **Frontend Guide:** `docs/web-ui.md` [2,200 tokens]
- **ADW Complete Guide:** `adws/README.md` [3,900 tokens] ⚠️ LARGE

**Feature-Specific** - Use conditional loading below for 40+ feature mappings

### Common Patterns

- **"I'm implementing a new API endpoint"** → `quick_start/backend.md` + `references/api_endpoints.md` (~2,000 tokens)
- **"I'm adding a React component"** → `quick_start/frontend.md` + (optionally) `docs/web-ui.md` (~2,500 tokens)
- **"I'm creating a new ADW workflow"** → `quick_start/adw.md` + `references/adw_workflows.md` (~1,900 tokens)
- **"I'm working on an existing feature"** → Check feature mappings below (~500 tokens)
- **"I need to understand everything"** → Start with `quick_start` for your domain, then `references/architecture_overview.md` (~1,200 tokens total)

### Token Budget Guidelines

**Minimize context loading:**
- Target: <3,000 tokens per session
- Acceptable: 3,000-6,000 tokens
- High: >6,000 tokens (try to avoid)

**Rule of thumb:**
- Quick start + 1-2 quick references = Perfect
- 3+ full docs = Too much (use quick references instead)

---

## Progressive Loading System

### Quick Start Docs [200-400 tokens each]
**Load FIRST for domain-specific context**

- `.claude/commands/quick_start/frontend.md` [~300 tokens]
  - Conditions: Working with app/client/, React components, styling, or frontend state

- `.claude/commands/quick_start/backend.md` [~300 tokens]
  - Conditions: Working with app/server/, API endpoints, SQL, or backend logic

- `.claude/commands/quick_start/adw.md` [~400 tokens]
  - Conditions: Working with adws/, ADW workflows, or worktree isolation

- `.claude/commands/quick_start/docs.md` [~200 tokens]
  - Conditions: Adding or updating documentation

### Scope Detection [~500 tokens]
- `.claude/commands/references/scope_detection.md`
  - Conditions: Implementing features, want to minimize context by detecting frontend/backend/docs/scripts scope
  - Token savings: 50-90% by loading only relevant subsystems

---

## Core System Documentation

### README.md [1,300 tokens]
- Conditions:
  - First-time setup or onboarding
  - Need startup commands (start scripts)
  - Understanding project structure
- **Quick alternative:** `.claude/commands/quick_start/{domain}.md` [300-400 tokens]

### adws/README.md [3,900 tokens] ⚠️ LARGE
- Conditions:
  - Working in adws/ directory
  - Implementing new ADW workflows
  - Deep dive into worktree isolation
- **Quick alternative:** `.claude/commands/references/adw_workflows.md` [1,500 tokens]

### ARCHITECTURE.md [1,900 tokens]
- Conditions:
  - Planning major architectural changes
  - Understanding complete system data flow
  - Onboarding to codebase
- **Quick alternative:** `.claude/commands/references/architecture_overview.md` [900 tokens]

---

## Quick Reference Documentation [900-1,700 tokens each]

### .claude/commands/references/architecture_overview.md [900 tokens]
- Conditions:
  - Understanding system architecture quickly
  - Integration points (GitHub, Claude Code, R2, Playwright)
  - Cost optimization framework
  - Security architecture overview

### .claude/commands/references/adw_workflows.md [1,500 tokens]
- Conditions:
  - Selecting which ADW workflow to use
  - Understanding workflow phases
  - Worktree structure and port allocation
  - Model selection logic

### .claude/commands/references/api_endpoints.md [1,700 tokens]
- Conditions:
  - Quick API endpoint reference
  - Request/response formats
  - Testing API endpoints

---

## Detailed Technical Documentation [2,000-2,400 tokens each]

### docs/api.md [2,400 tokens]
- Conditions:
  - Implementing new API endpoints
  - Modifying existing routes
  - Troubleshooting API issues
- **Quick alternative:** `.claude/commands/references/api_endpoints.md` [1,700 tokens]

### docs/web-ui.md [2,200 tokens]
- Conditions:
  - Implementing React components
  - WebSocket integration
  - Frontend state management details
- **Quick alternative:** `.claude/commands/quick_start/frontend.md` [300 tokens]

### docs/architecture.md [2,300 tokens]
- Conditions:
  - Complete system design understanding
  - Data flow diagrams
  - Component interactions
- **Quick alternative:** `.claude/commands/references/architecture_overview.md` [900 tokens]

### docs/cli.md
- Conditions:
  - Working with CLI commands
  - Implementing new CLI features
  - CLI workflow troubleshooting

### docs/testing/playwright-mcp.md
- Conditions:
  - Playwright MCP configuration
  - E2E testing with browser automation
  - Video recording or screenshot capture
  - MCP server troubleshooting

### docs/troubleshooting.md
- Conditions:
  - Debugging issues or errors
  - Development environment setup
  - Common problems

### docs/examples.md
- Conditions:
  - Understanding common patterns
  - Writing documentation
  - Example use cases

---

## Feature Documentation [~200-500 tokens each]

### Export & Data Features
- `app_docs/feature-490eb6b5-one-click-table-exports.md` - CSV export functionality, download buttons, pandas utilities

### UI & Styling Features
- `app_docs/feature-f055c4f8-off-white-background.md` - Off-white background styling, CSS variables
- `app_docs/feature-6445fc8f-light-sky-blue-background.md` - Light sky blue background variants
- `app_docs/feature-cc73faf1-upload-button-text.md` - Upload button text and labeling
- `app_docs/feature-ba65b834-landing-page-visual-design.md` - Landing page layout, visual separators, Tailwind config
- `app_docs/feature-c80e348c-zte-hopper-queue-card.md` - ZTE Hopper Queue card component, two-column grid layout, RequestForm modifications
  - Conditions:
    - Working with RequestForm component or layout
    - Implementing card-based UI components
    - Modifying ZteHopperQueueCard component
    - Troubleshooting two-column grid layout issues
- `app/client/src/style.css` - Direct CSS modifications

### Backend & Model Features
- `app_docs/feature-4c768184-model-upgrades.md` - LLM model configurations, OpenAI/Anthropic versions, llm_processor module

### NL Processing Features
- `app_docs/feature-e2bbe1a5-nl-processing-issue-formatter.md` - NL processing for GitHub issues, Claude API integration, issue formatting templates, project detection
- `app_docs/feature-afc2e0dd-nl-processing-tests.md` - NL processing tests, framework detection tests
- `app_docs/feature-5e6a13af-nl-processing-docs.md` - Comprehensive NL processing documentation structure

### CLI Features
- `app_docs/feature-fd9119bc-cli-interface.md` - CLI interface, Typer/questionary/rich libraries, interactive workflows

### MCP & Testing Features
- `app_docs/feature-1afd9aba-project-structure-adw-integration.md` - MCP configuration, Playwright MCP integration, worktree isolation, video recording
- `app_docs/feature-ba7c9f28-playwright-mcp-integration.md` - MCP integration in templates, browser automation
- `app_docs/feature-e7613043-playwright-mcp-readme.md` - Playwright MCP README documentation

### Project Structure & Organization
- `app_docs/feature-b5e84e34-frontend-migration.md` - React frontend architecture, TanStack Query, Zustand, Vite config
- `app_docs/feature-7a8b6bca-backend-reorganization.md` - Backend entry points, uvicorn config, app/server structure
- `app_docs/feature-0a6c3431-docs-structure-indexes.md` - Documentation organization, README indexes, cross-referencing

### Environment & Setup Features
- `app_docs/feature-f4d9b5e1-env-setup-scripts.md` - Environment configuration, .env files, setup scripts, bash scripts
- `app_docs/feature-e6104340-env-setup-documentation.md` - Configuration documentation, environment variables reference, CI/CD

### ADW & Automation Features
- `app_docs/feature-26e44bd2-test-worktree-path-fix.md` - ADW worktree path functionality, worktree testing
- `app_docs/feature-23bd15ec-integration-cleanup.md` - Full-stack startup scripts, health checking, graceful shutdown, start_full.sh
- `app_docs/feature-09115cf1-zte-hopper-queue-system.md` - ZTE Hopper queue system, batch processing, zte_hopper.sh
- `app_docs/feature-d2ac5466-workflows-documentation-tab.md` - ADW workflow documentation display, workflow categorization, workflows section UI
- `app_docs/feature-a5b80595-workflow-history-ui-enhancements.md` - Workflow history UI enhancements, classification badges, workflow journey display, structured input visualization, WorkflowHistoryCard component
- `app_docs/feature-da86f01c-adw-monitor-api.md` - ADW Monitor backend API, /api/adw-monitor endpoint, real-time workflow monitoring, state aggregation, process detection, phase progress tracking, modular route architecture
  - Conditions:
    - Working with ADW workflow monitoring or status tracking
    - Implementing new API endpoints in app/server/routes/
    - Understanding server route organization (data, workflow, system, github, websocket modules)
    - Working with app/server/core/adw_monitor.py
    - Troubleshooting workflow status detection or progress calculation
    - Implementing real-time monitoring features or caching strategies

### ADW Cleanup & Maintenance
- `docs/ADW_CLEANUP_PROCESS.md` [220 lines] - Manual archiving, cleanup scripts, UI changes
  - Conditions:
    - Cleaning up closed issue ADW directories
    - Working with ADW monitor cleanup features
    - Archiving old workflow states to agents/_archived/
    - Removing WorkflowDashboard "Current Workflow" tab references
    - Troubleshooting ADW directory clutter
    - Understanding cleanup scripts (scripts/cleanup_closed_adws.sh)
    - Working with Panel 10 (LogPanel) for session tracking

### Observability & Logging Features
- `.claude/commands/references/observability.md` [~900 tokens] - Quick reference for hook events, pattern learning, cost tracking, work logs
  - Conditions:
    - Quick lookup of observability API endpoints
    - Understanding observability database tables
    - Working with Panel 10 (Work Log) component
    - Checking pattern learning status
    - Cost tracking queries
- `docs/features/observability-and-logging.md` [566 lines, ~2,500 tokens] - Comprehensive observability documentation
  - Conditions:
    - Implementing hook event capture in ADW workflows
    - Working with pattern learning and detection algorithms
    - Implementing cost tracking and savings measurement
    - Troubleshooting pattern learning or tool call tracking
    - Working with `work_log`, `hook_events`, `operation_patterns`, `tool_calls`, `cost_savings_log` tables
    - Understanding complete observability architecture
    - Adding entries to Panel 10 (Work Log) via API or UI
    - Designing new automation workflows based on detected patterns
    - Setting up observability for new workflow types
- `docs/architecture/adw-tracking-architecture.md` [~800 tokens] - ADW tool call tracking system architecture
  - Conditions:
    - Understanding two-layer tracking (hook_events vs task_logs.tool_calls)
    - Working with pattern detection infrastructure
    - Implementing ToolCallTracker helper class
    - Understanding pattern approval workflow
    - Database schema for tool tracking (task_logs.tool_calls JSONB column)
- `docs/design/tool-call-tracking-design.md` [~1,200 tokens] - Tool call tracking implementation specification
  - Conditions:
    - Implementing tool call tracking in ADW phases
    - Understanding ToolCallRecord model structure
    - Working with observability.py log_task_completion() tool_calls parameter
    - Database migration for tool_calls column
    - JSON serialization/deserialization of tool calls
- `docs/analysis/tool-tracking-comprehensive-review.md` [~2,000 tokens] - Multi-agent analysis of tool tracking system
  - Conditions:
    - Understanding complete pattern→script automation pipeline
    - Evaluating ROI and cost savings from pattern automation
    - Six critical components: tracking, semantic detection, script generation, validation, registration, ROI feedback
    - 35-day implementation roadmap for complete automation system

### Error Handling & Recovery Features
- `app_docs/design-error-handling-protocol.md` [~750 lines, ~5,000 tokens] - Comprehensive error handling sub-agent protocol design
  - Conditions:
    - Implementing error handling for ADW workflow failures
    - Designing error analysis sub-agents
    - Working with workflow abort detection and recovery
    - Adding "failed" status to Plans Panel
    - Creating one-click fix workflows
    - Implementing cleanup operations after workflow failures
    - Understanding error classification and root cause analysis
    - Working with error reporting and GitHub integration
    - Building fix prompt generation system
    - Integrating error handling with Closed-Loop Automation System (Feature #99)
    - Troubleshooting workflow failure scenarios
    - Adding error analytics and monitoring

### Analytics & Insights Features
- `app_docs/feature-a7c948e2-insights-recommendations.md` - Phase 3D anomaly detection, optimization recommendations, workflow analytics insights, complexity detection, statistical thresholds
  - Conditions:
    - Working with workflow analytics or scoring systems
    - Implementing anomaly detection or recommendation engines
    - Troubleshooting workflow insights calculation
    - Modifying workflow_analytics.py or workflow_history.py
    - Adding new recommendation categories or anomaly types

- `app_docs/feature-pattern-caching-workflow-dry-run.md` - Workflow pattern caching system, intelligent similarity matching (70% threshold), dry-run speed optimization (<1s for 80% of requests), operation_patterns table usage
  - Conditions:
    - Working with pre-flight checks or workflow dry-run analysis
    - Implementing pattern learning or matching algorithms
    - Optimizing dry-run performance or cost estimation
    - Working with app/server/core/workflow_dry_run.py or workflow_pattern_cache.py
    - Troubleshooting pattern cache hits/misses
    - Adding pattern extraction from completed workflows
    - Understanding running averages for pattern statistics
    - Implementing similarity matching with SequenceMatcher
    - Working with operation_patterns database schema

### Routes & Validation Features
- `app_docs/feature-04a76d25-validation-optimization-routes-viz.md` - API routes visualization, AST parsing, routes_analyzer.py, Routes tab UI
- `app_docs/feature-4fc73599-api-routes-display.md` - Dynamic API routes introspection, /api/routes endpoint, route display functionality, FastAPI route discovery

### Database & Infrastructure Features
- `app_docs/feature-63f8bd05-db-connection-migration.md` - Database connection utility migration, centralized connection management, get_connection() context manager
  - Conditions:
    - Working with database connections in core modules
    - Implementing new database operations
    - Refactoring database code to use centralized utilities
    - Troubleshooting connection management issues
    - Understanding utils.db_connection patterns
- `app_docs/feature-af4246c1-workflow-history-schema-fix.md` - Workflow history schema fix, temporal column renaming (hour_of_day, day_of_week), SQLite migration patterns
  - Conditions:
    - Working with workflow_history database schema
    - Troubleshooting workflow history data retrieval errors
    - Creating database migrations that rename columns in SQLite
    - Understanding temporal analytics columns (hour_of_day, day_of_week)
    - Fixing schema mismatches between Python models and database tables
- `app_docs/feature-170-postgresql-pattern-predictions-migration.md` - PostgreSQL migration 010 for pattern predictions tracking, SQLite to PostgreSQL syntax conversion, migration application and verification
  - Conditions:
    - Applying database migrations to PostgreSQL
    - Converting SQLite migrations to PostgreSQL syntax
    - Working with pattern_predictions or operation_patterns tables
    - Implementing pattern validation loop features
    - Troubleshooting PostgreSQL migration issues
    - Understanding foreign key relationships in pattern tracking
    - Verifying database schema after migrations
- `app_docs/feature-dde14b2-workflow-history-postgresql-migration.md` - Workflow history PostgreSQL-only architecture, eliminating hardcoded SQLite paths, database adapter integration in ADW workflows, ToolRegistry refactoring
  - Conditions:
    - Working with ADW workflow database integration
    - Migrating workflows from SQLite to PostgreSQL
    - Refactoring hardcoded database paths to use database adapter
    - Working with adws/adw_review_iso.py or adws/adw_modules/tool_registry.py
    - Troubleshooting ADW workflow data persistence
    - Understanding database adapter pattern implementation
    - Creating database-agnostic queries with parameter placeholders (%s vs ?)
    - Working with workflow_history, adw_tools, or tool_calls tables

### Templates & Integration Features
- `app_docs/feature-0f04f66d-project-templates-docs.md` - Project templates, scaffolding scripts, setup_new_project.sh
- `templates/existing_webapp/integration_guide.md` - Integrating ADW into existing projects
- `templates/template_structure.json` - Template structure definitions

### GitHub Integration & Webhooks
- `app_docs/feature-github-webhook-planned-features-sync.md`
  - Conditions:
    - Working with GitHub webhooks or real-time issue synchronization
    - Implementing webhook handlers with HMAC signature verification
    - Setting up Cloudflare Tunnel routes for public API access
    - Troubleshooting planned features not syncing with GitHub issues
    - Understanding WebSocket broadcast architecture for real-time UI updates
    - Configuring bidirectional GitHub↔database sync

### Git & Version Control Features
- `app_docs/feature-git-commit-ui.md`
  - Conditions:
    - Working with git operations in the frontend UI
    - Implementing git status or commit functionality
    - Adding git-related API endpoints
    - Modifying Panel 1 (System Status section)
    - Troubleshooting git command execution from backend
    - Understanding GitCommitPanel or git_routes.py

---

## Special Purpose Docs

### .claude/commands/classify_adw.md
- Conditions: Adding or removing adws/adw_*.py workflow files

### .claude/commands/updatedocs.md
- Conditions:
  - Completed work in current session that should be documented
  - Created new features that need to be captured in project docs
  - Changed panel status or added API endpoints
  - Finished session and want to update `/prime` command
  - Need to update quick start guides or reference documentation

### Developer Productivity Tools
- `scripts/gen_prompt.sh` - Plan-to-Prompt Generator (Feature #104)
  - Conditions:
    - Converting planned features from Panel 5 into implementation prompts
    - Starting work on a new feature from the roadmap
    - Need structured prompts with codebase context and test locations
    - Want to save 15-18 min per prompt by automating template generation
  - Usage: `./scripts/gen_prompt.sh --list` or `./scripts/gen_prompt.sh 49`
  - Generates: `QUICK_WIN_{id}_{title}.md` or `{TYPE}_{id}_{title}.md` in project root
  - Includes: Codebase analysis (relevant files, functions, test locations)

---

## Loading Strategy Tips

**Minimize context loading:**
1. Start with `/prime` (50-100 tokens)
2. Load domain-specific `quick_start` (300-400 tokens)
3. Use `references/` for quick lookup (900-1,700 tokens)
4. Only load full `docs/` when essential (2,000+ tokens)
5. Load feature docs only when working on that specific feature

**Target:** <3,000 tokens per session
**Acceptable:** 3,000-6,000 tokens
**Avoid:** >6,000 tokens (break into multiple sessions or use smaller docs)
