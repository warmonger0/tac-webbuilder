import { useEffect, useRef, useState } from 'react';
import { confirmAndPost, getCostEstimate, getPreflightChecks, getPreview, getSystemStatus, submitRequest } from '../api/client';
import type { CostEstimate, GitHubIssue, ServiceHealth } from '../types';
import { type DragHandlers, useDragAndDrop } from '../hooks/useDragAndDrop';
import { useStaggeredLoad } from '../hooks/useStaggeredLoad';
import { parsePhases, type PhaseParseResult } from '../utils/phaseParser';
import { PhaseDetectionHandler } from './request-form/PhaseDetectionHandler';
import { clearFormState, loadFormState, PROJECT_PATH_STORAGE_KEY, saveFormState } from './request-form/utils/formStorage';

export interface UseRequestFormReturn {
  // Form state
  nlInput: string;
  setNlInput: (value: string) => void;
  projectPath: string;
  setProjectPath: (value: string) => void;
  autoPost: boolean;
  setAutoPost: (value: boolean) => void;

  // UI state
  isLoading: boolean;
  error: string | null;
  setError: (error: string | null) => void;
  successMessage: string | null;
  setSuccessMessage: (message: string | null) => void;
  storageWarning: string | null;

  // Preview state
  preview: GitHubIssue | null;
  costEstimate: CostEstimate | null;
  requestId: string | null;
  showConfirm: boolean;

  // System health state
  systemHealthy: boolean;
  healthWarning: string | null;

  // Staggered loading
  showAdwMonitor: boolean;
  showHopperQueue: boolean;

  // Drag and drop
  isDragging: boolean;
  dragError: string | null;
  isReading: boolean;
  dragHandlers: DragHandlers;
  clearDragError: () => void;

  // Phase handler
  phaseHandler: {
    openPhasePreview: (parseResult: PhaseParseResult) => void;
    isSubmitting: boolean;
    modal: React.ReactNode;
  };

  // Handlers
  handleSubmit: () => Promise<void>;
  handleConfirm: () => Promise<void>;
  handleCancel: () => void;
  handleContentReceived: (content: string) => void;
}

export function useRequestForm(): UseRequestFormReturn {
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

    setIsLoading(true);
    setError(null);
    setHealthWarning(null);

    // PRE-FLIGHT CHECKS: Run BEFORE creating issue
    try {
      const preflightResult = await getPreflightChecks(true); // Skip tests for speed

      if (!preflightResult.passed) {
        // BLOCKING FAILURES - DO NOT SUBMIT
        const failureMessages = preflightResult.blocking_failures.map(f =>
          `❌ ${f.check}:\n   ${f.error}\n   💡 Fix: ${f.fix}`
        ).join('\n\n');

        setError(
          `Cannot submit request - Pre-flight checks failed:\n\n${failureMessages}\n\n` +
          `Please fix these issues before submitting.`
        );
        setIsLoading(false);
        return;
      }
    } catch (err) {
      setError(`Pre-flight check error: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setIsLoading(false);
      return;
    }

    // System health check (warnings only, not blocking)
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

    // Continue with submission (already set isLoading=true and error=null above)
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

  return {
    // Form state
    nlInput,
    setNlInput,
    projectPath,
    setProjectPath,
    autoPost,
    setAutoPost,

    // UI state
    isLoading,
    error,
    setError,
    successMessage,
    setSuccessMessage,
    storageWarning,

    // Preview state
    preview,
    costEstimate,
    requestId,
    showConfirm,

    // System health state
    systemHealthy,
    healthWarning,

    // Staggered loading
    showAdwMonitor,
    showHopperQueue,

    // Drag and drop
    isDragging,
    dragError,
    isReading,
    dragHandlers,
    clearDragError: clearError,

    // Phase handler
    phaseHandler,

    // Handlers
    handleSubmit,
    handleConfirm,
    handleCancel,
    handleContentReceived,
  };
}
