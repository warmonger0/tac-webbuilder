import { useState } from 'react';
import { submitRequest } from '../../api/client';
import type { PhaseParseResult } from '../../utils/phaseParser';

interface UseMultiPhaseSubmitOptions {
  projectPath: string;
  onSuccess: (message: string) => void;
  onError: (error: string) => void;
  onFormClear: () => void;
}

export function useMultiPhaseSubmit({
  projectPath,
  onSuccess,
  onError,
  onFormClear
}: UseMultiPhaseSubmitOptions) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submitMultiPhase = async (phasePreview: PhaseParseResult): Promise<void> => {
    try {
      setIsSubmitting(true);

      // Convert parsed phases to API format
      const phases = phasePreview.phases.map(phase => ({
        number: phase.number,
        title: phase.title,
        content: phase.content,
        externalDocs: phase.externalDocs.length > 0 ? phase.externalDocs : undefined
      }));

      // Submit multi-phase request
      const response = await submitRequest({
        nl_input: phasePreview.originalContent,
        project_path: projectPath || undefined,
        auto_post: true,  // Auto-post multi-phase requests
        phases
      });

      // Handle multi-phase response
      console.log('[DEBUG] Multi-phase response:', JSON.stringify(response, null, 2));
      if (response.is_multi_phase && response.child_issues && response.child_issues.length > 0) {
        // Filter issues that have been created (issue_number is not null)
        const createdIssues = response.child_issues.filter(c => c.issue_number !== null);
        const queuedPhases = response.child_issues.filter(c => c.issue_number === null);

        const successMessage =
          `✅ Multi-phase request created!\n\n` +
          `🚀 Phase 1 Issue: ${createdIssues.length > 0 ? `#${createdIssues[0].issue_number}` : 'Creating...'}\n` +
          `⏳ Queued Phases: ${queuedPhases.length} (will be created just-in-time)\n\n` +
          `All ${phases.length} phases have been queued for execution.`;

        onSuccess(successMessage);
        onFormClear();
      } else {
        onError('Unexpected response format for multi-phase request');
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to submit multi-phase request');
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    submitMultiPhase,
    isSubmitting
  };
}
