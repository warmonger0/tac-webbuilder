export interface WorkflowStatusBadgeProps {
  status: string;
  size?: 'small' | 'medium' | 'large';
}

/**
 * WorkflowStatusBadge - Renders a status badge with appropriate styling
 */
export function WorkflowStatusBadge({ status, size = 'medium' }: WorkflowStatusBadgeProps) {
  const sizeClasses = {
    small: 'px-1.5 py-0.5 text-xs',
    medium: 'px-2 py-0.5 text-xs',
    large: 'px-3 py-1 text-sm'
  };

  const dotSizeClasses = {
    small: 'w-1 h-1',
    medium: 'w-1.5 h-1.5',
    large: 'w-2 h-2'
  };

  const getStatusLabel = () => {
    switch (status) {
      case 'running':
        return 'Workflow is currently running';
      case 'completed':
        return 'Workflow has completed successfully';
      case 'failed':
        return 'Workflow has failed';
      case 'paused':
        return 'Workflow is paused';
      default:
        return `Workflow status: ${status}`;
    }
  };

  return (
    <div
      className={`flex items-center gap-1.5 rounded-md font-medium transition-all duration-200 ease-in-out ${sizeClasses[size]} ${
        status === 'running' ? 'bg-emerald-500/20 text-emerald-300' :
        status === 'completed' ? 'bg-green-500/20 text-green-300' :
        status === 'failed' ? 'bg-red-500/20 text-red-300' :
        status === 'paused' ? 'bg-yellow-500/20 text-yellow-300' :
        'bg-slate-500/20 text-slate-300'
      }`}
      role="status"
      aria-label={getStatusLabel()}
    >
      <span
        className={`${dotSizeClasses[size]} rounded-full transition-all duration-200 ease-in-out ${
          status === 'running' ? 'bg-emerald-400 animate-pulse' :
          status === 'completed' ? 'bg-green-400' :
          status === 'failed' ? 'bg-red-400' :
          status === 'paused' ? 'bg-yellow-400' :
          'bg-slate-400'
        }`}
        aria-hidden="true"
      ></span>
      {status.toUpperCase()}
    </div>
  );
}
