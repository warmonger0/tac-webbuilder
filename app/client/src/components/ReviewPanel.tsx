/**
 * Review Panel Component (Panel 8)
 *
 * Allows reviewing and approving/rejecting automation patterns.
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import {
  patternReviewClient,
  PatternReview,
  ApproveRequest,
  RejectRequest,
  CommentRequest,
} from '../api/patternReviewClient';

export function ReviewPanel() {
  const queryClient = useQueryClient();
  const [selectedPattern, setSelectedPattern] = useState<PatternReview | null>(null);
  const [notes, setNotes] = useState('');
  const [reason, setReason] = useState('');
  const [comment, setComment] = useState('');
  const [showCommentForm, setShowCommentForm] = useState(false);
  const [mutationError, setMutationError] = useState<string | null>(null);

  // Fetch pending patterns
  const { data: patterns, isLoading, error } = useQuery({
    queryKey: ['patterns', 'pending'],
    queryFn: () => patternReviewClient.getPendingPatterns(20),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['patterns', 'statistics'],
    queryFn: () => patternReviewClient.getReviewStatistics(),
    refetchInterval: 30000,
  });

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: ({ patternId, request }: { patternId: string; request: ApproveRequest }) =>
      patternReviewClient.approvePattern(patternId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patterns'] });
      setSelectedPattern(null);
      setNotes('');
      setMutationError(null);
    },
    onError: (error: Error) => {
      console.error('[ReviewPanel] Approve mutation failed:', error);
      setMutationError(`Failed to approve pattern: ${error.message}`);
    },
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: ({ patternId, request }: { patternId: string; request: RejectRequest }) =>
      patternReviewClient.rejectPattern(patternId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patterns'] });
      setSelectedPattern(null);
      setReason('');
      setMutationError(null);
    },
    onError: (error: Error) => {
      console.error('[ReviewPanel] Reject mutation failed:', error);
      setMutationError(`Failed to reject pattern: ${error.message}`);
    },
  });

  // Comment mutation
  const commentMutation = useMutation({
    mutationFn: ({ patternId, request }: { patternId: string; request: CommentRequest }) =>
      patternReviewClient.addComment(patternId, request),
    onSuccess: () => {
      setShowCommentForm(false);
      setComment('');
      setMutationError(null);
    },
    onError: (error: Error) => {
      console.error('[ReviewPanel] Comment mutation failed:', error);
      setMutationError(`Failed to add comment: ${error.message}`);
    },
  });

  const handleApprove = () => {
    if (!selectedPattern) return;
    toast((t) => (
      <div>
        <p className="mb-3">Approve pattern "{selectedPattern.pattern_id}"?</p>
        <div className="flex gap-2">
          <button
            onClick={() => {
              approveMutation.mutate({
                patternId: selectedPattern.pattern_id,
                request: { notes },
              });
              toast.dismiss(t.id);
            }}
            className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
          >
            Approve
          </button>
          <button
            onClick={() => toast.dismiss(t.id)}
            className="px-3 py-1 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
          >
            Cancel
          </button>
        </div>
      </div>
    ), { duration: Infinity, icon: '✅' });
  };

  const handleReject = () => {
    if (!selectedPattern) return;
    if (!reason.trim()) {
      toast.error('Reason is required for rejection');
      return;
    }
    toast((t) => (
      <div>
        <p className="mb-3">Reject pattern "{selectedPattern.pattern_id}"?</p>
        <div className="flex gap-2">
          <button
            onClick={() => {
              rejectMutation.mutate({
                patternId: selectedPattern.pattern_id,
                request: { reason },
              });
              toast.dismiss(t.id);
            }}
            className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Reject
          </button>
          <button
            onClick={() => toast.dismiss(t.id)}
            className="px-3 py-1 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
          >
            Cancel
          </button>
        </div>
      </div>
    ), { duration: Infinity, icon: '❌' });
  };

  const handleAddComment = () => {
    if (!selectedPattern || !comment.trim()) return;
    commentMutation.mutate({
      patternId: selectedPattern.pattern_id,
      request: { comment },
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Pattern Review</h2>

      {/* Error Banner */}
      {mutationError && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-400 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="text-sm text-red-700 flex-1">{mutationError}</p>
            <button
              onClick={() => setMutationError(null)}
              className="ml-2 text-red-400 hover:text-red-600 font-bold text-lg leading-none"
              aria-label="Dismiss error"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Statistics Summary */}
      {stats && (
        <div className="mb-6 grid grid-cols-5 gap-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <div className="text-xs text-yellow-600 font-medium">PENDING</div>
            <div className="text-2xl font-bold text-yellow-900">{stats.pending}</div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <div className="text-xs text-green-600 font-medium">APPROVED</div>
            <div className="text-2xl font-bold text-green-900">{stats.approved}</div>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <div className="text-xs text-red-600 font-medium">REJECTED</div>
            <div className="text-2xl font-bold text-red-900">{stats.rejected}</div>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="text-xs text-blue-600 font-medium">AUTO-APPROVED</div>
            <div className="text-2xl font-bold text-blue-900">{stats.auto_approved}</div>
          </div>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div className="text-xs text-gray-600 font-medium">TOTAL</div>
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
          </div>
        </div>
      )}

      {isLoading && <div className="text-gray-600">Loading patterns...</div>}
      {error && <div className="text-red-600">Error loading patterns: {String(error)}</div>}

      <div className="grid grid-cols-2 gap-6">
        {/* Pattern List */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            Pending Patterns ({patterns?.length || 0})
          </h3>
          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            {patterns?.map((pattern) => (
              <div
                key={pattern.pattern_id}
                onClick={() => setSelectedPattern(pattern)}
                className={`border rounded-lg p-4 cursor-pointer transition-all ${
                  selectedPattern?.pattern_id === pattern.pattern_id
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="font-mono text-sm text-gray-900">
                    {pattern.pattern_id}
                  </div>
                  <div className="text-xs text-gray-500">
                    {(pattern.confidence_score * 100).toFixed(0)}% confidence
                  </div>
                </div>
                <div className="text-sm text-gray-700 mb-2">
                  {pattern.tool_sequence}
                </div>
                <div className="flex justify-between text-xs text-gray-600">
                  <span>{pattern.occurrence_count} occurrences</span>
                  <span className="font-semibold text-green-600">
                    ${pattern.estimated_savings_usd.toFixed(2)} savings
                  </span>
                </div>
                <div className="mt-2 text-xs font-medium text-indigo-600">
                  Impact: {pattern.impact_score.toLocaleString()}
                </div>
              </div>
            ))}
            {patterns?.length === 0 && (
              <div className="text-gray-500 text-center py-8">
                No pending patterns to review
              </div>
            )}
          </div>
        </div>

        {/* Pattern Details & Actions */}
        <div>
          {selectedPattern ? (
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Pattern Details
              </h3>

              <div className="space-y-3 mb-6">
                <div>
                  <div className="text-xs text-gray-500 font-medium">Pattern ID</div>
                  <div className="font-mono text-sm">{selectedPattern.pattern_id}</div>
                </div>

                <div>
                  <div className="text-xs text-gray-500 font-medium">Tool Sequence</div>
                  <div className="text-sm bg-gray-50 p-2 rounded">
                    {selectedPattern.tool_sequence}
                  </div>
                </div>

                {selectedPattern.pattern_context && (
                  <div>
                    <div className="text-xs text-gray-500 font-medium">Context</div>
                    <div className="text-sm">{selectedPattern.pattern_context}</div>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-gray-500 font-medium">Confidence</div>
                    <div className="text-lg font-semibold">
                      {(selectedPattern.confidence_score * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 font-medium">Occurrences</div>
                    <div className="text-lg font-semibold">
                      {selectedPattern.occurrence_count}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-gray-500 font-medium">Est. Savings</div>
                    <div className="text-lg font-semibold text-green-600">
                      ${selectedPattern.estimated_savings_usd.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 font-medium">Impact Score</div>
                    <div className="text-lg font-semibold text-indigo-600">
                      {selectedPattern.impact_score.toLocaleString()}
                    </div>
                  </div>
                </div>

                {selectedPattern.example_sessions && selectedPattern.example_sessions.length > 0 && (
                  <div>
                    <div className="text-xs text-gray-500 font-medium mb-1">
                      Example Sessions
                    </div>
                    <div className="text-xs space-y-1">
                      {selectedPattern.example_sessions.slice(0, 5).map((session, idx) => (
                        <div key={idx} className="font-mono text-gray-600">
                          {session}
                        </div>
                      ))}
                      {selectedPattern.example_sessions.length > 5 && (
                        <div className="text-gray-500">
                          ... and {selectedPattern.example_sessions.length - 5} more
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Approve Section */}
              <div className="mb-4 border-t pt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Approval Notes (optional)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
                  rows={2}
                  placeholder="Why approve this pattern?"
                />
                <button
                  onClick={handleApprove}
                  disabled={approveMutation.isPending}
                  className="mt-2 w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {approveMutation.isPending ? 'Approving...' : 'Approve Pattern'}
                </button>
              </div>

              {/* Reject Section */}
              <div className="mb-4 border-t pt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rejection Reason (required)
                </label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500"
                  rows={2}
                  placeholder="Why reject this pattern?"
                />
                <button
                  onClick={handleReject}
                  disabled={rejectMutation.isPending || !reason.trim()}
                  className="mt-2 w-full bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {rejectMutation.isPending ? 'Rejecting...' : 'Reject Pattern'}
                </button>
              </div>

              {/* Comment Section */}
              <div className="border-t pt-4">
                {!showCommentForm ? (
                  <button
                    onClick={() => setShowCommentForm(true)}
                    className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md font-medium"
                  >
                    Add Comment for Discussion
                  </button>
                ) : (
                  <>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Comment
                    </label>
                    <textarea
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                      rows={2}
                      placeholder="Add comment for further discussion..."
                    />
                    <div className="mt-2 flex gap-2">
                      <button
                        onClick={handleAddComment}
                        disabled={commentMutation.isPending || !comment.trim()}
                        className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md font-medium disabled:opacity-50"
                      >
                        {commentMutation.isPending ? 'Adding...' : 'Add Comment'}
                      </button>
                      <button
                        onClick={() => {
                          setShowCommentForm(false);
                          setComment('');
                        }}
                        className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded-md font-medium"
                      >
                        Cancel
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          ) : (
            <div className="border border-gray-200 rounded-lg p-8 text-center text-gray-500">
              Select a pattern to review
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
