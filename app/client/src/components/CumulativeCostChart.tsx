import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { PhaseCost } from '../types';

interface CumulativeCostChartProps {
  phases: PhaseCost[];
}

export function CumulativeCostChart({ phases }: CumulativeCostChartProps) {
  if (!phases || phases.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No cost data available
      </div>
    );
  }

  // Calculate cumulative costs
  let cumulative = 0;
  const chartData = phases.map((phase) => {
    cumulative += phase.cost;
    return {
      phase: phase.phase,
      cumulativeCost: parseFloat(cumulative.toFixed(4)),
    };
  });

  const totalCost = cumulative;

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg text-xs">
          <p className="font-semibold mb-1">{data.phase}</p>
          <p className="text-gray-700">
            Cumulative: ${data.cumulativeCost.toFixed(4)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700">
          Cumulative Cost Progression
        </h3>
        <span className="text-sm font-medium text-gray-600">
          Total: ${totalCost.toFixed(4)}
        </span>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <defs>
            <linearGradient id="costGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1} />
            </linearGradient>
          </defs>
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
              value: 'Cumulative Cost ($)',
              angle: -90,
              position: 'insideLeft',
              style: { fontSize: 12, fill: '#6B7280' },
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="cumulativeCost"
            stroke="#3B82F6"
            strokeWidth={2}
            fill="url(#costGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
