/**
 * Plans Panel - Database-driven planning system
 *
 * Displays planned features, sessions, and work items fetched from the API.
 */

import { useQuery } from '@tanstack/react-query';
import { plannedFeaturesClient, PlannedFeature } from '../api/plannedFeaturesClient';

export function PlansPanel() {
  // Fetch all features
  const {
    data: features,
    isLoading,
    error
  } = useQuery({
    queryKey: ['planned-features'],
    queryFn: () => plannedFeaturesClient.getAll({ limit: 200 }),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['planned-features-stats'],
    queryFn: () => plannedFeaturesClient.getStats(),
    refetchInterval: 60000, // Refresh every 60 seconds
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

  // Group features by status
  const inProgress = features?.filter(f => f.status === 'in_progress') || [];
  const planned = features?.filter(f => f.status === 'planned') || [];
  const completed = features?.filter(f => f.status === 'completed')
    .sort((a, b) => {
      // Sort by completed_at DESC (most recent first)
      const dateA = new Date(a.completed_at || 0);
      const dateB = new Date(b.completed_at || 0);
      return dateB.getTime() - dateA.getTime();
    }) || [];

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Pending Work Items
      </h2>

      {/* Statistics Dashboard */}
      {stats && (
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
            completed.slice(0, 15).map(feature => (
              <FeatureItem key={feature.id} feature={feature} />
            ))
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
        {feature.github_issue_number && (
          <div className="text-sm text-blue-600 mt-1">
            <a
              href={`https://github.com/user/repo/issues/${feature.github_issue_number}`}
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
