import { useState } from "react";

type TabType = "in-progress" | "completed";

export function ZteHopperQueueCard() {
  const [activeTab, setActiveTab] = useState<TabType>("in-progress");

  return (
    <div className="bg-white rounded-lg shadow p-6 h-full flex flex-col">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">
        Hopper Queue
      </h2>

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
          In Progress
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
          Completed
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1">
        {activeTab === "in-progress" && (
          <div
            role="tabpanel"
            id="in-progress-panel"
            aria-labelledby="in-progress-tab"
            className="h-[295px] bg-emerald-500 rounded-lg flex items-start p-6"
            style={{ backgroundColor: "rgb(16, 185, 129)" }}
          >
            <p className="text-white font-bold text-xl text-left">
              Queue Empty
            </p>
          </div>
        )}

        {activeTab === "completed" && (
          <div
            role="tabpanel"
            id="completed-panel"
            aria-labelledby="completed-tab"
            className="h-[295px] rounded-lg flex items-center justify-center bg-gray-50"
          >
            <p className="text-gray-500 text-lg">
              Completed items will be displayed here
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
