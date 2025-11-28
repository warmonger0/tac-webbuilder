import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { intervals } from '../config/intervals';

interface PreflightCheck {
  check: string;
  status: string;
  duration_ms: number;
  details?: string;
}

interface BlockingFailure {
  check: string;
  error: string;
  fix: string;
  failing_tests?: string[];
}

interface Warning {
  check: string;
  message: string;
  impact: string;
}

interface PreflightCheckResult {
  passed: boolean;
  blocking_failures: BlockingFailure[];
  warnings: Warning[];
  checks_run: PreflightCheck[];
  total_duration_ms: number;
}

export function PreflightCheckPanel() {
  const [skipTests, setSkipTests] = useState(false);

  const { data, isLoading, error, refetch } = useQuery<PreflightCheckResult>({
    queryKey: ['preflightChecks', skipTests],
    queryFn: async () => {
      const response = await fetch(`/api/preflight-checks?skip_tests=${skipTests}`);
      if (!response.ok) {
        throw new Error('Failed to fetch pre-flight checks');
      }
      return response.json();
    },
    refetchInterval: intervals.components.preflightChecks.autoRefreshInterval,
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pass':
        return '✅';
      case 'warn':
        return '⚠️';
      case 'fail':
        return '❌';
      default:
        return '❓';
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-lg font-bold text-gray-900">Pre-Flight Health Checks</h3>
          <p className="text-sm text-gray-600">
            System readiness before launching ADW workflows
          </p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center text-sm text-gray-700">
            <input
              type="checkbox"
              checked={skipTests}
              onChange={(e) => setSkipTests(e.target.checked)}
              className="mr-2"
            />
            Skip test checks (faster)
          </label>
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Checking...' : 'Run Checks'}
          </button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-8 text-gray-600">
          <div className="animate-pulse">Running pre-flight checks...</div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-medium">Error running pre-flight checks</p>
          <p className="text-red-600 text-sm mt-1">{(error as Error).message}</p>
        </div>
      )}

      {/* Results */}
      {data && !isLoading && (
        <div className="space-y-4">
          {/* Overall Status Banner */}
          <div
            className={`p-4 rounded-lg border ${
              data.passed
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}
          >
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{data.passed ? '✅' : '❌'}</span>
                <div>
                  <p className={`font-bold ${data.passed ? 'text-green-800' : 'text-red-800'}`}>
                    {data.passed ? 'All Checks Passed' : 'Checks Failed'}
                  </p>
                  <p className="text-sm text-gray-600">
                    {data.passed
                      ? 'System ready for ADW workflows'
                      : 'Fix blocking issues before launching workflows'}
                  </p>
                </div>
              </div>
              <div className="text-sm text-gray-600">
                Completed in {data.total_duration_ms}ms
              </div>
            </div>
          </div>

          {/* Blocking Failures */}
          {data.blocking_failures.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <h4 className="font-bold text-red-800 mb-3">
                🚫 Blocking Failures ({data.blocking_failures.length})
              </h4>
              <div className="space-y-3">
                {data.blocking_failures.map((failure, index) => (
                  <div key={index} className="bg-white rounded p-3">
                    <div className="font-medium text-red-900">{failure.check}</div>
                    <div className="text-sm text-red-700 mt-1">{failure.error}</div>
                    <div className="text-sm text-gray-700 mt-2">
                      <span className="font-medium">Fix:</span> {failure.fix}
                    </div>
                    {failure.failing_tests && failure.failing_tests.length > 0 && (
                      <details className="mt-2">
                        <summary className="text-sm text-gray-600 cursor-pointer hover:text-gray-800">
                          View failing tests ({failure.failing_tests.length})
                        </summary>
                        <ul className="mt-2 ml-4 text-xs text-gray-600 space-y-1">
                          {failure.failing_tests.map((test, idx) => (
                            <li key={idx} className="font-mono">
                              {test}
                            </li>
                          ))}
                        </ul>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Warnings */}
          {data.warnings.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h4 className="font-bold text-yellow-800 mb-3">
                ⚠️ Warnings ({data.warnings.length})
              </h4>
              <div className="space-y-3">
                {data.warnings.map((warning, index) => (
                  <div key={index} className="bg-white rounded p-3">
                    <div className="font-medium text-yellow-900">{warning.check}</div>
                    <div className="text-sm text-yellow-700 mt-1">{warning.message}</div>
                    <div className="text-sm text-gray-700 mt-2">
                      <span className="font-medium">Impact:</span> {warning.impact}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Individual Check Details */}
          <div>
            <h4 className="font-bold text-gray-800 mb-3">Check Details</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {data.checks_run.map((check, index) => (
                <div
                  key={index}
                  className="bg-gray-50 border border-gray-200 rounded-lg p-3"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-2">
                      <span>{getStatusIcon(check.status)}</span>
                      <div>
                        <div className="font-medium text-gray-900">
                          {check.check.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </div>
                        {check.details && (
                          <div className="text-xs text-gray-600 mt-1">
                            {check.details}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">{check.duration_ms}ms</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
