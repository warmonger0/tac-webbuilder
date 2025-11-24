import { useRef, useState } from 'react';
import { handleMultipleFiles } from '../../utils/fileHandlers';
import { parsePhases, type PhaseParseResult } from '../../utils/phaseParser';

interface FileUploadSectionProps {
  /** Callback when file content is processed */
  onContentReceived: (content: string) => void;
  /** Callback when multi-phase document is detected */
  onPhasePreviewOpen: (parseResult: PhaseParseResult) => void;
  /** Whether drag and drop is active */
  isDragging: boolean;
  /** Error from drag and drop operation */
  dragError: string | null;
  /** Whether file is being read */
  isReading: boolean;
  /** Clear drag error */
  clearDragError: () => void;
  /** Current NL input value (to check if we should append) */
  currentNlInput: string;
}

export function FileUploadSection({
  onContentReceived,
  onPhasePreviewOpen,
  isDragging,
  dragError,
  isReading,
  clearDragError,
  currentNlInput
}: FileUploadSectionProps) {
  const [uploadSuccessMessage, setUploadSuccessMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setError(null);
    clearDragError();

    try {
      const result = await handleMultipleFiles(Array.from(files));

      if (result.content === '' && result.processedCount === 0) {
        if (result.rejectedFiles.length > 0) {
          // Show the first error message (most relevant for single file uploads)
          setError(result.rejectedFiles[0].errorMessage);
        } else {
          setError('No valid files to process');
        }
        return;
      }

      // Parse content for phases (only for single file uploads)
      if (result.processedCount === 1) {
        const parseResult = parsePhases(result.content);

        // If multi-phase detected, show preview for confirmation
        if (parseResult.isMultiPhase && parseResult.phases.length > 1) {
          onPhasePreviewOpen(parseResult);

          // Build success message
          setUploadSuccessMessage(`Multi-phase document detected with ${parseResult.phases.length} phases`);
          setTimeout(() => setUploadSuccessMessage(null), 3000);

          // Reset file input
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
          return;
        }
      }

      // Single-phase or multiple files: append content normally
      if (currentNlInput.trim()) {
        onContentReceived('\n\n---\n\n' + result.content);
      } else {
        onContentReceived(result.content);
      }

      // Build success message
      let successMsg = '';
      if (result.processedCount === 1) {
        successMsg = 'File uploaded successfully';
      } else {
        successMsg = `${result.processedCount} files uploaded successfully`;
      }

      if (result.rejectedFiles.length > 0) {
        const rejectedNames = result.rejectedFiles.map(f => f.fileName).join(', ');
        successMsg += `. Rejected files: ${rejectedNames}`;
      }

      setUploadSuccessMessage(successMsg);
      setTimeout(() => setUploadSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to read file(s)');
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-2">
      {/* File upload button (keyboard accessibility) */}
      <div className="flex items-center gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept=".md,.markdown"
          multiple
          onChange={handleFileInputChange}
          className="hidden"
          id="file-upload"
          aria-label="Upload markdown files"
        />
        <label
          htmlFor="file-upload"
          className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus-within:ring-2 focus-within:ring-primary focus-within:ring-offset-2 cursor-pointer transition-colors"
        >
          <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          Upload .md file
        </label>
        <span className="text-xs text-gray-500">or drag and drop anywhere</span>
      </div>

      {/* Drag-and-drop and file input error messages */}
      {(dragError || error) && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
          {dragError || error}
        </div>
      )}

      {/* Upload success message */}
      {uploadSuccessMessage && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-800 text-sm">
          {uploadSuccessMessage}
        </div>
      )}

      {/* Drop zone overlay */}
      {isDragging && (
        <div className="absolute inset-0 flex items-center justify-center bg-blue-50 bg-opacity-95 border-2 border-dashed border-primary rounded-lg pointer-events-none z-10">
          <div className="text-center">
            <svg className="mx-auto h-16 w-16 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="mt-3 text-lg font-semibold text-primary">Drop .md file anywhere on this card</p>
            <p className="mt-1 text-sm text-gray-600">Supports multiple files</p>
          </div>
        </div>
      )}

      {/* Loading overlay */}
      {isReading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-95 rounded-lg z-10">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-3 text-base font-medium text-gray-700">Reading file(s)...</p>
          </div>
        </div>
      )}
    </div>
  );
}
