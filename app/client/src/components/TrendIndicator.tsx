import { formatPercentChange, getTrendArrow, getTrendColor } from '../utils/trendCalculations';

interface TrendIndicatorProps {
  percentChange: number;
  trend: 'up' | 'down' | 'neutral';
  invertColors?: boolean;
  ariaLabel?: string;
}

/**
 * Reusable trend indicator component with arrow and percentage display.
 *
 * Shows visual feedback for trends with appropriate colors and arrows:
 * - Up trend: ↑ with red (if inverted for costs) or green
 * - Down trend: ↓ with green (if inverted for costs) or red
 * - Neutral: → with gray
 */
export function TrendIndicator({ percentChange, trend, invertColors = false, ariaLabel }: TrendIndicatorProps) {
  const colorClass = getTrendColor(trend, invertColors);
  const arrow = getTrendArrow(trend);
  const formattedChange = formatPercentChange(percentChange);

  const defaultAriaLabel = ariaLabel || `${trend} by ${Math.abs(percentChange).toFixed(1)}%`;

  return (
    <span className={`inline-flex items-center gap-1 text-sm font-medium ${colorClass}`} aria-label={defaultAriaLabel}>
      <span className="text-base" aria-hidden="true">
        {arrow}
      </span>
      <span>{formattedChange}</span>
    </span>
  );
}
