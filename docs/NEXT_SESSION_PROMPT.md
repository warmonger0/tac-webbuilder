# Next Session Prompt

Copy this prompt to continue work in a new Claude Code session:

---

## Context Handoff

I'm working on **tac-webbuilder**, a workflow automation system with analytics scoring engine. We just completed Phase 3B and handed off Phase 3C to an ADW workflow.

### Current State

**Phase 3A: Analytics Infrastructure** ✅ COMPLETE
- Database schema with 16 analytics columns
- Backend module: `app/server/core/workflow_analytics.py` (642 lines)
- TypeScript types in sync
- Migration: `app/server/db/migrations/003_add_analytics_metrics.sql`

**Phase 3B: Core Scoring Engine** ✅ COMPLETE
- All 4 scoring functions implemented (clarity, cost, performance, quality)
- Comprehensive test suite (617 lines)
- Integrated into sync process
- Model appropriateness scoring
- Anomaly thresholds: 1.5x (tightened per my request)
- Scoring version tracking: "1.0"
- PR #28 merged, Issue #27 closed

**Phase 3C: Score Display UI** ⏳ IN PROGRESS (ADW Workflow)
- Handoff doc: `docs/PHASE_3C_HANDOFF.md`
- Components to review: ScoreCard.tsx, SimilarWorkflowsComparison.tsx
- Integration: WorkflowHistoryCard.tsx (lines 693-787)
- Expected completion: 5-6 hours

### Recent Commits (pushed to main)

1. Service control features + Phase 3C UI preview components
2. Phase 3 analytics models added to data_models.py
3. TypeScript types fixed (pattern metadata fields)
4. Revised Phase 3C handoff document (237 lines)

### System Status

- ✅ Backend starts successfully (tested)
- ✅ Frontend builds without errors (tested)
- ✅ All TypeScript types in sync
- ✅ Phase 3B test suite passing

### Important Decisions Made

1. **Missing cost estimate data:** Should NEVER happen - requirement is to kick back if missing
2. **Anomaly thresholds:** Tightened to 1.5x (from 2x) - previous was too lenient
3. **Score versioning:** Track version starting at "1.0"
4. **Priority:** Complete Phase 3B tests before Phase 3C UI (chose Option A)
5. **Score defaults:** Currently 0.0 when data missing (may need review)

### Key File Locations

**Backend:**
- Scoring engine: `app/server/core/workflow_analytics.py`
- Data models: `app/server/core/data_models.py`
- Workflow history: `app/server/core/workflow_history.py`
- Tests: `app/server/tests/test_workflow_analytics.py`
- Migration: `app/server/db/migrations/003_add_analytics_metrics.sql`

**Frontend:**
- Types: `app/client/src/types/api.types.ts`
- ScoreCard: `app/client/src/components/ScoreCard.tsx` (exists, needs review)
- SimilarWorkflows: `app/client/src/components/SimilarWorkflowsComparison.tsx` (exists, needs review)
- History Card: `app/client/src/components/WorkflowHistoryCard.tsx` (Phase 3 integration at lines 693-787)

**Documentation:**
- Phase 3A spec: `docs/PHASE_3A_ANALYTICS_INFRASTRUCTURE.md`
- Phase 3B spec: `docs/PHASE_3B_SCORING_ENGINE.md` (implementation summary at top)
- Phase 3B completion: `docs/PHASE_3B_COMPLETION_HANDOFF.md`
- Phase 3C handoff: `docs/PHASE_3C_HANDOFF.md` (active ADW workflow)
- Phase 3C full spec: `docs/PHASE_3C_SCORE_DISPLAY_UI.md`

### What's Next After Phase 3C Completes

**Monitor ADW Workflow:**
- Check GitHub issues for Phase 3C completion
- Review PR when created
- Test scores display in UI
- Merge if all acceptance criteria met

**Then Phase 3D/3E:**
- **Phase 3D:** Advanced insights (trend analysis, pattern detection)
- **Phase 3E:** Interactive similar workflows (clickable comparisons, detailed comparison view)

### Active Work

**Phase 3C ADW is running** - review progress at:
- GitHub issues: Check for new Phase 3C issue
- Pull requests: Watch for Phase 3C PR

**When Phase 3C PR arrives:**
1. Review implementation against `docs/PHASE_3C_HANDOFF.md` acceptance criteria
2. Test manually (run backend + frontend, create test workflow, verify scores display)
3. Check test coverage (should be >80%)
4. Verify accessibility (no violations)
5. Merge if criteria met

### Commands Reference

```bash
# Start backend
cd app/server && uv run python server.py

# Start frontend
cd app/client && bun run dev

# Build frontend
cd app/client && bun run build

# Run tests
cd app/server && uv run pytest tests/test_workflow_analytics.py -v
cd app/client && bun run test

# Check TypeScript
cd app/client && npx tsc --noEmit

# View GitHub issues
gh issue list

# View PRs
gh pr list
```

### Notes

- Documentation cleaned up: Old analysis docs moved to `docs/Archived Issues/` and `docs/Analysis/`
- Service control features added: Webhook/Cloudflare restart, GitHub webhook redelivery
- Backend has Phase 3 analytics API endpoints ready: `/api/workflow-analytics/{adw_id}`, `/api/workflow-trends`, `/api/cost-predictions`

### Quick Status Check

If you need to verify current state:
```bash
git status
git log --oneline -5
gh issue list --label "auto-routed"
gh pr list --state open
```

---

## Recommended Opening

Start with:
"I'm continuing work on tac-webbuilder. Phase 3C (Score Display UI) is currently running as an ADW workflow. What's the status of that workflow? Let me check GitHub for updates."

Then:
- Check for Phase 3C issue/PR
- Review if PR exists
- Merge if ready
- Plan next steps (Phase 3D/3E or other priorities)
