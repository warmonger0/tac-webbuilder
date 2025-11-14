# Documentation Quick Start

## Documentation Structure

### Technical Docs (`docs/` - 13 files)
- `architecture.md` - System design (464 lines)
- `api.md` - API reference (486 lines)
- `web-ui.md` - Frontend guide (449 lines)
- `cli.md` - CLI documentation
- `playwright-mcp.md` - E2E testing setup
- `troubleshooting.md` - Common issues
- `configuration.md` - Setup guide

### Feature Specs (`app_docs/` - 8 files)
- Feature documentation with screenshots
- Format: `feature-{id}-{slug}.md`

### Claude Commands (`.claude/commands/` - 35+ files)
- Custom slash commands
- E2E test scenarios
- Quick reference docs

## Adding Documentation

### New Feature
Create: `app_docs/feature-{8-char-id}-{slug}.md`
Include:
- Overview
- Technical implementation
- Screenshots (in `app_docs/assets/`)

### Technical Guide
Add to appropriate `docs/*.md` file or create new

### API Endpoint
Update: `docs/api.md` AND `.claude/commands/references/api_endpoints.md`

### ADW Workflow
Update: `adws/README.md` AND `.claude/commands/references/adw_workflows.md`

## Documentation Standards

### Format
- Markdown with code blocks
- Mermaid diagrams for architecture
- Screenshots for UI features
- Working code examples

### Keep Updated
When changing code, update:
1. Relevant `docs/*.md` file
2. Quick reference in `.claude/commands/references/`
3. Feature doc in `app_docs/` if applicable
4. `conditional_docs.md` if new doc added

## Quick Reference System

### Three Tiers
1. **Quick Start** (`.claude/commands/quick_start/`) - 200-400 tokens
2. **Quick Reference** (`.claude/commands/references/`) - 900-1,700 tokens
3. **Full Docs** (`docs/`, `adws/README.md`) - 2,000-4,000 tokens

### When Adding Docs
- Add to `conditional_docs.md` with conditions
- Create quick reference version if doc >2,000 tokens
- Add token estimate [e.g., "new-doc.md [2400 tokens]"]

## Common Tasks

### Find Existing Docs
Use: `.claude/commands/conditional_docs.md` (320 lines, categorized)

### Understand Architecture
- Quick: `.claude/commands/references/architecture_overview.md` (900 tokens)
- Full: `docs/architecture.md` (2,300 tokens) or `ARCHITECTURE.md` (1,900 tokens)

### API Reference
- Quick: `.claude/commands/references/api_endpoints.md` (1,700 tokens)
- Full: `docs/api.md` (2,400 tokens)

## Token Budget Awareness
Keep docs concise. Target:
- Quick start: 200-400 tokens
- Quick reference: <2,000 tokens
- Full docs: <5,000 tokens

If doc exceeds target, split into quick + detailed versions.
