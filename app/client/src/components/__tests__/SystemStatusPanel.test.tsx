/**
 * System Status Panel Tests
 *
 * Tests for the comprehensive system health monitoring panel
 */

import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SystemStatusPanel } from '../SystemStatusPanel';
import * as client from '../../api/client';

// Mock the API client
vi.mock('../../api/client');

describe('SystemStatusPanel', () => {
  afterEach(() => {
    vi.restoreAllMocks();
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
    vi.useFakeTimers();

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
    await act(async () => {
      vi.advanceTimersByTime(30000);
    });

    await waitFor(() => {
      expect(getSystemStatusSpy).toHaveBeenCalledTimes(2);
    });

    // Fast-forward another 30 seconds
    await act(async () => {
      vi.advanceTimersByTime(30000);
    });

    await waitFor(() => {
      expect(getSystemStatusSpy).toHaveBeenCalledTimes(3);
    });

    vi.useRealTimers();
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

  it('should show start button for webhook service when not running', async () => {
    const mockStatus = {
      overall_status: 'error' as const,
      timestamp: '2025-11-14T14:00:00Z',
      services: {
        webhook: {
          name: 'Webhook Service',
          status: 'error' as const,
          message: 'Not running (port 8001)',
        },
      },
      summary: { healthy_services: 0, total_services: 1, health_percentage: 0 },
    };

    vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockStatus);

    render(<SystemStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText('Start Service')).toBeInTheDocument();
    });
  });

  it('should disable start button when webhook service is healthy', async () => {
    const mockStatus = {
      overall_status: 'healthy' as const,
      timestamp: '2025-11-14T14:00:00Z',
      services: {
        webhook: {
          name: 'Webhook Service',
          status: 'healthy' as const,
          message: 'Port 8001 • 5/10 webhooks processed',
          details: { port: 8001, webhooks_processed: '5/10' },
        },
      },
      summary: { healthy_services: 1, total_services: 1, health_percentage: 100 },
    };

    vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockStatus);

    render(<SystemStatusPanel />);

    await waitFor(() => {
      const startButton = screen.getByText('Start Service');
      expect(startButton).toBeDisabled();
    });
  });

  it('should start webhook service when button clicked', async () => {
    const mockStatus = {
      overall_status: 'error' as const,
      timestamp: '2025-11-14T14:00:00Z',
      services: {
        webhook: {
          name: 'Webhook Service',
          status: 'error' as const,
          message: 'Not running (port 8001)',
        },
      },
      summary: { healthy_services: 0, total_services: 1, health_percentage: 0 },
    };

    const updatedStatus = {
      ...mockStatus,
      overall_status: 'healthy' as const,
      services: {
        webhook: {
          name: 'Webhook Service',
          status: 'healthy' as const,
          message: 'Port 8001 • 0/0 webhooks processed',
        },
      },
      summary: { healthy_services: 1, total_services: 1, health_percentage: 100 },
    };

    vi.spyOn(client, 'getSystemStatus')
      .mockResolvedValueOnce(mockStatus)
      .mockResolvedValueOnce(updatedStatus);

    vi.spyOn(client, 'startWebhookService').mockResolvedValue({
      status: 'started',
      message: 'Webhook service started successfully on port 8001',
    });

    render(<SystemStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText('Start Service')).toBeInTheDocument();
    });

    const startButton = screen.getByText('Start Service');
    await userEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByText(/Webhook service started successfully/)).toBeInTheDocument();
    });
  });

  it('should show restart button for Cloudflare tunnel', async () => {
    const mockStatus = {
      overall_status: 'healthy' as const,
      timestamp: '2025-11-14T14:00:00Z',
      services: {
        cloudflare_tunnel: {
          name: 'Cloudflare Tunnel',
          status: 'healthy' as const,
          message: 'Tunnel is running',
        },
      },
      summary: { healthy_services: 1, total_services: 1, health_percentage: 100 },
    };

    vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockStatus);

    render(<SystemStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText('Restart Tunnel')).toBeInTheDocument();
    });
  });

  it('should restart Cloudflare tunnel when button clicked', async () => {
    const mockStatus = {
      overall_status: 'error' as const,
      timestamp: '2025-11-14T14:00:00Z',
      services: {
        cloudflare_tunnel: {
          name: 'Cloudflare Tunnel',
          status: 'error' as const,
          message: 'Tunnel process not found',
        },
      },
      summary: { healthy_services: 0, total_services: 1, health_percentage: 0 },
    };

    vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockStatus);
    vi.spyOn(client, 'restartCloudflare').mockResolvedValue({
      status: 'restarted',
      message: 'Cloudflare tunnel restarted successfully',
    });

    render(<SystemStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText('Restart Tunnel')).toBeInTheDocument();
    });

    const restartButton = screen.getByText('Restart Tunnel');
    await userEvent.click(restartButton);

    await waitFor(() => {
      expect(screen.getByText(/Cloudflare tunnel restarted successfully/)).toBeInTheDocument();
    });
  });

  it('should show GitHub webhook panel with redeliver button', async () => {
    const mockStatus = {
      overall_status: 'error' as const,
      timestamp: '2025-11-14T14:00:00Z',
      services: {
        github_webhook: {
          name: 'GitHub Webhook',
          status: 'error' as const,
          message: 'Latest delivery failed (HTTP 502)',
          details: { webhook_url: 'webhook.directmyagent.com' },
        },
      },
      summary: { healthy_services: 0, total_services: 1, health_percentage: 0 },
    };

    vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockStatus);

    render(<SystemStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText('GitHub Webhook')).toBeInTheDocument();
      expect(screen.getByText('Redeliver Failed')).toBeInTheDocument();
    });
  });

  it('should redeliver GitHub webhook when button clicked', async () => {
    const mockStatus = {
      overall_status: 'error' as const,
      timestamp: '2025-11-14T14:00:00Z',
      services: {
        github_webhook: {
          name: 'GitHub Webhook',
          status: 'error' as const,
          message: 'Latest delivery failed (HTTP 502)',
        },
      },
      summary: { healthy_services: 0, total_services: 1, health_percentage: 0 },
    };

    vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockStatus);
    vi.spyOn(client, 'redeliverGitHubWebhook').mockResolvedValue({
      status: 'success',
      message: 'Webhook delivery 12345 redelivered',
    });

    render(<SystemStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText('Redeliver Failed')).toBeInTheDocument();
    });

    const redeliverButton = screen.getByText('Redeliver Failed');
    await userEvent.click(redeliverButton);

    await waitFor(() => {
      expect(screen.getByText(/Webhook delivery.*redelivered/)).toBeInTheDocument();
    });
  });

  it('should show port information for webhook service', async () => {
    const mockStatus = {
      overall_status: 'healthy' as const,
      timestamp: '2025-11-14T14:00:00Z',
      services: {
        webhook: {
          name: 'Webhook Service',
          status: 'healthy' as const,
          message: 'Port 8001 • 10/15 webhooks processed',
          details: {
            port: 8001,
            webhooks_processed: '10/15',
            failed: 5,
          },
        },
      },
      summary: { healthy_services: 1, total_services: 1, health_percentage: 100 },
    };

    vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockStatus);

    render(<SystemStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText(/Port 8001/)).toBeInTheDocument();
      expect(screen.getByText(/10\/15 webhooks processed/)).toBeInTheDocument();
    });
  });

  it('should render services in correct order', async () => {
    const mockStatus = {
      overall_status: 'healthy' as const,
      timestamp: '2025-11-14T14:00:00Z',
      services: {
        backend: { name: 'Backend API', status: 'healthy' as const, message: 'Running' },
        database: { name: 'Database', status: 'healthy' as const, message: 'Connected' },
        webhook: { name: 'Webhook Service', status: 'healthy' as const, message: 'Running' },
        frontend: { name: 'Frontend', status: 'healthy' as const, message: 'Serving' },
        cloudflare_tunnel: { name: 'Cloudflare Tunnel', status: 'healthy' as const, message: 'Running' },
        github_webhook: { name: 'GitHub Webhook', status: 'healthy' as const, message: 'Active' },
      },
      summary: { healthy_services: 6, total_services: 6, health_percentage: 100 },
    };

    vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockStatus);

    render(<SystemStatusPanel />);

    await waitFor(() => {
      const serviceCards = screen.getAllByRole('heading', { level: 4 });
      // Expected order: Backend, Database, Webhook, Frontend, Cloudflare, GitHub Webhook
      expect(serviceCards[0]).toHaveTextContent('Backend API');
      expect(serviceCards[1]).toHaveTextContent('Database');
      expect(serviceCards[2]).toHaveTextContent('Webhook Service');
      expect(serviceCards[3]).toHaveTextContent('Frontend');
      expect(serviceCards[4]).toHaveTextContent('Cloudflare Tunnel');
      expect(serviceCards[5]).toHaveTextContent('GitHub Webhook');
    });
  });
});
