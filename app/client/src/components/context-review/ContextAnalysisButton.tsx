/**
 * Context Analysis Button
 *
 * Triggers AI-powered codebase context analysis for the current request.
 */

import { useState } from 'react';
import { Loader2, Sparkles } from 'lucide-react';
import { ErrorBanner } from '../common/ErrorBanner';

interface ContextAnalysisButtonProps {
  changeDescription: string;
  projectPath?: string;
  onAnalysisStart: (reviewId: number) => void;
  disabled?: boolean;
}

export function ContextAnalysisButton({
  changeDescription,
  projectPath,
  onAnalysisStart,
  disabled = false,
}: ContextAnalysisButtonProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!changeDescription.trim()) {
      setError('Please describe your changes first');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/context-review/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          change_description: changeDescription,
          project_path: projectPath || '/Users/Warmonger0/tac/tac-webbuilder',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Analysis failed');
      }

      const data = await response.json();
      onAnalysisStart(data.review_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Context analysis error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-2">
      <button
        onClick={handleAnalyze}
        disabled={disabled || isAnalyzing || !changeDescription.trim()}
        className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-medium rounded-lg hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
        aria-label="Analyze codebase context"
      >
        {isAnalyzing ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Analyzing...</span>
          </>
        ) : (
          <>
            <Sparkles className="w-4 h-4" />
            <span>Analyze Context</span>
          </>
        )}
      </button>

      <ErrorBanner error={error} title="Analysis Error" />

      <p className="text-slate-400 text-xs">
        AI will suggest additional files and context to improve accuracy
      </p>
    </div>
  );
}
