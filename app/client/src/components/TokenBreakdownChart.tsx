import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

interface TokenBreakdownChartProps {
  inputTokens: number;
  outputTokens: number;
  cachedTokens: number;
  cacheHitTokens: number;
  cacheMissTokens: number;
  totalTokens: number;
}

export function TokenBreakdownChart({
  inputTokens,
  outputTokens,
  cacheHitTokens,
  cacheMissTokens,
  totalTokens,
}: TokenBreakdownChartProps) {
  // Format token count with K/M notation
  const formatTokenCount = (num: number): string => {
    if (num === 0) return '0';
    if (num < 1000) return num.toString();
    if (num < 1000000) {
      const k = num / 1000;
      return `${k.toFixed(k >= 100 ? 0 : 1)}K`;
    }
    const m = num / 1000000;
    return `${m.toFixed(m >= 100 ? 0 : 1)}M`;
  };

  // Check if we have any data
  if (!totalTokens || totalTokens === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500 border border-gray-200 rounded-lg bg-gray-50">
        No token data available
      </div>
    );
  }

  // Prepare data for the chart
  const chartData = [
    {
      name: 'Cache Hit',
      value: cacheHitTokens,
      color: '#10B981',
      description: 'Cache hits (90% cheaper)',
    },
    {
      name: 'Cache Miss',
      value: cacheMissTokens,
      color: '#F97316',
      description: 'Cache misses (full cost)',
    },
    {
      name: 'Input',
      value: inputTokens,
      color: '#3B82F6',
      description: 'Input tokens',
    },
    {
      name: 'Output',
      value: outputTokens,
      color: '#A855F7',
      description: 'Output tokens',
    },
  ].filter((item) => item.value > 0); // Only show non-zero values

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      const percentage = ((data.value / totalTokens) * 100).toFixed(1);
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg text-xs">
          <p className="font-semibold mb-1" style={{ color: data.payload.color }}>
            {data.name}
          </p>
          <p className="text-gray-700">
            Tokens: {data.value.toLocaleString()} ({percentage}%)
          </p>
          <p className="text-gray-600 text-xs mt-1">{data.payload.description}</p>
        </div>
      );
    }
    return null;
  };

  // Custom label for the pie chart
  const renderLabel = (entry: any) => {
    const percentage = ((entry.value / totalTokens) * 100).toFixed(0);
    if (parseFloat(percentage) < 5) return ''; // Don't show label for small segments
    return `${percentage}%`;
  };

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700">Token Breakdown</h3>
        <span className="text-sm font-medium text-gray-600">
          Total: {formatTokenCount(totalTokens)}
        </span>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderLabel}
            outerRadius={100}
            innerRadius={60}
            fill="#8884d8"
            dataKey="value"
            paddingAngle={2}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value, entry: any) => (
              <span className="text-xs text-gray-700">
                {value}: {formatTokenCount(entry.payload.value)}
              </span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
