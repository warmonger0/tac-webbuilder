/**
 * Context Review Panel
 *
 * Displays AI-powered codebase context analysis results with suggestions for
 * additional files and context to improve workflow accuracy.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertCircle, CheckCircle2, FileCode, Loader2, Sparkles } from 'lucide-react';

export interface ContextSuggestion {
  id: number;
  suggestion_type: string;
  suggestion_text: string;
  confidence: number;
  priority: number;
  rationale: string;
}

export interface ContextAnalysisResult {
  review_id: number;
  status: 'analyzing' | 'complete' | 'failed';
  result?: {
    total_files_analyzed: number;
    suggested_files: string[];
    missing_dependencies: string[];
    complexity_score: number;
    recommendations: string[];
  };
  created_at: string;
}

interface ContextReviewPanelProps {
  reviewId: number | null;
  onClose: () => void;
}

/**
 * Fetch context analysis by review ID.
 *
 * @param reviewId - Review ID to fetch
 * @returns Promise resolving to ContextAnalysisResult
 */
const fetchContextAnalysis = async (reviewId: number): Promise<ContextAnalysisResult> => {
  const response = await fetch(`/api/v1/context-review/${reviewId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch analysis: ${response.statusText}`);
  }

  return response.json();
};

/**
 * Fetch context suggestions by review ID.
 *
 * @param reviewId - Review ID to fetch suggestions for
 * @returns Promise resolving to array of ContextSuggestion
 */
const fetchContextSuggestions = async (reviewId: number): Promise<ContextSuggestion[]> => {
  const response = await fetch(`/api/v1/context-review/${reviewId}/suggestions`);

  if (!response.ok) {
    throw new Error(`Failed to fetch suggestions: ${response.statusText}`);
  }

  const data = await response.json();
  return data.suggestions || [];
};

export function ContextReviewPanel({ reviewId, onClose }: ContextReviewPanelProps) {
  // Fetch analysis with conditional polling
  const {
    data: analysis,
    isLoading: isLoadingAnalysis,
    error: analysisError,
  } = useQuery({
    queryKey: ['context-review', reviewId],
    queryFn: () => fetchContextAnalysis(reviewId!),
    // Conditional refetch: Poll every 3s while analyzing, stop when complete
    refetchInterval: (data) => {
      return data?.status === 'analyzing' ? 3000 : false;
    },
    // Only run query if reviewId exists
    enabled: !!reviewId,
    // Keep data fresh
    staleTime: 0,
  });

  // Fetch suggestions separately
  const {
    data: suggestions = [],
    isLoading: isLoadingSuggestions,
  } = useQuery({
    queryKey: ['context-review-suggestions', reviewId],
    queryFn: () => fetchContextSuggestions(reviewId!),
    enabled: !!reviewId,
    staleTime: 0,
  });

  const isLoading = isLoadingAnalysis || isLoadingSuggestions;
  const error = analysisError;

  if (!reviewId) return null;

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg shadow-xl border border-slate-700 p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-emerald-400" />
          <h3 className="text-lg font-semibold text-white">
            AI Context Analysis
          </h3>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white transition-colors"
          aria-label="Close analysis panel"
        >
          ×
        </button>
      </div>

      {/* Loading State */}
      {isLoading && !analysis && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 text-emerald-400 animate-spin" />
          <span className="ml-2 text-slate-300">Analyzing codebase context...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-300 font-medium">Analysis Failed</p>
            <p className="text-red-400 text-sm mt-1">
              {error instanceof Error ? error.message : 'Unknown error'}
            </p>
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && analysis.status === 'complete' && analysis.result && (
        <div className="space-y-4">
          {/* Summary Stats */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
              <div className="text-slate-400 text-xs mb-1">Files Analyzed</div>
              <div className="text-white text-2xl font-bold">
                {analysis.result.total_files_analyzed}
              </div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
              <div className="text-slate-400 text-xs mb-1">Complexity Score</div>
              <div className="text-white text-2xl font-bold">
                {analysis.result.complexity_score}/10
              </div>
            </div>
          </div>

          {/* Suggested Files */}
          {analysis.result.suggested_files && analysis.result.suggested_files.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                <FileCode className="w-4 h-4" />
                Suggested Additional Files
              </h4>
              <div className="space-y-1">
                {analysis.result.suggested_files.map((file, idx) => (
                  <div
                    key={idx}
                    className="bg-emerald-500/10 border border-emerald-500/30 rounded px-3 py-2 text-sm text-emerald-300 font-mono"
                  >
                    {file}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Missing Dependencies */}
          {analysis.result.missing_dependencies && analysis.result.missing_dependencies.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-yellow-400" />
                Potential Missing Dependencies
              </h4>
              <div className="space-y-1">
                {analysis.result.missing_dependencies.map((dep, idx) => (
                  <div
                    key={idx}
                    className="bg-yellow-500/10 border border-yellow-500/30 rounded px-3 py-2 text-sm text-yellow-300"
                  >
                    {dep}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {analysis.result.recommendations && analysis.result.recommendations.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-blue-400" />
                Recommendations
              </h4>
              <ul className="space-y-2">
                {analysis.result.recommendations.map((rec, idx) => (
                  <li
                    key={idx}
                    className="bg-blue-500/10 border border-blue-500/30 rounded px-3 py-2 text-sm text-blue-300 flex items-start gap-2"
                  >
                    <span className="text-blue-400 flex-shrink-0">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* High-Priority Suggestions */}
          {suggestions.filter(s => s.priority <= 2).length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-300 mb-2">
                High-Priority Suggestions
              </h4>
              <div className="space-y-2">
                {suggestions
                  .filter(s => s.priority <= 2)
                  .map((suggestion) => (
                    <div
                      key={suggestion.id}
                      className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-3"
                    >
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <span className="text-purple-300 text-sm font-medium">
                          {suggestion.suggestion_type}
                        </span>
                        <span className="text-purple-400 text-xs">
                          {Math.round(suggestion.confidence * 100)}% confident
                        </span>
                      </div>
                      <p className="text-purple-200 text-sm">{suggestion.suggestion_text}</p>
                      {suggestion.rationale && (
                        <p className="text-purple-400 text-xs mt-1 italic">
                          {suggestion.rationale}
                        </p>
                      )}
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Analyzing State */}
      {analysis && analysis.status === 'analyzing' && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4 flex items-center gap-3">
          <Loader2 className="w-5 h-5 text-emerald-400 animate-spin flex-shrink-0" />
          <div>
            <p className="text-emerald-300 font-medium">Analysis in progress...</p>
            <p className="text-emerald-400 text-sm mt-1">
              This may take a few seconds as we analyze your codebase
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
