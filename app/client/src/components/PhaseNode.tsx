import { useState } from 'react';

export type PhaseStatus = 'pending' | 'active' | 'completed';

export interface PhaseNodeProps {
  name: string;
  icon: string;
  status: PhaseStatus;
  x: number;
  y: number;
}

/**
 * Icon rendering helper for phase nodes
 */
const renderIcon = (iconName: string, status: PhaseStatus = 'pending') => {
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

/**
 * PhaseNode component - Renders a single phase node in the workflow pipeline visualization
 */
// eslint-disable-next-line max-lines-per-function, complexity
export function PhaseNode({ name, icon, status, x, y }: PhaseNodeProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      setIsExpanded(!isExpanded);
    }
  };

  const getStatusLabel = () => {
    switch (status) {
      case 'completed':
        return 'completed';
      case 'active':
        return 'in progress';
      case 'pending':
        return 'pending';
      default:
        return status;
    }
  };

  return (
    <div
      className="absolute"
      style={{
        left: '50%',
        top: '50%',
        transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`
      }}
      role="listitem"
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
        <div
          className={`relative w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 ease-in-out ${
            status === 'completed'
              ? 'bg-slate-900/40 border-2 border-emerald-400 shadow-[0_0_25px_rgba(16,185,129,0.7)] scale-100'
              : status === 'active'
              ? 'bg-slate-900/40 border-2 border-emerald-400 shadow-[0_0_35px_rgba(16,185,129,0.9)] scale-110'
              : 'bg-slate-900/40 border-2 border-slate-600/50 scale-100'
          } focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:outline-none cursor-pointer`}
          role="button"
          tabIndex={0}
          aria-label={`${name} phase, status: ${getStatusLabel()}`}
          aria-expanded={isExpanded}
          aria-current={status === 'active' ? 'step' : undefined}
          onKeyDown={handleKeyDown}
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {/* Pulsing glow animation for active phase */}
          {status === 'active' && (
            <>
              <div className="absolute inset-0 bg-emerald-400 rounded-full animate-ping opacity-20 transition-opacity duration-300"></div>
              <div className="absolute -inset-2 bg-gradient-to-br from-emerald-400/30 to-teal-400/30 rounded-full animate-pulse blur-lg transition-opacity duration-300"></div>
            </>
          )}

          {/* Solid glow for completed phase */}
          {status === 'completed' && (
            <div className="absolute -inset-1 bg-emerald-400/20 rounded-full blur-md transition-opacity duration-300"></div>
          )}

          <div className="relative z-10">
            {renderIcon(icon, status)}
          </div>
        </div>
        <span className={`mt-2 text-xs font-medium transition-all duration-300 text-center max-w-[60px] ${
          status === 'completed' ? 'text-emerald-400 drop-shadow-[0_0_6px_rgba(16,185,129,0.6)]' :
          status === 'active' ? 'text-emerald-300 drop-shadow-[0_0_8px_rgba(16,185,129,0.8)] font-bold' :
          'text-slate-500'
        }`}>
          {name}
        </span>
      </div>
    </div>
  );
}
