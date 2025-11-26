import { useEffect, useRef, useState } from 'react';
import { confirmAndPost, getCostEstimate, getPreview, getSystemStatus, submitRequest } from '../api/client';
import type { CostEstimate, GitHubIssue, ServiceHealth } from '../types';
import { IssuePreview } from './IssuePreview';
import { CostEstimateCard } from './CostEstimateCard';
import { ConfirmDialog } from './ConfirmDialog';
import { SystemStatusPanel } from './SystemStatusPanel';
import { ZteHopperQueueCard } from './ZteHopperQueueCard';
import { AdwMonitorCard } from './AdwMonitorCard';
import { AdwMonitorErrorBoundary } from './AdwMonitorErrorBoundary';
import { useDragAndDrop } from '../hooks/useDragAndDrop';
import { useStaggeredLoad } from '../hooks/useStaggeredLoad';
import { parsePhases } from '../utils/phaseParser';
import { FileUploadSection } from './request-form/FileUploadSection';
import { PhaseDetectionHandler } from './request-form/PhaseDetectionHandler';
import { saveFormState, loadFormState, clearFormState, PROJECT_PATH_STORAGE_KEY } from './request-form/utils/formStorage';

export function RequestForm() {
  // Stagger panel loading to prevent initial load slowdown
  const showAdwMonitor = useStaggeredLoad(100);  // Load ADW monitor after 100ms
  const showHopperQueue = useStaggeredLoad(400); // Load hopper queue after 400ms

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

      // Show predicted patterns if available
      if (response.predicted_patterns && response.predicted_patterns.length > 0) {
        const patterns = response.predicted_patterns.map(p => p.pattern).join(', ');
        setSuccessMessage(
          `✅ Request submitted! Detected patterns: ${patterns}`
        );
        // Clear after 5 seconds
        setTimeout(() => setSuccessMessage(null), 5000);
      }

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
      <div className="max-w-7xl mx-auto px-4">
        {/* First Row: Create New Request & Hopper Queue */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4 items-stretch">
          {/* Left Column - Create New Request */}
          <div
            className={`lg:col-span-2 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg shadow-xl border border-slate-700 p-4 space-y-3 relative transition-all flex flex-col ${
              isDragging ? 'ring-4 ring-emerald-500 ring-opacity-50' : ''
            }`}
            {...dragHandlers}
            aria-busy={isReading || phaseHandler.isSubmitting}
          >
            <div className="relative mb-1">
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 to-teal-500/10 rounded-lg -m-2"></div>
              <h2 className="text-xl font-bold text-white relative z-10">
                Create New Request
              </h2>
            </div>

            <div>
              <label
                htmlFor="nl-input"
                className="block text-sm font-medium text-slate-300 mb-2"
              >
                Describe what you want to build
              </label>

              <textarea
                id="nl-input"
                placeholder="Example: Build a REST API for user management with CRUD operations..."
                value={nlInput}
                onChange={(e) => setNlInput(e.target.value)}
                rows={4}
                className="w-full p-3 bg-slate-800 border border-slate-600 text-white placeholder-slate-400 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
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
                className="block text-sm font-medium text-slate-300 mb-2"
              >
                Project path (optional)
              </label>
              <input
                id="project-path"
                type="text"
                placeholder="/Users/username/projects/my-app"
                value={projectPath}
                onChange={(e) => setProjectPath(e.target.value)}
                className="w-full p-3 bg-slate-800 border border-slate-600 text-white placeholder-slate-400 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
            </div>

            <div className="flex items-center">
              <input
                id="auto-post"
                type="checkbox"
                checked={autoPost}
                onChange={(e) => setAutoPost(e.target.checked)}
                className="h-4 w-4 text-emerald-500 focus:ring-emerald-500 border-slate-600 rounded bg-slate-800"
              />
              <label htmlFor="auto-post" className="ml-2 text-sm text-slate-300">
                Auto-post to GitHub (skip confirmation)
              </label>
            </div>

            {storageWarning && (
              <div className="p-4 border rounded-lg bg-yellow-900/20 border-yellow-500/50 text-yellow-200">
                {storageWarning}
              </div>
            )}

            {healthWarning && (
              <div className={`p-4 border rounded-lg ${systemHealthy ? 'bg-yellow-900/20 border-yellow-500/50 text-yellow-200' : 'bg-red-900/20 border-red-500/50 text-red-200'}`}>
                {healthWarning}
              </div>
            )}

            {error && (
              <div className="p-4 bg-red-900/20 border border-red-500/50 rounded-lg text-red-200">
                {error}
              </div>
            )}

            {successMessage && (
              <div className="p-4 bg-emerald-900/20 border border-emerald-500/50 rounded-lg text-emerald-200">
                {successMessage}
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={isLoading || phaseHandler.isSubmitting}
              className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 text-white py-3 px-6 rounded-lg font-medium hover:from-emerald-600 hover:to-teal-600 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed transition-all shadow-lg"
            >
              {isLoading ? 'Processing...' : 'Generate Issue'}
            </button>

            {preview && !showConfirm && !autoPost && (
              <div className="mt-6 space-y-6">
                <h3 className="text-xl font-bold text-white">Preview</h3>

                {/* Cost Estimate Card - Displayed FIRST for visibility */}
                {costEstimate && (
                  <CostEstimateCard estimate={costEstimate} />
                )}

                {/* GitHub Issue Preview */}
                <IssuePreview issue={preview} />
              </div>
            )}
          </div>

          {/* Right Column - Hopper Queue */}
          <div className="lg:col-span-1">
            {showHopperQueue ? (
              <ZteHopperQueueCard />
            ) : (
              <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg shadow-xl border border-slate-700 p-4 flex items-center justify-center min-h-[200px]">
                <div className="text-slate-500 text-xs animate-pulse">●</div>
              </div>
            )}
          </div>
        </div>

        {/* Second Row: System Status & Current Workflow */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-stretch">
          {/* System Status */}
          <div className="lg:col-span-2 flex">
            <SystemStatusPanel />
          </div>

          {/* Current Workflow */}
          <div className="lg:col-span-1 flex">
            {showAdwMonitor ? (
              <AdwMonitorErrorBoundary>
                <AdwMonitorCard />
              </AdwMonitorErrorBoundary>
            ) : (
              <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg shadow-xl border border-slate-700 p-4 flex items-center justify-center min-h-[200px]">
                <div className="text-slate-500 text-xs animate-pulse">●</div>
              </div>
            )}
          </div>
        </div>
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
    </>
  );
}
