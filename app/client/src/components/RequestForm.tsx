import { useEffect, useRef, useState } from 'react';
import { confirmAndPost, getCostEstimate, getPreview, getSystemStatus, submitRequest } from '../api/client';
import type { CostEstimate, GitHubIssue, ServiceHealth } from '../types';
import { IssuePreview } from './IssuePreview';
import { CostEstimateCard } from './CostEstimateCard';
import { ConfirmDialog } from './ConfirmDialog';
import { SystemStatusPanel } from './SystemStatusPanel';
import { ZteHopperQueueCard } from './ZteHopperQueueCard';
import { AdwMonitorCard } from './AdwMonitorCard';
import { useDragAndDrop } from '../hooks/useDragAndDrop';
import { parsePhases } from '../utils/phaseParser';
import { FileUploadSection } from './request-form/FileUploadSection';
import { PhaseDetectionHandler } from './request-form/PhaseDetectionHandler';
import { saveFormState, loadFormState, clearFormState, PROJECT_PATH_STORAGE_KEY } from './request-form/utils/formStorage';

export function RequestForm() {
  // Form state
  const [nlInput, setNlInput] = useState('');
  const [projectPath, setProjectPath] = useState('');
  const [autoPost, setAutoPost] = useState(false);

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [storageWarning, setStorageWarning] = useState<string | null>(null);

  // Preview state
  const [preview, setPreview] = useState<GitHubIssue | null>(null);
  const [costEstimate, setCostEstimate] = useState<CostEstimate | null>(null);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);

  // System health state
  const [systemHealthy, setSystemHealthy] = useState(true);
  const [healthWarning, setHealthWarning] = useState<string | null>(null);

  // Ref for debounce timer
  const saveTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize drag-and-drop hook
  const { isDragging, error: dragError, isReading, dragHandlers, clearError } = useDragAndDrop({
    onContentReceived: (content) => {
      // Parse content for phases
      const parseResult = parsePhases(content);

      // If multi-phase detected, show preview for confirmation
      if (parseResult.isMultiPhase && parseResult.phases.length > 1) {
        phaseHandler.openPhasePreview(parseResult);
      } else {
        // Single-phase or no phases: append content normally
        if (nlInput.trim()) {
          setNlInput(prev => prev + '\n\n---\n\n' + content);
        } else {
          setNlInput(content);
        }
      }
    },
    onSuccess: () => {
      // Success message handled by FileUploadSection
    }
  });

  // Initialize phase detection handler
  const phaseHandler = PhaseDetectionHandler({
    projectPath,
    onSuccess: (message) => {
      setSuccessMessage(message);
      setNlInput('');
      clearFormState();
    },
    onError: (errorMsg) => setError(errorMsg),
    onFormClear: () => {
      setNlInput('');
      clearFormState();
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
        setPreview(null);
        setCostEstimate(null);
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
      setRequestId(null);
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

  const handleContentReceived = (content: string) => {
    if (nlInput.trim()) {
      setNlInput(prev => prev + content);
    } else {
      setNlInput(content);
    }
  };

  return (
    <>
      <div className="max-w-4xl mx-auto">
        <div className="grid grid-cols-2 gap-6">
          {/* Drag-and-drop zone - entire card */}
          <div
            className={`bg-white rounded-lg shadow p-6 space-y-4 relative transition-all ${
              isDragging ? 'ring-4 ring-primary ring-opacity-50 bg-blue-50' : ''
            }`}
            {...dragHandlers}
            aria-busy={isReading || phaseHandler.isSubmitting}
          >
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

              <textarea
                id="nl-input"
                placeholder="Example: Build a REST API for user management with CRUD operations..."
                value={nlInput}
                onChange={(e) => setNlInput(e.target.value)}
                rows={6}
                className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-colors"
                disabled={isReading}
              />

              <FileUploadSection
                onContentReceived={handleContentReceived}
                onPhasePreviewOpen={phaseHandler.openPhasePreview}
                isDragging={isDragging}
                dragError={dragError}
                isReading={isReading}
                clearDragError={clearError}
                currentNlInput={nlInput}
              />
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
              disabled={isLoading || phaseHandler.isSubmitting}
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

        {phaseHandler.modal}
      </div>

      {/* ADW Monitor Section */}
      <div className="max-w-4xl mx-auto mt-8">
        <AdwMonitorCard />
      </div>

      <SystemStatusPanel />
    </>
  );
}
