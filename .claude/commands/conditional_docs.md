# Conditional Documentation Guide

**Goal:** Load only the documentation you need. Use progressive loading to minimize context.

## Instructions
1. Identify your task category below
2. Check if conditions match
3. Load ONLY matching docs (prefer quick references over full docs)

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

### Decision Tree [~400 tokens]
- `.claude/commands/references/decision_tree.md`
  - Conditions: Not sure which docs to load, need routing guidance

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

### Analytics & Insights Features
- `app_docs/feature-a7c948e2-insights-recommendations.md` - Phase 3D anomaly detection, optimization recommendations, workflow analytics insights, complexity detection, statistical thresholds
  - Conditions:
    - Working with workflow analytics or scoring systems
    - Implementing anomaly detection or recommendation engines
    - Troubleshooting workflow insights calculation
    - Modifying workflow_analytics.py or workflow_history.py
    - Adding new recommendation categories or anomaly types

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

### Pattern Recognition Features
- `app_docs/feature-adw-fb7aff61-pattern-detection-logging.md` - Pattern recognition Phase 1 implementation, structured logging infrastructure, pattern prediction at submission time, frontend pattern display
  - Conditions:
    - Working with pattern recognition or prediction systems
    - Implementing or troubleshooting pattern_logging.py or pattern_predictor.py
    - Understanding pattern_predictions database schema
    - Adding pattern detection to new workflow types
    - Troubleshooting pattern prediction accuracy
    - Working with ConfirmDialog or RequestForm pattern display components
    - Analyzing pattern recognition logs or performance metrics

### Templates & Integration Features
- `app_docs/feature-0f04f66d-project-templates-docs.md` - Project templates, scaffolding scripts, setup_new_project.sh
- `templates/existing_webapp/integration_guide.md` - Integrating ADW into existing projects
- `templates/template_structure.json` - Template structure definitions

---

## Special Purpose Docs

### .claude/commands/classify_adw.md
- Conditions: Adding or removing adws/adw_*.py workflow files

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
