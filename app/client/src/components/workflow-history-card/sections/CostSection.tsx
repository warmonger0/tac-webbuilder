import type { WorkflowHistoryItem } from '../../../types';
import { CostBreakdownChart } from '../../CostBreakdownChart';
import { CumulativeCostChart } from '../../CumulativeCostChart';
import { transformToPhaseCosts, calculateBudgetDelta, formatCost } from '../helpers';

interface CostSectionProps {
  workflow: WorkflowHistoryItem;
}

export function CostSection({ workflow }: CostSectionProps) {
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
}
