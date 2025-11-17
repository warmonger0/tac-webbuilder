# Playwright MCP Lazy-Loading - Implementation & Verification

**Status**: ✅ Implemented & Verified
**Date Implemented**: 2025-11-14
**Commits**:
- `512d1a7` - feat: Implement lazy-loading for Playwright MCP to reduce context usage
- `00e9b0e` - docs: Add Playwright lazy-loading documentation with API routes test example

## Overview

Successfully implemented and verified a context optimization strategy that reduces Claude Code token usage by ~15k tokens (7.5%) through lazy-loading of Playwright MCP. The optimization defers Playwright installation until E2E testing is actually needed during ADW workflows.

## Problem Solved

**Before**: Playwright MCP was loaded in the main `.mcp.json`, consuming ~15k tokens in every Claude Code session
- All 23 Playwright browser automation tools loaded regardless of need
- Tools consumed context during Plan, Build, and other non-testing operations
- Wasted ~7.5% of available 200k token budget

**After**: Playwright MCP is lazy-loaded on-demand only when E2E tests execute
- Main sessions: 0 Playwright tools (saved 15k tokens)
- Plan phase: 0 Playwright tools (saved 15k tokens)
- Build phase: 0 Playwright tools (saved 15k tokens)
- Review phase: Playwright loaded dynamically when needed

## Architecture

### Main Repository Configuration

**File**: `.mcp.json`
```json
{
  "mcpServers": {}
}
```

**Result**: Clean context in all main Claude Code sessions - no Playwright overhead.

### Template Configuration

**File**: `playwright-mcp-config.json`
```json
{
  "launchOptions": {
    "headless": true,
    "args": ["--no-sandbox", "--disable-setuid-sandbox"]
  },
  "screenshotOptions": {
    "path": "videos/",
    "fullPage": true
  }
}
```

**Purpose**: Template for on-demand Playwright configuration in worktrees.

### Lazy-Loading Implementation

**File**: `adws/adw_modules/plan_executor.py`

**Function**: `install_playwright_mcp(worktree_path, logger)`

**When Called**: During Review phase when E2E validation is needed

**What It Does**:
1. Reads template from `playwright-mcp-config.json`
2. Updates worktree's `.mcp.json` to add Playwright server
3. Creates `videos/` directory for test recordings
4. Configures Playwright with worktree-specific paths

**Result**: Playwright becomes available in the worktree Claude Code session for E2E testing.

### Worktree Setup

**File**: `adws/adw_modules/plan_executor.py:_copy_mcp_files()`

**Behavior**:
- Copies `.mcp.json` from parent (which is empty)
- Creates empty MCP config if none exists
- Does NOT copy `playwright-mcp-config.json` (created on-demand later)
- Ensures each worktree starts clean without Playwright

## Implementation Details

### Phase-by-Phase Behavior

#### 1. Plan Phase (`adw_plan_iso.py`)
- Worktree `.mcp.json`: `{ "mcpServers": {} }`
- No Playwright tools loaded
- Context savings: ~15k tokens (7.5%)
- Claude Code focuses on planning without browser automation overhead

#### 2. Build Phase (`adw_build_iso.py`)
- Worktree `.mcp.json`: `{ "mcpServers": {} }` (still empty)
- No Playwright tools loaded
- Context savings: ~15k tokens (7.5%)
- Claude Code implements features without browser automation overhead

#### 3. Test Phase (`adw_test_iso.py`)
- SDLC workflows skip E2E tests (`--skip-e2e` flag)
- Unit and integration tests run without Playwright
- E2E testing deferred to Review phase for efficiency

#### 4. Review Phase (`adw_review_iso.py`)
- **Playwright lazy-loaded here!** 🎭
- Calls `install_playwright_mcp()` before review
- Worktree `.mcp.json` dynamically updated with Playwright configuration
- Screenshots captured for visual validation
- Acts as both E2E test and acceptance criteria verification

#### 5. Documentation Phase (`adw_document_iso.py`)
- Inherits Playwright from Review phase (if needed)
- Typically doesn't need browser automation

## Verification Test Case

### Test Scenario
Implemented Issue #3: "Display API routes dynamically in API Routes tab"
- Created backend `/api/routes` endpoint
- Used existing frontend RoutesView component
- Validated with Playwright-based E2E testing

### Test Results

**Issue**: #3
**PR**: #4
**ADW ID**: 4fc73599
**Workflow**: `adw_sdlc_iso.py`

#### Main Repository Verification
```bash
cat .mcp.json
# Output: { "mcpServers": {} }
```
✅ **Result**: No Playwright in main sessions

#### Plan Phase Verification
```bash
cat trees/4fc73599/.mcp.json  # During Plan phase
# Output: { "mcpServers": {} }
```
✅ **Result**: No Playwright during planning

#### Build Phase Verification
```bash
cat trees/4fc73599/.mcp.json  # During Build phase
# Output: { "mcpServers": {} }
```
✅ **Result**: No Playwright during implementation

#### Review Phase Verification
```bash
cat trees/4fc73599/.mcp.json  # After Review phase
# Output:
# {
#   "mcpServers": {
#     "playwright": {
#       "command": "npx",
#       "args": ["@playwright/mcp@latest", "--isolated", ...]
#     }
#   }
# }
```
✅ **Result**: Playwright dynamically installed!

**Git Commit**: `5ac3c77 reviewer: feature: configure Playwright MCP for testing`
- Changed `.mcp.json` from 1 line to 12 lines
- Added full Playwright MCP configuration

#### E2E Test Evidence

**Test File**: `.claude/commands/e2e/test_api_routes.md`

**Screenshots Captured**: 4 screenshots
1. Initial state with tabs
2. API Routes - All 10 routes displayed
3. Search filter functionality (filtered "health")
4. Method filter functionality (POST routes only)

**Screenshot URLs**:
- https://tac-webbuilder.directmyagent.com/adw/4fc73599/review/01_initial_state_with_tabs.png
- https://tac-webbuilder.directmyagent.com/adw/4fc73599/review/02_api_routes_all_routes.png
- https://tac-webbuilder.directmyagent.com/adw/4fc73599/review/03_search_filtered_health.png
- https://tac-webbuilder.directmyagent.com/adw/4fc73599/review/04_method_filter_post.png

**GitHub Issue**: https://github.com/warmonger0/tac-webbuilder/issues/3

## Performance Metrics

### Context Usage - Before vs After

#### Before Lazy-Loading
```
Main Claude Code Context: 79k/200k tokens (40%)
├── System prompt: 2.6k (1.3%)
├── System tools: 15.2k (7.6%)
├── MCP tools: 15.0k (7.5%) ← Playwright here
├── Custom agents: 1.7k (0.8%)
└── Messages: 8 tokens (0.0%)
```

#### After Lazy-Loading
```
Main Claude Code Context: 64k/200k tokens (32%)
├── System prompt: 2.6k (1.3%)
├── System tools: 15.2k (7.6%)
├── MCP tools: 0k (0%) ← Playwright removed
├── Custom agents: 1.7k (0.8%)
└── Messages: 8 tokens (0.0%)

Savings: 15k tokens (7.5% of total context)
```

### Per-Workflow Savings

For a typical ADW SDLC workflow with Plan, Build, Test, Review phases:

| Phase | Before | After | Savings |
|-------|--------|-------|---------|
| **Main Session** | 79k tokens | 64k tokens | **15k (7.5%)** |
| **Plan Worktree** | Had Playwright | No Playwright | **15k (7.5%)** |
| **Build Worktree** | Had Playwright | No Playwright | **15k (7.5%)** |
| **Review Worktree** | Had Playwright | Has Playwright* | 0 |

*Only loaded when E2E tests run

**Total Savings**: ~45k tokens per full SDLC workflow (excluding Review phase)

### Cumulative Impact

With multiple ADW workflows running concurrently (up to 15 possible):
- Each workflow saves 30-45k tokens across Plan and Build phases
- Main repo always saves 15k tokens in every session
- Scales linearly with number of concurrent ADWs

## Benefits

### 1. Context Efficiency
- **7.5% reduction** in base context usage
- More room for actual code, documentation, and conversation
- Reduced risk of hitting 200k token limit

### 2. Workflow Performance
- Faster Claude Code initialization (fewer tools to load)
- Cleaner context during planning and implementation
- Browser automation tools only when actually needed

### 3. Cost Optimization
- Fewer tokens consumed per API call
- Lower cost per ADW workflow execution
- Scales with concurrent workflow count

### 4. Maintainability
- Clear separation: planning/building vs testing
- Easier to debug MCP issues (isolated to test phase)
- Template-based configuration is simple to update

### 5. Backwards Compatibility
- All existing ADW workflows work unchanged
- E2E tests execute identically to before
- No changes needed to slash commands or test files

## Lifecycle Management

### New Workflow Creation
1. User runs `adw_sdlc_iso.py <issue-number>`
2. Fresh worktree created with empty `.mcp.json`
3. Plan phase: No Playwright (saves tokens)
4. Build phase: No Playwright (saves tokens)
5. Review phase: Playwright lazy-loaded on-demand
6. Workflow completes with Playwright in worktree

### Worktree Persistence
- Completed worktrees keep Playwright configuration
- Useful for debugging and manual testing
- Can be cleaned up with `./scripts/purge_tree.sh <adw-id>`

### Next Workflow
- Gets brand new worktree with fresh empty `.mcp.json`
- Lazy-loading happens again from scratch ♻️
- Each workflow is isolated and starts clean

## Configuration Files

### Modified Files
1. **`.mcp.json`** (main repo) - Emptied to remove Playwright
2. **`playwright-mcp-config.json`** (main repo) - Template for worktrees
3. **`adws/adw_modules/plan_executor.py`** - Added `install_playwright_mcp()` function
4. **`adws/adw_modules/plan_executor.py`** - Modified `_copy_mcp_files()` to strip Playwright

### New Files
1. **`docs/PLAYWRIGHT_LAZY_LOADING.md`** - User-facing documentation with test guide

## Rollback Instructions

If lazy-loading causes issues, rollback is simple:

```bash
# Revert the lazy-loading commit
git revert 512d1a7

# This restores Playwright to main .mcp.json
# All workflows will have Playwright in context again
```

## Future Enhancements

### Potential Improvements
1. **Conditional MCP Loading** - Framework for lazy-loading other MCPs (filesystem, IDE, etc.)
2. **MCP Usage Analytics** - Track which MCPs are actually used per phase
3. **Smart MCP Selection** - Auto-detect needed MCPs based on issue type
4. **MCP Unloading** - Remove MCPs after they're no longer needed

### Related Features
- Could extend to other heavyweight tools (databases, cloud services)
- Template system could support per-workflow MCP profiles
- MCP marketplace integration for on-demand tool discovery

## Documentation References

- **User Guide**: `docs/PLAYWRIGHT_LAZY_LOADING.md`
- **Implementation**: `adws/adw_modules/plan_executor.py`
- **Test Example**: Issue #3 - API Routes Display Feature
- **Architecture**: `docs/features/adw/technical-overview.md`

## Lessons Learned

### What Worked Well
1. Template-based configuration is flexible and maintainable
2. Lazy-loading at Review phase consolidates E2E testing
3. Per-worktree isolation prevents cross-contamination
4. Verification through real feature implementation is effective

### What Could Be Improved
1. Could add telemetry to track actual Playwright usage
2. Error handling for Playwright installation failures
3. Documentation could include more troubleshooting scenarios
4. Could support multiple test frameworks (not just Playwright)

## Conclusion

The Playwright MCP lazy-loading optimization successfully reduces Claude Code context usage by ~15k tokens (7.5%) per session while maintaining full E2E testing capabilities. The implementation was verified through a complete ADW workflow (Issue #3) that demonstrated:

✅ Zero Playwright overhead in main repository
✅ Clean context during Plan and Build phases
✅ On-demand Playwright installation during Review phase
✅ Full E2E testing with screenshot validation
✅ 45k tokens saved per SDLC workflow (cumulative)

The feature is production-ready, backwards-compatible, and provides immediate value for all ADW workflows in tac-webbuilder.

---

**Status**: Production
**Verification Date**: 2025-11-14
**Verification Method**: Live ADW workflow execution (Issue #3, PR #4)
**Success Criteria**: ✅ All met
