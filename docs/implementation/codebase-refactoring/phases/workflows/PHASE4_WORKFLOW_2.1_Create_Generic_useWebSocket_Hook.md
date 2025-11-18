### Workflow 2.1: Create Generic useWebSocket Hook
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** None

**Input Files:**
- `app/client/src/hooks/useWebSocket.ts` (analyze patterns)

**Output Files:**
- `app/client/src/hooks/useGenericWebSocket.ts` (new)

**Tasks:**
1. Extract common WebSocket connection logic
2. Create generic hook with configuration interface
3. Implement reconnection with exponential backoff
4. Implement React Query fallback polling
5. Add TypeScript generics for type safety

**Implementation:**

```typescript
// app/client/src/hooks/useGenericWebSocket.ts
import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';

interface WebSocketConfig<T> {
  /** WebSocket endpoint URL */
  endpoint: string;

  /** Message type to filter for */
  messageType: string;

  /** React Query key for fallback polling */
  queryKey: string[];

  /** React Query fetch function for fallback */
  queryFn: () => Promise<T>;

  /** Extract data from WebSocket message */
  dataExtractor: (message: any) => T;

  /** Reconnection configuration */
  reconnection?: {
    maxRetries?: number;
    initialDelay?: number;
    maxDelay?: number;
  };

  /** Polling configuration for fallback */
  polling?: {
    interval?: number;
    enabled?: boolean;
  };
}

/**
 * Generic WebSocket Hook
 *
 * Provides real-time data updates via WebSocket with automatic
 * fallback to React Query polling on connection failure.
 *
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Graceful degradation to polling
 * - TypeScript generic for type safety
 * - Connection state management
 *
 * @template T - Type of data received from WebSocket
 * @param config - WebSocket configuration
 * @returns Data and connection state
 */
export function useGenericWebSocket<T>({
  endpoint,
  messageType,
  queryKey,
  queryFn,
  dataExtractor,
  reconnection = {},
  polling = {}
}: WebSocketConfig<T>) {
  const [data, setData] = useState<T | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  // Reconnection configuration with defaults
  const {
    maxRetries = 5,
    initialDelay = 1000,
    maxDelay = 30000
  } = reconnection;

  // Polling configuration with defaults
  const {
    interval = 5000,
    enabled = true
  } = polling;

  /**
   * Calculate exponential backoff delay
   */
  const getReconnectDelay = (): number => {
    const delay = initialDelay * Math.pow(2, reconnectAttemptsRef.current);
    return Math.min(delay, maxDelay);
  };

  /**
   * Connect to WebSocket
   */
  const connect = () => {
    try {
      const ws = new WebSocket(endpoint);

      ws.onopen = () => {
        console.log(`[WebSocket] Connected to ${endpoint}`);
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === messageType) {
            const extractedData = dataExtractor(message);
            setData(extractedData);
          }
        } catch (err) {
          console.error('[WebSocket] Error parsing message:', err);
          setError(err instanceof Error ? err : new Error('Failed to parse message'));
        }
      };

      ws.onerror = (event) => {
        console.error('[WebSocket] Error:', event);
        setError(new Error('WebSocket connection error'));
      };

      ws.onclose = () => {
        console.log('[WebSocket] Disconnected');
        setIsConnected(false);

        // Attempt reconnection if not exceeded max retries
        if (reconnectAttemptsRef.current < maxRetries) {
          const delay = getReconnectDelay();
          console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1}/${maxRetries})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        } else {
          console.log('[WebSocket] Max reconnection attempts reached. Falling back to polling.');
          setError(new Error('WebSocket connection failed. Using polling fallback.'));
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('[WebSocket] Connection error:', err);
      setError(err instanceof Error ? err : new Error('Failed to connect'));
    }
  };

  /**
   * Disconnect from WebSocket
   */
  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  };

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [endpoint]);

  // Fallback to React Query polling when WebSocket disconnected
  const { data: fallbackData } = useQuery({
    queryKey,
    queryFn,
    enabled: enabled && !isConnected,
    refetchInterval: isConnected ? false : interval,
    staleTime: interval,
  });

  // Use fallback data when WebSocket not connected
  useEffect(() => {
    if (fallbackData && !isConnected) {
      setData(fallbackData);
    }
  }, [fallbackData, isConnected]);

  return {
    data,
    isConnected,
    error,
    reconnect: connect,
    disconnect
  };
}
```

**Test File:**

```typescript
// app/client/src/hooks/__tests__/useGenericWebSocket.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useGenericWebSocket } from '../useGenericWebSocket';

// Mock WebSocket
class MockWebSocket {
  onopen: (() => void) | null = null;
  onmessage: ((event: any) => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  onclose: (() => void) | null = null;

  constructor(public url: string) {
    setTimeout(() => {
      if (this.onopen) this.onopen();
    }, 0);
  }

  send(data: string) {}
  close() {
    if (this.onclose) this.onclose();
  }
}

describe('useGenericWebSocket', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    global.WebSocket = MockWebSocket as any;
  });

  afterEach(() => {
    queryClient.clear();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('connects to WebSocket on mount', async () => {
    const { result } = renderHook(
      () => useGenericWebSocket({
        endpoint: 'ws://localhost:8000/test',
        messageType: 'test_update',
        queryKey: ['test'],
        queryFn: async () => [],
        dataExtractor: (msg) => msg.data
      }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });
  });

  it('receives and processes messages', async () => {
    const mockData = [{ id: 1, name: 'Test' }];

    const { result } = renderHook(
      () => useGenericWebSocket({
        endpoint: 'ws://localhost:8000/test',
        messageType: 'test_update',
        queryKey: ['test'],
        queryFn: async () => [],
        dataExtractor: (msg) => msg.data
      }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate message
    const ws = global.WebSocket as any;
    if (ws.onmessage) {
      ws.onmessage({
        data: JSON.stringify({
          type: 'test_update',
          data: mockData
        })
      });
    }

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });
  });

  it('falls back to polling when WebSocket fails', async () => {
    const mockFallbackData = [{ id: 2, name: 'Fallback' }];

    // Mock WebSocket to fail
    global.WebSocket = class extends MockWebSocket {
      constructor(url: string) {
        super(url);
        setTimeout(() => {
          if (this.onerror) this.onerror(new Event('error'));
          if (this.onclose) this.onclose();
        }, 0);
      }
    } as any;

    const { result } = renderHook(
      () => useGenericWebSocket({
        endpoint: 'ws://localhost:8000/test',
        messageType: 'test_update',
        queryKey: ['test'],
        queryFn: async () => mockFallbackData,
        dataExtractor: (msg) => msg.data,
        polling: { interval: 100 }
      }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.data).toEqual(mockFallbackData);
    }, { timeout: 3000 });
  });
});
```

**Acceptance Criteria:**
- [ ] Generic hook created with TypeScript generics
- [ ] Reconnection with exponential backoff works
- [ ] Fallback to polling when WebSocket fails
- [ ] Tests pass with >80% coverage
- [ ] No memory leaks from WebSocket connections

**Verification Commands:**
```bash
cd app/client
npm run test -- useGenericWebSocket.test.ts
npm run typecheck
```

**Status:** Not Started

---
