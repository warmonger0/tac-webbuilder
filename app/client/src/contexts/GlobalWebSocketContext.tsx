import { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getQueueData, type PhaseQueueItem } from '../api/queueClient';
import { getAdwMonitor, type AdwMonitorSummary, type AdwWorkflowStatus, getRoutes, getWorkflowHistory, listWorkflows } from '../api/client';
import { type PlannedFeature, type PlannedFeaturesStats, plannedFeaturesClient } from '../api/plannedFeaturesClient';
import type { HistoryAnalytics, Route, WorkflowExecution, WorkflowHistoryItem } from '../types';
import { apiConfig } from '../config/api';
import { intervals } from '../config/intervals';

// Debug flag - only show errors, not connection status
const DEBUG_WS = false;

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
  [key: string]: any;
}

interface WebhookStatusData {
  status: 'healthy' | 'degraded' | 'error' | 'unknown';
  uptime?: {
    hours: number;
    human: string;
  };
  stats?: {
    total_received: number;
    successful: number;
    failed: number;
    success_rate: string;
  };
  recent_failures?: Array<{
    issue: number;
    timestamp: string;
    error: string;
  }>;
  last_successful?: {
    issue: number;
    adw_id: string;
    workflow: string;
    timestamp: string;
  } | null;
}

interface ConnectionState {
  isConnected: boolean;
  connectionQuality: 'excellent' | 'good' | 'poor' | 'disconnected';
  lastUpdated: Date | null;
  reconnectAttempts: number;
}

interface GlobalWebSocketContextValue {
  // Queue data
  queueData: QueueData;
  queueConnectionState: ConnectionState;

  // ADW Monitor data
  adwMonitorData: ADWMonitorData;
  adwConnectionState: ConnectionState;

  // System Status data
  systemStatusData: SystemStatusData | null;
  systemConnectionState: ConnectionState;

  // Workflows data
  workflows: WorkflowExecution[];
  workflowsConnectionState: ConnectionState;

  // Routes data
  routes: Route[];
  routesConnectionState: ConnectionState;

  // History data
  historyWorkflows: WorkflowHistoryItem[];
  historyTotalCount: number;
  historyAnalytics: HistoryAnalytics | null;
  historyConnectionState: ConnectionState;

  // Planned Features data
  plannedFeatures: PlannedFeature[];
  plannedFeaturesStats: PlannedFeaturesStats | null;
  plannedFeaturesConnectionState: ConnectionState;

  // Webhook Status data
  webhookStatusData: WebhookStatusData | null;
  webhookStatusConnectionState: ConnectionState;
}

const GlobalWebSocketContext = createContext<GlobalWebSocketContextValue | null>(null);

export function useGlobalWebSocket() {
  const context = useContext(GlobalWebSocketContext);
  if (!context) {
    throw new Error('useGlobalWebSocket must be used within GlobalWebSocketProvider');
  }
  return context;
}

interface GlobalWebSocketProviderProps {
  children: ReactNode;
}

export function GlobalWebSocketProvider({ children }: GlobalWebSocketProviderProps) {
  // ============================================================================
  // State - Queue
  // ============================================================================
  const [queueData, setQueueData] = useState<QueueData>({ phases: [], paused: false });
  const [queueConnectionState, setQueueConnectionState] = useState<ConnectionState>({
    isConnected: false,
    connectionQuality: 'disconnected',
    lastUpdated: null,
    reconnectAttempts: 0,
  });

  // ============================================================================
  // State - ADW Monitor
  // ============================================================================
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

  // ============================================================================
  // State - System Status
  // ============================================================================
  const [systemStatusData, setSystemStatusData] = useState<SystemStatusData | null>(null);
  const [systemConnectionState, setSystemConnectionState] = useState<ConnectionState>({
    isConnected: false,
    connectionQuality: 'disconnected',
    lastUpdated: null,
    reconnectAttempts: 0,
  });

  // ============================================================================
  // State - Workflows
  // ============================================================================
  const [workflows, setWorkflows] = useState<WorkflowExecution[]>([]);
  const [workflowsConnectionState, setWorkflowsConnectionState] = useState<ConnectionState>({
    isConnected: false,
    connectionQuality: 'disconnected',
    lastUpdated: null,
    reconnectAttempts: 0,
  });

  // ============================================================================
  // State - Routes
  // ============================================================================
  const [routes, setRoutes] = useState<Route[]>([]);
  const [routesConnectionState, setRoutesConnectionState] = useState<ConnectionState>({
    isConnected: false,
    connectionQuality: 'disconnected',
    lastUpdated: null,
    reconnectAttempts: 0,
  });

  // ============================================================================
  // State - History
  // ============================================================================
  const [historyWorkflows, setHistoryWorkflows] = useState<WorkflowHistoryItem[]>([]);
  const [historyTotalCount, setHistoryTotalCount] = useState(0);
  const [historyAnalytics, setHistoryAnalytics] = useState<HistoryAnalytics | null>(null);
  const [historyConnectionState, setHistoryConnectionState] = useState<ConnectionState>({
    isConnected: false,
    connectionQuality: 'disconnected',
    lastUpdated: null,
    reconnectAttempts: 0,
  });

  // ============================================================================
  // State - Planned Features
  // ============================================================================
  const [plannedFeatures, setPlannedFeatures] = useState<PlannedFeature[]>([]);
  const [plannedFeaturesStats, setPlannedFeaturesStats] = useState<PlannedFeaturesStats | null>(null);
  const [plannedFeaturesConnectionState, setPlannedFeaturesConnectionState] = useState<ConnectionState>({
    isConnected: false,
    connectionQuality: 'disconnected',
    lastUpdated: null,
    reconnectAttempts: 0,
  });

  // ============================================================================
  // State - Webhook Status
  // ============================================================================
  const [webhookStatusData, setWebhookStatusData] = useState<WebhookStatusData | null>(null);
  const [webhookStatusConnectionState, setWebhookStatusConnectionState] = useState<ConnectionState>({
    isConnected: false,
    connectionQuality: 'disconnected',
    lastUpdated: null,
    reconnectAttempts: 0,
  });

  // ============================================================================
  // WebSocket refs
  // ============================================================================
  const queueWsRef = useRef<WebSocket | null>(null);
  const adwWsRef = useRef<WebSocket | null>(null);
  const systemWsRef = useRef<WebSocket | null>(null);
  const workflowsWsRef = useRef<WebSocket | null>(null);
  const routesWsRef = useRef<WebSocket | null>(null);
  const historyWsRef = useRef<WebSocket | null>(null);
  const plannedFeaturesWsRef = useRef<WebSocket | null>(null);
  const webhookStatusWsRef = useRef<WebSocket | null>(null);

  const reconnectTimeoutRefs = useRef<{
    queue?: NodeJS.Timeout;
    adw?: NodeJS.Timeout;
    system?: NodeJS.Timeout;
    workflows?: NodeJS.Timeout;
    routes?: NodeJS.Timeout;
    history?: NodeJS.Timeout;
    plannedFeatures?: NodeJS.Timeout;
    webhookStatus?: NodeJS.Timeout;
  }>({});

  const reconnectAttemptsRefs = useRef({
    queue: 0,
    adw: 0,
    system: 0,
    workflows: 0,
    routes: 0,
    history: 0,
    plannedFeatures: 0,
    webhookStatus: 0,
  });

  // ============================================================================
  // HTTP fallback queries (for fast initial load)
  // ============================================================================
  const { data: queuePolledData } = useQuery({
    queryKey: ['queue'],
    queryFn: getQueueData,
    refetchInterval: false,
    enabled: true,
  });

  const { data: adwPolledData } = useQuery({
    queryKey: ['adw-monitor'],
    queryFn: getAdwMonitor,
    refetchInterval: false,
    enabled: true,
  });

  const { data: systemPolledData } = useQuery({
    queryKey: ['system-status'],
    queryFn: async () => {
      const { getSystemStatus } = await import('../api/client');
      return getSystemStatus();
    },
    refetchInterval: false,
    enabled: true,
  });

  const { data: workflowsPolledData } = useQuery({
    queryKey: ['workflows'],
    queryFn: listWorkflows,
    refetchInterval: false,
    enabled: true,
  });

  const { data: routesPolledData } = useQuery({
    queryKey: ['routes'],
    queryFn: getRoutes,
    refetchInterval: false,
    enabled: true,
  });

  const { data: historyPolledData } = useQuery({
    queryKey: ['workflow-history'],
    queryFn: () => getWorkflowHistory({ limit: 50, offset: 0 }),
    refetchInterval: false,
    enabled: true,
  });

  const { data: plannedFeaturesPolledData } = useQuery({
    queryKey: ['planned-features'],
    queryFn: async () => {
      const features = await plannedFeaturesClient.getAll({ limit: 100 });
      const stats = await plannedFeaturesClient.getStats();
      return { features, stats };
    },
    refetchInterval: false,
    enabled: true,
  });

  // Webhook status has NO HTTP fallback - WebSocket only
  // The webhook service (port 8001) doesn't have CORS configured
  // Backend fetches from port 8001 internally and broadcasts via WebSocket
  const webhookStatusPolledData = null;

  // ============================================================================
  // Update state when polled data arrives
  // ============================================================================
  useEffect(() => {
    if (queuePolledData) {
      setQueueData(queuePolledData);
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
      if (!systemConnectionState.isConnected) {
        setSystemConnectionState(prev => ({
          ...prev,
          lastUpdated: new Date(),
          connectionQuality: 'poor',
        }));
      }
    }
  }, [systemPolledData, systemConnectionState.isConnected]);

  useEffect(() => {
    if (workflowsPolledData) {
      setWorkflows(workflowsPolledData);
      if (!workflowsConnectionState.isConnected) {
        setWorkflowsConnectionState(prev => ({
          ...prev,
          lastUpdated: new Date(),
          connectionQuality: 'poor',
        }));
      }
    }
  }, [workflowsPolledData, workflowsConnectionState.isConnected]);

  useEffect(() => {
    if (routesPolledData?.routes) {
      setRoutes(routesPolledData.routes);
      if (!routesConnectionState.isConnected) {
        setRoutesConnectionState(prev => ({
          ...prev,
          lastUpdated: new Date(),
          connectionQuality: 'poor',
        }));
      }
    }
  }, [routesPolledData, routesConnectionState.isConnected]);

  useEffect(() => {
    if (historyPolledData) {
      setHistoryWorkflows(historyPolledData.workflows);
      setHistoryTotalCount(historyPolledData.total_count);
      setHistoryAnalytics(historyPolledData.analytics);
      if (!historyConnectionState.isConnected) {
        setHistoryConnectionState(prev => ({
          ...prev,
          lastUpdated: new Date(),
          connectionQuality: 'poor',
        }));
      }
    }
  }, [historyPolledData, historyConnectionState.isConnected]);

  useEffect(() => {
    if (plannedFeaturesPolledData) {
      setPlannedFeatures(plannedFeaturesPolledData.features);
      setPlannedFeaturesStats(plannedFeaturesPolledData.stats);
      if (!plannedFeaturesConnectionState.isConnected) {
        setPlannedFeaturesConnectionState(prev => ({
          ...prev,
          lastUpdated: new Date(),
          connectionQuality: 'poor',
        }));
      }
    }
  }, [plannedFeaturesPolledData, plannedFeaturesConnectionState.isConnected]);

  useEffect(() => {
    if (webhookStatusPolledData) {
      setWebhookStatusData(webhookStatusPolledData);
      if (!webhookStatusConnectionState.isConnected) {
        setWebhookStatusConnectionState(prev => ({
          ...prev,
          lastUpdated: new Date(),
          connectionQuality: 'poor',
        }));
      }
    }
  }, [webhookStatusPolledData, webhookStatusConnectionState.isConnected]);

  // ============================================================================
  // Exponential backoff calculation
  // ============================================================================
  const getReconnectDelay = (attempt: number): number => {
    const baseDelay = 1000;
    const delay = Math.min(baseDelay * Math.pow(2, attempt), intervals.websocket.maxReconnectDelay);
    const jitter = Math.random() * 1000;
    return delay + jitter;
  };

  // ============================================================================
  // WebSocket Connection Functions
  // ============================================================================

  // Connect to Queue WebSocket
  const connectQueueWs = () => {
    if (reconnectAttemptsRefs.current.queue >= intervals.websocket.maxReconnectAttempts) {
      console.warn('[WS] Max reconnection attempts reached for Queue');
      return;
    }

    const url = apiConfig.websocket.queue();
    if (DEBUG_WS) console.log(`[WS] Connecting to Queue: ${url}`);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        if (DEBUG_WS) console.log(`[WS] Queue connected`);
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
    if (DEBUG_WS) console.log(`[WS] Connecting to ADW Monitor: ${url}`);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        if (DEBUG_WS) console.log(`[WS] ADW Monitor connected`);
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
    if (DEBUG_WS) console.log(`[WS] Connecting to System Status: ${url}`);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        if (DEBUG_WS) console.log(`[WS] System Status connected`);
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

        reconnectAttemptsRefs.current.system++;
        const delay = getReconnectDelay(reconnectAttemptsRefs.current.system);
        reconnectTimeoutRefs.current.system = setTimeout(connectSystemWs, delay);
      };

      systemWsRef.current = ws;
    } catch (err) {
      console.error('[WS] System Status connection failed:', err);
    }
  };

  // Connect to Workflows WebSocket
  const connectWorkflowsWs = () => {
    if (reconnectAttemptsRefs.current.workflows >= intervals.websocket.maxReconnectAttempts) {
      console.warn('[WS] Max reconnection attempts reached for Workflows');
      return;
    }

    const url = apiConfig.websocket.workflows();
    if (DEBUG_WS) console.log(`[WS] Connecting to Workflows: ${url}`);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        if (DEBUG_WS) console.log(`[WS] Workflows connected`);
        reconnectAttemptsRefs.current.workflows = 0;
        setWorkflowsConnectionState({
          isConnected: true,
          connectionQuality: 'excellent',
          lastUpdated: new Date(),
          reconnectAttempts: 0,
        });
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'workflows_update') {
            setWorkflows(message.data);
            setWorkflowsConnectionState(prev => ({
              ...prev,
              lastUpdated: new Date(),
              connectionQuality: 'excellent',
            }));
            if (DEBUG_WS) console.log('[WS] Workflows update:', message.data.length, 'workflows');
          }
        } catch (err) {
          console.error('[WS] Workflows message parse error:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] Workflows error:', error);
      };

      ws.onclose = () => {
        if (DEBUG_WS) console.log('[WS] Workflows disconnected');
        setWorkflowsConnectionState(prev => ({
          ...prev,
          isConnected: false,
          connectionQuality: 'disconnected',
        }));

        reconnectAttemptsRefs.current.workflows++;
        const delay = getReconnectDelay(reconnectAttemptsRefs.current.workflows);
        reconnectTimeoutRefs.current.workflows = setTimeout(connectWorkflowsWs, delay);
      };

      workflowsWsRef.current = ws;
    } catch (err) {
      console.error('[WS] Workflows connection failed:', err);
    }
  };

  // Connect to Routes WebSocket
  const connectRoutesWs = () => {
    if (reconnectAttemptsRefs.current.routes >= intervals.websocket.maxReconnectAttempts) {
      console.warn('[WS] Max reconnection attempts reached for Routes');
      return;
    }

    const url = apiConfig.websocket.routes();
    if (DEBUG_WS) console.log(`[WS] Connecting to Routes: ${url}`);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        if (DEBUG_WS) console.log(`[WS] Routes connected`);
        reconnectAttemptsRefs.current.routes = 0;
        setRoutesConnectionState({
          isConnected: true,
          connectionQuality: 'excellent',
          lastUpdated: new Date(),
          reconnectAttempts: 0,
        });
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'routes_update') {
            setRoutes(message.data);
            setRoutesConnectionState(prev => ({
              ...prev,
              lastUpdated: new Date(),
              connectionQuality: 'excellent',
            }));
            if (DEBUG_WS) console.log('[WS] Routes update:', message.data.length, 'routes');
          }
        } catch (err) {
          console.error('[WS] Routes message parse error:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] Routes error:', error);
      };

      ws.onclose = () => {
        if (DEBUG_WS) console.log('[WS] Routes disconnected');
        setRoutesConnectionState(prev => ({
          ...prev,
          isConnected: false,
          connectionQuality: 'disconnected',
        }));

        reconnectAttemptsRefs.current.routes++;
        const delay = getReconnectDelay(reconnectAttemptsRefs.current.routes);
        reconnectTimeoutRefs.current.routes = setTimeout(connectRoutesWs, delay);
      };

      routesWsRef.current = ws;
    } catch (err) {
      console.error('[WS] Routes connection failed:', err);
    }
  };

  // Connect to History WebSocket
  const connectHistoryWs = () => {
    if (reconnectAttemptsRefs.current.history >= intervals.websocket.maxReconnectAttempts) {
      console.warn('[WS] Max reconnection attempts reached for History');
      return;
    }

    const url = apiConfig.websocket.workflowHistory();
    if (DEBUG_WS) console.log(`[WS] Connecting to History: ${url}`);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        if (DEBUG_WS) console.log(`[WS] History connected`);
        reconnectAttemptsRefs.current.history = 0;
        setHistoryConnectionState({
          isConnected: true,
          connectionQuality: 'excellent',
          lastUpdated: new Date(),
          reconnectAttempts: 0,
        });
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'workflow_history_update') {
            setHistoryWorkflows(message.data.workflows);
            setHistoryTotalCount(message.data.total_count);
            setHistoryAnalytics(message.data.analytics);
            setHistoryConnectionState(prev => ({
              ...prev,
              lastUpdated: new Date(),
              connectionQuality: 'excellent',
            }));
            if (DEBUG_WS) console.log('[WS] History update:', message.data.workflows.length, 'workflows');
          }
        } catch (err) {
          console.error('[WS] History message parse error:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] History error:', error);
      };

      ws.onclose = () => {
        if (DEBUG_WS) console.log('[WS] History disconnected');
        setHistoryConnectionState(prev => ({
          ...prev,
          isConnected: false,
          connectionQuality: 'disconnected',
        }));

        reconnectAttemptsRefs.current.history++;
        const delay = getReconnectDelay(reconnectAttemptsRefs.current.history);
        reconnectTimeoutRefs.current.history = setTimeout(connectHistoryWs, delay);
      };

      historyWsRef.current = ws;
    } catch (err) {
      console.error('[WS] History connection failed:', err);
    }
  };

  // Connect to Planned Features WebSocket
  const connectPlannedFeaturesWs = () => {
    if (reconnectAttemptsRefs.current.plannedFeatures >= intervals.websocket.maxReconnectAttempts) {
      console.warn('[WS] Max reconnection attempts reached for Planned Features');
      return;
    }

    const url = apiConfig.websocket.plannedFeatures();
    if (DEBUG_WS) console.log(`[WS] Connecting to Planned Features: ${url}`);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        if (DEBUG_WS) console.log(`[WS] Planned Features connected`);
        reconnectAttemptsRefs.current.plannedFeatures = 0;
        setPlannedFeaturesConnectionState({
          isConnected: true,
          connectionQuality: 'excellent',
          lastUpdated: new Date(),
          reconnectAttempts: 0,
        });
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'planned_features_update') {
            if (Array.isArray(message.data)) {
              setPlannedFeatures(message.data);
            } else if (message.data.features) {
              setPlannedFeatures(message.data.features);
              if (message.data.stats) {
                setPlannedFeaturesStats(message.data.stats);
              }
            }
            setPlannedFeaturesConnectionState(prev => ({
              ...prev,
              lastUpdated: new Date(),
              connectionQuality: 'excellent',
            }));
            if (DEBUG_WS) console.log('[WS] Planned Features update:', Array.isArray(message.data) ? message.data.length : message.data.features?.length, 'features');
          }
        } catch (err) {
          console.error('[WS] Planned Features message parse error:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] Planned Features error:', error);
      };

      ws.onclose = () => {
        if (DEBUG_WS) console.log('[WS] Planned Features disconnected');
        setPlannedFeaturesConnectionState(prev => ({
          ...prev,
          isConnected: false,
          connectionQuality: 'disconnected',
        }));

        reconnectAttemptsRefs.current.plannedFeatures++;
        const delay = getReconnectDelay(reconnectAttemptsRefs.current.plannedFeatures);
        reconnectTimeoutRefs.current.plannedFeatures = setTimeout(connectPlannedFeaturesWs, delay);
      };

      plannedFeaturesWsRef.current = ws;
    } catch (err) {
      console.error('[WS] Planned Features connection failed:', err);
    }
  };

  // Connect to Webhook Status WebSocket
  const connectWebhookStatusWs = () => {
    if (reconnectAttemptsRefs.current.webhookStatus >= intervals.websocket.maxReconnectAttempts) {
      console.warn('[WS] Max reconnection attempts reached for Webhook Status');
      return;
    }

    const url = apiConfig.websocket.webhookStatus();
    if (DEBUG_WS) console.log(`[WS] Connecting to Webhook Status: ${url}`);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        if (DEBUG_WS) console.log(`[WS] Webhook Status connected`);
        reconnectAttemptsRefs.current.webhookStatus = 0;
        setWebhookStatusConnectionState({
          isConnected: true,
          connectionQuality: 'excellent',
          lastUpdated: new Date(),
          reconnectAttempts: 0,
        });
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'webhook_status_update') {
            setWebhookStatusData(message.data);
            setWebhookStatusConnectionState(prev => ({
              ...prev,
              lastUpdated: new Date(),
              connectionQuality: 'excellent',
            }));
            if (DEBUG_WS) console.log('[WS] Webhook Status update');
          }
        } catch (err) {
          console.error('[WS] Webhook Status message parse error:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] Webhook Status error:', error);
      };

      ws.onclose = () => {
        if (DEBUG_WS) console.log('[WS] Webhook Status disconnected');
        setWebhookStatusConnectionState(prev => ({
          ...prev,
          isConnected: false,
          connectionQuality: 'disconnected',
        }));

        reconnectAttemptsRefs.current.webhookStatus++;
        const delay = getReconnectDelay(reconnectAttemptsRefs.current.webhookStatus);
        reconnectTimeoutRefs.current.webhookStatus = setTimeout(connectWebhookStatusWs, delay);
      };

      webhookStatusWsRef.current = ws;
    } catch (err) {
      console.error('[WS] Webhook Status connection failed:', err);
    }
  };

  // ============================================================================
  // Initialize all WebSocket connections on mount
  // ============================================================================
  useEffect(() => {
    connectQueueWs();
    connectAdwWs();
    connectSystemWs();
    connectWorkflowsWs();
    connectRoutesWs();
    connectHistoryWs();
    connectPlannedFeaturesWs();
    connectWebhookStatusWs();

    // Cleanup on unmount
    return () => {
      // Clear all reconnection timeouts
      Object.values(reconnectTimeoutRefs.current).forEach(timeout => {
        if (timeout) clearTimeout(timeout);
      });

      // Close all WebSocket connections
      queueWsRef.current?.close();
      adwWsRef.current?.close();
      systemWsRef.current?.close();
      workflowsWsRef.current?.close();
      routesWsRef.current?.close();
      historyWsRef.current?.close();
      plannedFeaturesWsRef.current?.close();
      webhookStatusWsRef.current?.close();
    };
  }, []);

  // ============================================================================
  // Context Value
  // ============================================================================
  const value: GlobalWebSocketContextValue = {
    queueData,
    queueConnectionState,
    adwMonitorData,
    adwConnectionState,
    systemStatusData,
    systemConnectionState,
    workflows,
    workflowsConnectionState,
    routes,
    routesConnectionState,
    historyWorkflows,
    historyTotalCount,
    historyAnalytics,
    historyConnectionState,
    plannedFeatures,
    plannedFeaturesStats,
    plannedFeaturesConnectionState,
    webhookStatusData,
    webhookStatusConnectionState,
  };

  return (
    <GlobalWebSocketContext.Provider value={value}>
      {children}
    </GlobalWebSocketContext.Provider>
  );
}
