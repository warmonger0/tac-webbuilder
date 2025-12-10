---
description: Update project documentation and /prime command to capture completed work from current session
---

# Update Documentation - Capture Session Work

Updates project documentation and the `/prime` command based on work completed in the current session.

## Usage

`/updatedocs [session_summary]`

**Example:**
- `/updatedocs` - Interactive mode (asks questions about session work)
- `/updatedocs Added WebSocket support to Panel 8` - Quick update with summary

## Instructions

### Step 1: Analyze Session Work

First, understand what was accomplished in the current session:

1. **Review recent commits:**
   ```bash
   git log -5 --oneline --no-decorate
   git log -1 --stat
   ```

2. **Check current changes:**
   ```bash
   git status
   git diff --stat main
   ```

3. **Identify the scope of changes:**
   - Frontend changes (app/client/)
   - Backend changes (app/server/)
   - ADW workflow changes (adws/)
   - Documentation changes (docs/, app_docs/, .claude/commands/)
   - Infrastructure/scripts changes (scripts/, configs)

### Step 2: Determine Documentation Updates Needed

Based on the analysis, determine which documentation needs updating:

#### A. Feature Documentation (app_docs/)
**When to create/update:**
- New feature implemented
- Significant enhancement to existing feature
- Architectural change that affects how features work

**Action:**
- If new feature: Create `app_docs/feature-{unique-id}-{descriptive-name}.md`
- If existing feature: Update relevant `app_docs/feature-*.md` file
- Follow the format from `.claude/commands/document.md`

#### B. Quick Start Guides (.claude/commands/quick_start/)
**When to update:**
- New subsystem added (e.g., new panel, new service layer)
- Tech stack changes (new major library, framework change)
- Startup commands changed
- Port allocation changed

**Files to consider:**
- `frontend.md` - React components, panels, state management
- `backend.md` - API endpoints, services, database
- `adw.md` - ADW workflows, phases
- `docs.md` - Documentation structure

#### C. Reference Documentation (.claude/commands/references/)
**When to update:**
- API endpoints added/changed → `api_endpoints.md`
- ADW workflows added/changed → `adw_workflows.md`
- Architecture changes → `architecture_overview.md`
- New observability features → `observability.md`
- New analytics features → `analytics.md`
- New planned features → `planned_features.md`

#### D. Prime Command (.claude/commands/prime.md)
**When to update (HIGH BAR - only for significant changes):**
- New core feature added (impacts "Four Core Features")
- Architecture change (new database, tech stack change)
- Panel status changed (stub → active → complete)
- New session milestones (e.g., "Sessions 7-14" becomes "Sessions 7-16")
- Port configuration changed
- New health check categories added

**DO NOT update prime.md for:**
- Minor bug fixes
- Small enhancements
- Internal refactoring
- Individual component updates

#### E. Conditional Documentation (.claude/commands/conditional_docs.md)
**When to update:**
- New feature documentation created (add entry with conditions)
- Documentation reorganized (update loading strategies)
- New quick reference created

### Step 3: Interactive Session Analysis (if no summary provided)

If user didn't provide a summary, ask these questions:

```
Please help me understand what was accomplished in this session:

1. What was the main goal or feature implemented?
2. Which subsystems were modified? (Frontend/Backend/ADW/Docs/Scripts)
3. Were any new API endpoints added?
4. Were any new UI panels or components created?
5. Were there any architectural changes?
6. Were any new observability/analytics features added?
7. Should this be documented as a new feature in app_docs/?
8. Does this warrant updating the /prime command?
```

Use `AskUserQuestion` tool to gather this information interactively.

### Step 4: Update Documentation Files

For each identified documentation file:

1. **Read the current file** using the Read tool
2. **Identify the section to update** (or determine where to add new content)
3. **Update with new information:**
   - Add new features to lists
   - Update status indicators (stub → active → complete)
   - Add new API endpoints
   - Update session numbers
   - Add new components/services
4. **Use the Edit tool** to make precise updates

### Step 5: Update Prime Command (if warranted)

**Only update if changes are significant enough to warrant high-level overview update.**

Common updates:
- Panel status: Change from `Panel 8: Review (stub)` → `Panel 8: Review (active)`
- Session milestones: Add to relevant section (e.g., WebSocket, Observability)
- New features: Add to existing sections or create new subsection
- Architecture: Update Quick Architecture section
- Commands: Update Quick Commands if new scripts added

**Format preservation:**
- Maintain token counts in annotations `[~300 tokens]`
- Keep progressive loading structure
- Preserve all existing sections
- Keep concise (target ~150 tokens for prime itself)

### Step 6: Update Conditional Docs (if new feature docs created)

If you created new feature documentation:

1. Read `.claude/commands/conditional_docs.md`
2. Find the appropriate section (Feature Documentation or create new category)
3. Add entry with:
   - File path
   - Brief description (one line)
   - Conditions (2-5 bullet points about when to load this doc)

**Format:**
```md
- `app_docs/feature-{id}-{name}.md` - Brief description
  - Conditions:
    - When working with {specific component/feature}
    - When implementing {related functionality}
    - When troubleshooting {specific issues}
```

### Step 7: Verify Updates

After updating documentation:

1. **Check token counts** (if updated prime or quick_start):
   ```bash
   wc -w .claude/commands/prime.md
   wc -w .claude/commands/quick_start/*.md
   ```
   - Prime: Target ~300-400 words (~150 tokens)
   - Quick Start: Target ~600-800 words (~300-400 tokens)
   - References: Target ~1,800-3,400 words (~900-1,700 tokens)

2. **Verify links and references** are still valid

3. **Check formatting** (markdown structure, code blocks, bullet points)

### Step 8: Report to User

Summarize what was updated:

```
Documentation Updated:

✅ Feature Documentation:
   - Created: app_docs/feature-{id}-{name}.md

✅ Quick Start Guides:
   - Updated: .claude/commands/quick_start/frontend.md
     → Added Panel 8 WebSocket migration

✅ Reference Documentation:
   - Updated: .claude/commands/references/observability.md
     → Added new analytics endpoints

✅ Prime Command:
   - Updated: .claude/commands/prime.md
     → Panel 8 status: stub → active
     → Added Session 19 to WebSocket section

✅ Conditional Documentation:
   - Updated: .claude/commands/conditional_docs.md
     → Added entry for new feature documentation

Token Counts:
- Prime: 387 words (~150 tokens) ✓
- Frontend Quick Start: 634 words (~317 tokens) ✓
```

## Examples

### Example 1: New Feature Implementation

**User:** `/updatedocs Implemented real-time chat in Panel 8`

**Actions:**
1. Create `app_docs/feature-{id}-panel-8-real-time-chat.md`
2. Update `.claude/commands/quick_start/frontend.md`:
   - Change Panel 8 status from "stub" to "active"
   - Add WebSocket info if relevant
3. Update `.claude/commands/prime.md`:
   - Change Panel 8 line to "Panel 8: Chat (active)"
4. Update `.claude/commands/conditional_docs.md`:
   - Add entry for new feature doc

### Example 2: New API Endpoints

**User:** `/updatedocs Added 5 new analytics API endpoints`

**Actions:**
1. Update `.claude/commands/references/api_endpoints.md`:
   - Add new endpoints with request/response formats
2. Update `.claude/commands/quick_start/backend.md`:
   - Update endpoint count (36 → 41)
3. Check if prime.md needs updating (usually not for API additions)
4. Update conditional_docs.md if analytics docs created

### Example 3: Bug Fixes Only

**User:** `/updatedocs Fixed WebSocket connection bug`

**Response:**
```
Bug fixes typically don't require documentation updates.

However, consider updating if:
- The fix changes how developers should use the API
- The fix reveals a common pitfall worth documenting
- Troubleshooting docs should include this solution

Would you like to add this to troubleshooting documentation?
```

## Guidelines

### What Requires Documentation Updates?

**YES - Update docs:**
- ✅ New features or capabilities
- ✅ New API endpoints
- ✅ New UI components/panels
- ✅ Architecture changes
- ✅ Breaking changes
- ✅ New configuration options
- ✅ New scripts or tools
- ✅ Panel status changes (stub → active → complete)

**NO - Skip docs update:**
- ❌ Bug fixes (unless they change usage)
- ❌ Code refactoring (internal only)
- ❌ Test additions
- ❌ Dependency updates
- ❌ Performance optimizations (internal)
- ❌ Minor UI tweaks

### Prime Command Update Criteria

**Update prime.md only if:**
- Core feature list changes
- New major subsystem added
- Panel status changes
- Session milestone achieved (e.g., completed WebSocket migration)
- Architecture fundamentally changed
- New health check category added

**Do NOT update prime.md for:**
- Individual component changes
- API endpoint additions
- Bug fixes
- Internal refactoring
- Minor features

### Token Budget Targets

- **Prime:** ~150 tokens (300-400 words)
- **Quick Start:** ~300-400 tokens (600-800 words)
- **References:** ~900-1,700 tokens (1,800-3,400 words)
- **Feature Docs:** ~200-500 tokens (400-1,000 words)

## Best Practices

1. **Be selective** - Not every change needs documentation
2. **Update existing docs** rather than creating new ones when possible
3. **Keep it concise** - Documentation should be scannable
4. **Use progressive loading** - Point to detailed docs rather than duplicating
5. **Verify token counts** - Ensure docs stay within target ranges
6. **Check cross-references** - Update all references to changed components
7. **Use consistent formatting** - Follow existing patterns
8. **Add conditions** - Help future developers know when to load docs

## Notes

- Use the `document` command for comprehensive ADW-based feature documentation
- Use `/updatedocs` for quick session-based updates to existing docs
- Prime command is the "table of contents" - keep it minimal and high-level
- Quick Start guides are domain-specific entry points - keep them focused
- Reference docs are for quick lookups - keep them comprehensive but concise
- Feature docs are for specific implementation details - can be more verbose
