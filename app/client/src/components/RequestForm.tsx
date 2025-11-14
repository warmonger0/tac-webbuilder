import { useState } from 'react';
import { submitRequest, getPreview, confirmAndPost } from '../api/client';
import type { GitHubIssue } from '../types';
import { IssuePreview } from './IssuePreview';
import { ConfirmDialog } from './ConfirmDialog';

export function RequestForm() {
  const [nlInput, setNlInput] = useState('');
  const [projectPath, setProjectPath] = useState('');
  const [autoPost, setAutoPost] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<GitHubIssue | null>(null);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!nlInput.trim()) {
      setError('Please enter a description');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await submitRequest({
        nl_input: nlInput,
        project_path: projectPath || undefined,
        auto_post: autoPost,
      });

      setRequestId(response.request_id);

      const previewData = await getPreview(response.request_id);
      setPreview(previewData);

      if (autoPost) {
        const confirmResponse = await confirmAndPost(response.request_id);
        setSuccessMessage(
          `Issue #${confirmResponse.issue_number} created successfully! ${confirmResponse.github_url}`
        );
        setNlInput('');
        setProjectPath('');
        setPreview(null);
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
      setNlInput('');
      setProjectPath('');
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
    setRequestId(null);
  };

  return (
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
          <div className="mt-6">
            <h3 className="text-xl font-bold mb-4">Preview</h3>
            <IssuePreview issue={preview} />
          </div>
        )}
      </div>

      {showConfirm && preview && (
        <ConfirmDialog
          issue={preview}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      )}
    </div>
  );
}
