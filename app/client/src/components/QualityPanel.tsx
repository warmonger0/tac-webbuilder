/**
 * Quality Control Panel (Panel 7)
 *
 * Displays comprehensive code quality metrics including:
 * - Test coverage (overall, backend, frontend, ADWs)
 * - Naming convention compliance
 * - File structure metrics
 * - Linting issues
 * - Overall quality score
 *
 * Uses WebSocket for real-time updates (5-minute background refresh)
 */

import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { qcMetricsClient, QCMetrics } from '../api/qcMetricsClient';
import { LoadingState } from './common/LoadingState';
import { ErrorBanner } from './common/ErrorBanner';
import { formatErrorMessage, logError } from '../utils/errorHandler';
import { apiConfig } from '../config/api';

// ============================================================================
// Utility Functions
// ============================================================================

function getScoreColor(score: number): string {
  if (score >= 90) return 'text-emerald-400';
  if (score >= 75) return 'text-blue-400';
  if (score >= 60) return 'text-yellow-400';
  return 'text-red-400';
}

function getScoreBgColor(score: number): string {
  if (score >= 90) return 'bg-emerald-900/20 border-emerald-500/50';
  if (score >= 75) return 'bg-blue-900/20 border-blue-500/50';
  if (score >= 60) return 'bg-yellow-900/20 border-yellow-500/50';
  return 'bg-red-900/20 border-red-500/50';
}

function getCoverageColor(coverage: number): string {
  if (coverage >= 80) return 'text-emerald-400';
  if (coverage >= 60) return 'text-yellow-400';
  return 'text-red-400';
}

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// ============================================================================
// Sub-Components
// ============================================================================

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: string;
  icon?: string;
  children?: React.ReactNode;
}

function MetricCard({ title, value, subtitle, color = 'text-gray-300', icon, children }: MetricCardProps) {
  return (
    <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-400">{title}</h3>
        {icon && <span className="text-lg">{icon}</span>}
      </div>
      <div className={`text-2xl font-bold ${color} mb-1`}>{value}</div>
      {subtitle && <div className="text-xs text-gray-500">{subtitle}</div>}
      {children}
    </div>
  );
}

interface CoverageSectionProps {
  coverage: QCMetrics['coverage'];
}

function CoverageSection({ coverage }: CoverageSectionProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-200 flex items-center gap-2">
        <span>📊</span>
        Test Coverage
      </h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Overall Coverage"
          value={`${coverage.overall_coverage}%`}
          color={getCoverageColor(coverage.overall_coverage)}
          icon="🎯"
        />
        <MetricCard
          title="Backend Coverage"
          value={`${coverage.backend_coverage}%`}
          color={getCoverageColor(coverage.backend_coverage)}
          icon="⚙️"
        />
        <MetricCard
          title="Frontend Coverage"
          value={`${coverage.frontend_coverage}%`}
          color={getCoverageColor(coverage.frontend_coverage)}
          icon="🖥️"
        />
        <MetricCard
          title="ADWs Coverage"
          value={`${coverage.adws_coverage}%`}
          color={getCoverageColor(coverage.adws_coverage)}
          icon="🤖"
        />
      </div>

      <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">Total Tests</span>
          <span className="text-lg font-semibold text-gray-200">{coverage.total_tests}</span>
        </div>
      </div>
    </div>
  );
}

interface NamingSectionProps {
  naming: QCMetrics['naming'];
}

function NamingSection({ naming }: NamingSectionProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-200 flex items-center gap-2">
        <span>📝</span>
        Naming Conventions
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Compliance Rate"
          value={`${naming.compliance_rate}%`}
          color={getCoverageColor(naming.compliance_rate)}
          icon="✓"
        />
        <MetricCard
          title="Files Checked"
          value={naming.total_files_checked}
          subtitle="Total code files"
          color="text-blue-400"
        />
        <MetricCard
          title="Violations"
          value={naming.violations.length}
          subtitle={naming.violations.length > 0 ? 'Needs attention' : 'All good!'}
          color={naming.violations.length === 0 ? 'text-emerald-400' : 'text-yellow-400'}
        />
      </div>

      {naming.violations.length > 0 && (
        <div className="bg-slate-800/30 rounded-lg border border-slate-700/30">
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-slate-700/20 transition-colors"
          >
            <span className="text-sm font-medium text-gray-300">
              View Violations ({naming.violations.length})
            </span>
            <span className="text-gray-400">{expanded ? '▼' : '▶'}</span>
          </button>

          {expanded && (
            <div className="px-4 pb-4 max-h-64 overflow-y-auto">
              <div className="space-y-2">
                {naming.violations.map((violation, idx) => (
                  <div
                    key={`${violation.file}-${violation.issue}-${idx}`}
                    className="bg-slate-900/50 rounded p-3 border-l-2 border-yellow-500/50"
                  >
                    <div className="text-xs font-mono text-gray-400 mb-1">{violation.file}</div>
                    <div className="text-sm text-gray-300">{violation.issue}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      Severity: {violation.severity}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface FileStructureSectionProps {
  fileStructure: QCMetrics['file_structure'];
}

function FileStructureSection({ fileStructure }: FileStructureSectionProps) {
  const [showOversized, setShowOversized] = useState(false);
  const [showLong, setShowLong] = useState(false);

  const hasIssues =
    fileStructure.oversized_files.length > 0 || fileStructure.long_files.length > 0;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-200 flex items-center gap-2">
        <span>📁</span>
        File Structure
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Total Files"
          value={fileStructure.total_files}
          subtitle="Code files analyzed"
          color="text-blue-400"
          icon="📄"
        />
        <MetricCard
          title="Avg File Size"
          value={`${fileStructure.avg_file_size_kb} KB`}
          subtitle="Average across all files"
          color="text-gray-300"
          icon="📏"
        />
        <MetricCard
          title="Issues"
          value={fileStructure.oversized_files.length + fileStructure.long_files.length}
          subtitle={hasIssues ? 'Files need attention' : 'All files OK'}
          color={hasIssues ? 'text-yellow-400' : 'text-emerald-400'}
          icon={hasIssues ? '⚠️' : '✅'}
        />
      </div>

      {fileStructure.oversized_files.length > 0 && (
        <div className="bg-slate-800/30 rounded-lg border border-slate-700/30">
          <button
            onClick={() => setShowOversized(!showOversized)}
            className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-slate-700/20 transition-colors"
          >
            <span className="text-sm font-medium text-gray-300">
              Oversized Files ({fileStructure.oversized_files.length}) &gt; 500 KB
            </span>
            <span className="text-gray-400">{showOversized ? '▼' : '▶'}</span>
          </button>

          {showOversized && (
            <div className="px-4 pb-4 max-h-48 overflow-y-auto">
              <div className="space-y-2">
                {fileStructure.oversized_files.map((file) => (
                  <div
                    key={`${file.file}-${file.size_kb}`}
                    className="bg-slate-900/50 rounded p-2 flex items-center justify-between"
                  >
                    <span className="text-xs font-mono text-gray-400">{file.file}</span>
                    <span className="text-sm font-semibold text-yellow-400">
                      {file.size_kb} KB
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {fileStructure.long_files.length > 0 && (
        <div className="bg-slate-800/30 rounded-lg border border-slate-700/30">
          <button
            onClick={() => setShowLong(!showLong)}
            className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-slate-700/20 transition-colors"
          >
            <span className="text-sm font-medium text-gray-300">
              Long Files ({fileStructure.long_files.length}) &gt; 1000 lines
            </span>
            <span className="text-gray-400">{showLong ? '▼' : '▶'}</span>
          </button>

          {showLong && (
            <div className="px-4 pb-4 max-h-48 overflow-y-auto">
              <div className="space-y-2">
                {fileStructure.long_files.map((file) => (
                  <div
                    key={`${file.file}-${file.lines}`}
                    className="bg-slate-900/50 rounded p-2 flex items-center justify-between"
                  >
                    <span className="text-xs font-mono text-gray-400">{file.file}</span>
                    <span className="text-sm font-semibold text-yellow-400">
                      {file.lines} lines
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface LintingSectionProps {
  linting: QCMetrics['linting'];
}

function LintingSection({ linting }: LintingSectionProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-200 flex items-center gap-2">
        <span>🔍</span>
        Linting Issues
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Total Issues"
          value={linting.total_issues}
          subtitle={linting.total_issues === 0 ? 'No issues found' : 'Across all code'}
          color={linting.total_issues === 0 ? 'text-emerald-400' : 'text-red-400'}
          icon={linting.total_issues === 0 ? '✅' : '⚠️'}
        />
        <MetricCard
          title="Backend Issues"
          value={linting.backend_issues}
          subtitle={`${linting.backend_errors} errors, ${linting.backend_warnings} warnings`}
          color={linting.backend_errors > 0 ? 'text-red-400' : 'text-yellow-400'}
          icon="⚙️"
        />
        <MetricCard
          title="Frontend Issues"
          value={linting.frontend_issues}
          subtitle={`${linting.frontend_errors} errors, ${linting.frontend_warnings} warnings`}
          color={linting.frontend_errors > 0 ? 'text-red-400' : 'text-yellow-400'}
          icon="🖥️"
        />
      </div>

      <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-400">Backend Errors:</span>
            <span className="ml-2 font-semibold text-red-400">{linting.backend_errors}</span>
          </div>
          <div>
            <span className="text-gray-400">Frontend Errors:</span>
            <span className="ml-2 font-semibold text-red-400">{linting.frontend_errors}</span>
          </div>
          <div>
            <span className="text-gray-400">Backend Warnings:</span>
            <span className="ml-2 font-semibold text-yellow-400">{linting.backend_warnings}</span>
          </div>
          <div>
            <span className="text-gray-400">Frontend Warnings:</span>
            <span className="ml-2 font-semibold text-yellow-400">
              {linting.frontend_warnings}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function QualityPanel() {
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [wsMetrics, setWsMetrics] = useState<QCMetrics | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const maxReconnectAttempts = 5;

  // Fetch QC metrics (initial load only, then WebSocket takes over)
  const { data: initialMetrics, isLoading } = useQuery<QCMetrics>({
    queryKey: ['qc-metrics'],
    queryFn: qcMetricsClient.getQCMetrics,
    staleTime: Infinity, // WebSocket will keep it fresh
    retry: 2,
  });

  // Use WebSocket data if available, otherwise use initial data
  const metrics = wsMetrics || initialMetrics;

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      if (reconnectAttempts.current >= maxReconnectAttempts) {
        console.warn('[QC_WS] Max reconnection attempts reached');
        return;
      }

      const url = apiConfig.websocket.qcMetrics();
      console.log(`[QC_WS] Connecting to: ${url}`);

      try {
        const ws = new WebSocket(url);

        ws.onopen = () => {
          console.log('[QC_WS] Connected');
          reconnectAttempts.current = 0;
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            if (message.type === 'qc_metrics_update') {
              console.log('[QC_WS] Metrics updated');
              setWsMetrics(message.data);
            }
          } catch (err) {
            console.error('[QC_WS] Message parse error:', err);
          }
        };

        ws.onerror = (error) => {
          console.error('[QC_WS] Error:', error);
        };

        ws.onclose = () => {
          console.log('[QC_WS] Disconnected');
          setIsConnected(false);

          // Attempt reconnect with exponential backoff
          reconnectAttempts.current++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, delay);
        };

        wsRef.current = ws;
      } catch (err) {
        console.error('[QC_WS] Connection failed:', err);
      }
    };

    connectWebSocket();

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    setError(null);

    try {
      const freshMetrics = await qcMetricsClient.refreshQCMetrics();
      setWsMetrics(freshMetrics);
    } catch (err: unknown) {
      logError('[QualityPanel]', 'Refresh metrics', err);
      setError(formatErrorMessage(err));
    } finally {
      setIsRefreshing(false);
    }
  };

  if (isLoading) {
    return <LoadingState message="Loading quality metrics..." />;
  }

  if (!metrics) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <ErrorBanner
          error={new Error('No QC metrics available')}
          onDismiss={() => setError(null)}
        />
      </div>
    );
  }

  return (
    <div className="bg-slate-900 text-gray-100 rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-100 flex items-center gap-2">
            <span>🎯</span>
            Quality Control Panel
            {isConnected && (
              <span className="ml-2 text-xs text-emerald-400 bg-emerald-900/20 px-2 py-1 rounded-full">
                Live
              </span>
            )}
          </h2>
          <p className="text-sm text-gray-400 mt-1">
            Last updated: {formatDate(metrics.last_updated)}
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center gap-2"
        >
          <span>{isRefreshing ? '🔄' : '↻'}</span>
          <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
        </button>
      </div>

      {/* Error Banner */}
      {error && <ErrorBanner error={new Error(error)} onDismiss={() => setError(null)} />}

      {/* Overall Score */}
      <div className={`rounded-lg p-6 mb-6 border-2 ${getScoreBgColor(metrics.overall_score)}`}>
        <div className="text-center">
          <div className="text-sm font-medium text-gray-400 mb-2">Overall Quality Score</div>
          <div className={`text-6xl font-bold ${getScoreColor(metrics.overall_score)} mb-2`}>
            {metrics.overall_score}
          </div>
          <div className="text-sm text-gray-500">
            {metrics.overall_score >= 90 && 'Excellent code quality!'}
            {metrics.overall_score >= 75 && metrics.overall_score < 90 && 'Good code quality'}
            {metrics.overall_score >= 60 && metrics.overall_score < 75 && 'Fair code quality'}
            {metrics.overall_score < 60 && 'Needs improvement'}
          </div>
        </div>
      </div>

      {/* Metrics Sections */}
      <div className="space-y-8">
        <CoverageSection coverage={metrics.coverage} />
        <div className="border-t border-slate-700/50"></div>

        <NamingSection naming={metrics.naming} />
        <div className="border-t border-slate-700/50"></div>

        <FileStructureSection fileStructure={metrics.file_structure} />
        <div className="border-t border-slate-700/50"></div>

        <LintingSection linting={metrics.linting} />
      </div>
    </div>
  );
}
