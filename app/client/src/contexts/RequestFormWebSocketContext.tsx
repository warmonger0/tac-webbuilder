import { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getQueueData, type PhaseQueueItem } from '../api/queueClient';
import { getAdwMonitor, type AdwMonitorSummary, type AdwWorkflowStatus } from '../api/client';
import { apiConfig } from '../config/api';
import { intervals } from '../config/intervals';

// Debug flag
const DEBUG_WS = import.meta.env.DEV;

interface QueueData {
  phases: PhaseQueueItem[];
  paused: boolean;
}

interface ADWMonitorData {
  workflows: AdwWorkflowStatus[];
  summary: AdwMonitorSummary;
  lastUpdated: string;
}

interface SystemStatusData {
  // System status type will be defined by the actual API response
  [key: string]: any;
}

interface ConnectionState {
  isConnected: boolean;
  connectionQuality: 'excellent' | 'good' | 'poor' | 'disconnected';
  lastUpdated: Date | null;
  reconnectAttempts: number;
}

interface RequestFormWebSocketContextValue {
  // Queue data
  queueData: QueueData;
  queueConnectionState: ConnectionState;

  // ADW Monitor data
  adwMonitorData: ADWMonitorData;
  adwConnectionState: ConnectionState;

  // System Status data
  systemStatusData: SystemStatusData | null;
  systemConnectionState: ConnectionState;
}

const RequestFormWebSocketContext = createContext<RequestFormWebSocketContextValue | null>(null);

export function useRequestFormWebSocket() {
  const context = useContext(RequestFormWebSocketContext);
  if (!context) {
    throw new Error('useRequestFormWebSocket must be used within RequestFormWebSocketProvider');
  }
  return context;
}

interface RequestFormWebSocketProviderProps {
  children: ReactNode;
}

export function RequestFormWebSocketProvider({ children }: RequestFormWebSocketProviderProps) {
  // Queue state
  const [queueData, setQueueData] = useState<QueueData>({ phases: [], paused: false });
  const [queueConnectionState, setQueueConnectionState] = useState<ConnectionState>({
    isConnected: false,
    connectionQuality: 'disconnected',
    lastUpdated: null,
    reconnectAttempts: 0,
  });

  // ADW Monitor state
  const [adwMonitorData, setAdwMonitorData] = useState<ADWMonitorData>({
    workflows: [],
    summary: { total: 0, running: 0, completed: 0, failed: 0, paused: 0 },
    lastUpdated: '',
  });
  const [adwConnectionState, setAdwConnectionState] = useState<ConnectionState>({
    isConnected: false,
    connectionQuality: 'disconnected',
    lastUpdated: null,
    reconnectAttempts: 0,
  });

  // System Status state
  const [systemStatusData, setSystemStatusData] = useState<SystemStatusData | null>(null);
  const [systemConnectionState, setSystemConnectionState] = useState<ConnectionState>({
    isConnected: false,
    connectionQuality: 'disconnected',
    lastUpdated: null,
    reconnectAttempts: 0,
  });

  // WebSocket refs
  const queueWsRef = useRef<WebSocket | null>(null);
  const adwWsRef = useRef<WebSocket | null>(null);
  const systemWsRef = useRef<WebSocket | null>(null);

  const reconnectTimeoutRefs = useRef<{
    queue?: NodeJS.Timeout;
    adw?: NodeJS.Timeout;
    system?: NodeJS.Timeout;
  }>({});

  const reconnectAttemptsRefs = useRef({
    queue: 0,
    adw: 0,
    system: 0,
  });

  // HTTP fallback queries (enabled for fast initial load like Panel 5)
  const { data: queuePolledData } = useQuery({
    queryKey: ['queue'],
    queryFn: getQueueData,
    refetchInterval: false,
    enabled: true, // Enable initial HTTP fetch for fast page load
  });

  const { data: adwPolledData } = useQuery({
    queryKey: ['adw-monitor'],
    queryFn: getAdwMonitor,
    refetchInterval: false,
    enabled: true, // Enable initial HTTP fetch for fast page load
  });

  const { data: systemPolledData } = useQuery({
    queryKey: ['system-status'],
    queryFn: async () => {
      const { getSystemStatus } = await import('../api/client');
      return getSystemStatus();
    },
    refetchInterval: false,
    enabled: true, // Enable initial HTTP fetch for fast page load
  });

  // Update state when polled data arrives (use HTTP data immediately for fast initial load)
  useEffect(() => {
    if (queuePolledData) {
      setQueueData(queuePolledData);
      // Only mark as 'poor' quality if WebSocket is explicitly disconnected
      if (!queueConnectionState.isConnected) {
        setQueueConnectionState(prev => ({
          ...prev,
          lastUpdated: new Date(),
          connectionQuality: 'poor',
        }));
      }
    }
  }, [queuePolledData, queueConnectionState.isConnected]);

  useEffect(() => {
    if (adwPolledData) {
      setAdwMonitorData({
        ...adwPolledData,
        lastUpdated: adwPolledData.last_updated || new Date().toISOString(),
      });
      // Only mark as 'poor' quality if WebSocket is explicitly disconnected
      if (!adwConnectionState.isConnected) {
        setAdwConnectionState(prev => ({
          ...prev,
          lastUpdated: new Date(),
          connectionQuality: 'poor',
        }));
      }
    }
  }, [adwPolledData, adwConnectionState.isConnected]);

  useEffect(() => {
    if (systemPolledData) {
      setSystemStatusData(systemPolledData);
      // Only mark as 'poor' quality if WebSocket is explicitly disconnected
      if (!systemConnectionState.isConnected) {
        setSystemConnectionState(prev => ({
          ...prev,
          lastUpdated: new Date(),
          connectionQuality: 'poor',
        }));
      }
    }
  }, [systemPolledData, systemConnectionState.isConnected]);

  // Exponential backoff calculation
  const getReconnectDelay = (attempt: number): number => {
    const baseDelay = 1000;
    const delay = Math.min(baseDelay * Math.pow(2, attempt), intervals.websocket.maxReconnectDelay);
    const jitter = Math.random() * 1000;
    return delay + jitter;
  };

  // Connect to Queue WebSocket
  const connectQueueWs = () => {
    if (reconnectAttemptsRefs.current.queue >= intervals.websocket.maxReconnectAttempts) {
      console.warn('[WS] Max reconnection attempts reached for Queue');
      return;
    }

    const url = apiConfig.websocket.queue();
    const startTime = performance.now();
    if (DEBUG_WS) console.log(`[WS] Connecting to Queue: ${url}`);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        const connectTime = performance.now() - startTime;
        if (DEBUG_WS) console.log(`[WS] Queue connected in ${connectTime.toFixed(2)}ms`);
        reconnectAttemptsRefs.current.queue = 0;
        setQueueConnectionState({
          isConnected: true,
          connectionQuality: 'excellent',
          lastUpdated: new Date(),
          reconnectAttempts: 0,
        });
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'queue_update') {
            setQueueData(message.data);
            setQueueConnectionState(prev => ({
              ...prev,
              lastUpdated: new Date(),
              connectionQuality: 'excellent',
            }));
            if (DEBUG_WS) console.log('[WS] Queue update:', message.data.phases.length, 'phases');
          }
        } catch (err) {
          console.error('[WS] Queue message parse error:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] Queue error:', error);
      };

      ws.onclose = () => {
        if (DEBUG_WS) console.log('[WS] Queue disconnected');
        setQueueConnectionState(prev => ({
          ...prev,
          isConnected: false,
          connectionQuality: 'disconnected',
        }));

        // Attempt reconnection
        reconnectAttemptsRefs.current.queue++;
        const delay = getReconnectDelay(reconnectAttemptsRefs.current.queue);
        reconnectTimeoutRefs.current.queue = setTimeout(connectQueueWs, delay);
      };

      queueWsRef.current = ws;
    } catch (err) {
      console.error('[WS] Queue connection failed:', err);
    }
  };

  // Connect to ADW Monitor WebSocket
  const connectAdwWs = () => {
    if (reconnectAttemptsRefs.current.adw >= intervals.websocket.maxReconnectAttempts) {
      console.warn('[WS] Max reconnection attempts reached for ADW Monitor');
      return;
    }

    const url = apiConfig.websocket.adwMonitor();
    const startTime = performance.now();
    if (DEBUG_WS) console.log(`[WS] Connecting to ADW Monitor: ${url}`);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        const connectTime = performance.now() - startTime;
        if (DEBUG_WS) console.log(`[WS] ADW Monitor connected in ${connectTime.toFixed(2)}ms`);
        reconnectAttemptsRefs.current.adw = 0;
        setAdwConnectionState({
          isConnected: true,
          connectionQuality: 'excellent',
          lastUpdated: new Date(),
          reconnectAttempts: 0,
        });
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'adw_monitor_update') {
            setAdwMonitorData(message.data);
            setAdwConnectionState(prev => ({
              ...prev,
              lastUpdated: new Date(),
              connectionQuality: 'excellent',
            }));
            if (DEBUG_WS) console.log('[WS] ADW Monitor update:', message.data.workflows.length, 'workflows');
          }
        } catch (err) {
          console.error('[WS] ADW Monitor message parse error:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] ADW Monitor error:', error);
      };

      ws.onclose = () => {
        if (DEBUG_WS) console.log('[WS] ADW Monitor disconnected');
        setAdwConnectionState(prev => ({
          ...prev,
          isConnected: false,
          connectionQuality: 'disconnected',
        }));

        // Attempt reconnection
        reconnectAttemptsRefs.current.adw++;
        const delay = getReconnectDelay(reconnectAttemptsRefs.current.adw);
        reconnectTimeoutRefs.current.adw = setTimeout(connectAdwWs, delay);
      };

      adwWsRef.current = ws;
    } catch (err) {
      console.error('[WS] ADW Monitor connection failed:', err);
    }
  };

  // Connect to System Status WebSocket
  const connectSystemWs = () => {
    if (reconnectAttemptsRefs.current.system >= intervals.websocket.maxReconnectAttempts) {
      console.warn('[WS] Max reconnection attempts reached for System Status');
      return;
    }

    const url = apiConfig.websocket.systemStatus();
    const startTime = performance.now();
    if (DEBUG_WS) console.log(`[WS] Connecting to System Status: ${url}`);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        const connectTime = performance.now() - startTime;
        if (DEBUG_WS) console.log(`[WS] System Status connected in ${connectTime.toFixed(2)}ms`);
        reconnectAttemptsRefs.current.system = 0;
        setSystemConnectionState({
          isConnected: true,
          connectionQuality: 'excellent',
          lastUpdated: new Date(),
          reconnectAttempts: 0,
        });
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'system_status_update') {
            setSystemStatusData(message.data);
            setSystemConnectionState(prev => ({
              ...prev,
              lastUpdated: new Date(),
              connectionQuality: 'excellent',
            }));
            if (DEBUG_WS) console.log('[WS] System Status update');
          }
        } catch (err) {
          console.error('[WS] System Status message parse error:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] System Status error:', error);
      };

      ws.onclose = () => {
        if (DEBUG_WS) console.log('[WS] System Status disconnected');
        setSystemConnectionState(prev => ({
          ...prev,
          isConnected: false,
          connectionQuality: 'disconnected',
        }));

        // Attempt reconnection
        reconnectAttemptsRefs.current.system++;
        const delay = getReconnectDelay(reconnectAttemptsRefs.current.system);
        reconnectTimeoutRefs.current.system = setTimeout(connectSystemWs, delay);
      };

      systemWsRef.current = ws;
    } catch (err) {
      console.error('[WS] System Status connection failed:', err);
    }
  };

  // Initialize connections on mount
  useEffect(() => {
    connectQueueWs();
    connectAdwWs();
    connectSystemWs();

    // Cleanup on unmount
    return () => {
      if (queueWsRef.current) queueWsRef.current.close();
      if (adwWsRef.current) adwWsRef.current.close();
      if (systemWsRef.current) systemWsRef.current.close();

      if (reconnectTimeoutRefs.current.queue) clearTimeout(reconnectTimeoutRefs.current.queue);
      if (reconnectTimeoutRefs.current.adw) clearTimeout(reconnectTimeoutRefs.current.adw);
      if (reconnectTimeoutRefs.current.system) clearTimeout(reconnectTimeoutRefs.current.system);
    };
  }, []);

  const value: RequestFormWebSocketContextValue = {
    queueData,
    queueConnectionState,
    adwMonitorData,
    adwConnectionState,
    systemStatusData,
    systemConnectionState,
  };

  return (
    <RequestFormWebSocketContext.Provider value={value}>
      {children}
    </RequestFormWebSocketContext.Provider>
  );
}
