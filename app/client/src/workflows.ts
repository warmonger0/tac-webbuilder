/**
 * ADW Workflows Module
 *
 * Contains definitions for all AI Developer Workflow (ADW) scripts that automate
 * software development using isolated git worktrees.
 */

// Workflow data with descriptions based on ADW documentation
export const workflows: Workflow[] = [
  // === Single Phase Workflows ===
  {
    name: "Plan Only",
    script_name: "adw_plan_iso",
    description: "Creates implementation plans in isolated worktrees without executing code changes",
    use_case: "Use when you need to generate a detailed implementation plan before making changes",
    category: "single-phase"
  },
  {
    name: "Build Only",
    script_name: "adw_build_iso",
    description: "Implements solutions based on existing plans in isolated environments",
    use_case: "Use after planning phase to implement the solution. Requires existing worktree",
    category: "single-phase"
  },
  {
    name: "Test Only",
    script_name: "adw_test_iso",
    description: "Runs test suites with automatic failure resolution in isolated worktrees",
    use_case: "Use to run unit tests and E2E tests with automatic retry and fix logic. Requires existing worktree",
    category: "single-phase"
  },
  {
    name: "Review Only",
    script_name: "adw_review_iso",
    description: "Performs code review against specifications with screenshot capture",
    use_case: "Use to validate implementation matches specifications and capture visual evidence. Requires existing worktree",
    category: "single-phase"
  },
  {
    name: "Document Only",
    script_name: "adw_document_iso",
    description: "Generates comprehensive feature documentation from implementation",
    use_case: "Use to create user-facing and technical documentation. Requires existing worktree",
    category: "single-phase"
  },
  {
    name: "Ship",
    script_name: "adw_ship_iso",
    description: "Approves and merges pull request to main branch after validation",
    use_case: "Use as final step to merge completed work to production. Validates all workflow steps completed",
    category: "single-phase"
  },

  // === Multi-Phase Workflows ===
  {
    name: "Plan + Build",
    script_name: "adw_plan_build_iso",
    description: "Combines planning and implementation phases in a single workflow",
    use_case: "Use for quick feature development when you don't need testing or review",
    category: "multi-phase"
  },
  {
    name: "Plan + Build + Test",
    script_name: "adw_plan_build_test_iso",
    description: "Executes planning, implementation, and testing phases sequentially",
    use_case: "Use for standard feature development with automated testing validation",
    category: "multi-phase"
  },
  {
    name: "Plan + Build + Test + Review",
    script_name: "adw_plan_build_test_review_iso",
    description: "Full development cycle including planning, building, testing, and review",
    use_case: "Use for complex features requiring thorough validation before documentation",
    category: "multi-phase"
  },
  {
    name: "Quick Patch",
    script_name: "adw_patch_iso",
    description: "Fast-track workflow for urgent fixes triggered by 'adw_patch' keyword",
    use_case: "Use for quick bug fixes and small changes. Searches for 'adw_patch' in issues/comments",
    category: "multi-phase"
  },

  // === Complete SDLC Workflows ===
  {
    name: "Complete SDLC",
    script_name: "adw_sdlc_iso",
    description: "Full Software Development Life Cycle: plan, build, test, review, and document",
    use_case: "Use for complete feature development. Requires manual PR approval before merging",
    category: "full-sdlc"
  },
  {
    name: "Zero Touch Execution",
    script_name: "adw_sdlc_zte_iso",
    description: "Complete SDLC with automatic PR merge - no human intervention required",
    use_case: "Use for automated deployment to production. Automatically merges if all phases pass. WARNING: Merges to main automatically!",
    category: "full-sdlc"
  }
];

/**
 * Get all workflows
 */
export function getAllWorkflows(): Workflow[] {
  return workflows;
}

/**
 * Get workflows by category
 */
export function getWorkflowsByCategory(category: Workflow['category']): Workflow[] {
  return workflows.filter(w => w.category === category);
}

/**
 * Get workflow by script name
 */
export function getWorkflowByScriptName(scriptName: string): Workflow | undefined {
  return workflows.find(w => w.script_name === scriptName);
}

/**
 * Category display names
 */
export const categoryNames = {
  "single-phase": "Single Phase Workflows",
  "multi-phase": "Multi-Phase Workflows",
  "full-sdlc": "Complete SDLC Workflows"
} as const;

/**
 * Category descriptions
 */
export const categoryDescriptions = {
  "single-phase": "Targeted, isolated operations for specific phases of development",
  "multi-phase": "Combinations of phases for common development scenarios",
  "full-sdlc": "Complete software development lifecycle from plan to production"
} as const;
