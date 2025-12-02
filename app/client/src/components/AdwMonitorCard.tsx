import { useState } from 'react';
import {
  type AdwHealthCheckResponse,
  type AdwMonitorSummary,
  type AdwWorkflowStatus,
  getAdwMonitor
} from '../api/client';
import { useReliablePolling } from '../hooks/useReliablePolling';
import { ConnectionStatusIndicator } from './ConnectionStatusIndicator';
import { intervals } from '../config/intervals';
import { phaseSvgIconMap, workflowPhases, workflowTypeLabels } from '../config/workflows';
import { uiText } from '../config/ui';

export function AdwMonitorCard() {
  const [workflows, setWorkflows] = useState<AdwWorkflowStatus[]>([]);
  const [summary, setSummary] = useState<AdwMonitorSummary>({ total: 0, running: 0, completed: 0, failed: 0, paused: 0 });
  const [healthStatus, setHealthStatus] = useState<AdwHealthCheckResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [debugMode, setDebugMode] = useState<boolean>(false);

  const pollingState = useReliablePolling<{ workflows: AdwWorkflowStatus[]; summary: AdwMonitorSummary }>({
    fetchFn: getAdwMonitor,
    onSuccess: (data) => {
      // DEBUG: Log received data
      console.log('[AdwMonitorCard] Received data:', {
        totalWorkflows: data.workflows.length,
        summary: data.summary,
        runningCount: data.workflows.filter(w => w.status === 'running').length
      });

      setWorkflows(data.workflows);
      setSummary(data.summary);
      setError(null);

      // Note: Removed cascade health check fetch for performance.
      // Health checks can be added on-demand via separate UI action if needed.
      setHealthStatus(null);
    },
    onError: (err) => {
      setError(err.message);
    },
    enabled: true,
    // Dynamic interval: active polling for running workflows, idle polling otherwise
    interval: summary.running > 0
      ? intervals.components.adwMonitor.activePollingInterval
      : intervals.components.adwMonitor.idlePollingInterval,
    adaptiveInterval: true,
  });

  // Note: Removed useEffect that forced polling restart on interval changes.
  // The useReliablePolling hook now handles dynamic intervals internally without restarting.

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hours > 0) return `${hours}h ${mins}m`;
    if (mins > 0) return `${mins}m ${secs}s`;
    return `${secs}s`;
  };

  const formatCost = (cost: number | null) => {
    if (!cost) return '$0.00';
    return `$${cost.toFixed(2)}`;
  };

  const formatLastUpdated = (timestamp: string | null) => {
    if (!timestamp) return 'Unknown';
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffSecs = Math.floor(diffMs / 1000);

      if (diffSecs < 60) return `${diffSecs}s ago`;
      if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}m ago`;
      if (diffSecs < 86400) return `${Math.floor(diffSecs / 3600)}h ago`;
      return `${Math.floor(diffSecs / 86400)}d ago`;
    } catch {
      return 'Unknown';
    }
  };

  // Workflow phases for the pipeline visualization (imported from config)
  const phasesWithIcons = workflowPhases.map(phase => ({
    name: phase.name,
    icon: phaseSvgIconMap[phase.phase] || 'clipboard',
    key: phase.phase
  }));

  // Icon rendering helper
  const renderIcon = (iconName: string, status: 'pending' | 'active' | 'completed' = 'pending') => {
    const iconClass = `w-6 h-6 transition-all duration-300 ${
      status === 'completed'
        ? 'text-emerald-400 drop-shadow-[0_0_8px_rgba(16,185,129,0.8)]'
        : status === 'active'
        ? 'text-emerald-400 drop-shadow-[0_0_10px_rgba(16,185,129,1)]'
        : 'text-slate-500'
    }`;

    switch (iconName) {
      case 'clipboard':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        );
      case 'check-circle':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'cube':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
        );
      case 'sparkles':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
          </svg>
        );
      case 'beaker':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
        );
      case 'eye':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        );
      case 'document':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        );
      case 'rocket':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        );
      case 'trash':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        );
      default:
        return <span className="text-lg">•</span>;
    }
  };

  const getPhaseStatus = (workflow: AdwWorkflowStatus, phaseKey: string) => {
    const lowerPhase = phaseKey.toLowerCase();
    const currentPhase = workflow.current_phase?.toLowerCase() || '';

    // Check if this phase is completed
    if (workflow.phases_completed.some(p => p.toLowerCase().includes(lowerPhase))) {
      return 'completed';
    }
    // Check if this is the current phase
    if (currentPhase.includes(lowerPhase)) {
      return 'active';
    }
    // Otherwise it's pending
    return 'pending';
  };

  if (!pollingState.isPolling && workflows.length === 0) {
    return (
      <div className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-lg shadow-xl border border-slate-200 p-8">
        <div className="flex items-center justify-center h-48">
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 relative">
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-teal-500 rounded-full animate-ping opacity-75"></div>
              <div className="relative bg-gradient-to-r from-emerald-500 to-teal-600 rounded-full w-16 h-16 flex items-center justify-center">
                <svg className="w-8 h-8 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
            </div>
            <p className="text-slate-600 font-medium">Loading workflows...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gradient-to-br from-red-50 to-rose-100 rounded-lg shadow-xl border border-red-200 p-8">
        <div className="flex flex-col items-center text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-red-500 to-rose-600 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-red-700 font-semibold mb-2">Unable to load workflows</p>
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  // Get current workflow (first RUNNING or PAUSED workflow only)
  // Only show active workflows - completed/failed workflows are historical
  const currentWorkflow = workflows.find(w => w.status === 'running')
    || workflows.find(w => w.status === 'paused')
    || null;

  // Determine colors based on workflow status
  const getStatusColors = (status: string) => {
    switch (status) {
      case 'failed':
        return {
          card: 'shadow-red-500/10',
          cardGlow: 'from-red-500/5 to-red-500/5',
          header: 'from-red-500/10 to-red-500/10',
          icon: 'from-red-500 to-red-600',
          iconShadow: 'shadow-[0_0_15px_rgba(239,68,68,0.5)]',
          iconGlow: 'from-red-400/20 to-red-400/20',
          innerGlow: 'from-red-500/5'
        };
      case 'running':
        return {
          card: 'shadow-emerald-500/10',
          cardGlow: 'from-emerald-500/5 to-teal-500/5',
          header: 'from-emerald-500/10 to-teal-500/10',
          icon: 'from-emerald-500 to-teal-500',
          iconShadow: 'shadow-[0_0_15px_rgba(16,185,129,0.5)]',
          iconGlow: 'from-emerald-400/20 to-teal-400/20',
          innerGlow: 'from-emerald-500/5'
        };
      case 'paused':
        return {
          card: 'shadow-yellow-500/10',
          cardGlow: 'from-yellow-500/5 to-orange-500/5',
          header: 'from-yellow-500/10 to-orange-500/10',
          icon: 'from-yellow-500 to-orange-500',
          iconShadow: 'shadow-[0_0_15px_rgba(234,179,8,0.5)]',
          iconGlow: 'from-yellow-400/20 to-orange-400/20',
          innerGlow: 'from-yellow-500/5'
        };
      default: // completed, queued, etc.
        return {
          card: 'shadow-slate-500/10',
          cardGlow: 'from-slate-500/5 to-slate-500/5',
          header: 'from-slate-500/10 to-slate-500/10',
          icon: 'from-slate-500 to-slate-600',
          iconShadow: 'shadow-[0_0_15px_rgba(100,116,139,0.5)]',
          iconGlow: 'from-slate-400/20 to-slate-400/20',
          innerGlow: 'from-slate-500/5'
        };
    }
  };

  const colors = getStatusColors(currentWorkflow?.status || 'completed');

  return (
    <div className={`bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg shadow-xl ${colors.card} overflow-hidden border border-slate-700 flex-1 flex flex-col relative`}>
        {/* Subtle status-based glow around the card */}
        <div className={`absolute -inset-0.5 bg-gradient-to-r ${colors.cardGlow} rounded-lg blur-sm -z-10`}></div>

      {/* Header with Gradient */}
      <div className="relative px-4 py-3 border-b border-slate-700/50">
        <div className={`absolute inset-0 bg-gradient-to-r ${colors.header}`}></div>
        <div className="relative">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`relative w-8 h-8 bg-gradient-to-r ${colors.icon} rounded-lg flex items-center justify-center ${colors.iconShadow}`}>
                {/* Icon glow */}
                <div className={`absolute -inset-1 bg-gradient-to-r ${colors.iconGlow} rounded-lg blur-md animate-pulse`}></div>
                <svg className="w-5 h-5 text-white relative z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
                  {uiText.adwMonitor.currentWorkflowTitle}
                </h2>
                <p className="text-slate-400 text-xs">{uiText.adwMonitor.currentWorkflowSubtitle}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setDebugMode(!debugMode)}
                className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                  debugMode
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50'
                    : 'bg-slate-700/50 text-slate-400 border border-slate-600/50 hover:bg-slate-700 hover:text-slate-300'
                }`}
                title="Toggle debug mode to see process details and terminal commands"
              >
                {debugMode ? '⚙️ Debug' : '⚙️'}
              </button>
              <ConnectionStatusIndicator
                isConnected={pollingState.isPolling}
                connectionQuality={pollingState.connectionQuality}
                lastUpdated={pollingState.lastUpdated}
                consecutiveErrors={pollingState.consecutiveErrors}
                onRetry={pollingState.retry}
                variant="compact"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Workflow Display */}
      <div className="p-5 flex-1 flex flex-col">
        {!currentWorkflow ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-emerald-500/20 to-teal-500/20 rounded-2xl flex items-center justify-center">
              <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
            </div>
            <p className="text-lg font-semibold text-slate-300 mb-1">{uiText.adwMonitor.noActiveWorkflow}</p>
            <p className="text-slate-500 text-sm">Queue is empty</p>
          </div>
        ) : (
          <div>
            <div
              className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl border border-slate-700/50 shadow-[0_0_15px_rgba(16,185,129,0.1)] overflow-hidden relative"
            >
              {/* Subtle inner glow */}
              <div className={`absolute inset-0 bg-gradient-to-br ${colors.innerGlow} to-transparent pointer-events-none`}></div>
                {/* Header */}
                <div className="px-4 py-3 border-b border-slate-700/50 flex items-center justify-between relative z-10">
                  <div className="flex items-center gap-3">
                    {currentWorkflow.issue_number ? (
                      <div className="flex items-center gap-2">
                        {currentWorkflow.github_url ? (
                          <a
                            href={currentWorkflow.github_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-emerald-400 hover:text-emerald-300 font-mono text-lg font-bold transition-colors"
                          >
                            #{currentWorkflow.issue_number}
                          </a>
                        ) : (
                          <span className="text-emerald-400 font-mono text-lg font-bold">
                            #{currentWorkflow.issue_number}
                          </span>
                        )}
                        {currentWorkflow.pr_number && currentWorkflow.github_url && (
                          <>
                            <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                            <a
                              href={`https://github.com/${new URL(currentWorkflow.github_url).pathname.split('/').slice(1, 3).join('/')}/pull/${currentWorkflow.pr_number}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-purple-400 hover:text-purple-300 font-mono text-sm font-bold transition-colors flex items-center gap-1"
                              title="Pull Request"
                            >
                              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 16 16">
                                <path fillRule="evenodd" d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z" />
                              </svg>
                              PR #{currentWorkflow.pr_number}
                            </a>
                          </>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-500 font-mono text-lg font-bold">
                        {currentWorkflow.adw_id.substring(0, 8)}
                      </span>
                    )}
                    <div>
                      <h3 className="text-white font-semibold text-base leading-tight">
                        {workflowTypeLabels.getLabel(currentWorkflow.workflow_template)}
                      </h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="px-2 py-0.5 bg-blue-500/20 text-blue-300 text-xs rounded-md font-medium">
                          {currentWorkflow.workflow_template.replace('adw_', '').replace('_', ' ')}
                        </span>
                        {currentWorkflow.issue_class && (
                          <span className="px-2 py-0.5 bg-slate-700/50 text-slate-300 text-xs rounded-md font-medium">
                            {currentWorkflow.issue_class}
                          </span>
                        )}
                        <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium ${
                          currentWorkflow.status === 'running' ? 'bg-emerald-500/20 text-emerald-300' :
                          currentWorkflow.status === 'completed' ? 'bg-green-500/20 text-green-300' :
                          currentWorkflow.status === 'failed' ? 'bg-red-500/20 text-red-300' :
                          'bg-slate-500/20 text-slate-300'
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${
                            currentWorkflow.status === 'running' ? 'bg-emerald-400 animate-pulse' :
                            currentWorkflow.status === 'completed' ? 'bg-green-400' :
                            currentWorkflow.status === 'failed' ? 'bg-red-400' :
                            'bg-slate-400'
                          }`}></span>
                          {currentWorkflow.status.toUpperCase()}
                        </div>
                        {/* Process Active Badge - Real-time verification */}
                        {currentWorkflow.is_process_active ? (
                          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium bg-green-500/20 text-green-300 border border-green-500/30"
                            title="Process is actively running (verified via ps aux)">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
                            PROCESS ACTIVE
                          </div>
                        ) : currentWorkflow.status === 'running' ? (
                          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium bg-yellow-500/20 text-yellow-300 border border-yellow-500/30"
                            title="Marked as running but process not detected">
                            <span className="w-1.5 h-1.5 rounded-full bg-yellow-400"></span>
                            NO PROCESS
                          </div>
                        ) : null}

                        {/* Health Status Badge */}
                        {healthStatus && (
                          <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium ${
                            healthStatus.overall_health === 'ok' ? 'bg-green-500/20 text-green-300' :
                            healthStatus.overall_health === 'warning' ? 'bg-yellow-500/20 text-yellow-300' :
                            'bg-red-500/20 text-red-300'
                          }`} title={healthStatus.warnings.join(', ')}>
                            <span className={`w-1.5 h-1.5 rounded-full ${
                              healthStatus.overall_health === 'ok' ? 'bg-green-400' :
                              healthStatus.overall_health === 'warning' ? 'bg-yellow-400' :
                              'bg-red-400'
                            }`}></span>
                            {healthStatus.overall_health === 'ok' ? '🟢' : healthStatus.overall_health === 'warning' ? '🟡' : '🔴'} HEALTH
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-bold text-lg">
                      {formatCost(currentWorkflow.current_cost)}
                    </div>
                    {currentWorkflow.estimated_cost_total && (
                      <div className="text-slate-400 text-xs">
                        of {formatCost(currentWorkflow.estimated_cost_total)}
                      </div>
                    )}
                  </div>
                </div>

                {/* Debug Information Panel */}
                {debugMode && (
                  <div className="px-4 py-3 bg-slate-950/50 border-y border-slate-700/50">
                    <div className="space-y-3">
                      {/* Status Analysis */}
                      <div>
                        <h4 className="text-xs font-semibold text-emerald-400 mb-2 flex items-center gap-2">
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Status Verification
                        </h4>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="bg-slate-800/50 rounded p-2">
                            <span className="text-slate-400">Process Active:</span>
                            <span className={`ml-2 font-mono ${currentWorkflow.is_process_active ? 'text-green-400' : 'text-red-400'}`}>
                              {currentWorkflow.is_process_active ? 'true' : 'false'}
                            </span>
                          </div>
                          <div className="bg-slate-800/50 rounded p-2">
                            <span className="text-slate-400">Status:</span>
                            <span className="ml-2 font-mono text-blue-400">{currentWorkflow.status}</span>
                          </div>
                          <div className="bg-slate-800/50 rounded p-2">
                            <span className="text-slate-400">Phases Complete:</span>
                            <span className="ml-2 font-mono text-purple-400">{currentWorkflow.phases_completed.length}/{currentWorkflow.total_phases}</span>
                          </div>
                          <div className="bg-slate-800/50 rounded p-2">
                            <span className="text-slate-400">Progress:</span>
                            <span className="ml-2 font-mono text-cyan-400">{currentWorkflow.phase_progress}%</span>
                          </div>
                        </div>
                      </div>

                      {/* Terminal Commands */}
                      <div>
                        <h4 className="text-xs font-semibold text-emerald-400 mb-2 flex items-center gap-2">
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          Terminal Commands
                        </h4>
                        <div className="space-y-1.5">
                          <div className="bg-slate-900/80 rounded p-2 font-mono text-xs">
                            <div className="text-slate-500 mb-1"># Check if process is running</div>
                            <code className="text-emerald-400">ps aux | grep {currentWorkflow.adw_id} | grep -v grep</code>
                          </div>
                          <div className="bg-slate-900/80 rounded p-2 font-mono text-xs">
                            <div className="text-slate-500 mb-1"># View workflow state</div>
                            <code className="text-cyan-400">cat agents/{currentWorkflow.adw_id}/adw_state.json | jq</code>
                          </div>
                          {currentWorkflow.issue_number && (
                            <div className="bg-slate-900/80 rounded p-2 font-mono text-xs">
                              <div className="text-slate-500 mb-1"># Check GitHub issue status</div>
                              <code className="text-purple-400">gh issue view {currentWorkflow.issue_number}</code>
                            </div>
                          )}
                          <div className="bg-slate-900/80 rounded p-2 font-mono text-xs">
                            <div className="text-slate-500 mb-1"># Check worktree</div>
                            <code className="text-yellow-400">ls -la trees/{currentWorkflow.adw_id}/</code>
                          </div>
                        </div>
                      </div>

                      {/* Phase Directories */}
                      {currentWorkflow.phases_completed.length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold text-emerald-400 mb-2 flex items-center gap-2">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                            </svg>
                            Completed Phase Directories
                          </h4>
                          <div className="flex flex-wrap gap-1.5">
                            {currentWorkflow.phases_completed.map(phase => (
                              <div key={phase} className="px-2 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded text-xs text-emerald-300 font-mono">
                                {phase}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Animated Pipeline Visualization - VoltAgent Style */}
                <div className="px-4 py-6 relative z-10">
                  <div className="relative min-h-[300px] flex items-center justify-center">
                    {/* Ambient Floating Particles */}
                    {[...Array(12)].map((_, i) => (
                      <div
                        key={`particle-${i}`}
                        className="absolute w-2 h-2 rounded-full opacity-60"
                        style={{
                          background: i % 3 === 0 ? '#10b981' : i % 3 === 1 ? '#a855f7' : '#06b6d4',
                          boxShadow: i % 3 === 0
                            ? '0 0 10px rgba(16,185,129,0.8)'
                            : i % 3 === 1
                            ? '0 0 10px rgba(168,85,247,0.8)'
                            : '0 0 10px rgba(6,182,212,0.8)',
                          left: `${15 + (i * 7)}%`,
                          top: `${20 + (i % 5) * 15}%`,
                          animation: `float ${3 + (i % 4)}s ease-in-out infinite`,
                          animationDelay: `${i * 0.3}s`,
                        }}
                      />
                    ))}

                    {/* Central Hub */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                      <div className="relative w-24 h-24 rounded-full border-2 border-emerald-400/60 bg-gradient-to-br from-slate-900 via-emerald-950 to-teal-950 flex items-center justify-center shadow-[0_0_50px_rgba(16,185,129,0.9)]">
                        {/* Pulsing glow rings */}
                        <div className="absolute inset-0 rounded-full border-2 border-emerald-400/40 animate-ping"></div>
                        <div className="absolute -inset-4 rounded-full border border-emerald-400/20 animate-pulse"></div>
                        <div className="absolute -inset-8 rounded-full border border-emerald-400/10"></div>

                        {/* Horizontal Lightning Ring */}
                        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" style={{ transform: 'rotate(-12deg)' }}>
                          <defs>
                            <filter id="lightningGlow">
                              <feGaussianBlur stdDeviation="1" result="coloredBlur"/>
                              <feMerge>
                                <feMergeNode in="coloredBlur"/>
                                <feMergeNode in="SourceGraphic"/>
                              </feMerge>
                            </filter>
                          </defs>

                          {/* Elliptical lightning ring wrapping around center */}
                          {/* Top arc - compressed vertically, extended horizontally */}
                          <path
                            d="M10,47 L13,45 L16,46 L20,44 L24,45 L28,43 L32,44 L37,42 L42,43 L47,42 L52,43 L57,42 L62,43 L67,42 L72,44 L76,43 L80,45 L84,44 L87,46 L90,47"
                            fill="none"
                            stroke="rgba(16,185,129,0.9)"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            filter="url(#lightningGlow)"
                            opacity="0"
                          >
                            <animate
                              attributeName="opacity"
                              values="0;0;0.9;0.7;0.9;0.5;0.8;0;0"
                              dur="1.5s"
                              begin="0s"
                              repeatCount="indefinite"
                            />
                          </path>

                          {/* Bottom arc - compressed vertically, extended horizontally */}
                          <path
                            d="M90,53 L87,55 L84,54 L80,56 L76,55 L72,57 L67,56 L62,58 L57,57 L52,58 L47,57 L42,58 L37,57 L32,58 L28,56 L24,57 L20,55 L16,56 L13,54 L10,53"
                            fill="none"
                            stroke="rgba(16,185,129,0.9)"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            filter="url(#lightningGlow)"
                            opacity="0"
                          >
                            <animate
                              attributeName="opacity"
                              values="0;0;0.8;0.6;0.9;0.6;0.7;0;0"
                              dur="1.5s"
                              begin="0.3s"
                              repeatCount="indefinite"
                            />
                          </path>

                          {/* Upper thin bolt - more horizontal */}
                          <path
                            d="M12,45 L18,43 L25,44 L33,42 L42,43 L50,42 L58,43 L67,42 L75,44 L82,43 L88,45"
                            fill="none"
                            stroke="rgba(255,255,255,0.8)"
                            strokeWidth="0.8"
                            strokeLinecap="round"
                            filter="url(#lightningGlow)"
                            opacity="0"
                          >
                            <animate
                              attributeName="opacity"
                              values="0;0;1;0.8;0;0"
                              dur="1.5s"
                              begin="0.15s"
                              repeatCount="indefinite"
                            />
                          </path>

                          {/* Lower thin bolt - more horizontal */}
                          <path
                            d="M88,55 L82,57 L75,56 L67,58 L58,57 L50,58 L42,57 L33,58 L25,56 L18,57 L12,55"
                            fill="none"
                            stroke="rgba(255,255,255,0.8)"
                            strokeWidth="0.8"
                            strokeLinecap="round"
                            filter="url(#lightningGlow)"
                            opacity="0"
                          >
                            <animate
                              attributeName="opacity"
                              values="0;0;1;0.7;0;0"
                              dur="1.5s"
                              begin="0.45s"
                              repeatCount="indefinite"
                            />
                          </path>

                          {/* Connecting branches - left side (shorter, more faint - behind W) */}
                          <path
                            d="M11,47 L10,49 L9,50 L10,51 L11,53"
                            fill="none"
                            stroke="rgba(16,185,129,0.4)"
                            strokeWidth="1"
                            strokeLinecap="round"
                            filter="url(#lightningGlow)"
                            opacity="0"
                          >
                            <animate
                              attributeName="opacity"
                              values="0;0;0.3;0.2;0.3;0;0"
                              dur="1.5s"
                              begin="0.2s"
                              repeatCount="indefinite"
                            />
                          </path>

                          {/* Connecting branches - right side (shorter, more faint - behind W) */}
                          <path
                            d="M89,47 L90,49 L91,50 L90,51 L89,53"
                            fill="none"
                            stroke="rgba(16,185,129,0.4)"
                            strokeWidth="1"
                            strokeLinecap="round"
                            filter="url(#lightningGlow)"
                            opacity="0"
                          >
                            <animate
                              attributeName="opacity"
                              values="0;0;0.25;0.15;0.25;0;0"
                              dur="1.5s"
                              begin="0.5s"
                              repeatCount="indefinite"
                            />
                          </path>

                          {/* Faint back arcs - very subtle behind W */}
                          <path
                            d="M10,49 L15,50 L20,49.5 L25,50.5"
                            fill="none"
                            stroke="rgba(16,185,129,0.3)"
                            strokeWidth="0.8"
                            strokeLinecap="round"
                            filter="url(#lightningGlow)"
                            opacity="0"
                          >
                            <animate
                              attributeName="opacity"
                              values="0;0;0.2;0.1;0.2;0;0"
                              dur="1.5s"
                              begin="0.4s"
                              repeatCount="indefinite"
                            />
                          </path>

                          <path
                            d="M90,49 L85,50 L80,49.5 L75,50.5"
                            fill="none"
                            stroke="rgba(16,185,129,0.3)"
                            strokeWidth="0.8"
                            strokeLinecap="round"
                            filter="url(#lightningGlow)"
                            opacity="0"
                          >
                            <animate
                              attributeName="opacity"
                              values="0;0;0.2;0.1;0.2;0;0"
                              dur="1.5s"
                              begin="0.6s"
                              repeatCount="indefinite"
                            />
                          </path>

                          {/* Small sparks - more spread out horizontally */}
                          {[20, 35, 50, 65, 80].map((x, i) => (
                            <circle
                              key={i}
                              cx={x}
                              cy={i % 2 === 0 ? 44 : 56}
                              r="0.5"
                              fill="rgba(16,185,129,1)"
                              filter="url(#lightningGlow)"
                              opacity="0"
                            >
                              <animate
                                attributeName="opacity"
                                values="0;1;0"
                                dur="0.5s"
                                begin={`${0.1 + i * 0.15}s`}
                                repeatCount="indefinite"
                              />
                              <animate
                                attributeName="r"
                                values="0.5;1;0.5"
                                dur="0.5s"
                                begin={`${0.1 + i * 0.15}s`}
                                repeatCount="indefinite"
                              />
                            </circle>
                          ))}
                        </svg>

                        {/* Stylized "W" outline */}
                        <svg className="w-8 h-8 text-white relative z-10 animate-pulse" viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round">
                          {/* Bold W shape */}
                          <path d="M10,20 L25,80 L40,35 L50,55 L60,35 L75,80 L90,20"
                            className="drop-shadow-[0_0_10px_rgba(255,255,255,0.9)]"
                            style={{
                              filter: 'drop-shadow(0 0 8px rgba(16,185,129,0.8))'
                            }}
                          />
                          {/* Inner glow effect */}
                          <path d="M10,20 L25,80 L40,35 L50,55 L60,35 L75,80 L90,20"
                            strokeWidth="3"
                            className="opacity-60"
                            style={{
                              filter: 'blur(2px)'
                            }}
                          />
                        </svg>
                      </div>
                    </div>

                    {/* Phase Nodes in Circle */}
                    {phasesWithIcons.map((phase, idx) => {
                      const status = getPhaseStatus(currentWorkflow, phase.key);
                      const totalPhases = phasesWithIcons.length;
                      const angle = (idx * 360) / totalPhases - 90; // Start from top
                      const radius = 110; // Distance from center
                      const x = Math.cos((angle * Math.PI) / 180) * radius;
                      const y = Math.sin((angle * Math.PI) / 180) * radius;

                      return (
                        <div
                          key={phase.key}
                          className="absolute"
                          style={{
                            left: '50%',
                            top: '50%',
                            transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`
                          }}
                        >
                          {/* Connection Line to Center */}
                          <svg
                            className="absolute top-1/2 left-1/2 -z-10"
                            style={{
                              width: `${Math.abs(x) + 40}px`,
                              height: `${Math.abs(y) + 40}px`,
                              transform: 'translate(-50%, -50%)',
                              pointerEvents: 'none'
                            }}
                          >
                            <line
                              x1={x > 0 ? 0 : Math.abs(x) + 40}
                              y1={y > 0 ? 0 : Math.abs(y) + 40}
                              x2={x > 0 ? Math.abs(x) + 40 : 0}
                              y2={y > 0 ? Math.abs(y) + 40 : 0}
                              className={`transition-all duration-500 ${
                                status === 'completed'
                                  ? 'stroke-emerald-400/70'
                                  : status === 'active'
                                  ? 'stroke-emerald-400/90'
                                  : 'stroke-slate-600/40'
                              }`}
                              strokeWidth="1.5"
                              strokeDasharray="6 6"
                              strokeLinecap="round"
                              style={{
                                filter: status === 'active' ? 'drop-shadow(0 0 6px rgba(16,185,129,0.8))' : 'none'
                              }}
                            >
                              {status === 'active' && (
                                <animate
                                  attributeName="stroke-dashoffset"
                                  from="0"
                                  to="12"
                                  dur="1s"
                                  repeatCount="indefinite"
                                />
                              )}
                            </line>
                          </svg>

                          {/* Animated flow dots on line - flowing from center outward */}
                          {status === 'active' && (
                            <>
                              {[0, 0.33, 0.66].map((delay, i) => (
                                <div
                                  key={i}
                                  className="absolute w-2.5 h-2.5 bg-emerald-400 rounded-full shadow-[0_0_12px_rgba(16,185,129,1)]"
                                  style={{
                                    animation: `flowFromCenter 1.5s ease-in-out infinite`,
                                    animationDelay: `${delay}s`,
                                    left: '50%',
                                    top: '50%',
                                    transformOrigin: 'center',
                                    '--flow-x': `${x}px`,
                                    '--flow-y': `${y}px`,
                                  } as React.CSSProperties}
                                ></div>
                              ))}
                            </>
                          )}

                          {/* Phase Node */}
                          <div className="flex flex-col items-center">
                            <div className={`relative w-14 h-14 rounded-full flex items-center justify-center transition-all duration-500 ${
                              status === 'completed'
                                ? 'bg-slate-900/40 border-2 border-emerald-400 shadow-[0_0_25px_rgba(16,185,129,0.7)]'
                                : status === 'active'
                                ? 'bg-slate-900/40 border-2 border-emerald-400 shadow-[0_0_35px_rgba(16,185,129,0.9)]'
                                : 'bg-slate-900/40 border-2 border-slate-600/50'
                            }`}>
                              {/* Pulsing glow animation for active phase */}
                              {status === 'active' && (
                                <>
                                  <div className="absolute inset-0 bg-emerald-400 rounded-full animate-ping opacity-20"></div>
                                  <div className="absolute -inset-2 bg-gradient-to-br from-emerald-400/30 to-teal-400/30 rounded-full animate-pulse blur-lg"></div>
                                </>
                              )}

                              {/* Solid glow for completed phase */}
                              {status === 'completed' && (
                                <div className="absolute -inset-1 bg-emerald-400/20 rounded-full blur-md"></div>
                              )}

                              <div className="relative z-10">
                                {renderIcon(phase.icon, status)}
                              </div>
                            </div>
                            <span className={`mt-2 text-xs font-medium transition-all duration-300 text-center max-w-[60px] ${
                              status === 'completed' ? 'text-emerald-400 drop-shadow-[0_0_6px_rgba(16,185,129,0.6)]' :
                              status === 'active' ? 'text-emerald-300 drop-shadow-[0_0_8px_rgba(16,185,129,0.8)] font-bold' :
                              'text-slate-500'
                            }`}>
                              {phase.name}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Progress Info - Below the circle */}
                  <div className="mt-4 pt-4 border-t border-slate-700/50 flex items-center justify-between text-sm">
                      <div className="flex items-center gap-4">
                        {/* Last Activity / Start Time */}
                        {currentWorkflow.start_time && (
                          <div className="flex items-center gap-1.5">
                            <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span className="text-slate-300">
                              {currentWorkflow.status === 'running' ? 'Started' : 'Last active'} {formatLastUpdated(currentWorkflow.start_time)}
                            </span>
                          </div>
                        )}
                        {currentWorkflow.duration_seconds !== null && (
                          <div className="flex items-center gap-1.5">
                            <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                            <span className="text-slate-300">{formatDuration(currentWorkflow.duration_seconds)} elapsed</span>
                          </div>
                        )}
                        {currentWorkflow.error_count > 0 && (
                          <div className="flex items-center gap-1.5" title={currentWorkflow.last_error || undefined}>
                            <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            <span className="text-red-400">{currentWorkflow.error_count} error{currentWorkflow.error_count > 1 ? 's' : ''}</span>
                          </div>
                        )}
                        {currentWorkflow.is_process_active && (
                          <div className="flex items-center gap-1.5">
                            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                            <span className="text-green-400 text-xs font-medium">{uiText.adwMonitor.processActive}</span>
                          </div>
                        )}
                      </div>
                      <div className="text-slate-400 flex items-center gap-2">
                        <span>{currentWorkflow.phases_completed.length} / {workflowPhases.length} {uiText.adwMonitor.phasesCompleted}</span>
                        {currentWorkflow.current_phase && (
                          <span className="text-emerald-400">• {currentWorkflow.current_phase}</span>
                        )}
                      </div>
                    </div>
                </div>
              </div>
          </div>
        )}
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgb(30 41 59);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgb(71 85 105);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgb(100 116 139);
        }

        @keyframes flowDot {
          0% {
            left: -4px;
            opacity: 0;
          }
          10% {
            opacity: 1;
          }
          90% {
            opacity: 1;
          }
          100% {
            left: calc(100% + 4px);
            opacity: 0;
          }
        }

        @keyframes flowToCenter {
          0% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.5);
          }
          50% {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1);
          }
          100% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.5);
          }
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(0) translateX(0);
            opacity: 0.3;
          }
          25% {
            opacity: 0.6;
          }
          50% {
            transform: translateY(-20px) translateX(10px);
            opacity: 0.8;
          }
          75% {
            opacity: 0.6;
          }
        }

        @keyframes flowFromCenter {
          0% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.8);
          }
          20% {
            opacity: 1;
          }
          80% {
            opacity: 1;
          }
          100% {
            opacity: 0;
            transform: translate(calc(-50% + var(--flow-x)), calc(-50% + var(--flow-y))) scale(1.2);
          }
        }
      `}</style>
    </div>
  );
}
