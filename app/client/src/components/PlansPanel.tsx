/**
 * Plans Panel - Database-driven planning system
 *
 * Displays planned features, sessions, and work items fetched from the API.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PlannedFeature, plannedFeaturesClient, PlannedFeaturesStats } from '../api/plannedFeaturesClient';
import { apiConfig } from '../config/api';

// ============================================================================
// Utility Functions
// ============================================================================

function formatDate(dateStr?: string) {
  if (!dateStr) return null;
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

// Priority sort order: high > medium > low
const priorityOrder = { high: 1, medium: 2, low: 3 };

// Sort function for planned/in-progress: priority DESC, then estimated_hours ASC
function sortByPriority(a: PlannedFeature, b: PlannedFeature) {
  // Sort by priority first (high to low)
  const priorityA = priorityOrder[a.priority as keyof typeof priorityOrder] || 99;
  const priorityB = priorityOrder[b.priority as keyof typeof priorityOrder] || 99;
  if (priorityA !== priorityB) return priorityA - priorityB;

  // Then by estimated hours (ascending - quick wins first)
  const hoursA = a.estimated_hours || 999;
  const hoursB = b.estimated_hours || 999;
  return hoursA - hoursB;
}

// Sort function for completed items: completed_at DESC (most recent first)
function sortByCompletedDate(a: PlannedFeature, b: PlannedFeature) {
  const dateA = new Date(a.completed_at || 0);
  const dateB = new Date(b.completed_at || 0);
  return dateB.getTime() - dateA.getTime();
}

// Apply filters and group features by status
function groupFeaturesByStatus(
  features: PlannedFeature[] | undefined,
  filterPriority: string | null,
  filterType: string | null
) {
  const filteredFeatures = features?.filter(f => {
    if (filterPriority && f.priority !== filterPriority) return false;
    if (filterType && f.item_type !== filterType) return false;
    return true;
  }) || [];

  return {
    inProgress: filteredFeatures
      .filter(f => f.status === 'in_progress')
      .sort(sortByPriority),
    planned: filteredFeatures
      .filter(f => f.status === 'planned')
      .sort(sortByPriority),
    completed: filteredFeatures
      .filter(f => f.status === 'completed')
      .sort(sortByCompletedDate)
  };
}

// ============================================================================
// Sub-Components
// ============================================================================

interface LoadingStateProps {
  message: string;
}

function LoadingState({ message }: LoadingStateProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-center p-8">
        <div className="animate-pulse text-gray-500">{message}</div>
      </div>
    </div>
  );
}

interface ErrorStateProps {
  message: string;
}

function ErrorState({ message }: ErrorStateProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="text-red-600">{message}</div>
    </div>
  );
}

interface PlanStatisticsProps {
  stats?: PlannedFeaturesStats;
  isLoading: boolean;
  error: Error | null;
}

function PlanStatistics({ stats, isLoading, error }: PlanStatisticsProps) {
  if (error) {
    return (
      <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-yellow-800 text-sm">
          Unable to load statistics: {error.message}
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <p className="text-gray-500 text-sm">Loading statistics...</p>
      </div>
    );
  }

  if (!stats) return null;

  const totalItems = Object.values(stats.by_status).reduce((a, b) => a + b, 0);

  return (
    <div className="mb-6 grid grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
      <div>
        <div className="text-sm text-gray-600">Total Items</div>
        <div className="text-2xl font-bold">{totalItems}</div>
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
  );
}

interface PlanFiltersProps {
  filterPriority: string | null;
  filterType: string | null;
  onPriorityChange: (priority: string | null) => void;
  onTypeChange: (type: string | null) => void;
  onClearFilters: () => void;
}

function PlanFilters({
  filterPriority,
  filterType,
  onPriorityChange,
  onTypeChange,
  onClearFilters
}: PlanFiltersProps) {
  return (
    <div className="mb-6 flex gap-4 items-center">
      <label className="flex items-center gap-2">
        <span className="text-sm text-gray-600">Priority:</span>
        <select
          value={filterPriority || 'all'}
          onChange={(e) => onPriorityChange(e.target.value === 'all' ? null : e.target.value)}
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
          onChange={(e) => onTypeChange(e.target.value === 'all' ? null : e.target.value)}
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
          onClick={onClearFilters}
          className="text-sm text-blue-600 hover:underline"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}

interface FeatureListSectionProps {
  title: string;
  icon: string;
  colorClass: string;
  features: PlannedFeature[];
  emptyMessage: string;
  showAllCompleted?: boolean;
  onToggleShowAll?: () => void;
}

function FeatureListSection({
  title,
  icon,
  colorClass,
  features,
  emptyMessage,
  showAllCompleted,
  onToggleShowAll
}: FeatureListSectionProps) {
  const displayedFeatures = showAllCompleted !== undefined && !showAllCompleted
    ? features.slice(0, 15)
    : features;

  return (
    <div className="mb-8">
      <h3 className={`text-lg font-semibold ${colorClass} mb-3 flex items-center`}>
        <span className="mr-2">{icon}</span> {title}
      </h3>
      <div className="space-y-3 pl-6">
        {features.length === 0 ? (
          <p className="text-gray-500 italic">{emptyMessage}</p>
        ) : (
          <>
            {displayedFeatures.map(feature => (
              <FeatureItem key={feature.id} feature={feature} />
            ))}
            {showAllCompleted !== undefined && onToggleShowAll && features.length > 15 && (
              <button
                onClick={onToggleShowAll}
                className="text-sm text-blue-600 hover:underline mt-2"
              >
                {showAllCompleted
                  ? 'Show less'
                  : `Show ${features.length - 15} more completed items`}
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}

interface FeatureItemHeaderProps {
  title: string;
  isInProgress: boolean;
  priority?: string;
  estimatedHours?: number;
  isCompleted: boolean;
}

function FeatureItemHeader({
  title,
  isInProgress,
  priority,
  estimatedHours,
  isCompleted
}: FeatureItemHeaderProps) {
  const priorityColor = {
    high: 'bg-red-100 text-red-700',
    medium: 'bg-orange-100 text-orange-700',
    low: 'bg-blue-100 text-blue-700'
  }[priority || 'low'];

  const isQuickWin = estimatedHours && estimatedHours <= 2.0 && !isCompleted;

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <div className="font-medium text-gray-700">{title}</div>
      {isInProgress && (
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
          In Progress
        </span>
      )}
      {priority && (
        <span className={`text-xs px-2 py-0.5 rounded ${priorityColor}`}>
          {priority.toUpperCase()}
        </span>
      )}
      {isQuickWin && (
        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded font-medium">
          ⚡ QUICK WIN
        </span>
      )}
    </div>
  );
}

interface FeatureItemMetadataProps {
  completedAt?: string;
  actualHours?: number;
  githubIssueNumber?: number;
  estimatedHours?: number;
  isCompleted: boolean;
  tags?: string[];
}

function FeatureItemMetadata({
  completedAt,
  actualHours,
  githubIssueNumber,
  estimatedHours,
  isCompleted,
  tags
}: FeatureItemMetadataProps) {
  return (
    <>
      {completedAt && (
        <div className="text-sm text-gray-500">
          Completed {formatDate(completedAt)}
          {actualHours && ` (~${actualHours} hours)`}
        </div>
      )}

      {tags && tags.length > 0 && (
        <div className="flex gap-2 mt-2 flex-wrap">
          {tags.map(tag => (
            <span
              key={tag}
              className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {githubIssueNumber && githubIssueNumber > 0 && (
        <div className="text-sm text-blue-600 mt-1">
          <a
            href={apiConfig.github.getIssueUrl(githubIssueNumber)}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:underline"
          >
            Issue #{githubIssueNumber}
          </a>
        </div>
      )}

      {!isCompleted && estimatedHours && (
        <div className="text-sm text-gray-500 mt-1">
          Estimated: {estimatedHours} hours
        </div>
      )}
    </>
  );
}

interface FeatureItemDescriptionProps {
  description?: string;
  completionNotes?: string;
}

function FeatureItemDescription({
  description,
  completionNotes
}: FeatureItemDescriptionProps) {
  return (
    <>
      {description && (
        <div className="text-sm text-gray-600 mt-1">
          {description}
        </div>
      )}

      {completionNotes && (
        <div className="text-sm text-gray-600 mt-1">
          {completionNotes.includes('\n') ? (
            <ul className="list-disc pl-5 space-y-0.5">
              {completionNotes.split('\n').filter(line => line.trim()).map((line, i) => (
                <li key={i}>{line.replace(/^[•\-*]\s*/, '')}</li>
              ))}
            </ul>
          ) : (
            <div>{completionNotes}</div>
          )}
        </div>
      )}
    </>
  );
}

/**
 * Individual feature/session item component
 */
function FeatureItem({ feature }: { feature: PlannedFeature }) {
  const isCompleted = feature.status === 'completed';
  const isInProgress = feature.status === 'in_progress';

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
        <FeatureItemHeader
          title={feature.title}
          isInProgress={isInProgress}
          priority={feature.priority}
          estimatedHours={feature.estimated_hours}
          isCompleted={isCompleted}
        />
        <FeatureItemMetadata
          completedAt={feature.completed_at}
          actualHours={feature.actual_hours}
          githubIssueNumber={feature.github_issue_number}
          estimatedHours={feature.estimated_hours}
          isCompleted={isCompleted}
          tags={feature.tags}
        />
        <FeatureItemDescription
          description={feature.description}
          completionNotes={feature.completion_notes}
        />
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

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
    return <LoadingState message="Loading plans..." />;
  }

  if (error) {
    return <ErrorState message={`Error loading plans: ${(error as Error).message}`} />;
  }

  // Group features by status with filters applied
  const { inProgress, planned, completed } = groupFeaturesByStatus(
    features,
    filterPriority,
    filterType
  );

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Pending Work Items
      </h2>

      <PlanFilters
        filterPriority={filterPriority}
        filterType={filterType}
        onPriorityChange={setFilterPriority}
        onTypeChange={setFilterType}
        onClearFilters={() => {
          setFilterPriority(null);
          setFilterType(null);
        }}
      />

      <PlanStatistics
        stats={stats}
        isLoading={statsLoading}
        error={statsError as Error | null}
      />

      <FeatureListSection
        title="In Progress"
        icon="🔄"
        colorClass="text-blue-700"
        features={inProgress}
        emptyMessage="No items in progress"
      />

      <FeatureListSection
        title="Planned Fixes & Enhancements"
        icon="📋"
        colorClass="text-purple-700"
        features={planned}
        emptyMessage="No planned items"
      />

      <FeatureListSection
        title="Recently Completed"
        icon="✅"
        colorClass="text-green-700"
        features={completed}
        emptyMessage="No completed items"
        showAllCompleted={showAllCompleted}
        onToggleShowAll={() => setShowAllCompleted(!showAllCompleted)}
      />

      {/* Footer Note */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <p className="text-sm text-gray-500 italic">
          Note: All items above are optional enhancements. System is fully functional and production-ready as-is.
        </p>
      </div>
    </div>
  );
}
