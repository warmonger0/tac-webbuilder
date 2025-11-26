import React from 'react';
import { PatternPrediction } from '@/types/api.types';
import {
  formatPatternSignature,
  formatConfidence,
  getConfidenceColor,
  getConfidenceLabel,
} from '@/utils/patternFormatters';

interface PatternBadgeProps {
  prediction: PatternPrediction;
}

/**
 * PatternBadge component displays a predicted pattern with confidence score
 *
 * Visualizes pattern predictions with color-coded badges:
 * - Green: High confidence (≥75%)
 * - Yellow: Medium confidence (50-74%)
 * - Gray: Low confidence (<50%)
 */
export default function PatternBadge({ prediction }: PatternBadgeProps) {
  const formattedPattern = formatPatternSignature(prediction.pattern);
  const confidencePercent = formatConfidence(prediction.confidence);
  const confidenceLabel = getConfidenceLabel(prediction.confidence);
  const colorClasses = getConfidenceColor(prediction.confidence);

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border ${colorClasses} text-sm font-medium`}
      title={prediction.reasoning}
    >
      <span>{formattedPattern}</span>
      <span className="text-xs opacity-75">
        {confidencePercent} {confidenceLabel}
      </span>
    </div>
  );
}
