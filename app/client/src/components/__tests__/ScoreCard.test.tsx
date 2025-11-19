import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ScoreCard } from '../ScoreCard';

describe('ScoreCard', () => {
  it('renders with green color for score 95 (90-100 range)', () => {
    render(
      <ScoreCard
        title="Cost Efficiency"
        score={95}
        description="Optimized cost performance"
      />
    );

    const container = screen.getByText('Cost Efficiency').closest('div');
    expect(container?.className).toContain('bg-green-50');
    expect(container?.className).toContain('border-green-200');
    expect(screen.getByText('95')).toBeInTheDocument();
  });

  it('renders with blue color for score 80 (70-89 range)', () => {
    render(
      <ScoreCard
        title="Performance"
        score={80}
        description="Good performance"
      />
    );

    const container = screen.getByText('Performance').closest('div');
    expect(container?.className).toContain('bg-blue-50');
    expect(container?.className).toContain('border-blue-200');
    expect(screen.getByText('80')).toBeInTheDocument();
  });

  it('renders with yellow color for score 60 (50-69 range)', () => {
    render(
      <ScoreCard
        title="Quality"
        score={60}
        description="Average quality"
      />
    );

    const container = screen.getByText('Quality').closest('div');
    expect(container?.className).toContain('bg-yellow-50');
    expect(container?.className).toContain('border-yellow-200');
    expect(screen.getByText('60')).toBeInTheDocument();
  });

  it('renders with orange color for score 30 (0-49 range)', () => {
    render(
      <ScoreCard
        title="Cost Efficiency"
        score={30}
        description="Needs improvement"
      />
    );

    const container = screen.getByText('Cost Efficiency').closest('div');
    expect(container?.className).toContain('bg-orange-50');
    expect(container?.className).toContain('border-orange-200');
    expect(screen.getByText('30')).toBeInTheDocument();
  });

  it('renders with orange color for score 0 (edge case: zero is valid poor score)', () => {
    render(
      <ScoreCard
        title="Quality"
        score={0}
        description="Poor quality"
      />
    );

    const container = screen.getByText('Quality').closest('div');
    expect(container?.className).toContain('bg-orange-50');
    expect(container?.className).toContain('border-orange-200');
    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  it('renders with green color for score 90 (boundary: lower bound of green range)', () => {
    render(
      <ScoreCard
        title="Performance"
        score={90}
        description="Excellent performance"
      />
    );

    const container = screen.getByText('Performance').closest('div');
    expect(container?.className).toContain('bg-green-50');
    expect(container?.className).toContain('border-green-200');
    expect(screen.getByText('90')).toBeInTheDocument();
  });

  it('renders with blue color for score 70 (boundary: lower bound of blue range)', () => {
    render(
      <ScoreCard
        title="Cost Efficiency"
        score={70}
        description="Decent efficiency"
      />
    );

    const container = screen.getByText('Cost Efficiency').closest('div');
    expect(container?.className).toContain('bg-blue-50');
    expect(container?.className).toContain('border-blue-200');
    expect(screen.getByText('70')).toBeInTheDocument();
  });

  it('renders with yellow color for score 50 (boundary: lower bound of yellow range)', () => {
    render(
      <ScoreCard
        title="Quality"
        score={50}
        description="Moderate quality"
      />
    );

    const container = screen.getByText('Quality').closest('div');
    expect(container?.className).toContain('bg-yellow-50');
    expect(container?.className).toContain('border-yellow-200');
    expect(screen.getByText('50')).toBeInTheDocument();
  });

  it('displays title correctly', () => {
    render(
      <ScoreCard
        title="Cost Efficiency"
        score={85}
        description="Test description"
      />
    );

    expect(screen.getByText('Cost Efficiency')).toBeInTheDocument();
  });

  it('displays description correctly', () => {
    render(
      <ScoreCard
        title="Performance"
        score={75}
        description="This is a test description"
      />
    );

    expect(screen.getByText('This is a test description')).toBeInTheDocument();
  });

  it('displays score number with correct formatting (rounds decimal)', () => {
    render(
      <ScoreCard
        title="Quality"
        score={85.7}
        description="Test"
      />
    );

    expect(screen.getByText('86')).toBeInTheDocument();
  });

  it('uses semantic HTML with heading', () => {
    render(
      <ScoreCard
        title="Cost Efficiency"
        score={85}
        description="Test description"
      />
    );

    const heading = screen.getByRole('heading', { level: 4 });
    expect(heading).toHaveTextContent('Cost Efficiency');
  });

  it('renders circular progress indicator (SVG)', () => {
    const { container } = render(
      <ScoreCard
        title="Performance"
        score={75}
        description="Test"
      />
    );

    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();

    const circles = container.querySelectorAll('circle');
    expect(circles).toHaveLength(2); // Background and progress circles
  });

  it('calculates circle progress offset correctly for score 100', () => {
    const { container } = render(
      <ScoreCard
        title="Quality"
        score={100}
        description="Perfect score"
      />
    );

    const progressCircle = container.querySelectorAll('circle')[1];
    expect(progressCircle).toBeInTheDocument();
    // For score 100, offset should be 0 (full circle)
    expect(progressCircle.getAttribute('stroke-dashoffset')).toBe('0');
  });

  it('calculates circle progress offset correctly for score 50', () => {
    const { container } = render(
      <ScoreCard
        title="Quality"
        score={50}
        description="Half score"
      />
    );

    const progressCircle = container.querySelectorAll('circle')[1];
    const circumference = 2 * Math.PI * 40; // radius = 40
    const expectedOffset = circumference - (50 / 100) * circumference;

    expect(progressCircle.getAttribute('stroke-dashoffset')).toBe(expectedOffset.toString());
  });
});
