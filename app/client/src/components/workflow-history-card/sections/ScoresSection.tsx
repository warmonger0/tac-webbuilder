import type { WorkflowHistoryItem } from '../../../types';
import { ScoreCard } from '../../ScoreCard';

interface ScoresSectionProps {
  workflow: WorkflowHistoryItem;
}

export function ScoresSection({ workflow }: ScoresSectionProps) {
  if (
    workflow.cost_efficiency_score === undefined &&
    workflow.performance_score === undefined &&
    workflow.quality_score === undefined
  ) {
    return null;
  }

  return (
    <div className="border-b border-gray-200 pb-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">
        📊 Efficiency Scores
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Cost Efficiency */}
        {workflow.cost_efficiency_score !== undefined && (
          <ScoreCard
            title="Cost Efficiency"
            score={workflow.cost_efficiency_score}
            description="Budget adherence, cache usage, retry rate"
          />
        )}

        {/* Performance */}
        {workflow.performance_score !== undefined && (
          <ScoreCard
            title="Performance"
            score={workflow.performance_score}
            description="Duration vs similar workflows"
          />
        )}

        {/* Quality */}
        {workflow.quality_score !== undefined && (
          <ScoreCard
            title="Quality"
            score={workflow.quality_score}
            description="Error rate, review cycles, tests"
          />
        )}
      </div>
    </div>
  );
}
