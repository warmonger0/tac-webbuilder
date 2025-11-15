import { useState, useEffect } from 'react';
import { submitRequest, getPreview, getCostEstimate, confirmAndPost, getSystemStatus } from '../api/client';
import type { GitHubIssue, CostEstimate } from '../types';
import { IssuePreview } from './IssuePreview';
import { CostEstimateCard } from './CostEstimateCard';
import { ConfirmDialog } from './ConfirmDialog';
import { SystemStatusPanel } from './SystemStatusPanel';

const PROJECT_PATH_STORAGE_KEY = 'tac-webbuilder-project-path';

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

  // Load project path from localStorage on mount
  useEffect(() => {
    const savedPath = localStorage.getItem(PROJECT_PATH_STORAGE_KEY);
    if (savedPath) {
      setProjectPath(savedPath);
    }
  }, []);

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
          .filter(([_, service]: [string, any]) => service.status === 'error')
          .map(([_, service]: [string, any]) => service.name);

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
    } catch (err) {
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

  return (
    <>
      <div className="max-w-4xl mx-auto">
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
          <textarea
            id="nl-input"
            placeholder="Example: Build a REST API for user management with CRUD operations..."
            value={nlInput}
            onChange={(e) => setNlInput(e.target.value)}
            rows={6}
            className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
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
