import { useState } from 'react';
import { useRequestForm } from './RequestFormHooks';
import { RequestFormPreview } from './RequestFormPreview';
import { ConfirmDialog } from './ConfirmDialog';
import { SystemStatusPanel } from './SystemStatusPanel';
import { ZteHopperQueueCard } from './ZteHopperQueueCard';
import { CurrentWorkflowCard } from './CurrentWorkflowCard';
import { FileUploadSection } from './request-form/FileUploadSection';
import { ContextAnalysisButton } from './context-review/ContextAnalysisButton';
import { ContextReviewPanel } from './context-review/ContextReviewPanel';

export function RequestFormCore() {
  const [contextReviewId, setContextReviewId] = useState<number | null>(null);
  const {
    // Form state
    nlInput,
    setNlInput,
    projectPath,
    setProjectPath,
    autoPost,
    setAutoPost,

    // UI state
    isLoading,
    error,
    successMessage,
    storageWarning,

    // Preview state
    preview,
    costEstimate,
    showConfirm,

    // System health state
    systemHealthy,
    healthWarning,

    // Staggered loading
    showHopperQueue,

    // Drag and drop
    isDragging,
    dragError,
    isReading,
    dragHandlers,
    clearDragError,

    // Phase handler
    phaseHandler,

    // Handlers
    handleSubmit,
    handleConfirm,
    handleCancel,
    handleContentReceived,
  } = useRequestForm();

  return (
    <>
      <div className="max-w-7xl mx-auto px-4">
        {/* First Row: Create New Request & Hopper Queue */}
        <div className="flex flex-col lg:flex-row gap-4 mb-4 items-stretch">
          {/* Left Column - Create New Request */}
          <div
            className={`lg:w-1/2 lg:flex-shrink-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg shadow-xl border border-slate-700 p-4 space-y-3 relative transition-all flex flex-col ${
              isDragging ? 'ring-4 ring-emerald-500 ring-opacity-50' : ''
            }`}
            {...dragHandlers}
            aria-busy={isReading || phaseHandler.isSubmitting}
          >
            <div className="relative mb-1">
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 to-teal-500/10 rounded-lg -m-2"></div>
              <h2 className="text-xl font-bold text-white relative z-10">
                Create New Request
              </h2>
            </div>

            <div>
              <label
                htmlFor="nl-input"
                className="block text-sm font-medium text-slate-300 mb-2"
              >
                Describe what you want to build
              </label>

              <textarea
                id="nl-input"
                placeholder="Example: Build a REST API for user management with CRUD operations..."
                value={nlInput}
                onChange={(e) => setNlInput(e.target.value)}
                rows={4}
                className="w-full p-3 bg-slate-800 border border-slate-600 text-white placeholder-slate-400 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
                disabled={isReading}
              />

              <FileUploadSection
                onContentReceived={handleContentReceived}
                onPhasePreviewOpen={phaseHandler.openPhasePreview}
                isDragging={isDragging}
                dragError={dragError}
                isReading={isReading}
                clearDragError={clearDragError}
                currentNlInput={nlInput}
              />
            </div>

            <div>
              <label
                htmlFor="project-path"
                className="block text-sm font-medium text-slate-300 mb-2"
              >
                Project path (optional)
              </label>
              <input
                id="project-path"
                type="text"
                placeholder="/Users/username/projects/my-app"
                value={projectPath}
                onChange={(e) => setProjectPath(e.target.value)}
                className="w-full p-3 bg-slate-800 border border-slate-600 text-white placeholder-slate-400 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
            </div>

            {/* Context Analysis Section */}
            <div className="border-t border-slate-700 pt-3">
              <ContextAnalysisButton
                changeDescription={nlInput}
                projectPath={projectPath}
                onAnalysisStart={setContextReviewId}
                disabled={isLoading}
              />
            </div>

            {contextReviewId && (
              <ContextReviewPanel
                reviewId={contextReviewId}
                onClose={() => setContextReviewId(null)}
              />
            )}

            <div className="flex items-center">
              <input
                id="auto-post"
                type="checkbox"
                checked={autoPost}
                onChange={(e) => setAutoPost(e.target.checked)}
                className="h-4 w-4 text-emerald-500 focus:ring-emerald-500 border-slate-600 rounded bg-slate-800"
              />
              <label htmlFor="auto-post" className="ml-2 text-sm text-slate-300">
                Auto-post to GitHub (skip confirmation)
              </label>
            </div>

            {storageWarning && (
              <div className="p-4 border rounded-lg bg-yellow-900/20 border-yellow-500/50 text-yellow-200">
                {storageWarning}
              </div>
            )}

            {healthWarning && (
              <div className={`p-4 border rounded-lg ${systemHealthy ? 'bg-yellow-900/20 border-yellow-500/50 text-yellow-200' : 'bg-red-900/20 border-red-500/50 text-red-200'}`}>
                {healthWarning}
              </div>
            )}

            {error && (
              <div className="p-4 bg-red-900/20 border border-red-500/50 rounded-lg text-red-200">
                {error}
              </div>
            )}

            {successMessage && (
              <div className="p-4 bg-emerald-900/20 border border-emerald-500/50 rounded-lg text-emerald-200">
                {successMessage}
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={isLoading || phaseHandler.isSubmitting}
              className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 text-white py-3 px-6 rounded-lg font-medium hover:from-emerald-600 hover:to-teal-600 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed transition-all shadow-lg"
            >
              {isLoading ? 'Processing...' : 'Generate Issue'}
            </button>

            <RequestFormPreview
              preview={preview}
              costEstimate={costEstimate}
              showConfirm={showConfirm}
              autoPost={autoPost}
            />
          </div>

          {/* Right Column - Hopper Queue */}
          <div className="lg:flex-grow">
            {showHopperQueue ? (
              <ZteHopperQueueCard />
            ) : (
              <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg shadow-xl border border-slate-700 p-4 flex items-center justify-center min-h-[200px]">
                <div className="text-slate-500 text-xs animate-pulse">●</div>
              </div>
            )}
          </div>
        </div>

        {/* Second Row: System Status & Current Workflow */}
        <div className="flex flex-col lg:flex-row gap-4 items-stretch">
          {/* System Status */}
          <div className="lg:w-1/2 lg:flex-shrink-0">
            <SystemStatusPanel />
          </div>

          {/* Current Workflow */}
          <div className="lg:flex-grow">
            {showHopperQueue ? (
              <CurrentWorkflowCard />
            ) : (
              <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg shadow-xl border border-slate-700 p-4 flex items-center justify-center min-h-[200px]">
                <div className="text-slate-500 text-xs animate-pulse">●</div>
              </div>
            )}
          </div>
        </div>
      </div>

      {showConfirm && preview && (
        <ConfirmDialog
          issue={preview}
          costEstimate={costEstimate}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      )}

      {phaseHandler.modal}
    </>
  );
}
