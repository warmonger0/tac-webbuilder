# Playwright MCP Integration

## What is Playwright MCP?

The Playwright Model Context Protocol (MCP) server enables Claude Code to:
- Control browsers programmatically
- Run E2E tests automatically
- Capture screenshots and videos
- Validate visual appearance
- Test user interactions

## Setup

### 1. Configure MCP
```bash
# Copy sample configuration
cp .mcp.json.sample .mcp.json
```

### 2. Install Playwright
```bash
npm install -D playwright
npx playwright install chromium
```

### 3. Verify Setup
The Playwright MCP server will automatically start when Claude Code runs.

## Usage

### In ADW Workflows

ADW workflows automatically use Playwright MCP for:
- **Testing Phase**: E2E test execution
- **Review Phase**: Visual validation with screenshots
- **Documentation Phase**: Capturing UI examples

### Manual Testing

Use `/test_e2e` command to run tests on demand.

### Visual Review

Use `/review` command to capture screenshots for review.

## Configuration

### Browser Settings
Edit `playwright-mcp-config.json`:

```json
{
  "browser": {
    "browserName": "chromium",  // or "firefox", "webkit"
    "launchOptions": {
      "headless": true,  // Set to false for debugging
      "slowMo": 0        // Milliseconds to slow down operations
    }
  }
}
```

### Video Recording
Videos are saved to `./videos/` directory when tests run.

To disable video recording:
```json
{
  "contextOptions": {
    "recordVideo": null
  }
}
```

### Viewport Size
Default: 1920x1080

To change:
```json
{
  "contextOptions": {
    "viewport": {
      "width": 1280,
      "height": 720
    }
  }
}
```

## Troubleshooting

### MCP Server Won't Start
- Ensure Node.js is installed
- Run `npx @playwright/mcp@latest --version` to verify
- Check `.mcp.json` syntax is valid

### Browser Launch Fails
- Run `npx playwright install chromium`
- Check system dependencies: `npx playwright install-deps`

### Videos Not Recording
- Ensure `videos/` directory exists
- Check `recordVideo` config in `playwright-mcp-config.json`
- Verify disk space available

## Best Practices

### 1. Headless Mode
Keep `headless: true` for CI/CD and automated workflows.
Use `headless: false` only for local debugging.

### 2. Video Storage
Videos can be large. Add to `.gitignore`:
```
videos/
```

### 3. Screenshot Organization
Store screenshots in `logs/screenshots/` for easy access.

### 4. Test Stability
Use proper waits and selectors to avoid flaky tests:
```typescript
// Good: Wait for element
await page.waitForSelector('[data-testid="submit-button"]');

// Bad: Hard-coded timeout
await page.waitForTimeout(5000);
```

## Examples

See `docs/examples.md` for example test requests that leverage Playwright MCP.

## Integration with ADW

The Playwright MCP integration is seamlessly integrated with ADW workflows:

1. **Automatic Feature Testing**: When ADW implements a feature, it can automatically test it using Playwright MCP
2. **Visual Validation**: ADW captures screenshots to verify UI implementations match requirements
3. **Regression Testing**: ADW can validate that new changes don't break existing functionality
4. **Documentation Screenshots**: UI examples are automatically captured for documentation

This zero-touch testing capability ensures higher quality deliverables with minimal manual intervention.
