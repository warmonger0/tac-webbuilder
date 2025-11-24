# Multi-Phase Uploads User Guide

## Overview

The Multi-Phase Upload feature allows you to break down complex development tasks into sequential phases that execute automatically. When you upload a markdown file with multiple phases, the system:

1. **Detects and parses** phase headers automatically
2. **Creates a parent GitHub issue** and child issues for each phase
3. **Queues phases** with dependency tracking
4. **Executes phases sequentially** - each phase waits for the previous one to complete
5. **Monitors progress** via real-time UI updates

## Creating Multi-Phase Markdown Files

### Phase Header Formats

The parser recognizes multiple header formats for flexibility:

**Standard Format:**
```markdown
# Phase 1: Setup Database
```

**Variants (all supported):**
```markdown
## Phase: Two - Create API Endpoints
### Phase Three: Add Unit Tests
# Phase 4 - Integration Testing
## Phase - 5: Documentation
# Phase: Six Setup CI/CD
```

**Word-to-Number Conversion:**
The system automatically converts written numbers to digits:
- One → 1, Two → 2, Three → 3, Four → 4, Five → 5
- Six → 6, Seven → 7, Eight → 8, Nine → 9, Ten → 10

### Phase Requirements

- **Phase 1 is required** - Multi-phase files must start with Phase 1
- **No gaps allowed** - Phases must be sequential (1, 2, 3, ...)
- **No duplicates** - Each phase number must be unique
- **Maximum 20 phases** - System limit for performance
- **Minimum content** - Each phase should have meaningful content

### External Document References

You can reference external documentation files that will be made available to the ADW during execution:

**Supported Formats:**
```markdown
See the architecture.md for database schema details
Refer to docs/api-design.md for endpoint specifications
Check design-doc.md in the project root
Reference the ~/project/specs/feature.md file
```

**Extraction Pattern:**
The parser looks for phrases like:
- "see the [filename].md"
- "refer to [path]/[filename].md"
- "check [filename].md"
- "reference [path]/[filename].md"

External files are passed to the ADW as additional context for that phase.

## Example Multi-Phase File

```markdown
# Multi-Phase Feature: User Authentication System

This request implements a complete user authentication system with OAuth2 support.

---

# Phase 1: Database Schema and Models

Create the database schema for user authentication.

**Tasks:**
- Create users table with email, password_hash, and metadata
- Create sessions table for managing active sessions
- Add indexes for email lookups and session expiry
- Create SQLAlchemy models for User and Session

**External Reference:**
See the database-schema.md for detailed table structures.

---

# Phase 2: Authentication API Endpoints

Implement the authentication API endpoints.

**Tasks:**
- POST /api/auth/register - User registration
- POST /api/auth/login - User login
- POST /api/auth/logout - Session termination
- GET /api/auth/me - Get current user info
- Add input validation and error handling

Refer to api-design.md for endpoint specifications.

---

# Phase 3: Frontend Login Components

Create React components for authentication UI.

**Tasks:**
- LoginForm component with email/password inputs
- RegisterForm component with validation
- AuthContext for managing authentication state
- Protected route wrapper component
- Add Tailwind styling

---

# Phase 4: Integration Tests

Add comprehensive integration tests.

**Tasks:**
- Test registration flow end-to-end
- Test login/logout flow
- Test protected route access
- Test session expiry
- Achieve >80% test coverage
```

## Uploading Multi-Phase Files

### Using the Web Interface

1. **Navigate to "Create New Request"**
2. **Upload your .md file** via:
   - Drag and drop into the upload area
   - Click to browse and select file
3. **Review the Phase Preview modal:**
   - Verify phase count is correct
   - Check that all phases were detected
   - Review external document references
   - Check for validation warnings/errors
4. **Click "Confirm and Submit"**
   - Parent issue and child issues are created automatically
   - Phases are queued for execution
   - Phase 1 starts immediately

### Phase Preview Modal

The preview modal shows:

- **Phase Count Badge** - Total number of phases detected
- **Phase Cards** - One card per phase with:
  - Phase number and title
  - Content preview (first 200 characters)
  - External document references (if any)
  - Dependency information
- **Validation Results:**
  - ✅ Success: All validations passed
  - ⚠️ Warnings: Non-critical issues
  - ❌ Errors: Must fix before submission

## Monitoring Execution

### Queue Display

After submission, monitor your phases in the **"ZTE Hopper Queue"** panel:

#### Status Colors

- 🟢 **Ready** (Green) - Phase is ready to execute
- 🔵 **Running** (Blue) - Phase is currently executing
- ⚪ **Queued** (Gray) - Waiting for dependencies
- ✅ **Completed** (Green checkmark) - Phase finished successfully
- ❌ **Failed** (Red X) - Phase execution failed
- 🚫 **Blocked** (Red) - Blocked by failed dependency

#### Queue Card Information

Each phase card shows:
- **Phase number and title**
- **Current status**
- **Dependency chain** - "Depends on Phase X"
- **GitHub issue link** - Click to view issue details
- **External docs** - Referenced files for this phase
- **Error message** - If phase failed

### Auto-Refresh

The queue display auto-refreshes every **10 seconds** to show the latest status. You can also manually refresh by switching tabs.

### GitHub Comments

Progress updates are posted to the **parent GitHub issue** automatically:

**On Phase Completion:**
```markdown
## Phase 2 Completed ✅

**Issue:** #456
**Status:** Completed

Phase 2 has completed successfully. Moving to Phase 3.

[View Phase 2 Details](https://github.com/owner/repo/issues/456)
```

**On Phase Failure:**
```markdown
## Phase 1 Failed ❌

**Issue:** #455
**Status:** Failed
**Error:** Database connection timeout

Phase 1 has failed. Subsequent phases have been blocked.

[View Phase 1 Details](https://github.com/owner/repo/issues/455)
```

## Sequential Execution Model

### How It Works

1. **Phase 1 starts immediately** after submission (status: ready → running)
2. **Phases 2+ remain queued** until their dependencies complete
3. **When Phase N completes:**
   - Phase N is marked complete
   - Phase N+1 becomes ready
   - Phase N+1 starts execution automatically
4. **If Phase N fails:**
   - All subsequent phases are blocked
   - Parent issue receives failure notification
   - Manual intervention required to restart

### Dependency Chain

```
Phase 1 (ready) → Phase 2 (queued) → Phase 3 (queued)
         ↓
Phase 1 (running)
         ↓
Phase 1 (completed) → Phase 2 (ready) → Phase 3 (queued)
                              ↓
                     Phase 2 (running)
                              ↓
                     Phase 2 (completed) → Phase 3 (ready)
                                                    ↓
                                           Phase 3 (running)
                                                    ↓
                                           Phase 3 (completed)
```

## Troubleshooting

### Phase Not Detected

**Problem:** Phase header not recognized

**Possible Causes:**
- Missing "Phase" keyword in header
- Using unsupported header format
- Phase number missing or invalid

**Solutions:**
✅ Use standard format: `# Phase 1: Title`
✅ Include phase number (1, 2, 3, or One, Two, Three)
✅ Ensure "Phase" keyword is present
✅ Check for typos in phase header

### Validation Errors

#### "Phase 1 is required"
Multi-phase files must start with Phase 1. Renumber your phases to start from 1.

#### "Gap detected in phase sequence"
Phases must be sequential. If you have Phases 1, 3, 4, add the missing Phase 2.

#### "Duplicate phase numbers found"
Each phase must have a unique number. Renumber duplicate phases.

#### "Maximum 20 phases exceeded"
System limit reached. Consider splitting into multiple requests or combining some phases.

### Phase Stays in "Queued" Status

**Problem:** Phase remains queued after previous phase completes

**Possible Causes:**
- PhaseCoordinator polling issue
- Database connection problem
- Dependency not properly marked complete

**Solutions:**
1. **Check the previous phase status** - Ensure it's marked complete
2. **Verify workflow_history** - Check if workflow completed successfully
3. **Wait for next poll cycle** - System polls every 10 seconds
4. **Check server logs** - Look for PhaseCoordinator errors

**Manual Fix:**
If needed, you can manually update phase status via API:
```bash
curl -X POST http://localhost:8000/api/queue/{queue_id}/status \
  -H "Content-Type: application/json" \
  -d '{"status": "ready"}'
```

### Phase Failed - How to Restart

**Problem:** Phase failed and blocked subsequent phases

**Current Limitation:**
There is no automatic restart mechanism yet. You must:

1. **Investigate the failure:**
   - Click the GitHub issue link
   - Review error logs
   - Check ADW state file
2. **Fix the underlying issue** in your codebase
3. **Create a new single-phase request** for the failed phase
4. **Or re-submit** the entire multi-phase request

**Future Enhancement:**
A "Retry Phase" feature is planned for Phase 5.

### External Document Not Found

**Problem:** Referenced document not available to ADW

**Possible Causes:**
- File doesn't exist in project
- Incorrect path specified
- File not committed to git

**Solutions:**
✅ Verify file exists: `ls path/to/file.md`
✅ Check path is relative to project root
✅ Ensure file is committed to git
✅ Use correct filename and extension

### WebSocket Updates Not Working

**Problem:** Queue display not updating automatically

**Possible Causes:**
- WebSocket connection failed
- Browser refresh needed
- Server WebSocket manager not initialized

**Solutions:**
1. **Refresh the page** - Reconnect WebSocket
2. **Check browser console** - Look for WebSocket errors
3. **Manually refresh** - Click "In Progress" tab to reload
4. **Check server status** - Ensure FastAPI server running

## Best Practices

### Phase Granularity

**Good Phase Size:**
- 1-3 hours of development work
- Clear, testable deliverable
- Minimal dependencies on future phases

**Too Small:**
```markdown
# Phase 1: Create User Model
# Phase 2: Add Email Field
# Phase 3: Add Password Field
```
❌ Too granular - combine into one phase

**Too Large:**
```markdown
# Phase 1: Implement Complete Authentication System
```
❌ Too broad - split into smaller phases

**Just Right:**
```markdown
# Phase 1: Database Schema and Models
# Phase 2: Authentication API Endpoints
# Phase 3: Frontend Login Components
# Phase 4: Integration Tests
```
✅ Each phase is substantial but focused

### Writing Phase Content

**Good Phase Description:**
```markdown
# Phase 2: Authentication API Endpoints

Implement the authentication API endpoints using FastAPI.

**Requirements:**
- POST /api/auth/register - User registration with validation
- POST /api/auth/login - Login with JWT token generation
- POST /api/auth/logout - Session invalidation
- GET /api/auth/me - Get current user profile

**Implementation Details:**
- Use Pydantic models for request/response validation
- Hash passwords with bcrypt
- Generate JWT tokens with 24-hour expiry
- Return 401 for authentication failures

**Success Criteria:**
- All endpoints return correct status codes
- Passwords are never stored in plaintext
- JWT tokens include user_id and expiry
- Error messages are user-friendly

Refer to api-design.md for detailed endpoint specifications.
```

**What Makes It Good:**
✅ Clear requirements list
✅ Specific technical details
✅ Success criteria defined
✅ External reference for details

### Handling Dependencies

**Explicit Dependencies:**
```markdown
# Phase 2: API Layer

This phase requires:
- Database schema from Phase 1
- User and Session models

Reference the models in src/models/user.py created in Phase 1.
```

**Implicit Order:**
The system enforces sequential execution, so Phase 2 always waits for Phase 1. Mention dependencies explicitly to help the ADW understand context.

### Testing Phases

**Recommended Pattern:**
```markdown
# Phase 1: Core Feature Implementation
# Phase 2: Unit Tests for Phase 1
# Phase 3: Additional Features
# Phase 4: Integration Tests for All Features
```

**Why This Works:**
- Each phase is tested before proceeding
- Tests serve as documentation
- Failures caught early
- Easier to debug issues

## Advanced Usage

### Conditional Execution

**Pattern:**
```markdown
# Phase 1: Setup Core Feature

Implement the feature. If tests pass, proceed to Phase 2.
If tests fail, fix issues before continuing.

# Phase 2: Optimization

Optimize the implementation from Phase 1.
Skip this phase if Phase 1 performance is already acceptable.
```

**Note:** The system doesn't support automatic skip logic yet. ADW will execute all phases.

### Rollback Strategy

**Pattern:**
```markdown
# Phase 3: Database Migration

Apply database migration for new fields.

**Rollback Instructions:**
If this phase fails, run:
```bash
python manage.py migrate down 001
```

Keep rollback instructions in phase content for manual recovery.
```

### Multi-Repository Phases

**Pattern:**
```markdown
# Phase 1: Backend API Changes

Update the backend API in the main repository.

# Phase 2: Frontend Updates

Update the frontend repository to use the new API.

**Note:** Manually trigger Phase 2 in the frontend repo after Phase 1 completes.
```

**Current Limitation:** Multi-phase uploads work within a single repository. Coordinate cross-repo changes manually.

## FAQ

**Q: Can I edit phases after submission?**
A: No, phases are immutable once submitted. You can cancel remaining phases or submit a new request.

**Q: What happens if I close the browser?**
A: Phases continue executing in the background. Open the app again to view progress.

**Q: Can I run multiple multi-phase requests simultaneously?**
A: Yes, the system supports concurrent multi-phase requests for different parent issues.

**Q: How do I cancel a queued phase?**
A: Use the delete button on the phase card in the queue display (coming in future update).

**Q: What if a phase takes too long?**
A: Check the GitHub issue for the phase. The ADW may still be working. Standard timeout is 30 minutes.

**Q: Can I prioritize one multi-phase request over another?**
A: Not yet. Phases execute in the order they were submitted.

**Q: How do I restart a failed phase?**
A: Currently manual - create a new single-phase request. Automatic retry coming in future update.

## Related Documentation

- **[Feature Implementation Guide](../implementation/README-multi-phase-upload.md)** - Technical architecture
- **[Phase Parser API](../../app/client/src/utils/phaseParser.ts)** - Parser implementation details
- **[Queue API Endpoints](../../app/server/routes/queue_routes.py)** - REST API documentation
- **[Phase Coordinator Service](../../app/server/services/phase_coordinator.py)** - Background service details

## Support

If you encounter issues:

1. **Check server logs** - `app/server/logs/` for error details
2. **Inspect queue database** - `app/server/db/database.db` → `phase_queue` table
3. **Review GitHub issues** - Check parent and child issues for status
4. **File a bug report** - Create an issue with:
   - Phase markdown file content
   - Error messages from logs
   - Screenshots of queue display
   - Expected vs actual behavior

---

**Version:** 1.0.0 (Phase 4 - Testing & Documentation)
**Last Updated:** 2025-11-24
**Status:** ✅ Complete
