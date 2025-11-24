/**
 * Phase Parser Utility
 *
 * Parses multi-phase markdown files to extract individual phases,
 * their content, and external document references.
 */

import {
  PHASE_HEADER_REGEX,
  extractExternalDocs,
  parsePhaseNumber,
} from './phaseUtils';

export interface ParsedPhase {
  number: number;
  title: string;
  content: string;
  rawHeader: string;
  externalDocs: string[];
  startLine: number;
  endLine: number;
}

export interface PhaseParseResult {
  isMultiPhase: boolean;
  phases: ParsedPhase[];
  originalContent: string;
  warnings: string[];
}

/**
 * Parse markdown content to extract phases
 */
export function parsePhases(markdownContent: string): PhaseParseResult {
  const lines = markdownContent.split('\n');
  const phases: ParsedPhase[] = [];
  const warnings: string[] = [];

  let currentPhase: Partial<ParsedPhase> | null = null;
  let phasePosition = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const match = line.match(PHASE_HEADER_REGEX);

    if (match) {
      // Save previous phase if it exists
      if (currentPhase && currentPhase.startLine !== undefined) {
        currentPhase.endLine = i - 1;
        currentPhase.content = lines
          .slice(currentPhase.startLine + 1, i)
          .join('\n')
          .trim();
        currentPhase.externalDocs = extractExternalDocs(currentPhase.content);
        phases.push(currentPhase as ParsedPhase);
      }

      // Start new phase
      phasePosition++;
      // const headerLevel = match[1]; // #, ##, ###, etc. (reserved for future use)
      const phaseNumberText = match[2]; // Could be number or word
      // Clean title: remove leading colons/dashes and trim
      const rawTitle = match[3]?.trim() || '';
      const title = rawTitle.replace(/^[:\-]\s*/, '').trim() || `Phase ${phasePosition}`;
      const phaseNumber = parsePhaseNumber(phaseNumberText, phasePosition);

      currentPhase = {
        number: phaseNumber,
        title,
        rawHeader: line,
        content: '',
        externalDocs: [],
        startLine: i,
        endLine: i
      };

      // Validate phase number sequence
      if (phaseNumber !== phasePosition) {
        warnings.push(
          `Phase ${phaseNumber} appears at position ${phasePosition}. Expected sequential numbering.`
        );
      }
    }
  }

  // Save last phase
  if (currentPhase && currentPhase.startLine !== undefined) {
    currentPhase.endLine = lines.length - 1;
    currentPhase.content = lines
      .slice(currentPhase.startLine + 1)
      .join('\n')
      .trim();
    currentPhase.externalDocs = extractExternalDocs(currentPhase.content);
    phases.push(currentPhase as ParsedPhase);
  }

  // Additional validations
  if (phases.length > 0) {
    // Check if Phase 1 exists
    const hasPhaseOne = phases.some(p => p.number === 1);
    if (!hasPhaseOne) {
      warnings.push('Missing Phase 1. Multi-phase documents should start with Phase 1.');
    }

    // Check for duplicate phase numbers
    const phaseNumbers = phases.map(p => p.number);
    const duplicates = phaseNumbers.filter((num, idx) => phaseNumbers.indexOf(num) !== idx);
    if (duplicates.length > 0) {
      warnings.push(`Duplicate phase numbers detected: ${[...new Set(duplicates)].join(', ')}`);
    }

    // Check for empty phases
    phases.forEach(phase => {
      if (!phase.content || phase.content.length < 10) {
        warnings.push(`Phase ${phase.number} has very little or no content.`);
      }
    });
  }

  return {
    isMultiPhase: phases.length > 1,
    phases,
    originalContent: markdownContent,
    warnings
  };
}

// Re-export for backwards compatibility
export { validatePhases } from './phaseValidator';
export { formatPhaseSummary } from './phaseUtils';
