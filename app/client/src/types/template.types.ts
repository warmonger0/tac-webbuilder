/**
 * Workflow Template Types
 *
 * These types represent workflow template definitions from the catalog.
 */

// Basic workflow template from workflows.ts
export interface WorkflowTemplate {
  name: string;
  script_name: string;
  description: string;
  use_case: string;
  category: "single-phase" | "multi-phase" | "full-sdlc";
}

// Extended template type with display information from API
export interface WorkflowTemplateDisplay {
  name: string;
  display_name: string;
  phases: string[];
  purpose: string;
  cost_range: string;
  best_for: string[];
}

export interface WorkflowCatalogResponse {
  workflows: WorkflowTemplateDisplay[];
  total: number;
}
