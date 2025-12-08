# Frontend Quick Start

## Tech Stack
React 18.3 + Vite + TypeScript + Tailwind CSS + TanStack Query
**Note:** Zustand listed in package.json but unused - all state via React hooks

## Key Directories
- `app/client/src/components/` - React components (58+ files)
- `app/client/src/hooks/` - Custom hooks (5 specialized WebSocket hooks)
- `app/client/src/api/` - Domain-driven API clients (7 clients)
- `app/client/src/style.css` - Tailwind configuration

## 10-Panel System
- **Panel 1: RequestForm** - NL input and workflow triggering
- **Panel 2: WorkflowDashboard** - Real-time ADW monitoring (Catalog view)
- **Panel 3: HistoryView** - Workflow execution history
- **Panel 4: RoutesView** - API route visualization
- **Panel 5: PlansPanel** - Roadmap tracking (database-driven) - COMPLETE (Session 8B)
- **Panel 6-9:** Placeholder panels (future features)
- **Panel 10: LogPanel** - Work log and session summaries - COMPLETE

## State Management
- **React Hooks** - Local component state (useState, useEffect)
- **TanStack Query** - Server state, caching, mutations
- **WebSocket** - Real-time updates via 5 specialized hooks

## Common Tasks

### Styling Changes
Read directly: `app/client/src/style.css`

### Component Work
- Quick reference: `.claude/commands/references/architecture_overview.md` (frontend section)
- Full details: `docs/web-ui.md` (449 lines)

### API Integration
- Quick reference: `.claude/commands/references/api_endpoints.md`
- Full details: `docs/api.md`

### Build Issues
Check: `app/client/vite.config.ts`, `app/client/tsconfig.json`

## Quick Commands
```bash
cd app/client
bun install          # Install dependencies
bun run dev          # Start dev server (port 5173 or FRONTEND_PORT)
bun run build        # Build for production
```

## When to Load Full Docs
- **Component architecture:** `docs/web-ui.md` (2,200 tokens)
- **Complete architecture:** `docs/architecture.md` (2,300 tokens)
- **Panel 5 / Plans Panel:** `.claude/commands/references/planned_features.md` (600 tokens)
- **Panel 10 / Work Logs:** `.claude/commands/references/observability.md` (900 tokens)
- **Feature-specific:** Use `conditional_docs.md` for feature mappings
