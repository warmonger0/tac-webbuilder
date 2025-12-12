/**
 * Plans Panel - Database-driven planning system
 *
 * Displays planned features, sessions, and work items fetched from the API.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PlannedFeature, plannedFeaturesClient } from '../api/plannedFeaturesClient';
import { apiConfig } from '../config/api';

export function PlansPanel() {
  // Local state for UI controls
  const [showAllCompleted, setShowAllCompleted] = useState(false);
  const [filterPriority, setFilterPriority] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string | null>(null);

  // Fetch all features
  const {
    data: features,
    isLoading,
    error
  } = useQuery({
    queryKey: ['planned-features'],
    queryFn: () => plannedFeaturesClient.getAll({ limit: 200 }),
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes (plans data changes infrequently)
    refetchIntervalInBackground: false, // Don't poll when tab hidden
    refetchOnWindowFocus: true, // Refetch when user returns to tab
  });

  // Fetch statistics
  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError
  } = useQuery({
    queryKey: ['planned-features-stats'],
    queryFn: () => plannedFeaturesClient.getStats(),
    refetchInterval: 10 * 60 * 1000, // Refresh every 10 minutes
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-center p-8">
          <div className="animate-pulse text-gray-500">Loading plans...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-red-600">
          Error loading plans: {(error as Error).message}
        </div>
      </div>
    );
  }

  // Apply filters
  const filteredFeatures = features?.filter(f => {
    if (filterPriority && f.priority !== filterPriority) return false;
    if (filterType && f.item_type !== filterType) return false;
    return true;
  }) || [];

  // Priority sort order: high > medium > low
  const priorityOrder = { high: 1, medium: 2, low: 3 };

  // Sort function for planned/in-progress: priority DESC, then estimated_hours ASC
  const sortByPriority = (a: PlannedFeature, b: PlannedFeature) => {
    // Sort by priority first (high to low)
    const priorityA = priorityOrder[a.priority as keyof typeof priorityOrder] || 99;
    const priorityB = priorityOrder[b.priority as keyof typeof priorityOrder] || 99;
    if (priorityA !== priorityB) return priorityA - priorityB;

    // Then by estimated hours (ascending - quick wins first)
    const hoursA = a.estimated_hours || 999;
    const hoursB = b.estimated_hours || 999;
    return hoursA - hoursB;
  };

  // Group features by status
  const inProgress = filteredFeatures
    .filter(f => f.status === 'in_progress')
    .sort(sortByPriority);

  const planned = filteredFeatures
    .filter(f => f.status === 'planned')
    .sort(sortByPriority);

  const completed = filteredFeatures.filter(f => f.status === 'completed')
    .sort((a, b) => {
      // Sort by completed_at DESC (most recent first)
      const dateA = new Date(a.completed_at || 0);
      const dateB = new Date(b.completed_at || 0);
      return dateB.getTime() - dateA.getTime();
    });

  // Slice completed items based on showAllCompleted state
  const displayedCompleted = showAllCompleted ? completed : completed.slice(0, 15);

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Pending Work Items
      </h2>

      {/* Filters */}
      <div className="mb-6 flex gap-4 items-center">
        <label className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Priority:</span>
          <select
            value={filterPriority || 'all'}
            onChange={(e) => setFilterPriority(e.target.value === 'all' ? null : e.target.value)}
            className="border border-gray-300 rounded px-2 py-1 text-sm"
          >
            <option value="all">All</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </label>
        <label className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Type:</span>
          <select
            value={filterType || 'all'}
            onChange={(e) => setFilterType(e.target.value === 'all' ? null : e.target.value)}
            className="border border-gray-300 rounded px-2 py-1 text-sm"
          >
            <option value="all">All</option>
            <option value="bug">Bug</option>
            <option value="enhancement">Enhancement</option>
            <option value="feature">Feature</option>
            <option value="session">Session</option>
          </select>
        </label>
        {(filterPriority || filterType) && (
          <button
            onClick={() => {
              setFilterPriority(null);
              setFilterType(null);
            }}
            className="text-sm text-blue-600 hover:underline"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Statistics Dashboard */}
      {statsError && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-yellow-800 text-sm">
            Unable to load statistics: {(statsError as Error).message}
          </p>
        </div>
      )}
      {statsLoading && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <p className="text-gray-500 text-sm">Loading statistics...</p>
        </div>
      )}
      {stats && !statsError && !statsLoading && (
        <div className="mb-6 grid grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
          <div>
            <div className="text-sm text-gray-600">Total Items</div>
            <div className="text-2xl font-bold">
              {Object.values(stats.by_status).reduce((a, b) => a + b, 0)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">In Progress</div>
            <div className="text-2xl font-bold text-blue-600">
              {stats.by_status.in_progress || 0}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Planned</div>
            <div className="text-2xl font-bold text-purple-600">
              {stats.by_status.planned || 0}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Completed</div>
            <div className="text-2xl font-bold text-green-600">
              {stats.by_status.completed || 0}
            </div>
          </div>
        </div>
      )}

      {/* In Progress Section */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-blue-700 mb-3 flex items-center">
          <span className="mr-2">🔄</span> In Progress
        </h3>
        <div className="space-y-2 pl-6">
          {inProgress.length === 0 ? (
            <p className="text-gray-500 italic">No items in progress</p>
          ) : (
            inProgress.map(feature => (
              <FeatureItem key={feature.id} feature={feature} />
            ))
          )}
        </div>
      </div>

      {/* Planned Section */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-purple-700 mb-3 flex items-center">
          <span className="mr-2">📋</span> Planned Fixes & Enhancements
        </h3>
        <div className="space-y-3 pl-6">
          {planned.length === 0 ? (
            <p className="text-gray-500 italic">No planned items</p>
          ) : (
            planned.map(feature => (
              <FeatureItem key={feature.id} feature={feature} />
            ))
          )}
        </div>
      </div>

      {/* Recently Completed Section */}
      <div>
        <h3 className="text-lg font-semibold text-green-700 mb-3 flex items-center">
          <span className="mr-2">✅</span> Recently Completed
        </h3>
        <div className="space-y-3 pl-6">
          {completed.length === 0 ? (
            <p className="text-gray-500 italic">No completed items</p>
          ) : (
            <>
              {displayedCompleted.map(feature => (
                <FeatureItem key={feature.id} feature={feature} />
              ))}
              {completed.length > 15 && !showAllCompleted && (
                <button
                  onClick={() => setShowAllCompleted(true)}
                  className="text-sm text-blue-600 hover:underline mt-2"
                >
                  Show {completed.length - 15} more completed items
                </button>
              )}
              {showAllCompleted && completed.length > 15 && (
                <button
                  onClick={() => setShowAllCompleted(false)}
                  className="text-sm text-blue-600 hover:underline mt-2"
                >
                  Show less
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Footer Note */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <p className="text-sm text-gray-500 italic">
          Note: All items above are optional enhancements. System is fully functional and production-ready as-is.
        </p>
      </div>
    </div>
  );
}

/**
 * Individual feature/session item component
 */
function FeatureItem({ feature }: { feature: PlannedFeature }) {
  const isCompleted = feature.status === 'completed';
  const isInProgress = feature.status === 'in_progress';

  // Format date
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return null;
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Priority badge color
  const priorityColor = {
    high: 'bg-red-100 text-red-700',
    medium: 'bg-orange-100 text-orange-700',
    low: 'bg-blue-100 text-blue-700'
  }[feature.priority || 'low'];

  return (
    <div className="flex items-start">
      <input
        type="checkbox"
        checked={isCompleted}
        className="mt-1 mr-3"
        disabled
        readOnly
        aria-label={isCompleted ? "Completed" : "Not completed"}
        title="Status indicator (read-only)"
      />
      <div className="flex-1">
        {/* Title and Status */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="font-medium text-gray-700">{feature.title}</div>
          {isInProgress && (
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
              In Progress
            </span>
          )}
          {feature.priority && (
            <span className={`text-xs px-2 py-0.5 rounded ${priorityColor}`}>
              {feature.priority.toUpperCase()}
            </span>
          )}
        </div>

        {/* Completion info */}
        {feature.completed_at && (
          <div className="text-sm text-gray-500">
            Completed {formatDate(feature.completed_at)}
            {feature.actual_hours && ` (~${feature.actual_hours} hours)`}
          </div>
        )}

        {/* Description */}
        {feature.description && (
          <div className="text-sm text-gray-600 mt-1">
            {feature.description}
          </div>
        )}

        {/* Completion notes */}
        {feature.completion_notes && (
          <div className="text-sm text-gray-600 mt-1">
            {/* Parse completion notes as list items if they contain bullet points */}
            {feature.completion_notes.includes('\n') ? (
              <ul className="list-disc pl-5 space-y-0.5">
                {feature.completion_notes.split('\n').filter(line => line.trim()).map((line, i) => (
                  <li key={i}>{line.replace(/^[•\-*]\s*/, '')}</li>
                ))}
              </ul>
            ) : (
              <div>{feature.completion_notes}</div>
            )}
          </div>
        )}

        {/* Tags */}
        {feature.tags && feature.tags.length > 0 && (
          <div className="flex gap-2 mt-2 flex-wrap">
            {feature.tags.map(tag => (
              <span
                key={tag}
                className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* GitHub issue link */}
        {feature.github_issue_number && feature.github_issue_number > 0 && (
          <div className="text-sm text-blue-600 mt-1">
            <a
              href={apiConfig.github.getIssueUrl(feature.github_issue_number)}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline"
            >
              Issue #{feature.github_issue_number}
            </a>
          </div>
        )}

        {/* Time estimate (for planned items) */}
        {!isCompleted && feature.estimated_hours && (
          <div className="text-sm text-gray-500 mt-1">
            Estimated: {feature.estimated_hours} hours
          </div>
        )}
      </div>
    </div>
  );
}
