#!/usr/bin/env python3
"""View all sub-features of the Closed-Loop Automation System."""

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'server'))

from database import get_database_adapter


def view_features():
    adapter = get_database_adapter()
    db_type = adapter.get_db_type()

    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        # Get parent feature
        cursor.execute(
            "SELECT id, title, status, estimated_hours FROM planned_features WHERE id = %s" if db_type == "postgresql" else
            "SELECT id, title, status, estimated_hours FROM planned_features WHERE id = ?",
            (99,)
        )
        parent = cursor.fetchone()

        if not parent:
            print("❌ Parent feature #99 not found")
            return

        if isinstance(parent, tuple):
            p_id, p_title, p_status, p_hours = parent
        else:
            p_id = parent.get('id')
            p_title = parent.get('title')
            p_status = parent.get('status')
            p_hours = parent.get('estimated_hours')

        print("=" * 70)
        print(f"📦 Parent Feature #{p_id}: {p_title}")
        print(f"   Status: {p_status} | Estimated: {p_hours}h")
        print("=" * 70)
        print()

        # Get all sub-features
        cursor.execute(
            """
            SELECT id, title, status, estimated_hours, priority, tags
            FROM planned_features
            WHERE parent_id = %s
            ORDER BY id
            """ if db_type == "postgresql" else """
            SELECT id, title, status, estimated_hours, priority, tags
            FROM planned_features
            WHERE parent_id = ?
            ORDER BY id
            """,
            (99,)
        )

        sub_features = cursor.fetchall()

        if not sub_features:
            print("📝 No sub-features found")
            return

        total_hours = 0
        print(f"📋 Sub-Features ({len(sub_features)} total):\n")

        for i, feature in enumerate(sub_features, 1):
            if isinstance(feature, tuple):
                f_id, f_title, f_status, f_hours, f_priority, f_tags = feature
            else:
                f_id = feature.get('id')
                f_title = feature.get('title')
                f_status = feature.get('status')
                f_hours = feature.get('estimated_hours')
                f_priority = feature.get('priority')
                f_tags = feature.get('tags')

            status_icon = {
                "planned": "📝",
                "in_progress": "🔄",
                "completed": "✅",
                "cancelled": "❌",
                "failed": "⚠️"
            }.get(f_status, "❓")

            print(f"{i}. {status_icon} Feature #{f_id}")
            print(f"   Title: {f_title}")
            print(f"   Status: {f_status}")
            print(f"   Priority: {f_priority}")
            print(f"   Estimated: {f_hours}h")

            if f_tags:
                if isinstance(f_tags, str):
                    tags_list = json.loads(f_tags)
                else:
                    tags_list = f_tags
                print(f"   Tags: {', '.join(tags_list)}")

            print()

            if f_hours:
                total_hours += f_hours

        print("=" * 70)
        print(f"📊 Total Estimated Hours: {total_hours}h")
        print("=" * 70)


if __name__ == "__main__":
    view_features()
