/**
 * Unit tests for useDragAndDrop hook
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { useDragAndDrop } from '../useDragAndDrop';

// Mock the fileHandlers module
vi.mock('../../utils/fileHandlers', () => ({
  handleMultipleFiles: vi.fn(),
}));

describe('useDragAndDrop', () => {
  let mockOnContentReceived: ReturnType<typeof vi.fn>;
  let mockOnSuccess: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockOnContentReceived = vi.fn();
    mockOnSuccess = vi.fn();
    vi.clearAllMocks();
  });

  it('should initialize with correct default state', () => {
    const { result } = renderHook(() =>
      useDragAndDrop({ onContentReceived: mockOnContentReceived })
    );

    expect(result.current.isDragging).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.isReading).toBe(false);
    expect(result.current.dragHandlers).toBeDefined();
    expect(result.current.clearError).toBeDefined();
  });

  it('should provide all drag event handlers', () => {
    const { result } = renderHook(() =>
      useDragAndDrop({ onContentReceived: mockOnContentReceived })
    );

    const { dragHandlers } = result.current;

    expect(dragHandlers.onDragEnter).toBeDefined();
    expect(dragHandlers.onDragOver).toBeDefined();
    expect(dragHandlers.onDragLeave).toBeDefined();
    expect(dragHandlers.onDrop).toBeDefined();
  });

  it('should set isDragging to true on dragEnter with files', () => {
    const { result } = renderHook(() =>
      useDragAndDrop({ onContentReceived: mockOnContentReceived })
    );

    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer: {
        types: ['Files'],
      },
    } as any;

    act(() => {
      result.current.dragHandlers.onDragEnter(mockEvent);
    });

    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(mockEvent.stopPropagation).toHaveBeenCalled();
    expect(result.current.isDragging).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('should not set isDragging if no files are being dragged', () => {
    const { result } = renderHook(() =>
      useDragAndDrop({ onContentReceived: mockOnContentReceived })
    );

    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer: {
        types: ['text/plain'],
      },
    } as any;

    act(() => {
      result.current.dragHandlers.onDragEnter(mockEvent);
    });

    expect(result.current.isDragging).toBe(false);
  });

  it('should set dropEffect on dragOver', () => {
    const { result } = renderHook(() =>
      useDragAndDrop({ onContentReceived: mockOnContentReceived })
    );

    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer: {
        types: ['Files'],
        dropEffect: '',
      },
    } as any;

    act(() => {
      result.current.dragHandlers.onDragOver(mockEvent);
    });

    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(mockEvent.stopPropagation).toHaveBeenCalled();
    expect(mockEvent.dataTransfer.dropEffect).toBe('copy');
  });

  it('should set isDragging to false on dragLeave when leaving drop zone', () => {
    const { result } = renderHook(() =>
      useDragAndDrop({ onContentReceived: mockOnContentReceived })
    );

    // First set isDragging to true
    act(() => {
      result.current.dragHandlers.onDragEnter({
        preventDefault: vi.fn(),
        stopPropagation: vi.fn(),
        dataTransfer: { types: ['Files'] },
      } as any);
    });

    expect(result.current.isDragging).toBe(true);

    // Then simulate dragLeave
    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      currentTarget: document.createElement('div'),
      relatedTarget: null,
    } as any;

    act(() => {
      result.current.dragHandlers.onDragLeave(mockEvent);
    });

    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(result.current.isDragging).toBe(false);
  });

  it('should not set isDragging to false when moving to child element', () => {
    const { result } = renderHook(() =>
      useDragAndDrop({ onContentReceived: mockOnContentReceived })
    );

    // Set isDragging to true
    act(() => {
      result.current.dragHandlers.onDragEnter({
        preventDefault: vi.fn(),
        stopPropagation: vi.fn(),
        dataTransfer: { types: ['Files'] },
      } as any);
    });

    const container = document.createElement('div');
    const child = document.createElement('span');
    container.appendChild(child);

    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      currentTarget: container,
      relatedTarget: child,
    } as any;

    act(() => {
      result.current.dragHandlers.onDragLeave(mockEvent);
    });

    // Should still be dragging because we moved to a child element
    expect(result.current.isDragging).toBe(true);
  });

  it('should handle file drop successfully', async () => {
    const { handleMultipleFiles } = await import('../../utils/fileHandlers');

    (handleMultipleFiles as any).mockResolvedValue({
      content: '# Test Content',
      processedCount: 1,
      rejectedFiles: [],
    });

    const { result } = renderHook(() =>
      useDragAndDrop({
        onContentReceived: mockOnContentReceived,
        onSuccess: mockOnSuccess,
      })
    );

    const mockFile = new File(['test'], 'test.md', { type: 'text/markdown' });
    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer: {
        files: [mockFile],
      },
    } as any;

    await act(async () => {
      result.current.dragHandlers.onDrop(mockEvent);
      await waitFor(() => expect(result.current.isReading).toBe(false));
    });

    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(result.current.isDragging).toBe(false);
    expect(mockOnContentReceived).toHaveBeenCalledWith('# Test Content');
    expect(mockOnSuccess).toHaveBeenCalledWith('File uploaded successfully');
    expect(result.current.error).toBeNull();
  });

  it('should handle multiple files drop', async () => {
    const { handleMultipleFiles } = await import('../../utils/fileHandlers');

    (handleMultipleFiles as any).mockResolvedValue({
      content: '# File 1\n\n---\n\n# File 2',
      processedCount: 2,
      rejectedFiles: [],
    });

    const { result } = renderHook(() =>
      useDragAndDrop({
        onContentReceived: mockOnContentReceived,
        onSuccess: mockOnSuccess,
      })
    );

    const mockFiles = [
      new File(['test1'], 'test1.md', { type: 'text/markdown' }),
      new File(['test2'], 'test2.md', { type: 'text/markdown' }),
    ];

    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer: {
        files: mockFiles,
      },
    } as any;

    await act(async () => {
      result.current.dragHandlers.onDrop(mockEvent);
      await waitFor(() => expect(result.current.isReading).toBe(false));
    });

    expect(mockOnContentReceived).toHaveBeenCalledWith('# File 1\n\n---\n\n# File 2');
    expect(mockOnSuccess).toHaveBeenCalledWith('2 files uploaded successfully');
  });

  it('should handle rejected files in success message', async () => {
    const { handleMultipleFiles } = await import('../../utils/fileHandlers');

    (handleMultipleFiles as any).mockResolvedValue({
      content: '# Valid File',
      processedCount: 1,
      rejectedFiles: ['invalid.txt', 'doc.pdf'],
    });

    const { result } = renderHook(() =>
      useDragAndDrop({
        onContentReceived: mockOnContentReceived,
        onSuccess: mockOnSuccess,
      })
    );

    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer: {
        files: [new File(['test'], 'test.md', { type: 'text/markdown' })],
      },
    } as any;

    await act(async () => {
      result.current.dragHandlers.onDrop(mockEvent);
      await waitFor(() => expect(result.current.isReading).toBe(false));
    });

    expect(mockOnSuccess).toHaveBeenCalledWith(
      'File uploaded successfully. Rejected files: invalid.txt, doc.pdf'
    );
  });

  it('should set error when no valid files are dropped', async () => {
    const { handleMultipleFiles } = await import('../../utils/fileHandlers');

    (handleMultipleFiles as any).mockResolvedValue({
      content: '',
      processedCount: 0,
      rejectedFiles: ['invalid.txt'],
    });

    const { result } = renderHook(() =>
      useDragAndDrop({ onContentReceived: mockOnContentReceived })
    );

    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer: {
        files: [new File(['test'], 'invalid.txt', { type: 'text/plain' })],
      },
    } as any;

    await act(async () => {
      result.current.dragHandlers.onDrop(mockEvent);
      await waitFor(() => expect(result.current.isReading).toBe(false));
    });

    expect(result.current.error).toContain('No valid .md files found');
    expect(result.current.error).toContain('invalid.txt');
    expect(mockOnContentReceived).not.toHaveBeenCalled();
  });

  it('should set error when file reading fails', async () => {
    const { handleMultipleFiles } = await import('../../utils/fileHandlers');

    (handleMultipleFiles as any).mockRejectedValue(new Error('Read failed'));

    const { result } = renderHook(() =>
      useDragAndDrop({ onContentReceived: mockOnContentReceived })
    );

    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer: {
        files: [new File(['test'], 'test.md', { type: 'text/markdown' })],
      },
    } as any;

    await act(async () => {
      result.current.dragHandlers.onDrop(mockEvent);
      await waitFor(() => expect(result.current.isReading).toBe(false));
    });

    expect(result.current.error).toBe('Read failed');
    expect(mockOnContentReceived).not.toHaveBeenCalled();
  });

  it('should set error when no files are dropped', async () => {
    const { result } = renderHook(() =>
      useDragAndDrop({ onContentReceived: mockOnContentReceived })
    );

    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer: {
        files: [],
      },
    } as any;

    await act(async () => {
      result.current.dragHandlers.onDrop(mockEvent);
    });

    expect(result.current.error).toBe('No files were dropped');
    expect(mockOnContentReceived).not.toHaveBeenCalled();
  });

  it('should clear error when clearError is called', () => {
    const { result } = renderHook(() =>
      useDragAndDrop({ onContentReceived: mockOnContentReceived })
    );

    // Set an error first
    act(() => {
      result.current.dragHandlers.onDrop({
        preventDefault: vi.fn(),
        stopPropagation: vi.fn(),
        dataTransfer: { files: [] },
      } as any);
    });

    expect(result.current.error).not.toBeNull();

    // Clear the error
    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });

  it('should set isReading to true during file processing', async () => {
    const { handleMultipleFiles } = await import('../../utils/fileHandlers');

    let resolvePromise: (value: any) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    (handleMultipleFiles as any).mockReturnValue(promise);

    const { result } = renderHook(() =>
      useDragAndDrop({ onContentReceived: mockOnContentReceived })
    );

    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer: {
        files: [new File(['test'], 'test.md', { type: 'text/markdown' })],
      },
    } as any;

    act(() => {
      result.current.dragHandlers.onDrop(mockEvent);
    });

    // Should be reading immediately after drop
    await waitFor(() => expect(result.current.isReading).toBe(true));

    // Resolve the promise
    await act(async () => {
      resolvePromise!({
        content: '# Test',
        processedCount: 1,
        rejectedFiles: [],
      });
      await promise;
    });

    // Should not be reading after completion
    expect(result.current.isReading).toBe(false);
  });
});
