/**
 * Trend calculation utilities for cost metrics and analytics.
 *
 * Provides helpers for calculating percentage changes, determining trend directions,
 * formatting trend values, and selecting appropriate colors for visualization.
 */

/**
 * Calculate percentage change between current and previous values.
 *
 * @param current - Current value
 * @param previous - Previous value for comparison
 * @returns Percentage change (e.g., 5.2 for 5.2% increase, -3.1 for 3.1% decrease)
 */
export function calculatePercentChange(current: number, previous: number): number {
  if (previous === 0) {
    return current === 0 ? 0 : 100;
  }
  return ((current - previous) / previous) * 100;
}

/**
 * Determine trend direction based on percentage change.
 *
 * Uses ±1% threshold to avoid noise from small fluctuations.
 *
 * @param percentChange - Percentage change value
 * @returns Trend direction: 'up' (>1%), 'down' (<-1%), or 'neutral' (±1%)
 */
export function getTrendDirection(percentChange: number): 'up' | 'down' | 'neutral' {
  if (percentChange > 1.0) return 'up';
  if (percentChange < -1.0) return 'down';
  return 'neutral';
}

/**
 * Format percentage change as a display string.
 *
 * @param percentChange - Percentage change value
 * @returns Formatted string (e.g., "+5.2%", "-3.1%", "0.0%")
 */
export function formatPercentChange(percentChange: number): string {
  const sign = percentChange > 0 ? '+' : '';
  return `${sign}${percentChange.toFixed(1)}%`;
}

/**
 * Get Tailwind CSS color class for trend visualization.
 *
 * @param trend - Trend direction
 * @param invertColors - If true, 'down' is green (good for costs), 'up' is red
 * @returns Tailwind color class string
 */
export function getTrendColor(trend: 'up' | 'down' | 'neutral', invertColors: boolean = false): string {
  if (trend === 'neutral') return 'text-gray-600';

  if (invertColors) {
    // For costs: down is good (green), up is bad (red)
    return trend === 'down' ? 'text-green-600' : 'text-red-600';
  } else {
    // For metrics: up is good (green), down is bad (red)
    return trend === 'up' ? 'text-green-600' : 'text-red-600';
  }
}

/**
 * Get arrow character for trend direction.
 *
 * @param trend - Trend direction
 * @returns Unicode arrow character
 */
export function getTrendArrow(trend: 'up' | 'down' | 'neutral'): string {
  if (trend === 'up') return '↑';
  if (trend === 'down') return '↓';
  return '→';
}
