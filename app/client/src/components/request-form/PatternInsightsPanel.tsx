import { useState, useEffect } from 'react';
import { PatternPrediction, SimilarWorkflowSummary } from '../../types/api.types';
import PatternBadge from './PatternBadge';
import SimilarWorkflowCard from './SimilarWorkflowCard';

interface PatternInsightsPanelProps {
  predictions: PatternPrediction[];
  similarWorkflows: SimilarWorkflowSummary[];
  recommendations: string[];
  isLoading: boolean;
  error: string | null;
}

/**
 * PatternInsightsPanel displays real-time pattern predictions and insights
 *
 * Features:
 * - Collapsible panel with expand/collapse
 * - Pattern predictions with confidence scores
 * - Similar historical workflows
 * - Optimization recommendations
 * - Loading and error states
 * - Keyboard shortcut (Cmd/Ctrl+I) to toggle
 */
export default function PatternInsightsPanel({
  predictions,
  similarWorkflows,
  recommendations,
  isLoading,
  error,
}: PatternInsightsPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [showAllPatterns, setShowAllPatterns] = useState(false);

  const hasContent = predictions.length > 0 || similarWorkflows.length > 0;

  // Auto-expand when predictions arrive
  useEffect(() => {
    if (hasContent && !isExpanded) {
      setIsExpanded(true);
    }
  }, [hasContent]);

  // Keyboard shortcut: Cmd/Ctrl+I to toggle
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'i') {
        e.preventDefault();
        setIsExpanded(prev => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Determine which patterns to show
  const visiblePatterns = showAllPatterns ? predictions : predictions.slice(0, 6);
  const hasMorePatterns = predictions.length > 6;

  if (!hasContent && !isLoading && !error) {
    return (
      <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-sm text-gray-500 text-center">
          Start typing to see pattern predictions...
        </p>
      </div>
    );
  }

  return (
    <div className="mt-4 border border-gray-200 rounded-lg bg-white">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700">Pattern Insights</span>
          {isLoading && (
            <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full" />
          )}
          {!isLoading && hasContent && (
            <span className="text-xs text-gray-500">
              {predictions.length} pattern{predictions.length !== 1 ? 's' : ''} detected
            </span>
          )}
        </div>
        <svg
          className={`w-5 h-5 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="p-4 pt-0 space-y-4">
          {/* Error State */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">Error: {error}</p>
            </div>
          )}

          {/* Loading Skeleton */}
          {isLoading && !hasContent && (
            <div className="space-y-3 animate-pulse">
              <div className="h-8 bg-gray-200 rounded w-1/3" />
              <div className="h-6 bg-gray-200 rounded w-1/2" />
              <div className="h-6 bg-gray-200 rounded w-2/3" />
            </div>
          )}

          {/* Predicted Patterns */}
          {predictions.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">
                Predicted Patterns
              </h4>
              <div className="flex flex-wrap gap-2">
                {visiblePatterns.map((prediction, index) => (
                  <PatternBadge key={index} prediction={prediction} />
                ))}
              </div>
              {hasMorePatterns && !showAllPatterns && (
                <button
                  onClick={() => setShowAllPatterns(true)}
                  className="mt-2 text-xs text-blue-600 hover:text-blue-700 font-medium"
                >
                  Show {predictions.length - 6} more pattern{predictions.length - 6 !== 1 ? 's' : ''}
                </button>
              )}
              {showAllPatterns && hasMorePatterns && (
                <button
                  onClick={() => setShowAllPatterns(false)}
                  className="mt-2 text-xs text-blue-600 hover:text-blue-700 font-medium"
                >
                  Show less
                </button>
              )}
            </div>
          )}

          {/* Similar Workflows */}
          {similarWorkflows.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">
                Similar Workflows
              </h4>
              <div className="space-y-2">
                {similarWorkflows.slice(0, 3).map((workflow) => (
                  <SimilarWorkflowCard key={workflow.adw_id} workflow={workflow} />
                ))}
              </div>
            </div>
          )}

          {/* Optimization Tips */}
          {recommendations.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">
                Optimization Tips
              </h4>
              <ul className="space-y-1.5">
                {recommendations.map((rec, index) => (
                  <li key={index} className="text-sm text-gray-700 flex items-start gap-2">
                    <span className="text-blue-500 mt-0.5">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Keyboard Shortcut Hint */}
          <div className="pt-2 border-t border-gray-100">
            <p className="text-xs text-gray-400 text-center">
              Press <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs">Cmd/Ctrl+I</kbd> to toggle
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
