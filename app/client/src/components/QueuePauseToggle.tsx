import { useState } from "react";

interface QueuePauseToggleProps {
  isPaused: boolean;
  onToggle: (paused: boolean) => void;
  disabled?: boolean;
}

export function QueuePauseToggle({ isPaused, onToggle, disabled = false }: QueuePauseToggleProps) {
  const [isToggling, setIsToggling] = useState(false);

  const handleToggle = async () => {
    if (disabled || isToggling) return;

    setIsToggling(true);
    try {
      await onToggle(!isPaused);
    } finally {
      setIsToggling(false);
    }
  };

  return (
    <div
      className={`
        relative w-12 h-28 rounded-full border-2
        ${isPaused
          ? 'bg-slate-800 border-amber-500/50 hover:border-amber-500'
          : 'bg-slate-800 border-emerald-500/50 hover:border-emerald-500'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        transition-all duration-300
        shadow-lg
      `}
      onClick={handleToggle}
      title={isPaused ? "Queue Paused - Click to Resume" : "Queue Active - Click to Pause"}
    >
      {/* Pause symbol at top */}
      <div className="absolute top-2 left-1/2 -translate-x-1/2">
        <div className="flex gap-0.5">
          <div className={`w-1 h-3 rounded-sm ${isPaused ? 'bg-amber-400' : 'bg-slate-600'}`} />
          <div className={`w-1 h-3 rounded-sm ${isPaused ? 'bg-amber-400' : 'bg-slate-600'}`} />
        </div>
      </div>

      {/* Toggle switch */}
      <div
        className={`
          absolute left-1/2 -translate-x-1/2
          w-8 h-8 rounded-full
          ${isPaused ? 'top-1 bg-amber-500' : 'bottom-1 bg-emerald-500'}
          transition-all duration-300 ease-in-out
          flex items-center justify-center
          shadow-md
          ${isToggling ? 'animate-pulse' : ''}
        `}
      >
        {/* Icon in toggle */}
        {isPaused ? (
          // Pause icon
          <div className="flex gap-0.5">
            <div className="w-1 h-3 rounded-sm bg-slate-900" />
            <div className="w-1 h-3 rounded-sm bg-slate-900" />
          </div>
        ) : (
          // Play icon
          <div className="w-0 h-0 border-l-[6px] border-l-slate-900 border-t-[4px] border-t-transparent border-b-[4px] border-b-transparent ml-0.5" />
        )}
      </div>

      {/* Play symbol at bottom */}
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2">
        <div className="w-0 h-0 border-l-[6px] border-t-[4px] border-b-[4px] border-t-transparent border-b-transparent"
          style={{
            borderLeftColor: isPaused ? '#64748b' : '#10b981'
          }}
        />
      </div>
    </div>
  );
}
