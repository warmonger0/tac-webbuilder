import { useMemo, useState } from 'react';
import { useRoutesWebSocket } from '../hooks/useWebSocket';
import type { Route } from '../types';
import { httpMethodColors } from '../config/theme';

function formatTimestamp(date: Date | null): string {
  if (!date) return '';

  const now = new Date();
  const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffSeconds < 5) return 'Just now';
  if (diffSeconds < 60) return `${diffSeconds}s ago`;
  if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;
  return `${Math.floor(diffSeconds / 3600)}h ago`;
}

function MethodBadge({ method }: { method: string }) {
  const colorClass = httpMethodColors[method as keyof typeof httpMethodColors] || 'bg-gray-100 text-gray-800';

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}
    >
      {method}
    </span>
  );
}

export function RoutesView() {
  const [searchText, setSearchText] = useState('');
  const [methodFilter, setMethodFilter] = useState<string>('ALL');
  const { routes, isConnected, lastUpdated } = useRoutesWebSocket();

  const filteredRoutes = useMemo(() => {
    if (!routes || routes.length === 0) return [];

    return routes.filter((route: Route) => {
      // Method filter
      if (methodFilter !== 'ALL' && route.method !== methodFilter) {
        return false;
      }

      // Text search (case-insensitive)
      if (searchText) {
        const search = searchText.toLowerCase();
        return (
          route.path.toLowerCase().includes(search) ||
          (route.name?.toLowerCase().includes(search) ?? false) ||
          (route.description?.toLowerCase().includes(search) ?? false) ||
          (route.summary?.toLowerCase().includes(search) ?? false)
        );
      }

      return true;
    });
  }, [routes, searchText, methodFilter]);

  if (!routes || routes.length === 0) {
    return (
      <div>
        {/* Connection status banner */}
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
              }`}
            />
            <span className="text-sm text-gray-600">
              {isConnected ? 'Live updates' : 'Reconnecting...'}
            </span>
            {lastUpdated && (
              <span className="text-xs text-gray-500">
                • Updated {formatTimestamp(lastUpdated)}
              </span>
            )}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
          <p className="text-gray-600 text-lg">No routes found</p>
          <p className="text-gray-500 text-sm mt-2">
            Routes will appear here once the server is analyzed
          </p>
        </div>
      </div>
    );
  }

  const methods = ['ALL', ...Array.from(new Set(routes.map((r: Route) => r.method)))];

  return (
    <div>
      {/* Header with connection status */}
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">API Routes</h2>
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'
            }`}
          />
          <span className="text-sm text-gray-600">
            {isConnected ? 'Live updates' : 'Polling fallback'}
          </span>
          {lastUpdated && (
            <span className="text-xs text-gray-500">
              • Updated {formatTimestamp(lastUpdated)}
            </span>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        {/* Search input */}
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search routes by path, handler, or description..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Method filter */}
        <div>
          <select
            value={methodFilter}
            onChange={(e) => setMethodFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
          >
            {methods.map((method) => (
              <option key={method} value={method}>
                {method === 'ALL' ? 'All Methods' : method}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Summary */}
      <div className="mb-4 text-sm text-gray-600">
        Showing {filteredRoutes.length} of {routes.length} routes
      </div>

      {/* Routes table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Method
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Path
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Handler
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredRoutes.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                    No routes match your filters
                  </td>
                </tr>
              ) : (
                filteredRoutes.map((route: Route) => (
                  <tr
                    key={`${route.method}-${route.path}`}
                    className="hover:bg-gray-50 transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <MethodBadge method={route.method} />
                    </td>
                    <td className="px-6 py-4">
                      <code className="text-sm font-mono text-gray-900">
                        {route.path}
                      </code>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 font-medium">
                        {route.name || 'N/A'}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-600 max-w-md">
                        {route.description || route.summary || 'No description'}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
