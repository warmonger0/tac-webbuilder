import { useState } from 'react';
import { AdwWorkflowCatalog } from './AdwWorkflowCatalog';
import { AdwMonitorCard } from './AdwMonitorCard';

type AdwPanelTab = 'catalog' | 'current';

export function WorkflowDashboard() {
  const [activeTab, setActiveTab] = useState<AdwPanelTab>('current');

  return (
    <div className="space-y-4">
      {/* Tab Navigation */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('catalog')}
            className={`flex-1 px-6 py-3 font-medium text-sm transition-colors ${
              activeTab === 'catalog'
                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            📚 Workflow Catalog
          </button>
          <button
            onClick={() => setActiveTab('current')}
            className={`flex-1 px-6 py-3 font-medium text-sm transition-colors ${
              activeTab === 'current'
                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            ⚡ Current Workflow
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="min-h-[600px]">
        {activeTab === 'catalog' && <AdwWorkflowCatalog />}
        {activeTab === 'current' && <AdwMonitorCard />}
      </div>
    </div>
  );
}
