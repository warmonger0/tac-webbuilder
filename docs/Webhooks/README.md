# Webhooks Documentation

Webhook setup, configuration, and integration guides

**Created:** 2025-11-17

## Overview

This folder contains documentation for setting up and using webhooks with the tac-webbuilder system, including GitHub webhook integration for automated ADW workflows.

## Documentation

### Setup Guides

- **[WEBHOOK_TRIGGER_SETUP.md](WEBHOOK_TRIGGER_SETUP.md)** - Complete webhook setup guide including GitHub configuration, ngrok setup, and troubleshooting
- **[WEBHOOK_TRIGGER_QUICK_REFERENCE.md](WEBHOOK_TRIGGER_QUICK_REFERENCE.md)** - Quick reference for webhook configuration and common tasks

## Features

### GitHub Integration
- Automated ADW workflow triggering on issue/PR events
- Issue labeling automation
- Comment-based workflow control

### Webhook Processing
- Event validation and filtering
- Queue-based workflow execution
- Status reporting via GitHub comments

## Quick Start

1. **Read the Setup Guide**: [WEBHOOK_TRIGGER_SETUP.md](WEBHOOK_TRIGGER_SETUP.md)
2. **Configure GitHub Webhooks**: Follow the step-by-step instructions
3. **Set Up ngrok** (for local development): See ngrok configuration section
4. **Test Your Setup**: Use the validation steps in the setup guide

## Common Tasks

### Setting Up a New Webhook

See: [WEBHOOK_TRIGGER_SETUP.md](WEBHOOK_TRIGGER_SETUP.md) - Section: "GitHub Webhook Configuration"

### Troubleshooting Webhooks

See: [WEBHOOK_TRIGGER_SETUP.md](WEBHOOK_TRIGGER_SETUP.md) - Section: "Troubleshooting"

### Quick Reference

See: [WEBHOOK_TRIGGER_QUICK_REFERENCE.md](WEBHOOK_TRIGGER_QUICK_REFERENCE.md)

## Related Documentation

- [ADW Documentation](../ADW/) - ADW workflow system
- [API Reference](../api.md) - API endpoints including webhook endpoints
- [Troubleshooting](../troubleshooting.md) - General troubleshooting guide

## See Also

- **Main Docs**: [../README.md](../README.md)
- **System Architecture**: [../architecture.md](../architecture.md)
- **Configuration Guide**: [../configuration.md](../configuration.md)
