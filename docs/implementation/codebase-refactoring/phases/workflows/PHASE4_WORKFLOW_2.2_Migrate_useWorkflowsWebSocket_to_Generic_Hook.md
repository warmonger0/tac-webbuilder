### Workflow 2.2: Migrate useWorkflowsWebSocket to Generic Hook
**Estimated Time:** 1 hour
**Complexity:** Low
**Dependencies:** Workflow 2.1

**Input Files:**
- `app/client/src/hooks/useWebSocket.ts` (useWorkflowsWebSocket function)
- `app/client/src/hooks/useGenericWebSocket.ts`

**Output Files:**
- `app/client/src/hooks/useWorkflowsWebSocket.ts` (new, refactored)

**Implementation:**

```typescript
// app/client/src/hooks/useWorkflowsWebSocket.ts
import { useGenericWebSocket } from './useGenericWebSocket';
import type { Workflow } from '../types';

/**
 * WebSocket hook for real-time workflow updates
 *
 * Connects to /ws/workflows endpoint and receives workflow list updates.
 * Falls back to REST API polling if WebSocket connection fails.
 *
 * @returns Workflows data and connection state
 */
export function useWorkflowsWebSocket() {
  return useGenericWebSocket<Workflow[]>({
    endpoint: `ws://${window.location.host}/ws/workflows`,
    messageType: 'workflows_update',
    queryKey: ['workflows'],
    queryFn: async () => {
      const response = await fetch('/api/workflows');
      if (!response.ok) {
        throw new Error('Failed to fetch workflows');
      }
      const data = await response.json();
      return data.workflows || [];
    },
    dataExtractor: (message) => message.data,
    reconnection: {
      maxRetries: 5,
      initialDelay: 1000,
      maxDelay: 30000
    },
    polling: {
      interval: 5000,
      enabled: true
    }
  });
}
```

**Test File:**

```typescript
// app/client/src/hooks/__tests__/useWorkflowsWebSocket.test.ts
import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useWorkflowsWebSocket } from '../useWorkflowsWebSocket';

describe('useWorkflowsWebSocket', () => {
  it('connects to workflows WebSocket endpoint', async () => {
    const queryClient = new QueryClient();
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useWorkflowsWebSocket(), { wrapper });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });
  });

  it('fetches workflows via REST API as fallback', async () => {
    const mockWorkflows = [
      { id: '1', name: 'Workflow 1', status: 'running' },
      { id: '2', name: 'Workflow 2', status: 'completed' }
    ];

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ workflows: mockWorkflows })
    });

    const queryClient = new QueryClient();
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useWorkflowsWebSocket(), { wrapper });

    await waitFor(() => {
      expect(result.current.data).toEqual(mockWorkflows);
    });
  });
});
```

**Acceptance Criteria:**
- [ ] useWorkflowsWebSocket refactored to use generic hook
- [ ] Reduced from ~81 lines to ~30 lines
- [ ] Tests pass
- [ ] Functionality unchanged
- [ ] Type safety maintained

**Verification Commands:**
```bash
cd app/client
npm run test -- useWorkflowsWebSocket.test.ts
npm run typecheck
npm run dev
# Manual: Verify workflows list updates in real-time
```

**Status:** Not Started
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
