import { useEffect, useState } from 'react';
import type { Workflow } from '../types';

interface WebSocketMessage {
  type: string;
  adw_id: string;
  phase: string;
}

export function useWebSocket() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8002/ws');

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        if (message.type === 'workflow_progress') {
          setWorkflows((prev) =>
            prev.map((w) =>
              w.adw_id === message.adw_id
                ? { ...w, phase: message.phase }
                : w
            )
          );
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  return { workflows, isConnected };
}
