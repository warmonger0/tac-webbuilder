# Task: Plans Panel Database Migration - Backend (Session 8A)

## Context
I'm working on the tac-webbuilder project. The Plans Panel (Panel 5 - PlansPanel.tsx) currently contains hardcoded session history and planned work items directly in the component JSX. This session (8A) implements the backend infrastructure: database tables, service layer, API endpoints, and data migration from hardcoded TSX to database.

## Objective
Create the backend foundation for a database-driven planning system: database schema, Pydantic models, service layer with CRUD operations, REST API endpoints, and migrate existing hardcoded data to database.

## Background Information
- **Current State:** PlansPanel.tsx contains ~528 lines of hardcoded JSX
- **Session 8A Scope:** Backend only (database, service, API)
- **Session 8B Scope:** Frontend (TypeScript client, component refactor)
- **Benefits:** Programmatic access, historical tracking, filtering, metrics

---

## Implementation Steps

### Step 1: Database Migration (45 min)

**Create:** `app/server/db/migrations/017_add_planned_features.sql`

**Template:** See `.claude/templates/DATABASE_MIGRATION.md`

**Table: planned_features**
```sql
CREATE TABLE IF NOT EXISTS planned_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT NOT NULL CHECK(item_type IN ('session', 'feature', 'bug', 'enhancement')),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK(status IN ('planned', 'in_progress', 'completed', 'cancelled')),
    priority TEXT CHECK(priority IN ('high', 'medium', 'low')),
    estimated_hours REAL,
    actual_hours REAL,
    session_number INTEGER,
    github_issue_number INTEGER,
    parent_id INTEGER,
    tags TEXT,  -- JSON array
    completion_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES planned_features(id)
);

-- Indexes
CREATE INDEX idx_planned_features_status ON planned_features(status);
CREATE INDEX idx_planned_features_priority ON planned_features(priority);
CREATE INDEX idx_planned_features_type ON planned_features(item_type);
CREATE INDEX idx_planned_features_session ON planned_features(session_number);
CREATE INDEX idx_planned_features_github ON planned_features(github_issue_number);
CREATE INDEX idx_planned_features_completed ON planned_features(completed_at);

-- Trigger for updated_at
CREATE TRIGGER update_planned_features_timestamp
AFTER UPDATE ON planned_features
BEGIN
    UPDATE planned_features
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
```

**PostgreSQL version:**

**Create:** `app/server/db/migrations/017_add_planned_features_postgres.sql`

```sql
CREATE TABLE IF NOT EXISTS planned_features (
    id SERIAL PRIMARY KEY,
    item_type TEXT NOT NULL CHECK(item_type IN ('session', 'feature', 'bug', 'enhancement')),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK(status IN ('planned', 'in_progress', 'completed', 'cancelled')),
    priority TEXT CHECK(priority IN ('high', 'medium', 'low')),
    estimated_hours REAL,
    actual_hours REAL,
    session_number INTEGER,
    github_issue_number INTEGER,
    parent_id INTEGER,
    tags JSONB,  -- Use JSONB for PostgreSQL
    completion_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES planned_features(id)
);

-- Indexes (same as SQLite)
CREATE INDEX idx_planned_features_status ON planned_features(status);
CREATE INDEX idx_planned_features_priority ON planned_features(priority);
CREATE INDEX idx_planned_features_type ON planned_features(item_type);
CREATE INDEX idx_planned_features_session ON planned_features(session_number);
CREATE INDEX idx_planned_features_github ON planned_features(github_issue_number);
CREATE INDEX idx_planned_features_completed ON planned_features(completed_at);

-- Trigger for updated_at (PostgreSQL syntax)
CREATE OR REPLACE FUNCTION update_planned_features_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_planned_features_timestamp
BEFORE UPDATE ON planned_features
FOR EACH ROW
EXECUTE FUNCTION update_planned_features_timestamp();
```

**Run migrations:**
```bash
# SQLite
sqlite3 app/server/db/workflow_history.db < app/server/db/migrations/017_add_planned_features.sql

# PostgreSQL
PGPASSWORD=changeme psql -h localhost -p 5432 -U tac_user -d tac_webbuilder \
    -f app/server/db/migrations/017_add_planned_features_postgres.sql
```

---

### Step 2: Pydantic Models (30 min)

**Modify:** `app/server/models/workflow.py`

**Add models:**
```python
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class PlannedFeature(BaseModel):
    """Planned feature or session model."""
    id: Optional[int] = None
    item_type: str  # 'session', 'feature', 'bug', 'enhancement'
    title: str
    description: Optional[str] = None
    status: str  # 'planned', 'in_progress', 'completed', 'cancelled'
    priority: Optional[str] = None  # 'high', 'medium', 'low'
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    session_number: Optional[int] = None
    github_issue_number: Optional[int] = None
    parent_id: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    completion_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PlannedFeatureCreate(BaseModel):
    """Model for creating a new planned feature."""
    item_type: str
    title: str
    description: Optional[str] = None
    status: str = 'planned'
    priority: Optional[str] = None
    estimated_hours: Optional[float] = None
    session_number: Optional[int] = None
    github_issue_number: Optional[int] = None
    parent_id: Optional[int] = None
    tags: List[str] = Field(default_factory=list)

class PlannedFeatureUpdate(BaseModel):
    """Model for updating a planned feature."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    github_issue_number: Optional[int] = None
    tags: Optional[List[str]] = None
    completion_notes: Optional[str] = None
```

---

### Step 3: Service Layer (60 min)

**Create:** `app/server/services/planned_features_service.py` (~300 lines)

**Template:** See `.claude/templates/SERVICE_LAYER.md`

**Key Methods:**
```python
import json
from typing import Optional, List, Dict, Any
from app.server.models.workflow import PlannedFeature, PlannedFeatureCreate, PlannedFeatureUpdate
from app.server.db.connection import get_connection

class PlannedFeaturesService:
    """Service for managing planned features and sessions."""

    def get_all(
        self,
        status: Optional[str] = None,
        item_type: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100
    ) -> List[PlannedFeature]:
        """Get all planned features with optional filtering."""
        with get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM planned_features WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)
            if item_type:
                query += " AND item_type = ?"
                params.append(item_type)
            if priority:
                query += " AND priority = ?"
                params.append(priority)

            query += " ORDER BY CASE status "
            query += "   WHEN 'in_progress' THEN 1 "
            query += "   WHEN 'planned' THEN 2 "
            query += "   WHEN 'completed' THEN 3 "
            query += "   WHEN 'cancelled' THEN 4 END, "
            query += " priority DESC, created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_model(row) for row in rows]

    def get_by_id(self, feature_id: int) -> Optional[PlannedFeature]:
        """Get single planned feature by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM planned_features WHERE id = ?", (feature_id,))
            row = cursor.fetchone()

            return self._row_to_model(row) if row else None

    def get_by_session(self, session_number: int) -> Optional[PlannedFeature]:
        """Get planned feature by session number."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM planned_features WHERE session_number = ?",
                (session_number,)
            )
            row = cursor.fetchone()

            return self._row_to_model(row) if row else None

    def create(self, feature_data: PlannedFeatureCreate) -> PlannedFeature:
        """Create new planned feature."""
        tags_json = json.dumps(feature_data.tags)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO planned_features
                    (item_type, title, description, status, priority,
                     estimated_hours, session_number, github_issue_number,
                     parent_id, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feature_data.item_type,
                feature_data.title,
                feature_data.description,
                feature_data.status,
                feature_data.priority,
                feature_data.estimated_hours,
                feature_data.session_number,
                feature_data.github_issue_number,
                feature_data.parent_id,
                tags_json
            ))
            conn.commit()
            feature_id = cursor.lastrowid

        return self.get_by_id(feature_id)

    def update(self, feature_id: int, update_data: PlannedFeatureUpdate) -> PlannedFeature:
        """Update existing planned feature."""
        # Get existing feature
        existing = self.get_by_id(feature_id)
        if not existing:
            raise ValueError(f"Feature {feature_id} not found")

        # Build dynamic SET clause
        set_clauses = []
        params = []

        if update_data.title is not None:
            set_clauses.append("title = ?")
            params.append(update_data.title)
        if update_data.description is not None:
            set_clauses.append("description = ?")
            params.append(update_data.description)
        if update_data.status is not None:
            set_clauses.append("status = ?")
            params.append(update_data.status)

            # Auto-set timestamps on status change
            if update_data.status == 'in_progress' and not existing.started_at:
                set_clauses.append("started_at = CURRENT_TIMESTAMP")
            elif update_data.status == 'completed' and not existing.completed_at:
                set_clauses.append("completed_at = CURRENT_TIMESTAMP")

        if update_data.priority is not None:
            set_clauses.append("priority = ?")
            params.append(update_data.priority)
        if update_data.estimated_hours is not None:
            set_clauses.append("estimated_hours = ?")
            params.append(update_data.estimated_hours)
        if update_data.actual_hours is not None:
            set_clauses.append("actual_hours = ?")
            params.append(update_data.actual_hours)
        if update_data.github_issue_number is not None:
            set_clauses.append("github_issue_number = ?")
            params.append(update_data.github_issue_number)
        if update_data.tags is not None:
            set_clauses.append("tags = ?")
            params.append(json.dumps(update_data.tags))
        if update_data.completion_notes is not None:
            set_clauses.append("completion_notes = ?")
            params.append(update_data.completion_notes)

        if not set_clauses:
            return existing  # No changes

        params.append(feature_id)
        query = f"UPDATE planned_features SET {', '.join(set_clauses)} WHERE id = ?"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

        return self.get_by_id(feature_id)

    def delete(self, feature_id: int) -> bool:
        """Delete planned feature (soft delete via status='cancelled')."""
        update_data = PlannedFeatureUpdate(status='cancelled')
        self.update(feature_id, update_data)
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about planned features."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Counts by status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM planned_features
                GROUP BY status
            """)
            by_status = dict(cursor.fetchall())

            # Counts by priority
            cursor.execute("""
                SELECT priority, COUNT(*) as count
                FROM planned_features
                WHERE priority IS NOT NULL
                GROUP BY priority
            """)
            by_priority = dict(cursor.fetchall())

            # Counts by type
            cursor.execute("""
                SELECT item_type, COUNT(*) as count
                FROM planned_features
                GROUP BY item_type
            """)
            by_type = dict(cursor.fetchall())

            # Hours summary
            cursor.execute("""
                SELECT
                    SUM(estimated_hours) as total_estimated,
                    SUM(actual_hours) as total_actual
                FROM planned_features
            """)
            hours = cursor.fetchone()

            # Completion rate
            cursor.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'completed') * 100.0 / COUNT(*) as completion_rate
                FROM planned_features
                WHERE status IN ('completed', 'cancelled')
            """)
            completion = cursor.fetchone()

            return {
                'by_status': by_status,
                'by_priority': by_priority,
                'by_type': by_type,
                'total_estimated_hours': hours[0] or 0,
                'total_actual_hours': hours[1] or 0,
                'completion_rate': completion[0] if completion else 0
            }

    def get_recent_completions(self, days: int = 30) -> List[PlannedFeature]:
        """Get recently completed features."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM planned_features
                WHERE status = 'completed'
                  AND completed_at >= datetime('now', '-' || ? || ' days')
                ORDER BY completed_at DESC
            """, (days,))
            rows = cursor.fetchall()

            return [self._row_to_model(row) for row in rows]

    def _row_to_model(self, row) -> PlannedFeature:
        """Convert database row to Pydantic model."""
        data = dict(row)

        # Parse JSON tags
        if data.get('tags'):
            try:
                data['tags'] = json.loads(data['tags'])
            except (json.JSONDecodeError, TypeError):
                data['tags'] = []
        else:
            data['tags'] = []

        return PlannedFeature(**data)
```

**Reference:**
- `app/server/services/workflow_service.py` for database patterns
- `app/server/services/pattern_review_service.py` for similar CRUD

---

### Step 4: API Routes (60 min)

**Create:** `app/server/routes/planned_features_routes.py` (~250 lines)

**Endpoints:**
```python
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.server.services.planned_features_service import PlannedFeaturesService
from app.server.models.workflow import PlannedFeature, PlannedFeatureCreate, PlannedFeatureUpdate

router = APIRouter(prefix="/api/planned-features", tags=["planned-features"])

@router.get("/", response_model=List[PlannedFeature])
async def get_planned_features(
    status: Optional[str] = Query(None, description="Filter by status"),
    item_type: Optional[str] = Query(None, description="Filter by type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(100, description="Max results")
):
    """Get all planned features with optional filtering."""
    service = PlannedFeaturesService()
    return service.get_all(status=status, item_type=item_type, priority=priority, limit=limit)

@router.get("/stats")
async def get_statistics():
    """Get statistics about planned features."""
    service = PlannedFeaturesService()
    return service.get_statistics()

@router.get("/recent-completions")
async def get_recent_completions(
    days: int = Query(30, description="Number of days to look back")
):
    """Get recently completed features."""
    service = PlannedFeaturesService()
    return service.get_recent_completions(days=days)

@router.get("/{feature_id}", response_model=PlannedFeature)
async def get_planned_feature(feature_id: int):
    """Get single planned feature by ID."""
    service = PlannedFeaturesService()
    feature = service.get_by_id(feature_id)

    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    return feature

@router.post("/", response_model=PlannedFeature, status_code=201)
async def create_planned_feature(feature_data: PlannedFeatureCreate):
    """Create new planned feature."""
    service = PlannedFeaturesService()
    return service.create(feature_data)

@router.patch("/{feature_id}", response_model=PlannedFeature)
async def update_planned_feature(
    feature_id: int,
    update_data: PlannedFeatureUpdate
):
    """Update existing planned feature."""
    service = PlannedFeaturesService()

    # Verify feature exists
    existing = service.get_by_id(feature_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Feature not found")

    return service.update(feature_id, update_data)

@router.delete("/{feature_id}", status_code=204)
async def delete_planned_feature(feature_id: int):
    """Delete planned feature (soft delete)."""
    service = PlannedFeaturesService()

    # Verify feature exists
    existing = service.get_by_id(feature_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Feature not found")

    service.delete(feature_id)
    return None
```

**Register routes in `app/server/main.py`:**
```python
from app.server.routes.planned_features_routes import router as planned_features_router

app.include_router(planned_features_router)
```

---

### Step 5: Data Migration Script (45 min)

**Create:** `scripts/migrate_plans_panel_data.py` (~200 lines)

**Extract Sessions 1-7 from PlansPanel.tsx and populate database:**
```python
#!/usr/bin/env python3
"""
Migrate Plans Panel Data to Database

Extracts hardcoded sessions from PlansPanel.tsx and populates
the planned_features table.

Usage:
    python scripts/migrate_plans_panel_data.py --dry-run
    python scripts/migrate_plans_panel_data.py
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.server.services.planned_features_service import PlannedFeaturesService
from app.server.models.workflow import PlannedFeatureCreate

class PlansPanelMigrator:
    """Migrate hardcoded plans panel data to database."""

    def __init__(self, dry_run=False):
        self.service = PlannedFeaturesService()
        self.dry_run = dry_run

    def migrate_completed_sessions(self):
        """Migrate completed sessions 1-7 to database."""
        sessions = [
            {
                'item_type': 'session',
                'session_number': 7,
                'title': 'Session 7: Daily Pattern Analysis System',
                'status': 'completed',
                'priority': 'high',
                'estimated_hours': 3.0,
                'actual_hours': 3.0,
                'tags': ['observability', 'automation', 'pattern-analysis'],
                'completion_notes': '13/13 tests passing, PostgreSQL compatible'
            },
            {
                'item_type': 'session',
                'session_number': 6,
                'title': 'Session 6: Pattern Review System (CLI + Web UI)',
                'status': 'completed',
                'priority': 'high',
                'estimated_hours': 4.0,
                'actual_hours': 4.0,
                'tags': ['observability', 'cli', 'web-ui', 'panel-8'],
                'completion_notes': 'CLI + Web UI + 6 API endpoints'
            },
            {
                'item_type': 'session',
                'session_number': 5,
                'title': 'Session 5: Verify Phase Implementation',
                'status': 'completed',
                'priority': 'high',
                'estimated_hours': 2.0,
                'actual_hours': 2.0,
                'tags': ['adw', 'verification', 'phase-10'],
                'completion_notes': '23/23 tests passing, 10-phase SDLC complete'
            },
            {
                'item_type': 'session',
                'session_number': 4,
                'title': 'Session 4: Integration Checklist Validation',
                'status': 'completed',
                'priority': 'high',
                'estimated_hours': 3.5,
                'actual_hours': 3.5,
                'tags': ['adw', 'ship-phase', 'validation'],
                'completion_notes': '28/28 tests passing, 90% bug reduction'
            },
            {
                'item_type': 'session',
                'session_number': 3,
                'title': 'Session 3: Integration Checklist Generation',
                'status': 'completed',
                'priority': 'high',
                'estimated_hours': 3.0,
                'actual_hours': 3.0,
                'tags': ['adw', 'plan-phase', 'checklist'],
                'completion_notes': '10/10 tests passing, smart feature detection'
            },
            {
                'item_type': 'session',
                'session_number': 2,
                'title': 'Session 2: Port Pool Implementation',
                'status': 'completed',
                'priority': 'high',
                'estimated_hours': 3.0,
                'actual_hours': 3.0,
                'tags': ['infrastructure', 'port-management'],
                'completion_notes': '13/13 tests passing, 100-slot capacity'
            },
            {
                'item_type': 'session',
                'session_number': 1.5,
                'title': 'Session 1.5: Pattern Detection System Cleanup',
                'status': 'completed',
                'priority': 'high',
                'estimated_hours': 3.0,
                'actual_hours': 3.0,
                'tags': ['observability', 'bug-fix', 'database'],
                'completion_notes': 'Fixed 87x duplication, analyzed 39K events'
            },
            {
                'item_type': 'session',
                'session_number': 1,
                'title': 'Session 1: Pattern Detection Audit',
                'status': 'completed',
                'priority': 'high',
                'estimated_hours': 2.0,
                'actual_hours': 2.0,
                'tags': ['observability', 'audit'],
                'completion_notes': 'Discovered pattern detection bug'
            }
        ]

        print("\nMigrating completed sessions...")
        for session_data in sessions:
            if self.dry_run:
                print(f"[DRY RUN] Would create: {session_data['title']}")
            else:
                try:
                    feature = PlannedFeatureCreate(**session_data)
                    created = self.service.create(feature)
                    print(f"✅ Created: {created.title} (ID: {created.id})")
                except Exception as e:
                    print(f"❌ Error creating {session_data['title']}: {e}")

    def migrate_planned_sessions(self):
        """Migrate planned sessions 8-14 to database."""
        sessions = [
            {
                'item_type': 'session',
                'session_number': 8,
                'title': 'Session 8: Plans Panel Database Migration',
                'status': 'in_progress',
                'priority': 'medium',
                'estimated_hours': 4.5,
                'tags': ['database', 'frontend', 'api']
            },
            {
                'item_type': 'session',
                'session_number': 9,
                'title': 'Session 9: Cost Attribution Analytics',
                'status': 'planned',
                'priority': 'medium',
                'estimated_hours': 3.5,
                'tags': ['analytics', 'cost-optimization']
            },
            {
                'item_type': 'session',
                'session_number': 10,
                'title': 'Session 10: Error Analytics',
                'status': 'planned',
                'priority': 'low',
                'estimated_hours': 3.5,
                'tags': ['analytics', 'error-tracking']
            },
            {
                'item_type': 'session',
                'session_number': 11,
                'title': 'Session 11: Latency Analytics',
                'status': 'planned',
                'priority': 'low',
                'estimated_hours': 3.5,
                'tags': ['analytics', 'performance']
            },
            {
                'item_type': 'session',
                'session_number': 12,
                'title': 'Session 12: Closed-Loop ROI Tracking',
                'status': 'planned',
                'priority': 'low',
                'estimated_hours': 4.5,
                'tags': ['observability', 'roi', 'automation']
            },
            {
                'item_type': 'session',
                'session_number': 13,
                'title': 'Session 13: Confidence Updating System',
                'status': 'planned',
                'priority': 'low',
                'estimated_hours': 3.5,
                'tags': ['observability', 'machine-learning']
            },
            {
                'item_type': 'session',
                'session_number': 14,
                'title': 'Session 14: Auto-Archiving System',
                'status': 'planned',
                'priority': 'low',
                'estimated_hours': 2.5,
                'tags': ['automation', 'maintenance']
            }
        ]

        print("\nMigrating planned sessions...")
        for session_data in sessions:
            if self.dry_run:
                print(f"[DRY RUN] Would create: {session_data['title']}")
            else:
                try:
                    feature = PlannedFeatureCreate(**session_data)
                    created = self.service.create(feature)
                    print(f"✅ Created: {created.title} (ID: {created.id})")
                except Exception as e:
                    print(f"❌ Error creating {session_data['title']}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Migrate Plans Panel data to database')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    args = parser.parse_args()

    migrator = PlansPanelMigrator(dry_run=args.dry_run)

    migrator.migrate_completed_sessions()
    migrator.migrate_planned_sessions()

    print("\n✅ Migration complete!")

if __name__ == '__main__':
    main()
```

---

### Step 6: Tests (60 min)

**Create:** `app/server/tests/services/test_planned_features_service.py` (~200 lines)

**Template:** See `.claude/templates/PYTEST_TESTS.md`

**Test Cases:**
```python
import pytest
import json
from app.server.services.planned_features_service import PlannedFeaturesService
from app.server.models.workflow import PlannedFeatureCreate, PlannedFeatureUpdate

@pytest.fixture
def service():
    """Create service instance."""
    return PlannedFeaturesService()

@pytest.fixture
def sample_feature_data():
    """Sample feature data for testing."""
    return {
        'item_type': 'session',
        'title': 'Test Session',
        'description': 'Test description',
        'status': 'planned',
        'priority': 'high',
        'estimated_hours': 3.0,
        'session_number': 99,
        'tags': ['test', 'session']
    }

def test_create_planned_feature(service, sample_feature_data):
    """Test creating a new planned feature."""
    feature_create = PlannedFeatureCreate(**sample_feature_data)
    feature = service.create(feature_create)

    assert feature.id is not None
    assert feature.title == sample_feature_data['title']
    assert feature.status == 'planned'
    assert feature.tags == ['test', 'session']
    assert feature.created_at is not None

def test_get_by_id(service, sample_feature_data):
    """Test fetching feature by ID."""
    feature_create = PlannedFeatureCreate(**sample_feature_data)
    created = service.create(feature_create)

    fetched = service.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == created.title

def test_get_all_filters(service, sample_feature_data):
    """Test filtering by status, type, priority."""
    # Create test features
    service.create(PlannedFeatureCreate(**sample_feature_data))

    # Filter by status
    planned = service.get_all(status='planned')
    assert len(planned) > 0
    assert all(f.status == 'planned' for f in planned)

    # Filter by type
    sessions = service.get_all(item_type='session')
    assert all(f.item_type == 'session' for f in sessions)

def test_update_feature(service, sample_feature_data):
    """Test updating feature fields."""
    feature_create = PlannedFeatureCreate(**sample_feature_data)
    created = service.create(feature_create)

    update = PlannedFeatureUpdate(
        title='Updated Title',
        actual_hours=2.5
    )
    updated = service.update(created.id, update)

    assert updated.title == 'Updated Title'
    assert updated.actual_hours == 2.5

def test_update_status_timestamps(service, sample_feature_data):
    """Test that timestamps are auto-set on status changes."""
    feature_create = PlannedFeatureCreate(**sample_feature_data)
    created = service.create(feature_create)

    # Change to in_progress
    update = PlannedFeatureUpdate(status='in_progress')
    updated = service.update(created.id, update)
    assert updated.started_at is not None

    # Change to completed
    update = PlannedFeatureUpdate(status='completed')
    completed = service.update(created.id, update)
    assert completed.completed_at is not None

def test_get_statistics(service, sample_feature_data):
    """Test statistics calculation."""
    service.create(PlannedFeatureCreate(**sample_feature_data))

    stats = service.get_statistics()

    assert 'by_status' in stats
    assert 'by_priority' in stats
    assert 'by_type' in stats
    assert 'total_estimated_hours' in stats

def test_json_tags_parsing(service, sample_feature_data):
    """Test tags JSON serialization and parsing."""
    feature_create = PlannedFeatureCreate(**sample_feature_data)
    created = service.create(feature_create)

    fetched = service.get_by_id(created.id)
    assert fetched.tags == ['test', 'session']
    assert isinstance(fetched.tags, list)
```

**Run tests:**
```bash
# SQLite
pytest app/server/tests/services/test_planned_features_service.py -v

# PostgreSQL
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql \
pytest app/server/tests/services/test_planned_features_service.py -v
```

---

## Success Criteria

- ✅ Migration creates planned_features table (SQLite + PostgreSQL)
- ✅ Pydantic models added to workflow.py
- ✅ Service layer implements all CRUD operations with filtering
- ✅ 7 REST API endpoints implemented
- ✅ Routes registered in main.py
- ✅ Data migration script populates database with sessions 1-7
- ✅ All tests passing (8/8)
- ✅ API endpoints testable via curl/Postman
- ✅ Backend ready for Session 8B (frontend integration)

---

## Files Expected to Change

**Created (6):**
- `app/server/db/migrations/017_add_planned_features.sql` (~60 lines)
- `app/server/db/migrations/017_add_planned_features_postgres.sql` (~70 lines)
- `app/server/services/planned_features_service.py` (~300 lines)
- `app/server/routes/planned_features_routes.py` (~250 lines)
- `app/server/tests/services/test_planned_features_service.py` (~200 lines)
- `scripts/migrate_plans_panel_data.py` (~200 lines)

**Modified (2):**
- `app/server/models/workflow.py` (add PlannedFeature models)
- `app/server/main.py` (register routes)

---

## Quick Reference

**Run migration:**
```bash
# SQLite
sqlite3 app/server/db/workflow_history.db < app/server/db/migrations/017_add_planned_features.sql

# PostgreSQL
PGPASSWORD=changeme psql -h localhost -p 5432 -U tac_user -d tac_webbuilder \
    -f app/server/db/migrations/017_add_planned_features_postgres.sql
```

**Populate database:**
```bash
python scripts/migrate_plans_panel_data.py --dry-run  # Preview
python scripts/migrate_plans_panel_data.py            # Execute
```

**Test API:**
```bash
curl http://localhost:8000/api/planned-features
curl http://localhost:8000/api/planned-features/stats
```

---

## Estimated Time

**Total: 3 hours**

- Step 1 (Migration): 45 min
- Step 2 (Models): 30 min
- Step 3 (Service): 60 min
- Step 4 (Routes): 60 min
- Step 5 (Data Migration): 45 min
- Step 6 (Tests): 60 min

---

## Session Completion Template

When done, provide summary in this format:

```markdown
## ✅ Session 8A Complete - Plans Panel Backend

**Duration:** ~X hours
**Status:** Complete ✅
**Next:** Ready for Session 8B (Frontend Integration)

### What Was Done
- Created planned_features table (SQLite + PostgreSQL)
- Implemented PlannedFeaturesService with full CRUD
- Created 7 REST API endpoints
- Migrated sessions 1-7 to database
- 8/8 tests passing

### Key Results
- X sessions migrated to database
- API fully functional and tested
- Backend ready for frontend integration

### Files Changed
**Created (6):**
- app/server/db/migrations/017_add_planned_features.sql
- app/server/db/migrations/017_add_planned_features_postgres.sql
- app/server/services/planned_features_service.py
- app/server/routes/planned_features_routes.py
- app/server/tests/services/test_planned_features_service.py
- scripts/migrate_plans_panel_data.py

**Modified (2):**
- app/server/models/workflow.py
- app/server/main.py

### Test Results
```
pytest app/server/tests/services/test_planned_features_service.py -v
======================== 8 passed in X.XXs ========================
```

### Next Session
Session 8B: Plans Panel Frontend (2 hours)
- TypeScript API client
- Component refactor with TanStack Query
- Real-time updates
```
