/**
 * Plans Panel - Database-driven planning system
 *
 * Displays planned features, sessions, and work items fetched from the API.
 */

import { useState, useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { PlannedFeature, plannedFeaturesClient, PlannedFeaturesStats } from '../api/plannedFeaturesClient';
import { systemClient, PreflightChecksResponse } from '../api/systemClient';
import { PreflightCheckModal } from './PreflightCheckModal';
import { apiConfig } from '../config/api';
import { useGlobalWebSocket } from '../contexts/GlobalWebSocketContext';

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
  features: PlannedFeature[] | null | undefined,
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
  onStartAutomation?: (id: number) => void;
  startingAutomationId?: number | null;
}

function FeatureListSection({
  title,
  icon,
  colorClass,
  features,
  emptyMessage,
  showAllCompleted,
  onToggleShowAll,
  onStartAutomation,
  startingAutomationId
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
              <FeatureItem
                key={feature.id}
                feature={feature}
                onStartAutomation={onStartAutomation}
                isStartingAutomation={startingAutomationId === feature.id}
              />
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
                <li key={`note-${i}`}>{line.replace(/^[•\-*]\s*/, '')}</li>
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
function FeatureItem({
  feature,
  onStartAutomation,
  isStartingAutomation
}: {
  feature: PlannedFeature;
  onStartAutomation?: (id: number) => void;
  isStartingAutomation?: boolean;
}) {
  const isCompleted = feature.status === 'completed';
  const isInProgress = feature.status === 'in_progress';
  const isPlanned = feature.status === 'planned';

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
        {/* Start Automation button for planned features */}
        {isPlanned && onStartAutomation && (
          <button
            onClick={() => onStartAutomation(feature.id)}
            disabled={isStartingAutomation}
            className="mt-2 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isStartingAutomation ? '⏳ Running checks...' : '🚀 Start Automation'}
          </button>
        )}
        {/* Retry button for in-progress features */}
        {isInProgress && onStartAutomation && (
          <button
            onClick={() => onStartAutomation(feature.id)}
            disabled={isStartingAutomation}
            className="mt-2 px-3 py-1 bg-orange-600 text-white text-sm rounded hover:bg-orange-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isStartingAutomation ? '⏳ Running checks...' : '🔄 Retry Automation'}
          </button>
        )}
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
  const [automationMessage, setAutomationMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Pre-flight check modal state
  const [showPreflightModal, setShowPreflightModal] = useState(false);
  const [preflightResults, setPreflightResults] = useState<PreflightChecksResponse | null>(null);
  const [pendingFeature, setPendingFeature] = useState<PlannedFeature | null>(null);
  const [isRunningPreflight, setIsRunningPreflight] = useState(false);

  const queryClient = useQueryClient();

  // WebSocket connection for real-time updates
  const {
    plannedFeatures: features,
    plannedFeaturesStats: stats,
    plannedFeaturesConnectionState: { isConnected, connectionQuality, lastUpdated: wsLastUpdated },
  } = useGlobalWebSocket();

  // Loading state: show loading only if features array is null/undefined (not yet fetched)
  // An empty array [] is a valid state (no features in database)
  const isLoading = features === undefined || features === null;
  const error = null; // WebSocket handles errors internally

  // Start automation mutation
  const startAutomationMutation = useMutation({
    mutationFn: (featureId: number) => plannedFeaturesClient.startAutomation(featureId),
    onSuccess: (data) => {
      // Invalidate queries to refetch updated data
      queryClient.invalidateQueries({ queryKey: ['planned-features'] });
      queryClient.invalidateQueries({ queryKey: ['planned-features-stats'] });

      // Show success message
      setAutomationMessage({
        type: 'success',
        text: `✅ ${data.message} (${data.ready_phases} ready, ${data.queued_phases} queued)`
      });

      // Clear message after 10 seconds
      setTimeout(() => setAutomationMessage(null), 10000);
    },
    onError: (error: Error) => {
      setAutomationMessage({
        type: 'error',
        text: `❌ Failed to start automation: ${error.message}`
      });

      // Clear message after 10 seconds
      setTimeout(() => setAutomationMessage(null), 10000);
    }
  });

  // Run pre-flight checks before starting automation
  const handleStartAutomation = async (featureId: number) => {
    const feature = features?.find(f => f.id === featureId);
    if (!feature) return;

    setPendingFeature(feature);
    setIsRunningPreflight(true);

    try {
      // Run pre-flight checks (skip tests for faster UX, include dry-run and issue number)
      const results = await systemClient.getPreflightChecks({
        skipTests: true,
        issueNumber: feature.github_issue_number,
        runDryRun: true,
        featureId: feature.id,
        featureTitle: feature.title,
      });

      setPreflightResults(results);
      setShowPreflightModal(true);
    } catch (error) {
      setAutomationMessage({
        type: 'error',
        text: `❌ Pre-flight checks failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
      setTimeout(() => setAutomationMessage(null), 10000);
    } finally {
      setIsRunningPreflight(false);
    }
  };

  // Confirm and proceed with automation after pre-flight checks
  const handlePreflightConfirm = () => {
    if (pendingFeature) {
      setShowPreflightModal(false);
      startAutomationMutation.mutate(pendingFeature.id);
      setPendingFeature(null);
      setPreflightResults(null);
    }
  };

  // Cancel automation
  const handlePreflightCancel = () => {
    setShowPreflightModal(false);
    setPendingFeature(null);
    setPreflightResults(null);
  };

  // Group features by status with filters applied (memoized to prevent unnecessary re-sorting)
  // MUST be called before any early returns to satisfy Rules of Hooks
  const { inProgress, planned, completed } = useMemo(
    () => groupFeaturesByStatus(features, filterPriority, filterType),
    [features, filterPriority, filterType]
  );

  if (isLoading) {
    return <LoadingState message="Loading plans..." />;
  }

  if (error) {
    return <ErrorState message={`Error loading plans: ${(error as Error).message}`} />;
  }

  // Handle manual refresh (for WebSocket reconnection)
  const handleRefresh = () => {
    // Force page reload to reconnect WebSocket
    window.location.reload();
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          Pending Work Items
        </h2>
        <div className="flex items-center gap-3">
          {/* WebSocket connection status */}
          <div className="flex items-center gap-2">
            <span
              className={`inline-block w-2 h-2 rounded-full ${
                isConnected
                  ? connectionQuality === 'excellent'
                    ? 'bg-green-500'
                    : connectionQuality === 'good'
                    ? 'bg-yellow-500'
                    : 'bg-orange-500'
                  : 'bg-red-500'
              }`}
              title={`Connection: ${isConnected ? connectionQuality : 'disconnected'}`}
            />
            <span className="text-sm text-gray-500">
              {isConnected ? 'Live' : 'Disconnected'}
              {wsLastUpdated && (
                <> • {new Date(wsLastUpdated).toLocaleTimeString()}</>
              )}
            </span>
          </div>
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-1.5"
            title="Reconnect WebSocket"
          >
            <span>🔄</span>
            <span>Reconnect</span>
          </button>
        </div>
      </div>

      {/* Automation message banner */}
      {automationMessage && (
        <div className={`mb-6 p-4 rounded-lg ${
          automationMessage.type === 'success'
            ? 'bg-green-50 border border-green-200 text-green-800'
            : 'bg-red-50 border border-red-200 text-red-800'
        }`}>
          <p className="text-sm">{automationMessage.text}</p>
        </div>
      )}

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
        stats={stats || undefined}
        isLoading={false}
        error={null}
      />

      <FeatureListSection
        title="In Progress"
        icon="🔄"
        colorClass="text-blue-700"
        features={inProgress}
        emptyMessage="No items in progress"
        onStartAutomation={handleStartAutomation}
        startingAutomationId={
          isRunningPreflight && pendingFeature
            ? pendingFeature.id
            : startAutomationMutation.isPending
            ? startAutomationMutation.variables
            : null
        }
      />

      <FeatureListSection
        title="Planned Fixes & Enhancements"
        icon="📋"
        colorClass="text-purple-700"
        features={planned}
        emptyMessage="No planned items"
        onStartAutomation={handleStartAutomation}
        startingAutomationId={
          isRunningPreflight && pendingFeature
            ? pendingFeature.id
            : startAutomationMutation.isPending
            ? startAutomationMutation.variables
            : null
        }
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

      {/* Pre-flight Check Modal */}
      {showPreflightModal && preflightResults && pendingFeature && (
        <PreflightCheckModal
          results={preflightResults}
          featureTitle={pendingFeature.title}
          onConfirm={handlePreflightConfirm}
          onCancel={handlePreflightCancel}
        />
      )}
    </div>
  );
}
