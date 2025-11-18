### Workflow 2.3: Migrate useRoutesWebSocket and useWorkflowHistoryWebSocket
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** Workflow 2.1

**Output Files:**
- `app/client/src/hooks/useRoutesWebSocket.ts` (new, refactored)
- `app/client/src/hooks/useWorkflowHistoryWebSocket.ts` (new, refactored)

**Implementation - useRoutesWebSocket.ts:**

```typescript
// app/client/src/hooks/useRoutesWebSocket.ts
import { useGenericWebSocket } from './useGenericWebSocket';
import type { Route } from '../types';

/**
 * WebSocket hook for real-time routes updates
 *
 * @returns Routes data and connection state
 */
export function useRoutesWebSocket() {
  return useGenericWebSocket<Route[]>({
    endpoint: `ws://${window.location.host}/ws/routes`,
    messageType: 'routes_update',
    queryKey: ['routes'],
    queryFn: async () => {
      const response = await fetch('/api/routes');
      if (!response.ok) {
        throw new Error('Failed to fetch routes');
      }
      const data = await response.json();
      return data.routes || [];
    },
    dataExtractor: (message) => message.data,
  });
}
```

**Implementation - useWorkflowHistoryWebSocket.ts:**

```typescript
// app/client/src/hooks/useWorkflowHistoryWebSocket.ts
import { useGenericWebSocket } from './useGenericWebSocket';
import type { WorkflowHistoryResponse } from '../types';

/**
 * WebSocket hook for real-time workflow history updates
 *
 * @returns Workflow history data and connection state
 */
export function useWorkflowHistoryWebSocket() {
  return useGenericWebSocket<WorkflowHistoryResponse>({
    endpoint: `ws://${window.location.host}/ws/workflow-history`,
    messageType: 'workflow_history_update',
    queryKey: ['workflowHistory'],
    queryFn: async () => {
      const response = await fetch('/api/workflow-history?limit=50');
      if (!response.ok) {
        throw new Error('Failed to fetch workflow history');
      }
      return await response.json();
    },
    dataExtractor: (message) => message.data,
  });
}
```

**Update useWebSocket.ts Index:**

```typescript
// app/client/src/hooks/useWebSocket.ts
/**
 * WebSocket Hooks
 *
 * Consolidated exports for all WebSocket hooks.
 * All hooks use the generic useGenericWebSocket implementation.
 */

export { useWorkflowsWebSocket } from './useWorkflowsWebSocket';
export { useRoutesWebSocket } from './useRoutesWebSocket';
export { useWorkflowHistoryWebSocket } from './useWorkflowHistoryWebSocket';
export { useGenericWebSocket } from './useGenericWebSocket';

// Re-export types
export type { WebSocketConfig } from './useGenericWebSocket';
```

**Acceptance Criteria:**
- [ ] useRoutesWebSocket refactored
- [ ] useWorkflowHistoryWebSocket refactored
- [ ] Total code reduced from 275 lines to ~80 lines
- [ ] All tests pass
- [ ] Real-time updates work correctly

**Verification Commands:**
```bash
cd app/client
npm run test -- useWebSocket
npm run typecheck
npm run dev
# Manual: Verify all real-time updates work
```

**Status:** Not Started

---
