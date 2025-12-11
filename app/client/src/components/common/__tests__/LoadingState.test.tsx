import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LoadingState } from '../LoadingState';

describe('LoadingState', () => {
  it('renders with default message', () => {
    render(<LoadingState />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders with custom message', () => {
    render(<LoadingState message="Please wait..." />);
    expect(screen.getByText('Please wait...')).toBeInTheDocument();
  });

  it('renders different sizes', () => {
    const { rerender } = render(<LoadingState size="small" />);
    expect(screen.getByRole('status')).toHaveClass('h-4');

    rerender(<LoadingState size="large" />);
    expect(screen.getByRole('status')).toHaveClass('h-12');
  });

  it('applies custom className', () => {
    const { container } = render(<LoadingState className="my-custom-class" />);
    expect(container.firstChild).toHaveClass('my-custom-class');
  });
});
