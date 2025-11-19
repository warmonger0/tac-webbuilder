import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { PhaseCost } from '../types';

interface CostBreakdownChartProps {
  phases: PhaseCost[];
}

export function CostBreakdownChart({ phases }: CostBreakdownChartProps) {
  if (!phases || phases.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No cost data available
      </div>
    );
  }

  // Map phase names to colors (consistent with StatusBadge)
  const getPhaseColor = (phase: string): string => {
    const phaseLower = phase.toLowerCase();
    if (phaseLower.includes('plan')) return '#3B82F6'; // blue
    if (phaseLower.includes('build')) return '#A855F7'; // purple
    if (phaseLower.includes('test')) return '#EAB308'; // yellow
    if (phaseLower.includes('review')) return '#F97316'; // orange
    if (phaseLower.includes('document')) return '#6366F1'; // indigo
    if (phaseLower.includes('ship')) return '#10B981'; // green
    return '#6B7280'; // gray
  };

  // Format data for Recharts
  const chartData = phases.map((phase) => ({
    phase: phase.phase,
    cost: parseFloat(phase.cost.toFixed(4)),
    color: getPhaseColor(phase.phase),
  }));

  // Custom tooltip to show detailed token breakdown
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const phaseData = phases.find((p) => p.phase === data.phase);

      if (!phaseData) return null;

      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg text-xs">
          <p className="font-semibold mb-2">{data.phase}</p>
          <p className="text-gray-700">Cost: ${data.cost.toFixed(4)}</p>
          <div className="mt-2 pt-2 border-t border-gray-200">
            <p className="font-medium mb-1">Token Breakdown:</p>
            <p className="text-gray-600">
              Input: {phaseData.tokens.input_tokens.toLocaleString()}
            </p>
            <p className="text-gray-600">
              Cache Write: {phaseData.tokens.cache_creation_tokens.toLocaleString()}
            </p>
            <p className="text-gray-600">
              Cache Read: {phaseData.tokens.cache_read_tokens.toLocaleString()}
            </p>
            <p className="text-gray-600">
              Output: {phaseData.tokens.output_tokens.toLocaleString()}
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full">
      <h3 className="text-sm font-semibold mb-3 text-gray-700">
        Cost Breakdown by Phase
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey="phase"
            tick={{ fontSize: 12 }}
            stroke="#6B7280"
          />
          <YAxis
            tick={{ fontSize: 12 }}
            stroke="#6B7280"
            label={{
              value: 'Cost ($)',
              angle: -90,
              position: 'insideLeft',
              style: { fontSize: 12, fill: '#6B7280' },
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="cost" radius={[8, 8, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
