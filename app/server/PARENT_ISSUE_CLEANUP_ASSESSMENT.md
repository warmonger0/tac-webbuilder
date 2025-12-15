# parent_issue Cleanup Assessment

## Executive Summary

**Status:** Phase 1 Complete - Event-driven architecture using `feature_id` is live and tested
**Remaining Work:** Legacy code paths still reference `parent_issue` for backward compatibility

## What's Been Migrated ✅

### Database Schema (v2.0)
- ✅ `migration/phase_queue_event_driven_v2.sql` applied
- ✅ `parent_issue` → `feature_id` (references planned_features.id)
- ✅ `depends_on_phase` → `depends_on_phases` (JSONB array)

### Core Models & Repositories
- ✅ `models/phase_queue_item.py` - Updated to use feature_id, depends_on_phases
- ✅ `repositories/phase_queue_repository.py` - All queries use new schema
  - `get_all_by_parent_issue()` → `get_all_by_feature_id()`
  - `find_by_depends_on_phase()` → `find_phases_depending_on()`

### Panel 5 Integration (NEW - Event-Driven)
- ✅ `routes/planned_features_routes.py` - POST /start-automation endpoint
- ✅ `app/client/src/components/PlansPanel.tsx` - UI integration
- ✅ `app/client/src/api/plannedFeaturesClient.ts` - API client
- ✅ PhaseCoordinator uses event-driven approach (no parent_issue)

## Legacy Code Paths Still Using parent_issue 🔶

### Backend Services (15 files with references)

**Active Usage (Need Decision):**
1. **services/phase_queue_service.py**
   - `enqueue(parent_issue, ...)` - Used by legacy routes
   - `get_queue_by_parent(parent_issue)` - Used by legacy routes
   - **Decision Needed:** Deprecate or migrate?

2. **routes/queue_routes.py** 
   - Line 253: `get_queue_by_parent(parent_issue)`
   - Line 263: `enqueue(parent_issue, ...)`
   - Line 505: `get_queue_by_parent(next_phase.parent_issue)`
   - **Impact:** Legacy manual queue management endpoints

3. **services/multi_phase_issue_handler.py**
   - Line 146: `enqueue(parent_issue, ...)`
   - **Impact:** Legacy multi-phase workflow handler

4. **services/phase_coordination/phase_github_notifier.py**
   - Line 109: `get_queue_by_parent(parent_issue)`
   - **Impact:** GitHub PR comment notifications

5. **routes/issue_completion_routes.py**
   - References to parent_issue in completion logic
   - **Impact:** Issue completion webhooks

**Supporting Services (May be legacy):**
6. services/hopper_sorter.py
7. services/phase_dependency_tracker.py
8. services/github_issue_service.py
9. services/issue_linking_service.py

### Frontend (5 files)

1. **app/client/src/components/PhaseQueueCard.tsx**
   - Displays parent_issue in UI
   - **Note:** Panel 5 doesn't use this (uses feature_id)

2. **app/client/src/api/queueClient.ts**
   - API client methods reference parent_issue
   - **Note:** Panel 5 uses plannedFeaturesClient instead

3. **app/client/src/types/api.types.ts**
   - TypeScript type definitions
   - **Action:** Add feature_id types, mark parent_issue as deprecated

4. **app/client/src/api/observabilityClient.ts**
5. **app/client/src/components/__tests__/PhaseQueueCard.test.tsx**

### Documentation (60+ files)
- Migration guides
- Architecture docs
- Session notes
- Templates
- **Action:** Update to reflect new event-driven approach

## Recommended Cleanup Strategy

### Phase 1: Completed ✅
- Database migration applied
- Core models/repositories updated
- Panel 5 integration working end-to-end
- Event-driven PhaseCoordinator using feature_id

### Phase 2: Deprecation Warnings (Next Session)
**Goal:** Add deprecation warnings to legacy code paths

1. **Add deprecation decorators:**
   ```python
   @deprecated("Use Panel 5 automation instead. See POST /api/v1/planned-features/{id}/start-automation")
   def enqueue(self, parent_issue: int, ...):
   ```

2. **Update API responses:**
   ```json
   {
     "warning": "This endpoint is deprecated. Use Panel 5 automation for new workflows.",
     "migration_guide": "/docs/migration-guide"
   }
   ```

3. **Log deprecation usage:**
   - Track which endpoints are still being called
   - Identify active users of legacy paths
   - Plan migration timeline

### Phase 3: Migration Support (Future)
**Goal:** Provide migration path for legacy workflows

1. **Add dual-mode support:**
   - Services accept both parent_issue (legacy) and feature_id (new)
   - Internally map parent_issue to feature_id
   - Gradual migration of active workflows

2. **Migration script:**
   - Convert existing parent_issue workflows to feature_id
   - Update database records
   - Preserve backward compatibility

### Phase 4: Complete Removal (6-12 months)
**Goal:** Remove all parent_issue references

1. **Remove legacy code:**
   - Delete deprecated endpoints
   - Remove parent_issue column from database
   - Update all documentation

2. **Final cleanup:**
   - Remove backward compatibility shims
   - Simplify codebase
   - Performance optimization

## Current Recommendation

**For this session:**
1. ✅ DONE: Event-driven architecture is live and working
2. ✅ DONE: Panel 5 integration complete and tested
3. 📝 DOCUMENT: This assessment for future reference
4. 🔄 DEFER: Deprecation warnings and migration (separate feature/session)

**Why defer full cleanup:**
- Legacy endpoints may still be in use
- Need to audit actual usage before removal
- Deprecation should be gradual with warnings
- Requires coordination with any external consumers

## Files Tracked for Future Cleanup

### High Priority (Active Code)
- [ ] services/phase_queue_service.py (2 methods)
- [ ] routes/queue_routes.py (3 usages)
- [ ] services/multi_phase_issue_handler.py (1 usage)
- [ ] services/phase_coordination/phase_github_notifier.py (1 usage)
- [ ] routes/issue_completion_routes.py (references)

### Medium Priority (Supporting Services)
- [ ] services/hopper_sorter.py
- [ ] services/phase_dependency_tracker.py
- [ ] services/github_issue_service.py
- [ ] services/issue_linking_service.py

### Low Priority (Frontend - May not be used)
- [ ] app/client/src/components/PhaseQueueCard.tsx
- [ ] app/client/src/api/queueClient.ts
- [ ] app/client/src/types/api.types.ts

### Documentation (Update when ready)
- [ ] docs/architecture/*.md
- [ ] docs/api/*.md
- [ ] README files

## Success Metrics

**Current State:**
- ✅ Event-driven automation working
- ✅ Database schema migrated
- ✅ Core models updated
- ✅ Panel 5 integration complete
- ✅ End-to-end tested successfully

**Future Success Criteria:**
- [ ] Zero new code uses parent_issue
- [ ] Deprecation warnings logged
- [ ] Migration guide published
- [ ] Legacy usage tracking implemented
- [ ] Removal plan approved

## Related Issues

- Feature #99: Event-Driven Phase Coordination (Parent)
- Feature #103: Next-Task Suggestion Engine
- Session 19: Event-driven phase coordination handoff

## Next Actions

**Immediate (This Session):**
1. Commit this assessment document ✅
2. Update session documentation
3. Close current work

**Next Session:**
1. Create "Deprecate parent_issue" feature in planned_features
2. Add deprecation warnings to legacy endpoints
3. Implement usage tracking
4. Create migration guide

---

**Generated:** 2025-12-15  
**Session:** Event-Driven Phase Coordination + Panel 5 Integration  
**Status:** Phase 1 Complete, Cleanup Deferred
