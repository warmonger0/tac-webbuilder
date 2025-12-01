/**
 * Tests for PhaseQueueCard Component
 *
 * Tests pattern badge rendering and display logic.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PhaseQueueCard, PhaseQueueItem } from '../PhaseQueueCard';

// Mock API client
vi.mock('../../api/client', () => ({
  executePhase: vi.fn().mockResolvedValue({
    message: 'Phase execution started',
    adw_id: 'test-adw-id',
    issue_number: 123
  })
}));

const createMockQueueItem = (overrides?: Partial<PhaseQueueItem>): PhaseQueueItem => ({
  queue_id: 'test-queue-id',
  parent_issue: 100,
  phase_number: 1,
  status: 'ready',
  phase_data: {
    title: 'Test Phase',
    content: 'Test content'
  },
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  ...overrides
});

describe('PhaseQueueCard - Pattern Display', () => {
  it('displays predicted pattern badges when patterns exist', () => {
    const queueItem = createMockQueueItem({
      phase_data: {
        title: 'Test Phase',
        content: 'Run tests',
        predicted_patterns: ['test:pytest:backend', 'build:typecheck']
      }
    });

    render(<PhaseQueueCard queueItem={queueItem} />);

    // Expand to show patterns
    const expandButton = screen.getByTitle(/expand details/i);
    fireEvent.click(expandButton);

    // Verify pattern badges displayed
    expect(screen.getByText('test:pytest:backend')).toBeInTheDocument();
    expect(screen.getByText('build:typecheck')).toBeInTheDocument();
    expect(screen.getByText('Patterns:')).toBeInTheDocument();
  });

  it('hides pattern section when no patterns', () => {
    const queueItem = createMockQueueItem({
      phase_data: {
        title: 'Test Phase',
        content: 'Run tests'
        // No predicted_patterns
      }
    });

    render(<PhaseQueueCard queueItem={queueItem} />);

    // Expand card
    const expandButton = screen.getByTitle(/expand details/i);
    fireEvent.click(expandButton);

    // Pattern section should not appear
    expect(screen.queryByText(/Patterns:/i)).not.toBeInTheDocument();
  });

  it('hides pattern section when patterns array is empty', () => {
    const queueItem = createMockQueueItem({
      phase_data: {
        title: 'Test Phase',
        content: 'Run tests',
        predicted_patterns: []  // Empty array
      }
    });

    render(<PhaseQueueCard queueItem={queueItem} />);

    // Expand card
    const expandButton = screen.getByTitle(/expand details/i);
    fireEvent.click(expandButton);

    // Pattern section should not appear for empty array
    expect(screen.queryByText(/Patterns:/i)).not.toBeInTheDocument();
  });

  it('displays multiple pattern badges correctly', () => {
    const queueItem = createMockQueueItem({
      phase_data: {
        title: 'Complex Phase',
        content: 'Multi-operation phase',
        predicted_patterns: [
          'test:unit',
          'test:integration',
          'build:frontend',
          'build:backend',
          'deploy:staging'
        ]
      }
    });

    render(<PhaseQueueCard queueItem={queueItem} />);

    // Expand card
    const expandButton = screen.getByTitle(/expand details/i);
    fireEvent.click(expandButton);

    // All patterns should be displayed
    expect(screen.getByText('test:unit')).toBeInTheDocument();
    expect(screen.getByText('test:integration')).toBeInTheDocument();
    expect(screen.getByText('build:frontend')).toBeInTheDocument();
    expect(screen.getByText('build:backend')).toBeInTheDocument();
    expect(screen.getByText('deploy:staging')).toBeInTheDocument();
  });

  it('patterns have correct styling classes', () => {
    const queueItem = createMockQueueItem({
      phase_data: {
        title: 'Test Phase',
        content: 'Run tests',
        predicted_patterns: ['test:pytest']
      }
    });

    render(<PhaseQueueCard queueItem={queueItem} />);

    // Expand card
    const expandButton = screen.getByTitle(/expand details/i);
    fireEvent.click(expandButton);

    // Find pattern badge element
    const patternBadge = screen.getByText('test:pytest');

    // Verify emerald theme classes applied
    expect(patternBadge).toHaveClass('bg-emerald-500/20');
    expect(patternBadge).toHaveClass('text-emerald-300');
    expect(patternBadge).toHaveClass('border-emerald-500/30');
    expect(patternBadge).toHaveClass('rounded-md');
  });

  it('pattern badges have correct title attribute', () => {
    const queueItem = createMockQueueItem({
      phase_data: {
        title: 'Test Phase',
        content: 'Run tests',
        predicted_patterns: ['test:pytest']
      }
    });

    render(<PhaseQueueCard queueItem={queueItem} />);

    // Expand card
    const expandButton = screen.getByTitle(/expand details/i);
    fireEvent.click(expandButton);

    // Pattern badge should have title
    const patternBadge = screen.getByText('test:pytest');
    expect(patternBadge).toHaveAttribute('title', 'Predicted pattern');
  });

  it('patterns section appears after issue/PR badges', () => {
    const queueItem = createMockQueueItem({
      issue_number: 123,
      pr_number: 456,
      phase_data: {
        title: 'Test Phase',
        content: 'Run tests',
        predicted_patterns: ['test:pytest']
      }
    });

    render(<PhaseQueueCard queueItem={queueItem} />);

    // Expand card
    const expandButton = screen.getByTitle(/expand details/i);
    fireEvent.click(expandButton);

    // All elements should be present
    expect(screen.getByText('Open')).toBeInTheDocument();  // Issue badge
    expect(screen.getByText('#456')).toBeInTheDocument();  // PR badge
    expect(screen.getByText('Patterns:')).toBeInTheDocument();  // Patterns label
    expect(screen.getByText('test:pytest')).toBeInTheDocument();  // Pattern badge
  });

  it('patterns hidden when card collapsed', () => {
    const queueItem = createMockQueueItem({
      phase_data: {
        title: 'Test Phase',
        content: 'Run tests',
        predicted_patterns: ['test:pytest']
      }
    });

    render(<PhaseQueueCard queueItem={queueItem} />);

    // Pattern should not be visible initially (card collapsed)
    expect(screen.queryByText('test:pytest')).not.toBeInTheDocument();

    // Expand card
    const expandButton = screen.getByTitle(/expand details/i);
    fireEvent.click(expandButton);

    // Now pattern should be visible
    expect(screen.getByText('test:pytest')).toBeInTheDocument();

    // Collapse again
    const collapseButton = screen.getByTitle(/collapse details/i);
    fireEvent.click(collapseButton);

    // Pattern hidden again
    expect(screen.queryByText('test:pytest')).not.toBeInTheDocument();
  });

  it('handles long pattern names gracefully', () => {
    const queueItem = createMockQueueItem({
      phase_data: {
        title: 'Test Phase',
        content: 'Run tests',
        predicted_patterns: ['test:integration:api:authentication:oauth2:complex']
      }
    });

    render(<PhaseQueueCard queueItem={queueItem} />);

    // Expand card
    const expandButton = screen.getByTitle(/expand details/i);
    fireEvent.click(expandButton);

    // Long pattern name should be displayed
    expect(screen.getByText('test:integration:api:authentication:oauth2:complex')).toBeInTheDocument();
  });

  it('pattern section uses flex-wrap for proper layout', () => {
    const queueItem = createMockQueueItem({
      phase_data: {
        title: 'Test Phase',
        content: 'Run tests',
        predicted_patterns: ['test:pytest', 'build:npm']
      }
    });

    render(<PhaseQueueCard queueItem={queueItem} />);

    // Expand card
    const expandButton = screen.getByTitle(/expand details/i);
    fireEvent.click(expandButton);

    // Find the patterns container
    const patternsLabel = screen.getByText('Patterns:');
    const container = patternsLabel.parentElement;

    // Verify flex-wrap class
    expect(container).toHaveClass('flex-wrap');
  });

  it('displays patterns for different phase statuses', () => {
    const statuses: Array<'queued' | 'ready' | 'running' | 'completed' | 'blocked' | 'failed'> = [
      'queued', 'ready', 'running', 'completed', 'blocked', 'failed'
    ];

    statuses.forEach(status => {
      const queueItem = createMockQueueItem({
        status,
        phase_data: {
          title: 'Test Phase',
          content: 'Run tests',
          predicted_patterns: ['test:pytest']
        }
      });

      const { unmount } = render(<PhaseQueueCard queueItem={queueItem} />);

      // Expand card
      const expandButton = screen.getByTitle(/expand details/i);
      fireEvent.click(expandButton);

      // Pattern should be visible regardless of status
      expect(screen.getByText('test:pytest')).toBeInTheDocument();

      unmount();
    });
  });
});
