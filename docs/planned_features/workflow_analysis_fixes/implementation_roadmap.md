# Implementation Roadmap

**Total Duration:** 3 weeks
**Team Size:** 1 developer (Claude Code assisted)
**Approach:** Two-phase (Tactical → Strategic)

---

## Week 1: Tactical Fixes + Core Reliability

### Day 1: Database Cleanup + Critical Bugs (Phase 1)

**Morning (4 hours):**
- [ ] Create `cleanup_stale_workflows.py` script
- [ ] Run cleanup on 19 stale workflows
- [ ] Verify database accuracy
- [ ] Create `cleanup_orphaned_states.sh` script
- [ ] Archive orphaned state files

**Afternoon (4 hours):**
- [ ] Fix PR creation JSON serialization bug
- [ ] Fix external test tool JSON parsing
- [ ] Add error message logging to database
- [ ] Test fixes with simple workflow

**Deliverables:**
- Clean database (no stale "running" workflows)
- Critical bugs fixed
- Error logging operational

---

### Day 2: Webhook Fix + Request 1.4 (Phase 1)

**Morning (4 hours):**
- [ ] Investigate webhook trigger issue
- [ ] Fix webhook configuration or add manual trigger
- [ ] Create synthetic test workflow
- [ ] Run synthetic test end-to-end
- [ ] Validate all phases complete

**Afternoon (4 hours):**
- [ ] Trigger Request 1.4 (Issue #54)
- [ ] Monitor execution through all phases
- [ ] Verify PR creation works
- [ ] Confirm workflow completes
- [ ] Document Phase 1 results

**Deliverables:**
- Webhook working OR manual trigger available
- Request 1.4 completed successfully
- Phase 1 validation complete

---

### Day 3: State Machine Implementation (Phase 2.1)

**Morning (4 hours):**
- [ ] Create `state_machine.py` with WorkflowState enum
- [ ] Implement StateTransition validation
- [ ] Create WorkflowStateMachine class
- [ ] Write unit tests for state transitions

**Afternoon (4 hours):**
- [ ] Create `atomic_state.py` with AtomicStateWriter
- [ ] Implement atomic file writes (temp + rename)
- [ ] Add state validation on read
- [ ] Write unit tests for atomic operations

**Deliverables:**
- Formal state machine implemented
- Atomic state writes working
- Unit tests passing

---

### Day 4: State Schema Versioning (Phase 2.1)

**Morning (4 hours):**
- [ ] Create `state_schema.py` with version definitions
- [ ] Implement StateMigration system
- [ ] Create v1.0 → v2.0 migration
- [ ] Write tests for migrations

**Afternoon (4 hours):**
- [ ] Integrate state machine into adw_plan_iso.py
- [ ] Update state persistence to use atomic writes
- [ ] Test state transitions in plan phase
- [ ] Validate state file format

**Deliverables:**
- State versioning system complete
- Migration system tested
- Plan phase using new state management

---

### Day 5: Error Classification System (Phase 2.2)

**Morning (4 hours):**
- [ ] Create `error_handler.py` with ErrorCategory enum
- [ ] Implement WorkflowError class
- [ ] Create ErrorClassifier with classification rules
- [ ] Write unit tests for classification

**Afternoon (4 hours):**
- [ ] Create `retry_handler.py` with RetryStrategy
- [ ] Implement exponential backoff logic
- [ ] Add category-specific retry delays
- [ ] Write tests for retry logic

**Deliverables:**
- Error classification system complete
- Retry logic with exponential backoff
- Tests passing

---

## Week 2: Error Recovery + Concurrency

### Day 6-7: Rollback Mechanism (Phase 2.2)

**Day 6 Morning (4 hours):**
- [ ] Create `rollback.py` with WorkflowRollback class
- [ ] Implement PR closing logic
- [ ] Implement branch deletion logic
- [ ] Write tests for PR/branch cleanup

**Day 6 Afternoon (4 hours):**
- [ ] Implement worktree removal logic
- [ ] Implement port freeing logic
- [ ] Implement external process cleanup
- [ ] Write tests for resource cleanup

**Day 7 Morning (4 hours):**
- [ ] Add GitHub comment posting for rollbacks
- [ ] Add database state updates
- [ ] Integrate rollback into error handling
- [ ] Write end-to-end rollback tests

**Day 7 Afternoon (4 hours):**
- [ ] Replace `sys.exit(1)` in adw_plan_iso.py
- [ ] Replace `sys.exit(1)` in adw_build_iso.py
- [ ] Add try-finally blocks for cleanup
- [ ] Test rollback on intentional failures

**Deliverables:**
- Complete rollback mechanism
- sys.exit(1) calls replaced in 2 phases
- Rollback tested and working

---

### Day 8: sys.exit() Replacement (Phase 2.2)

**Morning (4 hours):**
- [ ] Replace `sys.exit(1)` in adw_lint_iso.py
- [ ] Replace `sys.exit(1)` in adw_test_iso.py
- [ ] Add cleanup blocks to both phases
- [ ] Test error recovery in lint/test

**Afternoon (4 hours):**
- [ ] Replace `sys.exit(1)` in adw_review_iso.py
- [ ] Replace `sys.exit(1)` in adw_document_iso.py
- [ ] Replace `sys.exit(1)` in adw_ship_iso.py
- [ ] Replace `sys.exit(1)` in adw_cleanup_iso.py

**Deliverables:**
- All sys.exit(1) calls replaced
- Error propagation working
- Cleanup guaranteed on failures

---

### Day 9: Concurrency Fixes (Phase 2.3)

**Morning (4 hours):**
- [ ] Fix lock bypass in trigger_webhook.py
- [ ] Implement verify_lock_ownership()
- [ ] Add lock verification for continuing workflows
- [ ] Write tests for lock enforcement

**Afternoon (4 hours):**
- [ ] Create `resource_manager.py` with ResourceQuota
- [ ] Implement disk space checks
- [ ] Implement worktree count limits
- [ ] Implement API budget validation

**Deliverables:**
- Lock bypass vulnerability fixed
- Resource quotas enforced
- Concurrency race conditions prevented

---

### Day 10: Resource Cleanup Automation (Phase 2.3)

**Morning (4 hours):**
- [ ] Create automatic worktree cleanup job
- [ ] Add stale worktree detection (>48h old)
- [ ] Create orphaned resource scanner
- [ ] Schedule cleanup cron job

**Afternoon (4 hours):**
- [ ] Test resource quota enforcement
- [ ] Test automatic cleanup
- [ ] Run stress test (start 5 workflows simultaneously)
- [ ] Validate no resource leaks

**Deliverables:**
- Automatic cleanup operational
- Resource limits enforced
- Stress tests passing

---

## Week 3: Observability + Testing + Validation

### Day 11-12: Observability (Phase 2.4)

**Day 11 Morning (4 hours):**
- [ ] Create `structured_logger.py` with JSON logging
- [ ] Integrate into adw_plan_iso.py
- [ ] Integrate into adw_build_iso.py
- [ ] Test log parsing

**Day 11 Afternoon (4 hours):**
- [ ] Integrate structured logging into all phases
- [ ] Create log aggregation queries
- [ ] Add log rotation
- [ ] Test log analysis tools

**Day 12 Morning (4 hours):**
- [ ] Create metrics collection module
- [ ] Track success rate per phase
- [ ] Track duration per phase
- [ ] Track cost per phase

**Day 12 Afternoon (4 hours):**
- [ ] Create basic observability dashboard
- [ ] Add real-time workflow status view
- [ ] Add error rate graphs
- [ ] Add cost tracking graphs

**Deliverables:**
- Structured logging across all phases
- Metrics collection operational
- Basic observability dashboard

---

### Day 13: Testing Infrastructure (Phase 2.5)

**Morning (4 hours):**
- [ ] Create end-to-end workflow test
- [ ] Create phase integration tests
- [ ] Create failure scenario tests
- [ ] Create concurrency stress tests

**Afternoon (4 hours):**
- [ ] Add mocks for GitHub API
- [ ] Add mocks for LLM APIs
- [ ] Create test fixtures for state files
- [ ] Run full test suite

**Deliverables:**
- Comprehensive test suite
- All tests passing
- CI/CD integration ready

---

### Day 14: Validation with NL_REQUESTS.md (Phase 2)

**Full Day (8 hours):**
- [ ] Run Request 1.4 end-to-end (if not done in Phase 1)
- [ ] Run Request 1.5 end-to-end
- [ ] Run Request 1.6 end-to-end
- [ ] Run Request 1.7 end-to-end
- [ ] Monitor success rates
- [ ] Document any failures
- [ ] Iterate on fixes

**Deliverables:**
- 4+ NL_REQUESTS workflows completed
- Success rate measured
- Reliability validated

---

### Day 15: Documentation + Polish (Phase 2)

**Morning (4 hours):**
- [ ] Update ADW architecture documentation
- [ ] Document new state machine
- [ ] Document error recovery process
- [ ] Document rollback mechanism

**Afternoon (4 hours):**
- [ ] Create operator's guide for monitoring
- [ ] Create troubleshooting guide
- [ ] Create runbook for common issues
- [ ] Final validation of success metrics

**Deliverables:**
- Complete documentation
- Operator guides
- Success metrics validated
- Phase 2 complete

---

## Success Milestones

### End of Week 1
- ✅ Phase 1 complete (Request 1.4 working)
- ✅ State machine implemented
- ✅ Error classification system ready
- ✅ Database cleanup complete

### End of Week 2
- ✅ Rollback mechanism working
- ✅ All sys.exit(1) replaced
- ✅ Concurrency fixes deployed
- ✅ Resource quotas enforced

### End of Week 3
- ✅ Observability operational
- ✅ Test suite comprehensive
- ✅ >80% success rate achieved
- ✅ Full documentation complete

---

## Risk Mitigation

### If Behind Schedule
**Week 1:** Cut Day 4 (state versioning) - can be added later
**Week 2:** Cut Day 10 (automation) - run cleanup manually
**Week 3:** Cut Day 12 (dashboard) - use command-line tools

### If Blocked on Dependencies
- **GitHub API issues:** Use manual triggers
- **Test failures:** Run in isolation mode
- **Resource conflicts:** Reduce concurrent workflows

### Rollback Points
- **End of Day 2:** Can revert to Phase 1 only
- **End of Day 7:** Can pause before concurrency changes
- **End of Day 12:** Can pause before final validation

---

## Daily Checkpoints

Each day:
1. Morning standup (5 min) - review plan
2. Mid-day check (5 min) - on track?
3. End-of-day review (10 min) - deliverables met?
4. Commit working code
5. Update progress in this document

---

## Post-Implementation

After Week 3:
- [ ] Monitor production workflows for 1 week
- [ ] Collect success rate data
- [ ] Iterate on any new issues discovered
- [ ] Plan Phase 2.6 (async execution) if time permits

---

## Notes

- **Feature Flags:** Implement new systems behind flags for safe rollout
- **Parallel Systems:** Run old and new systems in parallel during migration
- **Gradual Rollout:** Migrate workflows incrementally, not all at once
- **Documentation:** Update docs in real-time, not at the end
