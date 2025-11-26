/**
 * LoadingSkeleton - Loading state component for WorkflowPipelineView
 * Displays a skeleton layout with shimmer animation during initial data fetch
 */
export function LoadingSkeleton() {
  return (
    <div
      className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl border border-slate-700/50 shadow-[0_0_15px_rgba(16,185,129,0.1)] overflow-hidden relative"
      role="status"
      aria-live="polite"
      aria-label="Loading workflow data, please wait"
    >
      {/* Subtle inner glow */}
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent pointer-events-none"></div>

      {/* Screen reader announcement */}
      <span className="absolute w-px h-px p-0 -m-px overflow-hidden whitespace-nowrap border-0">Loading workflow visualization</span>

      {/* Header Skeleton */}
      <div className="px-4 py-3 border-b border-slate-700/50 flex items-center justify-between relative z-10">
        <div className="flex items-center gap-3">
          {/* Issue number skeleton */}
          <div className="w-16 h-6 bg-gradient-to-r from-slate-700 to-slate-600 rounded animate-pulse"></div>
          <div>
            {/* Title skeleton */}
            <div className="w-32 h-4 bg-gradient-to-r from-slate-700 to-slate-600 rounded animate-pulse mb-2"></div>
            {/* Badges skeleton */}
            <div className="flex items-center gap-2">
              <div className="w-20 h-5 bg-gradient-to-r from-slate-700 to-slate-600 rounded-md animate-pulse"></div>
              <div className="w-16 h-5 bg-gradient-to-r from-slate-700 to-slate-600 rounded-md animate-pulse"></div>
            </div>
          </div>
        </div>
        {/* Cost skeleton */}
        <div className="text-right">
          <div className="w-16 h-6 bg-gradient-to-r from-slate-700 to-slate-600 rounded animate-pulse mb-1"></div>
          <div className="w-20 h-3 bg-gradient-to-r from-slate-700 to-slate-600 rounded animate-pulse"></div>
        </div>
      </div>

      {/* Pipeline Visualization Skeleton */}
      <div className="px-4 py-6 relative z-10">
        <div className="relative min-h-[300px] flex items-center justify-center">
          {/* Central Hub Skeleton */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
            <div className="relative w-24 h-24 rounded-full border-2 border-slate-700/60 bg-gradient-to-br from-slate-700 to-slate-600 flex items-center justify-center animate-pulse">
              {/* Pulsing rings */}
              <div className="absolute inset-0 rounded-full border-2 border-slate-600/40"></div>
              <div className="absolute -inset-4 rounded-full border border-slate-600/20"></div>
              <div className="absolute -inset-8 rounded-full border border-slate-600/10"></div>
              {/* W placeholder */}
              <div className="w-8 h-8 bg-slate-600 rounded opacity-50"></div>
            </div>
          </div>

          {/* Phase Nodes Skeleton - 9 nodes in circle */}
          {Array.from({ length: 9 }).map((_, idx) => {
            const angle = (idx * 360) / 9 - 90; // Start from top
            const radius = 110;
            const x = Math.cos((angle * Math.PI) / 180) * radius;
            const y = Math.sin((angle * Math.PI) / 180) * radius;

            return (
              <div
                key={idx}
                className="absolute top-1/2 left-1/2"
                style={{
                  transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`,
                }}
              >
                <div className="flex flex-col items-center gap-1">
                  {/* Phase node circle */}
                  <div className="w-12 h-12 rounded-full border-2 border-slate-700/60 bg-gradient-to-br from-slate-700 to-slate-600 flex items-center justify-center animate-pulse">
                    <div className="w-5 h-5 bg-slate-600 rounded opacity-50"></div>
                  </div>
                  {/* Phase name */}
                  <div className="w-12 h-3 bg-gradient-to-r from-slate-700 to-slate-600 rounded animate-pulse"></div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Progress Info Skeleton */}
        <div className="mt-4 pt-4 border-t border-slate-700/50 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Duration skeleton */}
            <div className="flex items-center gap-1.5">
              <div className="w-4 h-4 bg-slate-700 rounded animate-pulse"></div>
              <div className="w-16 h-4 bg-gradient-to-r from-slate-700 to-slate-600 rounded animate-pulse"></div>
            </div>
          </div>
          {/* Phase progress skeleton */}
          <div className="w-40 h-4 bg-gradient-to-r from-slate-700 to-slate-600 rounded animate-pulse"></div>
        </div>
      </div>
    </div>
  );
}
