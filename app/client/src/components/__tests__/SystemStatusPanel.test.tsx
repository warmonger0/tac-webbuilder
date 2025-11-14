/**
 * System Status Panel Tests
 *
 * Tests for the comprehensive system health monitoring panel
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SystemStatusPanel } from '../SystemStatusPanel';
import * as client from '../../api/client';

// Mock the API client
vi.mock('../../api/client');

describe('SystemStatusPanel', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('should render loading state initially', () => {
    vi.spyOn(client, 'getSystemStatus').mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<SystemStatusPanel />);
    expect(screen.getByText('Checking...')).toBeInTheDocument();
  });

  it('should display healthy system status', async () => {
    const mockStatus = {
      overall_status: 'healthy' as const,
      timestamp: '2025-11-14T14:00:00Z',
      services: {
        backend_api: {
          name: 'Backend API',
          status: 'healthy' as const,
          uptime_seconds: 3600,
          uptime_human: '1h 0m',
          message: 'Running on port 8000',
          details: { port: '8000' },
        },
        database: {
          name: 'Database',
          status: 'healthy' as const,
          message: '5 tables available',
          details: { tables_count: 5 },
        },
        webhook: {
          name: 'Webhook Service',
          status: 'healthy' as const,
          uptime_seconds: 1800,
          uptime_human: '30m',
          message: 'Success rate: 100.0%',
          details: { total_received: 10, successful: 10 },
        },
        cloudflare_tunnel: {
          name: 'Cloudflare Tunnel',
          status: 'healthy' as const,
          message: 'Tunnel is running',
        },
        frontend: {
          name: 'Frontend',
          status: 'healthy' as const,
          message: 'Serving on port 5173',
          details: { port: '5173' },
        },
      },
      summary: {
        healthy_services: 5,
        total_services: 5,
        health_percentage: 100,
      },
    };

    vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockStatus);

    render(<SystemStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText('Overall Status: Healthy')).toBeInTheDocument();
    });

    expect(screen.getByText('5 of 5 services healthy (100%)')).toBeInTheDocument();
    expect(screen.getByText('Backend API')).toBeInTheDocument();
    expect(screen.getByText('Database')).toBeInTheDocument();
    expect(screen.getByText('Webhook Service')).toBeInTheDocument();
    expect(screen.getByText('Cloudflare Tunnel')).toBeInTheDocument();
    expect(screen.getByText('Frontend')).toBeInTheDocument();
  });

  it('should display degraded system status', async () => {
    const mockStatus = {
      overall_status: 'degraded' as const,
      timestamp: '2025-11-14T14:00:00Z',
      services: {
        backend_api: {
          name: 'Backend API',
          status: 'healthy' as const,
          message: 'Running on port 8000',
        },
        webhook: {
          name: 'Webhook Service',
          status: 'degraded' as const,
          message: 'Success rate: 85.0%',
        },
      },
      summary: {
        healthy_services: 1,
        total_services: 2,
        health_percentage: 50,
      },
    };

    vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockStatus);

    render(<SystemStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText('Overall Status: Degraded')).toBeInTheDocument();
    });

    expect(screen.getByText('1 of 2 services healthy (50%)')).toBeInTheDocument();
  });

  it('should display error system status', async () => {
    const mockStatus = {
      overall_status: 'error' as const,
      timestamp: '2025-11-14T14:00:00Z',
      services: {
        backend_api: {
          name: 'Backend API',
          status: 'healthy' as const,
          message: 'Running',
        },
        webhook: {
          name: 'Webhook Service',
          status: 'error' as const,
          message: 'Service not responding on port 8001',
        },
        cloudflare_tunnel: {
          name: 'Cloudflare Tunnel',
          status: 'error' as const,
          message: 'Tunnel process not found',
        },
      },
      summary: {
        healthy_services: 1,
        total_services: 3,
        health_percentage: 33.3,
      },
    };

    vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockStatus);

    render(<SystemStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText('Overall Status: Error')).toBeInTheDocument();
    });

    expect(screen.getByText('Service not responding on port 8001')).toBeInTheDocument();
    expect(screen.getByText('Tunnel process not found')).toBeInTheDocument();
  });

  it('should handle API errors gracefully', async () => {
    vi.spyOn(client, 'getSystemStatus').mockRejectedValue(new Error('Network error'));

    render(<SystemStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to fetch system status/)).toBeInTheDocument();
    });
  });

  it('should refresh status when button clicked', async () => {
    const mockStatus = {
      overall_status: 'healthy' as const,
      timestamp: '2025-11-14T14:00:00Z',
      services: {},
      summary: { healthy_services: 0, total_services: 0, health_percentage: 0 },
    };

    const getSystemStatusSpy = vi
      .spyOn(client, 'getSystemStatus')
      .mockResolvedValue(mockStatus);

    render(<SystemStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });

    expect(getSystemStatusSpy).toHaveBeenCalledTimes(1);

    const refreshButton = screen.getByText('Refresh');
    await userEvent.click(refreshButton);

    await waitFor(() => {
      expect(getSystemStatusSpy).toHaveBeenCalledTimes(2);
    });
  });

  it('should auto-refresh every 30 seconds', async () => {
    const mockStatus = {
      overall_status: 'healthy' as const,
      timestamp: '2025-11-14T14:00:00Z',
      services: {},
      summary: { healthy_services: 0, total_services: 0, health_percentage: 0 },
    };

    const getSystemStatusSpy = vi
      .spyOn(client, 'getSystemStatus')
      .mockResolvedValue(mockStatus);

    render(<SystemStatusPanel />);

    await waitFor(() => {
      expect(getSystemStatusSpy).toHaveBeenCalledTimes(1);
    });

    // Fast-forward 30 seconds
    vi.advanceTimersByTime(30000);

    await waitFor(() => {
      expect(getSystemStatusSpy).toHaveBeenCalledTimes(2);
    });

    // Fast-forward another 30 seconds
    vi.advanceTimersByTime(30000);

    await waitFor(() => {
      expect(getSystemStatusSpy).toHaveBeenCalledTimes(3);
    });
  });

  it('should display service uptime information', async () => {
    const mockStatus = {
      overall_status: 'healthy' as const,
      timestamp: '2025-11-14T14:00:00Z',
      services: {
        backend_api: {
          name: 'Backend API',
          status: 'healthy' as const,
          uptime_seconds: 7200,
          uptime_human: '2h 0m',
          message: 'Running',
        },
      },
      summary: { healthy_services: 1, total_services: 1, health_percentage: 100 },
    };

    vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockStatus);

    render(<SystemStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText('Uptime: 2h 0m')).toBeInTheDocument();
    });
  });

  it('should display service details', async () => {
    const mockStatus = {
      overall_status: 'healthy' as const,
      timestamp: '2025-11-14T14:00:00Z',
      services: {
        database: {
          name: 'Database',
          status: 'healthy' as const,
          message: '5 tables available',
          details: {
            tables_count: 5,
            path: 'db/database.db',
          },
        },
      },
      summary: { healthy_services: 1, total_services: 1, health_percentage: 100 },
    };

    vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockStatus);

    render(<SystemStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText(/tables count/i)).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText(/path/i)).toBeInTheDocument();
    });
  });
});
