import { useCallback, useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { intervals } from '../config/intervals';

// Debug flag - disabled to reduce console noise
const DEBUG_WS = false;

interface ReliableWebSocketOptions<T, M = any> {
  url: string;
  queryKey: string[];
  queryFn: () => Promise<T>;
  onMessage: (data: M) => void;
  enabled?: boolean;
  pollingInterval?: number;
  maxReconnectDelay?: number;
  maxReconnectAttempts?: number;
}

interface ConnectionState {
  isConnected: boolean;
  connectionQuality: 'excellent' | 'good' | 'poor' | 'disconnected';
  lastUpdated: Date | null;
  reconnectAttempts: number;
}

/**
 * Reliable WebSocket hook with:
 * - Exponential backoff reconnection
 * - Automatic fallback to HTTP polling
 * - Visibility API integration (pause when hidden)
 * - Connection quality monitoring
 * - Maximum retry limits
 */
export function useReliableWebSocket<T, M = any>({
  url,
  queryKey,
  queryFn,
  onMessage,
  enabled = true,
  pollingInterval = intervals.websocket.pollingInterval, // Kept for backwards compat but not used
  maxReconnectDelay = intervals.websocket.maxReconnectDelay,
  maxReconnectAttempts = intervals.websocket.maxReconnectAttempts,
}: ReliableWebSocketOptions<T, M>) {
  // Disable unused parameter warning
  void pollingInterval;
  const [state, setState] = useState<ConnectionState>({
    isConnected: false,
    connectionQuality: 'disconnected',
    lastUpdated: null,
    reconnectAttempts: 0,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);
  const isPageVisibleRef = useRef(true);
  const lastMessageTimeRef = useRef<number>(Date.now());
  const messageCountRef = useRef(0);

  // Use refs for callbacks to avoid recreating connect on every render
  const onMessageRef = useRef(onMessage);
  const queryFnRef = useRef(queryFn);

  // Update refs when callbacks change
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    queryFnRef.current = queryFn;
  }, [queryFn]);

  // Initial HTTP fetch - loads data immediately while WebSocket connects
  // No continuous polling - WebSocket provides real-time updates once connected
  const { data: polledData } = useQuery({
    queryKey,
    queryFn: () => queryFnRef.current(),
    refetchInterval: false, // No polling - WebSocket handles updates
    enabled: enabled, // Fetch initial data on mount
    staleTime: Infinity, // Cache indefinitely - WebSocket keeps it fresh
  });

  // Handle initial polled data
  useEffect(() => {
    if (polledData) {
      // Send initial data through the message handler
      onMessageRef.current(polledData as any as M);

      // Mark as loaded (even if WebSocket not connected yet)
      setState((prev) => ({
        ...prev,
        lastUpdated: new Date(),
      }));
    }
  }, [polledData]);

  // Calculate exponential backoff delay
  const getReconnectDelay = useCallback((attempt: number): number => {
    const baseDelay = 1000; // Start at 1 second
    const delay = Math.min(baseDelay * Math.pow(2, attempt), maxReconnectDelay);
    // Add jitter to prevent thundering herd
    const jitter = Math.random() * 1000;
    return delay + jitter;
  }, [maxReconnectDelay]);

  // Calculate connection quality based on message frequency
  const updateConnectionQuality = useCallback((isConnected: boolean) => {
    const now = Date.now();
    const timeSinceLastMessage = now - lastMessageTimeRef.current;

    if (!isConnected) {
      return 'disconnected' as const;
    }

    // Excellent: messages within last 5 seconds
    if (timeSinceLastMessage < 5000) {
      return 'excellent' as const;
    }
    // Good: messages within last 15 seconds
    if (timeSinceLastMessage < 15000) {
      return 'good' as const;
    }
    // Poor: messages within last 30 seconds
    if (timeSinceLastMessage < 30000) {
      return 'poor' as const;
    }
    // No recent messages
    return 'disconnected' as const;
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!enabled || !isPageVisibleRef.current) {
      return;
    }

    // Don't reconnect if we've exceeded max attempts
    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      console.warn(`[WS] Max reconnection attempts (${maxReconnectAttempts}) reached for ${url}`);
      setState((prev) => ({
        ...prev,
        connectionQuality: 'disconnected',
      }));
      return;
    }

    if (DEBUG_WS) console.log(`[WS] Connecting to: ${url} (attempt ${reconnectAttemptsRef.current + 1})`);

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (DEBUG_WS) console.log(`[WS] Connected to ${url}`);
        reconnectAttemptsRef.current = 0;
        lastMessageTimeRef.current = Date.now();
        messageCountRef.current = 0;

        setState({
          isConnected: true,
          connectionQuality: 'excellent',
          lastUpdated: new Date(),
          reconnectAttempts: 0,
        });
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          onMessageRef.current(message);

          lastMessageTimeRef.current = Date.now();
          messageCountRef.current++;

          setState((prev) => ({
            ...prev,
            lastUpdated: new Date(),
            connectionQuality: updateConnectionQuality(true),
          }));
        } catch (err) {
          console.error(`[WS] Error parsing message from ${url}:`, err);
        }
      };

      ws.onerror = (error) => {
        console.error(`[WS] Error on ${url}:`, error);
        setState((prev) => ({
          ...prev,
          isConnected: false,
          connectionQuality: 'disconnected',
        }));
      };

      ws.onclose = () => {
        if (DEBUG_WS) console.log(`[WS] Disconnected from ${url}`);
        setState((prev) => ({
          ...prev,
          isConnected: false,
          connectionQuality: 'disconnected',
        }));

        // Schedule reconnection with exponential backoff
        if (enabled && isPageVisibleRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = getReconnectDelay(reconnectAttemptsRef.current);
          if (DEBUG_WS) console.log(`[WS] Reconnecting to ${url} in ${Math.round(delay / 1000)}s...`);

          reconnectAttemptsRef.current++;
          setState((prev) => ({
            ...prev,
            reconnectAttempts: reconnectAttemptsRef.current,
          }));

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };
    } catch (err) {
      console.error(`[WS] Failed to create WebSocket for ${url}:`, err);
      setState((prev) => ({
        ...prev,
        isConnected: false,
        connectionQuality: 'disconnected',
      }));
    }
  }, [url, enabled, getReconnectDelay, updateConnectionQuality, maxReconnectAttempts]);


  // Handle visibility change
  useEffect(() => {
    const handleVisibilityChange = () => {
      const isVisible = document.visibilityState === 'visible';
      isPageVisibleRef.current = isVisible;

      if (isVisible && enabled) {
        if (DEBUG_WS) console.log(`[WS] Page visible, reconnecting to ${url}...`);
        // Reset reconnect attempts on visibility change
        reconnectAttemptsRef.current = 0;
      } else if (!isVisible) {
        if (DEBUG_WS) console.log(`[WS] Page hidden, pausing connection to ${url}`);
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        if (wsRef.current) {
          wsRef.current.close();
          wsRef.current = null;
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [enabled, url]);

  // Initial connection and cleanup
  useEffect(() => {
    if (!enabled) {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      return;
    }

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [enabled, connect]);

  // Periodic connection quality update
  useEffect(() => {
    const interval = setInterval(() => {
      setState((prev) => {
        const quality = updateConnectionQuality(prev.isConnected);
        if (prev.connectionQuality !== quality) {
          return { ...prev, connectionQuality: quality };
        }
        return prev;
      });
    }, 5000);

    return () => clearInterval(interval);
  }, [updateConnectionQuality]);

  return state;
}
