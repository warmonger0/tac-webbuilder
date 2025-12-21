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
- **Panel 5: PlansPanel** - Roadmap tracking (database-driven), AI plan generation (Session 21) - COMPLETE
- **Panel 6-9:** Placeholder panels (future features)
- **Panel 10: LogPanel** - Work log and session summaries - COMPLETE

## State Management
- **React Hooks** - Local component state (useState, useEffect)
- **TanStack Query** - Server state, caching, mutations
- **WebSocket** - Real-time updates via 5 specialized hooks (see below)

## WebSocket Real-Time Updates (Sessions 15-16)
**5 specialized hooks in `src/hooks/useWebSocket.ts`:**
- `useWorkflowsWebSocket()` - Real-time workflow status
- `useRoutesWebSocket()` - Real-time route updates
- `useWorkflowHistoryWebSocket()` - Real-time history updates
- `useADWMonitorWebSocket()` - Real-time ADW monitoring
- `useQueueWebSocket()` - Real-time queue updates (NEW in Session 16)

**Base hook:** `useReliableWebSocket()` handles reconnection + HTTP polling fallback

**Components using WebSocket:**
- ✅ CurrentWorkflowCard - Replaced 3s polling
- ✅ AdwMonitorCard - Replaced 2-10s polling
- ✅ ZteHopperQueueCard - Replaced 10s polling
- ✅ RoutesView - Already using WebSocket
- ✅ WorkflowHistoryView - Already using WebSocket

**Performance:** <2s latency vs 3-10s polling, reduced network traffic

## Session 19: Standard Patterns (NEW)

### Data Fetching Patterns
**Use useQuery for one-time fetches:**
```typescript
import { useQuery } from '@tanstack/react-query';
import { LoadingState } from './common/LoadingState';
import { ErrorBanner } from './common/ErrorBanner';

const { data, isLoading, error } = useQuery({
  queryKey: ['resource', id],
  queryFn: () => fetchResource(id),
});

if (isLoading) return <LoadingState message="Loading..." />;
if (error) return <ErrorBanner error={error} />;
```

**Use WebSocket for real-time data:**
```typescript
import { useWorkflowHistoryWebSocket } from '../hooks/useWebSocket';

const { workflowHistory, isConnected } = useWorkflowHistoryWebSocket();

if (!isConnected) return <LoadingState message="Connecting..." />;
```

**NO POLLING:** Never use `refetchInterval` except conditional (self-terminating)

### Reusable UI Components
**Location:** `app/client/src/components/common/`

```typescript
import { LoadingState } from './common/LoadingState';
import { ErrorBanner } from './common/ErrorBanner';
import { ConfirmationDialog } from './common/ConfirmationDialog';

// Loading indicator
<LoadingState message="Loading data..." />

// Error display
<ErrorBanner error={error} onDismiss={() => setError(null)} />

// Confirmation dialog
<ConfirmationDialog
  isOpen={showConfirm}
  onClose={() => setShowConfirm(false)}
  onConfirm={handleDelete}
  title="Delete Entry?"
  message="This action cannot be undone."
  confirmVariant="danger"
/>
```

### Error Handling Pattern
```typescript
import { formatErrorMessage, logError } from '../utils/errorHandler';

const mutation = useMutation({
  mutationFn: apiCall,

  onError: (err: unknown) => {
    logError('[ComponentName]', 'Operation', err);
    setError(formatErrorMessage(err));
  },

  onSuccess: () => setError(null),
});
```

**Documentation:**
- Migration Guide: `docs/guides/migration-guide-session-19.md`
- Frontend Patterns: `docs/patterns/frontend-patterns.md`
- WebSocket API: `docs/api/websocket-api.md`
- Error Handler: `docs/api/error-handler.md`
- Components API: `docs/api/reusable-components.md`

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
