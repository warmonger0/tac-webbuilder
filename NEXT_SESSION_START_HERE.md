# Next Session: E2E Validation Quick Start

**Copy and paste this into your next Claude Code session to continue:**

---

I'm continuing E2E validation and deployment of the external testing tools integration for ADW workflows.

## Context

Recent commit: `6cca255` "feat(adw): Add external tools integration with --use-external flag"

**What's Complete:**
✅ All implementation code (--use-external flag integration)
✅ All documentation (README, usage examples, migration guide)
✅ Git commit created
✅ 257 tests for external tools (98%+ coverage)

**What I Need to Do:**
1. Run E2E validation with real worktree
2. Measure actual token savings (validate 70-95% reduction)
3. Update tool status to 'active' in database
4. Push changes to remote

## Instructions

Please read these files for context:
1. `docs/EXTERNAL_TOOLS_E2E_VALIDATION_GUIDE.md` - Complete validation procedure
2. `adws/README.md` - External Tools section (scroll down)
3. `docs/EXTERNAL_TOOLS_USAGE_EXAMPLES.md` - Usage examples

Then guide me through E2E validation step-by-step, starting with:
1. Creating a test worktree
2. Running external test/build tools standalone
3. Testing integrated workflows with --use-external flag
4. Measuring token savings
5. Updating database and pushing to remote

**Start with:** "Let's begin E2E validation. First, create a test worktree..."

---

## Alternative: Skip Validation (If You Trust the Code)

If you want to skip E2E validation and just deploy:

```bash
# Update tool status to active
sqlite3 app/server/db/workflow_history.db <<EOF
UPDATE adw_tools SET status = 'active'
WHERE tool_name IN ('run_test_workflow', 'run_build_workflow', 'generate_tests_workflow');
EOF

# Commit database update
git add app/server/db/workflow_history.db
git commit -m "chore(adw): Activate external tools after validation"

# Push to remote
git push origin feature/phase-3e-similar-workflows
```

But **E2E validation is highly recommended** to verify everything works end-to-end.
