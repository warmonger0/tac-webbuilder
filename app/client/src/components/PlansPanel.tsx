export function PlansPanel() {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Pending Work Items</h2>

      {/* In Progress Section */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-blue-700 mb-3 flex items-center">
          <span className="mr-2">🔄</span> In Progress
        </h3>
        <div className="space-y-2 pl-6">
          <div className="flex items-start">
            <input type="checkbox" className="mt-1 mr-3" disabled />
            <div>
              <div className="font-medium text-gray-900">Configuration Management System</div>
              <div className="text-sm text-gray-600">3 hours - Medium Value</div>
              <ul className="text-sm text-gray-600 mt-1 list-disc pl-5">
                <li>Port centralized YAML + env var config from tac-7</li>
                <li>Pydantic-based type-safe configuration</li>
                <li>Better deployment scenario support</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Planned Section */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-purple-700 mb-3 flex items-center">
          <span className="mr-2">📋</span> Planned Optional Enhancements
        </h3>
        <div className="space-y-3 pl-6">
          <div className="flex items-start">
            <input type="checkbox" className="mt-1 mr-3" disabled />
            <div>
              <div className="font-medium text-gray-900">Enhanced Structured Logging</div>
              <div className="text-sm text-gray-600">4 hours - Medium Value</div>
              <ul className="text-sm text-gray-600 mt-1 list-disc pl-5">
                <li>Add JSONL output to observability.py</li>
                <li>Pydantic JSON serialization for debugging</li>
                <li>Per-workflow log isolation improvements</li>
              </ul>
            </div>
          </div>

          <div className="flex items-start">
            <input type="checkbox" className="mt-1 mr-3" disabled />
            <div>
              <div className="font-medium text-gray-900">Address ESLint Warnings</div>
              <div className="text-sm text-gray-600">Variable - Low Priority</div>
              <ul className="text-sm text-gray-600 mt-1 list-disc pl-5">
                <li>132 warnings about code complexity, max-lines, console.log</li>
                <li>Non-blocking, style preferences</li>
              </ul>
            </div>
          </div>

          <div className="flex items-start">
            <input type="checkbox" className="mt-1 mr-3" disabled />
            <div>
              <div className="font-medium text-gray-900">CLI Interface</div>
              <div className="text-sm text-gray-600">8 hours - Low Priority</div>
              <ul className="text-sm text-gray-600 mt-1 list-disc pl-5">
                <li>Port from tac-7 for power users</li>
                <li>Terminal access to core features</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Recently Completed Section */}
      <div>
        <h3 className="text-lg font-semibold text-green-700 mb-3 flex items-center">
          <span className="mr-2">✅</span> Recently Completed
        </h3>
        <div className="space-y-3 pl-6">
          <div className="flex items-start">
            <input type="checkbox" checked className="mt-1 mr-3" disabled />
            <div>
              <div className="font-medium text-gray-700">Token Monitoring Tools</div>
              <div className="text-sm text-gray-500">Completed 2025-12-02</div>
              <ul className="text-sm text-gray-500 mt-1 list-disc pl-5">
                <li>monitor_adw_tokens.py - Real-time tracking</li>
                <li>analyze_context_usage.py - Optimization analysis</li>
                <li>Tested: 87.4% cache efficiency</li>
              </ul>
            </div>
          </div>

          <div className="flex items-start">
            <input type="checkbox" checked className="mt-1 mr-3" disabled />
            <div>
              <div className="font-medium text-gray-700">Critical ESLint Fixes</div>
              <div className="text-sm text-gray-500">Completed 2025-12-02</div>
              <ul className="text-sm text-gray-500 mt-1 list-disc pl-5">
                <li>Fixed 6 critical errors</li>
                <li>Auto-formatted frontend components</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Note */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <p className="text-sm text-gray-500 italic">
          Note: All items above are optional enhancements. System is fully functional and production-ready as-is.
        </p>
      </div>
    </div>
  );
}
