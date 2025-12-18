/**
 * QC Metrics Update Notification
 *
 * Shows a toast notification when QC metrics are updated via WebSocket.
 * Displays the new score and what changed.
 */

import { useEffect, useState } from 'react';

interface QCNotificationProps {
  oldScore?: number;
  newScore: number;
  changedCategories?: string[];
}

export function QCMetricsNotification({ oldScore, newScore, changedCategories }: QCNotificationProps) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    // Auto-hide after 5 seconds
    const timer = setTimeout(() => {
      setVisible(false);
    }, 5000);

    return () => clearTimeout(timer);
  }, []);

  if (!visible) return null;

  const scoreDelta = oldScore ? newScore - oldScore : 0;
  const scoreImproved = scoreDelta > 0;
  const scoreChanged = Math.abs(scoreDelta) > 0.5;

  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in-right">
      <div className="bg-slate-800 border border-slate-700 rounded-lg shadow-xl p-4 max-w-sm">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <span className="text-2xl">
              {scoreImproved ? '📈' : scoreChanged ? '📊' : '🔄'}
            </span>
          </div>

          <div className="flex-1">
            <h3 className="text-sm font-semibold text-gray-200 mb-1">
              QC Metrics Updated
            </h3>

            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg font-bold text-blue-400">{newScore.toFixed(1)}</span>
              {scoreChanged && (
                <span
                  className={`text-xs font-medium ${
                    scoreImproved ? 'text-emerald-400' : 'text-red-400'
                  }`}
                >
                  {scoreImproved ? '+' : ''}
                  {scoreDelta.toFixed(1)}
                </span>
              )}
            </div>

            {changedCategories && changedCategories.length > 0 && (
              <div className="text-xs text-gray-400">
                Updated: {changedCategories.join(', ')}
              </div>
            )}
          </div>

          <button
            onClick={() => setVisible(false)}
            className="flex-shrink-0 text-gray-500 hover:text-gray-300 transition-colors"
          >
            <span className="text-lg">×</span>
          </button>
        </div>
      </div>
    </div>
  );
}
