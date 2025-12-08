# Plans Panel - Database-Driven Planning System

## Overview
The Plans Panel (Panel 5) provides a database-driven system for tracking project planning,
session history, feature roadmap, and work items with full CRUD operations and API access.

## Architecture

### Backend
- **Database:** `planned_features` table (PostgreSQL with SQLite fallback)
- **Service:** `PlannedFeaturesService` - Full CRUD with filtering
- **API:** 7 REST endpoints at `/api/planned-features/`
- **Models:** 3 Pydantic models for type safety and validation

### Frontend
- **Component:** `PlansPanel.tsx` - Dynamic rendering with TanStack Query
- **API Client:** `plannedFeaturesClient.ts` - TypeScript client with full type safety
- **Real-time Updates:** 30-second polling for live data
- **Statistics Dashboard:** Real-time counts by status/priority/type

## Features

### Data Display
- **In Progress:** Currently active sessions/features
- **Planned:** Future work items with estimates
- **Recently Completed:** Last 15 completed items with dates and notes
- **Statistics Dashboard:** Live counts and metrics

### Item Properties
- **Title & Description:** Main content
- **Status:** `planned`, `in_progress`, `completed`, `cancelled`
- **Priority:** `high`, `medium`, `low` with color-coded badges
- **Time Tracking:** Estimated hours and actual hours
- **Tags:** JSONB array for categorization
- **GitHub Integration:** Issue number links
- **Relationships:** Parent/child for subtasks
- **Completion Notes:** Detailed notes with bullet point support

### Real-time Updates
- Automatic polling every 30 seconds for feature data
- Statistics refresh every 60 seconds
- Seamless data synchronization
- Error recovery on backend reconnection

## Usage

### Web UI
Navigate to Panel 5 (Plans Panel) to view planned work items. The panel displays:

1. **Statistics Dashboard** at the top showing:
   - Total items count
   - In progress count (blue)
   - Planned count (purple)
   - Completed count (green)

2. **In Progress Section** showing currently active work

3. **Planned Section** showing future work with estimates

4. **Recently Completed Section** showing last 15 completed items

### API Access

**Get all features:**
```bash
curl http://localhost:8000/api/planned-features/
```

**Filter by status:**
```bash
curl 'http://localhost:8000/api/planned-features/?status=in_progress'
curl 'http://localhost:8000/api/planned-features/?status=planned'
curl 'http://localhost:8000/api/planned-features/?status=completed'
```

**Get statistics:**
```bash
curl http://localhost:8000/api/planned-features/stats
```

**Get recent completions:**
```bash
curl 'http://localhost:8000/api/planned-features/recent-completions?days=30'
```

**Get specific feature:**
```bash
curl http://localhost:8000/api/planned-features/1
```

**Create new feature:**
```bash
curl -X POST http://localhost:8000/api/planned-features/ \
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

**Complete a feature:**
```bash
curl -X PATCH http://localhost:8000/api/planned-features/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "actual_hours": 3.5,
    "completion_notes": "Successfully implemented and tested"
  }'
```

**Delete a feature:**
```bash
curl -X DELETE http://localhost:8000/api/planned-features/1
```

### Programmatic Access (Python)

```python
from app.server.services.planned_features_service import PlannedFeaturesService
from app.server.models.workflow import PlannedFeatureCreate, PlannedFeatureUpdate

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
service.update(feature.id, PlannedFeatureUpdate(status='in_progress'))

# Complete feature
service.update(feature.id, PlannedFeatureUpdate(
    status='completed',
    actual_hours=4.5,
    completion_notes='Successfully implemented'
))

# Get statistics
stats = service.get_statistics()
print(f"Completion rate: {stats.completion_rate:.1f}%")
```

### Frontend Integration (TypeScript)

```typescript
import { useQuery } from '@tanstack/react-query';
import { plannedFeaturesClient } from '../api/plannedFeaturesClient';

function MyComponent() {
  // Fetch all features
  const { data: features, isLoading, error } = useQuery({
    queryKey: ['planned-features'],
    queryFn: () => plannedFeaturesClient.getAll({ limit: 100 }),
    refetchInterval: 30000,
  });

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['planned-features-stats'],
    queryFn: () => plannedFeaturesClient.getStats(),
  });

  return (
    <div>
      <h2>Total: {stats?.by_status.planned || 0} planned items</h2>
      {features?.map(f => <div key={f.id}>{f.title}</div>)}
    </div>
  );
}
```

## Migration from Hardcoded

All hardcoded session data from PlansPanel.tsx has been migrated to the database
using `scripts/migrate_plans_panel_data.py`. The migration script:

1. Parsed 15 sessions from hardcoded JSX
2. Created database records with proper relationships
3. Set status based on completion state
4. Assigned priority and estimated hours
5. Added tags for categorization

The component now fetches all data dynamically from the API.

## Database Schema

```sql
CREATE TABLE planned_features (
    id SERIAL PRIMARY KEY,
    item_type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'planned',
    priority VARCHAR(20),
    estimated_hours NUMERIC(5,2),
    actual_hours NUMERIC(5,2),
    session_number INTEGER,
    github_issue_number INTEGER,
    parent_id INTEGER REFERENCES planned_features(id),
    tags JSONB DEFAULT '[]',
    completion_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### Indexes
- `idx_planned_features_status` - Fast filtering by status
- `idx_planned_features_type` - Fast filtering by item type
- `idx_planned_features_priority` - Fast filtering by priority
- `idx_planned_features_session` - Fast lookup by session number
- `idx_planned_features_github` - Fast lookup by GitHub issue
- `idx_planned_features_parent` - Fast subtask queries
- `idx_planned_features_tags` - GIN index for tag searches
- `idx_planned_features_completed` - Fast recent completions query
- `idx_planned_features_created` - Fast chronological queries

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/planned-features/` | List all features (with optional filters) |
| GET | `/api/planned-features/{id}` | Get single feature by ID |
| GET | `/api/planned-features/stats` | Get statistics (counts, totals, completion rate) |
| GET | `/api/planned-features/recent-completions` | Get recently completed features |
| POST | `/api/planned-features/` | Create new feature |
| PATCH | `/api/planned-features/{id}` | Update existing feature |
| DELETE | `/api/planned-features/{id}` | Delete feature (soft delete) |

### Query Parameters

**List endpoint** (`GET /api/planned-features/`):
- `status` - Filter by status (planned, in_progress, completed, cancelled)
- `item_type` - Filter by type (session, feature, bug, enhancement)
- `priority` - Filter by priority (high, medium, low)
- `limit` - Limit number of results

**Recent completions** (`GET /api/planned-features/recent-completions`):
- `days` - Number of days to look back (default: 30)

## Statistics Response

```json
{
  "by_status": {
    "completed": 8,
    "in_progress": 1,
    "planned": 6
  },
  "by_priority": {
    "high": 8,
    "medium": 2,
    "low": 5
  },
  "by_type": {
    "session": 15
  },
  "total_estimated_hours": 49.0,
  "total_actual_hours": 0.0,
  "completion_rate": 53.33
}
```

## Future Enhancements

### Planned Features (Not Yet Implemented)
- Filtering UI (by status, priority, tags)
- Search functionality across title/description
- Drag-and-drop reordering
- Export to CSV/JSON
- GitHub issue auto-sync
- Email notifications on status changes
- Mobile-responsive design improvements
- Gantt chart view for timeline visualization
- Time tracking integration
- Bulk operations (update multiple items)

## Testing

### Backend Tests
```bash
cd app/server
.venv/bin/pytest tests/services/test_planned_features_service.py -v
```

**Test Coverage:**
- 12/12 tests passing
- CRUD operations
- Filtering and statistics
- Date handling and sorting
- Tag management

### Manual Testing Checklist

1. **API Testing:**
   ```bash
   # Test stats
   curl http://localhost:8000/api/planned-features/stats

   # Test filtering
   curl 'http://localhost:8000/api/planned-features/?status=in_progress'

   # Test creation
   curl -X POST http://localhost:8000/api/planned-features/ \
     -H "Content-Type: application/json" \
     -d '{"item_type":"feature","title":"Test","status":"planned"}'
   ```

2. **Frontend Testing:**
   - Navigate to Panel 5 at http://localhost:5173
   - Verify statistics dashboard displays correctly
   - Confirm sessions appear in correct sections
   - Check real-time updates (wait 30 seconds)
   - Verify tags and badges display correctly
   - Test error recovery (stop backend, restart)

3. **Data Verification:**
   ```bash
   # PostgreSQL
   PGPASSWORD=changeme psql -h localhost -U tac_user -d tac_webbuilder \
     -c "SELECT status, COUNT(*) FROM planned_features GROUP BY status;"
   ```

## Troubleshooting

### Panel shows "Loading plans..." indefinitely
- Check backend is running: `curl http://localhost:8000/api/planned-features/stats`
- Check browser console for errors
- Verify API_BASE is set correctly in frontend config

### API returns 307 redirect
- Ensure URL has trailing slash: `/api/planned-features/` not `/api/planned-features`
- Frontend client handles this automatically

### Statistics not updating
- Statistics refresh every 60 seconds (slower than feature data)
- Hard refresh page to force immediate update
- Check backend logs for errors

### Tags not displaying
- Verify tags are stored as JSON array in database
- Check that frontend properly maps `feature.tags`
- Ensure tags column is JSONB type (PostgreSQL) or TEXT (SQLite)

## Performance Considerations

- **Polling:** 30-second interval balances freshness vs. load
- **Caching:** TanStack Query caches responses automatically
- **Indexes:** All filter columns indexed for fast queries
- **Limits:** Default limit of 200 items prevents large payloads
- **Statistics:** Computed on-demand (could be cached for high traffic)

## Security

- **Read-only UI:** Frontend displays data but doesn't allow modifications
- **API Protection:** Backend validates all inputs with Pydantic
- **SQL Injection:** Parameterized queries prevent injection
- **XSS Prevention:** React automatically escapes user content
- **CORS:** Configured for same-origin or trusted domains only

## Related Documentation

- [Observability & Logging](./observability-and-logging.md) - Pattern detection and work logs
- [Database Schema](../database/schema.md) - Full database documentation
- [API Reference](../api/README.md) - All API endpoints
- [Frontend Architecture](../frontend/README.md) - Component structure
