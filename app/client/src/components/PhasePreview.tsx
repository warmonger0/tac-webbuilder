import type { ParsedPhase, PhaseParseResult } from '../utils/phaseParser';

interface PhasePreviewProps {
  parseResult: PhaseParseResult;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * PhasePreview - Displays detected phases before submission
 *
 * Shows parsed phases with validation warnings and external document references.
 * Allows user to confirm multi-phase submission or cancel to edit.
 */
export function PhasePreview({ parseResult, onConfirm, onCancel }: PhasePreviewProps) {
  const { isMultiPhase, phases, warnings } = parseResult;

  if (!isMultiPhase) {
    return null; // Don't show preview for single-phase documents
  }

  const hasWarnings = warnings.length > 0;
  const hasErrors = phases.length === 0 || !phases.some(p => p.number === 1);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-blue-600 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">📋</span>
            <div>
              <h2 className="text-xl font-semibold">Multi-Phase Document Detected</h2>
              <p className="text-sm text-blue-100">
                {phases.length} phase{phases.length !== 1 ? 's' : ''} will be created as separate issues
              </p>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="text-white hover:bg-blue-700 rounded p-2 transition-colors"
            aria-label="Close preview"
          >
            ✕
          </button>
        </div>

        {/* Warnings */}
        {hasWarnings && (
          <div className={`px-6 py-4 ${hasErrors ? 'bg-red-50 border-b-2 border-red-200' : 'bg-yellow-50 border-b-2 border-yellow-200'}`}>
            <div className="flex items-start gap-2">
              <span className="text-xl">{hasErrors ? '❌' : '⚠️'}</span>
              <div className="flex-1">
                <h3 className={`font-semibold mb-2 ${hasErrors ? 'text-red-800' : 'text-yellow-800'}`}>
                  {hasErrors ? 'Validation Errors' : 'Warnings'}
                </h3>
                <ul className="space-y-1">
                  {warnings.map((warning, idx) => (
                    <li key={`warning-${idx}`} className={`text-sm ${hasErrors ? 'text-red-700' : 'text-yellow-700'}`}>
                      • {warning}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Phase List */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">Detected Phases</h3>
            <p className="text-sm text-gray-600">
              Each phase will be created as a separate GitHub issue and executed sequentially.
              Phase {phases.length > 1 ? '2+' : 'N+1'} will only execute after Phase {phases.length > 1 ? '1' : 'N'} completes successfully.
            </p>
          </div>

          {phases.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <span className="text-4xl mb-2 block">🔍</span>
              <p>No phases detected in this document.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {phases.map((phase, idx) => (
                <PhaseCard key={`phase-${phase.number}`} phase={phase} position={idx + 1} />
              ))}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            {!hasErrors && (
              <>
                <span className="font-semibold">{phases.length} issues</span> will be created and queued
              </>
            )}
          </div>
          <div className="flex gap-3">
            <button
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors font-medium text-gray-700"
            >
              Cancel
            </button>
            <button
              onClick={onConfirm}
              disabled={hasErrors}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                hasErrors
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              Confirm & Submit
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * PhaseCard - Individual phase display card
 */
function PhaseCard({ phase, position }: { phase: ParsedPhase; position: number }) {
  const isOutOfSequence = phase.number !== position;
  const contentPreview = phase.content.substring(0, 200).replace(/\n+/g, ' ').trim();
  const hasExternalDocs = phase.externalDocs.length > 0;

  return (
    <div className={`border-2 rounded-lg p-4 ${isOutOfSequence ? 'border-yellow-300 bg-yellow-50' : 'border-gray-200 bg-white'}`}>
      {/* Phase Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold">
            {phase.number}
          </div>
          <div>
            <h4 className="font-semibold text-gray-900">
              {phase.title || `Phase ${phase.number}`}
            </h4>
            {isOutOfSequence && (
              <span className="text-xs text-yellow-700 font-medium">
                ⚠️ Out of sequence (appears at position {position})
              </span>
            )}
          </div>
        </div>
        <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full font-medium">
          {position === 1 ? 'Executes first' : `After Phase ${position - 1}`}
        </span>
      </div>

      {/* Content Preview */}
      <div className="mb-3">
        <div className="text-sm text-gray-700 bg-gray-50 rounded p-3 border border-gray-200">
          {contentPreview}
          {phase.content.length > 200 && (
            <span className="text-gray-500"> ...</span>
          )}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {phase.content.length} characters, {phase.content.split('\n').length} lines
        </div>
      </div>

      {/* External Documents */}
      {hasExternalDocs && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="flex items-start gap-2">
            <span className="text-sm">📎</span>
            <div className="flex-1">
              <div className="text-xs font-medium text-gray-600 mb-1">
                Referenced Documents:
              </div>
              <div className="flex flex-wrap gap-1">
                {phase.externalDocs.map((doc, idx) => (
                  <code key={`doc-${idx}`} className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded border border-blue-200">
                    {doc}
                  </code>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
