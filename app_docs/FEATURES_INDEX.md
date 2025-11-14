# Features Index

Quick reference for all implemented features. For complete details, see individual feature files.

## Export & Data Features

### CSV Export (feature-490eb6b5)
**Summary:** One-click CSV export for tables and query results
- Pandas-based export utilities
- Download buttons in UI
- Export API endpoints
**Full doc:** `feature-490eb6b5-one-click-table-exports.md` [101 lines]

## UI & Styling Features

### Off-White Background (feature-f055c4f8)
**Summary:** Off-white background styling for main application
- CSS color variables: `--bg-primary`, `--bg-secondary`
- Theme configuration in style.css
**Full doc:** `feature-f055c4f8-off-white-background.md` [47 lines]

### Light Sky Blue Background (feature-6445fc8f)
**Summary:** Light sky blue background for improved visual hierarchy
- Light blue color variants
- Background color transitions
**Full doc:** `feature-6445fc8f-light-sky-blue-background.md` [51 lines]

### Upload Button Text (feature-cc73faf1)
**Summary:** Updated upload button text and labeling
- UI text changes for clarity
- Upload functionality improvements
**Full doc:** `feature-cc73faf1-upload-button-text.md` [53 lines]

### Landing Page Visual Design (feature-ba65b834)
**Summary:** Landing page layout with visual separators
- Drop shadow effects
- Center-aligned header content
- Tailwind custom colors
**Full doc:** `feature-ba65b834-landing-page-visual-design.md` [88 lines]

## Backend & Model Features

### Model Upgrades (feature-4c768184)
**Summary:** LLM model configuration and version upgrades
- OpenAI and Anthropic model versions
- SQL query generation accuracy improvements
- llm_processor module enhancements
**Full doc:** `feature-4c768184-model-upgrades.md` [79 lines]

## Natural Language Processing Features

### NL Processing - Issue Formatter (feature-e2bbe1a5)
**Summary:** Natural language processing for GitHub issues
- Claude API integration for intent analysis
- Issue formatting templates (feature/bug/chore)
- Project context detection (framework, tech stack)
- GitHub CLI integration
**Modules:** nl_processor.py, issue_formatter.py, project_detector.py, github_poster.py
**Full doc:** `feature-e2bbe1a5-nl-processing-issue-formatter.md` [124 lines]

### NL Processing - Tests (feature-afc2e0dd)
**Summary:** Test coverage for NL processing
- Framework detection tests (Angular, Svelte, Vite, Fastify, NestJS)
- Backend framework tests (Django, Flask, FastAPI)
- pyproject.toml and requirements.txt detection
**Full doc:** `feature-afc2e0dd-nl-processing-tests.md` [89 lines]

### NL Processing - Documentation (feature-5e6a13af)
**Summary:** Comprehensive NL processing documentation
- API documentation structure
- Usage guides and examples
- Mermaid architecture diagrams
**Full doc:** `feature-5e6a13af-nl-processing-docs.md` [156 lines]

## CLI Features

### CLI Interface (feature-fd9119bc)
**Summary:** Interactive CLI interface for tac-webbuilder
- Typer, questionary, and rich libraries
- Interactive workflows
- CLI history tracking
- NL processing integration
**Full doc:** `feature-fd9119bc-cli-interface.md` [134 lines]

## MCP & Testing Features

### Project Structure - ADW Integration (feature-1afd9aba)
**Summary:** MCP configuration and ADW worktree integration
- Playwright MCP server integration
- Worktree isolation for ADW
- Absolute paths for worktree resources
- Video recording directories
**Full doc:** `feature-1afd9aba-project-structure-adw-integration.md` [118 lines]

### Playwright MCP Integration (feature-ba7c9f28)
**Summary:** Playwright MCP integration in project templates
- MCP configuration files (.mcp.json.sample, playwright-mcp-config.json)
- Scaffolding scripts with MCP setup
- E2E testing infrastructure
- Browser automation and video recording
**Full doc:** `feature-ba7c9f28-playwright-mcp-integration.md` [142 lines]

### Playwright MCP README (feature-e7613043)
**Summary:** Playwright MCP README documentation
- Integration documentation sections
- High-level overview bridging README and technical docs
**Full doc:** `feature-e7613043-playwright-mcp-readme.md` [67 lines]

## Project Structure & Organization

### Frontend Migration (feature-b5e84e34)
**Summary:** React frontend architecture migration
- Migration from vanilla TypeScript to React 18.3
- TanStack Query and Zustand state management
- Vite configuration with React plugin
- WebSocket real-time updates
**Components:** App, WorkflowDashboard, RequestForm, HistoryView, RoutesView
**Full doc:** `feature-b5e84e34-frontend-migration.md` [198 lines]

### Backend Reorganization (feature-7a8b6bca)
**Summary:** Backend entry points and module structure
- main.py entry point
- uvicorn configuration
- app/server directory structure
- Migration from interfaces/web to app/server
**Full doc:** `feature-7a8b6bca-backend-reorganization.md` [95 lines]

### Documentation Structure (feature-0a6c3431)
**Summary:** Documentation organization and indexes
- Documentation directory structure
- README index files
- Cross-referencing with "See Also" sections
- Issue tracking directories
**Full doc:** `feature-0a6c3431-docs-structure-indexes.md` [112 lines]

## Environment & Setup Features

### Environment Setup Scripts (feature-f4d9b5e1)
**Summary:** Environment configuration and setup scripts
- Interactive .env setup wizard
- Validation scripts
- Cross-platform bash compatibility
- Onboarding workflows
**Full doc:** `feature-f4d9b5e1-env-setup-scripts.md` [127 lines]

### Environment Setup Documentation (feature-e6104340)
**Summary:** Comprehensive configuration documentation
- Environment variables reference tables
- Cloud services configuration
- CI/CD setup guides
- Best practices for security and performance
**Full doc:** `feature-e6104340-env-setup-documentation.md` [143 lines]

## ADW & Automation Features

### Test Worktree Path Fix (feature-26e44bd2)
**Summary:** ADW worktree path functionality and testing
- Worktree file creation tests
- Path reporting in planning agent
- MCP configuration for worktrees
**Full doc:** `feature-26e44bd2-test-worktree-path-fix.md` [81 lines]

### Integration Cleanup (feature-23bd15ec)
**Summary:** Full-stack startup scripts and orchestration
- scripts/start_full.sh
- Health checking and process management
- Graceful shutdown handlers
- Multi-service coordination
**Full doc:** `feature-23bd15ec-integration-cleanup.md` [119 lines]

### ZTE Hopper Queue System (feature-09115cf1)
**Summary:** Zero Touch Execution queue processing
- Batch processing of GitHub issues
- scripts/zte_hopper.sh and scripts/gi
- Automated issue creation and validation
- FIFO queue ordering
- ADW completion detection
**Full doc:** `feature-09115cf1-zte-hopper-queue-system.md` [167 lines]

## Routes & Validation Features

### Routes Visualization (feature-04a76d25)
**Summary:** API routes visualization and route discovery
- AST-based route analysis (routes_analyzer.py)
- Routes tab in web UI
- Route filtering and search
- Codebase metadata extraction
**Full doc:** `feature-04a76d25-validation-optimization-routes-viz.md` [152 lines]

## Templates & Integration Features

### Project Templates Documentation (feature-0f04f66d)
**Summary:** Project template system documentation
- React-Vite, Next.js, Vanilla JS templates
- Scaffolding scripts (setup_new_project.sh)
- Existing codebase integration (integrate_existing.sh)
- Template testing infrastructure
**Full doc:** `feature-0f04f66d-project-templates-docs.md` [178 lines]

---

## Quick Reference

**Total Features:** 23 documented features
**Total Lines:** ~2,800 lines across all feature docs

### By Category
- **UI/Styling:** 5 features
- **Backend/Model:** 1 feature
- **NL Processing:** 3 features
- **CLI:** 1 feature
- **MCP/Testing:** 3 features
- **Project Structure:** 3 features
- **Environment/Setup:** 2 features
- **ADW/Automation:** 3 features
- **Routes/Validation:** 1 feature
- **Templates:** 1 feature

### Loading Strategy
- For feature overview: Read this file (~500 tokens)
- For specific feature details: Load individual feature file (200-500 tokens)
- For related features: Check category sections above
