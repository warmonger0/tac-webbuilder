interface CacheEfficiencyBadgeProps {
  cacheEfficiencyPercent: number;
  cacheSavingsAmount: number;
}

export function CacheEfficiencyBadge({
  cacheEfficiencyPercent,
  cacheSavingsAmount,
}: CacheEfficiencyBadgeProps) {
  const getEfficiencyColor = (efficiency: number) => {
    if (efficiency >= 80) return 'bg-green-100 text-green-800 border-green-200';
    if (efficiency >= 60) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    if (efficiency >= 40) return 'bg-orange-100 text-orange-800 border-orange-200';
    return 'bg-red-100 text-red-800 border-red-200';
  };

  const getEfficiencyIcon = (efficiency: number) => {
    if (efficiency >= 80) return '🚀';
    if (efficiency >= 60) return '✅';
    if (efficiency >= 40) return '⚡';
    return '⚠️';
  };

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg border ${getEfficiencyColor(
        cacheEfficiencyPercent
      )}`}
      title="Cache efficiency shows what percentage of tokens were read from cache, reducing costs by ~90%"
    >
      <span className="text-base">{getEfficiencyIcon(cacheEfficiencyPercent)}</span>
      <div className="flex flex-col items-start">
        <span className="font-semibold">
          {cacheEfficiencyPercent.toFixed(1)}% Cache Efficiency
        </span>
        <span className="text-xs opacity-80">
          Saved ${cacheSavingsAmount.toFixed(4)}
        </span>
      </div>
    </div>
  );
}
