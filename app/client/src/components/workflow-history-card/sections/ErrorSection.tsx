import type { WorkflowHistoryItem } from '../../../types';
import { calculateRetryCost, formatCost, formatDuration } from '../helpers';

interface ErrorSectionProps {
  workflow: WorkflowHistoryItem;
}

export function ErrorSection({ workflow }: ErrorSectionProps) {
  if (workflow.retry_count === 0 && workflow.status !== 'failed') return null;

  return (
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
  );
}
