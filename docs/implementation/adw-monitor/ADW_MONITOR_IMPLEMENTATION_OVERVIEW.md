# ADW Monitor Implementation Overview

## Purpose
This document provides an overview of the ADW Monitor implementation, which provides real-time monitoring of all ADW workflows in the system.

## Complete Design
For the complete design specifications, including UI/UX, API schemas, and all three implementation phases, see:
- [ISSUE_ADW_MONITOR_DESIGN.md](./ISSUE_ADW_MONITOR_DESIGN.md)

## Implementation Phases

### Phase 1: Backend API ✅
**Status:** Implemented

Creates the `/api/adw-monitor` endpoint that aggregates ADW workflow status from multiple sources:
- ADW state files in `agents/*/adw_state.json`
- Running process checks
- Worktree existence validation
- Phase progress calculation
- Cost tracking

**Implementation Details:** See [PHASE_1_BACKEND_API.md](./PHASE_1_BACKEND_API.md)

### Phase 2: Frontend Component 🔄
**Status:** Planned

Creates the `AdwMonitorCard.tsx` React component that displays workflow status in the New Request tab.

**Features:**
- Real-time polling (10s for active, 30s for idle)
- Status indicators with color coding
- Phase progress bars
- Cost tracking display
- User interactions (view logs, cancel workflow)

### Phase 3: Polish & Integration 📋
**Status:** Planned

Adds polish and advanced features:
- Animations and visual enhancements
- WebSocket integration for real-time updates
- Performance optimizations
- Enhanced error handling
- Comprehensive documentation

## Architecture

### Data Flow
```
ADW State Files → Backend Aggregation → API Endpoint → Frontend Display
   (agents/)     (adw_monitor.py)    (/api/adw-monitor)  (AdwMonitorCard)
```

### Key Components
1. **Core Module:** `app/server/core/adw_monitor.py` - State aggregation logic
2. **API Endpoint:** `app/server/server.py` - FastAPI endpoint
3. **Data Models:** Pydantic models for request/response validation
4. **Tests:** Unit, integration, and E2E test coverage

## Success Metrics
- API response time: <200ms
- Accurate status reporting: 100%
- Test coverage: >80%
- Zero regressions in existing functionality

## Related Documentation
- [Code Quality Standards](../../../.claude/references/code_quality_standards.md)
- [TypeScript Standards](../../../.claude/references/typescript_standards.md)
