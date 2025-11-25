interface ConnectionStatusIndicatorProps {
  isConnected: boolean;
  connectionQuality: 'excellent' | 'good' | 'poor' | 'disconnected';
  lastUpdated: Date | null;
  reconnectAttempts?: number;
  consecutiveErrors?: number;
  onRetry?: () => void;
  variant?: 'compact' | 'detailed';
}

export function ConnectionStatusIndicator({
  connectionQuality,
  lastUpdated,
  reconnectAttempts = 0,
  consecutiveErrors = 0,
  onRetry,
  variant = 'compact',
}: ConnectionStatusIndicatorProps) {
  const getStatusConfig = () => {
    switch (connectionQuality) {
      case 'excellent':
        return {
          color: 'bg-green-500',
          textColor: 'text-green-600',
          label: 'Live',
          icon: '●',
          animate: true,
        };
      case 'good':
        return {
          color: 'bg-blue-500',
          textColor: 'text-blue-600',
          label: 'Connected',
          icon: '●',
          animate: true,
        };
      case 'poor':
        return {
          color: 'bg-yellow-500',
          textColor: 'text-yellow-600',
          label: 'Slow',
          icon: '●',
          animate: false,
        };
      case 'disconnected':
        return {
          color: 'bg-red-500',
          textColor: 'text-red-600',
          label: 'Offline',
          icon: '○',
          animate: false,
        };
    }
  };

  const config = getStatusConfig();

  const formatLastUpdated = () => {
    if (!lastUpdated) return 'Never';

    const now = new Date();
    const diffSeconds = Math.floor((now.getTime() - lastUpdated.getTime()) / 1000);

    if (diffSeconds < 5) return 'Just now';
    if (diffSeconds < 60) return `${diffSeconds}s ago`;
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;
    return lastUpdated.toLocaleTimeString();
  };

  if (variant === 'compact') {
    return (
      <div className="flex items-center gap-2">
        <div
          className={`w-2 h-2 rounded-full ${config.color} ${
            config.animate ? 'animate-pulse' : ''
          }`}
          title={`Connection: ${config.label}`}
        />
        <span className="text-xs text-gray-600">{config.label}</span>
        {lastUpdated && (
          <span className="text-xs text-gray-500">{formatLastUpdated()}</span>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className={`w-3 h-3 rounded-full ${config.color} ${
              config.animate ? 'animate-pulse' : ''
            }`}
          />
          <span className={`text-sm font-medium ${config.textColor}`}>
            {config.label}
          </span>
        </div>
        {onRetry && connectionQuality === 'disconnected' && (
          <button
            onClick={onRetry}
            className="px-2 py-1 text-xs font-medium text-white bg-blue-500 hover:bg-blue-600 rounded transition-colors"
          >
            Retry
          </button>
        )}
      </div>

      <div className="flex items-center justify-between text-xs text-gray-600">
        <span>Last update: {formatLastUpdated()}</span>
        {(reconnectAttempts > 0 || consecutiveErrors > 0) && (
          <span className="text-orange-600">
            {reconnectAttempts > 0 ? `Reconnect attempts: ${reconnectAttempts}` : `Errors: ${consecutiveErrors}`}
          </span>
        )}
      </div>

      {connectionQuality === 'disconnected' && (
        <div className="mt-1 text-xs text-red-600">
          Connection lost. Retrying automatically...
        </div>
      )}

      {connectionQuality === 'poor' && (
        <div className="mt-1 text-xs text-yellow-600">
          Connection is slow. Updates may be delayed.
        </div>
      )}
    </div>
  );
}
