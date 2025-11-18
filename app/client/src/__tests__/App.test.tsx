/**
 * App Component Tests
 *
 * Tests for tab persistence across page refreshes
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App';

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

describe('App', () => {
  beforeEach(() => {
    localStorageMock.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Tab Persistence', () => {
    it('should default to "request" tab when no saved tab', () => {
      render(<App />);

      // Request tab should be active (button has different styling)
      const requestTab = screen.getByText('New Requests');
      expect(requestTab.className).toContain('border-primary');
    });

    it('should load saved tab from localStorage on mount', () => {
      localStorageMock.setItem('tac-webbuilder-active-tab', 'workflows');

      render(<App />);

      // Workflows tab should be active
      const workflowsTab = screen.getByText('Workflows');
      expect(workflowsTab.className).toContain('border-primary');
    });

    it('should save active tab to localStorage when changed', async () => {
      render(<App />);

      // Initially on "request" tab
      expect(localStorageMock.getItem('tac-webbuilder-active-tab')).toBe('request');

      // Click on "Workflows" tab
      const workflowsTab = screen.getByText('Workflows');
      await userEvent.click(workflowsTab);

      // localStorage should be updated
      expect(localStorageMock.getItem('tac-webbuilder-active-tab')).toBe('workflows');
    });

    it('should persist tab selection across all tabs', async () => {
      render(<App />);

      // Test all tabs
      const tabs = ['Workflows', 'History', 'Routes', 'New Requests'];

      for (const tabName of tabs) {
        const tab = screen.getByText(tabName);
        await userEvent.click(tab);

        const expectedValue = tabName === 'New Requests' ? 'request' : tabName.toLowerCase();
        expect(localStorageMock.getItem('tac-webbuilder-active-tab')).toBe(expectedValue);
      }
    });

    it('should ignore invalid saved tab values', () => {
      localStorageMock.setItem('tac-webbuilder-active-tab', 'invalid-tab');

      render(<App />);

      // Should default to "request" tab
      const requestTab = screen.getByText('New Requests');
      expect(requestTab.className).toContain('border-primary');
    });

    it('should restore exact tab state after refresh simulation', () => {
      // First render - select History tab
      const { unmount } = render(<App />);
      const historyTab = screen.getByText('History');
      userEvent.click(historyTab);

      // Simulate page refresh by unmounting and remounting
      unmount();
      render(<App />);

      // History tab should still be active
      const newHistoryTab = screen.getByText('History');
      expect(newHistoryTab.className).toContain('border-primary');
    });
  });

  describe('Tab Navigation', () => {
    it('should render correct content for each tab', async () => {
      render(<App />);

      // New Requests tab
      expect(screen.getByText('Create New Request')).toBeInTheDocument();

      // Workflows tab
      await userEvent.click(screen.getByText('Workflows'));
      expect(screen.getByText(/Active Workflows/i)).toBeInTheDocument();

      // History tab
      await userEvent.click(screen.getByText('History'));
      expect(screen.getByText(/Workflow History/i)).toBeInTheDocument();

      // Routes tab
      await userEvent.click(screen.getByText('Routes'));
      expect(screen.getByText(/API Routes/i)).toBeInTheDocument();
    });

    it('should update active tab styling when clicked', async () => {
      render(<App />);

      const requestTab = screen.getByText('New Requests');
      const workflowsTab = screen.getByText('Workflows');

      // Initially request tab is active
      expect(requestTab.className).toContain('border-primary');
      expect(workflowsTab.className).toContain('border-transparent');

      // Click workflows tab
      await userEvent.click(workflowsTab);

      // Workflows tab should be active
      expect(workflowsTab.className).toContain('border-primary');
      expect(requestTab.className).toContain('border-transparent');
    });
  });

  describe('Regression Tests', () => {
    it('should render app header', () => {
      render(<App />);

      expect(screen.getByText('tac-webbuilder')).toBeInTheDocument();
      expect(screen.getByText('Build web apps with natural language')).toBeInTheDocument();
    });

    it('should render all navigation tabs', () => {
      render(<App />);

      expect(screen.getByText('New Requests')).toBeInTheDocument();
      expect(screen.getByText('Workflows')).toBeInTheDocument();
      expect(screen.getByText('History')).toBeInTheDocument();
      expect(screen.getByText('Routes')).toBeInTheDocument();
    });

    it('should maintain QueryClient provider', () => {
      render(<App />);

      // QueryClientProvider should wrap the app
      // This is tested implicitly by other components that use React Query
      expect(screen.getByText('tac-webbuilder')).toBeInTheDocument();
    });
  });
});
