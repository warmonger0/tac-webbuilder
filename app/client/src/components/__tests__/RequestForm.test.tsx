/**
 * Request Form Tests
 *
 * Tests for project path persistence, health checks, and form submission
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RequestForm } from '../RequestForm';
import * as client from '../../api/client';

// Mock the API client
vi.mock('../../api/client');

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    clear: () => {
      store = {};
    },
    removeItem: (key: string) => {
      delete store[key];
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('RequestForm', () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Project Path Persistence', () => {
    it('should load saved project path from localStorage on mount', () => {
      localStorageMock.setItem('tac-webbuilder-project-path', '/saved/project/path');

      render(<RequestForm />);

      const projectPathInput = screen.getByPlaceholderText(/projects\/my-app/i);
      expect(projectPathInput).toHaveValue('/saved/project/path');
    });

    it('should save project path to localStorage on successful submission', async () => {
      const mockHealthStatus = {
        overall_status: 'healthy' as const,
        services: {},
        summary: { healthy_services: 5, total_services: 5, health_percentage: 100 },
      };

      const mockSubmitResponse = { request_id: 'test-123' };
      const mockPreview = {
        title: 'Test Issue',
        body: 'Test body',
        labels: [],
        classification: 'feature',
        workflow: 'adw_plan_iso',
        model_set: 'base',
      };

      vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockHealthStatus);
      vi.spyOn(client, 'submitRequest').mockResolvedValue(mockSubmitResponse);
      vi.spyOn(client, 'getPreview').mockResolvedValue(mockPreview);

      render(<RequestForm />);

      const nlInput = screen.getByPlaceholderText(/Build a REST API/i);
      const projectPathInput = screen.getByPlaceholderText(/projects\/my-app/i);
      const submitButton = screen.getByText('Generate Issue');

      await userEvent.type(nlInput, 'Create a new feature');
      await userEvent.type(projectPathInput, '/my/new/project');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(localStorageMock.getItem('tac-webbuilder-project-path')).toBe(
          '/my/new/project'
        );
      });
    });

    it('should not clear project path after successful submission', async () => {
      const mockHealthStatus = {
        overall_status: 'healthy' as const,
        services: {},
        summary: { healthy_services: 5, total_services: 5, health_percentage: 100 },
      };

      const mockSubmitResponse = { request_id: 'test-123' };
      const mockPreview = {
        title: 'Test Issue',
        body: 'Test body',
        labels: [],
        classification: 'feature',
        workflow: 'adw_plan_iso',
        model_set: 'base',
      };
      const mockConfirmResponse = {
        issue_number: 42,
        github_url: 'https://github.com/user/repo/issues/42',
      };

      vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockHealthStatus);
      vi.spyOn(client, 'submitRequest').mockResolvedValue(mockSubmitResponse);
      vi.spyOn(client, 'getPreview').mockResolvedValue(mockPreview);
      vi.spyOn(client, 'confirmAndPost').mockResolvedValue(mockConfirmResponse);

      render(<RequestForm />);

      const nlInput = screen.getByPlaceholderText(/Build a REST API/i);
      const projectPathInput = screen.getByPlaceholderText(/projects\/my-app/i);
      const autoPostCheckbox = screen.getByLabelText(/Auto-post to GitHub/i);
      const submitButton = screen.getByText('Generate Issue');

      await userEvent.type(nlInput, 'Create a new feature');
      await userEvent.type(projectPathInput, '/persistent/path');
      await userEvent.click(autoPostCheckbox);
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Issue #42 created successfully/)).toBeInTheDocument();
      });

      // NL input should be cleared
      expect(nlInput).toHaveValue('');

      // Project path should NOT be cleared
      expect(projectPathInput).toHaveValue('/persistent/path');
    });
  });

  describe('System Health Checks', () => {
    it('should perform health check before submission', async () => {
      const mockHealthStatus = {
        overall_status: 'healthy' as const,
        services: {
          webhook: {
            name: 'Webhook Service',
            status: 'healthy' as const,
          },
        },
        summary: { healthy_services: 1, total_services: 1, health_percentage: 100 },
      };

      const mockSubmitResponse = { request_id: 'test-123' };
      const mockPreview = {
        title: 'Test',
        body: 'Test',
        labels: [],
        classification: 'feature',
        workflow: 'adw_plan_iso',
        model_set: 'base',
      };

      const healthCheckSpy = vi
        .spyOn(client, 'getSystemStatus')
        .mockResolvedValue(mockHealthStatus);
      vi.spyOn(client, 'submitRequest').mockResolvedValue(mockSubmitResponse);
      vi.spyOn(client, 'getPreview').mockResolvedValue(mockPreview);

      render(<RequestForm />);

      const nlInput = screen.getByPlaceholderText(/Build a REST API/i);
      const submitButton = screen.getByText('Generate Issue');

      await userEvent.type(nlInput, 'Test request');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(healthCheckSpy).toHaveBeenCalled();
      });
    });

    it('should show warning when system status is degraded', async () => {
      const mockHealthStatus = {
        overall_status: 'degraded' as const,
        services: {
          webhook: {
            name: 'Webhook Service',
            status: 'degraded' as const,
          },
        },
        summary: { healthy_services: 0, total_services: 1, health_percentage: 0 },
      };

      const mockSubmitResponse = { request_id: 'test-123' };
      const mockPreview = {
        title: 'Test',
        body: 'Test',
        labels: [],
        classification: 'feature',
        workflow: 'adw_plan_iso',
        model_set: 'base',
      };

      vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockHealthStatus);
      vi.spyOn(client, 'submitRequest').mockResolvedValue(mockSubmitResponse);
      vi.spyOn(client, 'getPreview').mockResolvedValue(mockPreview);

      render(<RequestForm />);

      const nlInput = screen.getByPlaceholderText(/Build a REST API/i);
      const submitButton = screen.getByText('Generate Issue');

      await userEvent.type(nlInput, 'Test request');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Some services are degraded/i)
        ).toBeInTheDocument();
      });
    });

    it('should show error warning when critical services are down', async () => {
      const mockHealthStatus = {
        overall_status: 'error' as const,
        services: {
          webhook: {
            name: 'Webhook Service',
            status: 'error' as const,
          },
          cloudflare_tunnel: {
            name: 'Cloudflare Tunnel',
            status: 'error' as const,
          },
        },
        summary: { healthy_services: 0, total_services: 2, health_percentage: 0 },
      };

      const mockSubmitResponse = { request_id: 'test-123' };
      const mockPreview = {
        title: 'Test',
        body: 'Test',
        labels: [],
        classification: 'feature',
        workflow: 'adw_plan_iso',
        model_set: 'base',
      };

      vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockHealthStatus);
      vi.spyOn(client, 'submitRequest').mockResolvedValue(mockSubmitResponse);
      vi.spyOn(client, 'getPreview').mockResolvedValue(mockPreview);

      render(<RequestForm />);

      const nlInput = screen.getByPlaceholderText(/Build a REST API/i);
      const submitButton = screen.getByText('Generate Issue');

      await userEvent.type(nlInput, 'Test request');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Critical services are down: Webhook Service, Cloudflare Tunnel/i)
        ).toBeInTheDocument();
      });
    });

    it('should handle health check failures gracefully', async () => {
      const mockSubmitResponse = { request_id: 'test-123' };
      const mockPreview = {
        title: 'Test',
        body: 'Test',
        labels: [],
        classification: 'feature',
        workflow: 'adw_plan_iso',
        model_set: 'base',
      };

      vi.spyOn(client, 'getSystemStatus').mockRejectedValue(
        new Error('Health check failed')
      );
      vi.spyOn(client, 'submitRequest').mockResolvedValue(mockSubmitResponse);
      vi.spyOn(client, 'getPreview').mockResolvedValue(mockPreview);

      render(<RequestForm />);

      const nlInput = screen.getByPlaceholderText(/Build a REST API/i);
      const submitButton = screen.getByText('Generate Issue');

      await userEvent.type(nlInput, 'Test request');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Unable to check system health. Proceeding anyway./i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    it('should validate required fields', async () => {
      render(<RequestForm />);

      const submitButton = screen.getByText('Generate Issue');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Please enter a description')).toBeInTheDocument();
      });
    });

    it('should disable submit button while loading', async () => {
      const mockHealthStatus = {
        overall_status: 'healthy' as const,
        services: {},
        summary: { healthy_services: 5, total_services: 5, health_percentage: 100 },
      };

      vi.spyOn(client, 'getSystemStatus').mockResolvedValue(mockHealthStatus);
      vi.spyOn(client, 'submitRequest').mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      render(<RequestForm />);

      const nlInput = screen.getByPlaceholderText(/Build a REST API/i);
      const submitButton = screen.getByText('Generate Issue');

      await userEvent.type(nlInput, 'Test request');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Processing...')).toBeDisabled();
      });
    });
  });
});
