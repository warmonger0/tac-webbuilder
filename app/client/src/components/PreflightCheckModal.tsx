/**
 * Preflight Check Modal Component
 *
 * Displays pre-flight check results before starting ADW automation.
 * Shows blocking failures, warnings, and check details.
 */

import type {
  PreflightChecksResponse,
  PreflightCheckResult,
  PreflightBlockingFailure,
  PreflightWarning,
} from '../api/systemClient';

interface PreflightCheckModalProps {
  results: PreflightChecksResponse;
  featureTitle: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function PreflightCheckModal({
  results,
  featureTitle,
  onConfirm,
  onCancel,
}: PreflightCheckModalProps) {
  const hasBlockingFailures = results.blocking_failures.length > 0;
  const hasWarnings = results.warnings.length > 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 space-y-6">
          {/* Header */}
          <div>
            <h3 className="text-2xl font-bold text-gray-900">
              Pre-flight Checks
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Feature: {featureTitle}
            </p>
          </div>

          {/* Overall Status */}
          <div
            className={`p-4 rounded-lg ${
              results.passed
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}
          >
            <div className="flex items-center gap-2">
              <span className="text-2xl">
                {results.passed ? '✅' : '❌'}
              </span>
              <div className="flex-1">
                <p
                  className={`font-semibold ${
                    results.passed ? 'text-green-800' : 'text-red-800'
                  }`}
                >
                  {results.passed
                    ? 'All critical checks passed'
                    : 'Critical checks failed'}
                </p>
                <p className="text-sm text-gray-600">
                  Completed in {results.total_duration_ms}ms
                </p>
              </div>
            </div>
          </div>

          {/* Blocking Failures */}
          {hasBlockingFailures && (
            <div className="space-y-3">
              <h4 className="font-semibold text-red-800 flex items-center gap-2">
                <span className="text-xl">❌</span>
                Blocking Issues ({results.blocking_failures.length})
              </h4>
              <div className="space-y-3">
                {results.blocking_failures.map((failure, idx) => (
                  <BlockingFailureCard key={idx} failure={failure} />
                ))}
              </div>
            </div>
          )}

          {/* Warnings */}
          {hasWarnings && (
            <div className="space-y-3">
              <h4 className="font-semibold text-yellow-800 flex items-center gap-2">
                <span className="text-xl">⚠️</span>
                Warnings ({results.warnings.length})
              </h4>
              <div className="space-y-3">
                {results.warnings.map((warning, idx) => (
                  <WarningCard key={idx} warning={warning} />
                ))}
              </div>
            </div>
          )}

          {/* Check Details */}
          <details className="border border-gray-200 rounded-lg">
            <summary className="p-3 cursor-pointer hover:bg-gray-50 font-medium">
              View All Checks ({results.checks_run.length})
            </summary>
            <div className="p-3 space-y-2 border-t border-gray-200">
              {results.checks_run.map((check, idx) => (
                <CheckResultRow key={idx} check={check} />
              ))}
            </div>
          </details>

          {/* Issue Validation Warning (if present) */}
          {results.issue_validation && results.issue_validation.is_resolved && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-start gap-2">
                <span className="text-xl">⚠️</span>
                <div className="flex-1">
                  <p className="font-semibold text-yellow-800">
                    Issue May Already Be Resolved
                  </p>
                  <p className="text-sm text-gray-700 mt-1">
                    {results.issue_validation.message}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    Confidence: {Math.round(results.issue_validation.confidence * 100)}%
                  </p>
                  {results.issue_validation.recommendation && (
                    <p className="text-sm text-gray-700 mt-2 font-medium">
                      💡 {results.issue_validation.recommendation}
                    </p>
                  )}
                  {results.issue_validation.evidence.length > 0 && (
                    <details className="mt-2">
                      <summary className="text-sm text-blue-600 cursor-pointer hover:underline">
                        View Evidence
                      </summary>
                      <ul className="list-disc pl-5 mt-1 text-sm text-gray-600 space-y-1">
                        {results.issue_validation.evidence.map((evidence, idx) => (
                          <li key={idx}>{evidence}</li>
                        ))}
                      </ul>
                    </details>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-4">
            {results.passed ? (
              <>
                <button
                  onClick={onConfirm}
                  className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 transition-colors"
                >
                  {hasWarnings ? '⚠️ Proceed Anyway' : '🚀 Start Automation'}
                </button>
                <button
                  onClick={onCancel}
                  className="flex-1 bg-gray-200 text-gray-800 py-3 px-6 rounded-lg font-medium hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
              </>
            ) : (
              <button
                onClick={onCancel}
                className="flex-1 bg-gray-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-gray-700 transition-colors"
              >
                Close (Fix Issues First)
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Sub-Components
// ============================================================================

function BlockingFailureCard({ failure }: { failure: PreflightBlockingFailure }) {
  return (
    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
      <p className="font-semibold text-red-900">{failure.check}</p>
      <p className="text-sm text-red-800 mt-1">{failure.error}</p>
      <div className="mt-2 p-2 bg-red-100 rounded text-sm text-red-900">
        <p className="font-medium">Fix:</p>
        <p className="mt-1">{failure.fix}</p>
      </div>
      {failure.failing_tests && failure.failing_tests.length > 0 && (
        <details className="mt-2">
          <summary className="text-sm text-red-700 cursor-pointer hover:underline">
            View Failing Tests ({failure.failing_tests.length})
          </summary>
          <ul className="list-disc pl-5 mt-1 text-sm text-red-800 space-y-1">
            {failure.failing_tests.slice(0, 10).map((test, idx) => (
              <li key={idx} className="font-mono text-xs">
                {test}
              </li>
            ))}
            {failure.failing_tests.length > 10 && (
              <li className="text-red-600">
                ...and {failure.failing_tests.length - 10} more
              </li>
            )}
          </ul>
        </details>
      )}
    </div>
  );
}

function WarningCard({ warning }: { warning: PreflightWarning }) {
  return (
    <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
      <p className="font-semibold text-yellow-900">{warning.check}</p>
      <p className="text-sm text-yellow-800 mt-1">{warning.message}</p>
      <p className="text-sm text-gray-700 mt-1">
        <span className="font-medium">Impact:</span> {warning.impact}
      </p>
      {warning.recommendation && (
        <p className="text-sm text-gray-700 mt-1">
          <span className="font-medium">💡 Recommendation:</span> {warning.recommendation}
        </p>
      )}
      {warning.evidence && warning.evidence.length > 0 && (
        <details className="mt-2">
          <summary className="text-sm text-yellow-700 cursor-pointer hover:underline">
            View Details
          </summary>
          <ul className="list-disc pl-5 mt-1 text-sm text-gray-600 space-y-1">
            {warning.evidence.map((evidence, idx) => (
              <li key={idx}>{evidence}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

function CheckResultRow({ check }: { check: PreflightCheckResult }) {
  const statusIcon = {
    pass: '✅',
    fail: '❌',
    warn: '⚠️',
  }[check.status];

  const statusColor = {
    pass: 'text-green-700',
    fail: 'text-red-700',
    warn: 'text-yellow-700',
  }[check.status];

  return (
    <div className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
      <div className="flex items-center gap-2 flex-1">
        <span>{statusIcon}</span>
        <span className={`font-medium ${statusColor}`}>
          {check.check.replace(/_/g, ' ')}
        </span>
        {check.details && (
          <span className="text-sm text-gray-500">({check.details})</span>
        )}
      </div>
      <span className="text-sm text-gray-500">{check.duration_ms}ms</span>
    </div>
  );
}
