import { useState, useEffect } from "react";
import { getQueueAll, type PhaseQueueItem } from "../api/client";
import { PhaseQueueList } from "./PhaseQueueCard";

type TabType = "in-progress" | "completed";

export function ZteHopperQueueCard() {
  const [activeTab, setActiveTab] = useState<TabType>("in-progress");
  const [phases, setPhases] = useState<PhaseQueueItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch queue data
  useEffect(() => {
    const fetchQueue = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await getQueueAll();
        setPhases(response.phases);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch queue');
        console.error('Failed to fetch queue:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchQueue();

    // Refresh every 10 seconds
    const interval = setInterval(fetchQueue, 10000);

    return () => clearInterval(interval);
  }, []);

  // Filter phases by status
  const inProgressPhases = phases.filter(p =>
    p.status === 'queued' || p.status === 'ready' || p.status === 'running'
  );
  const completedPhases = phases.filter(p =>
    p.status === 'completed' || p.status === 'failed' || p.status === 'blocked'
  );

  return (
    <div className="bg-white rounded-lg shadow p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-900">
          Hopper Queue
        </h2>
        {phases.length > 0 && (
          <span className="text-sm text-gray-600">
            {inProgressPhases.length} in progress • {completedPhases.length} completed
          </span>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 mb-4" role="tablist">
        <button
          role="tab"
          aria-selected={activeTab === "in-progress"}
          aria-controls="in-progress-panel"
          onClick={() => setActiveTab("in-progress")}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === "in-progress"
              ? "text-emerald-600 border-b-2 border-emerald-500"
              : "text-gray-500 hover:text-gray-700"
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
              ? "text-emerald-600 border-b-2 border-emerald-500"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Completed ({completedPhases.length})
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <p className="text-red-700 text-sm">⚠️ {error}</p>
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center h-[295px]">
            <div className="text-center">
              <div className="animate-spin text-4xl mb-2">⚙️</div>
              <p className="text-gray-500">Loading queue...</p>
            </div>
          </div>
        ) : (
          <>
            {activeTab === "in-progress" && (
              <div
                role="tabpanel"
                id="in-progress-panel"
                aria-labelledby="in-progress-tab"
                className="h-[295px] overflow-hidden"
              >
                {inProgressPhases.length === 0 ? (
                  <div className="bg-emerald-500 rounded-lg flex items-start p-6 h-full">
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
                className="h-[295px] overflow-hidden"
              >
                {completedPhases.length === 0 ? (
                  <div className="rounded-lg flex items-center justify-center bg-gray-50 h-full">
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

      {/* Refresh Indicator */}
      {!isLoading && phases.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            Auto-refreshing every 10 seconds
          </p>
        </div>
      )}
    </div>
  );
}
