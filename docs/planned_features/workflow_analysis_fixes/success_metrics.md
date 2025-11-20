# Success Metrics & Validation

**Purpose:** Define measurable success criteria for ADW reliability improvements
**Timeline:** Measured throughout implementation and post-deployment
**Review Frequency:** Daily during implementation, weekly post-deployment

---

## Phase 1: Tactical Fixes (Days 1-2)

### Critical Success Metrics

#### Database Health
- [ ] **Zero stale "running" workflows** in database
  - Before: 19 workflows stuck in "running"
  - After: 0 workflows stuck
  - Measurement: `SELECT COUNT(*) FROM workflow_history WHERE status = 'running' AND created_at < datetime('now', '-24 hours')`

- [ ] **All workflows have accurate timestamps**
  - Before: `start_time`, `end_time`, `duration_seconds` often NULL
  - After: 100% of completed workflows have timestamps
  - Measurement: `SELECT COUNT(*) FROM workflow_history WHERE status = 'completed' AND (end_time IS NULL OR duration_seconds IS NULL)`

- [ ] **Error messages captured**
  - Before: `error_message` always NULL
  - After: 100% of failed workflows have error messages
  - Measurement: `SELECT COUNT(*) FROM workflow_history WHERE status = 'failed' AND (error_message IS NULL OR error_message = '')`

---

#### Webhook Reliability
- [ ] **Webhook triggers for new issues**
  - Before: Issue #54 created with 0 comments
  - After: New issues receive trigger comment within 60 seconds
  - Measurement: Manual testing + webhook service logs

- [ ] **Webhook service uptime**
  - Target: >99% uptime
  - Measurement: `ps aux | grep webhook_service` + health check endpoint

---

#### Bug Fixes Validated
- [ ] **PR creation succeeds without JSON errors**
  - Before: "Object of type datetime is not JSON serializable"
  - After: 0 JSON serialization errors
  - Measurement: Search logs for "JSONSerializableError" during PR creation

- [ ] **External test tools return valid JSON**
  - Before: "JSONDecodeError: Expecting value: line 1 column 1"
  - After: 100% of test outputs are valid JSON
  - Measurement: Test tool output validation in test phase logs

- [ ] **Database state syncs on completion**
  - Before: Workflows complete but stay "running"
  - After: 100% of workflows marked "completed" when done
  - Measurement: Compare worktree cleanup logs with database status

---

#### Request 1.4 Completion
- [ ] **Request 1.4 (Extract LLM Client Utilities) completes end-to-end**
  - All 8 phases succeed: plan → build → lint → test → review → document → ship → cleanup
  - PR created successfully
  - PR merged to main
  - Worktree cleaned up
  - Database shows "completed"
  - Files created:
    - `app/server/utils/llm_clients.py`
    - `app/server/tests/utils/test_llm_clients.py`

---

### Phase 1 Success Threshold

**Minimum to proceed to Phase 2:**
- ✅ Request 1.4 completes successfully
- ✅ Database shows no stale workflows
- ✅ Webhook triggers working (manual OR automatic)
- ✅ No JSON errors in PR creation
- ✅ All critical bugs fixed

**Target Date:** End of Day 2

---

## Phase 2: Strategic Redesign (Weeks 1-3)

### Core Reliability Metrics

#### Workflow Success Rate
- [ ] **>80% end-to-end success rate**
  - Before: ~60% (recent), ~16% (overall)
  - After: >80% of workflows complete all 8 phases
  - Measurement:
    ```sql
    SELECT
        CAST(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100 AS success_rate
    FROM workflow_history
    WHERE created_at > '2025-11-20'  -- After Phase 2 start
    ```

- [ ] **Zero orphaned resources**
  - Before: Orphaned worktrees, branches, PRs, processes
  - After: All resources cleaned up within 5 minutes of workflow end
  - Measurement:
    - `ls trees/` (should be empty after cleanup)
    - `git branch -r | grep adw-` (count remote ADW branches)
    - `ps aux | grep adw_` (count running ADW processes)
    - `gh pr list --state open --json number,title | grep adw` (count open ADW PRs)

---

#### Error Recovery

- [ ] **100% of failures trigger rollback**
  - Before: Failed workflows leave orphaned resources
  - After: All failures clean up resources
  - Measurement: Intentionally fail workflows, verify cleanup

- [ ] **Transient errors retried automatically**
  - Target: >90% of transient failures recover via retry
  - Measurement: Count retries in logs, compare to final status

- [ ] **Mean time to recovery <5 minutes**
  - Before: Manual intervention required
  - After: Automatic recovery within 5 minutes
  - Measurement: Time from error to successful retry or rollback completion

---

#### State Management

- [ ] **Zero state corruption incidents**
  - Before: State files could be corrupted by crashes
  - After: Atomic writes prevent corruption
  - Measurement: Intentionally crash workflows mid-write, verify state integrity

- [ ] **100% of state transitions validated**
  - Before: Invalid transitions possible
  - After: State machine rejects invalid transitions
  - Measurement: Unit tests + production monitoring

- [ ] **State schema migrations work**
  - Before: No migration support
  - After: Old state files automatically migrated
  - Measurement: Test with v1.0 state files, verify upgrade to v2.0

---

#### Concurrency & Resource Management

- [ ] **Zero concurrent workflow conflicts**
  - Before: Two workflows could start for same issue
  - After: Lock mechanism prevents conflicts
  - Measurement: Start 2 workflows for same issue simultaneously, verify only 1 proceeds

- [ ] **Resource quotas enforced**
  - Before: Unlimited worktrees could be created
  - After: Max 15 worktrees enforced
  - Measurement: Attempt to create 16th worktree, verify rejection

- [ ] **No port conflicts**
  - Before: Port conflicts possible
  - After: Port allocation managed centrally
  - Measurement: Start maximum concurrent workflows, verify unique ports

---

#### Observability

- [ ] **100% of workflows have structured logs**
  - Before: Unstructured logs, hard to parse
  - After: JSON logs with standardized fields
  - Measurement: Verify all log entries are valid JSON

- [ ] **Real-time status visibility**
  - Before: Must check database manually
  - After: Dashboard shows current workflow states
  - Measurement: Dashboard operational and accurate

- [ ] **Error categorization working**
  - Before: All errors treated equally
  - After: Errors classified (transient, rate_limit, fatal, etc.)
  - Measurement: Review error logs, verify categories assigned

---

### NL_REQUESTS.md Validation

#### Request Completion Rate

**Goal:** All 22 NL_REQUESTS workflows complete successfully

| Phase | Request | Status | Success Metric |
|-------|---------|--------|----------------|
| 1.1 | Extract Database Connection Utility | ✅ Complete | PR #48 merged |
| 1.2 | Migrate server.py to DB Utility | ✅ Complete | PR #51 merged |
| 1.3 | Migrate Core Modules to DB Utility | ✅ Complete | PR #53 merged |
| 1.4 | Extract LLM Client Utilities | 🔄 Phase 1 | Phase 1 validation |
| 1.5 | Migrate LLM Processors | ⏳ Pending | Phase 2 validation |
| 1.6 | Extract Subprocess Utilities | ⏳ Pending | Phase 2 validation |
| 1.7 | Extract Frontend Formatters | ⏳ Pending | Phase 2 validation |
| 2.1-4 | Backend Modularity (4 requests) | ⏳ Pending | Phase 2 validation |
| 3.1-3 | workflow_history Decomposition (3 requests) | ⏳ Pending | Phase 2 validation |
| 4.1-4 | Frontend Decomposition (4 requests) | ⏳ Pending | Phase 2 validation |

**Success Threshold:**
- **Minimum:** Requests 1.4-1.7 complete (100% of Phase 1 requests)
- **Target:** All 22 requests complete (100% success)
- **Measurement:** Count merged PRs from NL_REQUESTS workflows

---

### Performance Metrics

#### Workflow Duration

- [ ] **Average workflow duration <2 hours**
  - Measurement: `SELECT AVG(duration_seconds) / 3600.0 FROM workflow_history WHERE status = 'completed' AND created_at > '2025-11-20'`

- [ ] **No workflows stuck >4 hours**
  - Measurement: `SELECT COUNT(*) FROM workflow_history WHERE status IN ('planning', 'building', 'testing') AND created_at < datetime('now', '-4 hours')`

---

#### Cost Efficiency

- [ ] **Average cost per workflow <$3**
  - Before: Some workflows cost >$5
  - Target: Average <$3 using lightweight/haiku models
  - Measurement: `SELECT AVG(total_cost) FROM workflow_history WHERE created_at > '2025-11-20'`

- [ ] **No workflow exceeds budget**
  - Target: 100% of workflows stay within estimated cost ±20%
  - Measurement: Compare `total_cost` vs `estimated_cost_total`

---

### Testing Coverage

- [ ] **>80% code coverage for ADW modules**
  - Measurement: `pytest --cov=adws --cov-report=term-missing`

- [ ] **100% of phases have integration tests**
  - 8 phases × 1 integration test minimum
  - Measurement: Count test files in `adws/tests/integration/`

- [ ] **All failure scenarios tested**
  - Plan failure + rollback
  - Build failure + rollback
  - Test failure + retry
  - API rate limit + backoff
  - Concurrency conflict + lock rejection
  - Measurement: Test suite execution report

---

## Continuous Monitoring (Post-Implementation)

### Daily Metrics (First Week)

**Check every morning:**
```bash
# Workflow success rate (last 24h)
sqlite3 db/database.db "SELECT
  COUNT(*) as total,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
FROM workflow_history
WHERE created_at > datetime('now', '-1 day')"

# Orphaned resources
ls trees/ | wc -l  # Should be 0
git branch -r | grep adw- | wc -l  # Should be 0 or match active workflows

# Error rate
grep -c "ERROR" adws/logs/*.log

# Average duration
sqlite3 db/database.db "SELECT AVG(duration_seconds) / 3600.0 FROM workflow_history WHERE status = 'completed' AND created_at > datetime('now', '-1 day')"
```

---

### Weekly Metrics (Ongoing)

**Review every Monday:**
1. **Success Rate Trend**
   - Plot success rate over past week
   - Target: Steady >80%

2. **Error Categories**
   - Breakdown of errors by category
   - Identify patterns for improvement

3. **Resource Cleanup**
   - Verify no resource leaks
   - Check disk space trends

4. **Cost Analysis**
   - Average cost per workflow
   - Cost per phase breakdown

---

## Regression Prevention

### Automated Checks (CI/CD)

- [ ] **Pre-commit hooks:**
  - No `sys.exit(1)` without try-finally
  - All database writes use transactions
  - State writes use atomic operations

- [ ] **Pre-merge checks:**
  - All tests pass
  - Code coverage >80%
  - No new sys.exit(1) calls
  - Structured logging format validated

- [ ] **Post-deployment checks:**
  - Webhook service responding
  - Database migrations applied
  - No stale workflows after 24h

---

## Success Declaration

### Phase 1 Success (Day 2)
✅ Declare success when:
- [ ] Request 1.4 merged to main
- [ ] Database clean (0 stale workflows)
- [ ] Webhook working OR manual trigger documented
- [ ] All P0/P1 bugs fixed
- [ ] No regressions in existing functionality

### Phase 2 Success (Week 3)
✅ Declare success when:
- [ ] >80% workflow success rate (measured over 50+ workflows)
- [ ] All 22 NL_REQUESTS.md workflows complete
- [ ] Zero orphaned resources (7 consecutive days)
- [ ] Error recovery working (tested with intentional failures)
- [ ] Observability dashboard operational
- [ ] Full test suite passing (>80% coverage)
- [ ] Documentation complete
- [ ] Team can operate system without developer intervention

---

## Failure Criteria (When to Pause/Pivot)

### Red Flags (Phase 1)
🚨 Pause if:
- Request 1.4 fails 3+ times consecutively
- New bugs introduced worse than old bugs
- Database corruption occurs
- Webhook cannot be fixed within 2 days

### Red Flags (Phase 2)
🚨 Pause if:
- Success rate does not improve after Week 1
- Rollback mechanism fails in testing
- State machine causes more issues than it solves
- Resource leaks persist after fixes

---

## Reporting

### Daily Status (During Implementation)
```
Date: YYYY-MM-DD
Phase: [1 or 2]
Day: [X of Y]

✅ Completed:
- Task 1
- Task 2

🔄 In Progress:
- Task 3

⏳ Blocked:
- Task 4 (reason)

📊 Metrics:
- Workflows completed today: X
- Success rate: Y%
- Bugs fixed: Z
```

### Weekly Summary (Post-Implementation)
```
Week: YYYY-MM-DD to YYYY-MM-DD

📈 Success Rate: X%
🐛 Bugs Found: Y
✅ Bugs Fixed: Z
💰 Avg Cost: $X.XX
⏱️ Avg Duration: Xh

🔝 Top Issues:
1. Issue type (count)
2. Issue type (count)

📋 Next Week:
- Priority 1
- Priority 2
```

---

## Long-Term Goals (3-6 Months)

- [ ] **>95% success rate** sustained for 30 days
- [ ] **<$2 average cost** per workflow
- [ ] **<1 hour average duration** for lightweight workflows
- [ ] **Zero manual interventions** required for 30 days
- [ ] **All 22 NL_REQUESTS complete** and validated
- [ ] **100+ workflows executed** with consistent reliability
