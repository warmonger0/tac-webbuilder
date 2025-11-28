/**
 * Theme Configuration
 * Centralized configuration for all colors, status mappings, and visual elements
 */

/**
 * Status Badge Color Mappings
 */
export const statusColors = {
  plan: {
    bg: 'bg-blue-100',
    text: 'text-blue-800',
    border: 'border-blue-300',
  },
  build: {
    bg: 'bg-yellow-100',
    text: 'text-yellow-800',
    border: 'border-yellow-300',
  },
  test: {
    bg: 'bg-purple-100',
    text: 'text-purple-800',
    border: 'border-purple-300',
  },
  review: {
    bg: 'bg-indigo-100',
    text: 'text-indigo-800',
    border: 'border-indigo-300',
  },
  document: {
    bg: 'bg-cyan-100',
    text: 'text-cyan-800',
    border: 'border-cyan-300',
  },
  ship: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    border: 'border-green-300',
  },
  completed: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    border: 'border-green-300',
  },
  success: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    border: 'border-green-300',
  },
  error: {
    bg: 'bg-red-100',
    text: 'text-red-800',
    border: 'border-red-300',
  },
  failed: {
    bg: 'bg-red-100',
    text: 'text-red-800',
    border: 'border-red-300',
  },
  pending: {
    bg: 'bg-gray-100',
    text: 'text-gray-800',
    border: 'border-gray-300',
  },
} as const;

/**
 * Phase Queue Status Configuration
 */
export const phaseQueueStatusColors = {
  queued: {
    bg: 'bg-gray-100',
    text: 'text-gray-700',
    border: 'border-gray-300',
    badge: 'bg-gray-500',
    icon: '⏸️',
    label: 'Queued',
  },
  ready: {
    bg: 'bg-blue-50',
    text: 'text-blue-900',
    border: 'border-blue-300',
    badge: 'bg-blue-500',
    icon: '▶️',
    label: 'Ready',
  },
  running: {
    bg: 'bg-yellow-50',
    text: 'text-yellow-900',
    border: 'border-yellow-300',
    badge: 'bg-yellow-500',
    icon: '⚙️',
    label: 'Running',
  },
  completed: {
    bg: 'bg-green-50',
    text: 'text-green-900',
    border: 'border-green-300',
    badge: 'bg-green-500',
    icon: '✅',
    label: 'Completed',
  },
  blocked: {
    bg: 'bg-orange-50',
    text: 'text-orange-900',
    border: 'border-orange-300',
    badge: 'bg-orange-500',
    icon: '🚫',
    label: 'Blocked',
  },
  failed: {
    bg: 'bg-red-50',
    text: 'text-red-900',
    border: 'border-red-300',
    badge: 'bg-red-500',
    icon: '❌',
    label: 'Failed',
  },
} as const;

/**
 * HTTP Method Color Mappings
 */
export const httpMethodColors = {
  GET: 'bg-blue-100 text-blue-800 border-blue-300',
  POST: 'bg-green-100 text-green-800 border-green-300',
  PUT: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  DELETE: 'bg-red-100 text-red-800 border-red-300',
  PATCH: 'bg-purple-100 text-purple-800 border-purple-300',
} as const;

/**
 * ADW Status Color Configurations
 */
export const adwStatusColors = {
  failed: {
    outer: 'bg-red-100 border-red-300',
    header: 'bg-red-50 border-red-200',
    titleText: 'text-red-900',
    badge: 'bg-red-100 text-red-800 border-red-300',
    phaseBar: 'bg-red-200',
    phaseProgress: 'bg-red-500',
  },
  running: {
    outer: 'bg-blue-50 border-blue-200',
    header: 'bg-blue-50 border-blue-200',
    titleText: 'text-blue-900',
    badge: 'bg-blue-100 text-blue-800 border-blue-300',
    phaseBar: 'bg-blue-200',
    phaseProgress: 'bg-blue-500',
  },
  paused: {
    outer: 'bg-yellow-50 border-yellow-200',
    header: 'bg-yellow-50 border-yellow-200',
    titleText: 'text-yellow-900',
    badge: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    phaseBar: 'bg-yellow-200',
    phaseProgress: 'bg-yellow-500',
  },
  default: {
    outer: 'bg-white border-gray-200',
    header: 'bg-gray-50 border-gray-200',
    titleText: 'text-gray-900',
    badge: 'bg-gray-100 text-gray-800 border-gray-300',
    phaseBar: 'bg-gray-200',
    phaseProgress: 'bg-gray-500',
  },
} as const;

/**
 * Connection Status Icons
 */
export const connectionStatusIcons = {
  live: '●',          // Filled circle
  connected: '●',     // Filled circle
  slow: '●',          // Filled circle
  offline: '○',       // Empty circle
} as const;

/**
 * Preflight Check Icons
 */
export const preflightCheckIcons = {
  pass: '✅',
  warning: '⚠️',
  fail: '❌',
  unknown: '❓',
} as const;

/**
 * Health Status Icons
 */
export const healthStatusIcons = {
  healthy: '🟢',
  warning: '🟡',
  error: '🔴',
} as const;

/**
 * UI Icons
 */
export const uiIcons = {
  collapse: '▼',
  expand: '▶',
  issue: '⭕',
  pullRequest: '🔀',
} as const;

/**
 * Cost Estimate Icons
 */
export const costEstimateIcons = {
  lightweight: '💡',
  standard: '💰',
  complex: '⚠️',
} as const;

// Type exports for better TypeScript support
export type StatusColors = typeof statusColors;
export type PhaseQueueStatusColors = typeof phaseQueueStatusColors;
export type HttpMethodColors = typeof httpMethodColors;
export type AdwStatusColors = typeof adwStatusColors;
