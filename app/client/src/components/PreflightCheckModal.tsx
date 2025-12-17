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
  DryRunResult,
  DryRunPhase,
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

          {/* Workflow Dry-Run (if present) */}
          {results.dry_run && (
            <DryRunSection dryRun={results.dry_run} />
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

function DryRunSection({ dryRun }: { dryRun: DryRunResult }) {
  return (
    <div className="space-y-3">
      <h4 className="font-semibold text-blue-800 flex items-center gap-2">
        <span className="text-xl">📋</span>
        Workflow Plan
      </h4>

      {/* Summary */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-sm text-gray-600">Total Phases</p>
            <p className="text-lg font-bold text-blue-900">{dryRun.summary.total_phases}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Estimated Cost</p>
            <p className="text-lg font-bold text-blue-900">{dryRun.summary.total_cost}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Estimated Time</p>
            <p className="text-lg font-bold text-blue-900">{dryRun.summary.total_time}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">High Risk Phases</p>
            <p className="text-lg font-bold text-red-900">{dryRun.summary.high_risk_phases}</p>
          </div>
        </div>
        {dryRun.pattern_info.matched && (
          <p className="text-xs text-gray-600 mt-2">
            ⚡ Using cached pattern: {dryRun.pattern_info.source}
          </p>
        )}
      </div>

      {/* Phase Breakdown */}
      <details className="border border-blue-200 rounded-lg">
        <summary className="p-3 cursor-pointer hover:bg-blue-50 font-medium text-blue-900">
          View Phase Details ({dryRun.phases.length} phases)
        </summary>
        <div className="p-3 space-y-3 border-t border-blue-200">
          {dryRun.phases.map((phase) => (
            <PhaseCard key={phase.phase_number} phase={phase} />
          ))}
        </div>
      </details>
    </div>
  );
}

function PhaseCard({ phase }: { phase: DryRunPhase }) {
  const riskColor = {
    low: 'bg-green-100 text-green-800 border-green-300',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    high: 'bg-red-100 text-red-800 border-red-300',
  }[phase.risk_level];

  return (
    <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-900">
              Phase {phase.phase_number}: {phase.title}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded border ${riskColor}`}>
              {phase.risk_level}
            </span>
          </div>
          {phase.description && (
            <p className="text-sm text-gray-600 mt-1">{phase.description}</p>
          )}
        </div>
        <div className="text-right ml-4">
          <p className="text-sm font-semibold text-blue-700">{phase.estimated_cost}</p>
          <p className="text-xs text-gray-500">{phase.estimated_time}</p>
        </div>
      </div>

      {phase.files_to_modify.length > 0 && (
        <details className="mt-2">
          <summary className="text-xs text-blue-600 cursor-pointer hover:underline">
            Files to modify ({phase.files_to_modify.length})
          </summary>
          <ul className="list-disc pl-5 mt-1 text-xs text-gray-600 space-y-0.5">
            {phase.files_to_modify.slice(0, 5).map((file, idx) => (
              <li key={idx} className="font-mono">
                {file}
              </li>
            ))}
            {phase.files_to_modify.length > 5 && (
              <li className="text-gray-500">
                ...and {phase.files_to_modify.length - 5} more
              </li>
            )}
          </ul>
        </details>
      )}

      {phase.depends_on.length > 0 && (
        <p className="text-xs text-gray-500 mt-2">
          Depends on: Phase{phase.depends_on.length > 1 ? 's' : ''} {phase.depends_on.join(', ')}
        </p>
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
