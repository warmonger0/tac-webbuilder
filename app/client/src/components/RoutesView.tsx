import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getRoutes } from '../api/client';
import type { Route } from '../types';

function MethodBadge({ method }: { method: string }) {
  const colors: Record<string, string> = {
    GET: 'bg-blue-100 text-blue-800',
    POST: 'bg-green-100 text-green-800',
    PUT: 'bg-yellow-100 text-yellow-800',
    DELETE: 'bg-red-100 text-red-800',
    PATCH: 'bg-purple-100 text-purple-800',
  };

  const colorClass = colors[method] || 'bg-gray-100 text-gray-800';

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

  const {
    data: routesData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['routes'],
    queryFn: getRoutes,
  });

  const filteredRoutes = useMemo(() => {
    if (!routesData?.routes) return [];

    return routesData.routes.filter((route: Route) => {
      // Method filter
      if (methodFilter !== 'ALL' && route.method !== methodFilter) {
        return false;
      }

      // Text search (case-insensitive)
      if (searchText) {
        const search = searchText.toLowerCase();
        return (
          route.path.toLowerCase().includes(search) ||
          route.handler.toLowerCase().includes(search) ||
          route.description.toLowerCase().includes(search)
        );
      }

      return true;
    });
  }, [routesData, searchText, methodFilter]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-gray-600">Loading routes...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
        Error loading routes:{' '}
        {error instanceof Error ? error.message : 'Unknown error'}
      </div>
    );
  }

  if (!routesData || routesData.routes.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
        <p className="text-gray-600 text-lg">No routes found</p>
        <p className="text-gray-500 text-sm mt-2">
          Routes will appear here once the server is analyzed
        </p>
      </div>
    );
  }

  const methods = ['ALL', ...Array.from(new Set(routesData.routes.map((r: Route) => r.method)))];

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">API Routes</h2>

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
        Showing {filteredRoutes.length} of {routesData.total} routes
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
                        {route.handler}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-600 max-w-md">
                        {route.description}
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
