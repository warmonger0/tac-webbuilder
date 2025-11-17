# Launch & Health Check Fixes Implementation Guide

**Fix WebSocket connections, reduce log verbosity, and improve system health monitoring.**

---

## 📋 Executive Summary

The `launch.sh` startup process produces voluminous output with WebSocket connection failures, database sync messages, and API warnings. **The core functionality works correctly**, but false health check failures cause the frontend to fall back to polling mode instead of using real-time WebSocket updates.

### Impact
- **Current State:** Frontend polls every 3 seconds (fallback mode)
- **Desired State:** Real-time WebSocket updates (instant)
- **Performance Impact:** 3-second latency vs. instant updates
- **User Experience:** Degraded real-time responsiveness

### Root Cause
Health check uses HTTP HEAD requests to test WebSocket endpoints, which always return 404 because WebSockets require an upgrade handshake.

---

## 🎯 Implementation Overview

| Part | Focus Area | Duration | Priority | Lines of Code |
|------|-----------|----------|----------|---------------|
| 1 | WebSocket Health Check | 30 min | **Critical** | ~40 lines |
| 2 | Logging Verbosity | 15 min | Medium | ~20 lines |
| 3 | API Validation | 15 min | Medium | ~15 lines |
| 4 | Workflow Cleanup | 20 min | Low | ~30 lines |

**Total Timeline:** 1.5 hours
**Total Impact:** Real-time WebSocket functionality restored

---

## 📚 Implementation Parts

### Quick Navigation

1. **[PART_1_WEBSOCKET_HEALTH_CHECK.md](PART_1_WEBSOCKET_HEALTH_CHECK.md)** (Critical - Start Here)
   - Fix WebSocket health check in `scripts/health_check.sh`
   - Restore real-time WebSocket connections
   - Eliminate polling fallback mode
   - **Highest impact on user experience**

2. **[PART_2_LOGGING_VERBOSITY.md](PART_2_LOGGING_VERBOSITY.md)** (Medium Priority)
   - Reduce database sync log output
   - Change INFO → DEBUG for routine operations
   - Keep summary logs visible
   - **Reduces startup noise by ~270 lines**

3. **[PART_3_API_VALIDATION.md](PART_3_API_VALIDATION.md)** (Medium Priority)
   - Fix workflows API health check
   - Handle array response format correctly
   - Eliminate false warning messages
   - **Cleaner health check output**

4. **[PART_4_WORKFLOW_CLEANUP.md](PART_4_WORKFLOW_CLEANUP.md)** (Low Priority)
   - Remove invalid workflow directories
   - Fix GitHub API warnings
   - Clean up test data
   - **Maintenance and cleanup**

---

## 🚀 Quick Start

### Prerequisites
- Application running locally (backend on port 8000, frontend on port 5173)
- Git repository at `/Users/Warmonger0/tac/tac-webbuilder`
- Python 3.10+ with `uv` installed
- Bun installed for frontend

### Implementation Order

**Step 1: Critical Fix (30 minutes)**
```bash
# Fix WebSocket health check
# Follow: PART_1_WEBSOCKET_HEALTH_CHECK.md

# Test the fix
./scripts/health_check.sh

# Verify WebSockets working
# Open http://localhost:5173 and check browser console
# Should see: "WebSocket connected: ws://localhost:8000/ws/workflows"
```

**Step 2: Reduce Noise (15 minutes)**
```bash
# Reduce logging verbosity
# Follow: PART_2_LOGGING_VERBOSITY.md

# Test the fix
./scripts/start.sh
# Should see ~270 fewer log lines during startup
```

**Step 3: Fix API Check (15 minutes)**
```bash
# Fix workflows API validation
# Follow: PART_3_API_VALIDATION.md

# Test the fix
./scripts/health_check.sh
# Should see green checkmark for workflows API
```

**Step 4: Cleanup (20 minutes)**
```bash
# Remove invalid workflows
# Follow: PART_4_WORKFLOW_CLEANUP.md

# Verify cleanup
ls agents/
# Should not see adw-* directories with invalid issue numbers
```

---

## 📊 Expected Outcomes

### Before Implementation
```
Launch output:
- 370+ log lines
- WebSocket 404 errors
- API validation warnings
- GitHub warnings for invalid issues
- Frontend using polling mode (3-second intervals)
```

### After Implementation
```
Launch output:
- ~100 log lines (73% reduction)
- ✅ WebSocket endpoints available
- ✅ Workflows API validated
- No GitHub warnings
- Frontend using WebSockets (instant updates)
```

### Performance Improvements
- **Startup logs:** 370 lines → 100 lines (73% reduction)
- **Update latency:** 3 seconds → instant (100% improvement)
- **Network requests:** 20/min polling → event-driven (90% reduction)
- **Server load:** Reduced by ~15% (fewer polling requests)

---

## 🧪 Testing Strategy

### Unit Testing
Each part includes specific test commands:
- WebSocket upgrade handshake test
- Log level verification
- API response format validation
- Workflow directory validation

### Integration Testing
```bash
# Full system test
./scripts/start.sh

# Verify WebSocket connections in browser console
# Open: http://localhost:5173
# Console should show WebSocket connection messages

# Verify reduced log output
./scripts/start.sh 2>&1 | wc -l
# Should be ~100 lines instead of 370+
```

### End-to-End Validation
1. Start application: `./scripts/start.sh`
2. Open browser: `http://localhost:5173`
3. Open DevTools → Network → WS tab
4. Verify WebSocket connections established
5. Create test workflow
6. Verify instant updates (no 3-second delay)

---

## 📁 Files Modified

### Scripts
- `scripts/health_check.sh` - WebSocket and API validation fixes

### Backend
- `app/server/core/workflow_history.py` - Log level adjustments

### New Scripts
- `scripts/cleanup_invalid_workflows.sh` - Workflow cleanup utility

---

## 🔧 Troubleshooting

### WebSocket Still Not Connecting

**Symptom:** Browser console shows polling instead of WebSocket
**Check:**
```bash
# Verify health check passes
./scripts/health_check.sh | grep WebSocket
# Should show green checkmarks

# Test WebSocket manually
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: dGVzdA==" \
  http://localhost:8000/ws/workflows
# Should return 101 Switching Protocols
```

**Fix:** Verify backend is running on port 8000

---

### Still Seeing Verbose Logs

**Symptom:** 300+ log lines during startup
**Check:**
```bash
# Verify log level changes
grep "logger.debug" app/server/core/workflow_history.py
# Should see debug() instead of info() for routine operations
```

**Fix:** Restart backend to apply changes

---

### API Validation Fails

**Symptom:** Health check shows API warning
**Check:**
```bash
# Test API manually
curl http://localhost:8000/api/workflows | python3 -m json.tool
# Should return valid JSON array
```

**Fix:** Verify response is array, update health check accordingly

---

### GitHub Warnings Persist

**Symptom:** Still seeing invalid issue warnings
**Check:**
```bash
# List workflow directories
ls agents/ | grep -E "999|base"
# Should be empty after cleanup
```

**Fix:** Re-run cleanup script

---

## 📋 Implementation Checklist

### Part 1: WebSocket Health Check (Critical)
- [ ] Update health check script with WebSocket upgrade test
- [ ] Test with `./scripts/health_check.sh`
- [ ] Verify browser console shows WebSocket connections
- [ ] Confirm no polling fallback in DevTools Network tab
- [ ] Validate instant updates when creating workflows

### Part 2: Logging Verbosity (Medium)
- [ ] Change `logger.info()` → `logger.debug()` for routine DB operations
- [ ] Keep summary logs at INFO level
- [ ] Test startup log output
- [ ] Verify ~270 line reduction
- [ ] Confirm critical messages still visible

### Part 3: API Validation (Medium)
- [ ] Update workflows API check to expect array
- [ ] Test with `./scripts/health_check.sh`
- [ ] Verify green checkmark for workflows API
- [ ] Confirm no false warnings

### Part 4: Workflow Cleanup (Low)
- [ ] Create cleanup script
- [ ] Run cleanup for invalid workflows
- [ ] Verify no GitHub warnings during sync
- [ ] Document cleanup process

---

## 🎓 Key Concepts

### WebSocket Upgrade Handshake
WebSockets use HTTP upgrade mechanism:
1. Client sends HTTP request with upgrade headers
2. Server responds with `101 Switching Protocols`
3. Connection upgrades to WebSocket protocol
4. Bidirectional communication begins

**HEAD requests don't work** because they skip the upgrade handshake.

### Polling vs WebSocket
| Aspect | Polling | WebSocket |
|--------|---------|-----------|
| Latency | 3 seconds | Instant |
| Network | 20 requests/min | Event-driven |
| Server load | High | Low |
| Scalability | Poor | Excellent |

### Log Levels
- **DEBUG:** Detailed diagnostic info (development only)
- **INFO:** General informational messages
- **WARNING:** Something unexpected but handled
- **ERROR:** Serious problem, feature may not work

**Strategy:** Routine operations → DEBUG, summaries → INFO

---

## 🎯 Success Criteria

### Overall Success
- [ ] WebSocket connections established on startup
- [ ] Browser console shows real-time WebSocket messages
- [ ] No polling fallback in DevTools Network tab
- [ ] Startup logs reduced to ~100 lines
- [ ] Health check passes all tests with green checkmarks
- [ ] No GitHub API warnings during sync

### Performance Metrics
- [ ] Update latency < 100ms (was 3000ms)
- [ ] Network requests reduced by 90%
- [ ] Startup log output reduced by 70%
- [ ] Health check completes in < 5 seconds

### User Experience
- [ ] Instant workflow status updates
- [ ] Clean, readable startup output
- [ ] No confusing error messages
- [ ] Confident system health monitoring

---

## 📚 Additional Resources

### Related Documentation
- `docs/architecture.md` - WebSocket architecture
- `docs/troubleshooting.md` - General troubleshooting guide
- `docs/web-ui.md` - Frontend WebSocket integration

### Code References
- `app/server/server.py:1224-1301` - WebSocket endpoints
- `app/client/src/hooks/useWebSocket.ts` - Frontend WebSocket hooks
- `scripts/health_check.sh` - Health monitoring script

### External Resources
- [WebSocket RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455) - WebSocket protocol spec
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) - FastAPI WebSocket documentation

---

## 🔄 Future Improvements

### Phase 2: Enhanced Health Monitoring
- Add WebSocket connection count metric
- Monitor message throughput
- Track reconnection attempts
- Alert on persistent failures

### Phase 3: Advanced Logging
- Structured JSON logging
- Log aggregation (ELK stack)
- Real-time log filtering
- Performance profiling integration

### Phase 4: Cleanup Automation
- Automated workflow archival
- Retention policy implementation
- Disk space monitoring
- Automated cleanup scheduling

---

## ✅ You're Ready!

**Start with Part 1** - fixing the WebSocket health check will immediately restore real-time functionality.

**Parts 2-4** can be implemented in any order based on your priorities.

**Total time investment: 1.5 hours for significant UX improvements.**

---

**Last Updated:** 2025-11-17
**Status:** Ready for Implementation
**Priority:** Part 1 (Critical), Parts 2-4 (Medium-Low)
