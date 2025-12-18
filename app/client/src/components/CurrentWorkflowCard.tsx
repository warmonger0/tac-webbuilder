import { useMemo, useState } from 'react';
import type { AdwWorkflowStatus } from '../api/client';
import { phaseSvgIconMap, workflowPhases } from '../config/workflows';
import { useGlobalWebSocket } from '../contexts/GlobalWebSocketContext';
import { resumeAdw } from '../api/client';

export function CurrentWorkflowCard() {
  // Use shared WebSocket context for real-time updates
  const { adwMonitorData, adwConnectionState } = useGlobalWebSocket();
  const { workflows } = adwMonitorData;
  const { isConnected } = adwConnectionState; // Used for connection indicator in UI

  // State for resume button
  const [resumeLoading, setResumeLoading] = useState(false);
  const [resumeError, setResumeError] = useState<string | null>(null);
  const [resumeSuccess, setResumeSuccess] = useState<string | null>(null);

  // Select current workflow (prioritize running > paused) - ONLY show active workflows
  const workflow = useMemo(() => {
    if (!workflows.length) return null;
    // Only return workflows that are actively in progress (running or paused)
    // Never show failed or completed workflows
    return workflows.find(w => w.status === 'running')
      || workflows.find(w => w.status === 'paused')
      || null; // Show "No Active Workflow" if only failed/completed workflows exist
  }, [workflows]);

  // Don't block on WebSocket connection - show empty state immediately
  const loading = false; // WebSocket will update asynchronously

  // Handle resume workflow
  const handleResumeWorkflow = async () => {
    if (!workflow?.adw_id) return;

    setResumeLoading(true);
    setResumeError(null);
    setResumeSuccess(null);

    try {
      const result = await resumeAdw(workflow.adw_id);
      setResumeSuccess(result.message);
      // Clear success message after 5 seconds
      setTimeout(() => setResumeSuccess(null), 5000);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to resume workflow';
      setResumeError(errorMessage);
      // Clear error message after 10 seconds
      setTimeout(() => setResumeError(null), 10000);
    } finally {
      setResumeLoading(false);
    }
  };

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

  const getPhaseStatus = (workflow: AdwWorkflowStatus | null, phaseKey: string) => {
    if (!workflow) return 'pending';
    const lowerPhase = phaseKey.toLowerCase();
    const currentPhase = workflow.current_phase?.toLowerCase() || '';

    if (workflow.phases_completed.some(p => p.toLowerCase().includes(lowerPhase))) {
      return 'completed';
    }
    if (currentPhase.includes(lowerPhase)) {
      return 'active';
    }
    return 'pending';
  };

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg border border-slate-700 p-8 flex items-center justify-center min-h-[400px]">
        <div className="text-slate-400">Loading workflow...</div>
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg border border-slate-700 p-8 flex flex-col items-center justify-center min-h-[400px]">
        <div className="w-16 h-16 mb-4 bg-slate-700/50 rounded-full flex items-center justify-center">
          <svg className="w-8 h-8 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <p className="text-slate-400 text-lg font-medium">No Active Workflow</p>
        <p className="text-slate-500 text-sm mt-1">Start a workflow to see real-time progress</p>
      </div>
    );
  }

  const phasesWithIcons = workflowPhases.map(phase => ({
    name: phase.name,
    icon: phaseSvgIconMap[phase.phase] || 'clipboard',
    key: phase.phase
  }));

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg border border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-700/50 bg-slate-900/50">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-amber-600 rounded-lg flex items-center justify-center shadow-lg">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h3 className="text-white font-bold text-base">Current Workflow</h3>
              <p className="text-slate-400 text-xs">Real-time progress</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative w-2 h-2">
              <div className={`absolute w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-yellow-500'}`}></div>
              {isConnected && <div className="absolute w-2 h-2 bg-emerald-500 rounded-full animate-ping"></div>}
            </div>
            <span className={`text-xs font-medium ${isConnected ? 'text-emerald-400' : 'text-yellow-400'}`}>
              {isConnected ? 'Live' : 'Reconnecting...'}
            </span>
            <span className="text-slate-500 text-xs">
              {isConnected ? 'Real-time' : 'Waiting'}
            </span>
          </div>
        </div>

        {/* Workflow Info Bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-emerald-400 font-bold text-lg">#{workflow.issue_number}</div>
            <div>
              <h4 className="text-white font-semibold text-sm">{workflow.workflow_template}</h4>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-slate-400 text-xs">{workflow.issue_class || '/chore'}</span>
                <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                  workflow.status === 'running' ? 'bg-emerald-500/20 text-emerald-300' :
                  workflow.status === 'paused' ? 'bg-yellow-500/20 text-yellow-300' :
                  workflow.status === 'completed' ? 'bg-blue-500/20 text-blue-300' :
                  workflow.status === 'failed' ? 'bg-red-500/20 text-red-300' :
                  'bg-slate-700 text-slate-400'
                }`}>
                  {workflow.status.toUpperCase()}
                </span>
              </div>
            </div>
          </div>
          <div className="text-slate-300 font-bold text-lg">
            ${(workflow.current_cost || workflow.estimated_cost_total || 0).toFixed(2)}
          </div>
        </div>

        {/* Resume Button Section (only for paused workflows) */}
        {workflow.status === 'paused' && (
          <div className="mt-3 pt-3 border-t border-slate-700/50">
            <div className="flex items-center gap-3">
              <button
                onClick={handleResumeWorkflow}
                disabled={resumeLoading}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg hover:from-emerald-700 hover:to-teal-700 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed transition-all shadow-lg text-sm font-medium"
              >
                {resumeLoading ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Running Preflight Checks...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Resume Workflow
                  </>
                )}
              </button>
              {resumeSuccess && (
                <div className="flex items-center gap-2 text-emerald-400 text-sm">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {resumeSuccess}
                </div>
              )}
              {resumeError && (
                <div className="flex items-center gap-2 text-red-400 text-sm">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  {resumeError}
                </div>
              )}
            </div>
            <p className="mt-2 text-xs text-slate-400">
              Workflow is paused. Click Resume to run preflight checks and continue to the next phase.
            </p>
          </div>
        )}
      </div>

      {/* Circular Visualization with W Logo */}
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

          {/* Central Hub with W Logo */}
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

                {/* Top arc */}
                <path
                  d="M10,47 L13,45 L16,46 L20,44 L24,45 L28,43 L32,44 L37,42 L42,43 L47,42 L52,43 L57,42 L62,43 L67,42 L72,44 L76,43 L80,45 L84,44 L87,46 L90,47"
                  fill="none"
                  stroke="rgba(16,185,129,0.9)"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  filter="url(#lightningGlow)"
                  opacity="0"
                >
                  <animate attributeName="opacity" values="0;0;0.9;0.7;0.9;0.5;0.8;0;0" dur="1.5s" begin="0s" repeatCount="indefinite" />
                </path>

                {/* Bottom arc */}
                <path
                  d="M90,53 L87,55 L84,54 L80,56 L76,55 L72,57 L67,56 L62,58 L57,57 L52,58 L47,57 L42,58 L37,57 L32,58 L28,56 L24,57 L20,55 L16,56 L13,54 L10,53"
                  fill="none"
                  stroke="rgba(16,185,129,0.9)"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  filter="url(#lightningGlow)"
                  opacity="0"
                >
                  <animate attributeName="opacity" values="0;0;0.8;0.6;0.9;0.6;0.7;0;0" dur="1.5s" begin="0.3s" repeatCount="indefinite" />
                </path>

                {/* Sparks */}
                {[20, 35, 50, 65, 80].map((x, i) => (
                  <circle
                    key={`spark-${i}`}
                    cx={x}
                    cy={i % 2 === 0 ? 44 : 56}
                    r="0.5"
                    fill="rgba(16,185,129,1)"
                    filter="url(#lightningGlow)"
                    opacity="0"
                  >
                    <animate attributeName="opacity" values="0;1;0" dur="0.5s" begin={`${0.1 + i * 0.15}s`} repeatCount="indefinite" />
                    <animate attributeName="r" values="0.5;1;0.5" dur="0.5s" begin={`${0.1 + i * 0.15}s`} repeatCount="indefinite" />
                  </circle>
                ))}
              </svg>

              {/* Stylized "W" outline */}
              <svg className="w-8 h-8 text-white relative z-10 animate-pulse" viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10,20 L25,80 L40,35 L50,55 L60,35 L75,80 L90,20"
                  className="drop-shadow-[0_0_10px_rgba(255,255,255,0.9)]"
                  style={{
                    filter: 'drop-shadow(0 0 8px rgba(16,185,129,0.8))'
                  }}
                />
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
            const status = getPhaseStatus(workflow, phase.key);
            const totalPhases = phasesWithIcons.length;
            const angle = (idx * 360) / totalPhases - 90;
            const radius = 110;
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
                {/* Phase Node */}
                <div className="flex flex-col items-center">
                  <div className={`relative w-14 h-14 rounded-full flex items-center justify-center transition-all duration-500 ${
                    status === 'completed'
                      ? 'bg-slate-900/40 border-2 border-emerald-400 shadow-[0_0_25px_rgba(16,185,129,0.7)]'
                      : status === 'active'
                      ? 'bg-slate-900/40 border-2 border-emerald-400 shadow-[0_0_35px_rgba(16,185,129,0.9)]'
                      : 'bg-slate-900/40 border-2 border-slate-600/50'
                  }`}>
                    {status === 'active' && (
                      <>
                        <div className="absolute inset-0 bg-emerald-400 rounded-full animate-ping opacity-20"></div>
                        <div className="absolute -inset-2 bg-gradient-to-br from-emerald-400/30 to-teal-400/30 rounded-full animate-pulse blur-lg"></div>
                      </>
                    )}
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

        {/* Progress Footer */}
        <div className="mt-4 pt-4 border-t border-slate-700/50 flex items-center justify-center gap-2 text-sm">
          <span className="text-slate-400">{workflow.phases_completed.length} / {workflow.total_phases} phases completed</span>
          {workflow.current_phase && (
            <>
              <span className="text-slate-600">•</span>
              <span className="text-emerald-400 font-medium">{workflow.current_phase}</span>
            </>
          )}
        </div>
      </div>

      <style>{`
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
      `}</style>
    </div>
  );
}
