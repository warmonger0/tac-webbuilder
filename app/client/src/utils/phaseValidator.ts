/**
 * Phase Validator
 *
 * Validates parsed phases for correctness and completeness.
 */

import type { PhaseParseResult } from './phaseParser';

/**
 * Validate that phases can be processed
 */
export function validatePhases(parseResult: PhaseParseResult): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!parseResult.isMultiPhase) {
    return { valid: true, errors: [] }; // Single-phase is always valid
  }

  if (parseResult.phases.length === 0) {
    errors.push('No phases detected in the markdown file.');
    return { valid: false, errors };
  }

  // Check for Phase 1
  const hasPhaseOne = parseResult.phases.some(p => p.number === 1);
  if (!hasPhaseOne) {
    errors.push('Multi-phase documents must include Phase 1.');
  }

  // Check phase sequence
  const sortedPhases = [...parseResult.phases].sort((a, b) => a.number - b.number);
  for (let i = 0; i < sortedPhases.length - 1; i++) {
    const currentNum = sortedPhases[i].number;
    const nextNum = sortedPhases[i + 1].number;

    if (nextNum - currentNum > 1) {
      errors.push(`Gap in phase sequence: Phase ${currentNum} is followed by Phase ${nextNum}.`);
    }
  }

  // Limit to reasonable number of phases
  if (parseResult.phases.length > 20) {
    errors.push(`Too many phases (${parseResult.phases.length}). Maximum is 20 phases.`);
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Validate phase warnings from parse result
 */
export function getPhaseWarnings(parseResult: PhaseParseResult): string[] {
  const warnings: string[] = [...parseResult.warnings];

  if (parseResult.phases.length > 0) {
    // Check if Phase 1 exists
    const hasPhaseOne = parseResult.phases.some(p => p.number === 1);
    if (!hasPhaseOne) {
      warnings.push('Missing Phase 1. Multi-phase documents should start with Phase 1.');
    }

    // Check for duplicate phase numbers
    const phaseNumbers = parseResult.phases.map(p => p.number);
    const duplicates = phaseNumbers.filter((num, idx) => phaseNumbers.indexOf(num) !== idx);
    if (duplicates.length > 0) {
      warnings.push(`Duplicate phase numbers detected: ${[...new Set(duplicates)].join(', ')}`);
    }

    // Check for empty phases
    parseResult.phases.forEach(phase => {
      if (!phase.content || phase.content.length < 10) {
        warnings.push(`Phase ${phase.number} has very little or no content.`);
      }
    });
  }

  return warnings;
}
