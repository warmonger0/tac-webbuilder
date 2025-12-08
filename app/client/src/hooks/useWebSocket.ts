import { useState } from 'react';
import { type AdwMonitorSummary, type AdwWorkflowStatus, getAdwMonitor, getRoutes, getWorkflowHistory, listWorkflows } from '../api/client';
import { getQueueData, type PhaseQueueItem } from '../api/queueClient';
import type { HistoryAnalytics, Route, WorkflowExecution, WorkflowHistoryItem } from '../types';
import { useReliableWebSocket } from './useReliableWebSocket';
import { apiConfig } from '../config/api';
import { intervals } from '../config/intervals';

// Debug flag - only log in development mode
const DEBUG_WS = import.meta.env.DEV;

interface WorkflowsWebSocketMessage {
  type: 'workflows_update';
  data: WorkflowExecution[];
}

interface RoutesWebSocketMessage {
  type: 'routes_update';
  data: Route[];
}

export function useWorkflowsWebSocket() {
  const [workflows, setWorkflows] = useState<WorkflowExecution[]>([]);

  const wsUrl = apiConfig.websocket.workflows();

  const connectionState = useReliableWebSocket<WorkflowExecution[], WorkflowsWebSocketMessage>({
    url: wsUrl,
    queryKey: ['workflows'],
    queryFn: listWorkflows,
    onMessage: (message) => {
      // Handle both WebSocket message format and HTTP polling response format
      if ('type' in message && message.type === 'workflows_update') {
        // WebSocket message format
        setWorkflows(message.data);
        if (DEBUG_WS) console.log('[WS] Received workflow update:', message.data.length, 'workflows');
      } else if (Array.isArray(message)) {
        // HTTP polling response format (array of workflows)
        setWorkflows(message);
        if (DEBUG_WS) console.log('[HTTP] Received workflow update:', message.length, 'workflows');
      }
    },
  });

  return {
    workflows,
    isConnected: connectionState.isConnected,
    connectionQuality: connectionState.connectionQuality,
    lastUpdated: connectionState.lastUpdated,
    reconnectAttempts: connectionState.reconnectAttempts,
  };
}

export function useRoutesWebSocket() {
  const [routes, setRoutes] = useState<Route[]>([]);

  const wsUrl = apiConfig.websocket.routes();

  const connectionState = useReliableWebSocket<{ routes: Route[] }, RoutesWebSocketMessage>({
    url: wsUrl,
    queryKey: ['routes'],
    queryFn: getRoutes,
    onMessage: (message: any) => {
      // Handle both WebSocket message format and HTTP polling response format
      if (message.type === 'routes_update') {
        // WebSocket message format
        setRoutes(message.data);
        if (DEBUG_WS) console.log('[WS] Received routes update:', message.data.length, 'routes');
      } else if (message.routes) {
        // HTTP polling response format
        setRoutes(message.routes);
        if (DEBUG_WS) console.log('[HTTP] Received routes update:', message.routes.length, 'routes');
      }
    },
  });

  return {
    routes,
    isConnected: connectionState.isConnected,
    connectionQuality: connectionState.connectionQuality,
    lastUpdated: connectionState.lastUpdated,
    reconnectAttempts: connectionState.reconnectAttempts,
  };
}

interface WorkflowHistoryWebSocketMessage {
  type: 'workflow_history_update';
  data: {
    workflows: WorkflowHistoryItem[];
    total_count: number;
    analytics: HistoryAnalytics;
  };
}

export function useWorkflowHistoryWebSocket() {
  const [workflows, setWorkflows] = useState<WorkflowHistoryItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [analytics, setAnalytics] = useState<HistoryAnalytics | null>(null);

  const wsUrl = apiConfig.websocket.workflowHistory();

  const connectionState = useReliableWebSocket<
    {
      workflows: WorkflowHistoryItem[];
      total_count: number;
      analytics: HistoryAnalytics;
    },
    WorkflowHistoryWebSocketMessage
  >({
    url: wsUrl,
    queryKey: ['workflow-history'],
    queryFn: () => getWorkflowHistory({ limit: intervals.components.workflowHistory.defaultLimit, offset: 0 }),
    onMessage: (message: any) => {
      // Handle both WebSocket message format and HTTP polling response format
      if (message.type === 'workflow_history_update') {
        // WebSocket message format
        setWorkflows(message.data.workflows);
        setTotalCount(message.data.total_count);
        setAnalytics(message.data.analytics);
        if (DEBUG_WS) console.log('[WS] Received workflow history update:', message.data.workflows.length, 'workflows');
      } else if (message.workflows) {
        // HTTP polling response format
        setWorkflows(message.workflows);
        setTotalCount(message.total_count);
        setAnalytics(message.analytics);
        if (DEBUG_WS) console.log('[HTTP] Received workflow history update:', message.workflows.length, 'workflows');
      }
    },
  });

  return {
    workflows,
    totalCount,
    analytics,
    isConnected: connectionState.isConnected,
    connectionQuality: connectionState.connectionQuality,
    lastUpdated: connectionState.lastUpdated,
    reconnectAttempts: connectionState.reconnectAttempts,
  };
}

interface ADWStateWebSocketMessage {
  type: 'adw_state_update';
  adw_id: string;
  data: {
    adw_id: string;
    issue_number?: string;
    status?: string;
    branch_name?: string;
    plan_file?: string;
    issue_class?: string;
    worktree_path?: string;
    backend_port?: number;
    frontend_port?: number;
    model_set?: string;
    all_adws?: string[];
    workflow_template?: string;
    model_used?: string;
    start_time?: string;
    nl_input?: string;
    github_url?: string;
    [key: string]: any;
  };
}

export function useADWStateWebSocket(adwId: string | null) {
  const [state, setState] = useState<ADWStateWebSocketMessage['data'] | null>(null);

  const wsUrl = adwId ? apiConfig.websocket.adwState(adwId) : '';

  const connectionState = useReliableWebSocket<
    ADWStateWebSocketMessage['data'],
    ADWStateWebSocketMessage
  >({
    url: wsUrl,
    queryKey: ['adw-state', adwId || ''],
    queryFn: async () => {
      // No HTTP fallback for ADW state - it's WebSocket-only
      throw new Error('ADW state only available via WebSocket');
    },
    onMessage: (message) => {
      if (message.type === 'adw_state_update') {
        setState(message.data);
        if (DEBUG_WS) console.log('[WS] Received ADW state update:', message.adw_id, message.data);
      }
    },
    enabled: !!adwId,
    maxReconnectAttempts: intervals.components.adwMonitor.maxReconnectAttempts,
  });

  return {
    state,
    isConnected: connectionState.isConnected,
    connectionQuality: connectionState.connectionQuality,
    lastUpdated: connectionState.lastUpdated,
    reconnectAttempts: connectionState.reconnectAttempts,
  };
}

interface ADWMonitorWebSocketMessage {
  type: 'adw_monitor_update';
  data: {
    workflows: AdwWorkflowStatus[];
    summary: AdwMonitorSummary;
    last_updated: string;
  };
}

export function useADWMonitorWebSocket() {
  const [workflows, setWorkflows] = useState<AdwWorkflowStatus[]>([]);
  const [summary, setSummary] = useState<AdwMonitorSummary>({
    total: 0,
    running: 0,
    completed: 0,
    failed: 0,
    paused: 0,
  });
  const [lastUpdated, setLastUpdated] = useState<string>('');

  const wsUrl = apiConfig.websocket.adwMonitor();

  const connectionState = useReliableWebSocket<
    ADWMonitorWebSocketMessage['data'],
    ADWMonitorWebSocketMessage
  >({
    url: wsUrl,
    queryKey: ['adw-monitor'],
    queryFn: getAdwMonitor,
    onMessage: (message: any) => {
      // Handle both WebSocket message format and HTTP polling response format
      if (message.type === 'adw_monitor_update') {
        // WebSocket message format
        setWorkflows(message.data.workflows);
        setSummary(message.data.summary);
        setLastUpdated(message.data.last_updated);
        if (DEBUG_WS) console.log('[WS] Received ADW monitor update:', message.data.workflows.length, 'workflows');
      } else if (message.workflows) {
        // HTTP polling response format
        setWorkflows(message.workflows);
        setSummary(message.summary);
        setLastUpdated(message.last_updated);
        if (DEBUG_WS) console.log('[HTTP] Received ADW monitor update:', message.workflows.length, 'workflows');
      }
    },
  });

  return {
    workflows,
    summary,
    lastUpdated,
    isConnected: connectionState.isConnected,
    connectionQuality: connectionState.connectionQuality,
    reconnectAttempts: connectionState.reconnectAttempts,
  };
}

interface QueueWebSocketMessage {
  type: 'queue_update';
  data: {
    phases: PhaseQueueItem[];
    total: number;
    paused: boolean;
  };
}

export function useQueueWebSocket() {
  const [phases, setPhases] = useState<PhaseQueueItem[]>([]);
  const [paused, setPaused] = useState<boolean>(false);

  const wsUrl = apiConfig.websocket.queue();

  const connectionState = useReliableWebSocket<
    { phases: PhaseQueueItem[]; total: number; paused: boolean },
    QueueWebSocketMessage
  >({
    url: wsUrl,
    queryKey: ['queue'],
    queryFn: getQueueData,
    onMessage: (message: any) => {
      // Handle both WebSocket message format and HTTP polling response format
      if (message.type === 'queue_update') {
        // WebSocket message format
        setPhases(message.data.phases);
        setPaused(message.data.paused);
        if (DEBUG_WS) console.log('[WS] Received queue update:', message.data.phases.length, 'phases');
      } else if (message.phases) {
        // HTTP polling response format
        setPhases(message.phases);
        setPaused(message.paused || false);
        if (DEBUG_WS) console.log('[HTTP] Received queue update:', message.phases.length, 'phases');
      }
    },
  });

  return {
    phases,
    paused,
    isConnected: connectionState.isConnected,
    connectionQuality: connectionState.connectionQuality,
    reconnectAttempts: connectionState.reconnectAttempts,
  };
}

interface SystemStatusWebSocketMessage {
  type: 'system_status_update';
  data: any; // SystemStatusResponse type
}

export function useSystemStatusWebSocket() {
  const [systemStatus, setSystemStatus] = useState<any>(null);

  const wsUrl = apiConfig.websocket.systemStatus();

  const connectionState = useReliableWebSocket<any, SystemStatusWebSocketMessage>({
    url: wsUrl,
    queryKey: ['system-status'],
    queryFn: async () => {
      const { getSystemStatus } = await import('../api/client');
      return getSystemStatus();
    },
    onMessage: (message: any) => {
      // Handle both WebSocket message format and HTTP polling response format
      if (message.type === 'system_status_update') {
        // WebSocket message format
        setSystemStatus(message.data);
        if (DEBUG_WS) console.log('[WS] Received system status update');
      } else if (message.overall_status) {
        // HTTP polling response format
        setSystemStatus(message);
        if (DEBUG_WS) console.log('[HTTP] Received system status update');
      }
    },
  });

  return {
    systemStatus,
    isConnected: connectionState.isConnected,
    connectionQuality: connectionState.connectionQuality,
    lastUpdated: connectionState.lastUpdated,
    reconnectAttempts: connectionState.reconnectAttempts,
  };
}

interface WebhookStatusWebSocketMessage {
  type: 'webhook_status_update';
  data: any; // Webhook status type
}

export function useWebhookStatusWebSocket() {
  const [webhookStatus, setWebhookStatus] = useState<any>(null);

  const wsUrl = apiConfig.websocket.webhookStatus();

  const connectionState = useReliableWebSocket<any, WebhookStatusWebSocketMessage>({
    url: wsUrl,
    queryKey: ['webhook-status'],
    queryFn: async () => {
      const { getWebhookStatus } = await import('../api/client');
      return getWebhookStatus();
    },
    onMessage: (message: any) => {
      // Handle both WebSocket message format and HTTP polling response format
      if (message.type === 'webhook_status_update') {
        // WebSocket message format
        setWebhookStatus(message.data);
        if (DEBUG_WS) console.log('[WS] Received webhook status update');
      } else if (message.status) {
        // HTTP polling response format
        setWebhookStatus(message);
        if (DEBUG_WS) console.log('[HTTP] Received webhook status update');
      }
    },
  });

  return {
    webhookStatus,
    isConnected: connectionState.isConnected,
    connectionQuality: connectionState.connectionQuality,
    lastUpdated: connectionState.lastUpdated,
    reconnectAttempts: connectionState.reconnectAttempts,
  };
}
