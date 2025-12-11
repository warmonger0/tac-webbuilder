/**
 * Task Logs View Component
 *
 * Displays ADW phase completion logs from the observability system.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { observabilityClient, TaskLog } from '../api/observabilityClient';
import { LoadingState } from './common/LoadingState';
import { ErrorBanner } from './common/ErrorBanner';

interface TaskLogsViewProps {
  filterIssueNumber?: number;
}

export function TaskLogsView({ filterIssueNumber }: TaskLogsViewProps) {
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);

  // Fetch task logs
  const { data, isLoading, error } = useQuery({
    queryKey: ['task-logs', filterIssueNumber, limit, offset],
    queryFn: () =>
      filterIssueNumber
        ? observabilityClient.getTaskLogsByIssue(filterIssueNumber)
        : observabilityClient.getTaskLogs({ limit, offset }),
  });

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const formatDuration = (seconds: number | null) => {
    if (seconds === null) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}m ${secs}s`;
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      started: 'bg-blue-100 text-blue-800',
      skipped: 'bg-gray-100 text-gray-800',
    };
    return styles[status as keyof typeof styles] || 'bg-gray-100 text-gray-800';
  };

  const totalCount = data?.length || 0;
  const displayedLogs = filterIssueNumber ? data : data?.slice(offset, offset + limit);

  return (
    <div>
      {/* Loading/Error States */}
      {isLoading && <LoadingState message="Loading task logs..." />}
      <ErrorBanner error={error ? `Error loading task logs: ${(error as Error).message}` : null} />

      {/* Task Logs Table */}
      {data && displayedLogs && displayedLogs.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Issue #
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ADW ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Phase
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Completed At
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Error
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {displayedLogs.map((log: TaskLog, idx: number) => (
                <tr key={log.id || idx} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                    #{log.issue_number}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-600">
                    {log.adw_id}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">{log.phase_name}</span>
                      {log.phase_number && (
                        <span className="text-xs text-gray-500">({log.phase_number})</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(
                        log.phase_status
                      )}`}
                    >
                      {log.phase_status}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                    {formatDuration(log.duration_seconds)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                    {formatDate(log.completed_at)}
                  </td>
                  <td className="px-4 py-3 text-sm text-red-600">
                    {log.error_message && (
                      <details className="cursor-pointer">
                        <summary className="text-red-600 hover:text-red-800">
                          View Error
                        </summary>
                        <div className="mt-1 p-2 bg-red-50 rounded text-xs max-w-md">
                          {log.error_message}
                        </div>
                      </details>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* No Results */}
      {data && data.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p>No task logs found.</p>
          {filterIssueNumber && <p className="text-sm">Try clearing the filter.</p>}
        </div>
      )}

      {/* Pagination (only when not filtering) */}
      {!filterIssueNumber && data && data.length > limit && (
        <div className="mt-6 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            Showing {offset + 1} - {Math.min(offset + limit, totalCount)} of {totalCount} logs
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= totalCount}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
