import { useEffect, useState } from "react";
import { getQueueAll, getQueueConfig, type PhaseQueueItem, setQueuePaused } from "../api/client";
import { PhaseQueueList } from "./PhaseQueueCard";
import { QueuePauseToggle } from "./QueuePauseToggle";
import { intervals } from '../config/intervals';

type TabType = "in-progress" | "completed";

export function ZteHopperQueueCard() {
  const [activeTab, setActiveTab] = useState<TabType>("in-progress");
  const [phases, setPhases] = useState<PhaseQueueItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const [configLoading, setConfigLoading] = useState(true);

  // Fetch queue and config on mount and poll for updates
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [queueData, configData] = await Promise.all([
          getQueueAll(),
          getQueueConfig()
        ]);
        setPhases(queueData.phases);
        setIsPaused(configData.paused);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch queue');
      } finally {
        setLoading(false);
        setConfigLoading(false);
      }
    };

    // Initial fetch
    fetchData();

    // Poll every 10 seconds for updates
    const interval = setInterval(fetchData, intervals.components.hopperQueue.pollingInterval);

    return () => clearInterval(interval);
  }, []); // Empty deps = run once on mount, cleanup on unmount

  const handleTogglePause = async (paused: boolean) => {
    try {
      const response = await setQueuePaused(paused);
      setIsPaused(response.paused);
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
            isPaused={isPaused}
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
        {error && (
          <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4 mb-4">
            <p className="text-red-200 text-sm">⚠️ {error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center flex-1">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 relative">
                <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-teal-500 rounded-full animate-ping opacity-75"></div>
                <div className="relative bg-gradient-to-r from-emerald-500 to-teal-600 rounded-full w-16 h-16 flex items-center justify-center">
                  <svg className="w-8 h-8 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
              </div>
              <p className="text-slate-300">Loading queue...</p>
            </div>
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
