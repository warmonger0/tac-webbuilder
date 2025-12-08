/**
 * PhaseQueueCard Component
 *
 * Displays an individual phase in the queue with status indicator,
 * title, parent issue link, and execution order.
 */

import { useState } from 'react';
import toast from 'react-hot-toast';
import { executePhase } from '../api/client';
import { WorkflowStateDisplay } from './WorkflowStateDisplay';
import { apiConfig } from '../config/api';
import { phaseQueueStatusColors, uiIcons } from '../config/theme';

export interface PhaseQueueItem {
  queue_id: string;
  parent_issue: number;
  phase_number: number;
  issue_number?: number;
  status: 'queued' | 'ready' | 'running' | 'completed' | 'blocked' | 'failed';
  depends_on_phase?: number;
  phase_data: {
    title: string;
    content: string;
    externalDocs?: string[];
    predicted_patterns?: string[];  // Predicted operation patterns
  };
  created_at: string;
  updated_at: string;
  error_message?: string;
  adw_id?: string;
  pr_number?: number;
}

interface PhaseQueueCardProps {
  queueItem: PhaseQueueItem;
}

// Import status colors from centralized theme configuration
const STATUS_COLORS = phaseQueueStatusColors;

export function PhaseQueueCard({ queueItem }: PhaseQueueCardProps) {
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { phase_number, phase_data, status, issue_number, queue_id, adw_id, pr_number } = queueItem;
  const statusStyle = STATUS_COLORS[status];
  const [isExecuting, setIsExecuting] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleClick = () => {
    if (issue_number) {
      window.open(apiConfig.github.getIssueUrl(issue_number), '_blank');
    }
  };

  const handlePRClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (pr_number) {
      window.open(apiConfig.github.getPullRequestUrl(pr_number), '_blank');
    }
  };

  const handleExecute = async (e: React.MouseEvent) => {
    // Stop propagation to prevent card click
    e.stopPropagation();

    setIsExecuting(true);

    try {
      const result = await executePhase(queue_id);
      console.log('Phase execution started:', result);
      toast.success(`${result.message}\n\nADW ID: ${result.adw_id}\nIssue: #${result.issue_number}`, { duration: 5000 });
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to execute phase';
      console.error('Failed to execute phase:', error);
      toast.error(`Failed to execute phase:\n\n${errorMsg}`, { duration: 6000 });
    } finally {
      setIsExecuting(false);
    }
  };

  const toggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  return (
    <div
      className={`${statusStyle.bg} ${statusStyle.border} border-2 rounded-lg p-3 transition-all hover:shadow-md`}
      role="article"
    >
      <div className="flex flex-col gap-2">
        {/* Top Row: Phase Number, Title, Status, and Expand Button */}
        <div className="flex items-center justify-between gap-2">
          {/* Left: Phase Number and Title */}
          <div className="flex items-center gap-3 flex-1 min-w-0">
            {/* Phase Number Badge */}
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-sm">
              {phase_number}
            </div>

            {/* Title with Issue Number - Clickable to expand/collapse */}
            <h4
              className={`font-semibold ${statusStyle.text} text-sm truncate cursor-pointer hover:underline`}
              onClick={toggleExpand}
            >
              {phase_data.title || `Phase ${phase_number}`} {statusStyle.icon}{' '}
              {issue_number && `#${issue_number}`}
            </h4>
          </div>

          {/* Right: Expand/Collapse, Execute Button, or Status Badge */}
          <div className="flex items-center gap-2">
            {/* Expand/Collapse Button */}
            <button
              onClick={toggleExpand}
              className="text-gray-600 hover:text-gray-900 transition-colors"
              title={isExpanded ? "Collapse details" : "Expand details"}
            >
              {isExpanded ? uiIcons.collapse : uiIcons.expand}
            </button>

            {status === 'ready' ? (
            <button
              onClick={handleExecute}
              disabled={isExecuting}
              className="flex-shrink-0 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-400 text-white text-xs font-medium px-3 py-1 rounded-full transition-colors flex items-center gap-1"
              title="Start phase execution"
            >
              {isExecuting ? (
                <>
                  <span className="animate-spin">⚙️</span>
                  <span>Starting...</span>
                </>
              ) : (
                <>
                  <span>▶️</span>
                  <span>Processing</span>
                </>
              )}
            </button>
          ) : (
              <span className={`${statusStyle.badge} text-white text-xs font-medium px-2 py-1 rounded-full flex items-center gap-1 flex-shrink-0`}>
                <span>{statusStyle.icon}</span>
                <span>{statusStyle.label}</span>
              </span>
            )}
          </div>
        </div>

        {/* Expandable Section */}
        {isExpanded && (
          <>
            {/* Issue and PR Badges Row */}
            {(issue_number || pr_number) && (
              <div className="flex items-center gap-2 ml-11">
            {issue_number && (
              <button
                onClick={handleClick}
                className="inline-flex items-center gap-1 px-2 py-1 bg-green-600 hover:bg-green-700 text-white text-xs font-medium rounded transition-colors"
                title={`View Issue #${issue_number}`}
              >
                <span>{uiIcons.issue}</span>
                <span>Open</span>
              </button>
            )}
            {pr_number && (
              <button
                onClick={handlePRClick}
                className="inline-flex items-center gap-1 px-2 py-1 bg-purple-600 hover:bg-purple-700 text-white text-xs font-medium rounded transition-colors"
                title={`View PR #${pr_number}`}
              >
                <span>{uiIcons.pullRequest}</span>
                <span>#{pr_number}</span>
              </button>
            )}
              </div>
            )}

            {/* Pattern Predictions */}
            {phase_data.predicted_patterns && phase_data.predicted_patterns.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1 ml-11">
                <span className="text-xs text-slate-400">Patterns:</span>
                {phase_data.predicted_patterns.map((pattern, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 text-xs rounded-md border border-emerald-500/30"
                    title="Predicted pattern"
                  >
                    {pattern}
                  </span>
                ))}
              </div>
            )}

            {/* Show workflow state for any phase with an ADW ID (real-time display) */}
            {adw_id && (
              <WorkflowStateDisplay adwId={adw_id} />
            )}
          </>
        )}
      </div>
    </div>
  );
}

/**
 * PhaseQueueList Component
 *
 * Displays a scrollable list of phase queue items
 */
interface PhaseQueueListProps {
  phases: PhaseQueueItem[];
}

export function PhaseQueueList({ phases }: PhaseQueueListProps) {
  return (
    <div className="flex flex-col justify-end space-y-3 overflow-y-auto h-full pr-2">
      {phases.map((phase) => (
        <PhaseQueueCard key={phase.queue_id} queueItem={phase} />
      ))}
    </div>
  );
}
