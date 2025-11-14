# Frontend Quick Start

## Tech Stack
React 18.3 + Vite + TypeScript + Tailwind CSS + TanStack Query + Zustand

## Key Directories
- `app/client/src/components/` - React components (9 files)
- `app/client/src/hooks/` - Custom hooks (useWebSocket.ts)
- `app/client/src/api/client.ts` - API client functions
- `app/client/src/style.css` - Tailwind configuration

## Main Components
- **App.tsx** - Root with tab navigation
- **RequestForm.tsx** - NL input and workflow triggering
- **WorkflowDashboard.tsx** - Real-time ADW monitoring
- **HistoryView.tsx** - Request history browser
- **RoutesView.tsx** - API route visualization

## State Management
- **Zustand** - Global state
- **TanStack Query** - Server state, caching
- **WebSocket** - Real-time updates via useWebSocket hook

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
- **Feature-specific:** Use `conditional_docs.md` for feature mappings
