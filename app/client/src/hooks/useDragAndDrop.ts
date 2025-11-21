/**
 * Custom React hook for managing drag-and-drop state and event handlers
 * Provides file validation, content extraction, and error handling for markdown files
 */

import { DragEvent, useCallback, useState } from 'react';
import { handleMultipleFiles } from '../utils/fileHandlers';

export interface UseDragAndDropOptions {
  /**
   * Callback invoked when valid file content is received
   */
  onContentReceived: (content: string) => void;

  /**
   * Optional callback for successful file processing
   */
  onSuccess?: (message: string) => void;
}

export interface DragHandlers {
  onDragEnter: (e: DragEvent<HTMLElement>) => void;
  onDragOver: (e: DragEvent<HTMLElement>) => void;
  onDragLeave: (e: DragEvent<HTMLElement>) => void;
  onDrop: (e: DragEvent<HTMLElement>) => void;
}

export interface UseDragAndDropResult {
  /**
   * True when a file is being dragged over the drop zone
   */
  isDragging: boolean;

  /**
   * Error message if file validation or reading fails
   */
  error: string | null;

  /**
   * True while file content is being read
   */
  isReading: boolean;

  /**
   * Event handlers to spread onto drop zone elements
   */
  dragHandlers: DragHandlers;

  /**
   * Manually clear error state
   */
  clearError: () => void;
}

/**
 * Custom hook for drag-and-drop file handling
 */
export function useDragAndDrop(options: UseDragAndDropOptions): UseDragAndDropResult {
  const { onContentReceived, onSuccess } = options;

  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isReading, setIsReading] = useState(false);

  const handleDragEnter = useCallback((e: DragEvent<HTMLElement>) => {
    e.preventDefault();
    e.stopPropagation();

    // Only set dragging if files are being dragged
    if (e.dataTransfer.types.includes('Files')) {
      setIsDragging(true);
      setError(null);
    }
  }, []);

  const handleDragOver = useCallback((e: DragEvent<HTMLElement>) => {
    e.preventDefault();
    e.stopPropagation();

    // Set dropEffect to copy to show proper cursor
    if (e.dataTransfer.types.includes('Files')) {
      e.dataTransfer.dropEffect = 'copy';
    }
  }, []);

  const handleDragLeave = useCallback((e: DragEvent<HTMLElement>) => {
    e.preventDefault();
    e.stopPropagation();

    // Only set dragging to false if we're leaving the drop zone entirely
    // Check if the related target is outside the current target
    const target = e.currentTarget;
    const relatedTarget = e.relatedTarget as Node | null;

    if (!relatedTarget || !target.contains(relatedTarget)) {
      setIsDragging(false);
    }
  }, []);

  const handleDrop = useCallback(async (e: DragEvent<HTMLElement>) => {
    e.preventDefault();
    e.stopPropagation();

    setIsDragging(false);
    setError(null);

    const files = Array.from(e.dataTransfer.files);

    if (files.length === 0) {
      setError('No files were dropped');
      return;
    }

    setIsReading(true);

    try {
      const result = await handleMultipleFiles(files);

      if (result.content === '' && result.processedCount === 0) {
        setError(
          result.rejectedFiles.length > 0
            ? `No valid .md files found. Rejected files: ${result.rejectedFiles.join(', ')}`
            : 'No valid files to process'
        );
        return;
      }

      // Call the content received callback
      onContentReceived(result.content);

      // Build success message
      let successMsg = '';
      if (result.processedCount === 1) {
        successMsg = 'File uploaded successfully';
      } else {
        successMsg = `${result.processedCount} files uploaded successfully`;
      }

      if (result.rejectedFiles.length > 0) {
        successMsg += `. Rejected files: ${result.rejectedFiles.join(', ')}`;
      }

      // Call success callback if provided
      if (onSuccess) {
        onSuccess(successMsg);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to read file(s)';
      setError(errorMessage);
    } finally {
      setIsReading(false);
    }
  }, [onContentReceived, onSuccess]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const dragHandlers: DragHandlers = {
    onDragEnter: handleDragEnter,
    onDragOver: handleDragOver,
    onDragLeave: handleDragLeave,
    onDrop: handleDrop,
  };

  return {
    isDragging,
    error,
    isReading,
    dragHandlers,
    clearError,
  };
}
