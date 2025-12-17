import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { ConfirmationDialog } from '../ConfirmationDialog';

describe('ConfirmationDialog', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onConfirm: vi.fn(),
    title: 'Confirm Action',
    message: 'Are you sure?',
  };

  it('renders nothing when isOpen is false', () => {
    const { container } = render(<ConfirmationDialog {...defaultProps} isOpen={false} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders dialog when isOpen is true', () => {
    render(<ConfirmationDialog {...defaultProps} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Confirm Action')).toBeInTheDocument();
    expect(screen.getByText('Are you sure?')).toBeInTheDocument();
  });

  it('calls onConfirm and onClose when confirm button clicked', () => {
    const onConfirm = vi.fn();
    const onClose = vi.fn();
    render(<ConfirmationDialog {...defaultProps} onConfirm={onConfirm} onClose={onClose} />);

    fireEvent.click(screen.getByText('Confirm'));

    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when cancel button clicked', () => {
    const onClose = vi.fn();
    render(<ConfirmationDialog {...defaultProps} onClose={onClose} />);

    fireEvent.click(screen.getByText('Cancel'));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when backdrop clicked', () => {
    const onClose = vi.fn();
    const { container } = render(<ConfirmationDialog {...defaultProps} onClose={onClose} />);

    const backdrop = container.querySelector('.bg-black.bg-opacity-50');
    fireEvent.click(backdrop!);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('renders custom button text', () => {
    render(
      <ConfirmationDialog
        {...defaultProps}
        confirmText="Delete"
        cancelText="Nevermind"
      />
    );

    expect(screen.getByText('Delete')).toBeInTheDocument();
    expect(screen.getByText('Nevermind')).toBeInTheDocument();
  });

  it('applies danger variant styling', () => {
    render(<ConfirmationDialog {...defaultProps} confirmVariant="danger" />);
    const confirmButton = screen.getByText('Confirm');
    expect(confirmButton).toHaveClass('bg-red-600');
  });
});
