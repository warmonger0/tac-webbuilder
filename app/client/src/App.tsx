import { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TabBar } from './components/TabBar';
import { RequestForm } from './components/RequestForm';
import { WorkflowDashboard } from './components/WorkflowDashboard';
import { WorkflowHistoryView } from './components/WorkflowHistoryView';
import { RoutesView } from './components/RoutesView';
import { config } from './config';

const queryClient = new QueryClient();
const ACTIVE_TAB_STORAGE_KEY = config.storage.ACTIVE_TAB_KEY;

function App() {
  const [activeTab, setActiveTab] = useState<
    'request' | 'workflows' | 'history' | 'routes'
  >(() => {
    // Load active tab from localStorage on mount
    const savedTab = localStorage.getItem(ACTIVE_TAB_STORAGE_KEY);
    if (savedTab && ['request', 'workflows', 'history', 'routes'].includes(savedTab)) {
      return savedTab as 'request' | 'workflows' | 'history' | 'routes';
    }
    return 'request';
  });

  // Save active tab to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem(ACTIVE_TAB_STORAGE_KEY, activeTab);
  }, [activeTab]);

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-gray-200">
          <div className="container mx-auto px-4 py-2 text-center">
            <h1 className="text-xl font-bold text-gray-900">
              {config.app.NAME}
            </h1>
            <p className="text-gray-600 text-xs">
              {config.app.TAGLINE}
            </p>
          </div>
        </header>

        <nav className="bg-white border-b border-gray-200">
          <div className="container mx-auto px-4">
            <TabBar activeTab={activeTab} onChange={setActiveTab} />
          </div>
        </nav>

        <div className="visual-separator" />

        <main className="container mx-auto px-4 py-4">
          {activeTab === 'request' && <RequestForm />}
          {activeTab === 'workflows' && <WorkflowDashboard />}
          {activeTab === 'history' && <WorkflowHistoryView />}
          {activeTab === 'routes' && <RoutesView />}
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;
