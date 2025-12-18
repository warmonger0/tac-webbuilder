/**
 * Log Panel Component (Panel 10)
 *
 * Tabbed interface for viewing:
 * - Work Logs (chat session summaries)
 * - Task Logs (ADW phase completions)
 * - User Prompts (request submissions)
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import {
  workLogClient,
  WorkLogEntryCreate,
} from '../api/workLogClient';
import { TaskLogsView } from './TaskLogsView';
import { UserPromptsView } from './UserPromptsView';
import { LoadingState } from './common/LoadingState';
import { ErrorBanner } from './common/ErrorBanner';
import { ConfirmationDialog } from './common/ConfirmationDialog';
import { formatErrorMessage, logError } from '../utils/errorHandler';

type TabType = 'workLogs' | 'taskLogs' | 'userPrompts';

export function LogPanel() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<TabType>('workLogs');
  const [filterIssueNumber, setFilterIssueNumber] = useState<string>('');
  const [mutationError, setMutationError] = useState<Error | string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);

  // Work Logs state
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [filterSession, setFilterSession] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState<WorkLogEntryCreate>({
    session_id: '',
    summary: '',
    chat_file_link: '',
    issue_number: undefined,
    workflow_id: '',
    tags: [],
  });
  const [tagInput, setTagInput] = useState('');

  // Fetch work logs (only for Work Logs tab)
  const { data, isLoading, error: queryError } = useQuery({
    queryKey: ['work-logs', limit, offset, filterSession],
    queryFn: () =>
      filterSession
        ? workLogClient.getSessionWorkLogs(filterSession).then((entries) => ({
            entries,
            total: entries.length,
            limit,
            offset: 0,
          }))
        : workLogClient.getWorkLogs(limit, offset),
    enabled: activeTab === 'workLogs',
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (entry: WorkLogEntryCreate) => workLogClient.createWorkLog(entry),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['work-logs'] });
      setShowCreateForm(false);
      resetForm();
      setMutationError(null);
    },
    onError: (err: unknown) => {
      logError('[LogPanel]', 'Create work log', err);
      setMutationError(formatErrorMessage(err));
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (entryId: number) => workLogClient.deleteWorkLog(entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['work-logs'] });
      setMutationError(null);
    },
    onError: (err: unknown) => {
      logError('[LogPanel]', 'Delete work log', err);
      setMutationError(formatErrorMessage(err));
    },
  });

  const resetForm = () => {
    setFormData({
      session_id: '',
      summary: '',
      chat_file_link: '',
      issue_number: undefined,
      workflow_id: '',
      tags: [],
    });
    setTagInput('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.summary.length > 280) {
      toast.error('Summary must be 280 characters or less');
      return;
    }
    createMutation.mutate(formData);
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags?.includes(tagInput.trim())) {
      setFormData({
        ...formData,
        tags: [...(formData.tags || []), tagInput.trim()],
      });
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setFormData({
      ...formData,
      tags: formData.tags?.filter((t) => t !== tag) || [],
    });
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const totalPages = Math.ceil((data?.total || 0) / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  const parseIssueNumber = (): number | undefined => {
    const num = parseInt(filterIssueNumber);
    return isNaN(num) ? undefined : num;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Log Panel</h2>
          <p className="text-gray-600 text-sm">
            View work logs, task logs, and user prompts
          </p>
        </div>
        {activeTab === 'workLogs' && (
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            {showCreateForm ? 'Cancel' : '+ New Entry'}
          </button>
        )}
      </div>

      {/* Error Banner */}
      <ErrorBanner error={mutationError} onDismiss={() => setMutationError(null)} className="mb-4" />

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => {
                setActiveTab('workLogs');
                setOffset(0);
              }}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'workLogs'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Work Logs
            </button>
            <button
              onClick={() => {
                setActiveTab('taskLogs');
                setOffset(0);
              }}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'taskLogs'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Task Logs
            </button>
            <button
              onClick={() => {
                setActiveTab('userPrompts');
                setOffset(0);
              }}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'userPrompts'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              User Prompts
            </button>
          </nav>
        </div>
      </div>

      {/* Shared Filter - Issue Number */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Filter by Issue Number (applies to all tabs)
        </label>
        <div className="flex gap-2">
          <input
            type="number"
            value={filterIssueNumber}
            onChange={(e) => setFilterIssueNumber(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="Enter issue number to filter..."
          />
          {filterIssueNumber && (
            <button
              onClick={() => setFilterIssueNumber('')}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {/* Work Logs Tab */}
        {activeTab === 'workLogs' && (
          <div>
            {/* Create Form */}
            {showCreateForm && (
              <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <h3 className="text-lg font-semibold mb-4">Create Work Log Entry</h3>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Session ID *
                    </label>
                    <input
                      type="text"
                      value={formData.session_id}
                      onChange={(e) =>
                        setFormData({ ...formData, session_id: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Summary * ({formData.summary.length}/280)
                    </label>
                    <textarea
                      value={formData.summary}
                      onChange={(e) =>
                        setFormData({ ...formData, summary: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      rows={3}
                      maxLength={280}
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Chat File Link
                      </label>
                      <input
                        type="text"
                        value={formData.chat_file_link}
                        onChange={(e) =>
                          setFormData({ ...formData, chat_file_link: e.target.value })
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Issue Number
                      </label>
                      <input
                        type="number"
                        value={formData.issue_number || ''}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            issue_number: e.target.value ? parseInt(e.target.value) : undefined,
                          })
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Workflow ID
                    </label>
                    <input
                      type="text"
                      value={formData.workflow_id}
                      onChange={(e) =>
                        setFormData({ ...formData, workflow_id: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tags
                    </label>
                    <div className="flex gap-2 mb-2">
                      <input
                        type="text"
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="Add a tag..."
                      />
                      <button
                        type="button"
                        onClick={handleAddTag}
                        className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                      >
                        Add
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {formData.tags?.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-1 bg-blue-100 text-blue-800 rounded-lg text-sm flex items-center gap-1"
                        >
                          {tag}
                          <button
                            type="button"
                            onClick={() => handleRemoveTag(tag)}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      type="submit"
                      disabled={createMutation.isPending}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                    >
                      {createMutation.isPending ? 'Creating...' : 'Create Entry'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowCreateForm(false)}
                      className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Session Filter (Work Logs Only) */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Session ID
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={filterSession}
                  onChange={(e) => {
                    setFilterSession(e.target.value);
                    setOffset(0);
                  }}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter session ID to filter..."
                />
                {filterSession && (
                  <button
                    onClick={() => setFilterSession('')}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>

            {/* Loading/Error States */}
            {isLoading && <LoadingState message="Loading work logs..." />}
            <ErrorBanner error={queryError ? `Error loading work logs: ${String(queryError)}` : null} />

            {/* Work Log Entries */}
            {data && data.entries.length > 0 && (
              <div className="space-y-3">
                {data.entries.map((entry) => (
                  <div
                    key={entry.id}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-mono text-gray-500">
                            #{entry.id}
                          </span>
                          <span className="text-xs text-gray-500">
                            {formatDate(entry.created_at)}
                          </span>
                        </div>
                        <p className="text-gray-900 mb-2">{entry.summary}</p>
                      </div>
                      <button
                        onClick={() => setDeleteConfirm(entry.id)}
                        className="text-red-600 hover:text-red-800 text-sm ml-2"
                      >
                        Delete
                      </button>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-sm mb-2">
                      <div>
                        <span className="text-gray-600">Session:</span>{' '}
                        <span className="font-mono text-gray-900">{entry.session_id}</span>
                      </div>
                      {entry.issue_number && (
                        <div>
                          <span className="text-gray-600">Issue:</span>{' '}
                          <span className="text-gray-900">#{entry.issue_number}</span>
                        </div>
                      )}
                      {entry.workflow_id && (
                        <div>
                          <span className="text-gray-600">Workflow:</span>{' '}
                          <span className="font-mono text-gray-900">{entry.workflow_id}</span>
                        </div>
                      )}
                      {entry.chat_file_link && (
                        <div className="col-span-2">
                          <span className="text-gray-600">Chat:</span>{' '}
                          <a
                            href={entry.chat_file_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            {entry.chat_file_link}
                          </a>
                        </div>
                      )}
                    </div>

                    {entry.tags && entry.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {entry.tags.map((tag, idx) => (
                          <span
                            key={`tag-${idx}`}
                            className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* No Results */}
            {data && data.entries.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <p>No work log entries found.</p>
                {filterSession && <p className="text-sm">Try clearing the filter.</p>}
              </div>
            )}

            {/* Pagination */}
            {data && data.entries.length > 0 && (
              <div className="mt-6 flex justify-between items-center">
                <div className="text-sm text-gray-600">
                  Showing {offset + 1} - {Math.min(offset + limit, data.total)} of {data.total} entries
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setOffset(Math.max(0, offset - limit))}
                    disabled={offset === 0}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="px-4 py-2 text-gray-700">
                    Page {currentPage} of {totalPages}
                  </span>
                  <button
                    onClick={() => setOffset(offset + limit)}
                    disabled={offset + limit >= data.total}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Task Logs Tab */}
        {activeTab === 'taskLogs' && (
          <TaskLogsView filterIssueNumber={parseIssueNumber()} />
        )}

        {/* User Prompts Tab */}
        {activeTab === 'userPrompts' && (
          <UserPromptsView filterIssueNumber={parseIssueNumber()} />
        )}
      </div>

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={deleteConfirm !== null}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={() => {
          if (deleteConfirm !== null) {
            deleteMutation.mutate(deleteConfirm);
          }
        }}
        title="Delete Entry?"
        message="This action cannot be undone. Are you sure you want to delete this work log entry?"
        confirmText="Delete"
        confirmVariant="danger"
      />
    </div>
  );
}
