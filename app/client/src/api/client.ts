/**
 * Barrel export for all API clients.
 *
 * This file re-exports all domain-specific API clients for easy importing.
 * Components can import from this file to maintain backward compatibility
 * or import from specific domain clients for better organization.
 *
 * Domain clients:
 * - baseClient: Shared utilities (API_BASE, fetchJSON)
 * - githubClient: GitHub issue workflow operations
 * - workflowClient: ADW workflow execution and history
 * - sqlClient: SQL queries, schema, and data export
 * - queueClient: Phase queue and ADW monitoring
 * - systemClient: System status and service management
 *
 * @example
 * // Import specific functions (backward compatible)
 * import { submitRequest, getPreview } from '@/api/client';
 *
 * @example
 * // Import client namespace for better organization
 * import { githubClient } from '@/api/client';
 * githubClient.submitRequest(data);
 *
 * @example
 * // Import from specific domain client
 * import { githubClient } from '@/api/githubClient';
 */

// ============================================================================
// Base Client - Shared utilities
// ============================================================================
export * from './baseClient';

// ============================================================================
// GitHub Client - Issue workflow operations
// ============================================================================
export * from './githubClient';
export { githubClient } from './githubClient';

// ============================================================================
// Workflow Client - ADW workflow execution and history
// ============================================================================
export * from './workflowClient';
export { workflowClient } from './workflowClient';

// ============================================================================
// SQL Client - Database queries and data operations
// ============================================================================
export * from './sqlClient';
export { sqlClient } from './sqlClient';

// ============================================================================
// Queue Client - Phase queue and ADW monitoring
// ============================================================================
export * from './queueClient';
export { queueClient } from './queueClient';

// ============================================================================
// System Client - System status and services
// ============================================================================
export * from './systemClient';
export { systemClient } from './systemClient';

// ============================================================================
// Context Review Client - AI-powered context analysis
// ============================================================================
export * from './contextReviewClient';
export { contextReviewClient } from './contextReviewClient';

// ============================================================================
// Legacy API namespace export for backward compatibility
// ============================================================================
import {
  submitRequest,
  getPreview,
  getCostEstimate,
  confirmAndPost,
} from './githubClient';
import {
  listWorkflows,
  getHistory,
  getWorkflowHistory,
  fetchWorkflowCosts,
} from './workflowClient';
import {
  processQuery,
  generateRandomQuery,
  uploadFile,
  getSchema,
  exportQueryResults,
  exportTable,
} from './sqlClient';
import {
  getQueueAll,
  getQueueByParent,
  dequeuePhase,
  executePhase,
  getAdwMonitor,
  getAdwHealth,
} from './queueClient';
import { getRoutes, getWebhookStatus, getSystemStatus } from './systemClient';

/**
 * Legacy API namespace object for components that use:
 * import { api } from '@/api/client';
 * api.submitRequest(...)
 */
export const api = {
  // GitHub operations
  submitRequest,
  getPreview,
  getCostEstimate,
  confirmAndPost,
  // Workflow operations
  listWorkflows,
  getHistory,
  getWorkflowHistory,
  fetchWorkflowCosts,
  // SQL operations
  processQuery,
  generateRandomQuery,
  uploadFile,
  getSchema,
  exportQueryResults,
  exportTable,
  // Queue operations
  getQueueAll,
  getQueueByParent,
  dequeuePhase,
  executePhase,
  // ADW Monitor operations
  getAdwMonitor,
  getAdwHealth,
  // System operations
  getRoutes,
  getWebhookStatus,
  getSystemStatus,
};
