# ADW Refactoring: Context Optimization & Path Reference Improvements

This directory contains the implementation plan for refactoring ADW workflows to eliminate unnecessary AI calls, optimize context usage, and improve reliability through deterministic path handling.

## Overview

The ADW refactoring is divided into 4 phases, addressing different aspects of context optimization and code quality improvements.

## Phases

### ✅ [Phase 1: Extract Deterministic Operations](./PHASE_1_COMPLETE.md)
**Status:** COMPLETE (Commit: e8ad1e5)
**Impact:** $0.30 + 86s per workflow

Extracted worktree setup, app lifecycle, and commit generation from AI slash commands to deterministic Python functions.

**New Modules:**
- `adw_modules/worktree_setup.py` - Worktree initialization
- `adw_modules/app_lifecycle.py` - App startup/shutdown
- `adw_modules/commit_generator.py` - Commit message generation

**Savings:** $30/year + 2.4 hours (assuming 100 workflows)

---

### 📋 [Phase 2: Fix Path Pre-computation](./PHASE_2_PATH_PRECOMPUTATION.md)
**Status:** Planned
**Priority:** High
**Estimated Effort:** 2 hours

Fix file path resolution anti-pattern by pre-computing paths instead of parsing agent output.

**Key Changes:**
- Pre-compute patch file paths
- Simplify `find_spec_file()` to fail fast
- Remove 150 lines of path validation/fallback logic

**Benefits:** Code quality, fewer file operations, better error detection

---

### 📋 [Phase 3: Optimize Slash Commands](./PHASE_3_OPTIMIZE_SLASH_COMMANDS.md)
**Status:** Planned
**Priority:** Medium
**Estimated Effort:** 2 hours

Pass explicit file paths to slash commands instead of having agents discover files via Bash/Git.

**Key Changes:**
- Update `/review` to receive explicit file paths
- Update `/patch` to receive target files
- Remove redundant doc loading from commands
- Pre-compute file lists in Python

**Benefits:** 2000-4500 tokens saved per review/patch cycle, faster execution

---

### 📋 [Phase 4: Validate Working Directory](./PHASE_4_VALIDATE_WORKING_DIR.md)
**Status:** Planned
**Priority:** Low
**Estimated Effort:** 1 hour

Ensure all worktree workflows properly pass `working_dir` for consistent MCP tool availability.

**Key Changes:**
- Create validation script to audit `execute_template()` calls
- Add logging for MCP config detection
- Fix any missing `working_dir` parameters

**Benefits:** Consistent tool availability, better debugging

---

## Total Impact (All Phases)

### Cost Savings
- **Phase 1:** $0.30 per workflow
- **Phase 2:** Code quality (no direct cost savings)
- **Phase 3:** ~$0.15-0.25 per workflow (token reduction)
- **Phase 4:** Reliability improvement

**Total per workflow:** ~$0.45-0.55 savings
**Annual (100 workflows):** ~$45-55 savings

### Time Savings
- **Phase 1:** 86 seconds per workflow
- **Phase 3:** ~20-30 seconds per workflow (fewer subprocess calls)

**Total per workflow:** ~106-116 seconds
**Annual (100 workflows):** ~3 hours saved

### Code Quality
- **Reduced complexity:** ~200+ lines of path validation removed
- **Better error detection:** Fail fast instead of masking issues
- **Improved reliability:** Deterministic operations
- **Enhanced debugging:** Explicit contracts, clear logging

## Implementation Order

1. ✅ **Phase 1** (COMPLETE) - Immediate high ROI
2. **Phase 2** (High Priority) - Addresses known pain points
3. **Phase 3** (Medium Priority) - Further optimization
4. **Phase 4** (Low Priority) - Validation and cleanup

## How to Use This Documentation

Each phase has its own detailed markdown file with:
- Problem description
- Solution approach
- Code examples
- Implementation steps
- Expected benefits
- Validation criteria

Start with Phase 2 for the next high-value improvement.
