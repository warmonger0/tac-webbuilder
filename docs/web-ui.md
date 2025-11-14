# Web UI Guide

Guide to using the tac-webbuilder web interface for natural language-driven development.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [User Interface](#user-interface)
- [Features](#features)
- [Real-time Updates](#real-time-updates)
- [Tips and Best Practices](#tips-and-best-practices)

## Overview

The Web UI provides a visual, user-friendly interface for:
- Creating natural language feature requests
- Previewing generated GitHub issues
- Monitoring ADW workflow progress
- Viewing request history
- Managing project configuration

## Getting Started

### Start the Web UI

```bash
cd /path/to/tac-webbuilder

# Start both backend and frontend
./scripts/start_web_full.sh

# Or start separately:
# Terminal 1: Backend
./scripts/start_web_backend.sh

# Terminal 2: Frontend
./scripts/start_web_frontend.sh
```

### Access the Application

Open your browser to:
- **Frontend:** [http://localhost:5174](http://localhost:5174)
- **Backend API:** [http://localhost:8002](http://localhost:8002)
- **API Docs:** [http://localhost:8002/docs](http://localhost:8002/docs)

## User Interface

### Main Request Form

The primary interface for creating feature requests.

#### Components:

**1. Request Text Area**
- Large text input for your natural language request
- Supports markdown formatting
- Multi-line input with syntax highlighting
- Character count indicator

**2. Project Detection**
- Automatically detects current project
- Shows framework, package manager, test framework
- Manual override option for custom projects

**3. Repository Selector**
- Dropdown of available GitHub repositories
- Search and filter functionality
- Recently used repos at top

**4. Additional Options**
- Custom labels for the issue
- Priority level selection
- Workflow options (auto-merge, auto-deploy)

**5. Action Buttons**
- **Preview** - Generate issue preview without posting
- **Submit** - Create GitHub issue and trigger workflow
- **Save Draft** - Save request for later
- **Clear** - Reset form

### Issue Preview Panel

Before submitting, preview the generated GitHub issue.

**Shows:**
- Issue title (auto-generated from request)
- Issue body with formatted markdown
- Detected requirements and acceptance criteria
- Estimated complexity
- Suggested labels
- Related files and dependencies

**Actions:**
- Edit title or body before posting
- Add/remove labels
- Modify metadata
- Confirm and post
- Go back to edit request

### Request History

View and manage previous requests.

**Features:**
- Chronological list of all requests
- Status indicators (pending, in-progress, completed, merged)
- Filter by status, repo, date range
- Search by text
- Click to view details

**Request Card shows:**
- Request summary
- GitHub issue number and link
- Associated PR (if merged)
- Status and timestamp
- Quick actions (view, reopen, duplicate)

### Workflow Monitor

Real-time monitoring of ADW workflow execution.

**Displays:**
- Current workflow stage (planning, implementing, testing, reviewing)
- Progress percentage
- Recent log output
- Estimated time remaining
- Error messages (if any)

**Stages:**
1. **Planning** - Analyzing request and creating spec
2. **Implementing** - Writing code changes
3. **Testing** - Running tests and validation
4. **Reviewing** - Creating PR for review
5. **Completed** - PR merged or closed

## Features

### 1. Natural Language Input

**What you can write:**
- Feature descriptions in plain English
- Technical requirements with specific technologies
- User stories and acceptance criteria
- Multiple related features in one request
- References to existing code or patterns

**Examples:**
```
Add a dark mode toggle that:
- Switches between light and dark themes
- Persists preference in localStorage
- Includes smooth transition animations
- Updates all components
```

```
Create a user authentication system using Firebase:
- Email/password signup and login
- Google OAuth integration
- Password reset via email
- Protected routes
- User profile page
```

### 2. Project Detection

The UI automatically detects:
- **Framework:** React, Next.js, Vue, FastAPI, etc.
- **Package Manager:** npm, yarn, bun, pnpm
- **Test Framework:** Jest, Vitest, Pytest
- **Project Structure:** Source directories, test locations
- **Dependencies:** Installed packages and versions

**Manual Override:**
If auto-detection fails, you can:
- Specify framework manually
- Set custom project path
- Define test commands
- Configure build scripts

### 3. Repository Management

**Features:**
- List all accessible GitHub repos
- Search repos by name
- Filter by organization
- Recently used repos
- Favorites/starred repos
- Quick switch between repos

**Repository Info:**
- Name and description
- Default branch
- Open issues and PRs
- Last commit date
- Collaborators

### 4. Request Templates

Pre-defined templates for common requests:

- **Authentication** - Add user auth system
- **CRUD** - Create database CRUD operations
- **UI Component** - Add new UI component
- **API Endpoint** - Create new API endpoint
- **Testing** - Add test coverage
- **Documentation** - Generate docs

**Using Templates:**
1. Click "Use Template" button
2. Select template from list
3. Form pre-fills with template
4. Customize for your needs
5. Submit

### 5. Draft Management

Save requests as drafts to finish later.

**Features:**
- Auto-save as you type
- Named drafts
- Organize by project
- Quick load from history
- Export/import drafts

### 6. Collaboration

**Share requests with team:**
- Generate shareable link
- Export as markdown
- Copy to clipboard
- Email direct from UI

**Team features:**
- See who's working on what
- Comment on requests
- Request review before posting
- @mention team members

## Real-time Updates

The Web UI uses WebSockets for live updates.

### What's Updated in Real-time:

**1. Workflow Progress**
- Stage changes (planning → implementing → testing)
- Progress percentage updates
- Log output streaming
- Error notifications

**2. Issue Status**
- Issue opened/closed
- Labels added/removed
- PR created/merged
- Comments added

**3. Notifications**
- Toast notifications for events
- Desktop notifications (with permission)
- Sound alerts (configurable)
- Email digest (optional)

### WebSocket Connection

**Connection Status Indicator:**
- 🟢 Connected - Real-time updates active
- 🟡 Connecting - Attempting to connect
- 🔴 Disconnected - No real-time updates

**Auto-reconnect:**
- Automatically reconnects on disconnect
- Exponential backoff retry strategy
- Manual reconnect button if needed

### Event Types:

```javascript
// Workflow events
{
  "type": "workflow.started",
  "issue": 42,
  "repo": "owner/repo"
}

{
  "type": "workflow.progress",
  "issue": 42,
  "stage": "implementing",
  "progress": 45,
  "message": "Adding authentication..."
}

{
  "type": "workflow.completed",
  "issue": 42,
  "pr": 45,
  "status": "success"
}

// Issue events
{
  "type": "issue.updated",
  "issue": 42,
  "status": "closed",
  "merged": true
}
```

## Tips and Best Practices

### Writing Effective Requests

**Be Specific:**
```
❌ Add authentication
✅ Add user authentication with email/password login, JWT tokens, and password reset functionality using FastAPI and PostgreSQL
```

**Include Context:**
```
✅ Add a dark mode toggle to the header component. Use the existing theme context and persist preference in localStorage. Update all components to respect the theme.
```

**Specify Technologies:**
```
✅ Create a dashboard with Chart.js showing user growth (line chart) and revenue (bar chart). Fetch data from /api/analytics endpoint. Update every 30 seconds.
```

### Managing Large Requests

**Break into Multiple Issues:**
- Create separate requests for distinct features
- Use incremental development
- Reference related issues

**Use Checklists:**
```
Add e-commerce checkout flow:
- [ ] Shopping cart page
- [ ] Shipping information form
- [ ] Payment integration (Stripe)
- [ ] Order confirmation
- [ ] Email notifications
```

### Monitoring Workflows

**Check Progress Regularly:**
- Monitor workflow stage
- Review generated code in PR
- Check test results
- Look for errors or blockers

**Be Ready to Intervene:**
- If workflow stalls, check logs
- If tests fail, review and fix
- If code needs changes, comment on PR
- Approve and merge when ready

### Using History Effectively

**Find Previous Requests:**
- Use search to find similar patterns
- Filter by status to find completed work
- Review successful requests for reference

**Learn from History:**
- See what works well
- Identify common patterns
- Improve future requests

### Keyboard Shortcuts

- `Ctrl+Enter` - Submit request
- `Ctrl+P` - Preview issue
- `Ctrl+S` - Save draft
- `Ctrl+K` - Focus search
- `Esc` - Close modal/cancel
- `/` - Focus request input

## Troubleshooting

### Issue: Preview not loading

**Cause:** Backend API not reachable

**Solution:**
```bash
# Check backend is running
curl http://localhost:8002/health

# Restart backend
./scripts/start_web_backend.sh
```

### Issue: WebSocket disconnected

**Cause:** Network issue or backend restart

**Solution:**
- Click reconnect button
- Refresh page
- Check browser console for errors
- Verify backend is running

### Issue: Request fails to post

**Cause:** Invalid GitHub token or permissions

**Solution:**
```bash
# Check GitHub CLI auth
gh auth status

# Re-authenticate
gh auth login

# Verify token has repo permissions
```

### Issue: Project not detected

**Cause:** Not in a git repository or no GitHub remote

**Solution:**
- Ensure you're in a git repo
- Add GitHub remote: `git remote add origin <url>`
- Manually specify project path in UI

### Issue: Slow performance

**Cause:** Large history or too many real-time connections

**Solution:**
- Clear history (Settings → Clear History)
- Limit history display (show last 50)
- Disable desktop notifications
- Close unused browser tabs

## See Also

- [CLI Reference](cli.md) - Command-line interface
- [API Reference](api.md) - Backend API documentation
- [Examples](examples.md) - Example requests
- [Troubleshooting](troubleshooting.md) - Common issues
