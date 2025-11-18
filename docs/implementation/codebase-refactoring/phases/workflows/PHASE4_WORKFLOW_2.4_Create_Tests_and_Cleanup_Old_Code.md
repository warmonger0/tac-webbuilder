### Workflow 2.4: Create Tests and Cleanup Old Code
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** Workflows 2.2, 2.3

**Tasks:**
1. Create comprehensive integration tests
2. Test all three WebSocket hooks together
3. Test reconnection scenarios
4. Test fallback polling
5. Delete old duplicated code
6. Update documentation

**Integration Test:**

```typescript
// app/client/src/hooks/__tests__/webSocketIntegration.test.ts
import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  useWorkflowsWebSocket,
  useRoutesWebSocket,
  useWorkflowHistoryWebSocket
} from '../useWebSocket';

describe('WebSocket Hooks Integration', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('all hooks can connect simultaneously', async () => {
    const workflows = renderHook(() => useWorkflowsWebSocket(), { wrapper });
    const routes = renderHook(() => useRoutesWebSocket(), { wrapper });
    const history = renderHook(() => useWorkflowHistoryWebSocket(), { wrapper });

    await waitFor(() => {
      expect(workflows.result.current.isConnected).toBe(true);
      expect(routes.result.current.isConnected).toBe(true);
      expect(history.result.current.isConnected).toBe(true);
    });
  });

  it('all hooks fall back to polling on connection failure', async () => {
    // Mock WebSocket to fail
    global.WebSocket = class {
      constructor() {
        setTimeout(() => {
          if (this.onerror) this.onerror(new Event('error'));
          if (this.onclose) this.onclose();
        }, 0);
      }
    } as any;

    const workflows = renderHook(() => useWorkflowsWebSocket(), { wrapper });

    await waitFor(() => {
      expect(workflows.result.current.data).not.toBeNull();
      expect(workflows.result.current.isConnected).toBe(false);
    }, { timeout: 3000 });
  });
});
```

**Documentation Update:**

```markdown
// app/client/src/hooks/README.md

# WebSocket Hooks
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
