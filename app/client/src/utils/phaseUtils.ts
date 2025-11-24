/**
 * Phase Utility Functions
 *
 * Helper functions for phase parsing and formatting.
 */

import type { ParsedPhase } from './phaseParser';

/**
 * Flexible phase header patterns:
 * - ## Phase 1: Title
 * - # Phase One - Title
 * - ### Phase: Setup
 * - ## Phase 2
 */
export const PHASE_HEADER_REGEX = /^(#{1,6})\s+Phase\s*[:\-]?\s*(\d+|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)?(?:[:\-]\s*)?(.*)$/im;

/**
 * Extract external document references (e.g., "see ARCHITECTURE.md", "refer to docs/SETUP.md")
 * Matches: "see FILE.md", "refer to docs/FILE.md", "reference the FILE.md", etc.
 */
export const EXTERNAL_DOC_REGEX = /(?:see|refer to|reference|referenced in|mentioned in|from)(?:\s+the)?\s+([a-zA-Z0-9_\-\/\.]+\.md)/gi;

/**
 * Word-to-number mapping for phase numbers
 */
const WORD_TO_NUMBER: Record<string, number> = {
  'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
  'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
};

/**
 * Parse phase number from text (supports numeric and word forms)
 */
export function parsePhaseNumber(text: string | undefined, position: number): number {
  if (!text) return position;

  const numeric = parseInt(text, 10);
  if (!isNaN(numeric)) return numeric;

  const lowerText = text.toLowerCase();
  return WORD_TO_NUMBER[lowerText] || position;
}

/**
 * Extract external document references from content
 */
export function extractExternalDocs(content: string): string[] {
  const docs = new Set<string>();
  let match;

  // Reset regex lastIndex
  const regex = new RegExp(EXTERNAL_DOC_REGEX.source, EXTERNAL_DOC_REGEX.flags);

  while ((match = regex.exec(content)) !== null) {
    docs.add(match[1]);
  }

  return Array.from(docs);
}

/**
 * Format phase summary for display
 */
export function formatPhaseSummary(phase: ParsedPhase): string {
  const docRefs = phase.externalDocs.length > 0
    ? ` (refs: ${phase.externalDocs.join(', ')})`
    : '';
  const contentPreview = phase.content.substring(0, 100).replace(/\n/g, ' ');
  return `Phase ${phase.number}: ${phase.title}${docRefs}\n${contentPreview}...`;
}
