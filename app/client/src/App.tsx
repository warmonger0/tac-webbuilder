import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TabBar } from './components/TabBar';
import { RequestForm } from './components/RequestForm';
import { WorkflowDashboard } from './components/WorkflowDashboard';
import { HistoryView } from './components/HistoryView';
import { RoutesView } from './components/RoutesView';

const queryClient = new QueryClient();

function App() {
  const [activeTab, setActiveTab] = useState<
    'request' | 'workflows' | 'history' | 'routes'
  >('request');

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-gray-200">
          <div className="container mx-auto px-4 py-6 text-center">
            <h1 className="text-3xl font-bold text-gray-900">
              tac-webbuilder
            </h1>
            <p className="text-gray-600 mt-1">
              Build web apps with natural language
            </p>
          </div>
        </header>

        <nav className="bg-white border-b border-gray-200">
          <div className="container mx-auto px-4">
            <TabBar activeTab={activeTab} onChange={setActiveTab} />
          </div>
        </nav>

        <div className="visual-separator" />

        <main className="container mx-auto px-4 py-8">
          {activeTab === 'request' && <RequestForm />}
          {activeTab === 'workflows' && <WorkflowDashboard />}
          {activeTab === 'history' && <HistoryView />}
          {activeTab === 'routes' && <RoutesView />}
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;
