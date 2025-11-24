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
  const { phase_number, phase_data, status, issue_number } = queueItem;
  const statusStyle = STATUS_COLORS[status];

  const handleClick = () => {
    if (issue_number) {
      window.open(`https://github.com/warmonger0/tac-webbuilder/issues/${issue_number}`, '_blank');
    }
  };

  return (
    <div
      className={`${statusStyle.bg} ${statusStyle.border} border-2 rounded-lg p-3 transition-all hover:shadow-md ${
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
      <div className="flex items-center justify-between">
        {/* Left: Phase Number and Title */}
        <div className="flex items-center gap-3 flex-1 min-w-0">
          {/* Phase Number Badge */}
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-sm">
            {phase_number}
          </div>

          {/* Title */}
          <h4 className={`font-semibold ${statusStyle.text} text-sm truncate`}>
            {phase_data.title || `Phase ${phase_number}`}
            {issue_number && (
              <span className="ml-2 text-xs font-normal opacity-75">
                #{issue_number}
              </span>
            )}
          </h4>
        </div>

        {/* Right: Status Badge */}
        <span className={`${statusStyle.badge} text-white text-xs font-medium px-2 py-1 rounded-full flex items-center gap-1 flex-shrink-0 ml-2`}>
          <span>{statusStyle.icon}</span>
          <span>{statusStyle.label}</span>
        </span>
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
    <div className="flex flex-col justify-end space-y-3 overflow-y-auto h-full pr-2 pb-0">
      {phases.map((phase) => (
        <PhaseQueueCard key={phase.queue_id} queueItem={phase} />
      ))}
    </div>
  );
}
