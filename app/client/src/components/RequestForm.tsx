import { useEffect, useRef, useState } from 'react';
import { confirmAndPost, getCostEstimate, getPreview, getSystemStatus, submitRequest } from '../api/client';
import type { CostEstimate, GitHubIssue, RequestFormPersistedState, ServiceHealth } from '../types';
import { IssuePreview } from './IssuePreview';
import { CostEstimateCard } from './CostEstimateCard';
import { ConfirmDialog } from './ConfirmDialog';
import { SystemStatusPanel } from './SystemStatusPanel';
import { ZteHopperQueueCard } from './ZteHopperQueueCard';
import { useDragAndDrop } from '../hooks/useDragAndDrop';

const PROJECT_PATH_STORAGE_KEY = 'tac-webbuilder-project-path';
const REQUEST_FORM_STATE_STORAGE_KEY = 'tac-webbuilder-request-form-state';
const REQUEST_FORM_STATE_VERSION = 1;

// Storage utility functions
function saveFormState(state: Omit<RequestFormPersistedState, 'version' | 'timestamp'>): void {
  try {
    const persistedState: RequestFormPersistedState = {
      version: REQUEST_FORM_STATE_VERSION,
      timestamp: new Date().toISOString(),
      ...state,
    };
    localStorage.setItem(REQUEST_FORM_STATE_STORAGE_KEY, JSON.stringify(persistedState));
  } catch (err) {
    // Handle quota exceeded or unavailable storage
    console.error('Failed to save form state:', err);
    throw err;
  }
}

function loadFormState(): RequestFormPersistedState | null {
  try {
    const savedData = localStorage.getItem(REQUEST_FORM_STATE_STORAGE_KEY);
    if (!savedData) {
      return null;
    }

    const parsed = JSON.parse(savedData);

    // Validate structure and version
    if (!validateFormState(parsed)) {
      console.warn('Invalid form state found, ignoring');
      return null;
    }

    return parsed as RequestFormPersistedState;
  } catch (err) {
    console.error('Failed to load form state:', err);
    return null;
  }
}

function clearFormState(): void {
  try {
    localStorage.removeItem(REQUEST_FORM_STATE_STORAGE_KEY);
  } catch (err) {
    console.error('Failed to clear form state:', err);
  }
}

function validateFormState(data: unknown): data is RequestFormPersistedState {
  if (!data || typeof data !== 'object') {
    return false;
  }

  const obj = data as Record<string, unknown>;

  // Check version
  if (obj.version !== REQUEST_FORM_STATE_VERSION) {
    return false;
  }

  // Check required fields
  if (
    typeof obj.nlInput !== 'string' ||
    typeof obj.projectPath !== 'string' ||
    typeof obj.autoPost !== 'boolean' ||
    typeof obj.timestamp !== 'string'
  ) {
    return false;
  }

  return true;
}

export function RequestForm() {
  const [nlInput, setNlInput] = useState('');
  const [projectPath, setProjectPath] = useState('');
  const [autoPost, setAutoPost] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<GitHubIssue | null>(null);
  const [costEstimate, setCostEstimate] = useState<CostEstimate | null>(null);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [systemHealthy, setSystemHealthy] = useState(true);
  const [healthWarning, setHealthWarning] = useState<string | null>(null);
  const [storageWarning, setStorageWarning] = useState<string | null>(null);
  const [uploadSuccessMessage, setUploadSuccessMessage] = useState<string | null>(null);

  // Ref for debounce timer
  const saveTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Ref for file input (keyboard accessibility)
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Initialize drag-and-drop hook
  const { isDragging, error: dragError, isReading, dragHandlers, clearError } = useDragAndDrop({
    onContentReceived: (content) => {
      // Append content to existing text with separator if there's existing content
      if (nlInput.trim()) {
        setNlInput(prev => prev + '\n\n---\n\n' + content);
      } else {
        setNlInput(content);
      }
    },
    onSuccess: (message) => {
      setUploadSuccessMessage(message);
      // Auto-dismiss success message after 3 seconds
      setTimeout(() => setUploadSuccessMessage(null), 3000);
    }
  });

  // Load form state from localStorage on mount
  useEffect(() => {
    const savedState = loadFormState();
    if (savedState) {
      setNlInput(savedState.nlInput);
      setProjectPath(savedState.projectPath);
      setAutoPost(savedState.autoPost);
    } else {
      // Backward compatibility: check for legacy project path key
      const savedPath = localStorage.getItem(PROJECT_PATH_STORAGE_KEY);
      if (savedPath) {
        setProjectPath(savedPath);
      }
    }
  }, []);

  // Debounced auto-save effect
  useEffect(() => {
    // Clear existing timer
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current);
    }

    // Set new timer for auto-save
    saveTimerRef.current = setTimeout(() => {
      try {
        saveFormState({
          nlInput,
          projectPath,
          autoPost,
        });
        setStorageWarning(null);
      } catch {
        setStorageWarning('Unable to save form state. Your work may not persist if you navigate away.');
      }
    }, 300); // AUTO_SAVE_DEBOUNCE_MS = 300

    // Cleanup on unmount
    return () => {
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current);
      }
    };
  }, [nlInput, projectPath, autoPost]);

  // Save form state before page unload
  useEffect(() => {
    const handleBeforeUnload = () => {
      try {
        saveFormState({
          nlInput,
          projectPath,
          autoPost,
        });
      } catch {
        // Silent failure on unload - no action needed
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [nlInput, projectPath, autoPost]);

  const handleSubmit = async () => {
    if (!nlInput.trim()) {
      setError('Please enter a description');
      return;
    }

    // Pre-flight health check
    setHealthWarning(null);
    try {
      const healthStatus = await getSystemStatus();
      if (healthStatus.overall_status === 'error') {
        const unhealthyServices = Object.entries(healthStatus.services)
          .filter(([, service]) => (service as ServiceHealth).status === 'error')
          .map(([, service]) => (service as ServiceHealth).name);

        setHealthWarning(
          `Warning: Critical services are down: ${unhealthyServices.join(', ')}. ` +
          `The workflow may fail. Do you want to proceed anyway?`
        );
        setSystemHealthy(false);

        // Optionally, you can prevent submission
        // return;
      } else if (healthStatus.overall_status === 'degraded') {
        setHealthWarning(
          `Some services are degraded. The workflow may experience delays but should complete.`
        );
        setSystemHealthy(true);
      } else {
        setSystemHealthy(true);
      }
    } catch {
      // If health check fails, warn but allow submission
      setHealthWarning('Unable to check system health. Proceeding anyway.');
    }

    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      // Save project path to localStorage if provided
      if (projectPath && projectPath.trim()) {
        localStorage.setItem(PROJECT_PATH_STORAGE_KEY, projectPath.trim());
      }

      const response = await submitRequest({
        nl_input: nlInput,
        project_path: projectPath || undefined,
        auto_post: autoPost,
      });

      setRequestId(response.request_id);

      // Fetch both preview and cost estimate in parallel
      const [previewData, costData] = await Promise.all([
        getPreview(response.request_id),
        getCostEstimate(response.request_id)
      ]);

      setPreview(previewData);
      setCostEstimate(costData);

      if (autoPost) {
        const confirmResponse = await confirmAndPost(response.request_id);
        setSuccessMessage(
          `Issue #${confirmResponse.issue_number} created successfully! ${confirmResponse.github_url}`
        );
        setNlInput('');
        // Don't clear project path - it will persist from localStorage
        setPreview(null);
        setCostEstimate(null);
        // Clear persisted form state after successful submission
        clearFormState();
      } else {
        setShowConfirm(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirm = async () => {
    if (!requestId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await confirmAndPost(requestId);
      setSuccessMessage(
        `Issue #${response.issue_number} created successfully! ${response.github_url}`
      );
      setShowConfirm(false);
      setPreview(null);
      setCostEstimate(null);
      setNlInput('');
      // Don't clear project path - it will persist from localStorage
      setRequestId(null);
      // Clear persisted form state after successful submission
      clearFormState();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setShowConfirm(false);
    setPreview(null);
    setCostEstimate(null);
    setRequestId(null);
  };

  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setError(null);
    clearError();

    try {
      const { handleMultipleFiles } = await import('../utils/fileHandlers');
      const result = await handleMultipleFiles(Array.from(files));

      if (result.content === '' && result.processedCount === 0) {
        setError(
          result.rejectedFiles.length > 0
            ? `No valid .md files found. Rejected files: ${result.rejectedFiles.join(', ')}`
            : 'No valid files to process'
        );
        return;
      }

      // Append content to existing text with separator if there's existing content
      if (nlInput.trim()) {
        setNlInput(prev => prev + '\n\n---\n\n' + result.content);
      } else {
        setNlInput(result.content);
      }

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
    <>
      <div className="max-w-4xl mx-auto">
        <div className="grid grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <h2 className="text-2xl font-bold text-gray-900">
              Create New Request
            </h2>

        <div>
          <label
            htmlFor="nl-input"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Describe what you want to build
          </label>

          {/* Drag-and-drop zone */}
          <div
            className={`relative ${isDragging ? 'ring-2 ring-primary' : ''}`}
            {...dragHandlers}
            aria-busy={isReading}
          >
            <textarea
              id="nl-input"
              placeholder="Example: Build a REST API for user management with CRUD operations..."
              value={nlInput}
              onChange={(e) => setNlInput(e.target.value)}
              rows={6}
              className={`w-full p-4 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-colors ${
                isDragging ? 'border-primary bg-blue-50' : 'border-gray-300'
              }`}
              disabled={isReading}
            />

            {/* Drop zone overlay */}
            {isDragging && (
              <div className="absolute inset-0 flex items-center justify-center bg-blue-50 bg-opacity-90 border-2 border-dashed border-primary rounded-lg pointer-events-none">
                <div className="text-center">
                  <svg className="mx-auto h-12 w-12 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="mt-2 text-sm font-medium text-primary">Drop .md file here</p>
                </div>
              </div>
            )}

            {/* Loading overlay */}
            {isReading && (
              <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90 rounded-lg">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                  <p className="mt-2 text-sm text-gray-600">Reading file(s)...</p>
                </div>
              </div>
            )}
          </div>

          {/* File upload button (keyboard accessibility) */}
          <div className="mt-2 flex items-center gap-2">
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
            <span className="text-xs text-gray-500">or drag and drop above</span>
          </div>

          {/* Drag-and-drop error message */}
          {dragError && (
            <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
              {dragError}
            </div>
          )}

          {/* Upload success message */}
          {uploadSuccessMessage && (
            <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-800 text-sm">
              {uploadSuccessMessage}
            </div>
          )}
        </div>

        <div>
          <label
            htmlFor="project-path"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Project path (optional)
          </label>
          <input
            id="project-path"
            type="text"
            placeholder="/Users/username/projects/my-app"
            value={projectPath}
            onChange={(e) => setProjectPath(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>

        <div className="flex items-center">
          <input
            id="auto-post"
            type="checkbox"
            checked={autoPost}
            onChange={(e) => setAutoPost(e.target.checked)}
            className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
          />
          <label htmlFor="auto-post" className="ml-2 text-sm text-gray-700">
            Auto-post to GitHub (skip confirmation)
          </label>
        </div>

        {storageWarning && (
          <div className="p-4 border rounded-lg bg-yellow-50 border-yellow-200 text-yellow-800">
            {storageWarning}
          </div>
        )}

        {healthWarning && (
          <div className={`p-4 border rounded-lg ${systemHealthy ? 'bg-yellow-50 border-yellow-200 text-yellow-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
            {healthWarning}
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            {error}
          </div>
        )}

        {successMessage && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
            {successMessage}
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={isLoading}
          className="w-full bg-primary text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Processing...' : 'Generate Issue'}
        </button>

        {preview && !showConfirm && !autoPost && (
          <div className="mt-6 space-y-6">
            <h3 className="text-xl font-bold">Preview</h3>

            {/* Cost Estimate Card - Displayed FIRST for visibility */}
            {costEstimate && (
              <CostEstimateCard estimate={costEstimate} />
            )}

            {/* GitHub Issue Preview */}
            <IssuePreview issue={preview} />
          </div>
        )}
          </div>

          <ZteHopperQueueCard />
        </div>

        {showConfirm && preview && (
          <ConfirmDialog
            issue={preview}
            costEstimate={costEstimate}
            onConfirm={handleConfirm}
            onCancel={handleCancel}
          />
        )}
      </div>

      <SystemStatusPanel />
    </>
  );
}
