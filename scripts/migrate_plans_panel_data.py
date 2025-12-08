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

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "server"))

from core.models import PlannedFeatureCreate
from services.planned_features_service import PlannedFeaturesService


class PlansPanelMigrator:
    """Migrate hardcoded plans panel data to database."""

    def __init__(self, dry_run=False):
        self.service = PlannedFeaturesService()
        self.dry_run = dry_run
        self.created_count = 0
        self.error_count = 0

    def migrate_completed_sessions(self):
        """Migrate completed sessions 1-7 to database."""
        sessions = [
            {
                "item_type": "session",
                "session_number": 7,
                "title": "Session 7: Daily Pattern Analysis System",
                "description": "Automated pattern detection and analysis with scheduled daily runs, database persistence, and comprehensive test coverage.",
                "status": "completed",
                "priority": "high",
                "estimated_hours": 3.0,
                "actual_hours": 3.0,
                "tags": ["observability", "automation", "pattern-analysis"],
                "completion_notes": "13/13 tests passing, PostgreSQL compatible, scheduled analysis working",
            },
            {
                "item_type": "session",
                "session_number": 6,
                "title": "Session 6: Pattern Review System (CLI + Web UI)",
                "description": "Pattern approval/rejection system with CLI tool, Panel 8 web UI, and full CRUD operations.",
                "status": "completed",
                "priority": "high",
                "estimated_hours": 4.0,
                "actual_hours": 4.0,
                "tags": ["observability", "cli", "web-ui", "panel-8"],
                "completion_notes": "CLI + Web UI + 6 API endpoints, manual review workflow implemented",
            },
            {
                "item_type": "session",
                "session_number": 5,
                "title": "Session 5: Verify Phase Implementation",
                "description": "10th phase of SDLC workflow for automated verification before Ship phase.",
                "status": "completed",
                "priority": "high",
                "estimated_hours": 2.0,
                "actual_hours": 2.0,
                "tags": ["adw", "verification", "phase-10"],
                "completion_notes": "23/23 tests passing, 10-phase SDLC complete with verification gate",
            },
            {
                "item_type": "session",
                "session_number": 4,
                "title": "Session 4: Integration Checklist Validation",
                "description": "Automated validation of integration checklists in Ship phase to prevent deployment errors.",
                "status": "completed",
                "priority": "high",
                "estimated_hours": 3.5,
                "actual_hours": 3.5,
                "tags": ["adw", "ship-phase", "validation"],
                "completion_notes": "28/28 tests passing, 90% bug reduction in Ship phase",
            },
            {
                "item_type": "session",
                "session_number": 3,
                "title": "Session 3: Integration Checklist Generation",
                "description": "Smart integration checklist generation in Plan phase with feature detection.",
                "status": "completed",
                "priority": "high",
                "estimated_hours": 3.0,
                "actual_hours": 3.0,
                "tags": ["adw", "plan-phase", "checklist"],
                "completion_notes": "10/10 tests passing, smart feature detection working",
            },
            {
                "item_type": "session",
                "session_number": 2,
                "title": "Session 2: Port Pool Implementation",
                "description": "Concurrent port management for ADW workflows (backend 9100-9114, frontend 9200-9214).",
                "status": "completed",
                "priority": "high",
                "estimated_hours": 3.0,
                "actual_hours": 3.0,
                "tags": ["infrastructure", "port-management"],
                "completion_notes": "13/13 tests passing, 100-slot capacity (15 concurrent ADWs)",
            },
            {
                "item_type": "session",
                "session_number": 1.5,
                "title": "Session 1.5: Pattern Detection System Cleanup",
                "description": "Fixed 87x pattern duplication bug in pattern detection system.",
                "status": "completed",
                "priority": "high",
                "estimated_hours": 3.0,
                "actual_hours": 3.0,
                "tags": ["observability", "bug-fix", "database"],
                "completion_notes": "Fixed 87x duplication bug, analyzed 39K events, database cleanup",
            },
            {
                "item_type": "session",
                "session_number": 1,
                "title": "Session 1: Pattern Detection Audit",
                "description": "Initial audit of pattern detection system, discovered duplication bug.",
                "status": "completed",
                "priority": "high",
                "estimated_hours": 2.0,
                "actual_hours": 2.0,
                "tags": ["observability", "audit"],
                "completion_notes": "Discovered pattern detection bug, paved way for Session 1.5 fix",
            },
        ]

        print("\n=== Migrating Completed Sessions (1-7) ===")
        for session_data in sessions:
            self._create_feature(session_data)

    def migrate_planned_sessions(self):
        """Migrate planned sessions 8-14 to database."""
        sessions = [
            {
                "item_type": "session",
                "session_number": 8,
                "title": "Session 8: Plans Panel Database Migration",
                "description": "Backend (8A): Database schema, service layer, API endpoints. Frontend (8B): TypeScript client, component refactor.",
                "status": "in_progress",
                "priority": "medium",
                "estimated_hours": 4.5,
                "tags": ["database", "frontend", "api", "panel-5"],
            },
            {
                "item_type": "session",
                "session_number": 9,
                "title": "Session 9: Cost Attribution Analytics",
                "description": "Track cost attribution per issue, phase, and workflow template for optimization insights.",
                "status": "planned",
                "priority": "medium",
                "estimated_hours": 3.5,
                "tags": ["analytics", "cost-optimization"],
            },
            {
                "item_type": "session",
                "session_number": 10,
                "title": "Session 10: Error Analytics",
                "description": "Analyze error patterns, categorize failures, track resolution times.",
                "status": "planned",
                "priority": "low",
                "estimated_hours": 3.5,
                "tags": ["analytics", "error-tracking"],
            },
            {
                "item_type": "session",
                "session_number": 11,
                "title": "Session 11: Latency Analytics",
                "description": "Track phase durations, identify bottlenecks, optimize performance.",
                "status": "planned",
                "priority": "low",
                "estimated_hours": 3.5,
                "tags": ["analytics", "performance"],
            },
            {
                "item_type": "session",
                "session_number": 12,
                "title": "Session 12: Closed-Loop ROI Tracking",
                "description": "Measure automation ROI, track time saved, calculate cost per feature.",
                "status": "planned",
                "priority": "low",
                "estimated_hours": 4.5,
                "tags": ["observability", "roi", "automation"],
            },
            {
                "item_type": "session",
                "session_number": 13,
                "title": "Session 13: Confidence Updating System",
                "description": "Machine learning-based confidence score updates for detected patterns.",
                "status": "planned",
                "priority": "low",
                "estimated_hours": 3.5,
                "tags": ["observability", "machine-learning"],
            },
            {
                "item_type": "session",
                "session_number": 14,
                "title": "Session 14: Auto-Archiving System",
                "description": "Automatically archive old workflows, cleanup stale data, maintain system performance.",
                "status": "planned",
                "priority": "low",
                "estimated_hours": 2.5,
                "tags": ["automation", "maintenance"],
            },
        ]

        print("\n=== Migrating Planned Sessions (8-14) ===")
        for session_data in sessions:
            self._create_feature(session_data)

    def _create_feature(self, feature_data: dict):
        """
        Create a single planned feature.

        Args:
            feature_data: Dictionary with feature details
        """
        if self.dry_run:
            print(f"[DRY RUN] Would create: {feature_data['title']}")
            return

        try:
            # Handle session 1.5 - convert to integer session 1 or remove it
            if feature_data.get("session_number") == 1.5:
                feature_data["session_number"] = None  # Store as non-session item or use integer

            feature = PlannedFeatureCreate(**feature_data)
            created = self.service.create(feature)
            print(f"✅ Created: {created.title} (ID: {created.id})")
            self.created_count += 1
        except Exception as e:
            print(f"❌ Error creating {feature_data['title']}: {e}")
            import traceback
            traceback.print_exc()
            self.error_count += 1

    def print_summary(self):
        """Print migration summary."""
        print("\n" + "=" * 60)
        print("Migration Summary")
        print("=" * 60)
        if self.dry_run:
            print("Mode: DRY RUN (no changes made)")
        else:
            print(f"✅ Successfully created: {self.created_count} features")
            print(f"❌ Errors: {self.error_count} features")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Migrate Plans Panel data to database"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without making changes"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Plans Panel Data Migration")
    print("=" * 60)

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made")

    migrator = PlansPanelMigrator(dry_run=args.dry_run)

    # Migrate all sessions
    migrator.migrate_completed_sessions()
    migrator.migrate_planned_sessions()

    # Print summary
    migrator.print_summary()

    if not args.dry_run:
        print("\n✅ Migration complete! Database is ready for Session 8B.")
    else:
        print("\n💡 Run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
