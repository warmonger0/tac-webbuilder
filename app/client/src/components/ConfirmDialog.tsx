import type { GitHubIssue } from '../types';
import { IssuePreview } from './IssuePreview';

interface ConfirmDialogProps {
  issue: GitHubIssue;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  issue,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h3 className="text-2xl font-bold mb-4">Confirm GitHub Issue</h3>

          <IssuePreview issue={issue} />

          <div className="flex gap-4 mt-6">
            <button
              onClick={onConfirm}
              className="flex-1 bg-primary text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-600 transition-colors"
            >
              Post to GitHub
            </button>
            <button
              onClick={onCancel}
              className="flex-1 bg-gray-200 text-gray-800 py-3 px-6 rounded-lg font-medium hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
