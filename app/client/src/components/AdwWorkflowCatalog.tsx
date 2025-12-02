import { useState } from 'react';
import { CurrentWorkflowCard } from './CurrentWorkflowCard';

type CatalogTab = 'workflows' | 'current';

interface WorkflowType {
  id: string;
  name: string;
  description: string;
  phases: string[];
  recommended: boolean;
  deprecated: boolean;
  flags?: string[];
  usage: string;
  category: 'entry' | 'orchestrator' | 'dependent' | 'automation';
}

const workflowCatalog: WorkflowType[] = [
  {
    id: 'adw_sdlc_complete_iso',
    name: 'Complete SDLC',
    description: 'Full Software Development Life Cycle with ALL 8 phases including lint validation. This is the recommended workflow for most tasks.',
    phases: ['Plan', 'Build', 'Lint', 'Test', 'Review', 'Document', 'Ship', 'Cleanup'],
    recommended: true,
    deprecated: false,
    flags: ['--skip-e2e', '--skip-resolution', '--no-external', '--use-optimized-plan'],
    usage: 'uv run adw_sdlc_complete_iso.py <issue-number>',
    category: 'orchestrator'
  },
  {
    id: 'adw_sdlc_complete_zte_iso',
    name: 'Zero Touch Execution (Complete)',
    description: '⚠️ Complete SDLC with ALL 8 phases + automatic PR merge. WARNING: Automatically merges to main if all phases pass!',
    phases: ['Plan', 'Build', 'Lint', 'Test', 'Review', 'Document', 'Ship', 'Cleanup'],
    recommended: true,
    deprecated: false,
    flags: ['--skip-e2e', '--skip-resolution', '--no-external', '--use-optimized-plan'],
    usage: 'uv run adw_sdlc_complete_zte_iso.py <issue-number>',
    category: 'orchestrator'
  },
  {
    id: 'adw_stepwise_iso',
    name: 'Stepwise Refinement Analysis',
    description: 'Analyzes issue complexity and decides between ATOMIC (single workflow) or DECOMPOSE (break into sub-issues). Great for complex tasks.',
    phases: ['Analysis', 'Decision', 'Route'],
    recommended: true,
    deprecated: false,
    usage: 'uv run adw_stepwise_iso.py <issue-number>',
    category: 'orchestrator'
  },
  {
    id: 'adw_plan_iso',
    name: 'Planning Phase',
    description: 'Creates isolated worktree and generates implementation plans. Entry point workflow that creates the isolated environment.',
    phases: ['Plan'],
    recommended: false,
    deprecated: false,
    usage: 'uv run adw_plan_iso.py <issue-number>',
    category: 'entry'
  },
  {
    id: 'adw_patch_iso',
    name: 'Quick Patch',
    description: 'Quick patches in isolated environment triggered by "adw_patch" keyword. Creates targeted patch plan and implements specific changes.',
    phases: ['Plan', 'Patch'],
    recommended: false,
    deprecated: false,
    usage: 'uv run adw_patch_iso.py <issue-number>',
    category: 'entry'
  },
  {
    id: 'adw_build_iso',
    name: 'Build Phase',
    description: 'Implements solutions in existing isolated environment. Requires existing worktree created by plan or patch workflow.',
    phases: ['Build'],
    recommended: false,
    deprecated: false,
    usage: 'uv run adw_build_iso.py <issue-number> <adw-id>',
    category: 'dependent'
  },
  {
    id: 'adw_test_iso',
    name: 'Test Phase',
    description: 'Runs tests in isolated environment with allocated ports. Auto-resolves failures and optionally runs E2E tests.',
    phases: ['Test'],
    recommended: false,
    deprecated: false,
    flags: ['--skip-e2e'],
    usage: 'uv run adw_test_iso.py <issue-number> <adw-id>',
    category: 'dependent'
  },
  {
    id: 'adw_lint_iso',
    name: 'Lint Phase',
    description: 'Validates code quality with TypeScript, ESLint, and formatting checks. Ensures code meets quality standards.',
    phases: ['Lint'],
    recommended: false,
    deprecated: false,
    usage: 'uv run adw_lint_iso.py <issue-number> <adw-id>',
    category: 'dependent'
  },
  {
    id: 'adw_review_iso',
    name: 'Review Phase',
    description: 'Reviews implementation in isolated environment against spec. Captures screenshots using allocated ports and auto-resolves blockers.',
    phases: ['Review'],
    recommended: false,
    deprecated: false,
    flags: ['--skip-resolution'],
    usage: 'uv run adw_review_iso.py <issue-number> <adw-id>',
    category: 'dependent'
  },
  {
    id: 'adw_document_iso',
    name: 'Documentation Phase',
    description: 'Generates comprehensive documentation in isolated environment. Analyzes changes and creates docs in app_docs/ directory.',
    phases: ['Document'],
    recommended: false,
    deprecated: false,
    usage: 'uv run adw_document_iso.py <issue-number> <adw-id>',
    category: 'dependent'
  },
  {
    id: 'adw_ship_iso',
    name: 'Ship Phase',
    description: 'Final shipping phase that validates state, approves, and merges PR to main. Validates all ADWState fields are populated.',
    phases: ['Ship'],
    recommended: false,
    deprecated: false,
    usage: 'uv run adw_ship_iso.py <issue-number> <adw-id>',
    category: 'dependent'
  },
  {
    id: 'adw_plan_build_iso',
    name: 'Plan + Build',
    description: 'Runs planning and building phases in isolation. Creates worktree, generates plan, and implements solution.',
    phases: ['Plan', 'Build'],
    recommended: false,
    deprecated: false,
    usage: 'uv run adw_plan_build_iso.py <issue-number>',
    category: 'orchestrator'
  },
  {
    id: 'adw_plan_build_test_iso',
    name: 'Plan + Build + Test',
    description: 'Full pipeline with testing in isolation. Creates worktree, implements solution, and runs tests.',
    phases: ['Plan', 'Build', 'Test'],
    recommended: false,
    deprecated: false,
    usage: 'uv run adw_plan_build_test_iso.py <issue-number>',
    category: 'orchestrator'
  },
  {
    id: 'adw_plan_build_test_review_iso',
    name: 'Plan + Build + Test + Review',
    description: 'Complete pipeline with review in isolation. Full workflow excluding documentation and shipping.',
    phases: ['Plan', 'Build', 'Test', 'Review'],
    recommended: false,
    deprecated: false,
    usage: 'uv run adw_plan_build_test_review_iso.py <issue-number>',
    category: 'orchestrator'
  },
  {
    id: 'trigger_cron',
    name: 'Polling Monitor',
    description: 'Continuously monitors GitHub for triggers. Polls every 20 seconds for new issues or "adw" comments.',
    phases: ['Monitor', 'Route'],
    recommended: false,
    deprecated: false,
    usage: 'uv run adw_triggers/trigger_cron.py',
    category: 'automation'
  },
  {
    id: 'trigger_webhook',
    name: 'Webhook Server',
    description: 'Real-time event processing via webhook. Instant GitHub event processing on port 8001.',
    phases: ['Listen', 'Route'],
    recommended: false,
    deprecated: false,
    usage: 'uv run adw_triggers/trigger_webhook.py',
    category: 'automation'
  },
  {
    id: 'adw_sdlc_iso',
    name: 'Complete SDLC (Old)',
    description: '⚠️ DEPRECATED: Use adw_sdlc_complete_iso.py instead. Missing lint phase - can deploy broken code.',
    phases: ['Plan', 'Build', 'Test', 'Review', 'Document'],
    recommended: false,
    deprecated: true,
    usage: 'uv run adw_sdlc_iso.py <issue-number>',
    category: 'orchestrator'
  },
  {
    id: 'adw_sdlc_zte_iso',
    name: 'Zero Touch Execution (Old)',
    description: '⚠️ DEPRECATED: Use adw_sdlc_complete_zte_iso.py instead. Missing lint and cleanup phases.',
    phases: ['Plan', 'Build', 'Test', 'Review', 'Document', 'Ship'],
    recommended: false,
    deprecated: true,
    usage: 'uv run adw_sdlc_zte_iso.py <issue-number>',
    category: 'orchestrator'
  },
];

export function AdwWorkflowCatalog() {
  const [activeTab, setActiveTab] = useState<CatalogTab>('current');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showDeprecated, setShowDeprecated] = useState(false);

  const categories = [
    { id: 'all', label: 'All Workflows', icon: '📚' },
    { id: 'orchestrator', label: 'Orchestrators', icon: '🎯' },
    { id: 'entry', label: 'Entry Points', icon: '🚪' },
    { id: 'dependent', label: 'Phase Workflows', icon: '🔗' },
    { id: 'automation', label: 'Automation', icon: '🤖' },
  ];

  const filteredWorkflows = workflowCatalog.filter(workflow => {
    const categoryMatch = selectedCategory === 'all' || workflow.category === selectedCategory;
    const deprecatedMatch = showDeprecated || !workflow.deprecated;
    return categoryMatch && deprecatedMatch;
  });

  const recommendedWorkflows = filteredWorkflows.filter(w => w.recommended && !w.deprecated);
  const otherWorkflows = filteredWorkflows.filter(w => !w.recommended || w.deprecated);

  const getCategoryBadgeColor = (category: string) => {
    switch (category) {
      case 'orchestrator':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'entry':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'dependent':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'automation':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg shadow-xl border border-slate-700 overflow-hidden flex-1 flex flex-col">
      {/* Header with Tabs */}
      <div className="relative border-b border-slate-700/50">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10"></div>
        <div className="relative px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="relative w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(59,130,246,0.5)]">
                <div className="absolute -inset-1 bg-gradient-to-r from-blue-400/20 to-purple-400/20 rounded-lg blur-md animate-pulse"></div>
                <svg className="w-5 h-5 text-white relative z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
                  ADW Panel
                </h2>
                <p className="text-slate-400 text-xs">Workflows and monitoring</p>
              </div>
            </div>
            {activeTab === 'workflows' && (
              <label className="flex items-center text-sm text-slate-400">
                <input
                  type="checkbox"
                  checked={showDeprecated}
                  onChange={(e) => setShowDeprecated(e.target.checked)}
                  className="mr-2 rounded"
                />
                Show deprecated
              </label>
            )}
          </div>
          {/* Tab Navigation */}
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('workflows')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'workflows'
                  ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg'
                  : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
            >
              📚 Workflow Catalog
            </button>
            <button
              onClick={() => setActiveTab('current')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'current'
                  ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg'
                  : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
            >
              ⚡ Current Workflow
            </button>
          </div>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'workflows' && (
        <>
          {/* Category Tabs */}
          <div className="px-4 py-3 border-b border-slate-700/50 bg-slate-800/50">
            <div className="flex flex-wrap gap-2">
              {categories.map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                    selectedCategory === cat.id
                      ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg'
                      : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700 hover:text-white'
                  }`}
                >
                  {cat.icon} {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* Workflow Cards */}
          <div className="p-4 flex-1 overflow-y-auto custom-scrollbar">
            {/* Recommended Section */}
            {recommendedWorkflows.length > 0 && (
              <div className="mb-6">
                <h3 className="text-emerald-400 font-semibold text-sm mb-3 flex items-center gap-2">
                  <span className="text-lg">⭐</span> RECOMMENDED WORKFLOWS
                </h3>
                <div className="grid grid-cols-1 gap-3">
                  {recommendedWorkflows.map(workflow => (
                    <div
                      key={workflow.id}
                      className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg border border-emerald-500/30 p-4 hover:border-emerald-500/50 transition-all shadow-lg hover:shadow-emerald-500/10"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="text-white font-semibold">{workflow.name}</h4>
                            <span className={`text-xs px-2 py-0.5 rounded border ${getCategoryBadgeColor(workflow.category)}`}>
                              {workflow.category}
                            </span>
                          </div>
                          <p className="text-slate-300 text-sm mb-2">{workflow.description}</p>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-1.5 mb-2">
                        {workflow.phases.map(phase => (
                          <span key={phase} className="px-2 py-0.5 bg-blue-500/20 text-blue-300 text-xs rounded border border-blue-500/30">
                            {phase}
                          </span>
                        ))}
                      </div>

                      {workflow.flags && workflow.flags.length > 0 && (
                        <div className="mb-2">
                          <span className="text-slate-400 text-xs">Optional flags: </span>
                          <span className="text-slate-300 text-xs font-mono">{workflow.flags.join(' ')}</span>
                        </div>
                      )}

                      <div className="bg-slate-950/50 rounded p-2 border border-slate-700/50">
                        <code className="text-emerald-400 text-xs font-mono">{workflow.usage}</code>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Other Workflows Section */}
            {otherWorkflows.length > 0 && (
              <div>
                <h3 className="text-slate-400 font-semibold text-sm mb-3 flex items-center gap-2">
                  {recommendedWorkflows.length > 0 ? 'OTHER WORKFLOWS' : 'WORKFLOWS'}
                </h3>
                <div className="grid grid-cols-1 gap-3">
                  {otherWorkflows.map(workflow => (
                    <div
                      key={workflow.id}
                      className={`bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg border p-4 transition-all ${
                        workflow.deprecated
                          ? 'border-red-500/30 opacity-60 hover:opacity-80'
                          : 'border-slate-700/50 hover:border-slate-600'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="text-white font-semibold">{workflow.name}</h4>
                            <span className={`text-xs px-2 py-0.5 rounded border ${getCategoryBadgeColor(workflow.category)}`}>
                              {workflow.category}
                            </span>
                            {workflow.deprecated && (
                              <span className="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/30">
                                DEPRECATED
                              </span>
                            )}
                          </div>
                          <p className="text-slate-300 text-sm mb-2">{workflow.description}</p>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-1.5 mb-2">
                        {workflow.phases.map(phase => (
                          <span key={phase} className="px-2 py-0.5 bg-purple-500/20 text-purple-300 text-xs rounded border border-purple-500/30">
                            {phase}
                          </span>
                        ))}
                      </div>

                      {workflow.flags && workflow.flags.length > 0 && (
                        <div className="mb-2">
                          <span className="text-slate-400 text-xs">Optional flags: </span>
                          <span className="text-slate-300 text-xs font-mono">{workflow.flags.join(' ')}</span>
                        </div>
                      )}

                      <div className="bg-slate-950/50 rounded p-2 border border-slate-700/50">
                        <code className="text-cyan-400 text-xs font-mono">{workflow.usage}</code>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {filteredWorkflows.length === 0 && (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-slate-500/20 to-slate-500/20 rounded-2xl flex items-center justify-center">
                  <svg className="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-lg font-semibold text-slate-300 mb-1">No workflows found</p>
                <p className="text-slate-500 text-sm">Try selecting a different category or enabling deprecated workflows</p>
              </div>
            )}
          </div>
        </>
      )}

      {activeTab === 'current' && (
        <div className="flex-1 overflow-y-auto p-4">
          <CurrentWorkflowCard />
        </div>
      )}

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgb(30 41 59);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgb(71 85 105);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgb(100 116 139);
        }
      `}</style>
    </div>
  );
}
