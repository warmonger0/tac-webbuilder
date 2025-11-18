### Workflow 4.2: Migrate Components to Use Formatters and Create Tests
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 4.1

**Input Files:**
- `app/client/src/utils/formatters.ts`
- `app/client/src/components/WorkflowHistoryCard.tsx`
- `app/client/src/components/SimilarWorkflowsComparison.tsx`
- `app/client/src/components/RoutesView.tsx`
- `app/client/src/components/TokenBreakdownChart.tsx`
- `app/client/src/components/CostBreakdownChart.tsx`

**Output Files:**
- All above components (modified)
- `app/client/src/utils/__tests__/formatters.test.ts` (new)

**Tasks:**
1. Create vitest test suite for formatters
2. Write tests for all formatter functions
3. Migrate WorkflowHistoryCard.tsx to use formatters
4. Migrate SimilarWorkflowsComparison.tsx
5. Migrate RoutesView.tsx
6. Migrate TokenBreakdownChart.tsx
7. Migrate CostBreakdownChart.tsx
8. Remove inline formatter functions
9. Run tests and verify UI unchanged

**Test Suite:**
```typescript
// app/client/src/utils/__tests__/formatters.test.ts
import { describe, it, expect } from 'vitest';
import {
  formatDate,
  formatRelativeTime,
  formatDuration,
  formatCost,
  formatNumber,
  formatBytes,
  formatPercentage,
  formatTokenCount
} from '../formatters';

describe('formatters', () => {
  describe('formatDate', () => {
    it('formats date correctly', () => {
      const date = new Date('2025-01-15T10:30:00Z');
      const result = formatDate(date);
      expect(result).toContain('Jan');
      expect(result).toContain('15');
      expect(result).toContain('2025');
    });

    it('handles string input', () => {
      const result = formatDate('2025-01-15T10:30:00Z');
      expect(result).toContain('Jan');
    });
  });

  describe('formatDuration', () => {
    it('formats seconds', () => {
      expect(formatDuration(45)).toBe('45s');
    });

    it('formats minutes and seconds', () => {
      expect(formatDuration(125)).toBe('2m 5s');
    });

    it('formats hours and minutes', () => {
      expect(formatDuration(3665)).toBe('1h 1m');
    });
  });

  describe('formatCost', () => {
    it('formats cost with 4 decimal places', () => {
      expect(formatCost(1.23456)).toContain('1.2346');
    });

    it('handles zero cost', () => {
      expect(formatCost(0)).toContain('0.0000');
    });
  });

  describe('formatNumber', () => {
    it('formats large numbers with commas', () => {
      expect(formatNumber(1234567)).toBe('1,234,567');
    });

    it('handles small numbers', () => {
      expect(formatNumber(42)).toBe('42');
    });
  });

  describe('formatBytes', () => {
    it('formats bytes', () => {
      expect(formatBytes(100)).toBe('100.00 B');
    });

    it('formats kilobytes', () => {
      expect(formatBytes(2048)).toBe('2.00 KB');
    });

    it('formats megabytes', () => {
      expect(formatBytes(5242880)).toBe('5.00 MB');
    });
  });

  describe('formatPercentage', () => {
    it('formats percentage with default decimals', () => {
      expect(formatPercentage(75.5)).toBe('75.5%');
    });

    it('formats percentage with custom decimals', () => {
      expect(formatPercentage(75.567, 2)).toBe('75.57%');
    });
  });

  describe('formatTokenCount', () => {
    it('formats small token counts', () => {
      expect(formatTokenCount(500)).toBe('500');
    });

    it('formats thousands with K suffix', () => {
      expect(formatTokenCount(5000)).toBe('5.0K');
    });

    it('formats millions with M suffix', () => {
      expect(formatTokenCount(2500000)).toBe('2.50M');
    });
  });
});
```

**Component Migration Example:**
```typescript
// Before (in WorkflowHistoryCard.tsx):
function formatDate(date: string): string {
  return new Date(date).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// After:
import { formatDate, formatDuration, formatCost } from '@/utils/formatters';

// Remove local formatter functions
// Use imported formatters throughout component
```

**Acceptance Criteria:**
- [ ] All formatter tests pass
- [ ] Test coverage >90%
- [ ] All components migrated
- [ ] No inline formatter functions remain
- [ ] UI appearance unchanged
- [ ] Code duplication reduced by ~50 lines

**Verification Commands:**
```bash
# Run formatter tests
cd app/client && npm run test -- formatters.test.ts

# Run type check
npm run typecheck

# Build to verify no errors
npm run build

# Visual regression check (manual)
npm run dev
# Navigate to components and verify formatting looks correct
```
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
