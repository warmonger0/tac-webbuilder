/**
 * PhaseQueueList Component
 *
 * Displays a list of phases in execution order (stacked cards)
 */

import { PhaseQueueCard, type PhaseQueueItem } from './PhaseQueueCard';

interface PhaseQueueListProps {
  phases: PhaseQueueItem[];
}

export function PhaseQueueList({ phases }: PhaseQueueListProps) {
  if (phases.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <span className="text-4xl mb-2 block">📭</span>
          <p className="text-gray-500 text-lg">No phases in queue</p>
        </div>
      </div>
    );
  }

  // Sort by phase number (ascending)
  const sortedPhases = [...phases].sort((a, b) => a.phase_number - b.phase_number);

  return (
    <div className="space-y-3 overflow-y-auto max-h-[600px]">
      {sortedPhases.map((phase) => (
        <PhaseQueueCard key={phase.queue_id} queueItem={phase} />
      ))}
    </div>
  );
}
