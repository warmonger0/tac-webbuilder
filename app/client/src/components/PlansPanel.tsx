/**
 * Plans Panel - Database-driven planning system
 *
 * Displays planned features, sessions, and work items fetched from the API.
 */

import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { PlannedFeature, plannedFeaturesClient, PlannedFeaturesStats, PlanSummary } from '../api/plannedFeaturesClient';
import { PreflightChecksResponse, systemClient } from '../api/systemClient';
import { PreflightCheckModal } from './PreflightCheckModal';
import { apiConfig } from '../config/api';
import { useGlobalWebSocket } from '../contexts/GlobalWebSocketContext';
import { getWorkflowsByCategory } from '../workflows';

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
  onGeneratePlan?: (id: number) => void;
  generatingPlanId?: number | null;
  generatedPlans?: Map<number, PlanSummary>;
  onWorkflowChange?: (featureId: number, workflowType: string) => void;
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
  startingAutomationId,
  onGeneratePlan,
  generatingPlanId,
  generatedPlans,
  onWorkflowChange
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
                onGeneratePlan={onGeneratePlan}
                isGeneratingPlan={generatingPlanId === feature.id}
                generatedPlan={generatedPlans?.get(feature.id)}
                onWorkflowChange={onWorkflowChange}
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
  isStartingAutomation,
  onGeneratePlan,
  isGeneratingPlan,
  generatedPlan,
  onWorkflowChange
}: {
  feature: PlannedFeature;
  onStartAutomation?: (id: number) => void;
  isStartingAutomation?: boolean;
  onGeneratePlan?: (id: number) => void;
  isGeneratingPlan?: boolean;
  generatedPlan?: PlanSummary;
  onWorkflowChange?: (featureId: number, workflowType: string) => void;
}) {
  const [showPlan, setShowPlan] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState(feature.workflow_type || 'adw_sdlc_complete_iso');
  const isCompleted = feature.status === 'completed';
  const isInProgress = feature.status === 'in_progress';
  const isPlanned = feature.status === 'planned';

  // Get available workflows for dropdown
  const availableWorkflows = useMemo(() => getWorkflowsByCategory('full-sdlc'), []);

  // Handle workflow change
  const handleWorkflowChange = (newWorkflow: string) => {
    setSelectedWorkflow(newWorkflow);
    if (onWorkflowChange) {
      onWorkflowChange(feature.id, newWorkflow);
    }
  };

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
        {/* Action buttons for planned/in-progress features */}
        {(isPlanned || isInProgress) && (
          <div className="mt-2 space-y-2">
            {/* Workflow Selector */}
            {onStartAutomation && (
              <div className="flex flex-col gap-1">
                <label htmlFor={`workflow-selector-${feature.id}`} className="text-xs font-medium text-gray-700">
                  Workflow:
                </label>
                <select
                  id={`workflow-selector-${feature.id}`}
                  value={selectedWorkflow}
                  onChange={(e) => handleWorkflowChange(e.target.value)}
                  disabled={isStartingAutomation}
                  className="px-3 py-2 border border-gray-300 rounded text-sm bg-white hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed max-w-md"
                  title={availableWorkflows.find(w => w.script_name === selectedWorkflow)?.use_case || ''}
                >
                  {availableWorkflows.map(workflow => (
                    <option key={workflow.script_name} value={workflow.script_name}>
                      {workflow.name} - {workflow.description.substring(0, 80)}...
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 italic">
                  {availableWorkflows.find(w => w.script_name === selectedWorkflow)?.use_case || ''}
                </p>
              </div>
            )}

            <div className="flex gap-2 flex-wrap">
              {/* Generate Plan button */}
              {onGeneratePlan && (
                <button
                  onClick={() => onGeneratePlan(feature.id)}
                  disabled={isGeneratingPlan}
                  className="px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {isGeneratingPlan ? '⏳ Generating...' : '📋 Generate Plan'}
                </button>
              )}

              {/* Start/Retry Automation button */}
              {onStartAutomation && (
                <button
                  onClick={() => onStartAutomation(feature.id)}
                  disabled={isStartingAutomation}
                  className={`px-3 py-1 text-white text-sm rounded disabled:bg-gray-400 disabled:cursor-not-allowed ${
                    isPlanned
                      ? 'bg-blue-600 hover:bg-blue-700'
                      : 'bg-orange-600 hover:bg-orange-700'
                  }`}
                >
                  {isStartingAutomation
                    ? '⏳ Running checks...'
                    : isPlanned
                      ? '🚀 Start Automation'
                      : '🔄 Retry Automation'
                  }
                </button>
              )}
            </div>
          </div>
        )}

        {/* Generated plan display (collapsible) */}
        {generatedPlan && (
          <div className="mt-3 border border-purple-300 rounded-lg overflow-hidden bg-purple-50">
            <button
              onClick={() => setShowPlan(!showPlan)}
              className="w-full px-4 py-3 bg-purple-100 hover:bg-purple-200 text-left font-medium text-sm flex items-center justify-between"
            >
              <span className="flex items-center gap-2">
                <span className="text-lg">📝</span>
                <span>
                  Implementation Prompts ({generatedPlan.total_phases} {generatedPlan.total_phases === 1 ? 'phase' : 'phases'},
                  ~{generatedPlan.total_estimated_hours}h total)
                </span>
              </span>
              <span className="text-purple-600 font-bold">{showPlan ? '▼' : '▶'}</span>
            </button>

            {showPlan && (
              <div className="p-4 space-y-4">
                {generatedPlan.phases.map((phase) => (
                  <div key={phase.phase_number} className="border border-purple-200 rounded-lg bg-white overflow-hidden">
                    {/* Phase Header */}
                    <div className="px-4 py-3 bg-purple-50 border-b border-purple-200">
                      <div className="font-bold text-gray-900 mb-1">
                        Phase {phase.phase_number}/{phase.total_phases}: {phase.title}
                      </div>
                      <div className="text-sm text-gray-600">{phase.description}</div>
                      <div className="text-xs text-gray-500 mt-2">
                        ⏱️ {phase.estimated_hours}h | 📁 {phase.files_to_modify.length} files | 📄 {phase.prompt_filename}
                      </div>
                    </div>

                    {/* Full Markdown Prompt */}
                    <div className="p-4">
                      <div className="mb-3 flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">Full Implementation Prompt:</span>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(phase.markdown_prompt);
                            // Show success feedback
                            const btn = document.activeElement as HTMLButtonElement;
                            const originalText = btn.textContent;
                            btn.textContent = '✅ Copied!';
                            setTimeout(() => { btn.textContent = originalText; }, 2000);
                          }}
                          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded font-medium"
                        >
                          📋 Copy Full Prompt
                        </button>
                      </div>

                      {/* Markdown Preview (scrollable) */}
                      <div className="relative">
                        <pre className="text-xs bg-gray-900 text-gray-100 p-4 rounded overflow-x-auto max-h-96 overflow-y-auto border border-gray-700">
                          <code>{phase.markdown_prompt}</code>
                        </pre>
                      </div>

                      {/* Quick file list */}
                      {phase.files_to_modify.length > 0 && (
                        <details className="mt-3">
                          <summary className="cursor-pointer text-sm text-blue-600 hover:underline">
                            Files to modify ({phase.files_to_modify.length})
                          </summary>
                          <ul className="mt-2 pl-4 list-disc text-xs text-gray-600 max-h-32 overflow-y-auto">
                            {phase.files_to_modify.map((file, idx) => (
                              <li key={idx} className="font-mono">{file}</li>
                            ))}
                          </ul>
                        </details>
                      )}
                    </div>
                  </div>
                ))}

                {/* Instructions */}
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-900">
                    <strong>How to use:</strong> Click "Copy Full Prompt" for each phase, then paste into Panel 1 (New Request) to execute the workflow.
                  </p>
                </div>
              </div>
            )}
          </div>
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

  // Generated plans state
  const [generatedPlans, setGeneratedPlans] = useState<Map<number, PlanSummary>>(new Map());

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

  // Load persisted plans from features when they arrive
  // This runs when features are first loaded or when they change
  useEffect(() => {
    if (features && features.length > 0) {
      const persistedPlans = new Map<number, PlanSummary>();
      features.forEach(feature => {
        if (feature.generated_plan) {
          persistedPlans.set(feature.id, feature.generated_plan);
        }
      });
      setGeneratedPlans(persistedPlans);
    }
  }, [features]);

  // Generate plan mutation
  const generatePlanMutation = useMutation({
    mutationFn: (featureId: number) => plannedFeaturesClient.generatePlan(featureId),
    onSuccess: (data, featureId) => {
      // Store the generated plan
      setGeneratedPlans(prev => new Map(prev).set(featureId, data));

      // Show success message
      setAutomationMessage({
        type: 'success',
        text: `✅ Plan generated: ${data.total_phases} ${data.total_phases === 1 ? 'phase' : 'phases'}, ~${data.total_estimated_hours}h total`
      });

      // Clear message after 10 seconds
      setTimeout(() => setAutomationMessage(null), 10000);
    },
    onError: (error: Error) => {
      setAutomationMessage({
        type: 'error',
        text: `❌ Failed to generate plan: ${error.message}`
      });

      // Clear message after 10 seconds
      setTimeout(() => setAutomationMessage(null), 10000);
    }
  });

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

  // Handle generate plan button click
  const handleGeneratePlan = (featureId: number) => {
    generatePlanMutation.mutate(featureId);
  };

  // Handle workflow type change - update feature immediately
  const handleWorkflowChange = async (featureId: number, workflowType: string) => {
    try {
      await plannedFeaturesClient.update(featureId, { workflow_type: workflowType });
      // Invalidate queries to refetch updated data
      queryClient.invalidateQueries({ queryKey: ['planned-features'] });
    } catch (error) {
      console.error('Failed to update workflow type:', error);
      setAutomationMessage({
        type: 'error',
        text: `❌ Failed to update workflow: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
      setTimeout(() => setAutomationMessage(null), 5000);
    }
  };

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
        onGeneratePlan={handleGeneratePlan}
        generatingPlanId={generatePlanMutation.isPending ? generatePlanMutation.variables : null}
        generatedPlans={generatedPlans}
        onWorkflowChange={handleWorkflowChange}
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
        onGeneratePlan={handleGeneratePlan}
        generatingPlanId={generatePlanMutation.isPending ? generatePlanMutation.variables : null}
        generatedPlans={generatedPlans}
        onWorkflowChange={handleWorkflowChange}
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
