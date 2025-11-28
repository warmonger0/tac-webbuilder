/**
 * Services Configuration
 * Centralized configuration for service definitions and ordering
 */

/**
 * Service Display Order
 * Defines the order in which services are displayed in the System Status Panel
 */
export const serviceDisplayOrder = [
  'backend_api',
  'database',
  'webhook',
  'frontend',
  'cloudflare_tunnel',
  'github_webhook',
] as const;

/**
 * Service metadata and configuration
 */
export const serviceConfig = {
  backend_api: {
    name: 'Backend API',
    description: 'FastAPI server',
  },
  database: {
    name: 'Database',
    description: 'SQLite/PostgreSQL database',
  },
  webhook: {
    name: 'Webhook Service',
    description: 'GitHub webhook handler',
  },
  frontend: {
    name: 'Frontend',
    description: 'React development server',
  },
  cloudflare_tunnel: {
    name: 'Cloudflare Tunnel',
    description: 'Public URL tunnel',
  },
  github_webhook: {
    name: 'GitHub Webhook',
    description: 'GitHub integration',
  },
} as const;

// Type exports for better TypeScript support
export type ServiceType = typeof serviceDisplayOrder[number];
export type ServiceConfig = typeof serviceConfig;
