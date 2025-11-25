/**
 * PhaseQueueCard Component
 *
 * Displays an individual phase in the queue with status indicator,
 * title, parent issue link, and execution order.
 */

import { useState } from 'react';
import { executePhase } from '../api/client';
import { WorkflowStateDisplay } from './WorkflowStateDisplay';
import { config } from '../config';

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

const STATUS_COLORS = {
  queued: {
    bg: 'bg-gray-100',
    border: 'border-gray-300',
    text: 'text-gray-700',
    badge: 'bg-gray-500',
    icon: '⏸️',
    label: 'Queued'
  },
  ready: {
    bg: 'bg-blue-50',
    border: 'border-blue-300',
    text: 'text-blue-900',
    badge: 'bg-blue-500',
    icon: '▶️',
    label: 'Ready'
  },
  running: {
    bg: 'bg-yellow-50',
    border: 'border-yellow-300',
    text: 'text-yellow-900',
    badge: 'bg-yellow-500',
    icon: '⚙️',
    label: 'Running'
  },
  completed: {
    bg: 'bg-green-50',
    border: 'border-green-300',
    text: 'text-green-900',
    badge: 'bg-green-500',
    icon: '✅',
    label: 'Completed'
  },
  blocked: {
    bg: 'bg-orange-50',
    border: 'border-orange-300',
    text: 'text-orange-900',
    badge: 'bg-orange-500',
    icon: '🚫',
    label: 'Blocked'
  },
  failed: {
    bg: 'bg-red-50',
    border: 'border-red-300',
    text: 'text-red-900',
    badge: 'bg-red-500',
    icon: '❌',
    label: 'Failed'
  }
};

export function PhaseQueueCard({ queueItem }: PhaseQueueCardProps) {
  const { phase_number, phase_data, status, issue_number, queue_id, adw_id, pr_number } = queueItem;
  const statusStyle = STATUS_COLORS[status];
  const [isExecuting, setIsExecuting] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleClick = () => {
    if (issue_number) {
      window.open(config.github.getIssueUrl(issue_number), '_blank');
    }
  };

  const handlePRClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (pr_number) {
      window.open(config.github.getPullRequestUrl(pr_number), '_blank');
    }
  };

  const handleExecute = async (e: React.MouseEvent) => {
    // Stop propagation to prevent card click
    e.stopPropagation();

    setIsExecuting(true);

    try {
      const result = await executePhase(queue_id);
      console.log('Phase execution started:', result);
      // Optionally show success toast/notification
      alert(`✅ ${result.message}\n\nADW ID: ${result.adw_id}\nIssue: #${result.issue_number}`);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to execute phase';
      console.error('Failed to execute phase:', error);
      alert(`❌ Failed to execute phase:\n\n${errorMsg}`);
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
              {isExpanded ? '▼' : '▶'}
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
                <span>⭕</span>
                <span>Open</span>
              </button>
            )}
            {pr_number && (
              <button
                onClick={handlePRClick}
                className="inline-flex items-center gap-1 px-2 py-1 bg-purple-600 hover:bg-purple-700 text-white text-xs font-medium rounded transition-colors"
                title={`View PR #${pr_number}`}
              >
                <span>🔀</span>
                <span>#{pr_number}</span>
              </button>
            )}
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
