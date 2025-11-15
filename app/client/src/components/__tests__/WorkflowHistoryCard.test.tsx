import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { WorkflowHistoryCard } from '../WorkflowHistoryCard';
import { WorkflowHistoryItem } from '../../types';

// Mock child components to isolate WorkflowHistoryCard testing
vi.mock('../ScoreCard', () => ({
  ScoreCard: ({ title, score }: { title: string; score: number }) => (
    <div data-testid="score-card">{title}: {score}</div>
  ),
}));

vi.mock('../SimilarWorkflowsComparison', () => ({
  SimilarWorkflowsComparison: ({ similarWorkflowIds }: { similarWorkflowIds: string[] }) => (
    <div data-testid="similar-workflows">Similar: {similarWorkflowIds.join(', ')}</div>
  ),
}));

const baseWorkflow: WorkflowHistoryItem = {
  id: 1,
  adw_id: 'test-123',
  issue_number: 42,
  status: 'completed',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  actual_cost_total: 0.0045,
  duration_seconds: 120,
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
  cache_efficiency_percent: 75,
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

const workflowWithPhase3Data: WorkflowHistoryItem = {
  ...baseWorkflow,
  cost_efficiency_score: 85,
  performance_score: 72,
  quality_score: 95,
  anomaly_flags: [
    'Cost 1.6x higher than average for similar workflows',
    'Unusual retry count (3 retries detected)',
  ],
  optimization_recommendations: [
    'Consider using Haiku model for similar simple features',
    'Cache efficiency is low (45%) - review prompt structure',
  ],
  similar_workflow_ids: ['abc123', 'def456', 'ghi789'],
  scoring_version: '1.0',
};

describe('WorkflowHistoryCard - Phase 3 Integration', () => {
  it('renders workflow card in collapsed state by default', () => {
    render(<WorkflowHistoryCard workflow={baseWorkflow} />);

    expect(screen.getByText(/test-123/)).toBeInTheDocument();
    expect(screen.getByText('▶ Show Details')).toBeInTheDocument();
  });

  it('expands to show Phase 3 Efficiency Scores section when clicked', async () => {
    const user = userEvent.setup();
    render(<WorkflowHistoryCard workflow={baseWorkflow} />);

    const expandButton = screen.getByText('▶ Show Details');
    await user.click(expandButton);

    expect(screen.getByText('📊 Efficiency Scores')).toBeInTheDocument();
    expect(screen.getByText('Cost Efficiency: 80')).toBeInTheDocument();
    expect(screen.getByText('Performance: 75')).toBeInTheDocument();
    expect(screen.getByText('Quality: 90')).toBeInTheDocument();
  });

  it('shows all Phase 3 sections when workflow has complete analytics data', async () => {
    const user = userEvent.setup();
    render(<WorkflowHistoryCard workflow={workflowWithPhase3Data} />);

    await user.click(screen.getByText('▶ Show Details'));

    // Efficiency Scores section
    expect(screen.getByText('📊 Efficiency Scores')).toBeInTheDocument();
    expect(screen.getByText('Cost Efficiency: 85')).toBeInTheDocument();
    expect(screen.getByText('Performance: 72')).toBeInTheDocument();
    expect(screen.getByText('Quality: 95')).toBeInTheDocument();

    // Insights & Recommendations section
    expect(screen.getByText('💡 Insights & Recommendations')).toBeInTheDocument();
    expect(screen.getByText('⚠️ Anomalies Detected')).toBeInTheDocument();
    expect(screen.getByText('Cost 1.6x higher than average for similar workflows')).toBeInTheDocument();
    expect(screen.getByText('✅ Optimization Tips')).toBeInTheDocument();
    expect(screen.getByText('Consider using Haiku model for similar simple features')).toBeInTheDocument();

    // Similar Workflows section
    expect(screen.getByText('🔗 Similar Workflows')).toBeInTheDocument();
    expect(screen.getByText('Found 3 similar workflows')).toBeInTheDocument();
    expect(screen.getByText('Similar: abc123, def456, ghi789')).toBeInTheDocument();
  });

  it('hides Insights section when no anomalies or recommendations exist', async () => {
    const user = userEvent.setup();
    const workflowWithoutInsights = {
      ...baseWorkflow,
      anomaly_flags: [],
      optimization_recommendations: [],
    };

    render(<WorkflowHistoryCard workflow={workflowWithoutInsights} />);
    await user.click(screen.getByText('▶ Show Details'));

    expect(screen.queryByText('💡 Insights & Recommendations')).not.toBeInTheDocument();
  });

  it('hides Similar Workflows section when no similar workflows exist', async () => {
    const user = userEvent.setup();
    const workflowWithoutSimilar = {
      ...baseWorkflow,
      similar_workflow_ids: [],
    };

    render(<WorkflowHistoryCard workflow={workflowWithoutSimilar} />);
    await user.click(screen.getByText('▶ Show Details'));

    expect(screen.queryByText('🔗 Similar Workflows')).not.toBeInTheDocument();
  });

  it('renders anomaly alerts with proper structure', async () => {
    const user = userEvent.setup();
    const workflowWithAnomalies = {
      ...baseWorkflow,
      anomaly_flags: ['Test anomaly 1', 'Test anomaly 2'],
    };

    render(<WorkflowHistoryCard workflow={workflowWithAnomalies} />);
    await user.click(screen.getByText('▶ Show Details'));

    expect(screen.getByText('⚠️ Anomalies Detected')).toBeInTheDocument();
    expect(screen.getByText('Test anomaly 1')).toBeInTheDocument();
    expect(screen.getByText('Test anomaly 2')).toBeInTheDocument();
  });

  it('renders optimization recommendations with proper structure', async () => {
    const user = userEvent.setup();
    const workflowWithRecommendations = {
      ...baseWorkflow,
      optimization_recommendations: ['Tip 1', 'Tip 2'],
    };

    render(<WorkflowHistoryCard workflow={workflowWithRecommendations} />);
    await user.click(screen.getByText('▶ Show Details'));

    expect(screen.getByText('✅ Optimization Tips')).toBeInTheDocument();
    expect(screen.getByText('Tip 1')).toBeInTheDocument();
    expect(screen.getByText('Tip 2')).toBeInTheDocument();
  });

  it('handles collapse after expansion', async () => {
    const user = userEvent.setup();
    render(<WorkflowHistoryCard workflow={baseWorkflow} />);

    // Expand
    await user.click(screen.getByText('▶ Show Details'));
    expect(screen.getByText('📊 Efficiency Scores')).toBeInTheDocument();

    // Collapse
    await user.click(screen.getByText('▼ Hide Details'));
    expect(screen.queryByText('📊 Efficiency Scores')).not.toBeInTheDocument();
  });
});
