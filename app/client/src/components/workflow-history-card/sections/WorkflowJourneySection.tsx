import type { WorkflowHistoryItem } from '../../../types';
import { formatStructuredInputForDisplay } from '../helpers';

interface WorkflowJourneySectionProps {
  workflow: WorkflowHistoryItem;
}

export function WorkflowJourneySection({ workflow }: WorkflowJourneySectionProps) {
  if (!workflow.nl_input && !workflow.structured_input) return null;

  return (
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
  );
}
