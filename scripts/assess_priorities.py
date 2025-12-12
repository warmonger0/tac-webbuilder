#!/usr/bin/env python3
"""Assess current priorities from Plans Panel."""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'server'))

from database import get_database_adapter


def assess_priorities():
    adapter = get_database_adapter()
    db_type = adapter.get_db_type()

    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        print("=" * 70)
        print("📊 CURRENT PRIORITIES ASSESSMENT")
        print("=" * 70)
        print()

        # Get high-priority planned items
        cursor.execute(
            """
            SELECT id, item_type, title, estimated_hours, tags, parent_id
            FROM planned_features
            WHERE status = 'planned'
              AND priority = 'high'
            ORDER BY estimated_hours ASC
            """ if db_type == "postgresql" else """
            SELECT id, item_type, title, estimated_hours, tags, parent_id
            FROM planned_features
            WHERE status = 'planned'
              AND priority = 'high'
            ORDER BY estimated_hours ASC
            """
        )

        high_priority = cursor.fetchall()

        print("🔥 HIGH PRIORITY - PLANNED (Quick Wins First)")
        print("-" * 70)

        if high_priority:
            for i, item in enumerate(high_priority, 1):
                if isinstance(item, tuple):
                    f_id, f_type, f_title, f_hours, f_tags, f_parent = item
                else:
                    f_id = item.get('id')
                    f_type = item.get('item_type')
                    f_title = item.get('title')
                    f_hours = item.get('estimated_hours')
                    f_tags = item.get('tags')
                    f_parent = item.get('parent_id')

                parent_label = f" [Sub-feature of #{f_parent}]" if f_parent else ""
                print(f"{i}. #{f_id} - {f_title}{parent_label}")
                print(f"   Type: {f_type} | Est: {f_hours}h")

                if f_tags:
                    if isinstance(f_tags, str):
                        tags_list = json.loads(f_tags)
                    else:
                        tags_list = f_tags
                    if tags_list:
                        print(f"   Tags: {', '.join(tags_list)}")
                print()
        else:
            print("   No high-priority planned items")
            print()

        # Get medium-priority planned items (for context)
        cursor.execute(
            """
            SELECT id, item_type, title, estimated_hours, parent_id
            FROM planned_features
            WHERE status = 'planned'
              AND priority = 'medium'
            ORDER BY estimated_hours ASC
            LIMIT 5
            """ if db_type == "postgresql" else """
            SELECT id, item_type, title, estimated_hours, parent_id
            FROM planned_features
            WHERE status = 'planned'
              AND priority = 'medium'
            ORDER BY estimated_hours ASC
            LIMIT 5
            """
        )

        medium_priority = cursor.fetchall()

        print("📋 MEDIUM PRIORITY - PLANNED (Top 5)")
        print("-" * 70)

        if medium_priority:
            for i, item in enumerate(medium_priority, 1):
                if isinstance(item, tuple):
                    f_id, f_type, f_title, f_hours, f_parent = item
                else:
                    f_id = item.get('id')
                    f_type = item.get('item_type')
                    f_title = item.get('title')
                    f_hours = item.get('estimated_hours')
                    f_parent = item.get('parent_id')

                parent_label = f" [Sub-feature of #{f_parent}]" if f_parent else ""
                print(f"{i}. #{f_id} - {f_title}{parent_label}")
                print(f"   Type: {f_type} | Est: {f_hours}h")
                print()
        else:
            print("   No medium-priority planned items")
            print()

        # Get in-progress items
        cursor.execute(
            """
            SELECT id, item_type, title, estimated_hours, started_at
            FROM planned_features
            WHERE status = 'in_progress'
            ORDER BY started_at ASC
            """ if db_type == "postgresql" else """
            SELECT id, item_type, title, estimated_hours, started_at
            FROM planned_features
            WHERE status = 'in_progress'
            ORDER BY started_at ASC
            """
        )

        in_progress = cursor.fetchall()

        print("🔄 IN PROGRESS")
        print("-" * 70)

        if in_progress:
            for i, item in enumerate(in_progress, 1):
                if isinstance(item, tuple):
                    f_id, f_type, f_title, f_hours, f_started = item
                else:
                    f_id = item.get('id')
                    f_type = item.get('item_type')
                    f_title = item.get('title')
                    f_hours = item.get('estimated_hours')
                    f_started = item.get('started_at')

                print(f"{i}. #{f_id} - {f_title}")
                print(f"   Type: {f_type} | Est: {f_hours}h | Started: {f_started}")
                print()
        else:
            print("   No items in progress")
            print()

        # Quick wins analysis (< 2 hours)
        cursor.execute(
            """
            SELECT COUNT(*), SUM(estimated_hours)
            FROM planned_features
            WHERE status = 'planned'
              AND estimated_hours <= 2.0
            """ if db_type == "postgresql" else """
            SELECT COUNT(*), SUM(estimated_hours)
            FROM planned_features
            WHERE status = 'planned'
              AND estimated_hours <= 2.0
            """
        )

        quick_wins = cursor.fetchone()
        if isinstance(quick_wins, tuple):
            qw_count, qw_hours = quick_wins
        else:
            qw_count = quick_wins.get('count')
            qw_hours = quick_wins.get('sum')

        print("=" * 70)
        print("⚡ QUICK WINS AVAILABLE")
        print("=" * 70)
        print(f"   {qw_count} tasks ≤ 2 hours")
        print(f"   Total time: {qw_hours}h")
        print()

        # Get the quick wins
        cursor.execute(
            """
            SELECT id, title, estimated_hours, priority, tags
            FROM planned_features
            WHERE status = 'planned'
              AND estimated_hours <= 2.0
            ORDER BY priority DESC, estimated_hours ASC
            """ if db_type == "postgresql" else """
            SELECT id, title, estimated_hours, priority, tags
            FROM planned_features
            WHERE status = 'planned'
              AND estimated_hours <= 2.0
            ORDER BY priority DESC, estimated_hours ASC
            """
        )

        quick_items = cursor.fetchall()

        for i, item in enumerate(quick_items, 1):
            if isinstance(item, tuple):
                f_id, f_title, f_hours, f_priority, f_tags = item
            else:
                f_id = item.get('id')
                f_title = item.get('title')
                f_hours = item.get('estimated_hours')
                f_priority = item.get('priority')
                f_tags = item.get('tags')

            priority_icon = "🔥" if f_priority == "high" else "📋" if f_priority == "medium" else "📝"
            print(f"{i}. {priority_icon} #{f_id} - {f_title}")
            print(f"   {f_hours}h | Priority: {f_priority}")

            if f_tags:
                if isinstance(f_tags, str):
                    tags_list = json.loads(f_tags)
                else:
                    tags_list = f_tags
                if tags_list:
                    print(f"   Tags: {', '.join(tags_list)}")
            print()

        # Recommendation engine
        print("=" * 70)
        print("💡 RECOMMENDATIONS")
        print("=" * 70)
        print()

        # Strategy 1: Quick Wins
        print("Strategy 1: QUICK WINS (Build Momentum)")
        print("-" * 70)
        print(f"   Pick from {qw_count} tasks ≤ 2h")
        print("   ✅ Pros: Fast progress, immediate value, morale boost")
        print("   ⚠️  Cons: May not address blockers or high-impact work")
        print()

        # Strategy 2: High Priority
        if high_priority:
            print("Strategy 2: HIGH PRIORITY (Critical Path)")
            print("-" * 70)
            print(f"   {len(high_priority)} high-priority items waiting")
            print("   ✅ Pros: Addresses blockers, enables other work")
            print("   ⚠️  Cons: May take longer, higher complexity")
            print()

        # Strategy 3: Complete in-progress
        if in_progress:
            print("Strategy 3: FINISH IN-PROGRESS (Reduce WIP)")
            print("-" * 70)
            print(f"   {len(in_progress)} items partially complete")
            print("   ✅ Pros: Clear the board, finish what you started")
            print("   ⚠️  Cons: May not be highest priority now")
            print()

        # Strategy 4: Closed-Loop Automation
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM planned_features
            WHERE parent_id = 99
              AND status = 'planned'
            """ if db_type == "postgresql" else """
            SELECT COUNT(*)
            FROM planned_features
            WHERE parent_id = 99
              AND status = 'planned'
            """
        )
        cl_count = cursor.fetchone()
        count = cl_count[0] if isinstance(cl_count, tuple) else cl_count.get('count')

        print("Strategy 4: CLOSED-LOOP AUTOMATION (Big Feature)")
        print("-" * 70)
        print(f"   {count}/11 sub-features remaining")
        print("   ✅ Pros: Game-changing feature, high ROI")
        print("   ⚠️  Cons: Large time investment (28.5h total)")
        print()

        print("=" * 70)
        print("🎯 SUGGESTED NEXT ACTIONS")
        print("=" * 70)
        print()
        print("Option A: Quick Win Sprint (2-4h)")
        print("   → Pick 2-3 quick wins from list above")
        print("   → Build momentum, clear small items")
        print()
        print("Option B: High-Priority Focus (variable)")
        print("   → Tackle highest-priority planned item")
        print("   → Address blockers and critical work")
        print()
        print("Option C: Closed-Loop Sub-Feature (1.5-4.5h)")
        print("   → Pick one sub-feature from #99")
        print("   → Progress toward game-changing automation")
        print()
        print("Option D: Session Documentation (variable)")
        print("   → Document recent PostgreSQL migration work")
        print("   → Update /prime and reference docs")
        print()


if __name__ == "__main__":
    assess_priorities()
