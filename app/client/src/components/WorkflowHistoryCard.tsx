import { useState } from 'react';
import type { WorkflowHistoryItem, PhaseCost, CostBreakdown } from '../types';
import { StatusBadge } from './StatusBadge';
import { CostBreakdownChart } from './CostBreakdownChart';
import { CumulativeCostChart } from './CumulativeCostChart';
import { CacheEfficiencyBadge } from './CacheEfficiencyBadge';
import { TokenBreakdownChart } from './TokenBreakdownChart';
import { PhaseDurationChart } from './PhaseDurationChart';

interface WorkflowHistoryCardProps {
  workflow: WorkflowHistoryItem;
}

// Helper function to transform cost_breakdown.by_phase to PhaseCost[]
function transformToPhaseCosts(costBreakdown?: CostBreakdown): PhaseCost[] | null {
  if (!costBreakdown?.by_phase) return null;

  const phases = Object.entries(costBreakdown.by_phase).map(([phase, cost]) => ({
    phase,
    cost,
    tokens: {
      input_tokens: 0,
      output_tokens: 0,
      cache_creation_tokens: 0,
      cache_read_tokens: 0,
    },
  }));

  return phases.length > 0 ? phases : null;
}

// Helper function to calculate budget delta
function calculateBudgetDelta(
  estimated: number,
  actual: number
): { delta: number; percentage: number; status: 'under' | 'over' | 'neutral' } {
  const delta = actual - estimated;
  const percentage = estimated > 0 ? (delta / estimated) * 100 : 0;

  let status: 'under' | 'over' | 'neutral';
  if (actual < estimated * 0.95) {
    status = 'under';
  } else if (actual > estimated * 1.05) {
    status = 'over';
  } else {
    status = 'neutral';
  }

  return { delta, percentage, status };
}

// Helper function to calculate retry cost
function calculateRetryCost(workflow: WorkflowHistoryItem): number | null {
  if (workflow.retry_count === 0) return null;
  if (workflow.actual_cost_total > workflow.estimated_cost_total) {
    return workflow.actual_cost_total - workflow.estimated_cost_total;
  }
  return null;
}

// Helper function to calculate cache savings
function calculateCacheSavings(workflow: WorkflowHistoryItem): number {
  // Cache hits are ~90% cheaper than cache misses
  // Assuming cache miss cost is standard input token cost
  const cacheHitCostPerToken = workflow.cost_per_token * 0.1;
  const cacheMissCostPerToken = workflow.cost_per_token;
  const savings =
    workflow.cache_hit_tokens * (cacheMissCostPerToken - cacheHitCostPerToken);
  return savings;
}

// Helper function to truncate text
function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

// Helper function to get classification badge color
function getClassificationColor(classification?: string): string {
  switch (classification?.toLowerCase()) {
    case 'feature':
      return 'bg-blue-100 text-blue-800 border-blue-300';
    case 'bug':
      return 'bg-red-100 text-red-800 border-red-300';
    case 'chore':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300';
  }
}

// Helper function to format structured input for display
function formatStructuredInputForDisplay(input?: Record<string, any>): Array<{ key: string; value: any }> {
  if (!input) return [];

  return Object.entries(input)
    .filter(([_, value]) => value !== null && value !== undefined)
    .map(([key, value]) => ({ key, value }));
}

export function WorkflowHistoryCard({ workflow }: WorkflowHistoryCardProps) {
  const [showDetails, setShowDetails] = useState(false);

  const formatDate = (timestamp?: string) => {
    if (!timestamp) return 'N/A';
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return 'Invalid date';
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatCost = (cost: number) => {
    return `$${cost.toFixed(4)}`;
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h3 className="text-lg font-semibold text-gray-900">
              ADW: {workflow.adw_id}
            </h3>
            <StatusBadge status={workflow.status} />
            {workflow.structured_input?.classification && (
              <span className={`text-xs px-2 py-1 rounded border ${getClassificationColor(workflow.structured_input.classification)}`}>
                {workflow.structured_input.classification.toUpperCase()}
              </span>
            )}
          </div>
          {workflow.nl_input && (
            <div className="text-sm text-gray-700 mt-2">
              "{truncateText(workflow.nl_input, 60)}"
            </div>
          )}
          {workflow.issue_number && (
            <a
              href={workflow.github_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:text-blue-800 font-medium mt-1 inline-block"
            >
              Issue #{workflow.issue_number}
            </a>
          )}
          {(workflow.workflow_template || workflow.model_used) && (
            <div className="flex flex-wrap gap-4 mt-2 text-sm text-gray-600">
              {workflow.workflow_template && (
                <span>
                  <span className="font-medium">Workflow:</span> {workflow.workflow_template}
                </span>
              )}
              {workflow.model_used && (
                <span>
                  <span className="font-medium">Model:</span> {workflow.model_used}
                </span>
              )}
            </div>
          )}
        </div>
        <div className="text-right text-sm text-gray-600">
          <div>{formatDate(workflow.created_at)}</div>
          {workflow.duration_seconds && (
            <div className="text-gray-500">Duration: {formatDuration(workflow.duration_seconds)}</div>
          )}
        </div>
      </div>

      {/* Metadata Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
        {workflow.current_phase && (
          <div>
            <div className="text-gray-600">Phase</div>
            <div className="font-medium text-gray-900">{workflow.current_phase}</div>
          </div>
        )}
        {workflow.steps_total > 0 && (
          <div>
            <div className="text-gray-600">Progress</div>
            <div className="font-medium text-gray-900">
              {workflow.steps_completed}/{workflow.steps_total} steps
            </div>
          </div>
        )}
      </div>

      {/* Cost & Token Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
        {workflow.actual_cost_total > 0 && (
          <div>
            <div className="text-gray-600">Actual Cost</div>
            <div className="font-semibold text-green-600">{formatCost(workflow.actual_cost_total)}</div>
          </div>
        )}
        {workflow.total_tokens > 0 && (
          <div>
            <div className="text-gray-600">Total Tokens</div>
            <div className="font-medium text-gray-900">{formatNumber(workflow.total_tokens)}</div>
          </div>
        )}
        {workflow.cache_efficiency_percent > 0 && (
          <div>
            <div className="text-gray-600">Cache Efficiency</div>
            <div className="font-medium text-blue-600">{workflow.cache_efficiency_percent.toFixed(1)}%</div>
          </div>
        )}
        {workflow.retry_count > 0 && (
          <div>
            <div className="text-gray-600">Retries</div>
            <div className="font-medium text-orange-600">{workflow.retry_count}</div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {workflow.error_message && (
        <div className="mb-4">
          <div className="text-sm font-medium text-red-700 mb-1">Error:</div>
          <div className="text-sm text-red-900 bg-red-50 rounded p-3 border border-red-200">
            {workflow.error_message}
          </div>
        </div>
      )}

      {/* Toggle Details Button */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
      >
        {showDetails ? '▼ Hide Details' : '▶ Show Details'}
      </button>

      {/* Detailed Information */}
      {showDetails && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-6">
          {/* Cost Economics Section */}
          {(() => {
            const phaseCosts = transformToPhaseCosts(workflow.cost_breakdown);
            const budgetDelta = calculateBudgetDelta(
              workflow.estimated_cost_total,
              workflow.actual_cost_total
            );
            const hasCostData = workflow.actual_cost_total > 0;

            return (
              <div className="border-b border-gray-200 pb-6">
                <h3 className="text-base font-semibold text-gray-800 mb-4">
                  💰 Cost Economics
                </h3>

                {/* Charts Section */}
                {phaseCosts ? (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                    <div className="border border-gray-200 rounded-lg p-4 bg-white">
                      <CostBreakdownChart phases={phaseCosts} />
                    </div>
                    <div className="border border-gray-200 rounded-lg p-4 bg-white">
                      <CumulativeCostChart phases={phaseCosts} />
                    </div>
                  </div>
                ) : (
                  hasCostData && (
                    <div className="text-sm text-gray-500 mb-6 p-4 bg-gray-50 border border-gray-200 rounded">
                      Cost breakdown by phase is not available for this workflow (may be from an
                      older execution)
                    </div>
                  )
                )}

                {/* Budget Comparison Section */}
                {hasCostData && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 mb-3">Budget Comparison</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <div className="text-gray-600 mb-1">Estimated Total</div>
                        <div className="text-lg font-semibold text-blue-700">
                          {formatCost(workflow.estimated_cost_total)}
                        </div>
                      </div>
                      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                        <div className="text-gray-600 mb-1">Actual Total</div>
                        <div className="text-lg font-semibold text-green-700">
                          {formatCost(workflow.actual_cost_total)}
                        </div>
                      </div>
                      <div
                        className={`rounded-lg p-3 border ${
                          budgetDelta.status === 'under'
                            ? 'bg-green-50 border-green-200'
                            : budgetDelta.status === 'over'
                            ? 'bg-red-50 border-red-200'
                            : 'bg-gray-50 border-gray-200'
                        }`}
                      >
                        <div className="text-gray-600 mb-1">Budget Delta</div>
                        <div
                          className={`text-lg font-semibold ${
                            budgetDelta.status === 'under'
                              ? 'text-green-700'
                              : budgetDelta.status === 'over'
                              ? 'text-red-700'
                              : 'text-gray-700'
                          }`}
                        >
                          {budgetDelta.delta >= 0 ? '+' : ''}
                          {formatCost(Math.abs(budgetDelta.delta))}
                        </div>
                        <div
                          className={`text-xs ${
                            budgetDelta.status === 'under'
                              ? 'text-green-600'
                              : budgetDelta.status === 'over'
                              ? 'text-red-600'
                              : 'text-gray-600'
                          }`}
                        >
                          {budgetDelta.percentage >= 0 ? '+' : ''}
                          {budgetDelta.percentage.toFixed(1)}%
                        </div>
                      </div>
                    </div>

                    {/* Per-step comparison */}
                    <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                      <div className="bg-gray-50 rounded p-3">
                        <div className="text-gray-600">Estimated per Step</div>
                        <div className="font-medium">{formatCost(workflow.estimated_cost_per_step)}</div>
                      </div>
                      <div className="bg-gray-50 rounded p-3">
                        <div className="text-gray-600">Actual per Step</div>
                        <div className="font-medium">{formatCost(workflow.actual_cost_per_step)}</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })()}

          {/* Token Analysis Section */}
          {workflow.total_tokens > 0 && (
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-base font-semibold text-gray-800 mb-4">
                🔢 Token Analysis
              </h3>

              {/* Token Breakdown Chart and Cache Efficiency */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-4">
                <div className="border border-gray-200 rounded-lg p-4 bg-white">
                  <TokenBreakdownChart
                    inputTokens={workflow.input_tokens}
                    outputTokens={workflow.output_tokens}
                    cachedTokens={workflow.cached_tokens}
                    cacheHitTokens={workflow.cache_hit_tokens}
                    cacheMissTokens={workflow.cache_miss_tokens}
                    totalTokens={workflow.total_tokens}
                  />
                </div>

                <div className="flex flex-col gap-4">
                  {/* Cache Efficiency Badge */}
                  {workflow.cache_efficiency_percent > 0 && (
                    <div>
                      <CacheEfficiencyBadge
                        cacheEfficiencyPercent={workflow.cache_efficiency_percent}
                        cacheSavingsAmount={calculateCacheSavings(workflow)}
                      />
                    </div>
                  )}

                  {/* Cache Hit/Miss Ratio Visualization */}
                  {(workflow.cache_hit_tokens > 0 || workflow.cache_miss_tokens > 0) && (
                    <div className="border border-gray-200 rounded-lg p-4 bg-white">
                      <h4 className="text-sm font-semibold text-gray-700 mb-3">
                        Cache Hit/Miss Ratio
                      </h4>
                      <div className="space-y-2">
                        {(() => {
                          const total = workflow.cache_hit_tokens + workflow.cache_miss_tokens;
                          const hitPercentage = (workflow.cache_hit_tokens / total) * 100;
                          return (
                            <>
                              <div className="relative w-full h-8 bg-orange-200 rounded-lg overflow-hidden">
                                <div
                                  className="absolute h-full bg-green-500 transition-all"
                                  style={{ width: `${hitPercentage}%` }}
                                />
                                <div className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-gray-900">
                                  {hitPercentage.toFixed(1)}% Cache Hits
                                </div>
                              </div>
                              <div className="flex justify-between text-xs text-gray-600">
                                <span>
                                  Hits: {workflow.cache_hit_tokens.toLocaleString()}
                                </span>
                                <span>
                                  Misses: {workflow.cache_miss_tokens.toLocaleString()}
                                </span>
                              </div>
                            </>
                          );
                        })()}
                      </div>
                    </div>
                  )}

                  {/* Detailed Token Breakdown Table */}
                  <div className="border border-gray-200 rounded-lg p-4 bg-white">
                    <h4 className="text-sm font-semibold text-gray-700 mb-3">Token Details</h4>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div className="bg-gray-50 rounded p-2">
                        <div className="text-gray-600">Input</div>
                        <div className="font-medium">{formatNumber(workflow.input_tokens)}</div>
                      </div>
                      <div className="bg-gray-50 rounded p-2">
                        <div className="text-gray-600">Output</div>
                        <div className="font-medium">{formatNumber(workflow.output_tokens)}</div>
                      </div>
                      <div className="bg-gray-50 rounded p-2">
                        <div className="text-gray-600">Cached</div>
                        <div className="font-medium">{formatNumber(workflow.cached_tokens)}</div>
                      </div>
                      <div className="bg-gray-50 rounded p-2">
                        <div className="text-gray-600">Total</div>
                        <div className="font-medium">{formatNumber(workflow.total_tokens)}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Performance Analysis Section */}
          {workflow.phase_durations && (
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-base font-semibold text-gray-800 mb-4">
                ⚡ Performance Analysis
              </h3>

              {/* Phase Duration Bar Chart */}
              <div className="mb-4">
                <PhaseDurationChart phaseDurations={workflow.phase_durations} />
              </div>

              {/* Bottleneck Alert */}
              {workflow.bottleneck_phase && (
                <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <div className="text-sm font-medium text-yellow-800">
                    ⚠️ Bottleneck Detected: {workflow.bottleneck_phase} phase
                  </div>
                  <div className="text-xs text-yellow-700 mt-1">
                    This phase took significantly longer than others (&gt;30% of total time)
                  </div>
                </div>
              )}

              {/* Idle Time */}
              {(workflow.idle_time_seconds !== undefined && workflow.idle_time_seconds > 0) && (
                <div className="mt-2 text-sm text-gray-600">
                  Idle time between phases: {formatDuration(workflow.idle_time_seconds)}
                </div>
              )}
            </div>
          )}

          {/* Error Analysis Section */}
          {(workflow.retry_count > 0 || workflow.status === 'failed') && (
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-base font-semibold text-gray-800 mb-4">
                ⚠️ Error Analysis
              </h3>

              {/* Error Category Badge */}
              {workflow.error_category && (
                <div className="mb-3">
                  <span className="inline-block bg-red-100 text-red-800 text-sm px-3 py-1 rounded border border-red-200">
                    {workflow.error_category.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
              )}

              {/* Error Message */}
              {workflow.error_message && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                  <div className="text-sm font-medium text-red-800 mb-2">Error Message:</div>
                  <p className="text-sm text-red-900">{workflow.error_message}</p>
                </div>
              )}

              {/* Retry Reasons */}
              {(workflow.retry_reasons && workflow.retry_reasons.length > 0) && (
                <div className="mb-4">
                  <div className="text-sm font-medium text-gray-700 mb-2">Retry Triggers:</div>
                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1 bg-gray-50 border border-gray-200 rounded-lg p-3">
                    {workflow.retry_reasons.map((reason, idx) => (
                      <li key={idx}>{reason.replace('_', ' ')}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Error Phase Distribution */}
              {(workflow.error_phase_distribution && Object.keys(workflow.error_phase_distribution).length > 0) && (
                <div className="mb-4">
                  <div className="text-sm font-medium text-gray-700 mb-2">Errors by Phase:</div>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {Object.entries(workflow.error_phase_distribution).map(([phase, count]) => (
                      <div key={phase} className="bg-red-50 border border-red-200 rounded p-2 text-sm">
                        <div className="text-gray-600 capitalize">{phase}</div>
                        <div className="font-semibold text-red-700">{count} {count === 1 ? 'error' : 'errors'}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recovery Time */}
              {(workflow.recovery_time_seconds !== undefined && workflow.recovery_time_seconds > 0) && (
                <div className="text-sm text-gray-600 mb-4">
                  Total recovery time: {formatDuration(workflow.recovery_time_seconds)}
                </div>
              )}

              {workflow.retry_count > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                    <div className="text-gray-700 mb-2">Retries Required</div>
                    <div className="text-2xl font-bold text-orange-600">
                      {workflow.retry_count}
                    </div>
                    <p className="text-xs text-gray-600 mt-2">
                      This workflow required {workflow.retry_count} {workflow.retry_count === 1 ? 'retry' : 'retries'}
                    </p>
                  </div>

                  {(() => {
                    const retryCost = calculateRetryCost(workflow);
                    return retryCost !== null ? (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <div className="text-gray-700 mb-2">Estimated Retry Cost Impact</div>
                        <div className="text-2xl font-bold text-red-600">
                          {formatCost(retryCost)}
                        </div>
                        <p className="text-xs text-gray-600 mt-2">
                          Additional cost due to retries (over budget)
                        </p>
                      </div>
                    ) : (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="text-gray-700 mb-2">Budget Status</div>
                        <div className="text-sm font-medium text-green-700">
                          Retries occurred but total cost remained under estimate
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}
            </div>
          )}

          {/* Resource Usage Section */}
          <div className="border-b border-gray-200 pb-6">
            <h3 className="text-base font-semibold text-gray-800 mb-4">
              💾 Resource Usage
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
              {workflow.backend_port && (
                <div className="bg-gray-50 rounded p-3">
                  <div className="text-gray-600">Backend Port</div>
                  <div className="font-medium">{workflow.backend_port}</div>
                </div>
              )}
              {workflow.frontend_port && (
                <div className="bg-gray-50 rounded p-3">
                  <div className="text-gray-600">Frontend Port</div>
                  <div className="font-medium">{workflow.frontend_port}</div>
                </div>
              )}
              <div className="bg-gray-50 rounded p-3">
                <div className="text-gray-600">Concurrent Workflows</div>
                <div className="font-medium">{workflow.concurrent_workflows}</div>
              </div>
              <div className="bg-gray-50 rounded p-3">
                <div className="text-gray-600">Worktree Reused</div>
                <div className="font-medium">{workflow.worktree_reused ? 'Yes' : 'No'}</div>
              </div>
            </div>
          </div>

          {/* Workflow Journey Section */}
          {(workflow.nl_input || workflow.structured_input) && (
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-base font-semibold text-gray-800 mb-4">
                🗺️ Workflow Journey
              </h3>
              <div className="space-y-4">
                {/* Original Request */}
                {workflow.nl_input && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-700 mb-2">Original Request</h4>
                    <p className="text-sm text-gray-900">{workflow.nl_input}</p>
                  </div>
                )}

                {/* Classification & Reasoning */}
                {workflow.structured_input && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-700 mb-2">Classification</h4>
                    <dl className="text-sm space-y-2">
                      <div>
                        <dt className="text-gray-600">Type:</dt>
                        <dd className="font-medium">
                          {workflow.structured_input.classification || 'Not specified'}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-gray-600">Reasoning:</dt>
                        <dd>
                          {workflow.structured_input.classification_reasoning || 'Not recorded'}
                        </dd>
                      </div>
                    </dl>
                  </div>
                )}

                {/* Model Selection Reasoning */}
                {workflow.structured_input && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-700 mb-2">Model Selection</h4>
                    <dl className="text-sm space-y-2">
                      <div>
                        <dt className="text-gray-600">Selected:</dt>
                        <dd className="font-medium">{workflow.model_used || 'Not specified'}</dd>
                      </div>
                      <div>
                        <dt className="text-gray-600">Reason:</dt>
                        <dd>
                          {workflow.structured_input.model_selection_reasoning || 'Not recorded'}
                        </dd>
                      </div>
                    </dl>
                  </div>
                )}

                {/* Structured Input */}
                {workflow.structured_input && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-700 mb-2">Structured Input</h4>
                    <dl className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm mb-3">
                      {formatStructuredInputForDisplay(workflow.structured_input).map(
                        ({ key, value }) => (
                          <div key={key}>
                            <dt className="text-gray-600 font-medium">{key}:</dt>
                            <dd className="text-gray-900">
                              {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                            </dd>
                          </div>
                        )
                      )}
                    </dl>
                    <details className="mt-3">
                      <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800">
                        View Raw JSON
                      </summary>
                      <pre className="text-xs bg-white rounded p-2 mt-2 overflow-x-auto border border-gray-300">
                        {JSON.stringify(workflow.structured_input, null, 2)}
                      </pre>
                    </details>
                  </div>
                )}
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  );
}
