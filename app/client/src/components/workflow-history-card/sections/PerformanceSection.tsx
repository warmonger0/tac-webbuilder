import type { WorkflowHistoryItem } from '../../../types';
import { PhaseDurationChart } from '../../PhaseDurationChart';
import { formatDuration } from '../helpers';

interface PerformanceSectionProps {
  workflow: WorkflowHistoryItem;
}

export function PerformanceSection({ workflow }: PerformanceSectionProps) {
  if (!workflow.phase_durations) return null;

  return (
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
  );
}
