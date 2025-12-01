import { useState } from 'react';
import { PhasePreview } from '../PhasePreview';
import { type PhaseParseResult, validatePhases } from '../../utils/phaseParser';
import { useMultiPhaseSubmit } from './useMultiPhaseSubmit';

interface PhaseDetectionHandlerProps {
  projectPath: string;
  onSuccess: (message: string) => void;
  onError: (error: string) => void;
  onFormClear: () => void;
}

/**
 * Handles phase detection and preview workflow
 *
 * This component manages the state for multi-phase document detection,
 * displays the PhasePreview modal, and handles submission/cancellation.
 */
export function PhaseDetectionHandler({
  projectPath,
  onSuccess,
  onError,
  onFormClear
}: PhaseDetectionHandlerProps) {
  const [phasePreview, setPhasePreview] = useState<PhaseParseResult | null>(null);
  const [showPhasePreview, setShowPhasePreview] = useState(false);

  const { submitMultiPhase, isSubmitting } = useMultiPhaseSubmit({
    projectPath,
    onSuccess,
    onError,
    onFormClear
  });

  /**
   * Open phase preview modal with parsed result
   */
  const openPhasePreview = (parseResult: PhaseParseResult) => {
    setPhasePreview(parseResult);
    setShowPhasePreview(true);
  };

  /**
   * Handle phase preview confirmation - submit multi-phase request
   */
  const handleConfirm = async () => {
    if (!phasePreview) return;

    // Validate phases before proceeding
    const validation = validatePhases(phasePreview);
    if (!validation.valid) {
      onError(`Cannot submit multi-phase document: ${validation.errors.join(', ')}`);
      setShowPhasePreview(false);
      setPhasePreview(null);
      return;
    }

    // Close preview modal
    setShowPhasePreview(false);

    // Submit multi-phase request
    await submitMultiPhase(phasePreview);

    // Clear phase preview state
    setPhasePreview(null);
  };

  /**
   * Handle phase preview cancellation
   */
  const handleCancel = () => {
    setShowPhasePreview(false);
    setPhasePreview(null);
  };

  return {
    openPhasePreview,
    isSubmitting,
    modal: showPhasePreview && phasePreview ? (
      <PhasePreview
        parseResult={phasePreview}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    ) : null
  };
}
