# Frontend Configuration System

This directory contains the centralized configuration system for the tac-webbuilder frontend application.

## Overview

The configuration system provides a single source of truth for all application settings, including:

- **API endpoints and request configuration**
- **WebSocket URLs and connection settings**
- **localStorage key management**
- **GitHub integration settings**
- **Environment-specific overrides**
- **Application constants and branding**

## Architecture

### Directory Structure

```
src/config/
├── index.ts              # Central export point
├── types.ts              # TypeScript type definitions
├── constants.ts          # Application constants
├── environment.ts        # Environment detection
├── api.config.ts         # API configuration
├── websocket.config.ts   # WebSocket configuration
├── storage.config.ts     # localStorage configuration
├── github.config.ts      # GitHub integration
└── README.md             # This file
```

### Configuration Modules

#### 1. `constants.ts` - Application Constants
General application-wide constants including branding and versioning.

```typescript
import { constants } from '@/config';

console.log(constants.NAME);       // 'tac-webbuilder'
console.log(constants.TAGLINE);    // 'Build web apps with natural language'
console.log(constants.VERSION);    // '1.0.0'
```

#### 2. `environment.ts` - Environment Detection
Detects and manages environment-specific settings (development, staging, production).

```typescript
import { environmentConfig } from '@/config';

if (environmentConfig.isDevelopment()) {
  console.log('Running in development mode');
}

console.log(environmentConfig.CURRENT); // 'development' | 'staging' | 'production'
```

#### 3. `api.config.ts` - API Configuration
Centralized API endpoint URLs, timeouts, and retry logic.

```typescript
import { apiConfig } from '@/config';

fetch(`${apiConfig.BASE_PATH}/workflows`); // '/api/workflows'
fetch(apiConfig.WEBHOOK_URL);              // 'http://localhost:8001/webhook-status'
```

#### 4. `websocket.config.ts` - WebSocket Configuration
WebSocket connection URLs, ports, and reconnection settings.

```typescript
import { websocketConfig } from '@/config';

// Build WebSocket URL with helper function
const wsUrl = websocketConfig.getWebSocketUrl('/ws/workflows');
// Result: 'ws://localhost:8000/ws/workflows'

// Build WebSocket URL with parameters
const adwUrl = websocketConfig.getWebSocketUrl('/ws/adw-state/:adwId', {
  adwId: 'adw-123'
});
// Result: 'ws://localhost:8000/ws/adw-state/adw-123'
```

#### 5. `storage.config.ts` - Storage Configuration
localStorage key management with namespace prefixing.

```typescript
import { storageConfig } from '@/config';

// Get namespaced storage key
const key = storageConfig.REQUEST_FORM_STATE_KEY;
// Result: 'tac-webbuilder-request-form-state'

// Use helper to create custom namespaced keys
const customKey = storageConfig.getStorageKey('my-data');
// Result: 'tac-webbuilder-my-data'

// Clear all app storage
storageConfig.clearAppStorage();
```

#### 6. `github.config.ts` - GitHub Integration
GitHub repository URLs and helper functions for issue/PR links.

```typescript
import { githubConfig } from '@/config';

// Get issue URL
const issueUrl = githubConfig.getIssueUrl(123);
// Result: 'https://github.com/warmonger0/tac-webbuilder/issues/123'

// Get PR URL
const prUrl = githubConfig.getPullRequestUrl(456);
// Result: 'https://github.com/warmonger0/tac-webbuilder/pull/456'
```

## Usage Examples

### Import the Unified Config Object

```typescript
import { config } from '@/config';

// Access any configuration
const apiBase = config.api.BASE_PATH;
const wsPort = config.websocket.PORT;
const storageKey = config.storage.ACTIVE_TAB_KEY;
const isDev = config.environment.isDevelopment();
```

### Import Individual Modules

```typescript
import { apiConfig, websocketConfig, githubConfig } from '@/config';

// Use specific configuration modules
const endpoint = apiConfig.ENDPOINTS.WORKFLOWS;
const wsUrl = websocketConfig.getWebSocketUrl('/ws/workflows');
const issueLink = githubConfig.getIssueUrl(108);
```

### Using in Components

```typescript
import { config } from '@/config';

function MyComponent() {
  const handleClick = () => {
    // Use GitHub helper to open issue
    const issueUrl = config.github.getIssueUrl(123);
    window.open(issueUrl, '_blank');
  };

  // Use WebSocket configuration
  const wsUrl = config.websocket.getWebSocketUrl('/ws/workflows');

  return <div>...</div>;
}
```

### Using in API Clients

```typescript
import { config } from '@/config';

async function fetchWorkflows() {
  const response = await fetch(`${config.api.BASE_PATH}/workflows`, {
    // Use configured timeout
    signal: AbortSignal.timeout(config.api.DEFAULT_TIMEOUT),
  });
  return response.json();
}
```

## Environment Variables

The configuration system supports environment variable overrides for flexible deployment:

### Available Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_GITHUB_REPO_OWNER` | GitHub repository owner | `warmonger0` |
| `VITE_GITHUB_REPO_NAME` | GitHub repository name | `tac-webbuilder` |
| `VITE_WEBSOCKET_PORT` | WebSocket port number | `8000` |
| `VITE_API_TIMEOUT` | API request timeout (ms) | `30000` |
| `VITE_WEBHOOK_URL` | Webhook service URL | `http://localhost:8001/webhook-status` |

### Setting Environment Variables

Create a `.env` file in `app/client/`:

```env
# .env.local (for local development overrides)
VITE_WEBSOCKET_PORT=8080
VITE_GITHUB_REPO_OWNER=myorg
VITE_API_TIMEOUT=60000
```

Environment-specific files:
- `.env.development` - Development environment
- `.env.staging` - Staging environment
- `.env.production` - Production environment

## Adding New Configuration

### Step 1: Update Types

Add your new configuration interface to `types.ts`:

```typescript
export interface MyNewConfig {
  SETTING_ONE: string;
  SETTING_TWO: number;
  helperFunction: () => void;
}

// Add to AppConfig interface
export interface AppConfig {
  app: AppConstants;
  api: ApiConfig;
  myNew: MyNewConfig; // Add here
  // ... other configs
}
```

### Step 2: Create Configuration Module

Create `my-new.config.ts`:

```typescript
import type { MyNewConfig } from './types';

export const myNewConfig: MyNewConfig = {
  SETTING_ONE: 'value',
  SETTING_TWO: 42,
  helperFunction: () => {
    // Implementation
  },
};

export default myNewConfig;
```

### Step 3: Export from Index

Update `index.ts` to export your new configuration:

```typescript
import { myNewConfig } from './my-new.config';

export const config: AppConfig = {
  app: constants,
  api: apiConfig,
  myNew: myNewConfig, // Add here
  // ... other configs
};

// Re-export for direct imports
export { myNewConfig };
```

### Step 4: Use Your Configuration

```typescript
import { config } from '@/config';

const value = config.myNew.SETTING_ONE;
config.myNew.helperFunction();
```

## Testing Configuration

### Unit Testing with Mocked Config

```typescript
import { vi } from 'vitest';
import * as configModule from '@/config';

// Mock the config
vi.spyOn(configModule, 'config', 'get').mockReturnValue({
  ...configModule.config,
  api: {
    ...configModule.config.api,
    BASE_PATH: '/mock-api',
  },
});
```

### Testing Environment Detection

```typescript
import { environmentConfig } from '@/config';

// Mock import.meta.env
vi.stubGlobal('import', {
  meta: {
    env: {
      MODE: 'production',
    },
  },
});

// Now environmentConfig.CURRENT will be 'production'
```

## Migration Guide

### Replacing Hardcoded Values

**Before:**
```typescript
const API_BASE = '/api';
const wsUrl = `ws://localhost:8000/ws/workflows`;
const storageKey = 'tac-webbuilder-form-state';
```

**After:**
```typescript
import { config } from '@/config';

const apiBase = config.api.BASE_PATH;
const wsUrl = config.websocket.getWebSocketUrl('/ws/workflows');
const storageKey = config.storage.REQUEST_FORM_STATE_KEY;
```

### Replacing GitHub URLs

**Before:**
```typescript
const issueUrl = `https://github.com/warmonger0/tac-webbuilder/issues/${issueNumber}`;
```

**After:**
```typescript
import { config } from '@/config';

const issueUrl = config.github.getIssueUrl(issueNumber);
```

## Best Practices

1. **Always import from `@/config`** - Use the centralized export, not individual files
2. **Use helper functions** - Prefer `config.websocket.getWebSocketUrl()` over manual URL building
3. **Never hardcode values** - All configuration should come from the config system
4. **Document new settings** - Update this README when adding new configuration
5. **Support environment variables** - Allow overrides for all environment-specific settings
6. **Test with different environments** - Verify your code works in dev, staging, and production

## Troubleshooting

### Configuration Not Loading
- Check that you're importing from `@/config`, not a relative path
- Verify environment variables are prefixed with `VITE_`
- Restart dev server after changing `.env` files

### WebSocket Connection Fails
- Verify `VITE_WEBSOCKET_PORT` matches backend WebSocket server port
- Check protocol detection (ws: vs wss:) matches your deployment

### GitHub Links Incorrect
- Verify `VITE_GITHUB_REPO_OWNER` and `VITE_GITHUB_REPO_NAME` are correct
- Check helper functions in `github.config.ts`

## Related Documentation

- [TypeScript Standards](/.claude/references/typescript_standards.md)
- [Code Quality Standards](/.claude/references/code_quality_standards.md)
