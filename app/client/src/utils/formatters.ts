/**
 * Format a duration in seconds to a human-readable string
 * @param seconds - Duration in seconds (null returns 'N/A')
 * @returns Formatted duration string (e.g., "2h 30m", "45m 12s", "30s")
 */
export function formatDuration(seconds: number | null): string {
  if (!seconds) return 'N/A';
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  if (hours > 0) return `${hours}h ${mins}m`;
  if (mins > 0) return `${mins}m ${secs}s`;
  return `${secs}s`;
}

/**
 * Format a cost value to a currency string
 * @param cost - Cost in dollars (null returns '$0.00')
 * @returns Formatted cost string (e.g., "$12.45", "$0.00")
 */
export function formatCost(cost: number | null): string {
  if (!cost) return '$0.00';
  return `$${cost.toFixed(2)}`;
}
