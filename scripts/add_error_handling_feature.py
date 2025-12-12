#!/usr/bin/env python3
"""
Add Error Handling Sub-Agent Protocol to Plans Panel

Adds the 9th sub-feature (Feature #108) to the Closed-Loop Automation System (Parent #99).
"""

import os
import sys
import json
from datetime import datetime

# Add server directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'server'))

from database import get_database_adapter


def add_error_handling_feature():
    """Add Error Handling Protocol feature to planned_features table."""

    adapter = get_database_adapter()
    db_type = adapter.get_db_type()

    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        # Check if parent feature (Closed-Loop Automation System) exists
        cursor.execute(
            "SELECT id, title FROM planned_features WHERE id = %s" if db_type == "postgresql" else
            "SELECT id, title FROM planned_features WHERE id = ?",
            (99,)
        )
        parent = cursor.fetchone()

        if not parent:
            print("❌ Error: Parent feature #99 (Closed-Loop Automation System) not found")
            print("Please create the parent feature first")
            return False

        parent_id = parent[0] if isinstance(parent, tuple) else parent.get('id')
        parent_title = parent[1] if isinstance(parent, tuple) else parent.get('title')
        print(f"✅ Found parent feature #{parent_id}: {parent_title}")

        # Check if error handling feature already exists
        cursor.execute(
            "SELECT id FROM planned_features WHERE id = %s" if db_type == "postgresql" else
            "SELECT id FROM planned_features WHERE id = ?",
            (108,)
        )
        existing = cursor.fetchone()

        if existing:
            print("⚠️  Feature #108 (Error Handling Protocol) already exists")
            print("Skipping insertion")
            return True

        # Insert Error Handling Sub-Agent Protocol feature
        feature_data = {
            "id": 108,
            "item_type": "feature",
            "title": "Error Handling Sub-Agent Protocol",
            "description": (
                "Comprehensive error handling system that detects workflow failures, "
                "analyzes root causes, updates Plans Panel, runs cleanup operations, "
                "and provides one-click fix workflows. Completes the closed-loop for "
                "both success and failure paths."
            ),
            "status": "planned",
            "priority": "high",
            "estimated_hours": 3.0,
            "parent_id": 99,
            "github_issue_number": None,
            "tags": json.dumps([
                "closed-loop-automation",
                "error-handling",
                "sub-agent",
                "plans-panel",
                "observability"
            ])
        }

        # Build INSERT query (database-agnostic)
        if db_type == "postgresql":
            query = """
                INSERT INTO planned_features (
                    id, item_type, title, description, status, priority,
                    estimated_hours, parent_id, github_issue_number, tags
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb
                )
            """
            params = (
                feature_data["id"],
                feature_data["item_type"],
                feature_data["title"],
                feature_data["description"],
                feature_data["status"],
                feature_data["priority"],
                feature_data["estimated_hours"],
                feature_data["parent_id"],
                feature_data["github_issue_number"],
                feature_data["tags"]
            )
        else:  # SQLite
            query = """
                INSERT INTO planned_features (
                    id, item_type, title, description, status, priority,
                    estimated_hours, parent_id, github_issue_number, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                feature_data["id"],
                feature_data["item_type"],
                feature_data["title"],
                feature_data["description"],
                feature_data["status"],
                feature_data["priority"],
                feature_data["estimated_hours"],
                feature_data["parent_id"],
                feature_data["github_issue_number"],
                feature_data["tags"]
            )

        cursor.execute(query, params)
        conn.commit()

        print("✅ Successfully added Error Handling Sub-Agent Protocol")
        print(f"   ID: {feature_data['id']}")
        print(f"   Parent: #{feature_data['parent_id']} (Closed-Loop Automation)")
        print(f"   Status: {feature_data['status']}")
        print(f"   Priority: {feature_data['priority']}")
        print(f"   Estimated Hours: {feature_data['estimated_hours']}h")
        print(f"   Tags: {json.loads(feature_data['tags'])}")

        # Display all sub-features of Closed-Loop Automation
        print("\n📋 Closed-Loop Automation System - Sub-Features:")
        cursor.execute(
            """
            SELECT id, title, status, estimated_hours, priority
            FROM planned_features
            WHERE parent_id = %s
            ORDER BY id
            """ if db_type == "postgresql" else """
            SELECT id, title, status, estimated_hours, priority
            FROM planned_features
            WHERE parent_id = ?
            ORDER BY id
            """,
            (99,)
        )

        sub_features = cursor.fetchall()
        total_hours = 0

        for i, feature in enumerate(sub_features, 1):
            if isinstance(feature, tuple):
                f_id, f_title, f_status, f_hours, f_priority = feature
            else:
                f_id = feature.get('id')
                f_title = feature.get('title')
                f_status = feature.get('status')
                f_hours = feature.get('estimated_hours')
                f_priority = feature.get('priority')

            status_icon = {
                "planned": "📝",
                "in_progress": "🔄",
                "completed": "✅",
                "cancelled": "❌",
                "failed": "⚠️"
            }.get(f_status, "❓")

            priority_color = {
                "high": "\033[91m",  # Red
                "medium": "\033[93m",  # Yellow
                "low": "\033[92m"  # Green
            }.get(f_priority, "")
            reset_color = "\033[0m"

            print(f"   {i}. {status_icon} #{f_id} - {f_title}")
            print(f"      Status: {f_status} | Priority: {priority_color}{f_priority}{reset_color} | Est: {f_hours}h")

            if f_hours:
                total_hours += f_hours

        print(f"\n📊 Total Estimated Hours: {total_hours}h")

        return True


if __name__ == "__main__":
    print("=" * 70)
    print("Adding Error Handling Sub-Agent Protocol to Plans Panel")
    print("=" * 70)
    print()

    try:
        success = add_error_handling_feature()

        if success:
            print("\n✅ Feature addition complete!")
            print("\n📖 Design Documentation:")
            print("   app_docs/design-error-handling-protocol.md")
            print("\n🔗 Next Steps:")
            print("   1. Review design document")
            print("   2. Create Migration 020 for 'failed' status")
            print("   3. Implement error_analyzer subagent")
            print("   4. Add error handling to ADW workflows")
            print("   5. Update Plans Panel UI for failed items")
        else:
            print("\n❌ Feature addition failed")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
