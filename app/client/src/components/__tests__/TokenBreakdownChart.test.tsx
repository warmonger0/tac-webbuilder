/**
 * TokenBreakdownChart Component Tests
 *
 * Tests for rendering, formatting, and handling edge cases
 */

import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TokenBreakdownChart } from '../TokenBreakdownChart';

describe('TokenBreakdownChart', () => {
  describe('Rendering', () => {
    it('should render chart with full token data', () => {
      render(
        <TokenBreakdownChart
          inputTokens={10000}
          outputTokens={5000}
          cachedTokens={8000}
          cacheHitTokens={7000}
          cacheMissTokens={3000}
          totalTokens={25000}
        />
      );

      expect(screen.getByText('Token Breakdown')).toBeInTheDocument();
      expect(screen.getByText(/Total: 25\.0K/)).toBeInTheDocument();
    });

    it('should display fallback message when total tokens is zero', () => {
      render(
        <TokenBreakdownChart
          inputTokens={0}
          outputTokens={0}
          cachedTokens={0}
          cacheHitTokens={0}
          cacheMissTokens={0}
          totalTokens={0}
        />
      );

      expect(screen.getByText('No token data available')).toBeInTheDocument();
    });

    it('should handle missing data gracefully', () => {
      render(
        <TokenBreakdownChart
          inputTokens={0}
          outputTokens={0}
          cachedTokens={0}
          cacheHitTokens={0}
          cacheMissTokens={0}
          totalTokens={0}
        />
      );

      expect(screen.getByText('No token data available')).toBeInTheDocument();
    });
  });

  describe('Token Count Formatting', () => {
    it('should format small numbers without suffix', () => {
      render(
        <TokenBreakdownChart
          inputTokens={500}
          outputTokens={400}
          cachedTokens={0}
          cacheHitTokens={0}
          cacheMissTokens={0}
          totalTokens={900}
        />
      );

      expect(screen.getByText(/Total: 900/)).toBeInTheDocument();
    });

    it('should format thousands with K suffix', () => {
      render(
        <TokenBreakdownChart
          inputTokens={45000}
          outputTokens={200}
          cachedTokens={0}
          cacheHitTokens={0}
          cacheMissTokens={0}
          totalTokens={45200}
        />
      );

      expect(screen.getByText(/Total: 45\.2K/)).toBeInTheDocument();
    });

    it('should format millions with M suffix', () => {
      render(
        <TokenBreakdownChart
          inputTokens={1234567}
          outputTokens={100000}
          cachedTokens={0}
          cacheHitTokens={0}
          cacheMissTokens={0}
          totalTokens={1334567}
        />
      );

      expect(screen.getByText(/Total: 1\.3M/)).toBeInTheDocument();
    });

    it('should handle boundary case at exactly 1000', () => {
      render(
        <TokenBreakdownChart
          inputTokens={1000}
          outputTokens={0}
          cachedTokens={0}
          cacheHitTokens={0}
          cacheMissTokens={0}
          totalTokens={1000}
        />
      );

      expect(screen.getByText(/Total: 1\.0K/)).toBeInTheDocument();
    });

    it('should handle boundary case near 1 million', () => {
      render(
        <TokenBreakdownChart
          inputTokens={999999}
          outputTokens={0}
          cachedTokens={0}
          cacheHitTokens={0}
          cacheMissTokens={0}
          totalTokens={999999}
        />
      );

      expect(screen.getByText(/Total: 1000K/)).toBeInTheDocument();
    });
  });

  describe('Data Display', () => {
    it('should display all token types when provided', () => {
      render(
        <TokenBreakdownChart
          inputTokens={1000}
          outputTokens={2000}
          cachedTokens={3000}
          cacheHitTokens={4000}
          cacheMissTokens={5000}
          totalTokens={15000}
        />
      );

      // Chart component should render with header
      expect(screen.getByText('Token Breakdown')).toBeInTheDocument();
      expect(screen.getByText(/Total: 15\.0K/)).toBeInTheDocument();
    });

    it('should handle zero values for some token types', () => {
      render(
        <TokenBreakdownChart
          inputTokens={5000}
          outputTokens={0}
          cachedTokens={0}
          cacheHitTokens={0}
          cacheMissTokens={0}
          totalTokens={5000}
        />
      );

      expect(screen.getByText('Token Breakdown')).toBeInTheDocument();
      expect(screen.getByText(/Total: 5\.0K/)).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle very small token counts', () => {
      render(
        <TokenBreakdownChart
          inputTokens={1}
          outputTokens={1}
          cachedTokens={1}
          cacheHitTokens={0}
          cacheMissTokens={0}
          totalTokens={3}
        />
      );

      expect(screen.getByText(/Total: 3/)).toBeInTheDocument();
    });

    it('should handle very large token counts', () => {
      render(
        <TokenBreakdownChart
          inputTokens={10000000}
          outputTokens={5000000}
          cachedTokens={3000000}
          cacheHitTokens={2000000}
          cacheMissTokens={1000000}
          totalTokens={21000000}
        />
      );

      expect(screen.getByText(/Total: 21\.0M/)).toBeInTheDocument();
    });
  });
});
