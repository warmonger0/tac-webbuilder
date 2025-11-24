/**
 * Phase Parser Utility
 *
 * Parses multi-phase markdown files to extract individual phases,
 * their content, and external document references.
 */

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
 * Flexible phase header patterns:
 * - ## Phase 1: Title
 * - # Phase One - Title
 * - ### Phase: Setup
 * - ## Phase 2
 */
const PHASE_HEADER_REGEX = /^(#{1,6})\s+Phase\s*[:\-]?\s*(\d+|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)?(?:[:\-]\s*)?(.*)$/im;

/**
 * Extract external document references (e.g., "see ARCHITECTURE.md", "refer to docs/SETUP.md")
 * Matches: "see FILE.md", "refer to docs/FILE.md", "reference the FILE.md", etc.
 */
const EXTERNAL_DOC_REGEX = /(?:see|refer to|reference|referenced in|mentioned in|from)(?:\s+the)?\s+([a-zA-Z0-9_\-\/\.]+\.md)/gi;

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
function parsePhaseNumber(text: string | undefined, position: number): number {
  if (!text) return position;

  const numeric = parseInt(text, 10);
  if (!isNaN(numeric)) return numeric;

  const lowerText = text.toLowerCase();
  return WORD_TO_NUMBER[lowerText] || position;
}

/**
 * Extract external document references from content
 */
function extractExternalDocs(content: string): string[] {
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
 * Format phase summary for display
 */
export function formatPhaseSummary(phase: ParsedPhase): string {
  const docRefs = phase.externalDocs.length > 0
    ? ` (refs: ${phase.externalDocs.join(', ')})`
    : '';
  const contentPreview = phase.content.substring(0, 100).replace(/\n/g, ' ');
  return `Phase ${phase.number}: ${phase.title}${docRefs}\n${contentPreview}...`;
}
