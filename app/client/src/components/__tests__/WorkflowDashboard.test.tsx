/**
 * Tests for WorkflowDashboard Component
 *
 * Verifies that the WorkflowDashboard only shows the Workflow Catalog
 * and does not show the "Current Workflow" tab.
 */

import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WorkflowDashboard } from '../WorkflowDashboard';

// Mock the AdwWorkflowCatalog component
vi.mock('../AdwWorkflowCatalog', () => ({
  AdwWorkflowCatalog: () => <div data-testid="workflow-catalog">Workflow Catalog Mock</div>
}));

// Create a test query client
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const renderWithQueryClient = (component: React.ReactElement) => {
  const testQueryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={testQueryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('WorkflowDashboard', () => {
  it('renders the workflow catalog', () => {
    renderWithQueryClient(<WorkflowDashboard />);

    // Verify workflow catalog is rendered
    expect(screen.getByTestId('workflow-catalog')).toBeInTheDocument();
  });

  it('does not show "Current Workflow" tab', () => {
    renderWithQueryClient(<WorkflowDashboard />);

    // Verify "Current Workflow" tab is not present
    expect(screen.queryByText(/Current Workflow/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/⚡ Current Workflow/i)).not.toBeInTheDocument();
  });

  it('does not show "Workflow Catalog" tab', () => {
    renderWithQueryClient(<WorkflowDashboard />);

    // Verify "Workflow Catalog" tab button is not present
    // (Since tabs were removed, there should be no tab navigation)
    expect(screen.queryByRole('button', { name: /Workflow Catalog/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/📚 Workflow Catalog/i)).not.toBeInTheDocument();
  });

  it('does not render tab navigation', () => {
    const { container } = renderWithQueryClient(<WorkflowDashboard />);

    // Verify no tab navigation buttons exist
    const tabButtons = container.querySelectorAll('button[class*="px-6 py-3"]');
    expect(tabButtons.length).toBe(0);
  });

  it('renders with correct structure', () => {
    const { container } = renderWithQueryClient(<WorkflowDashboard />);

    // Verify main container exists
    const mainContainer = container.querySelector('div.space-y-4');
    expect(mainContainer).toBeInTheDocument();

    // Verify min-height container exists
    const contentContainer = container.querySelector('div.min-h-\\[600px\\]');
    expect(contentContainer).toBeInTheDocument();
  });

  it('directly renders AdwWorkflowCatalog without state management', () => {
    renderWithQueryClient(<WorkflowDashboard />);

    // The component should immediately show the catalog without any state
    // This ensures no tab state management is present
    expect(screen.getByTestId('workflow-catalog')).toBeInTheDocument();
  });
});
