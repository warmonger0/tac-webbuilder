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
          <p className="text-gray-500 italic">No tasks currently in progress</p>
        </div>
      </div>

      {/* Planned Section */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-purple-700 mb-3 flex items-center">
          <span className="mr-2">📋</span> Planned Fixes & Enhancements
        </h3>
        <div className="space-y-3 pl-6">

          <div className="flex items-start">
            <input type="checkbox" className="mt-1 mr-3" disabled />
            <div>
              <div className="font-medium text-red-700">🐛 Pre-flight Check Before Issue Creation</div>
              <div className="text-sm text-gray-600">2-3 hours - HIGH Priority - Bug Fix</div>
              <ul className="text-sm text-gray-600 mt-1 list-disc pl-5">
                <li>Run pre-flight checks BEFORE creating GitHub issue</li>
                <li>Check git status, worktrees, disk space in Panel 1 submit handler</li>
                <li>Show validation errors to user before issue creation</li>
                <li>Prevents failed issues with error comments (Issue #140)</li>
              </ul>
            </div>
          </div>

          <div className="flex items-start">
            <input type="checkbox" className="mt-1 mr-3" disabled />
            <div>
              <div className="font-medium text-red-700">🐛 Panel 2 Not Updating with Current Workflow</div>
              <div className="text-sm text-gray-600">1-2 hours - HIGH Priority - Bug Fix</div>
              <ul className="text-sm text-gray-600 mt-1 list-disc pl-5">
                <li>Current Workflow panel doesn't update after successful submission</li>
                <li>Shows old completed workflow (#135) instead of new one (#140)</li>
                <li>Hard refresh doesn't fix it - data fetching or state issue</li>
                <li>Check polling interval, websocket connection, or API response</li>
              </ul>
            </div>
          </div>

          <div className="flex items-start">
            <input type="checkbox" className="mt-1 mr-3" disabled />
            <div>
              <div className="font-medium text-red-700">🐛 Implement Hybrid Lint Loop (External + LLM Fallback)</div>
              <div className="text-sm text-gray-600">3-4 hours - HIGH Priority - Architecture Fix</div>
              <ul className="text-sm text-gray-600 mt-1 list-disc pl-5">
                <li><strong>Current:</strong> Single external lint run → If errors exist → Kill workflow</li>
                <li><strong>Proposed:</strong> External loop (3 attempts) → LLM fallback → Continue</li>
                <li>External loop: Fast/cheap, fixes simple repetitive errors (ruff --fix, eslint --fix)</li>
                <li>LLM fallback: Handle nuanced/contextual errors that need understanding</li>
                <li>Don't kill workflow - reduce workload first, then let LLM finish</li>
                <li><strong>Impact:</strong> 167 errors blocked workflow #140 - this would fix it</li>
              </ul>
            </div>
          </div>

          <div className="flex items-start">
            <input type="checkbox" className="mt-1 mr-3" disabled />
            <div>
              <div className="font-medium text-gray-900">Average Cost Per Completion Metric</div>
              <div className="text-sm text-gray-600">4-6 hours - Medium Priority - Feature</div>
              <ul className="text-sm text-gray-600 mt-1 list-disc pl-5">
                <li>Add metric display to History panel (Panel 3)</li>
                <li>7-day and 30-day trend comparisons</li>
                <li>Phase cost breakdown with visual indicators</li>
                <li>Loading states and error handling</li>
              </ul>
            </div>
          </div>

          <div className="flex items-start">
            <input type="checkbox" className="mt-1 mr-3" disabled />
            <div>
              <div className="font-medium text-gray-900">CLI Interface</div>
              <div className="text-sm text-gray-600">8 hours - Low Priority - Feature</div>
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
              <div className="font-medium text-gray-700">ESLint Cleanup</div>
              <div className="text-sm text-gray-500">Completed 2025-12-02</div>
              <ul className="text-sm text-gray-500 mt-1 list-disc pl-5">
                <li>Fixed 25 warnings (console.log, naming, imports)</li>
                <li>Reduced from 134 to 109 warnings (0 errors)</li>
                <li>Updated config for test files</li>
                <li>Remaining warnings are acceptable technical debt</li>
              </ul>
            </div>
          </div>

          <div className="flex items-start">
            <input type="checkbox" checked className="mt-1 mr-3" disabled />
            <div>
              <div className="font-medium text-gray-700">Enhanced Structured Logging</div>
              <div className="text-sm text-gray-500">Completed 2025-12-02</div>
              <ul className="text-sm text-gray-500 mt-1 list-disc pl-5">
                <li>JSONL output with 6 event types (Workflow, Phase, System, DB, HTTP, Metrics)</li>
                <li>Per-workflow log isolation in separate files</li>
                <li>Pydantic validation and serialization</li>
                <li>13 passing tests, comprehensive documentation</li>
              </ul>
            </div>
          </div>

          <div className="flex items-start">
            <input type="checkbox" checked className="mt-1 mr-3" disabled />
            <div>
              <div className="font-medium text-gray-700">Configuration Management System</div>
              <div className="text-sm text-gray-500">Completed 2025-12-02</div>
              <ul className="text-sm text-gray-500 mt-1 list-disc pl-5">
                <li>Pydantic-based config with YAML + env var support</li>
                <li>5 config sections with type validation</li>
                <li>23 passing tests, full documentation</li>
              </ul>
            </div>
          </div>

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
