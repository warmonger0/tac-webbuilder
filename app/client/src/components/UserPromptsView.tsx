/**
 * User Prompts View Component
 *
 * Displays user request submissions from the observability system.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { observabilityClient, UserPrompt } from '../api/observabilityClient';

interface UserPromptsViewProps {
  filterIssueNumber?: number;
}

export function UserPromptsView({ filterIssueNumber }: UserPromptsViewProps) {
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  // Fetch user prompts
  const { data, isLoading, error } = useQuery({
    queryKey: ['user-prompts', filterIssueNumber, limit, offset],
    queryFn: () =>
      filterIssueNumber
        ? observabilityClient.getUserPromptsByIssue(filterIssueNumber)
        : observabilityClient.getUserPrompts({ limit, offset }),
  });

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getComplexityBadge = (complexity: string | null) => {
    if (!complexity) return null;
    const styles = {
      ATOMIC: 'bg-green-100 text-green-800',
      DECOMPOSE: 'bg-yellow-100 text-yellow-800',
    };
    return (
      <span
        className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
          styles[complexity as keyof typeof styles] || 'bg-gray-100 text-gray-800'
        }`}
      >
        {complexity}
      </span>
    );
  };

  const getTypeBadge = (type: string | null) => {
    if (!type) return null;
    const styles = {
      feature: 'bg-blue-100 text-blue-800',
      bug: 'bg-red-100 text-red-800',
      chore: 'bg-gray-100 text-gray-800',
    };
    return (
      <span
        className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
          styles[type as keyof typeof styles] || 'bg-gray-100 text-gray-800'
        }`}
      >
        {type}
      </span>
    );
  };

  const totalCount = data?.length || 0;
  const displayedPrompts = filterIssueNumber ? data : data?.slice(offset, offset + limit);

  return (
    <div>
      {/* Loading/Error States */}
      {isLoading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading user prompts...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          Error loading user prompts: {(error as Error).message}
        </div>
      )}

      {/* User Prompts List */}
      {data && displayedPrompts && displayedPrompts.length > 0 && (
        <div className="space-y-4">
          {displayedPrompts.map((prompt: UserPrompt, idx: number) => (
            <div
              key={prompt.id || idx}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              {/* Header Row */}
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2">
                  {prompt.github_issue_number && (
                    <a
                      href={prompt.github_issue_url || `#${prompt.github_issue_number}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline font-medium"
                    >
                      Issue #{prompt.github_issue_number}
                    </a>
                  )}
                  {getTypeBadge(prompt.issue_type)}
                  {getComplexityBadge(prompt.complexity)}
                  {prompt.is_multi_phase && (
                    <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-semibold">
                      Multi-Phase ({prompt.phase_count})
                    </span>
                  )}
                </div>
                <span className="text-xs text-gray-500">{formatDate(prompt.created_at)}</span>
              </div>

              {/* Title & Input */}
              {prompt.issue_title && (
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{prompt.issue_title}</h3>
              )}

              <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-600">Natural Language Input:</span>
                  <button
                    onClick={() => setExpandedId(expandedId === prompt.id ? null : prompt.id)}
                    className="text-blue-600 hover:text-blue-800 text-xs"
                  >
                    {expandedId === prompt.id ? 'Collapse' : 'Expand'}
                  </button>
                </div>
                <div
                  className={`text-sm text-gray-700 bg-gray-50 p-2 rounded ${
                    expandedId === prompt.id ? '' : 'line-clamp-2'
                  }`}
                >
                  {prompt.nl_input}
                </div>
              </div>

              {/* Cost Info */}
              {(prompt.estimated_cost_usd || prompt.estimated_tokens) && (
                <div className="flex gap-4 text-sm text-gray-600 mb-2">
                  {prompt.estimated_cost_usd && (
                    <div>
                      <span className="font-medium">Est. Cost:</span> $
                      {prompt.estimated_cost_usd.toFixed(4)}
                    </div>
                  )}
                  {prompt.estimated_tokens && (
                    <div>
                      <span className="font-medium">Est. Tokens:</span>{' '}
                      {prompt.estimated_tokens.toLocaleString()}
                    </div>
                  )}
                  {prompt.model_name && (
                    <div>
                      <span className="font-medium">Model:</span> {prompt.model_name}
                    </div>
                  )}
                </div>
              )}

              {/* Metadata */}
              <div className="flex flex-wrap gap-4 text-xs text-gray-500">
                <div>
                  <span className="font-medium">Request ID:</span>{' '}
                  <span className="font-mono">{prompt.request_id}</span>
                </div>
                {prompt.session_id && (
                  <div>
                    <span className="font-medium">Session:</span>{' '}
                    <span className="font-mono">{prompt.session_id}</span>
                  </div>
                )}
                {prompt.posted_at && (
                  <div>
                    <span className="font-medium">Posted:</span> {formatDate(prompt.posted_at)}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* No Results */}
      {data && data.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p>No user prompts found.</p>
          {filterIssueNumber && <p className="text-sm">Try clearing the filter.</p>}
        </div>
      )}

      {/* Pagination (only when not filtering) */}
      {!filterIssueNumber && data && data.length > limit && (
        <div className="mt-6 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            Showing {offset + 1} - {Math.min(offset + limit, totalCount)} of {totalCount} prompts
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
