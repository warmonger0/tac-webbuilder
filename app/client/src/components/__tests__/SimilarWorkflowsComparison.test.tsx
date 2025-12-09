import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { SimilarWorkflowsComparison } from '../SimilarWorkflowsComparison';
import { WorkflowHistoryItem } from '../../types/api.types';

// Mock workflowClient module
vi.mock('../../api/workflowClient', () => ({
  fetchWorkflowsBatch: vi.fn(),
}));

import { fetchWorkflowsBatch } from '../../api/workflowClient';

const mockCurrentWorkflow: WorkflowHistoryItem = {
  id: 1,
  adw_id: 'current-123',
  status: 'completed',
  duration_seconds: 120,
  actual_cost_total: 0.0045,
  cache_efficiency_percent: 75.5,
  github_url: 'https://github.com/example/repo/pull/1',
  issue_number: 1,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  retry_count: 0,
  steps_completed: 10,
  steps_total: 10,
  concurrent_workflows: 1,
  worktree_reused: false,
  input_tokens: 1000,
  output_tokens: 500,
  cached_tokens: 200,
  cache_hit_tokens: 200,
  cache_miss_tokens: 300,
  total_tokens: 1500,
  estimated_cost_total: 0.0050,
  estimated_cost_per_step: 0.0005,
  actual_cost_per_step: 0.00045,
  cost_per_token: 0.000003,
  hour_of_day: 10,
  day_of_week: 2,
  nl_input_clarity_score: 85,
  cost_efficiency_score: 80,
  performance_score: 75,
  quality_score: 90,
};

const mockSimilarWorkflow1: WorkflowHistoryItem = {
  id: 2,
  adw_id: 'similar-456',
  status: 'completed',
  duration_seconds: 100,
  actual_cost_total: 0.0032,
  cache_efficiency_percent: 80.2,
  github_url: 'https://github.com/example/repo/pull/2',
  issue_number: 2,
  created_at: '2024-01-02T00:00:00Z',
  updated_at: '2024-01-02T00:00:00Z',
  retry_count: 0,
  steps_completed: 10,
  steps_total: 10,
  concurrent_workflows: 1,
  worktree_reused: false,
  input_tokens: 900,
  output_tokens: 450,
  cached_tokens: 180,
  cache_hit_tokens: 180,
  cache_miss_tokens: 270,
  total_tokens: 1350,
  estimated_cost_total: 0.0040,
  estimated_cost_per_step: 0.0004,
  actual_cost_per_step: 0.00032,
  cost_per_token: 0.000003,
  hour_of_day: 10,
  day_of_week: 2,
  nl_input_clarity_score: 85,
  cost_efficiency_score: 85,
  performance_score: 80,
  quality_score: 92,
};

const mockSimilarWorkflow2: WorkflowHistoryItem = {
  id: 3,
  adw_id: 'similar-789',
  status: 'failed',
  duration_seconds: 150,
  actual_cost_total: 0.0067,
  cache_efficiency_percent: 60.0,
  github_url: 'https://github.com/example/repo/pull/3',
  issue_number: 3,
  created_at: '2024-01-03T00:00:00Z',
  updated_at: '2024-01-03T00:00:00Z',
  retry_count: 2,
  steps_completed: 8,
  steps_total: 10,
  concurrent_workflows: 1,
  worktree_reused: false,
  input_tokens: 1200,
  output_tokens: 600,
  cached_tokens: 150,
  cache_hit_tokens: 150,
  cache_miss_tokens: 450,
  total_tokens: 1800,
  estimated_cost_total: 0.0060,
  estimated_cost_per_step: 0.0006,
  actual_cost_per_step: 0.000837,
  cost_per_token: 0.000003,
  hour_of_day: 14,
  day_of_week: 3,
  nl_input_clarity_score: 70,
  cost_efficiency_score: 65,
  performance_score: 60,
  quality_score: 55,
};

describe('SimilarWorkflowsComparison', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    (fetchWorkflowsBatch as any).mockImplementation(
      () => new Promise(() => {}) // Never resolves to keep loading state
    );

    render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={['similar-456']}
      />
    );

    expect(screen.getByText('Loading similar workflows...')).toBeInTheDocument();
  });

  it('renders "No similar workflows found" when similarWorkflowIds is empty array', async () => {
    (fetchWorkflowsBatch as any).mockResolvedValueOnce([mockCurrentWorkflow]);

    render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={[]}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('No similar workflows found')).toBeInTheDocument();
    });
  });

  it('fetches and displays similar workflows correctly', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockCurrentWorkflow] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockSimilarWorkflow1] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockSimilarWorkflow2] }),
      });

    render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={['similar-456', 'similar-789']}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('similar-456')).toBeInTheDocument();
      expect(screen.getByText('similar-789')).toBeInTheDocument();
    });
  });

  it('displays current workflow in highlighted blue row', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockCurrentWorkflow] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockSimilarWorkflow1] }),
      });

    render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={['similar-456']}
      />
    );

    await waitFor(() => {
      const currentRow = screen.getByText('(current)').closest('tr');
      expect(currentRow?.className).toContain('bg-blue-50');
      expect(screen.getByText('current-123')).toBeInTheDocument();
    });
  });

  it('shows comparison indicators (arrows) correctly for duration', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockCurrentWorkflow] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockSimilarWorkflow1] }), // 100s < 120s (better)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockSimilarWorkflow2] }), // 150s > 120s (worse)
      });

    render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={['similar-456', 'similar-789']}
      />
    );

    await waitFor(() => {
      const betterIndicator = screen.getAllByText('↓');
      expect(betterIndicator.length).toBeGreaterThan(0);

      const worseIndicator = screen.getAllByText('↑');
      expect(worseIndicator.length).toBeGreaterThan(0);
    });
  });

  it('handles API errors gracefully (shows error message)', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

    render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={['similar-456']}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });
  });

  it('formats duration correctly (e.g., "2m 30s")', async () => {
    const workflow = { ...mockSimilarWorkflow1, duration_seconds: 150 };

    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockCurrentWorkflow] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [workflow] }),
      });

    render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={['similar-456']}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('2m 30s')).toBeInTheDocument();
    });
  });

  it('formats cost correctly (e.g., "$0.0045")', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockCurrentWorkflow] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockSimilarWorkflow1] }),
      });

    render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={['similar-456']}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('$0.0045')).toBeInTheDocument();
      expect(screen.getByText('$0.0032')).toBeInTheDocument();
    });
  });

  it('handles missing/undefined values (shows "N/A")', async () => {
    const workflowWithMissingData = {
      ...mockSimilarWorkflow1,
      duration_seconds: undefined,
      actual_cost_total: undefined,
      cache_efficiency_percent: undefined,
    };

    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockCurrentWorkflow] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [workflowWithMissingData] }),
      });

    render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={['similar-456']}
      />
    );

    await waitFor(() => {
      const naElements = screen.getAllByText('N/A');
      expect(naElements.length).toBeGreaterThanOrEqual(3); // Duration, cost, cache efficiency
    });
  });

  it('GitHub links are clickable and have correct href', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockCurrentWorkflow] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockSimilarWorkflow1] }),
      });

    render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={['similar-456']}
      />
    );

    await waitFor(() => {
      const link = screen.getByText('similar-456').closest('a');
      expect(link).toHaveAttribute('href', 'https://github.com/example/repo/pull/2');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });

  it('handles many similar workflows (20+ IDs) without breaking', async () => {
    const manyWorkflowIds = Array.from({ length: 25 }, (_, i) => `workflow-${i}`);

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('current-123')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ workflows: [mockCurrentWorkflow] }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({
          workflows: [{
            ...mockSimilarWorkflow1,
            adw_id: url.split('search=')[1].split('&')[0],
          }],
        }),
      });
    });

    render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={manyWorkflowIds}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('workflow-0')).toBeInTheDocument();
      expect(screen.getByText('workflow-24')).toBeInTheDocument();
    });
  });

  it('renders table with correct headers', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockCurrentWorkflow] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockSimilarWorkflow1] }),
      });

    render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={['similar-456']}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Workflow')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Duration')).toBeInTheDocument();
      expect(screen.getByText('Cost')).toBeInTheDocument();
      expect(screen.getByText('Cache Eff.')).toBeInTheDocument();
    });
  });

  it('displays status badges with correct colors', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockCurrentWorkflow] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockSimilarWorkflow1] }), // completed
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockSimilarWorkflow2] }), // failed
      });

    render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={['similar-456', 'similar-789']}
      />
    );

    await waitFor(() => {
      const completedBadges = screen.getAllByText('completed');
      expect(completedBadges[0].className).toContain('bg-green-100');

      const failedBadge = screen.getByText('failed');
      expect(failedBadge.className).toContain('bg-red-100');
    });
  });

  it('displays legend for comparison indicators', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockCurrentWorkflow] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockSimilarWorkflow1] }),
      });

    render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={['similar-456']}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Legend:')).toBeInTheDocument();
      expect(screen.getByText(/Better than current/)).toBeInTheDocument();
      expect(screen.getByText(/Worse than current/)).toBeInTheDocument();
    });
  });

  it('handles cache efficiency comparison correctly (higher is better)', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockCurrentWorkflow] }), // 75.5%
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ workflows: [mockSimilarWorkflow1] }), // 80.2% (better)
      });

    render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={['similar-456']}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('80.2%')).toBeInTheDocument();
      // For cache efficiency, higher is better, so should show green up arrow
      const cacheCell = screen.getByText('80.2%').closest('td');
      const indicator = cacheCell?.querySelector('.text-green-600');
      expect(indicator).toBeInTheDocument();
      expect(indicator?.textContent).toBe('↑');
    });
  });

  it('cleans up fetch on unmount (no memory leak)', async () => {
    // Mock fetchWorkflowsBatch to return a promise that resolves after a delay
    let abortCalled = false;

    // Override AbortController.abort to track if it was called
    const originalAbort = AbortController.prototype.abort;
    AbortController.prototype.abort = function() {
      abortCalled = true;
      originalAbort.call(this);
    };

    // Mock fetch to never resolve (simulates slow network)
    (fetchWorkflowsBatch as any).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    // Suppress console warnings for this test
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

    const { unmount } = render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={['similar-456']}
      />
    );

    // Verify loading state appears
    expect(screen.getByText('Loading similar workflows...')).toBeInTheDocument();

    // Unmount the component before the promise resolves
    unmount();

    // Wait a bit to ensure any state updates would have been attempted
    await new Promise(resolve => setTimeout(resolve, 100));

    // Verify abort was called
    expect(abortCalled).toBe(true);

    // Verify no console errors occurred
    expect(consoleError).not.toHaveBeenCalledWith(
      expect.stringContaining('unmounted component')
    );

    // Restore original abort and console.error
    AbortController.prototype.abort = originalAbort;
    consoleError.mockRestore();
  });

  it('handles AbortError gracefully (no error UI shown)', async () => {
    // Mock fetchWorkflowsBatch to throw AbortError
    const abortError = new DOMException('The operation was aborted', 'AbortError');
    (fetchWorkflowsBatch as any).mockRejectedValueOnce(abortError);

    render(
      <SimilarWorkflowsComparison
        currentWorkflowId="current-123"
        similarWorkflowIds={['similar-456']}
      />
    );

    // Initially should show loading
    expect(screen.getByText('Loading similar workflows...')).toBeInTheDocument();

    // Wait a bit for the promise to reject and be handled
    await new Promise(resolve => setTimeout(resolve, 50));

    // The key assertion: verify no error message is displayed after AbortError
    expect(screen.queryByText(/Error:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/operation was aborted/i)).not.toBeInTheDocument();
  });
});
