/**
 * ADW Monitor Card Phase 3 Tests
 *
 * Tests Phase 3 features including:
 * - WebSocket connection initialization
 * - Real-time state updates via WebSocket messages
 * - Fallback to polling when WebSocket fails
 * - Connection status indicator states
 * - Error boundary behavior
 * - Animation triggers on status changes
 * - Exponential backoff reconnection logic
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AdwMonitorCard } from '../AdwMonitorCard';
import * as useReliableWebSocketModule from '../../hooks/useReliableWebSocket';
import * as client from '../../api/client';

// Mock the API client
vi.mock('../../api/client', () => ({
  getAdwMonitor: vi.fn(),
}));

// Mock useReducedMotion hook
vi.mock('../../hooks/useReducedMotion', () => ({
  useReducedMotion: () => false,
}));

describe('AdwMonitorCard - Phase 3 WebSocket Features', () => {
  let mockUseReliableWebSocket: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock implementation
    mockUseReliableWebSocket = vi.fn().mockReturnValue({
      isConnected: false,
      connectionQuality: 'disconnected',
      lastUpdated: null,
      reconnectAttempts: 0,
      retry: vi.fn(),
    });

    vi.spyOn(useReliableWebSocketModule, 'useReliableWebSocket').mockImplementation(
      mockUseReliableWebSocket
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('WebSocket Connection Initialization', () => {
    it('should initialize WebSocket connection with correct URL', () => {
      render(<AdwMonitorCard />);

      expect(mockUseReliableWebSocket).toHaveBeenCalledWith(
        expect.objectContaining({
          url: expect.stringMatching(/^ws:\/\/.*:8000\/ws\/adw-monitor$/),
          queryKey: ['adw-monitor'],
          enabled: true,
        })
      );
    });

    it('should use wss:// protocol when page is served over https', () => {
      // Mock https location
      const originalLocation = window.location;
      Object.defineProperty(window, 'location', {
        value: { ...originalLocation, protocol: 'https:' },
        writable: true,
      });

      render(<AdwMonitorCard />);

      expect(mockUseReliableWebSocket).toHaveBeenCalledWith(
        expect.objectContaining({
          url: expect.stringMatching(/^wss:\/\//),
        })
      );

      // Restore original location
      Object.defineProperty(window, 'location', {
        value: originalLocation,
        writable: true,
      });
    });

    it('should configure exponential backoff with correct parameters', () => {
      render(<AdwMonitorCard />);

      expect(mockUseReliableWebSocket).toHaveBeenCalledWith(
        expect.objectContaining({
          maxReconnectDelay: 30000, // 30 seconds
          maxReconnectAttempts: 10,
        })
      );
    });

    it('should set polling interval for fallback mode', () => {
      render(<AdwMonitorCard />);

      expect(mockUseReliableWebSocket).toHaveBeenCalledWith(
        expect.objectContaining({
          pollingInterval: 10000, // 10 seconds
        })
      );
    });
  });

  describe('Real-time State Updates via WebSocket', () => {
    it('should update workflows when WebSocket message received', async () => {
      const mockWorkflows = [
        {
          adw_id: 'adw-test-001',
          status: 'running',
          progress: 0.5,
          phase: 'implementation',
          issue_number: 42,
        },
      ];

      let onMessageCallback: ((data: any) => void) | undefined;
      mockUseReliableWebSocket.mockImplementation((options: any) => {
        onMessageCallback = options.onMessage;
        return {
          isConnected: true,
          connectionQuality: 'excellent',
          lastUpdated: new Date(),
          reconnectAttempts: 0,
          retry: vi.fn(),
        };
      });

      render(<AdwMonitorCard />);

      // Wait for initial render
      await waitFor(() => {
        expect(onMessageCallback).toBeDefined();
      });

      // Simulate WebSocket message
      act(() => {
        onMessageCallback?.({
          workflows: mockWorkflows,
          summary: {
            total_workflows: 1,
            active_workflows: 1,
            completed_workflows: 0,
            failed_workflows: 0,
          },
        });
      });

      // Verify workflow displayed
      await waitFor(() => {
        expect(screen.getByText(/adw-test-001/i)).toBeInTheDocument();
      });
    });

    it('should clear error state when valid WebSocket message received', async () => {
      let onMessageCallback: ((data: any) => void) | undefined;
      mockUseReliableWebSocket.mockImplementation((options: any) => {
        onMessageCallback = options.onMessage;
        return {
          isConnected: true,
          connectionQuality: 'excellent',
          lastUpdated: new Date(),
          reconnectAttempts: 0,
          retry: vi.fn(),
        };
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(onMessageCallback).toBeDefined();
      });

      // Send valid message
      act(() => {
        onMessageCallback?.({
          workflows: [],
          summary: {
            total_workflows: 0,
            active_workflows: 0,
            completed_workflows: 0,
            failed_workflows: 0,
          },
        });
      });

      // Verify no error displayed
      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });
  });

  describe('Fallback to Polling on WebSocket Failure', () => {
    it('should use HTTP polling when WebSocket connection fails', async () => {
      mockUseReliableWebSocket.mockReturnValue({
        isConnected: false,
        connectionQuality: 'disconnected',
        lastUpdated: null,
        reconnectAttempts: 5,
        retry: vi.fn(),
      });

      const mockPollingData = {
        workflows: [
          {
            adw_id: 'adw-poll-001',
            status: 'running',
            progress: 0.3,
            phase: 'planning',
          },
        ],
        summary: {
          total_workflows: 1,
          active_workflows: 1,
          completed_workflows: 0,
          failed_workflows: 0,
        },
      };

      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue(mockPollingData);

      render(<AdwMonitorCard />);

      // Verify queryFn provided for polling
      expect(mockUseReliableWebSocket).toHaveBeenCalledWith(
        expect.objectContaining({
          queryFn: expect.any(Function),
        })
      );
    });

    it('should indicate polling mode when max reconnect attempts reached', async () => {
      mockUseReliableWebSocket.mockReturnValue({
        isConnected: false,
        connectionQuality: 'disconnected',
        lastUpdated: null,
        reconnectAttempts: 10, // Max attempts reached
        retry: vi.fn(),
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(
          screen.getByText(/Polling Mode Active/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Connection Status Indicator States', () => {
    it('should show loading state when connecting and no data', () => {
      mockUseReliableWebSocket.mockReturnValue({
        isConnected: false,
        connectionQuality: 'disconnected',
        lastUpdated: null,
        reconnectAttempts: 0,
        retry: vi.fn(),
      });

      render(<AdwMonitorCard />);

      // Loading skeleton should be visible
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('should show reconnecting state with attempt counter', async () => {
      mockUseReliableWebSocket.mockReturnValue({
        isConnected: false,
        connectionQuality: 'disconnected',
        lastUpdated: null,
        reconnectAttempts: 3,
        retry: vi.fn(),
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText(/Connection lost. Retrying.../i)).toBeInTheDocument();
        expect(screen.getByText(/Attempt 3\/10/i)).toBeInTheDocument();
      });
    });

    it('should show degraded state after max attempts', async () => {
      mockUseReliableWebSocket.mockReturnValue({
        isConnected: false,
        connectionQuality: 'disconnected',
        lastUpdated: null,
        reconnectAttempts: 10,
        retry: vi.fn(),
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(
          screen.getByText(/Connection failed after multiple attempts/i)
        ).toBeInTheDocument();
        expect(
          screen.getByText(/Falling back to polling mode/i)
        ).toBeInTheDocument();
      });
    });

    it('should provide retry button in disconnected state', async () => {
      const mockRetry = vi.fn();
      mockUseReliableWebSocket.mockReturnValue({
        isConnected: false,
        connectionQuality: 'disconnected',
        lastUpdated: null,
        reconnectAttempts: 2,
        retry: mockRetry,
      });

      const user = userEvent.setup();
      render(<AdwMonitorCard />);

      const retryButton = await screen.findByRole('button', { name: /Retry Now/i });
      await user.click(retryButton);

      expect(mockRetry).toHaveBeenCalledOnce();
    });
  });

  describe('Exponential Backoff Reconnection Logic', () => {
    it('should track reconnection attempts correctly', async () => {
      const attempts = [0, 1, 2, 4, 8];

      for (const attempt of attempts) {
        mockUseReliableWebSocket.mockReturnValue({
          isConnected: false,
          connectionQuality: 'disconnected',
          lastUpdated: null,
          reconnectAttempts: attempt,
          retry: vi.fn(),
        });

        const { unmount } = render(<AdwMonitorCard />);

        if (attempt > 0) {
          await waitFor(() => {
            expect(screen.getByText(new RegExp(`Attempt ${attempt}`, 'i'))).toBeInTheDocument();
          });
        }

        unmount();
      }
    });

    it('should stop reconnecting after max attempts', () => {
      mockUseReliableWebSocket.mockReturnValue({
        isConnected: false,
        connectionQuality: 'disconnected',
        lastUpdated: null,
        reconnectAttempts: 10, // At max
        retry: vi.fn(),
      });

      render(<AdwMonitorCard />);

      // Verify showing fallback message, not reconnecting message
      expect(screen.getByText(/Connection failed after multiple attempts/i)).toBeInTheDocument();
    });

    it('should reset reconnect attempts on manual retry', async () => {
      const mockRetry = vi.fn();
      mockUseReliableWebSocket.mockReturnValue({
        isConnected: false,
        connectionQuality: 'disconnected',
        lastUpdated: null,
        reconnectAttempts: 5,
        retry: mockRetry,
      });

      const user = userEvent.setup();
      render(<AdwMonitorCard />);

      const retryButton = await screen.findByRole('button', { name: /Retry Now/i });
      await user.click(retryButton);

      // Verify retry function called (which resets attempts in the hook)
      expect(mockRetry).toHaveBeenCalledOnce();
    });
  });

  describe('Connection Quality Monitoring', () => {
    it('should reflect excellent connection quality', () => {
      mockUseReliableWebSocket.mockReturnValue({
        isConnected: true,
        connectionQuality: 'excellent',
        lastUpdated: new Date(),
        reconnectAttempts: 0,
        retry: vi.fn(),
      });

      render(<AdwMonitorCard />);

      // Component should be functional with no error indicators
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('should handle poor connection quality gracefully', () => {
      mockUseReliableWebSocket.mockReturnValue({
        isConnected: true,
        connectionQuality: 'poor',
        lastUpdated: new Date(Date.now() - 25000), // 25 seconds ago
        reconnectAttempts: 0,
        retry: vi.fn(),
      });

      render(<AdwMonitorCard />);

      // Should still function even with poor connection
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility and ARIA Attributes', () => {
    it('should have proper ARIA labels on retry button', async () => {
      mockUseReliableWebSocket.mockReturnValue({
        isConnected: false,
        connectionQuality: 'disconnected',
        lastUpdated: null,
        reconnectAttempts: 3,
        retry: vi.fn(),
      });

      render(<AdwMonitorCard />);

      const retryButton = await screen.findByRole('button', {
        name: /Retry connection now. Attempt 3 of 10/i,
      });

      expect(retryButton).toHaveAttribute('aria-label');
    });

    it('should have live region for connection status updates', async () => {
      mockUseReliableWebSocket.mockReturnValue({
        isConnected: false,
        connectionQuality: 'disconnected',
        lastUpdated: null,
        reconnectAttempts: 2,
        retry: vi.fn(),
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        const alert = screen.getByRole('alert');
        expect(alert).toHaveAttribute('aria-live', 'assertive');
        expect(alert).toHaveAttribute('aria-atomic', 'true');
      });
    });

    it('should label regions appropriately', async () => {
      mockUseReliableWebSocket.mockReturnValue({
        isConnected: false,
        connectionQuality: 'disconnected',
        lastUpdated: null,
        reconnectAttempts: 1,
        retry: vi.fn(),
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        const region = screen.getByRole('region', { name: /Connection Error/i });
        expect(region).toBeInTheDocument();
      });
    });
  });

  describe('Recovery Instructions and User Guidance', () => {
    it('should show recovery steps when connection fails', async () => {
      mockUseReliableWebSocket.mockReturnValue({
        isConnected: false,
        connectionQuality: 'disconnected',
        lastUpdated: null,
        reconnectAttempts: 2,
        retry: vi.fn(),
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText(/Recovery Steps:/i)).toBeInTheDocument();
        expect(screen.getByText(/Check your internet connection/i)).toBeInTheDocument();
        expect(screen.getByText(/Verify the server is running/i)).toBeInTheDocument();
        expect(screen.getByText(/Refresh the page/i)).toBeInTheDocument();
      });
    });

    it('should display WebSocket URL in recovery instructions', async () => {
      mockUseReliableWebSocket.mockReturnValue({
        isConnected: false,
        connectionQuality: 'disconnected',
        lastUpdated: null,
        reconnectAttempts: 1,
        retry: vi.fn(),
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText(/ws:\/\/.*:8000\/ws\/adw-monitor/i)).toBeInTheDocument();
      });
    });
  });
});
