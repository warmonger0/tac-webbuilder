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
      if (response.is_multi_phase && response.parent_issue_number) {
        const successMessage =
          `✅ Multi-phase request created!\n\n` +
          `📋 Parent Issue: #${response.parent_issue_number}\n` +
          `🔢 Child Issues: ${response.child_issues?.map(c => `#${c.issue_number}`).join(', ')}\n\n` +
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
