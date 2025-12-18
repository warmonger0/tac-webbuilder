/**
 * QC Metrics API client for quality control metrics.
 *
 * This module handles:
 * - Fetching code quality metrics
 * - Coverage statistics
 * - Linting issues
 * - Naming conventions
 * - File structure metrics
 */

import { API_BASE, fetchJSON } from './baseClient';

// ============================================================================
// Type Definitions
// ============================================================================

export interface CoverageMetrics {
  overall_coverage: number;
  backend_coverage: number;
  frontend_coverage: number;
  adws_coverage: number;
  total_tests: number;
}

export interface NamingViolation {
  file: string;
  issue: string;
  severity: 'error' | 'warning' | 'info';
}

export interface NamingConventionMetrics {
  total_files_checked: number;
  compliant_files: number;
  violations: NamingViolation[];
  compliance_rate: number;
}

export interface OversizedFile {
  file: string;
  size_kb: number;
}

export interface LongFile {
  file: string;
  lines: number;
}

export interface FileStructureMetrics {
  total_files: number;
  oversized_files: OversizedFile[];
  long_files: LongFile[];
  avg_file_size_kb: number;
}

export interface LintingMetrics {
  backend_issues: number;
  frontend_issues: number;
  backend_errors: number;
  backend_warnings: number;
  frontend_errors: number;
  frontend_warnings: number;
  total_issues: number;
}

export interface QCMetrics {
  coverage: CoverageMetrics;
  naming: NamingConventionMetrics;
  file_structure: FileStructureMetrics;
  linting: LintingMetrics;
  overall_score: number;
  last_updated: string;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get complete QC metrics for the codebase.
 *
 * Returns comprehensive quality metrics including coverage, naming,
 * file structure, linting, and an overall quality score.
 *
 * Note: This endpoint uses caching. Results may be cached for performance.
 * Use refreshQCMetrics() to force a fresh computation.
 *
 * @returns Complete QC metrics
 */
export async function getQCMetrics(): Promise<QCMetrics> {
  return fetchJSON<QCMetrics>(`${API_BASE}/qc-metrics`);
}

/**
 * Force refresh QC metrics (clears cache and recomputes).
 *
 * Use this after:
 * - Running tests with coverage
 * - Fixing linting issues
 * - Refactoring code
 *
 * @returns Fresh QC metrics
 */
export async function refreshQCMetrics(): Promise<QCMetrics> {
  return fetchJSON<QCMetrics>(`${API_BASE}/qc-metrics/refresh`, {
    method: 'POST',
  });
}

/**
 * Get test coverage metrics only (faster than full metrics).
 *
 * @returns Coverage metrics
 */
export async function getCoverageMetrics(): Promise<CoverageMetrics> {
  return fetchJSON<CoverageMetrics>(`${API_BASE}/qc-metrics/coverage`);
}

/**
 * Get linting metrics only (faster than full metrics).
 *
 * @returns Linting metrics
 */
export async function getLintingMetrics(): Promise<LintingMetrics> {
  return fetchJSON<LintingMetrics>(`${API_BASE}/qc-metrics/linting`);
}

// ============================================================================
// QC Metrics Client (singleton pattern)
// ============================================================================

export const qcMetricsClient = {
  getQCMetrics,
  refreshQCMetrics,
  getCoverageMetrics,
  getLintingMetrics,
};
