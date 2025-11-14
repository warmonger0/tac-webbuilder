import { useEffect, useState, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { listWorkflows, getRoutes, getHistory } from '../api/client';
import type { Workflow, Route, WorkflowHistoryResponse } from '../types';

interface WorkflowsWebSocketMessage {
  type: 'workflows_update';
  data: Workflow[];
}

interface RoutesWebSocketMessage {
  type: 'routes_update';
  data: Route[];
}

interface WorkflowHistoryWebSocketMessage {
  type: 'history_update';
  data: {
    items: WorkflowHistoryResponse['items'];
    analytics: WorkflowHistoryResponse['analytics'];
    total: number;
    has_more: boolean;
  };
}

export function useWorkflowsWebSocket() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
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

export function useWorkflowHistoryWebSocket() {
  const [historyData, setHistoryData] = useState<WorkflowHistoryResponse | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  // Fallback polling when WebSocket is disconnected
  const { data: polledHistory } = useQuery({
    queryKey: ['history'],
    queryFn: () => getHistory({}),
    refetchInterval: isConnected ? false : 5000, // Only poll when WS disconnected
    enabled: !isConnected, // Only enable when WS is not connected
  });

  useEffect(() => {
    if (!isConnected && polledHistory) {
      setHistoryData(polledHistory);
      setLastUpdated(new Date());
    }
  }, [polledHistory, isConnected]);

  useEffect(() => {
    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.hostname;
      const wsUrl = `${protocol}//${host}:8000/ws/workflow-history`;

      console.log('[WS] Connecting to:', wsUrl);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Connected to workflow history updates');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message: WorkflowHistoryWebSocketMessage = JSON.parse(event.data);

          if (message.type === 'history_update') {
            setHistoryData({
              items: message.data.items,
              analytics: message.data.analytics,
              total: message.data.total,
              has_more: message.data.has_more,
            });
            setLastUpdated(new Date());
            console.log('[WS] Received workflow history update:', message.data.items.length, 'items');
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
        console.log('[WS] Disconnected from workflow history, will reconnect in 5s...');
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

  return { historyData, isConnected, lastUpdated };
}
