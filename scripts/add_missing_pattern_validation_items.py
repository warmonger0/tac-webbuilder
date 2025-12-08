#!/usr/bin/env python3
"""
Add missing Pattern Validation action items to Plans Panel

These were identified as missing from the roadmap:
1. Pattern Validation Loop (Phase 3: Close the Loop)
2. Verify Migration 010 Applied to PostgreSQL
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "server"))

from services.planned_features_service import PlannedFeaturesService
from core.models.workflow import PlannedFeatureCreate


def main():
    """Add missing pattern validation items to planned features."""
    service = PlannedFeaturesService()

    # Define the missing items
    items = [
        PlannedFeatureCreate(
            item_type="feature",
            title="Verify Migration 010 Applied to PostgreSQL",
            description=(
                "Check if migration 010 (pattern_predictions table) was applied to PostgreSQL database. "
                "This migration creates the pattern_predictions table needed for the closed-loop pattern "
                "validation system. The migration file exists but may not have been applied during database "
                "setup. Verify table exists and has correct schema with was_correct validation field."
            ),
            status="planned",
            priority="high",
            estimated_hours=0.5,
            session_number=None,
            tags=["database", "migration", "pattern-validation", "infrastructure"]
        ),
        PlannedFeatureCreate(
            item_type="feature",
            title="Implement Pattern Validation Loop (Phase 3: Close the Loop)",
            description=(
                "Complete Phase 3 of the Pattern Recognition System: Close the Loop - Validate Predictions. "
                "This creates a feedback loop that compares predicted patterns (from pattern_predictor.py) "
                "against actual patterns detected after workflow completion (from pattern_detector.py). "
                "Updates prediction accuracy metrics to improve future predictions. Includes: pattern_validator.py "
                "module, workflow completion integration, accuracy tracking, and analytics queries."
            ),
            status="planned",
            priority="high",
            estimated_hours=3.0,
            session_number=18,
            tags=["pattern-recognition", "machine-learning", "validation", "accuracy-tracking", "phase-3"]
        ),
    ]

    print("\n" + "=" * 100)
    print("ADDING MISSING PATTERN VALIDATION ACTION ITEMS")
    print("=" * 100 + "\n")

    for item in items:
        print(f"Adding: {item.title}")
        print(f"  Type: {item.item_type}")
        print(f"  Priority: {item.priority}")
        print(f"  Estimated Hours: {item.estimated_hours}")
        print(f"  Tags: {', '.join(item.tags)}")

        try:
            created = service.create(item)
            print(f"  ✅ Created with ID: {created.id}\n")
        except Exception as e:
            print(f"  ❌ Error: {e}\n")

    print("=" * 100)
    print("\nVerifying additions...")
    print("=" * 100 + "\n")

    # Verify the items were added
    all_features = service.get_all(limit=200)
    pattern_validation_features = [
        f for f in all_features
        if "pattern" in f.title.lower() and "validation" in f.title.lower()
        or "migration 010" in f.title.lower()
    ]

    print(f"Found {len(pattern_validation_features)} pattern validation related items:\n")
    for f in pattern_validation_features:
        print(f"  ID {f.id}: {f.title}")
        print(f"    Status: {f.status}, Priority: {f.priority}")
        print(f"    Tags: {', '.join(f.tags) if f.tags else 'None'}\n")

    print("=" * 100)
    print("\n✅ Complete! Check Plans Panel (Panel 5) in the UI to see the new items.")
    print("=" * 100 + "\n")


if __name__ == "__main__":
    main()
