# Task: Plans Panel Database Migration - Frontend (Session 8B)

## Context
I'm working on the tac-webbuilder project. Session 8A completed the backend infrastructure for the Plans Panel database migration (database, service, API). This session (8B) implements the frontend integration: TypeScript API client, component refactor to use TanStack Query, and real-time updates from the database.

## Objective
Refactor PlansPanel.tsx from hardcoded JSX to a dynamic, database-driven component that fetches data from the API, displays real-time updates, and provides a statistics dashboard.

## Background Information
- **Session 8A Complete:** Database table, service layer, 7 API endpoints operational
- **Session 8B Scope:** Frontend only (TypeScript client, component refactor)
- **Current State:** PlansPanel.tsx has ~528 lines of hardcoded JSX
- **Goal:** Replace with API calls, TanStack Query, and dynamic rendering

---

## Implementation Steps

### Step 1: TypeScript API Client (30 min)

**Create:** `app/client/src/api/plannedFeaturesClient.ts` (~150 lines)

**TypeScript Types:**
```typescript
export interface PlannedFeature {
  id: number;
  item_type: 'session' | 'feature' | 'bug' | 'enhancement';
  title: string;
  description?: string;
  status: 'planned' | 'in_progress' | 'completed' | 'cancelled';
  priority?: 'high' | 'medium' | 'low';
  estimated_hours?: number;
  actual_hours?: number;
  session_number?: number;
  github_issue_number?: number;
  parent_id?: number;
  tags: string[];
  completion_notes?: string;
  created_at?: string;
  updated_at?: string;
  started_at?: string;
  completed_at?: string;
}

export interface PlannedFeatureCreate {
  item_type: string;
  title: string;
  description?: string;
  status?: string;
  priority?: string;
  estimated_hours?: number;
  session_number?: number;
  github_issue_number?: number;
  parent_id?: number;
  tags?: string[];
}

export interface PlannedFeatureUpdate {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  estimated_hours?: number;
  actual_hours?: number;
  github_issue_number?: number;
  tags?: string[];
  completion_notes?: string;
}

export interface PlannedFeaturesStats {
  by_status: Record<string, number>;
  by_priority: Record<string, number>;
  by_type: Record<string, number>;
  total_estimated_hours: number;
  total_actual_hours: number;
  completion_rate: number;
}
```

**API Client Functions:**
```typescript
const API_BASE = '/api/planned-features';

export const plannedFeaturesClient = {
  /**
   * Get all planned features with optional filtering
   */
  getAll: async (params?: {
    status?: string;
    item_type?: string;
    priority?: string;
    limit?: number;
  }): Promise<PlannedFeature[]> => {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.item_type) queryParams.append('item_type', params.item_type);
    if (params?.priority) queryParams.append('priority', params.priority);
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = queryParams.toString()
      ? `${API_BASE}?${queryParams}`
      : API_BASE;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch planned features: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * Get single planned feature by ID
   */
  getById: async (id: number): Promise<PlannedFeature> => {
    const response = await fetch(`${API_BASE}/${id}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch planned feature: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * Get statistics about planned features
   */
  getStats: async (): Promise<PlannedFeaturesStats> => {
    const response = await fetch(`${API_BASE}/stats`);
    if (!response.ok) {
      throw new Error(`Failed to fetch statistics: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * Get recently completed features
   */
  getRecentCompletions: async (days: number = 30): Promise<PlannedFeature[]> => {
    const response = await fetch(`${API_BASE}/recent-completions?days=${days}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch recent completions: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * Create a new planned feature
   */
  create: async (data: PlannedFeatureCreate): Promise<PlannedFeature> => {
    const response = await fetch(API_BASE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error(`Failed to create planned feature: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * Update an existing planned feature
   */
  update: async (id: number, data: PlannedFeatureUpdate): Promise<PlannedFeature> => {
    const response = await fetch(`${API_BASE}/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error(`Failed to update planned feature: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * Delete a planned feature (soft delete)
   */
  delete: async (id: number): Promise<void> => {
    const response = await fetch(`${API_BASE}/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(`Failed to delete planned feature: ${response.statusText}`);
    }
  },
};
```

---

### Step 2: Component Refactor (90 min)

**Modify:** `app/client/src/components/PlansPanel.tsx`

**Replace hardcoded data with API calls:**
```typescript
import { useQuery } from '@tanstack/react-query';
import { plannedFeaturesClient, PlannedFeature } from '../api/plannedFeaturesClient';

export function PlansPanel() {
  // Fetch all features
  const {
    data: features,
    isLoading,
    error
  } = useQuery({
    queryKey: ['planned-features'],
    queryFn: () => plannedFeaturesClient.getAll({ limit: 200 }),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['planned-features-stats'],
    queryFn: () => plannedFeaturesClient.getStats(),
    refetchInterval: 60000, // Refresh every 60 seconds
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-center p-8">
          <div className="animate-pulse text-gray-500">Loading plans...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-red-600">
          Error loading plans: {(error as Error).message}
        </div>
      </div>
    );
  }

  // Group features by status
  const inProgress = features?.filter(f => f.status === 'in_progress') || [];
  const planned = features?.filter(f => f.status === 'planned') || [];
  const completed = features?.filter(f => f.status === 'completed')
    .sort((a, b) => {
      // Sort by completed_at DESC (most recent first)
      const dateA = new Date(a.completed_at || 0);
      const dateB = new Date(b.completed_at || 0);
      return dateB.getTime() - dateA.getTime();
    }) || [];

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Pending Work Items
      </h2>

      {/* Statistics Dashboard */}
      {stats && (
        <div className="mb-6 grid grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
          <div>
            <div className="text-sm text-gray-600">Total Items</div>
            <div className="text-2xl font-bold">
              {Object.values(stats.by_status).reduce((a, b) => a + b, 0)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">In Progress</div>
            <div className="text-2xl font-bold text-blue-600">
              {stats.by_status.in_progress || 0}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Planned</div>
            <div className="text-2xl font-bold text-purple-600">
              {stats.by_status.planned || 0}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Completed</div>
            <div className="text-2xl font-bold text-green-600">
              {stats.by_status.completed || 0}
            </div>
          </div>
        </div>
      )}

      {/* In Progress Section */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-blue-700 mb-3 flex items-center">
          <span className="mr-2">🔄</span> In Progress
        </h3>
        <div className="space-y-2 pl-6">
          {inProgress.length === 0 ? (
            <p className="text-gray-500 italic">No items in progress</p>
          ) : (
            inProgress.map(feature => (
              <FeatureItem key={feature.id} feature={feature} />
            ))
          )}
        </div>
      </div>

      {/* Planned Section */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-purple-700 mb-3 flex items-center">
          <span className="mr-2">📋</span> Planned Fixes & Enhancements
        </h3>
        <div className="space-y-3 pl-6">
          {planned.length === 0 ? (
            <p className="text-gray-500 italic">No planned items</p>
          ) : (
            planned.map(feature => (
              <FeatureItem key={feature.id} feature={feature} />
            ))
          )}
        </div>
      </div>

      {/* Recently Completed Section */}
      <div>
        <h3 className="text-lg font-semibold text-green-700 mb-3 flex items-center">
          <span className="mr-2">✅</span> Recently Completed
        </h3>
        <div className="space-y-3 pl-6">
          {completed.length === 0 ? (
            <p className="text-gray-500 italic">No completed items</p>
          ) : (
            completed.slice(0, 15).map(feature => (
              <FeatureItem key={feature.id} feature={feature} />
            ))
          )}
        </div>
      </div>

      {/* Footer Note */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <p className="text-sm text-gray-500 italic">
          Note: All items above are optional enhancements. System is fully functional and production-ready as-is.
        </p>
      </div>
    </div>
  );
}

/**
 * Individual feature/session item component
 */
function FeatureItem({ feature }: { feature: PlannedFeature }) {
  const isCompleted = feature.status === 'completed';
  const isInProgress = feature.status === 'in_progress';

  // Format date
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return null;
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Priority badge color
  const priorityColor = {
    high: 'bg-red-100 text-red-700',
    medium: 'bg-orange-100 text-orange-700',
    low: 'bg-blue-100 text-blue-700'
  }[feature.priority || 'low'];

  return (
    <div className="flex items-start">
      <input
        type="checkbox"
        checked={isCompleted}
        className="mt-1 mr-3"
        disabled
        readOnly
      />
      <div className="flex-1">
        {/* Title and Status */}
        <div className="flex items-center gap-2">
          <div className="font-medium text-gray-700">{feature.title}</div>
          {isInProgress && (
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
              In Progress
            </span>
          )}
          {feature.priority && (
            <span className={`text-xs px-2 py-0.5 rounded ${priorityColor}`}>
              {feature.priority.toUpperCase()}
            </span>
          )}
        </div>

        {/* Completion info */}
        {feature.completed_at && (
          <div className="text-sm text-gray-500">
            Completed {formatDate(feature.completed_at)}
            {feature.actual_hours && ` (~${feature.actual_hours} hours)`}
          </div>
        )}

        {/* Description */}
        {feature.description && (
          <div className="text-sm text-gray-600 mt-1">
            {feature.description}
          </div>
        )}

        {/* Completion notes */}
        {feature.completion_notes && (
          <div className="text-sm text-gray-600 mt-1 italic">
            {feature.completion_notes}
          </div>
        )}

        {/* Tags */}
        {feature.tags && feature.tags.length > 0 && (
          <div className="flex gap-2 mt-2 flex-wrap">
            {feature.tags.map(tag => (
              <span
                key={tag}
                className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* GitHub issue link */}
        {feature.github_issue_number && (
          <div className="text-sm text-blue-600 mt-1">
            <a
              href={`https://github.com/owner/repo/issues/${feature.github_issue_number}`}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline"
            >
              Issue #{feature.github_issue_number}
            </a>
          </div>
        )}

        {/* Time estimate (for planned items) */}
        {!isCompleted && feature.estimated_hours && (
          <div className="text-sm text-gray-500 mt-1">
            Estimated: {feature.estimated_hours} hours
          </div>
        )}
      </div>
    </div>
  );
}
```

**Key Changes:**
- ✅ Replace all hardcoded JSX with API data
- ✅ TanStack Query for data fetching
- ✅ Real-time updates (30-second polling)
- ✅ Statistics dashboard at top
- ✅ Dynamic grouping by status
- ✅ Loading and error states
- ✅ Tag display
- ✅ Priority badges
- ✅ GitHub issue links
- ✅ Time estimates and actuals

---

### Step 3: Test Frontend Integration (20 min)

**Manual Testing Checklist:**

1. **Start backend:**
   ```bash
   cd app/server
   .venv/bin/python3 main.py
   ```

2. **Start frontend:**
   ```bash
   cd app/client
   bun run dev
   ```

3. **Navigate to Panel 5** (Plans Panel) at http://localhost:5173

4. **Verify display:**
   - ✅ Statistics dashboard shows counts
   - ✅ Sessions 1-7 appear in "Recently Completed"
   - ✅ Session 8 appears in "In Progress"
   - ✅ Sessions 9-14 appear in "Planned"
   - ✅ Tags display correctly
   - ✅ No hardcoded data visible

5. **Test real-time updates:**
   - Open browser console
   - Wait 30 seconds
   - Should see new fetch requests in network tab
   - Data refreshes automatically

6. **Test API manually:**
   ```bash
   # Get all features
   curl http://localhost:8000/api/planned-features

   # Get stats
   curl http://localhost:8000/api/planned-features/stats

   # Get specific feature
   curl http://localhost:8000/api/planned-features/1
   ```

7. **Test error handling:**
   - Stop backend server
   - Frontend should show error message
   - Restart backend
   - Frontend should recover automatically

---

### Step 4: Documentation (10 min)

**Create:** `docs/features/plans-panel.md` (~200 lines)

```markdown
# Plans Panel - Database-Driven Planning System

## Overview
The Plans Panel (Panel 5) provides a database-driven system for tracking project planning,
session history, feature roadmap, and work items with full CRUD operations and API access.

## Architecture

### Backend
- **Database:** `planned_features` table (SQLite + PostgreSQL)
- **Service:** `PlannedFeaturesService` - Full CRUD with filtering
- **API:** 7 REST endpoints at `/api/planned-features`

### Frontend
- **Component:** `PlansPanel.tsx` - Dynamic rendering with TanStack Query
- **API Client:** `plannedFeaturesClient.ts` - TypeScript client
- **Real-time Updates:** 30-second polling for live data
- **Statistics Dashboard:** Real-time counts by status/priority/type

## Features

### Data Display
- **In Progress:** Currently active sessions/features
- **Planned:** Future work items with estimates
- **Recently Completed:** Last 15 completed items with dates and notes
- **Statistics Dashboard:** Live counts and metrics

### Item Properties
- Title, description, completion notes
- Status (planned, in_progress, completed, cancelled)
- Priority (high, medium, low) with color-coded badges
- Time estimates and actuals
- Tags for categorization
- GitHub issue links
- Parent/child relationships for subtasks

### Real-time Updates
- Automatic polling every 30 seconds
- Statistics refresh every 60 seconds
- Seamless data synchronization
- Error recovery on backend reconnection

## Usage

### Web UI
Navigate to Panel 5 (Plans Panel) to view planned work items.

### API Access

**Get all features:**
```bash
curl http://localhost:8000/api/planned-features
```

**Get statistics:**
```bash
curl http://localhost:8000/api/planned-features/stats
```

**Create new feature:**
```bash
curl -X POST http://localhost:8000/api/planned-features \
  -H "Content-Type: application/json" \
  -d '{
    "item_type": "feature",
    "title": "New Feature",
    "status": "planned",
    "priority": "high",
    "estimated_hours": 3.0,
    "tags": ["backend", "api"]
  }'
```

**Update feature status:**
```bash
curl -X PATCH http://localhost:8000/api/planned-features/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

### Programmatic Access

```python
from app.server.services.planned_features_service import PlannedFeaturesService
from app.server.models.workflow import PlannedFeatureCreate

service = PlannedFeaturesService()

# Create feature
feature = service.create(PlannedFeatureCreate(
    item_type='feature',
    title='New Feature',
    status='planned',
    priority='high',
    estimated_hours=5.0,
    tags=['backend', 'api']
))

# Update status
from app.server.models.workflow import PlannedFeatureUpdate
service.update(feature.id, PlannedFeatureUpdate(status='in_progress'))
```

## Migration from Hardcoded
All hardcoded session data from PlansPanel.tsx has been migrated to the database
using `scripts/migrate_plans_panel_data.py`. The component now fetches all data
dynamically from the API.

## Future Enhancements
- Filtering UI (by status, priority, tags)
- Search functionality
- Drag-and-drop reordering
- Export to CSV/JSON
- GitHub issue auto-sync
- Email notifications
- Mobile-responsive design improvements
```

---

## Success Criteria

- ✅ TypeScript API client implemented with full type safety
- ✅ PlansPanel.tsx refactored to use TanStack Query
- ✅ All hardcoded data removed from component
- ✅ Real-time updates working (30-second polling)
- ✅ Statistics dashboard displays live counts
- ✅ Loading and error states handled gracefully
- ✅ Tags, priority badges, and GitHub links display correctly
- ✅ Frontend recovers automatically on backend reconnection
- ✅ Documentation complete with usage examples
- ✅ Manual testing checklist completed

---

## Files Expected to Change

**Created (2):**
- `app/client/src/api/plannedFeaturesClient.ts` (~150 lines)
- `docs/features/plans-panel.md` (~200 lines)

**Modified (1):**
- `app/client/src/components/PlansPanel.tsx` (refactor to use API)

---

## Quick Reference

**Start services:**
```bash
# Backend
cd app/server && .venv/bin/python3 main.py

# Frontend
cd app/client && bun run dev
```

**Test API:**
```bash
curl http://localhost:8000/api/planned-features
curl http://localhost:8000/api/planned-features/stats
```

**Navigate to Panel 5:**
http://localhost:5173 → Panel 5 (Plans)

---

## Estimated Time

**Total: 2 hours**

- Step 1 (API Client): 30 min
- Step 2 (Component Refactor): 90 min
- Step 3 (Testing): 20 min
- Step 4 (Documentation): 10 min

---

## Session Completion Template

When done, provide summary in this format:

```markdown
## ✅ Session 8B Complete - Plans Panel Frontend

**Duration:** ~X hours
**Status:** Complete ✅
**Next:** Ready for Session 9 (Cost Attribution Analytics)

### What Was Done
- Created TypeScript API client (plannedFeaturesClient.ts)
- Refactored PlansPanel.tsx to use TanStack Query
- Removed all hardcoded data (~528 lines → dynamic)
- Implemented statistics dashboard with real-time updates
- Added loading/error states and auto-recovery
- Documentation with usage examples

### Key Results
- Frontend now 100% database-driven
- Real-time updates every 30 seconds
- Statistics dashboard operational
- X sessions displayed dynamically
- Clean separation of concerns

### Files Changed
**Created (2):**
- app/client/src/api/plannedFeaturesClient.ts
- docs/features/plans-panel.md

**Modified (1):**
- app/client/src/components/PlansPanel.tsx

### Test Results
Manual testing completed:
- ✅ Statistics dashboard displays correctly
- ✅ All sessions render from database
- ✅ Real-time updates working
- ✅ Error recovery functional
- ✅ Tags and badges display correctly

### Next Session
Session 9: Cost Attribution Analytics (3-4 hours)
- Break down costs by phase, workflow type, time period
- CLI tool for cost analysis
- Identify optimization opportunities
```

---

## Notes

**Session 8 Complete After 8B:**
- Backend (8A): Database, service, API ✅
- Frontend (8B): TypeScript client, component refactor ✅
- Full stack database-driven planning system operational
- Ready to track Sessions 9-14 programmatically
