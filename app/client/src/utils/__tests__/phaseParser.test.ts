/**
 * Unit tests for phase parser utility
 * Tests phase detection, validation, and external document extraction
 */

import { describe, it, expect } from 'vitest';
import { parsePhases, validatePhases, formatPhaseSummary } from '../phaseParser';

describe('parsePhases', () => {
  describe('Single-phase documents', () => {
    it('should detect single-phase document as not multi-phase', () => {
      const markdown = `
# My Project

This is a single-phase document.

## Phase 1: Implementation

Build the feature.
      `;

      const result = parsePhases(markdown);
      expect(result.isMultiPhase).toBe(false);
      expect(result.phases).toHaveLength(1);
    });

    it('should handle documents with no phases', () => {
      const markdown = `
# Regular Document

This document has no phases at all.

## Section 1
Some content here.
      `;

      const result = parsePhases(markdown);
      expect(result.isMultiPhase).toBe(false);
      expect(result.phases).toHaveLength(0);
    });
  });

  describe('Multi-phase documents', () => {
    it('should detect strict pattern multi-phase document', () => {
      const markdown = `
# Project Plan

## Phase 1: Foundation
Build the basic structure.

## Phase 2: Implementation
Add the main features.

## Phase 3: Testing
Write tests.
      `;

      const result = parsePhases(markdown);
      expect(result.isMultiPhase).toBe(true);
      expect(result.phases).toHaveLength(3);
      expect(result.phases[0].number).toBe(1);
      expect(result.phases[0].title).toBe('Foundation');
      expect(result.phases[1].number).toBe(2);
      expect(result.phases[1].title).toBe('Implementation');
      expect(result.phases[2].number).toBe(3);
      expect(result.phases[2].title).toBe('Testing');
    });

    it('should handle flexible phase patterns', () => {
      const markdown = `
# Project

# Phase One - Setup
Initial setup work.

### Phase: Configuration
Configure the system.

## Phase 3
Final steps.
      `;

      const result = parsePhases(markdown);
      expect(result.isMultiPhase).toBe(true);
      expect(result.phases).toHaveLength(3);
      expect(result.phases[0].number).toBe(1); // "One" converted to 1
      expect(result.phases[0].title).toBe('Setup');
      expect(result.phases[1].number).toBe(2); // Position-based
      expect(result.phases[1].title).toBe('Configuration');
      expect(result.phases[2].number).toBe(3);
      expect(result.phases[2].title).toBe('Phase 3'); // No title provided
    });

    it('should handle phases with colons and dashes', () => {
      const markdown = `
## Phase 1: Foundation
Content 1

## Phase 2 - Implementation
Content 2

## Phase: Review
Content 3
      `;

      const result = parsePhases(markdown);
      expect(result.isMultiPhase).toBe(true);
      expect(result.phases).toHaveLength(3);
      expect(result.phases[0].title).toBe('Foundation');
      expect(result.phases[1].title).toBe('Implementation');
      expect(result.phases[2].title).toBe('Review');
    });
  });

  describe('Phase content extraction', () => {
    it('should extract content between phases correctly', () => {
      const markdown = `
## Phase 1: First
This is phase 1 content.
It has multiple lines.

## Phase 2: Second
This is phase 2 content.
      `;

      const result = parsePhases(markdown);
      expect(result.phases[0].content).toContain('This is phase 1 content');
      expect(result.phases[0].content).toContain('It has multiple lines');
      expect(result.phases[1].content).toContain('This is phase 2 content');
    });

    it('should track line numbers correctly', () => {
      const markdown = `Line 1
## Phase 1: First
Line 3
Line 4
## Phase 2: Second
Line 6`;

      const result = parsePhases(markdown);
      expect(result.phases[0].startLine).toBe(1); // 0-indexed line where ## Phase 1 appears
      expect(result.phases[1].startLine).toBe(4);
    });
  });

  describe('External document references', () => {
    it('should extract external document references', () => {
      const markdown = `
## Phase 1: Setup
See the ARCHITECTURE.md file for details.
Refer to docs/SETUP.md for installation.

## Phase 2: Build
Reference implementation from EXAMPLES.md.
      `;

      const result = parsePhases(markdown);
      expect(result.phases[0].externalDocs).toContain('ARCHITECTURE.md');
      expect(result.phases[0].externalDocs).toContain('docs/SETUP.md');
      expect(result.phases[1].externalDocs).toContain('EXAMPLES.md');
    });

    it('should handle multiple reference patterns', () => {
      const markdown = `
## Phase 1: Research
see CONFIG.md
refer to docs/API.md
reference the SCHEMA.md
mentioned in DESIGN.md
from REQUIREMENTS.md
      `;

      const result = parsePhases(markdown);
      expect(result.phases[0].externalDocs).toHaveLength(5);
      expect(result.phases[0].externalDocs).toContain('CONFIG.md');
      expect(result.phases[0].externalDocs).toContain('docs/API.md');
      expect(result.phases[0].externalDocs).toContain('SCHEMA.md');
    });

    it('should not extract false positives', () => {
      const markdown = `
## Phase 1: Test
This is a test.md but not a reference.
The word see alone shouldn't trigger.
      `;

      const result = parsePhases(markdown);
      expect(result.phases[0].externalDocs).toHaveLength(0);
    });
  });

  describe('Validation warnings', () => {
    it('should warn about missing Phase 1', () => {
      const markdown = `
## Phase 2: Second
Content

## Phase 3: Third
Content
      `;

      const result = parsePhases(markdown);
      expect(result.warnings.length).toBeGreaterThan(0);
      expect(result.warnings.some(w => w.includes('Phase 1'))).toBe(true);
    });

    it('should warn about out-of-sequence phases', () => {
      const markdown = `
## Phase 1: First
Content

## Phase 5: Fifth
Content
      `;

      const result = parsePhases(markdown);
      expect(result.warnings.length).toBeGreaterThan(0);
      expect(result.warnings.some(w => w.includes('position'))).toBe(true);
    });

    it('should warn about duplicate phase numbers', () => {
      const markdown = `
## Phase 1: First
Content

## Phase 1: Also First
Content
      `;

      const result = parsePhases(markdown);
      expect(result.warnings.length).toBeGreaterThan(0);
      expect(result.warnings.some(w => w.includes('Duplicate'))).toBe(true);
    });

    it('should warn about empty phases', () => {
      const markdown = `
## Phase 1: First

## Phase 2: Second
Actual content here
      `;

      const result = parsePhases(markdown);
      expect(result.warnings.length).toBeGreaterThan(0);
      expect(result.warnings.some(w => w.includes('little or no content'))).toBe(true);
    });
  });

  describe('Word-to-number conversion', () => {
    it('should convert word phase numbers to integers', () => {
      const markdown = `
## Phase One: First
## Phase Two: Second
## Phase Three: Third
## Phase Four: Fourth
## Phase Five: Fifth
      `;

      const result = parsePhases(markdown);
      expect(result.phases[0].number).toBe(1);
      expect(result.phases[1].number).toBe(2);
      expect(result.phases[2].number).toBe(3);
      expect(result.phases[3].number).toBe(4);
      expect(result.phases[4].number).toBe(5);
    });

    it('should handle mixed numeric and word patterns', () => {
      const markdown = `
## Phase 1: First
## Phase Two: Second
## Phase 3: Third
      `;

      const result = parsePhases(markdown);
      expect(result.phases[0].number).toBe(1);
      expect(result.phases[1].number).toBe(2);
      expect(result.phases[2].number).toBe(3);
    });
  });
});

describe('validatePhases', () => {
  it('should validate single-phase documents as always valid', () => {
    const parseResult = {
      isMultiPhase: false,
      phases: [{ number: 1, title: 'Test', content: 'Content', rawHeader: '## Phase 1', externalDocs: [], startLine: 0, endLine: 5 }],
      originalContent: 'Test',
      warnings: []
    };

    const validation = validatePhases(parseResult);
    expect(validation.valid).toBe(true);
    expect(validation.errors).toHaveLength(0);
  });

  it('should require Phase 1 for multi-phase documents', () => {
    const parseResult = {
      isMultiPhase: true,
      phases: [
        { number: 2, title: 'Second', content: 'Content', rawHeader: '## Phase 2', externalDocs: [], startLine: 0, endLine: 5 }
      ],
      originalContent: 'Test',
      warnings: []
    };

    const validation = validatePhases(parseResult);
    expect(validation.valid).toBe(false);
    expect(validation.errors.some(e => e.includes('Phase 1'))).toBe(true);
  });

  it('should detect gaps in phase sequence', () => {
    const parseResult = {
      isMultiPhase: true,
      phases: [
        { number: 1, title: 'First', content: 'Content', rawHeader: '## Phase 1', externalDocs: [], startLine: 0, endLine: 5 },
        { number: 3, title: 'Third', content: 'Content', rawHeader: '## Phase 3', externalDocs: [], startLine: 6, endLine: 10 }
      ],
      originalContent: 'Test',
      warnings: []
    };

    const validation = validatePhases(parseResult);
    expect(validation.valid).toBe(false);
    expect(validation.errors.some(e => e.includes('Gap in phase sequence'))).toBe(true);
  });

  it('should reject documents with too many phases', () => {
    const phases = Array.from({ length: 25 }, (_, i) => ({
      number: i + 1,
      title: `Phase ${i + 1}`,
      content: 'Content',
      rawHeader: `## Phase ${i + 1}`,
      externalDocs: [],
      startLine: i * 2,
      endLine: i * 2 + 1
    }));

    const parseResult = {
      isMultiPhase: true,
      phases,
      originalContent: 'Test',
      warnings: []
    };

    const validation = validatePhases(parseResult);
    expect(validation.valid).toBe(false);
    expect(validation.errors.some(e => e.includes('Too many phases'))).toBe(true);
  });

  it('should validate properly structured multi-phase document', () => {
    const parseResult = {
      isMultiPhase: true,
      phases: [
        { number: 1, title: 'First', content: 'Content', rawHeader: '## Phase 1', externalDocs: [], startLine: 0, endLine: 5 },
        { number: 2, title: 'Second', content: 'Content', rawHeader: '## Phase 2', externalDocs: [], startLine: 6, endLine: 10 },
        { number: 3, title: 'Third', content: 'Content', rawHeader: '## Phase 3', externalDocs: [], startLine: 11, endLine: 15 }
      ],
      originalContent: 'Test',
      warnings: []
    };

    const validation = validatePhases(parseResult);
    expect(validation.valid).toBe(true);
    expect(validation.errors).toHaveLength(0);
  });
});

describe('formatPhaseSummary', () => {
  it('should format phase summary with title and preview', () => {
    const phase = {
      number: 1,
      title: 'Foundation',
      content: 'This is a longer piece of content that should be truncated in the preview to show only the first 100 characters or so.',
      rawHeader: '## Phase 1: Foundation',
      externalDocs: [],
      startLine: 0,
      endLine: 5
    };

    const summary = formatPhaseSummary(phase);
    expect(summary).toContain('Phase 1: Foundation');
    expect(summary).toContain('This is a longer piece');
    expect(summary).toContain('...');
  });

  it('should include external document references in summary', () => {
    const phase = {
      number: 2,
      title: 'Implementation',
      content: 'Build the feature.',
      rawHeader: '## Phase 2: Implementation',
      externalDocs: ['ARCHITECTURE.md', 'API.md'],
      startLine: 0,
      endLine: 5
    };

    const summary = formatPhaseSummary(phase);
    expect(summary).toContain('refs: ARCHITECTURE.md, API.md');
  });

  it('should handle phases without external docs', () => {
    const phase = {
      number: 1,
      title: 'Simple',
      content: 'Simple content.',
      rawHeader: '## Phase 1: Simple',
      externalDocs: [],
      startLine: 0,
      endLine: 5
    };

    const summary = formatPhaseSummary(phase);
    expect(summary).toContain('Phase 1: Simple');
    expect(summary).not.toContain('refs:');
  });
});

describe('Edge cases', () => {
  it('should handle empty markdown', () => {
    const result = parsePhases('');
    expect(result.isMultiPhase).toBe(false);
    expect(result.phases).toHaveLength(0);
  });

  it('should handle markdown with only whitespace', () => {
    const result = parsePhases('   \n\n  \t  \n   ');
    expect(result.isMultiPhase).toBe(false);
    expect(result.phases).toHaveLength(0);
  });

  it('should handle phases with special characters in titles', () => {
    const markdown = `
## Phase 1: Setup & Configuration
Content

## Phase 2: Build/Test/Deploy
Content
    `;

    const result = parsePhases(markdown);
    expect(result.phases[0].title).toBe('Setup & Configuration');
    expect(result.phases[1].title).toBe('Build/Test/Deploy');
  });

  it('should handle very long phase content', () => {
    const longContent = 'x'.repeat(10000);
    const markdown = `
## Phase 1: Long
${longContent}

## Phase 2: Short
Short content
    `;

    const result = parsePhases(markdown);
    expect(result.phases[0].content).toHaveLength(10000);
    expect(result.phases[1].content).toContain('Short content');
  });

  it('should handle case-insensitive word numbers', () => {
    const markdown = `
## Phase ONE: First
## Phase Two: Second
## Phase THREE: Third
    `;

    const result = parsePhases(markdown);
    expect(result.phases[0].number).toBe(1);
    expect(result.phases[1].number).toBe(2);
    expect(result.phases[2].number).toBe(3);
  });
});
