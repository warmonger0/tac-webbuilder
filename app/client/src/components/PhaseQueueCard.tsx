/**
 * PhaseQueueCard Component
 *
 * Displays an individual phase in the queue with status indicator,
 * title, parent issue link, and execution order.
 */

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
  const { phase_number, phase_data, status, parent_issue, issue_number, depends_on_phase, error_message } = queueItem;
  const statusStyle = STATUS_COLORS[status];

  const handleClick = () => {
    if (issue_number) {
      window.open(`https://github.com/warmonger0/tac-webbuilder/issues/${issue_number}`, '_blank');
    }
  };

  return (
    <div
      className={`${statusStyle.bg} ${statusStyle.border} border-2 rounded-lg p-4 transition-all hover:shadow-md ${
        issue_number ? 'cursor-pointer' : ''
      }`}
      onClick={handleClick}
      role={issue_number ? 'button' : 'article'}
      tabIndex={issue_number ? 0 : undefined}
      onKeyDown={(e) => {
        if (issue_number && (e.key === 'Enter' || e.key === ' ')) {
          handleClick();
        }
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {/* Phase Number Badge */}
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-lg">
            {phase_number}
          </div>

          {/* Title */}
          <div>
            <h4 className={`font-semibold ${statusStyle.text} text-lg`}>
              {phase_data.title || `Phase ${phase_number}`}
            </h4>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-gray-600">
                Parent: #{parent_issue}
              </span>
              {issue_number && (
                <>
                  <span className="text-gray-400">•</span>
                  <span className="text-xs text-gray-600">
                    Issue: #{issue_number}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Status Badge */}
        <div className="flex flex-col items-end gap-1">
          <span className={`${statusStyle.badge} text-white text-xs font-medium px-3 py-1 rounded-full flex items-center gap-1`}>
            <span>{statusStyle.icon}</span>
            <span>{statusStyle.label}</span>
          </span>
          {depends_on_phase && status === 'queued' && (
            <span className="text-xs text-gray-500">
              After Phase {depends_on_phase}
            </span>
          )}
        </div>
      </div>

      {/* Content Preview */}
      <div className="mb-3">
        <p className="text-sm text-gray-700 line-clamp-2">
          {phase_data.content.substring(0, 150)}
          {phase_data.content.length > 150 && '...'}
        </p>
      </div>

      {/* External Docs */}
      {phase_data.externalDocs && phase_data.externalDocs.length > 0 && (
        <div className="mb-3 pt-3 border-t border-gray-200">
          <div className="flex items-start gap-2">
            <span className="text-sm">📎</span>
            <div className="flex-1">
              <div className="text-xs font-medium text-gray-600 mb-1">
                Referenced Documents:
              </div>
              <div className="flex flex-wrap gap-1">
                {phase_data.externalDocs.map((doc, idx) => (
                  <code key={idx} className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded border border-blue-200">
                    {doc}
                  </code>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error_message && (status === 'blocked' || status === 'failed') && (
        <div className="mt-3 pt-3 border-t border-red-200 bg-red-50 rounded p-2">
          <div className="flex items-start gap-2">
            <span className="text-red-600 text-sm">⚠️</span>
            <div className="flex-1">
              <div className="text-xs font-medium text-red-700 mb-1">
                {status === 'blocked' ? 'Blocked by dependency failure' : 'Execution failed'}
              </div>
              <p className="text-xs text-red-600">{error_message}</p>
            </div>
          </div>
        </div>
      )}

      {/* Execution Order Indicator */}
      {status === 'ready' && (
        <div className="mt-3 pt-3 border-t border-blue-200">
          <div className="flex items-center gap-2 text-blue-700">
            <span className="text-sm">🎯</span>
            <span className="text-sm font-medium">
              {phase_number === 1 ? 'Ready to execute first' : `Ready to execute (after Phase ${depends_on_phase})`}
            </span>
          </div>
        </div>
      )}

      {/* Running Indicator */}
      {status === 'running' && (
        <div className="mt-3 pt-3 border-t border-yellow-200">
          <div className="flex items-center gap-2 text-yellow-700">
            <span className="text-sm animate-spin">⚙️</span>
            <span className="text-sm font-medium">Executing now...</span>
          </div>
        </div>
      )}
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
    <div className="space-y-3 overflow-y-auto h-full pr-2">
      {phases.map((phase) => (
        <PhaseQueueCard key={phase.queue_id} queueItem={phase} />
      ))}
    </div>
  );
}
