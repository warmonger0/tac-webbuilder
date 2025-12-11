import { useState } from "react";
import { setQueuePaused } from "../api/client";
import { PhaseQueueList } from "./PhaseQueueCard";
import { QueuePauseToggle } from "./QueuePauseToggle";
import { useQueueWebSocket } from "../hooks/useWebSocket";
import { LoadingState } from "./common/LoadingState";
import { ErrorBanner } from "./common/ErrorBanner";

type TabType = "in-progress" | "completed";

export function ZteHopperQueueCard() {
  const [activeTab, setActiveTab] = useState<TabType>("in-progress");
  const [error, setError] = useState<string | null>(null);

  // Use WebSocket hook for real-time updates
  const { phases, paused: isPaused, isConnected } = useQueueWebSocket();

  // Local state for tracking pause status updates
  const [localIsPaused, setLocalIsPaused] = useState(isPaused);

  // Sync local pause state with WebSocket data
  if (isPaused !== localIsPaused) {
    setLocalIsPaused(isPaused);
  }

  // Loading is true when not connected
  const loading = !isConnected && phases.length === 0;
  const configLoading = !isConnected;

  const handleTogglePause = async (paused: boolean) => {
    try {
      const response = await setQueuePaused(paused);
      setLocalIsPaused(response.paused);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update pause state');
      throw err; // Re-throw to let the toggle component handle it
    }
  };

  // Filter phases by status and sort high to low (phase 1 at bottom)
  const inProgressPhases = phases
    .filter(p => p.status === 'queued' || p.status === 'ready' || p.status === 'running')
    .sort((a, b) => b.phase_number - a.phase_number);
  const completedPhases = phases
    .filter(p => p.status === 'completed' || p.status === 'failed' || p.status === 'blocked')
    .sort((a, b) => b.phase_number - a.phase_number);

  // Debug logging (disabled in production)
  // console.log('[ZteHopperQueue] Total phases:', phases.length);
  // console.log('[ZteHopperQueue] In progress:', inProgressPhases.length, inProgressPhases.map(p => `#${p.phase_number}(${p.status})`));
  // console.log('[ZteHopperQueue] Completed:', completedPhases.length);

  return (
    <div className="relative h-full">
      {/* Main Queue Card */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg shadow-xl border border-slate-700 p-4 flex flex-col h-full">

        {/* Pause/Play Toggle - Attached to right side, outside card */}
        <div className="absolute -right-14 top-1/2 -translate-y-1/2">
          <QueuePauseToggle
            isPaused={localIsPaused}
            onToggle={handleTogglePause}
            disabled={configLoading || loading}
          />
        </div>
        <div className="relative mb-3">
          <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 to-teal-500/10 rounded-lg -m-2"></div>
          <div className="flex items-center justify-between relative z-10">
            <h2 className="text-xl font-bold text-white">
              Hopper Queue
            </h2>
            <div className="flex items-center gap-3">
              {phases.length > 0 && (
                <span className="text-sm text-slate-300">
                  {inProgressPhases.length} in progress • {completedPhases.length} completed
                </span>
              )}
            </div>
          </div>
        </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-slate-600 mb-3" role="tablist">
        <button
          role="tab"
          aria-selected={activeTab === "in-progress"}
          aria-controls="in-progress-panel"
          onClick={() => setActiveTab("in-progress")}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === "in-progress"
              ? "text-emerald-400 border-b-2 border-emerald-500"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          In Progress ({inProgressPhases.length})
        </button>
        <button
          role="tab"
          aria-selected={activeTab === "completed"}
          aria-controls="completed-panel"
          onClick={() => setActiveTab("completed")}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === "completed"
              ? "text-emerald-400 border-b-2 border-emerald-500"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Completed ({completedPhases.length})
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <ErrorBanner error={error} />

        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <LoadingState message="Loading queue..." />
          </div>
        ) : (
          <>
            {activeTab === "in-progress" && (
              <div
                role="tabpanel"
                id="in-progress-panel"
                aria-labelledby="in-progress-tab"
                className="flex-1 flex flex-col"
              >
                {inProgressPhases.length === 0 ? (
                  <div className="bg-gradient-to-r from-emerald-500 to-teal-500 rounded-lg flex items-start p-6 flex-1 shadow-lg">
                    <p className="text-white font-bold text-xl text-left">
                      Queue Empty
                    </p>
                  </div>
                ) : (
                  <PhaseQueueList phases={inProgressPhases} />
                )}
              </div>
            )}

            {activeTab === "completed" && (
              <div
                role="tabpanel"
                id="completed-panel"
                aria-labelledby="completed-tab"
                className="flex-1 flex flex-col"
              >
                {completedPhases.length === 0 ? (
                  <div className="rounded-lg flex items-center justify-center bg-gray-50 flex-1">
                    <p className="text-gray-500 text-lg">
                      Completed items will be displayed here
                    </p>
                  </div>
                ) : (
                  <PhaseQueueList phases={completedPhases} />
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
    </div>
  );
}
