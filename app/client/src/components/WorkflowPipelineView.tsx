import { PhaseNode, type PhaseStatus } from './PhaseNode';
import { WorkflowStatusBadge } from './WorkflowStatusBadge';
import { formatDuration, formatCost } from '../utils/formatters';
import type { AdwWorkflowStatus } from '../api/client';
import { useProgressInterpolation } from '../hooks/useProgressInterpolation';

export interface WorkflowPipelineViewProps {
  workflow: AdwWorkflowStatus;
  colors: {
    innerGlow: string;
  };
}

// Workflow phases for the pipeline visualization (9 phases total)
const workflowPhases = [
  { name: 'Plan', icon: 'clipboard', key: 'plan' },
  { name: 'Validate', icon: 'check-circle', key: 'validate' },
  { name: 'Build', icon: 'cube', key: 'build' },
  { name: 'Lint', icon: 'sparkles', key: 'lint' },
  { name: 'Test', icon: 'beaker', key: 'test' },
  { name: 'Review', icon: 'eye', key: 'review' },
  { name: 'Doc', icon: 'document', key: 'doc' },
  { name: 'Ship', icon: 'rocket', key: 'ship' },
  { name: 'Cleanup', icon: 'trash', key: 'cleanup' }
];

/**
 * Get phase status based on workflow state
 */
const getPhaseStatus = (workflow: AdwWorkflowStatus, phaseKey: string): PhaseStatus => {
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

/**
 * WorkflowPipelineView - Complete workflow visualization with pipeline, phases, and metadata
 */
export function WorkflowPipelineView({ workflow, colors }: WorkflowPipelineViewProps) {
  // Smooth progress interpolation for phase completion percentage
  const completedPhasesCount = workflow.phases_completed.length;
  const interpolatedPhaseCount = useProgressInterpolation(completedPhasesCount);

  return (
    <div
      className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl border border-slate-700/50 shadow-[0_0_15px_rgba(16,185,129,0.1)] overflow-hidden relative"
      role="region"
      aria-label="Workflow Pipeline Visualization"
    >
      {/* Subtle inner glow */}
      <div className={`absolute inset-0 bg-gradient-to-br ${colors.innerGlow} to-transparent pointer-events-none`}></div>
        {/* Header */}
        <div className="px-4 py-3 border-b border-slate-700/50 flex items-center justify-between relative z-10">
          <div className="flex items-center gap-3">
            {workflow.github_url ? (
              <div className="flex items-center gap-2">
                <a
                  href={workflow.github_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-emerald-400 hover:text-emerald-300 font-mono text-lg font-bold transition-colors"
                >
                  #{workflow.issue_number}
                </a>
                {workflow.pr_number && (
                  <>
                    <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <a
                      href={`https://github.com/${new URL(workflow.github_url).pathname.split('/').slice(1, 3).join('/')}/pull/${workflow.pr_number}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-400 hover:text-purple-300 font-mono text-sm font-bold transition-colors flex items-center gap-1"
                      title="Pull Request"
                    >
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 16 16">
                        <path fillRule="evenodd" d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z" />
                      </svg>
                      PR #{workflow.pr_number}
                    </a>
                  </>
                )}
              </div>
            ) : (
              <span className="text-slate-500 font-mono text-lg font-bold">
                {workflow.adw_id.substring(0, 8)}
              </span>
            )}
            <div>
              <h3 className="text-white font-semibold text-base leading-tight">
                {workflow.workflow_template === 'adw_plan_iso' && 'Planning Phase' ||
                 workflow.workflow_template === 'adw_sdlc_complete_iso' && 'Full SDLC' ||
                 workflow.workflow_template === 'adw_sdlc_iso' && 'Standard SDLC' ||
                 `Workflow ${workflow.adw_id.substring(0, 8)}`}
              </h3>
              <div className="flex items-center gap-2 mt-1">
                <span className="px-2 py-0.5 bg-blue-500/20 text-blue-300 text-xs rounded-md font-medium">
                  {workflow.workflow_template.replace('adw_', '').replace('_', ' ')}
                </span>
                {workflow.issue_class && (
                  <span className="px-2 py-0.5 bg-slate-700/50 text-slate-300 text-xs rounded-md font-medium">
                    {workflow.issue_class}
                  </span>
                )}
                <WorkflowStatusBadge status={workflow.status} />
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-white font-bold text-lg">
              {formatCost(workflow.current_cost)}
            </div>
            {workflow.estimated_cost_total && (
              <div className="text-slate-400 text-xs">
                of {formatCost(workflow.estimated_cost_total)}
              </div>
            )}
          </div>
        </div>

        {/* Animated Pipeline Visualization - VoltAgent Style */}
        <div className="px-4 py-6 relative z-10" role="list" aria-label="Workflow phases">
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
            {workflowPhases.map((phase, idx) => {
              const status = getPhaseStatus(workflow, phase.key);
              const totalPhases = workflowPhases.length;
              const angle = (idx * 360) / totalPhases - 90; // Start from top
              const radius = 110; // Distance from center
              const x = Math.cos((angle * Math.PI) / 180) * radius;
              const y = Math.sin((angle * Math.PI) / 180) * radius;

              return (
                <PhaseNode
                  key={phase.key}
                  name={phase.name}
                  icon={phase.icon}
                  status={status}
                  x={x}
                  y={y}
                />
              );
            })}
          </div>

          {/* Progress Info - Below the circle */}
          <div className="mt-4 pt-4 border-t border-slate-700/50 flex items-center justify-between text-sm" role="status" aria-live="polite">
              <div className="flex items-center gap-4">
                {workflow.duration_seconds !== null && (
                  <div className="flex items-center gap-1.5" aria-label={`Workflow duration: ${formatDuration(workflow.duration_seconds)}`}>
                    <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-slate-300">{formatDuration(workflow.duration_seconds)}</span>
                  </div>
                )}
                {workflow.error_count > 0 && (
                  <div className="flex items-center gap-1.5" title={workflow.last_error || undefined} aria-label={`${workflow.error_count} error${workflow.error_count > 1 ? 's' : ''} occurred`}>
                    <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <span className="text-red-400">{workflow.error_count} error{workflow.error_count > 1 ? 's' : ''}</span>
                  </div>
                )}
                {workflow.is_process_active && (
                  <div className="flex items-center gap-1.5" aria-label="Workflow process is currently active">
                    <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                    <span className="text-green-400 text-xs font-medium">Process Active</span>
                  </div>
                )}
              </div>
              <div className="text-slate-400 flex items-center gap-2" aria-label={`${Math.round(interpolatedPhaseCount)} of ${workflowPhases.length} phases completed. Current phase: ${workflow.current_phase || 'None'}`}>
                <span>{Math.round(interpolatedPhaseCount)} / {workflowPhases.length} phases completed</span>
                {workflow.current_phase && (
                  <span className="text-emerald-400">• {workflow.current_phase}</span>
                )}
              </div>
            </div>
        </div>
      </div>
  );
}
