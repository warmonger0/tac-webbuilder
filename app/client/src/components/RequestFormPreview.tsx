import type { CostEstimate, GitHubIssue } from '../types';
import { IssuePreview } from './IssuePreview';
import { CostEstimateCard } from './CostEstimateCard';

export interface RequestFormPreviewProps {
  preview: GitHubIssue | null;
  costEstimate: CostEstimate | null;
  showConfirm: boolean;
  autoPost: boolean;
  className?: string;
}

export function RequestFormPreview({
  preview,
  costEstimate,
  showConfirm,
  autoPost,
  className = '',
}: RequestFormPreviewProps) {
  // Don't render if no preview or if showing confirm dialog or auto-posting
  if (!preview || showConfirm || autoPost) {
    return null;
  }

  return (
    <div className={`mt-6 space-y-6 ${className}`}>
      <h3 className="text-xl font-bold text-white">Preview</h3>

      {/* Cost Estimate Card - Displayed FIRST for visibility */}
      {costEstimate && (
        <CostEstimateCard estimate={costEstimate} />
      )}

      {/* GitHub Issue Preview */}
      <IssuePreview issue={preview} />
    </div>
  );
}
