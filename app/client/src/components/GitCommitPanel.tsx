import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { LoadingState } from './common/LoadingState';
import { ErrorBanner } from './common/ErrorBanner';

interface GitStatusFile {
  path: string;
  status: string;
}

interface GitStatusResponse {
  branch: string;
  ahead: number;
  behind: number;
  staged: GitStatusFile[];
  unstaged: GitStatusFile[];
  untracked: GitStatusFile[];
  clean: boolean;
}

interface GitCommitRequest {
  message: string;
  files: string[];
}

interface GitCommitResponse {
  success: boolean;
  commit_hash: string | null;
  message: string;
  files_committed: number;
}

export function GitCommitPanel() {
  const [commitMessage, setCommitMessage] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const queryClient = useQueryClient();

  const { data: gitStatus, isLoading, error, refetch } = useQuery<GitStatusResponse>({
    queryKey: ['gitStatus'],
    queryFn: async () => {
      const response = await fetch('/api/v1/git/status');
      if (!response.ok) {
        throw new Error('Failed to fetch git status');
      }
      return response.json();
    },
    // Don't auto-fetch on mount
    enabled: false,
    refetchOnWindowFocus: false,
  });

  const commitMutation = useMutation({
    mutationFn: async (request: GitCommitRequest) => {
      const response = await fetch('/api/v1/git/commit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to commit changes');
      }
      return response.json() as Promise<GitCommitResponse>;
    },
    onSuccess: () => {
      // Clear form
      setCommitMessage('');
      setSelectedFiles([]);
      // Refresh git status
      refetch();
      // Invalidate preflight checks (they check git status too)
      queryClient.invalidateQueries({ queryKey: ['preflightChecks'] });
    },
  });

  const handleCommit = () => {
    if (!commitMessage.trim()) {
      return;
    }
    commitMutation.mutate({
      message: commitMessage,
      files: selectedFiles,
    });
  };

  const toggleFileSelection = (filePath: string) => {
    setSelectedFiles(prev =>
      prev.includes(filePath)
        ? prev.filter(f => f !== filePath)
        : [...prev, filePath]
    );
  };

  const selectAllFiles = () => {
    if (!gitStatus) return;
    const allFiles = [
      ...gitStatus.unstaged.map(f => f.path),
      ...gitStatus.untracked.map(f => f.path),
    ];
    setSelectedFiles(allFiles);
  };

  const clearSelection = () => {
    setSelectedFiles([]);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'modified':
        return '📝';
      case 'added':
        return '➕';
      case 'deleted':
        return '🗑️';
      case 'untracked':
        return '❓';
      default:
        return '📄';
    }
  };

  const allFiles = gitStatus
    ? [...gitStatus.staged, ...gitStatus.unstaged, ...gitStatus.untracked]
    : [];

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-lg font-bold text-gray-900">Git Commit</h3>
          <p className="text-sm text-gray-600">
            Commit changes from the frontend
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Checking...' : 'Check Status'}
          </button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && <LoadingState message="Checking git status..." />}

      {/* Error State */}
      <ErrorBanner
        error={error ? `Error checking git status: ${(error as Error).message}` : null}
        title="Git Status Failed"
      />

      {/* Commit Error */}
      <ErrorBanner
        error={commitMutation.error ? `Commit failed: ${(commitMutation.error as Error).message}` : null}
        title="Commit Failed"
      />

      {/* Success Message */}
      {commitMutation.isSuccess && commitMutation.data && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-2xl">✅</span>
            <div>
              <p className="font-bold text-green-800">{commitMutation.data.message}</p>
              <p className="text-sm text-gray-600">
                Committed {commitMutation.data.files_committed} file(s)
                {commitMutation.data.commit_hash && (
                  <span className="ml-1 font-mono text-xs">
                    ({commitMutation.data.commit_hash.substring(0, 7)})
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {gitStatus && !isLoading && (
        <div className="space-y-4">
          {/* Status Banner */}
          <div
            className={`p-4 rounded-lg border ${
              gitStatus.clean
                ? 'bg-green-50 border-green-200'
                : 'bg-yellow-50 border-yellow-200'
            }`}
          >
            <div className="flex justify-between items-center">
              <div>
                <p className={`font-bold ${gitStatus.clean ? 'text-green-800' : 'text-yellow-800'}`}>
                  {gitStatus.clean ? 'Working tree clean' : 'Uncommitted changes'}
                </p>
                <p className="text-sm text-gray-600">
                  Branch: <span className="font-mono">{gitStatus.branch}</span>
                  {gitStatus.ahead > 0 && (
                    <span className="ml-2">↑ {gitStatus.ahead} ahead</span>
                  )}
                  {gitStatus.behind > 0 && (
                    <span className="ml-2">↓ {gitStatus.behind} behind</span>
                  )}
                </p>
              </div>
            </div>
          </div>

          {/* Files List */}
          {!gitStatus.clean && (
            <>
              <div className="flex justify-between items-center">
                <h4 className="font-bold text-gray-800">
                  Files ({allFiles.length})
                </h4>
                <div className="flex gap-2">
                  <button
                    onClick={selectAllFiles}
                    className="text-xs text-blue-600 hover:text-blue-800"
                  >
                    Select All
                  </button>
                  <button
                    onClick={clearSelection}
                    className="text-xs text-blue-600 hover:text-blue-800"
                  >
                    Clear
                  </button>
                </div>
              </div>

              <div className="max-h-60 overflow-y-auto border border-gray-200 rounded-lg">
                {allFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-2 p-2 hover:bg-gray-50 border-b last:border-b-0"
                  >
                    <input
                      type="checkbox"
                      checked={selectedFiles.includes(file.path)}
                      onChange={() => toggleFileSelection(file.path)}
                      className="h-4 w-4"
                    />
                    <span className="text-lg">{getStatusIcon(file.status)}</span>
                    <div className="flex-1">
                      <div className="font-mono text-sm text-gray-900">{file.path}</div>
                      <div className="text-xs text-gray-500 capitalize">{file.status}</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Commit Form */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Commit Message
                </label>
                <textarea
                  value={commitMessage}
                  onChange={(e) => setCommitMessage(e.target.value)}
                  placeholder="Enter commit message..."
                  rows={3}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <div className="flex justify-end">
                  <button
                    onClick={handleCommit}
                    disabled={!commitMessage.trim() || commitMutation.isPending}
                    className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {commitMutation.isPending ? 'Committing...' : 'Commit Changes'}
                  </button>
                </div>
                {selectedFiles.length === 0 && (
                  <p className="text-xs text-gray-500">
                    No files selected - will commit all changes
                  </p>
                )}
                {selectedFiles.length > 0 && (
                  <p className="text-xs text-gray-500">
                    {selectedFiles.length} file(s) selected
                  </p>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
