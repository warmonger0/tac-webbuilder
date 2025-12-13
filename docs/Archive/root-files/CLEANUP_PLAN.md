# Project Cleanup Plan

## Root Directory (/tac-webbuilder/)

### Current State
- 21 .md files cluttering root
- Most are old session summaries, fix reports, and guides

### Archive to docs/Archive/root-files/

**Old session summaries:**
- SESSION_19_E2E_FIX_SUMMARY.md
- SESSION_20_TEST_FIXES.md
- SESSION_SUMMARY_ERROR_HANDLING_PROTOCOL.md

**Old fix reports:**
- E2E_FIXTURE_FIXES_FINAL_REPORT.md
- E2E_TEST_FIXES_SUMMARY.md
- FIX_PANEL8_ERRORS.md
- FIXTURE_FIXES_REPORT.md
- WORKFLOW_FIXES.md

**Old guides (superseded):**
- DB_SNAPSHOT_GUIDE.md
- DEPLOYMENT_STATUS.md
- IMPLEMENTATION_COMPLETE.md
- PENDING_WORK.md
- PROMPTS_SUMMARY.md
- PUSH_AND_MERGE_GUIDE.md
- WORKFLOW_QUICKSTART.md
- CC-Audit-Proposal-03.12.25-14.47.md

**Other cleanup:**
- migration_output.log (old log file)

### Keep in Root
- README.md (project readme)
- ARCHITECTURE.md (high-level architecture)
- CLAUDE.md (AI instructions - important!)
- FEATURE_106_REQUIREMENTS.md (active feature)
- QUICK_WIN_106_106_auto_workflow_launcher.md (active feature)

**After cleanup: 5 files in root (down from 21)**

---

## docs/ Directory

### Current State
- 30 .md files in docs/ root
- 24 subdirectories
- Many old session files and guides

### Archive to docs/Archive/old-docs/

**Old session files:**
- ADW_CLEANUP_PROCESS.md
- ADW_COMPLETION_GUIDE.md
- ADW_FAILURE_ANALYSIS_AND_FIX_PROTOCOL.md
- ADW_FIX_IMPLEMENTATION_SUMMARY.md
- ADW_ROBUSTNESS_SYSTEM.md
- ADW_WORKFLOW_BEST_PRACTICES.md
- SESSION_18_HANDOFF.md
- SESSION_2025-11-21_ROUTING_AND_TEST_FIXES.md
- PANEL_REVIEW_CORRECTIONS.md
- PANEL_REVIEW_SESSION_17.md

**Old analysis/planning:**
- CODEBASE_HEALTH_ASSESSMENT_2025-11-25.md
- FEATURE_IMPLEMENTATION_ROADMAP.md
- ISSUE_66_COMPREHENSIVE_IMPLEMENTATION_PLAN.md
- postgresql_migration_plan.md
- RECENT_FIXES_2025-11-25.md
- frontend-hardcoded-data.md
- WORKFLOW_HISTORY_SCHEMA_MISMATCH.md

**Old guides:**
- CONFIG_MIGRATION_GUIDE.md
- MIGRATION_COMPLETE_SUMMARY.md
- OBSERVABILITY_IMPLEMENTATION_GUIDE.md
- STRUCTURED_LOGGING_GUIDE.md
- USING_PATTERN_PREDICTIONS.md

### Archive to docs/Archive/old-folders/

**Old tracking folders:**
- completed/ (old completed work)
- bugs/ (old bug tracking)
- session-19/ (old session folder)
- sessions/ (old session folders)
- incidents/ (old incidents)
- planned_features/ (old feature tracking)

### Keep in docs/
**Current reference docs (8 files):**
- README.md
- api.md
- architecture.md
- cli.md
- configuration.md
- examples.md
- troubleshooting.md
- web-ui.md

**Active folders (18 folders):**
- Archive/ (archive storage)
- adw/, api/, architecture/ (active docs)
- backend/, features/, guides/ (active docs)
- implementation/, patterns/, pattern_recognition/ (active docs)
- processes/, postmortems/, requests/ (active docs)
- templates/, testing/, user-guide/ (active docs)
- maintenance/ (organizational)
- logs/ (system logs - check if needed)

**After cleanup: 8 .md files + 18 folders in docs/ (down from 30 files + 24 folders)**

---

## Execution Plan

1. Archive root files (16 files)
2. Archive docs/ files (22 files)
3. Archive docs/ folders (6 folders)
4. Commit and push
5. Verify cleanup

**Total files to archive: 38 files + 6 folders**
**Result: Clean, maintainable structure**
