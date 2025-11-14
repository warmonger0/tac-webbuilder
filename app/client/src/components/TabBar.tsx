interface TabBarProps {
  activeTab: 'request' | 'workflows' | 'history' | 'routes';
  onChange: (tab: 'request' | 'workflows' | 'history' | 'routes') => void;
}

export function TabBar({ activeTab, onChange }: TabBarProps) {
  const tabs = [
    { id: 'request' as const, label: 'New Request' },
    { id: 'workflows' as const, label: 'Workflows' },
    { id: 'history' as const, label: 'History' },
    { id: 'routes' as const, label: 'API Routes' },
  ];

  return (
    <div className="flex gap-1 justify-center">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === tab.id
              ? 'text-primary border-b-2 border-primary'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
