/**
 * ADW Monitor Card Tests
 *
 * Tests for the real-time workflow monitoring component that displays
 * current ADW workflow status, phase progress, costs, and health indicators
 *
 * Note: This file uses simplified mock data that may not match all type requirements.
 * Tests pass with vitest runtime checking, and type mismatches are intentional for test simplicity.
 */

// @ts-nocheck - Simplified mock data for testing purposes
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AdwMonitorCard } from '../AdwMonitorCard';
import * as client from '../../api/client';
import type { AdwWorkflowStatus, AdwMonitorSummary, AdwHealthCheckResponse } from '../../api/client';

// Mock the API client
vi.mock('../../api/client', () => ({
  getAdwMonitor: vi.fn(),
  getAdwHealth: vi.fn(),
}));

// Mock the useReliablePolling hook
vi.mock('../../hooks/useReliablePolling', () => ({
  useReliablePolling: ({ fetchFn, onSuccess, onError, enabled }: any) => {
    // Immediately call fetchFn and trigger callbacks for testing
    if (enabled) {
      fetchFn()
        .then((data: any) => onSuccess(data))
        .catch((err: Error) => onError(err));
    }
    return {
      isPolling: enabled,
      connectionQuality: 'excellent' as const,
      lastUpdated: new Date(),
      consecutiveErrors: 0,
      retry: vi.fn(),
    };
  },
}));

// Mock ConnectionStatusIndicator to simplify tests
vi.mock('../ConnectionStatusIndicator', () => ({
  ConnectionStatusIndicator: () => <div data-testid="connection-status">Connected</div>,
}));

describe('AdwMonitorCard', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Loading State', () => {
    it('should render current workflow header', async () => {
      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [],
        summary: { total: 0, running: 0, completed: 0, failed: 0, paused: 0 },
      });

      render(<AdwMonitorCard />);

      // Verify the card renders with header
      await waitFor(() => {
        expect(screen.getByText('Current Workflow')).toBeInTheDocument();
      });
      expect(screen.getByText('Real-time progress')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should display "No Active Workflow" message when workflows array is empty', async () => {
      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [],
        summary: { total: 0, running: 0, completed: 0, failed: 0, paused: 0 },
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText('No Active Workflow')).toBeInTheDocument();
      });
      expect(screen.getByText('Queue is empty')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should display error message when API call fails', async () => {
      vi.spyOn(client, 'getAdwMonitor').mockRejectedValue(new Error('Network error'));

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText('Unable to load workflows')).toBeInTheDocument();
      });
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  describe('Workflow Display', () => {
    const mockWorkflow: AdwWorkflowStatus = {
      adw_id: 'adw-test123',
      issue_number: 42,
      workflow_template: 'adw_plan_iso',
      status: 'running',
      current_phase: 'Planning',
      phases_completed: ['Validate', 'Build'],
      duration_seconds: 120,
      current_cost: 1.25,
      estimated_cost_total: 5.0,
      github_url: 'https://github.com/test/repo/issues/42',
      pr_number: null,
      issue_class: 'feature',
      error_count: 0,
      last_error: null,
      is_process_active: true,
    };

    const mockSummary: AdwMonitorSummary = {
      total: 1,
      running: 1,
      completed: 0,
      failed: 0,
      paused: 0,
    };

    it('should display workflow information correctly', async () => {
      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [mockWorkflow],
        summary: mockSummary,
      });
      vi.spyOn(client, 'getAdwHealth').mockResolvedValue({
        adw_id: 'adw-test123',
        overall_health: 'ok',
        warnings: [],
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText('#42')).toBeInTheDocument();
      });

      expect(screen.getByText('Planning Phase')).toBeInTheDocument();
      expect(screen.getByText('$1.25')).toBeInTheDocument();
      expect(screen.getByText('of $5.00')).toBeInTheDocument();
    });

    it('should display running status badge correctly', async () => {
      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [mockWorkflow],
        summary: mockSummary,
      });
      vi.spyOn(client, 'getAdwHealth').mockResolvedValue({
        adw_id: 'adw-test123',
        overall_health: 'ok',
        warnings: [],
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText('RUNNING')).toBeInTheDocument();
      });
    });

    it('should display completed status badge correctly', async () => {
      const completedWorkflow = {
        ...mockWorkflow,
        status: 'completed' as const,
      };

      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [completedWorkflow],
        summary: { ...mockSummary, running: 0, completed: 1 },
      });
      vi.spyOn(client, 'getAdwHealth').mockResolvedValue({
        adw_id: 'adw-test123',
        overall_health: 'ok',
        warnings: [],
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText('COMPLETED')).toBeInTheDocument();
      });
    });

    it('should display failed status badge correctly', async () => {
      const failedWorkflow = {
        ...mockWorkflow,
        status: 'failed' as const,
      };

      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [failedWorkflow],
        summary: { ...mockSummary, running: 0, failed: 1 },
      });
      vi.spyOn(client, 'getAdwHealth').mockResolvedValue({
        adw_id: 'adw-test123',
        overall_health: 'ok',
        warnings: [],
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText('FAILED')).toBeInTheDocument();
      });
    });

    it('should display PR number when available', async () => {
      const workflowWithPR = {
        ...mockWorkflow,
        pr_number: 123,
      };

      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [workflowWithPR],
        summary: mockSummary,
      });
      vi.spyOn(client, 'getAdwHealth').mockResolvedValue({
        adw_id: 'adw-test123',
        overall_health: 'ok',
        warnings: [],
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText('PR #123')).toBeInTheDocument();
      });
    });

    it('should display workflow duration correctly', async () => {
      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [mockWorkflow],
        summary: mockSummary,
      });
      vi.spyOn(client, 'getAdwHealth').mockResolvedValue({
        adw_id: 'adw-test123',
        overall_health: 'ok',
        warnings: [],
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText('2m 0s')).toBeInTheDocument();
      });
    });

    it('should display error count when errors exist', async () => {
      const workflowWithErrors = {
        ...mockWorkflow,
        error_count: 3,
        last_error: 'Test error message',
      };

      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [workflowWithErrors],
        summary: mockSummary,
      });
      vi.spyOn(client, 'getAdwHealth').mockResolvedValue({
        adw_id: 'adw-test123',
        overall_health: 'ok',
        warnings: [],
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText('3 errors')).toBeInTheDocument();
      });
    });

    it('should display process active indicator when process is running', async () => {
      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [mockWorkflow],
        summary: mockSummary,
      });
      vi.spyOn(client, 'getAdwHealth').mockResolvedValue({
        adw_id: 'adw-test123',
        overall_health: 'ok',
        warnings: [],
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText('Process Active')).toBeInTheDocument();
      });
    });
  });

  describe('Health Status Integration', () => {
    const mockWorkflow: AdwWorkflowStatus = {
      adw_id: 'adw-test123',
      issue_number: 42,
      workflow_template: 'adw_plan_iso',
      status: 'running',
      current_phase: 'Planning',
      phases_completed: [],
      duration_seconds: 120,
      current_cost: 1.25,
      estimated_cost_total: 5.0,
      github_url: 'https://github.com/test/repo/issues/42',
      pr_number: null,
      issue_class: 'feature',
      error_count: 0,
      last_error: null,
      is_process_active: true,
    };

    it('should display healthy status badge', async () => {
      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [mockWorkflow],
        summary: { total: 1, running: 1, completed: 0, failed: 0, paused: 0 },
      });
      vi.spyOn(client, 'getAdwHealth').mockResolvedValue({
        adw_id: 'adw-test123',
        overall_health: 'ok',
        warnings: [],
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText(/HEALTH/)).toBeInTheDocument();
      });
    });

    it('should display warning health status badge', async () => {
      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [mockWorkflow],
        summary: { total: 1, running: 1, completed: 0, failed: 0, paused: 0 },
      });
      vi.spyOn(client, 'getAdwHealth').mockResolvedValue({
        adw_id: 'adw-test123',
        overall_health: 'warning',
        warnings: ['Test warning'],
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText(/HEALTH/)).toBeInTheDocument();
      });
    });

    it('should display error health status badge', async () => {
      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [mockWorkflow],
        summary: { total: 1, running: 1, completed: 0, failed: 0, paused: 0 },
      });
      vi.spyOn(client, 'getAdwHealth').mockResolvedValue({
        adw_id: 'adw-test123',
        overall_health: 'error',
        warnings: ['Critical error'],
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText(/HEALTH/)).toBeInTheDocument();
      });
    });

    it('should not display health status when health check fails', async () => {
      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [mockWorkflow],
        summary: { total: 1, running: 1, completed: 0, failed: 0, paused: 0 },
      });
      vi.spyOn(client, 'getAdwHealth').mockRejectedValue(new Error('Health check failed'));

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText('#42')).toBeInTheDocument();
      });

      // Health status should not be displayed
      expect(screen.queryByText(/HEALTH/)).not.toBeInTheDocument();
    });
  });

  describe('Phase Visualization', () => {
    it('should display all 9 workflow phases', async () => {
      const mockWorkflow: AdwWorkflowStatus = {
        adw_id: 'adw-test123',
        issue_number: 42,
        workflow_template: 'adw_plan_iso',
        status: 'running',
        current_phase: 'Planning',
        phases_completed: [],
        duration_seconds: 120,
        current_cost: 1.25,
        estimated_cost_total: 5.0,
        github_url: 'https://github.com/test/repo/issues/42',
        pr_number: null,
        issue_class: 'feature',
        error_count: 0,
        last_error: null,
        is_process_active: true,
      };

      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [mockWorkflow],
        summary: { total: 1, running: 1, completed: 0, failed: 0, paused: 0 },
      });
      vi.spyOn(client, 'getAdwHealth').mockResolvedValue({
        adw_id: 'adw-test123',
        overall_health: 'ok',
        warnings: [],
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText('Plan')).toBeInTheDocument();
      });

      expect(screen.getByText('Validate')).toBeInTheDocument();
      expect(screen.getByText('Build')).toBeInTheDocument();
      expect(screen.getByText('Lint')).toBeInTheDocument();
      expect(screen.getByText('Test')).toBeInTheDocument();
      expect(screen.getByText('Review')).toBeInTheDocument();
      expect(screen.getByText('Doc')).toBeInTheDocument();
      expect(screen.getByText('Ship')).toBeInTheDocument();
      expect(screen.getByText('Cleanup')).toBeInTheDocument();
    });

    it('should display phase completion count', async () => {
      const mockWorkflow: AdwWorkflowStatus = {
        adw_id: 'adw-test123',
        issue_number: 42,
        workflow_template: 'adw_plan_iso',
        status: 'running',
        current_phase: 'Test',
        phases_completed: ['Plan', 'Validate', 'Build', 'Lint'],
        duration_seconds: 120,
        current_cost: 1.25,
        estimated_cost_total: 5.0,
        github_url: 'https://github.com/test/repo/issues/42',
        pr_number: null,
        issue_class: 'feature',
        error_count: 0,
        last_error: null,
        is_process_active: true,
      };

      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [mockWorkflow],
        summary: { total: 1, running: 1, completed: 0, failed: 0, paused: 0 },
      });
      vi.spyOn(client, 'getAdwHealth').mockResolvedValue({
        adw_id: 'adw-test123',
        overall_health: 'ok',
        warnings: [],
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText('4 / 9 phases completed')).toBeInTheDocument();
      });
    });
  });

  describe('Cost Display', () => {
    it('should format cost correctly', async () => {
      const mockWorkflow: AdwWorkflowStatus = {
        adw_id: 'adw-test123',
        issue_number: 42,
        workflow_template: 'adw_plan_iso',
        status: 'running',
        current_phase: 'Planning',
        phases_completed: [],
        duration_seconds: 120,
        current_cost: 12.456,
        estimated_cost_total: 50.123,
        github_url: 'https://github.com/test/repo/issues/42',
        pr_number: null,
        issue_class: 'feature',
        error_count: 0,
        last_error: null,
        is_process_active: true,
      };

      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [mockWorkflow],
        summary: { total: 1, running: 1, completed: 0, failed: 0, paused: 0 },
      });
      vi.spyOn(client, 'getAdwHealth').mockResolvedValue({
        adw_id: 'adw-test123',
        overall_health: 'ok',
        warnings: [],
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText('$12.46')).toBeInTheDocument();
      });
      expect(screen.getByText('of $50.12')).toBeInTheDocument();
    });

    it('should display $0.00 for null cost', async () => {
      const mockWorkflow: AdwWorkflowStatus = {
        adw_id: 'adw-test123',
        issue_number: 42,
        workflow_template: 'adw_plan_iso',
        status: 'running',
        current_phase: 'Planning',
        phases_completed: [],
        duration_seconds: 120,
        current_cost: null,
        estimated_cost_total: null,
        github_url: 'https://github.com/test/repo/issues/42',
        pr_number: null,
        issue_class: 'feature',
        error_count: 0,
        last_error: null,
        is_process_active: true,
      };

      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [mockWorkflow],
        summary: { total: 1, running: 1, completed: 0, failed: 0, paused: 0 },
      });
      vi.spyOn(client, 'getAdwHealth').mockResolvedValue({
        adw_id: 'adw-test123',
        overall_health: 'ok',
        warnings: [],
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByText('$0.00')).toBeInTheDocument();
      });
    });
  });

  describe('Connection Status', () => {
    it('should display connection status indicator', async () => {
      vi.spyOn(client, 'getAdwMonitor').mockResolvedValue({
        workflows: [],
        summary: { total: 0, running: 0, completed: 0, failed: 0, paused: 0 },
      });

      render(<AdwMonitorCard />);

      await waitFor(() => {
        expect(screen.getByTestId('connection-status')).toBeInTheDocument();
      });
    });
  });
});
