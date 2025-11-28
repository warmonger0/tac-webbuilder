import { useState } from 'react';
import { getRoutes, getWorkflowHistory, listWorkflows } from '../api/client';
import type { HistoryAnalytics, Route, WorkflowExecution, WorkflowHistoryItem } from '../types';
import { useReliableWebSocket } from './useReliableWebSocket';
import { apiConfig } from '../config/api';
import { intervals } from '../config/intervals';

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
        console.log('[WS] Received workflow update:', message.data.length, 'workflows');
      } else if (Array.isArray(message)) {
        // HTTP polling response format (array of workflows)
        setWorkflows(message);
        console.log('[HTTP] Received workflow update:', message.length, 'workflows');
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
        console.log('[WS] Received routes update:', message.data.length, 'routes');
      } else if (message.routes) {
        // HTTP polling response format
        setRoutes(message.routes);
        console.log('[HTTP] Received routes update:', message.routes.length, 'routes');
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
        console.log('[WS] Received workflow history update:', message.data.workflows.length, 'workflows');
      } else if (message.workflows) {
        // HTTP polling response format
        setWorkflows(message.workflows);
        setTotalCount(message.total_count);
        setAnalytics(message.analytics);
        console.log('[HTTP] Received workflow history update:', message.workflows.length, 'workflows');
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
        console.log('[WS] Received ADW state update:', message.adw_id, message.data);
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
