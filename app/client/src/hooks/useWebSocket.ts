import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getRoutes, getWorkflowHistory, listWorkflows } from '../api/client';
import type { HistoryAnalytics, Route, WorkflowExecution, WorkflowHistoryItem } from '../types';

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
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  // Fallback polling when WebSocket is disconnected
  const { data: polledWorkflows } = useQuery({
    queryKey: ['workflows'],
    queryFn: listWorkflows,
    refetchInterval: isConnected ? false : 3000, // Only poll when WS disconnected
    enabled: !isConnected, // Only enable when WS is not connected
  });

  useEffect(() => {
    if (!isConnected && polledWorkflows) {
      setWorkflows(polledWorkflows);
      setLastUpdated(new Date());
    }
  }, [polledWorkflows, isConnected]);

  useEffect(() => {
    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.hostname;
      const wsUrl = `${protocol}//${host}:8000/ws/workflows`;

      console.log('[WS] Connecting to:', wsUrl);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Connected to workflow updates');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message: WorkflowsWebSocketMessage = JSON.parse(event.data);

          if (message.type === 'workflows_update') {
            setWorkflows(message.data);
            setLastUpdated(new Date());
            console.log('[WS] Received workflow update:', message.data.length, 'workflows');
          }
        } catch (err) {
          console.error('[WS] Error parsing message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] Error:', error);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('[WS] Disconnected, will reconnect in 5s...');
        setIsConnected(false);

        // Reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      };
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return { workflows, isConnected, lastUpdated };
}

export function useRoutesWebSocket() {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  // Fallback polling when WebSocket is disconnected
  const { data: polledRoutes } = useQuery({
    queryKey: ['routes'],
    queryFn: getRoutes,
    refetchInterval: isConnected ? false : 3000, // Only poll when WS disconnected
    enabled: !isConnected, // Only enable when WS is not connected
  });

  useEffect(() => {
    if (!isConnected && polledRoutes) {
      setRoutes(polledRoutes.routes);
      setLastUpdated(new Date());
    }
  }, [polledRoutes, isConnected]);

  useEffect(() => {
    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.hostname;
      const wsUrl = `${protocol}//${host}:8000/ws/routes`;

      console.log('[WS] Connecting to:', wsUrl);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Connected to routes updates');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message: RoutesWebSocketMessage = JSON.parse(event.data);

          if (message.type === 'routes_update') {
            setRoutes(message.data);
            setLastUpdated(new Date());
            console.log('[WS] Received routes update:', message.data.length, 'routes');
          }
        } catch (err) {
          console.error('[WS] Error parsing message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] Error:', error);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('[WS] Disconnected, will reconnect in 5s...');
        setIsConnected(false);

        // Reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      };
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return { routes, isConnected, lastUpdated };
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
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  // Fallback polling when WebSocket is disconnected
  const { data: polledData } = useQuery({
    queryKey: ['workflow-history'],
    queryFn: () => getWorkflowHistory({ limit: 50, offset: 0 }),
    refetchInterval: isConnected ? false : 3000, // Only poll when WS disconnected
    enabled: !isConnected, // Only enable when WS is not connected
  });

  useEffect(() => {
    if (!isConnected && polledData) {
      setWorkflows(polledData.workflows);
      setTotalCount(polledData.total_count);
      setAnalytics(polledData.analytics);
      setLastUpdated(new Date());
    }
  }, [polledData, isConnected]);

  useEffect(() => {
    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.hostname;
      const wsUrl = `${protocol}//${host}:8000/ws/workflow-history`;

      console.log('[WS] Connecting to workflow history:', wsUrl);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Connected to workflow history updates');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message: WorkflowHistoryWebSocketMessage = JSON.parse(event.data);

          if (message.type === 'workflow_history_update') {
            setWorkflows(message.data.workflows);
            setTotalCount(message.data.total_count);
            setAnalytics(message.data.analytics);
            setLastUpdated(new Date());
            console.log('[WS] Received workflow history update:', message.data.workflows.length, 'workflows');
          }
        } catch (err) {
          console.error('[WS] Error parsing workflow history message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] Workflow history error:', error);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('[WS] Workflow history disconnected, will reconnect in 5s...');
        setIsConnected(false);

        // Reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      };
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return { workflows, totalCount, analytics, isConnected, lastUpdated };
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
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    // Don't connect if no ADW ID
    if (!adwId) {
      return;
    }

    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.hostname;
      const wsUrl = `${protocol}//${host}:8000/ws/adw-state/${adwId}`;

      console.log('[WS] Connecting to ADW state:', wsUrl);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Connected to ADW state updates');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message: ADWStateWebSocketMessage = JSON.parse(event.data);

          if (message.type === 'adw_state_update') {
            setState(message.data);
            setLastUpdated(new Date());
            console.log('[WS] Received ADW state update:', message.adw_id, message.data);
          }
        } catch (err) {
          console.error('[WS] Error parsing ADW state message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] ADW state error:', error);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('[WS] ADW state disconnected, will reconnect in 5s...');
        setIsConnected(false);

        // Reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      };
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [adwId]);

  return { state, isConnected, lastUpdated };
}
