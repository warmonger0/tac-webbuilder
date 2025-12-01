/**
 * WorkflowProgressVisualization Component
 *
 * Displays an animated workflow progress visualization showing:
 * - Ingestion → Preflight → Workflow Steps
 * - Step status with color-coded animations:
 *   - Normal: Pulsing green when active, static green when completed
 *   - Stuck: Glowing purple when a step is taking too long
 *   - Error/Hung: Glowing red when workflow errors or hangs (>20 min)
 */

import { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle, Loader2, XCircle } from 'lucide-react';

interface WorkflowStep {
  id: string;
  label: string;
  phase: string;
}

interface WorkflowProgressVisualizationProps {
  currentPhase?: string | null;
  phaseProgress?: number;
  startTime?: string | null;
  endTime?: string | null;
  status?: string;
  errorCount?: number;
  lastError?: string | null;
}

const WORKFLOW_STEPS: WorkflowStep[] = [
  { id: 'ingestion', label: 'Ingestion', phase: 'ingestion' },
  { id: 'preflight', label: 'Preflight', phase: 'preflight' },
  { id: 'plan', label: 'Plan', phase: 'plan' },
  { id: 'validate', label: 'Validate', phase: 'validate' },
  { id: 'build', label: 'Build', phase: 'build' },
  { id: 'lint', label: 'Lint', phase: 'lint' },
  { id: 'test', label: 'Test', phase: 'test' },
  { id: 'review', label: 'Review', phase: 'review' },
  { id: 'doc', label: 'Doc', phase: 'doc' },
  { id: 'ship', label: 'Ship', phase: 'ship' },
];

// Time thresholds (in milliseconds)
const STUCK_THRESHOLD = 10 * 60 * 1000; // 10 minutes
const HUNG_THRESHOLD = 20 * 60 * 1000; // 20 minutes

type StepStatus = 'pending' | 'active' | 'completed' | 'stuck' | 'error' | 'hung';

function getStepStatus(
  step: WorkflowStep,
  currentPhase: string | null | undefined,
  _phaseProgress: number,
  startTime: string | null | undefined,
  endTime: string | null | undefined,
  status: string | undefined,
  errorCount: number | undefined,
  _lastError: string | null | undefined,
): StepStatus {
  // If workflow has ended with error or has errors
  if (status === 'failed' || (errorCount && errorCount > 0)) {
    const currentStepIndex = WORKFLOW_STEPS.findIndex((s) => s.phase === currentPhase);
    const stepIndex = WORKFLOW_STEPS.findIndex((s) => s.id === step.id);

    // Error on current or later steps
    if (stepIndex >= currentStepIndex) {
      return 'error';
    }
  }

  // Check if workflow is hung (>20 minutes on same step)
  if (startTime && !endTime && currentPhase === step.phase) {
    const elapsed = Date.now() - new Date(startTime).getTime();
    if (elapsed > HUNG_THRESHOLD) {
      return 'hung';
    }
    if (elapsed > STUCK_THRESHOLD) {
      return 'stuck';
    }
  }

  // Normal status flow
  if (!currentPhase) {
    return 'pending';
  }

  const currentStepIndex = WORKFLOW_STEPS.findIndex((s) => s.phase === currentPhase);
  const stepIndex = WORKFLOW_STEPS.findIndex((s) => s.id === step.id);

  if (stepIndex < currentStepIndex) {
    return 'completed';
  } else if (stepIndex === currentStepIndex) {
    return 'active';
  } else {
    return 'pending';
  }
}

function StepIcon({ status }: { status: StepStatus }) {
  const baseClasses = 'w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300';

  switch (status) {
    case 'completed':
      return (
        <div className={`${baseClasses} bg-green-500 shadow-lg`}>
          <CheckCircle className="w-5 h-5 text-white" />
        </div>
      );

    case 'active':
      return (
        <div className={`${baseClasses} bg-green-500 shadow-lg animate-pulse`}>
          <Loader2 className="w-5 h-5 text-white animate-spin" />
        </div>
      );

    case 'stuck':
      return (
        <div className={`${baseClasses} bg-purple-500 shadow-lg shadow-purple-500/50 animate-pulse-glow-purple`}>
          <AlertTriangle className="w-5 h-5 text-white" />
        </div>
      );

    case 'error':
    case 'hung':
      return (
        <div className={`${baseClasses} bg-red-500 shadow-lg shadow-red-500/50 animate-pulse-glow-red`}>
          <XCircle className="w-5 h-5 text-white" />
        </div>
      );

    case 'pending':
    default:
      return (
        <div className={`${baseClasses} bg-gray-300 border-2 border-gray-400`}>
          <div className="w-3 h-3 rounded-full bg-gray-500" />
        </div>
      );
  }
}

function ConnectingLine({
  status,
  animated
}: {
  status: 'completed' | 'active' | 'pending' | 'error';
  animated?: boolean;
}) {
  let colorClass = 'bg-gray-300';
  let animationClass = '';

  switch (status) {
    case 'completed':
      colorClass = 'bg-green-500';
      break;
    case 'active':
      colorClass = 'bg-green-500';
      animationClass = animated ? 'animate-flow-line' : '';
      break;
    case 'error':
      colorClass = 'bg-red-500';
      break;
    case 'pending':
    default:
      colorClass = 'bg-gray-300';
  }

  return (
    <div className="flex-1 h-1 mx-2 relative overflow-hidden rounded">
      <div className={`absolute inset-0 ${colorClass} ${animationClass}`} />
    </div>
  );
}

export function WorkflowProgressVisualization({
  currentPhase,
  phaseProgress = 0,
  startTime,
  endTime,
  status,
  errorCount,
  lastError,
}: WorkflowProgressVisualizationProps) {
  const [, setTick] = useState(0);

  // Force re-render every second to update stuck/hung detection
  useEffect(() => {
    const interval = setInterval(() => {
      setTick((t) => t + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Calculate elapsed time
  const elapsedTime = startTime && !endTime
    ? Math.floor((Date.now() - new Date(startTime).getTime()) / 1000)
    : null;

  return (
    <div className="space-y-4">
      {/* Timeline visualization */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-semibold text-gray-700">Workflow Progress</h4>
          {elapsedTime !== null && (
            <span className="text-xs text-gray-500">
              {Math.floor(elapsedTime / 60)}m {elapsedTime % 60}s
            </span>
          )}
        </div>

        <div className="space-y-3">
          {WORKFLOW_STEPS.map((step, index) => {
            const stepStatus = getStepStatus(
              step,
              currentPhase,
              phaseProgress,
              startTime,
              endTime,
              status,
              errorCount,
              lastError,
            );

            const lineStatus =
              stepStatus === 'completed' ? 'completed' :
              stepStatus === 'active' ? 'active' :
              stepStatus === 'error' || stepStatus === 'hung' ? 'error' :
              'pending';

            return (
              <div key={step.id}>
                <div className="flex items-center">
                  <StepIcon status={stepStatus} />
                  <span
                    className={`ml-3 text-sm font-medium transition-colors duration-300 ${
                      stepStatus === 'completed'
                        ? 'text-green-700'
                        : stepStatus === 'active'
                        ? 'text-green-600 font-semibold'
                        : stepStatus === 'stuck'
                        ? 'text-purple-600 font-semibold'
                        : stepStatus === 'error' || stepStatus === 'hung'
                        ? 'text-red-600 font-semibold'
                        : 'text-gray-500'
                    }`}
                  >
                    {step.label}
                    {stepStatus === 'stuck' && ' (Stuck)'}
                    {stepStatus === 'hung' && ' (Hung)'}
                  </span>
                </div>
                {index < WORKFLOW_STEPS.length - 1 && (
                  <div className="ml-4 flex items-center h-4">
                    <ConnectingLine
                      status={lineStatus}
                      animated={stepStatus === 'active'}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Error message if present */}
      {lastError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h5 className="text-sm font-semibold text-red-900 mb-1">Last Error</h5>
              <p className="text-xs text-red-700">{lastError}</p>
            </div>
          </div>
        </div>
      )}

      {/* Status indicators legend */}
      <div className="flex items-center gap-4 text-xs text-gray-600">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span>Active/Completed</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-purple-500 animate-pulse" />
          <span>Stuck (&gt;10m)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse" />
          <span>Error/Hung (&gt;20m)</span>
        </div>
      </div>
    </div>
  );
}
