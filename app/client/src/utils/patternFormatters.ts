/**
 * Pattern formatting utilities
 *
 * Functions for formatting pattern signatures into human-readable strings
 * and determining confidence-based color coding.
 */

/**
 * Formats a pattern signature into a human-readable string
 *
 * @param pattern - Pattern signature (e.g., "test:pytest:backend")
 * @returns Formatted string (e.g., "Backend Pytest Testing")
 *
 * @example
 * formatPatternSignature("test:pytest:backend") // "Backend Pytest Testing"
 * formatPatternSignature("build:typecheck:frontend") // "Frontend Typecheck Build"
 */
export function formatPatternSignature(pattern: string): string {
  const parts = pattern.split(':');

  if (parts.length === 0) return pattern;

  // Capitalize each part and reverse order for better readability
  const formatted = parts
    .reverse()
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');

  return formatted;
}

/**
 * Gets a Tailwind color class based on confidence score
 *
 * @param confidence - Confidence score (0.0-1.0)
 * @returns Tailwind color class
 *
 * High confidence (≥0.75): green
 * Medium confidence (0.5-0.74): yellow
 * Low confidence (<0.5): gray
 *
 * @example
 * getConfidenceColor(0.85) // "bg-green-100 text-green-800 border-green-300"
 * getConfidenceColor(0.65) // "bg-yellow-100 text-yellow-800 border-yellow-300"
 * getConfidenceColor(0.35) // "bg-gray-100 text-gray-800 border-gray-300"
 */
export function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.75) {
    return 'bg-green-100 text-green-800 border-green-300';
  } else if (confidence >= 0.5) {
    return 'bg-yellow-100 text-yellow-800 border-yellow-300';
  } else {
    return 'bg-gray-100 text-gray-800 border-gray-300';
  }
}

/**
 * Gets a confidence label based on confidence score
 *
 * @param confidence - Confidence score (0.0-1.0)
 * @returns Confidence label ("High", "Medium", or "Low")
 *
 * @example
 * getConfidenceLabel(0.85) // "High"
 * getConfidenceLabel(0.65) // "Medium"
 * getConfidenceLabel(0.35) // "Low"
 */
export function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.75) {
    return 'High';
  } else if (confidence >= 0.5) {
    return 'Medium';
  } else {
    return 'Low';
  }
}

/**
 * Formats a confidence percentage for display
 *
 * @param confidence - Confidence score (0.0-1.0)
 * @returns Formatted percentage string (e.g., "85%")
 *
 * @example
 * formatConfidence(0.8547) // "85%"
 */
export function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}
