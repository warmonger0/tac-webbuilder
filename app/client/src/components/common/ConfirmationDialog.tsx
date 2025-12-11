import React, { useEffect } from 'react';

interface ConfirmationDialogProps {
  /** Whether dialog is open */
  isOpen: boolean;

  /** Callback when dialog should close */
  onClose: () => void;

  /** Callback when user confirms */
  onConfirm: () => void;

  /** Dialog title */
  title: string;

  /** Dialog message */
  message: string;

  /** Text for confirm button */
  confirmText?: string;

  /** Text for cancel button */
  cancelText?: string;

  /** Variant for confirm button */
  confirmVariant?: 'danger' | 'primary';
}

/**
 * Standardized confirmation dialog component.
 *
 * @example
 * ```tsx
 * <ConfirmationDialog
 *   isOpen={showConfirm}
 *   onClose={() => setShowConfirm(false)}
 *   onConfirm={handleDelete}
 *   title="Delete Entry?"
 *   message="This action cannot be undone."
 *   confirmText="Delete"
 *   confirmVariant="danger"
 * />
 * ```
 */
export const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmVariant = 'primary',
}) => {
  // Handle Escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const confirmClasses =
    confirmVariant === 'danger'
      ? 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500'
      : 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500';

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
      >
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <h3 id="dialog-title" className="text-lg font-semibold text-gray-900 mb-3">
            {title}
          </h3>
          <p className="text-sm text-gray-700 mb-6">{message}</p>

          <div className="flex gap-3 justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-400"
            >
              {cancelText}
            </button>
            <button
              onClick={handleConfirm}
              className={`px-4 py-2 text-sm font-medium rounded-md focus:outline-none focus:ring-2 ${confirmClasses}`}
            >
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    </>
  );
};
