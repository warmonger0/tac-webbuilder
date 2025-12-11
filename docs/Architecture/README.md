# Architecture Documentation

System architecture and technical design documents for the tac-webbuilder project.

**Created:** 2025-11-17
**Updated:** 2025-12-11 (Session 19 - Phase 4)

## Overview

This folder contains architectural documentation including system design documents, technical overviews, architecture specifications, and design decision records.

---

## Quick Navigation

**New to the project?**
- Start with [Quick Start Guides](#quick-start-guides)
- Review [Session 19 Improvements](#session-19-improvements-new) for modern patterns

**Migrating existing code?**
- [Session 19 Migration Guide](../guides/migration-guide-session-19.md)
- [Frontend Patterns](../patterns/frontend-patterns.md)
- [Backend Patterns](../patterns/backend-patterns.md)

**API Reference?**
- [WebSocket API](../api/websocket-api.md)
- [Error Handler](../api/error-handler.md)
- [Reusable Components](../api/reusable-components.md)

---

## Architecture Documents

### Session 19 Improvements (NEW)

**[session-19-improvements.md](./session-19-improvements.md)** (~9,800 lines)

Comprehensive documentation of Session 19's architectural improvements:
- **Phase 1:** Database & State Management (Single Source of Truth)
- **Phase 2:** WebSocket Real-Time Updates (NO POLLING mandate)
- **Phase 3:** Code Quality & Consistency (Standardized patterns)
- **Phase 4:** Documentation & Knowledge Transfer

**Key Topics:**
- Single Source of Truth (SSOT) pattern
- WebSocket architecture and data flow
- Repository naming standards
- Reusable UI components
- Structured error handling

**When to read:**
- Understanding modern architecture patterns
- Learning Session 19 improvements
- Reference for implementation decisions

---

### Real-Time Updates & WebSocket

**[REAL_TIME_UPDATES_STANDARDIZATION.md](./REAL_TIME_UPDATES_STANDARDIZATION.md)**

Standards for real-time update patterns.

**[WEBSOCKET_ARCHITECTURE.md](./WEBSOCKET_ARCHITECTURE.md)**

WebSocket implementation architecture.

---

### Queue & Workflow

**[HOPPER_WORKFLOW.md](./HOPPER_WORKFLOW.md)**

Hopper workflow architecture and implementation.

**[QUEUE_DETERMINISM_PLAN.md](./QUEUE_DETERMINISM_PLAN.md)**

Plan for deterministic queue implementation.

**[DETERMINISTIC_QUEUE_IMPLEMENTATION.md](./DETERMINISTIC_QUEUE_IMPLEMENTATION.md)**

Implementation of deterministic queue patterns.

**[NXTCHAT_QUEUE_VALIDATION.md](./NXTCHAT_QUEUE_VALIDATION.md)**

Queue validation for NxtChat integration.

---

### Workflow Save/Resume

**[workflow-save-resume.md](./workflow-save-resume.md)**

Complete workflow save and resume architecture.

**[workflow-save-resume-quickstart.md](./workflow-save-resume-quickstart.md)**

Quick start guide for workflow save/resume.

**[workflow-save-resume-diagrams.md](./workflow-save-resume-diagrams.md)**

Architecture diagrams for workflow persistence.

---

### Cleanup & Performance

**[CLEANUP_PERFORMANCE_OPTIMIZATION.md](decisions/CLEANUP_PERFORMANCE_OPTIMIZATION.md)**

Performance optimization strategies for cleanup operations.

**[POST_SHIPPING_CLEANUP_ARCHITECTURE.md](decisions/POST_SHIPPING_CLEANUP_ARCHITECTURE.md)**

Architecture for post-shipping cleanup phase.

**[POST_SHIPPING_CLEANUP_IMPLEMENTATION_PLAN.md](decisions/POST_SHIPPING_CLEANUP_IMPLEMENTATION_PLAN.md)**

Implementation plan for cleanup phase.

**[POST_SHIPPING_CLEANUP_SUMMARY.md](decisions/POST_SHIPPING_CLEANUP_SUMMARY.md)**

Summary of cleanup phase implementation and results.

---

## Pattern Documentation

Location: `docs/patterns/`

### Frontend Patterns

**[frontend-patterns.md](../patterns/frontend-patterns.md)** (~840 lines)

Complete frontend development patterns:
- Data fetching (useQuery vs WebSocket)
- UI components (LoadingState, ErrorBanner, ConfirmationDialog)
- Error handling (errorHandler utility)
- State management
- Best practices and migration checklists

---

### Backend Patterns

**[backend-patterns.md](../patterns/backend-patterns.md)** (~940 lines)

Complete backend development patterns:
- Repository pattern (standard CRUD naming)
- Service layer organization
- State management (Single Source of Truth)
- WebSocket broadcasting
- Error handling and best practices

---

## API References

Location: `docs/api/`

### WebSocket API Reference

**[websocket-api.md](../api/websocket-api.md)** (~1,500 lines)

Complete WebSocket API documentation:
- All 8 WebSocket hooks
- Message formats
- Connection management
- Error handling and troubleshooting

---

### Error Handler API Reference

**[error-handler.md](../api/error-handler.md)** (~1,400 lines)

Complete errorHandler utility documentation:
- All 7 utility functions
- Usage patterns and examples
- Testing guide

---

### Reusable Components API Reference

**[reusable-components.md](../api/reusable-components.md)** (~1,800 lines)

Complete UI components documentation:
- LoadingState, ErrorBanner, ConfirmationDialog
- Usage examples and testing guide

---

## Migration Guides

Location: `docs/guides/`

### Session 19 Migration Guide

**[migration-guide-session-19.md](../guides/migration-guide-session-19.md)** (~2,000 lines)

Step-by-step migration guide:
- Backend: Repository method renaming
- Frontend: Manual fetch → useQuery
- Frontend: HTTP polling → WebSocket
- Frontend: Custom UI → Reusable components
- Frontend: Inconsistent errors → errorHandler
- Complete migration examples

---

## Quick Start Guides

Location: `.claude/commands/quick_start/`

### Frontend Quick Start

**[frontend.md](../../.claude/commands/quick_start/frontend.md)** (~200 lines)

Quick reference for frontend development with Session 19 patterns.

### Backend Quick Start

**[backend.md](../../.claude/commands/quick_start/backend.md)** (~200 lines)

Quick reference for backend development with repository standards.

### ADW Workflows Quick Start

**[adw.md](../../.claude/commands/quick_start/adw.md)**

Quick reference for ADW workflows and SDLC phases.

---

## Related Documentation

### Core Documentation

- [Main README](../../README.md) - Project overview and setup
- [API Documentation](../api.md) - Complete API reference
- [Web UI Documentation](../web-ui.md) - Frontend architecture
- [Backend Repository Standards](../backend/repository-standards.md) - Repository naming

### Feature Documentation

- [Planned Features](../../.claude/commands/references/planned_features.md) - Roadmap tracking
- [Observability](../../.claude/commands/references/observability.md) - Logging and analytics
- [Analytics](../../.claude/commands/references/analytics.md) - Cost and pattern analytics

### Session Documentation

- [Session 19](../session-19/) - All Session 19 phase documents

---

## How to Use This Documentation

### For New Developers

1. Start with [Quick Start Guides](#quick-start-guides)
2. Review [Session 19 Improvements](#session-19-improvements-new)
3. Deep dive into [Pattern Documentation](#pattern-documentation)

### For Existing Developers

1. Read [Session 19 Migration Guide](../guides/migration-guide-session-19.md)
2. Reference [Pattern Documentation](#pattern-documentation)
3. Use [API References](#api-references) for implementation details

### For Feature Work

1. Check relevant Quick Start guide
2. Review Pattern documentation
3. Reference API docs as needed
4. Follow Migration guide for updates

---

## Documentation Standards

### When to Create New Documentation

Create new architecture documentation when:
- Introducing major architectural changes
- Establishing new patterns or standards
- Documenting cross-cutting concerns
- Providing system-wide context

### Documentation Types

| Type | Purpose | Location | Example |
|------|---------|----------|---------|
| Architecture | System design | `docs/architecture/` | session-19-improvements.md |
| Patterns | Dev standards | `docs/patterns/` | frontend-patterns.md |
| API Reference | APIs | `docs/api/` | websocket-api.md |
| Migration Guides | Upgrades | `docs/guides/` | migration-guide-session-19.md |
| Quick Start | Quick ref | `.claude/commands/quick_start/` | frontend.md |

---

## Additional Resources

- [ADW Documentation](../ADW/) - ADW system architecture
- [Main Architecture Guide](../architecture.md) - High-level system architecture
- [Cost Optimization](../Cost-Optimization/) - Performance and cost optimization

---

**Last Updated:** Session 19 - Phase 4 (December 2025)

This index provides comprehensive navigation for all architecture documentation in the tac-webbuilder project.
