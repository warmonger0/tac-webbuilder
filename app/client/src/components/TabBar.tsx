interface TabBarProps {
  activeTab: 'request' | 'workflows' | 'history' | 'routes' | 'plans' | 'patterns' | 'quality' | 'review' | 'data';
  onChange: (tab: 'request' | 'workflows' | 'history' | 'routes' | 'plans' | 'patterns' | 'quality' | 'review' | 'data') => void;
}

export function TabBar({ activeTab, onChange }: TabBarProps) {
  const tabs = [
    { id: 'request' as const, label: '1. New Request Panel' },
    { id: 'workflows' as const, label: "2. ADW's Panel" },
    { id: 'history' as const, label: '3. History Panel' },
    { id: 'routes' as const, label: '4. API Routes Panel' },
    { id: 'plans' as const, label: '5. Plans Panel' },
    { id: 'patterns' as const, label: '6. Patterns Panel' },
    { id: 'quality' as const, label: '7. Quality / Compliance Panel' },
    { id: 'review' as const, label: '8. Review Panel' },
    { id: 'data' as const, label: '9. Data & Structure Panel' },
  ];

  return (
    <div className="flex gap-1 justify-center">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`px-4 py-1.5 font-medium text-sm transition-colors ${
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
