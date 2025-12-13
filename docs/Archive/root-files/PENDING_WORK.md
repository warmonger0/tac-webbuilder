# Pending Work Items

This document tracks optional enhancements and future work items for tac-webbuilder.

## 🔄 In Progress

_No active tasks_

## 📋 Planned Optional Enhancements

- [ ] **CLI Interface** (8 hours - Low Priority)
  - Port from tac-7 if power users need terminal access
  - Current state: Web-focused, CLI not necessary

- [ ] **Service Migration to Config System** (2-3 hours - Low Priority)
  - Gradually migrate services from direct os.getenv() to centralized config
  - Update server.py, github_issue_service.py, etc.
  - Can be done incrementally without breaking changes

- [ ] **Log Analysis Tools** (4-8 hours - Low Priority)
  - Build log streaming service for real-time monitoring
  - Create web-based log viewer and analysis UI
  - Implement automatic rotation and archiving
  - Add alerting based on log patterns

- [ ] **Component Refactoring** (Variable - Low Priority)
  - Break down large components flagged by max-lines-per-function
  - Reduce complexity in components with complexity warnings
  - Would improve maintainability but requires significant effort

## ✅ Recently Completed

- ✅ **Configuration Management System** (Completed 2025-12-02, Commit: 65e21e2)
  - Pydantic-based config with YAML + env var support
  - 5 sections: Server, GitHub, Database, LLM, Cloudflare
  - TWB_ prefix namespace with __ for nested sections
  - 23 passing tests, full documentation in CONFIG_MIGRATION_GUIDE.md

- ✅ **Enhanced Structured Logging** (Completed 2025-12-02, Commit: 1c5a746)
  - JSONL output with 6 Pydantic event types
  - Per-workflow isolation (workflow_adw-{id}.jsonl)
  - Date-based general logs (general_YYYY-MM-DD.jsonl)
  - 13 passing tests, comprehensive guide in STRUCTURED_LOGGING_GUIDE.md

- ✅ **ESLint Cleanup** (Completed 2025-12-02, Commit: ab7a469)
  - Fixed 25 warnings (134→109)
  - 0 errors maintained
  - Updated config for test file exemptions
  - Remaining warnings are acceptable (complexity, max-lines, any-types)

- ✅ **Token Monitoring Tools** (Completed 2025-12-02)
  - monitor_adw_tokens.py - Real-time token/cost tracking
  - analyze_context_usage.py - Context optimization analysis
  - TOKEN_TOOLS.md - Comprehensive documentation
  - Tested successfully with 87.4% cache efficiency

- ✅ **Critical ESLint Fixes** (Completed 2025-12-02)
  - Fixed 6 critical errors (duplicate imports, regex escapes)
  - Auto-formatted frontend components
  - Verified backend linting (all checks passed)

- ✅ **Branch Regex Bug** (Fixed in commit c3f8fc2)
  - Fixed branch name regex to capture multi-word descriptions

- ✅ **N+1 Query Pattern** (Already fixed in prior commits)
  - Using efficient find_by_id() at queue_routes.py:283

---

**Note:** All items above are optional enhancements. System is fully functional and production-ready as-is.

**Instructions:** Remove items from "Planned" and add to "Recently Completed" as work finishes.
