#!/usr/bin/env python3
"""Add tool call tracking feature to planned_features table."""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'server'))

from services.planned_features_service import PlannedFeaturesService
from core.models import PlannedFeatureCreate


def main():
    """Add tool call tracking feature."""
    service = PlannedFeaturesService()

    feature_data = PlannedFeatureCreate(
        title="Tool Call Tracking and Analytics",
        description="Implement comprehensive tracking of individual tool calls (Bash, Read, Write, Edit, Grep) during ADW workflow execution. Enable pattern analysis, efficiency optimization, and cost attribution at the tool level.",
        item_type="feature",
        priority="high",
        complexity="medium",
        estimated_effort_hours=16.0,
        status="planned",
        tags=["observability", "analytics", "performance", "optimization"],
        technical_notes="Extend task_logs table with tool_calls JSONB field. Modify observability.py to capture tool invocations with timing, success/failure, parameters, and results. Create tool sequence analysis for pattern detection (e.g., Read→Edit→Write). Build analytics endpoints for tool usage patterns, redundancy detection, and optimization recommendations.",
        dependencies=["ADW Tracking Architecture Documentation"],
        success_criteria=[
            "Tool calls tracked in task_logs.tool_calls JSONB field",
            "Tool call data includes: name, duration_ms, success, parameters, result, context_size",
            "Tool sequence patterns detected and stored",
            "Analytics dashboard shows tool usage patterns",
            "API endpoints for tool call queries and analysis",
            "Documentation updated with tool tracking details"
        ]
    )

    try:
        feature = service.create(feature_data)
        print(f"✅ Successfully added feature #{feature.id}: {feature.title}")
        print(f"   Priority: {feature.priority}")
        print(f"   Complexity: {feature.complexity}")
        print(f"   Estimated effort: {feature.estimated_effort_hours} hours")
        print(f"   Status: {feature.status}")
        return 0
    except Exception as e:
        print(f"❌ Error adding feature: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
