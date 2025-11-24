import type { WorkflowHistoryItem } from '../../../types';
import { TokenBreakdownChart } from '../../TokenBreakdownChart';
import { CacheEfficiencyBadge } from '../../CacheEfficiencyBadge';
import { calculateCacheSavings, formatNumber } from '../helpers';

interface TokenSectionProps {
  workflow: WorkflowHistoryItem;
}

export function TokenSection({ workflow }: TokenSectionProps) {
  if (workflow.total_tokens <= 0) return null;

  return (
    <div className="border-b border-gray-200 pb-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">
        🔢 Token Analysis
      </h3>

      {/* Token Breakdown Chart and Cache Efficiency */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-4">
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <TokenBreakdownChart
            inputTokens={workflow.input_tokens}
            outputTokens={workflow.output_tokens}
            cachedTokens={workflow.cached_tokens}
            cacheHitTokens={workflow.cache_hit_tokens}
            cacheMissTokens={workflow.cache_miss_tokens}
            totalTokens={workflow.total_tokens}
          />
        </div>

        <div className="flex flex-col gap-4">
          {/* Cache Efficiency Badge */}
          {workflow.cache_efficiency_percent > 0 && (
            <div>
              <CacheEfficiencyBadge
                cacheEfficiencyPercent={workflow.cache_efficiency_percent}
                cacheSavingsAmount={calculateCacheSavings(workflow)}
              />
            </div>
          )}

          {/* Cache Hit/Miss Ratio Visualization */}
          {(workflow.cache_hit_tokens > 0 || workflow.cache_miss_tokens > 0) && (
            <div className="border border-gray-200 rounded-lg p-4 bg-white">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">
                Cache Hit/Miss Ratio
              </h4>
              <div className="space-y-2">
                {(() => {
                  const total = workflow.cache_hit_tokens + workflow.cache_miss_tokens;
                  const hitPercentage = (workflow.cache_hit_tokens / total) * 100;
                  return (
                    <>
                      <div className="relative w-full h-8 bg-orange-200 rounded-lg overflow-hidden">
                        <div
                          className="absolute h-full bg-green-500 transition-all"
                          style={{ width: `${hitPercentage}%` }}
                        />
                        <div className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-gray-900">
                          {hitPercentage.toFixed(1)}% Cache Hits
                        </div>
                      </div>
                      <div className="flex justify-between text-xs text-gray-600">
                        <span>
                          Hits: {workflow.cache_hit_tokens.toLocaleString()}
                        </span>
                        <span>
                          Misses: {workflow.cache_miss_tokens.toLocaleString()}
                        </span>
                      </div>
                    </>
                  );
                })()}
              </div>
            </div>
          )}

          {/* Detailed Token Breakdown Table */}
          <div className="border border-gray-200 rounded-lg p-4 bg-white">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Token Details</h4>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-gray-50 rounded p-2">
                <div className="text-gray-600">Input</div>
                <div className="font-medium">{formatNumber(workflow.input_tokens)}</div>
              </div>
              <div className="bg-gray-50 rounded p-2">
                <div className="text-gray-600">Output</div>
                <div className="font-medium">{formatNumber(workflow.output_tokens)}</div>
              </div>
              <div className="bg-gray-50 rounded p-2">
                <div className="text-gray-600">Cached</div>
                <div className="font-medium">{formatNumber(workflow.cached_tokens)}</div>
              </div>
              <div className="bg-gray-50 rounded p-2">
                <div className="text-gray-600">Total</div>
                <div className="font-medium">{formatNumber(workflow.total_tokens)}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
