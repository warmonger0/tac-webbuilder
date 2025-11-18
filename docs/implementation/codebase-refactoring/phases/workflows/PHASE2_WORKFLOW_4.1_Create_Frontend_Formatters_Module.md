### Workflow 4.1: Create Frontend Formatters Module
**Estimated Time:** 2 hours
**Complexity:** Low
**Dependencies:** None

**Input Files:**
- `app/client/src/components/WorkflowHistoryCard.tsx` (formatter examples)
- `app/client/src/components/SimilarWorkflowsComparison.tsx` (formatter examples)

**Output Files:**
- `app/client/src/utils/formatters.ts` (new)

**Tasks:**
1. Create formatDate() function
2. Create formatRelativeTime() function
3. Create formatDuration() function
4. Create formatCost() function
5. Create formatNumber() function
6. Create formatBytes() function
7. Create formatPercentage() function
8. Create formatTokenCount() function
9. Add JSDoc comments to all functions

**Implementation:**
```typescript
/**
 * Format date to human-readable string
 *
 * @param date - Date string or Date object
 * @returns Formatted date string (e.g., "Jan 15, 2025, 10:30 AM")
 *
 * @example
 * formatDate('2025-01-15T10:30:00Z') // "Jan 15, 2025, 10:30 AM"
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * Format timestamp to relative time
 *
 * @param date - Date string or Date object
 * @returns Relative time string (e.g., "2 hours ago")
 *
 * @example
 * formatRelativeTime(new Date(Date.now() - 7200000)) // "2 hours ago"
 */
export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffDay > 0) return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;
  if (diffHour > 0) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
  if (diffMin > 0) return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
  return 'just now';
}

/**
 * Format duration in seconds to human-readable string
 *
 * @param seconds - Duration in seconds
 * @returns Formatted duration (e.g., "2m 30s", "1h 15m")
 *
 * @example
 * formatDuration(150) // "2m 30s"
 * formatDuration(3665) // "1h 1m"
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  }
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
}

/**
 * Format cost to currency string
 *
 * @param cost - Cost in dollars
 * @param currency - Currency code (default: 'USD')
 * @returns Formatted currency string (e.g., "$1.2345")
 *
 * @example
 * formatCost(1.23456) // "$1.2346"
 */
export function formatCost(cost: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 4,
    maximumFractionDigits: 4
  }).format(cost);
}

/**
 * Format large numbers with commas
 *
 * @param num - Number to format
 * @returns Formatted number string (e.g., "1,234,567")
 *
 * @example
 * formatNumber(1234567) // "1,234,567"
 */
export function formatNumber(num: number): string {
  return num.toLocaleString('en-US');
}

/**
 * Format bytes to human-readable size
 *
 * @param bytes - Size in bytes
 * @returns Formatted size string (e.g., "1.50 MB")
 *
 * @example
 * formatBytes(1572864) // "1.50 MB"
 */
export function formatBytes(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(2)} ${units[unitIndex]}`;
}

/**
 * Format percentage
 *
 * @param value - Percentage value
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted percentage string (e.g., "75.5%")
 *
 * @example
 * formatPercentage(75.567, 2) // "75.57%"
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Format token count with K/M suffixes
 *
 * @param tokens - Token count
 * @returns Formatted token count (e.g., "1.5K", "2.50M")
 *
 * @example
 * formatTokenCount(1500) // "1.5K"
 * formatTokenCount(2500000) // "2.50M"
 */
export function formatTokenCount(tokens: number): string {
  if (tokens < 1000) return tokens.toString();
  if (tokens < 1000000) return `${(tokens / 1000).toFixed(1)}K`;
  return `${(tokens / 1000000).toFixed(2)}M`;
}
```

**Acceptance Criteria:**
- [ ] All formatter functions created
- [ ] All functions have JSDoc comments
- [ ] All functions have examples
- [ ] Type safety with TypeScript
- [ ] Proper number formatting with Intl API

**Verification Command:**
```bash
cd app/client && npm run typecheck
```
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
