interface PhaseDurationChartProps {
  phaseDurations: Record<string, number>; // {phase: seconds}
}

export function PhaseDurationChart({ phaseDurations }: PhaseDurationChartProps) {
  if (!phaseDurations || Object.keys(phaseDurations).length === 0) {
    return null;
  }

  // Calculate max duration for scaling
  const maxDuration = Math.max(...Object.values(phaseDurations));
  const totalDuration = Object.values(phaseDurations).reduce((sum, dur) => sum + dur, 0);

  // Helper to format duration
  const formatDuration = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds}s`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
    }
  };

  // Helper to determine bar color based on duration relative to max
  const getBarColor = (duration: number): string => {
    const percentage = duration / maxDuration;

    if (percentage > 0.60) {
      return "bg-red-500"; // Slow (>60% of max)
    } else if (percentage > 0.30) {
      return "bg-yellow-500"; // Medium (30-60% of max)
    } else {
      return "bg-green-500"; // Fast (<30% of max)
    }
  };

  return (
    <div className="space-y-3">
      {Object.entries(phaseDurations).map(([phase, duration]) => {
        const percentage = totalDuration > 0 ? (duration / totalDuration) * 100 : 0;
        const barWidth = maxDuration > 0 ? (duration / maxDuration) * 100 : 0;
        const colorClass = getBarColor(duration);

        return (
          <div key={phase} className="space-y-1">
            <div className="flex justify-between items-center text-sm">
              <span className="font-medium text-gray-700 capitalize">{phase}</span>
              <span className="text-gray-600">
                {formatDuration(duration)} ({percentage.toFixed(1)}%)
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-6 overflow-hidden">
              <div
                className={`h-6 rounded-full transition-all duration-300 ${colorClass}`}
                style={{ width: `${barWidth}%` }}
              />
            </div>
          </div>
        );
      })}
      <div className="pt-2 border-t border-gray-200 text-sm text-gray-600">
        <div className="flex justify-between">
          <span>Total Duration:</span>
          <span className="font-medium">{formatDuration(totalDuration)}</span>
        </div>
      </div>
    </div>
  );
}
