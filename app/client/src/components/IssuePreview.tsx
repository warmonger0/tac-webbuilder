import ReactMarkdown from 'react-markdown';
import type { GitHubIssue } from '../types';

interface IssuePreviewProps {
  issue: GitHubIssue;
}

export function IssuePreview({ issue }: IssuePreviewProps) {
  return (
    <div className="border border-gray-200 rounded-lg p-6 bg-white">
      <h2 className="text-2xl font-bold mb-4 text-gray-900">{issue.title}</h2>

      <div className="prose max-w-none mb-4">
        <ReactMarkdown>{issue.body}</ReactMarkdown>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {issue.labels.map((label) => (
          <span
            key={label}
            className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full"
          >
            {label}
          </span>
        ))}
      </div>

      <div className="border-t pt-4 text-sm text-gray-600 space-y-1">
        <div>
          <span className="font-medium">Classification:</span>{' '}
          {issue.classification}
        </div>
        <div>
          <span className="font-medium">Workflow:</span> {issue.workflow}
        </div>
        <div>
          <span className="font-medium">Model Set:</span> {issue.model_set}
        </div>
      </div>
    </div>
  );
}
