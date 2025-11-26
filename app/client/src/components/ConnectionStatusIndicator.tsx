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
  const maxReconnectAttempts = 10; // Match the value from AdwMonitorCard

  const getStatusConfig = () => {
    // Special case: Show "Reconnecting..." when actively retrying
    if (connectionQuality === 'poor' && reconnectAttempts > 0) {
      return {
        color: 'bg-orange-500',
        textColor: 'text-orange-600',
        label: `Reconnecting... (${reconnectAttempts}/${maxReconnectAttempts})`,
        icon: '◐',
        animate: true,
        tooltip: 'Connection lost. Automatically retrying with exponential backoff.',
      };
    }

    // Special case: Polling mode after max reconnect attempts
    if (connectionQuality === 'disconnected' && reconnectAttempts >= maxReconnectAttempts) {
      return {
        color: 'bg-yellow-500',
        textColor: 'text-yellow-600',
        label: 'Polling Mode',
        icon: '⟳',
        animate: false,
        tooltip: 'WebSocket connection failed. Using HTTP polling for updates (slower).',
      };
    }

    switch (connectionQuality) {
      case 'excellent':
        return {
          color: 'bg-green-500',
          textColor: 'text-green-600',
          label: 'Live',
          icon: '●',
          animate: true,
          tooltip: 'WebSocket connected. Real-time updates active.',
        };
      case 'good':
        return {
          color: 'bg-blue-500',
          textColor: 'text-blue-600',
          label: 'Connected',
          icon: '●',
          animate: true,
          tooltip: 'WebSocket connected. Updates are flowing normally.',
        };
      case 'poor':
        return {
          color: 'bg-yellow-500',
          textColor: 'text-yellow-600',
          label: 'Slow',
          icon: '●',
          animate: false,
          tooltip: 'Connection is degraded. Updates may be delayed.',
        };
      case 'disconnected':
        return {
          color: 'bg-red-500',
          textColor: 'text-red-600',
          label: 'Offline',
          icon: '○',
          animate: false,
          tooltip: 'Not connected to server. Will retry automatically.',
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
      <div
        className="flex items-center gap-2"
        role="status"
        aria-label={`Connection status: ${config.label}. ${config.tooltip}${lastUpdated ? ` Last updated ${formatLastUpdated()}.` : ''}`}
        title={config.tooltip}
      >
        <div
          className={`w-2 h-2 rounded-full ${config.color} ${
            config.animate ? 'animate-pulse' : ''
          }`}
          aria-hidden="true"
        />
        <span className={`text-xs ${config.textColor}`}>{config.label}</span>
        {lastUpdated && (
          <span className="text-xs text-gray-500">{formatLastUpdated()}</span>
        )}
      </div>
    );
  }

  return (
    <div
      className="flex flex-col gap-2 p-3 bg-gray-50 rounded-lg border border-gray-200"
      role="status"
      aria-label={`Connection status: ${config.label}. ${config.tooltip}`}
      title={config.tooltip}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className={`w-3 h-3 rounded-full ${config.color} ${
              config.animate ? 'animate-pulse' : ''
            }`}
            aria-hidden="true"
          />
          <span className={`text-sm font-medium ${config.textColor}`}>
            {config.label}
          </span>
        </div>
        {onRetry && connectionQuality === 'disconnected' && (
          <button
            onClick={onRetry}
            className="px-2 py-1 text-xs font-medium text-white bg-blue-500 hover:bg-blue-600 rounded transition-colors focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none"
            aria-label="Retry connection"
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

      {/* Show detailed status message */}
      {connectionQuality === 'disconnected' && reconnectAttempts >= maxReconnectAttempts && (
        <div className="mt-1 text-xs text-yellow-600">
          Polling mode active. Updates via HTTP every 10s.
        </div>
      )}

      {connectionQuality === 'disconnected' && reconnectAttempts < maxReconnectAttempts && (
        <div className="mt-1 text-xs text-red-600">
          Connection lost. Retrying automatically...
        </div>
      )}

      {connectionQuality === 'poor' && reconnectAttempts > 0 && (
        <div className="mt-1 text-xs text-orange-600">
          Reconnecting with exponential backoff...
        </div>
      )}

      {connectionQuality === 'poor' && reconnectAttempts === 0 && (
        <div className="mt-1 text-xs text-yellow-600">
          Connection is slow. Updates may be delayed.
        </div>
      )}
    </div>
  );
}
