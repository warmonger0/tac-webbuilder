# Planned Features & Roadmap Tracking Quick Reference

## Overview (Session 8A/8B)
**Database-driven roadmap tracking system with Panel 5 integration**

- **Session 8A:** Backend infrastructure (API, service, repository, database)
- **Session 8B:** Frontend Panel 5 (PlansPanel.tsx, database-driven UI)

**Purpose:**
- Track development sessions and features
- Manage roadmap progress
- Estimate and measure actual hours
- Track dependencies between features
- Replace hardcoded PlansPanel with dynamic database-driven system

## Architecture

### Backend (Session 8A)

**Database Table:** `planned_features`
```sql
CREATE TABLE planned_features (
    id SERIAL PRIMARY KEY,
    session_number INTEGER UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending',  -- pending, in_progress, completed, cancelled
    estimated_hours REAL,
    actual_hours REAL,
    priority INTEGER DEFAULT 3,  -- 1 (highest) to 5 (lowest)
    dependencies TEXT,  -- JSON array of session numbers
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

**API Endpoints:** `/api/v1/planned-features`
- `POST /` - Create new feature
- `GET /` - List all features (with optional status filter)
- `GET /{id}` - Get feature by ID
- `GET /session/{session_number}` - Get by session number
- `PUT /{id}` - Update feature (status, hours, etc.)
- `DELETE /{id}` - Delete feature
- `POST /{id}/generate-plan` - Generate AI implementation plan (NEW - Session 21)
- `POST /{id}/start-automation` - Start automated workflow execution

**Service Layer:** `services/planned_features_service.py`
- `create(feature_data)` - Create new planned feature
- `get_all(status_filter=None)` - Get all features, optionally filtered
- `get_by_id(feature_id)` - Get single feature
- `get_by_session(session_number)` - Get feature by session number
- `update(feature_id, update_data)` - Update feature fields
- `delete(feature_id)` - Delete feature

**Repository:** `repositories/planned_features_repository.py`
- Database access layer
- PostgreSQL-specific queries
- JSON handling for dependencies array

### Frontend (Session 8B)

**Component:** `app/client/src/components/PlansPanel.tsx`

**Features:**
- **Session List:** Display all planned features grouped by status
- **Status Tracking:** Pending, In Progress, Completed, Cancelled
- **Edit Mode:** Inline editing of title, description, hours, priority
- **Add New:** Create new session features dynamically
- **Delete:** Remove features with confirmation
- **Real-time Updates:** TanStack Query for cache invalidation
- **Progress Indicators:** Show estimated vs actual hours
- **Dependency Tracking:** Visual display of session dependencies

**API Client:** `app/client/src/api/plannedFeatures.ts`
- `fetchPlannedFeatures()` - Get all features
- `createPlannedFeature(data)` - Create new
- `updatePlannedFeature(id, data)` - Update existing
- `deletePlannedFeature(id)` - Delete feature

## Common Use Cases

### Create New Planned Feature

**API Request:**
```json
POST /api/v1/planned-features
{
  "session_number": 15,
  "title": "Implement WebSocket reconnection logic",
  "description": "Add automatic reconnection with exponential backoff",
  "status": "pending",
  "estimated_hours": 4.0,
  "priority": 2,
  "dependencies": [8, 10]
}
```

**Response:**
```json
{
  "id": 15,
  "session_number": 15,
  "title": "Implement WebSocket reconnection logic",
  "description": "Add automatic reconnection with exponential backoff",
  "status": "pending",
  "estimated_hours": 4.0,
  "actual_hours": null,
  "priority": 2,
  "dependencies": [8, 10],
  "created_at": "2025-12-08T10:30:00Z",
  "started_at": null,
  "completed_at": null
}
```

### Update Feature Status (Mark as In Progress)

**API Request:**
```json
PUT /api/v1/planned-features/15
{
  "status": "in_progress",
  "started_at": "2025-12-08T14:00:00Z"
}
```

### Mark Feature as Complete

**API Request:**
```json
PUT /api/v1/planned-features/15
{
  "status": "completed",
  "actual_hours": 5.5,
  "completed_at": "2025-12-08T19:30:00Z"
}
```

### Get All In-Progress Features

**API Request:**
```
GET /api/v1/planned-features?status=in_progress
```

**Response:**
```json
[
  {
    "id": 15,
    "session_number": 15,
    "title": "Implement WebSocket reconnection logic",
    "status": "in_progress",
    "estimated_hours": 4.0,
    "started_at": "2025-12-08T14:00:00Z"
  }
]
```

## Panel 5 UI Features

### Session Cards
Each planned feature displayed as a card with:
- Session number badge
- Title and description
- Status indicator (color-coded)
- Estimated hours vs actual hours
- Priority level
- Dependencies list
- Edit and delete buttons

### Status Groups
Features grouped into sections:
- **Pending** (blue) - Not started
- **In Progress** (yellow) - Currently working on
- **Completed** (green) - Finished
- **Cancelled** (gray) - Abandoned

### Edit Mode
Click edit button to:
- Modify title inline
- Update description
- Change status
- Adjust estimated/actual hours
- Update priority (1-5)
- Add/remove dependencies

### Add New Feature
Form to create new planned feature:
- Auto-increment session number suggestion
- Required: title, session_number
- Optional: description, estimated_hours, priority, dependencies

## Database Update Commands (Python)

### Mark Session as Complete
```python
from app.server.services.planned_features_service import PlannedFeaturesService
from app.server.models.workflow import PlannedFeatureUpdate

service = PlannedFeaturesService()
session = service.get_by_session(14)
service.update(session.id, PlannedFeatureUpdate(
    status='completed',
    actual_hours=3.5,
    completed_at='2025-12-08T12:00:00Z'
))
```

### Create New Session
```python
from app.server.services.planned_features_service import PlannedFeaturesService

service = PlannedFeaturesService()
service.create({
    'session_number': 15,
    'title': 'New Feature Implementation',
    'description': 'Detailed description',
    'estimated_hours': 6.0,
    'priority': 2,
    'dependencies': [8, 10, 12]
})
```

## Testing

**Backend Tests:** `app/server/tests/services/test_planned_features_service.py`
- CRUD operations
- Status transitions
- Dependency validation
- Edge cases

**Frontend Tests:** `app/client/src/components/__tests__/PlansPanel.test.tsx`
- Component rendering
- Edit mode toggling
- API integration
- User interactions

## Migration from Hardcoded to Database-Driven

**Before (Session 8A):** PlansPanel.tsx had hardcoded session data
```tsx
const recentlyCompleted = [
  { session: 6, title: "Hardcoded title", hours: 3 }
];
```

**After (Session 8B):** PlansPanel.tsx fetches from database
```tsx
const { data: features } = useQuery({
  queryKey: ['plannedFeatures'],
  queryFn: fetchPlannedFeatures
});
```

**Migration Steps:**
1. Created `planned_features` table (Session 8A)
2. Created API endpoints (Session 8A)
3. Refactored PlansPanel to use API (Session 8B)
4. Removed hardcoded data (Session 8B)
5. Added edit/delete functionality (Session 8B)

## AI-Generated Implementation Plans (Session 21)

**Feature:** Generate full markdown implementation prompts for planned features

### Generate Plan Endpoint

**Request:**
```
POST /api/v1/planned-features/{id}/generate-plan
```

**Response:**
```json
{
  "feature_id": 123,
  "feature_title": "Add real-time notifications",
  "total_phases": 3,
  "total_estimated_hours": 8.5,
  "phases": [
    {
      "phase_number": 1,
      "total_phases": 3,
      "title": "Backend notification infrastructure",
      "description": "Create notification service and database schema",
      "estimated_hours": 3.0,
      "files_to_modify": ["app/server/services/notification_service.py", "..."],
      "depends_on": [],
      "prompt_filename": "phase_1_backend_infrastructure.md",
      "markdown_prompt": "# Phase 1/3: Backend Infrastructure\n\n..."
    }
  ]
}
```

### Plan Persistence

**Database Column:** `generated_plan` (JSONB)
- Plans are **automatically saved** to database when generated
- **No re-generation** needed on page refresh
- Loaded via WebSocket with planned features

**Frontend Integration:**
```tsx
// Plans are automatically loaded from feature.generated_plan
useEffect(() => {
  features.forEach(feature => {
    if (feature.generated_plan) {
      setGeneratedPlans(prev => new Map(prev).set(feature.id, feature.generated_plan));
    }
  });
}, [features]);
```

### UI Features

**Generate Plan Button:**
- Click "📋 Generate Plan" on any planned/in-progress feature
- AI analyzes feature and generates phase breakdown
- Full markdown prompts ready to copy into Panel 1
- Plan is **persisted to database** automatically

**Plan Display:**
- Collapsible section showing all phases
- Each phase includes:
  - Phase number and title
  - Description and estimated hours
  - Files to modify
  - Full markdown prompt (copy-ready)
  - "Copy Full Prompt" button for easy workflow execution

**Workflow:**
1. User clicks "Generate Plan" → AI creates phase breakdown
2. Plan saved to `planned_features.generated_plan` (JSONB)
3. User copies markdown prompt for each phase
4. Paste into Panel 1 to execute workflow
5. Plan persists across page refreshes (no re-generation needed)

## When to Load Full Documentation

**Load full docs when:**
- Implementing roadmap features
- Adding new fields to planned_features
- Customizing Panel 5 UI
- Understanding session dependency logic
- Troubleshooting roadmap tracking
- Working with AI-generated implementation plans

**Full Documentation:**
- Session 8A prompt: `archives/prompts/2025/SESSION_8A_PROMPT.md` (backend)
- Session 8B prompt: `archives/prompts/2025/SESSION_8B_PROMPT.md` (frontend)
- Feature doc: `docs/features/planned-features-system.md`
