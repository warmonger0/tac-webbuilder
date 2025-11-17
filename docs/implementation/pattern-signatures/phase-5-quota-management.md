# Phase 5: Proactive Quota Management - Implementation Strategy

**Duration:** Week 3-4 (7-10 days, overlaps with Phase 4)
**Dependencies:** Phases 1-3 complete (for accurate forecasting)
**Priority:** HIGH - Prevents catastrophic API exhaustion
**Status:** Ready to implement

---

## Overview

Build intelligent quota forecasting and workflow throttling to prevent API limit exhaustion. The system predicts monthly token usage, enforces workflow budgets, and gracefully throttles operations when approaching limits.

**This prevents the problem you experienced:** workflows stalling mid-execution due to unexpected quota exhaustion.

---

## Goals

1. ✅ Forecast monthly token usage with 90%+ accuracy
2. ✅ Implement pre-flight checks before starting workflows
3. ✅ Enforce token budgets per workflow (prevent oversized workflows)
4. ✅ Throttle low-priority workflows when quota at risk
5. ✅ Post informative GitHub comments explaining quota status
6. ✅ Provide dashboard endpoint for real-time monitoring

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  WORKFLOW START REQUESTED                                 │
│  Issue #42: "Run comprehensive integration tests"        │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  PRE-FLIGHT CHECK 1: API Quota Available?                │
│  (existing: api_quota.py)                                 │
│  Makes minimal API call to check quota                    │
└────────────────────┬─────────────────────────────────────┘
                     │ [✓ Available]
                     ▼
┌──────────────────────────────────────────────────────────┐
│  PRE-FLIGHT CHECK 2: Monthly Forecast                    │
│  NEW: quota_forecaster.py                                 │
│  • Calculate daily avg from last 7 days                   │
│  • Project to end of month                                │
│  • Compare to known limit                                 │
│  • Risk level: low/medium/high/critical                   │
└────────────────────┬─────────────────────────────────────┘
                     │ [✓ Risk acceptable]
                     ▼
┌──────────────────────────────────────────────────────────┐
│  PRE-FLIGHT CHECK 3: Workflow Budget                     │
│  NEW: workflow_budgets.py                                 │
│  • Estimate tokens based on similar workflows             │
│  • Check against MAX_TOKENS_PER_WORKFLOW (5M)             │
│  • Reject if exceeds budget                               │
└────────────────────┬─────────────────────────────────────┘
                     │ [✓ Within budget]
                     ▼
┌──────────────────────────────────────────────────────────┐
│  ✅ ALL CHECKS PASSED                                     │
│  Post GitHub comment with status                          │
│  Start workflow                                           │
└──────────────────────────────────────────────────────────┘

                [✗ ANY CHECK FAILS]
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  ❌ WORKFLOW BLOCKED                                      │
│  Post GitHub comment explaining why                       │
│  • Quota exhausted → wait for reset                       │
│  • High risk → throttling enabled                         │
│  • Budget exceeded → reduce scope                         │
└──────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Step 5.1: Create Token Usage Forecaster
**File:** `app/server/core/quota_forecaster.py`

**Full Implementation:**

```python
# app/server/core/quota_forecaster.py

"""
Token Usage Forecasting and Quota Management

Predicts monthly token usage based on recent trends and provides
risk assessment for quota exhaustion.
"""

import os
import sqlite3
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# Get quota limit from environment
ANTHROPIC_QUOTA_LIMIT = int(os.getenv("ANTHROPIC_QUOTA_LIMIT", 300_000_000))


# ============================================================================
# DATA COLLECTION
# ============================================================================

def get_recent_token_usage(db_connection, days: int = 7) -> List[Dict]:
    """
    Get token usage for the last N days.

    Returns:
        List of daily usage dicts:
        [
            {
                'date': '2025-11-10',
                'total_tokens': 18_500_000,
                'workflow_count': 12
            },
            ...
        ]
    """
    cursor = db_connection.cursor()

    cursor.execute("""
        SELECT
            DATE(created_at) as date,
            SUM(total_tokens) as total_tokens,
            COUNT(*) as workflow_count
        FROM workflow_history
        WHERE created_at >= datetime('now', ? || ' days')
        AND status IN ('completed', 'failed')
        AND total_tokens IS NOT NULL
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """, (f'-{days}',))

    rows = cursor.fetchall()

    if not rows:
        logger.warning("[Forecast] No recent token usage data available")
        return []

    return [
        {
            'date': row[0],
            'total_tokens': row[1] or 0,
            'workflow_count': row[2]
        }
        for row in rows
    ]


def get_current_month_usage(db_connection) -> Dict:
    """
    Get token usage for current month to date.

    Returns:
        {
            'month': '2025-11',
            'total_tokens': 185_000_000,
            'workflow_count': 89,
            'days_elapsed': 16,
            'first_workflow_date': '2025-11-01'
        }
    """
    cursor = db_connection.cursor()

    # Get current month
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    cursor.execute("""
        SELECT
            SUM(total_tokens) as total_tokens,
            COUNT(*) as workflow_count,
            MIN(DATE(created_at)) as first_date
        FROM workflow_history
        WHERE created_at >= ?
        AND status IN ('completed', 'failed')
        AND total_tokens IS NOT NULL
    """, (month_start.isoformat(),))

    row = cursor.fetchone()

    days_elapsed = (now - month_start).days + 1

    return {
        'month': now.strftime('%Y-%m'),
        'total_tokens': row[0] or 0,
        'workflow_count': row[1],
        'days_elapsed': days_elapsed,
        'first_workflow_date': row[2]
    }


# ============================================================================
# FORECASTING
# ============================================================================

def calculate_daily_average(recent_usage: List[Dict]) -> float:
    """
    Calculate average daily token usage from recent data.

    Uses weighted average (more recent days weighted higher).
    """
    if not recent_usage:
        return 0.0

    # Weight more recent days higher (exponential decay)
    total_weighted_tokens = 0.0
    total_weight = 0.0

    for i, day_data in enumerate(recent_usage):
        weight = 1.0 / (i + 1)  # Most recent = 1.0, next = 0.5, etc.
        total_weighted_tokens += day_data['total_tokens'] * weight
        total_weight += weight

    return total_weighted_tokens / total_weight if total_weight > 0 else 0.0


def project_end_of_month(
    current_month: Dict,
    daily_average: float
) -> Dict:
    """
    Project token usage to end of current month.

    Returns:
        {
            'projected_total': 345_000_000,
            'days_remaining': 14,
            'projected_daily_tokens': 11_428_571
        }
    """
    # Calculate days remaining in month
    now = datetime.now()
    last_day = (now.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    days_remaining = (last_day - now).days

    # Project forward
    projected_additional = daily_average * days_remaining
    projected_total = current_month['total_tokens'] + projected_additional

    return {
        'projected_total': int(projected_total),
        'days_remaining': days_remaining,
        'projected_daily_tokens': int(projected_total / (current_month['days_elapsed'] + days_remaining))
    }


def assess_risk_level(projected_total: int, quota_limit: int) -> Tuple[str, str]:
    """
    Assess risk of exceeding quota.

    Returns:
        (risk_level: str, explanation: str)

    Risk levels:
    - low: < 70% of quota
    - medium: 70-85% of quota
    - high: 85-95% of quota
    - critical: > 95% of quota
    """
    percentage = (projected_total / quota_limit) * 100

    if percentage < 70:
        return 'low', f"Projected usage is {percentage:.1f}% of quota - well within limits"
    elif percentage < 85:
        return 'medium', f"Projected usage is {percentage:.1f}% of quota - monitoring recommended"
    elif percentage < 95:
        return 'high', f"Projected usage is {percentage:.1f}% of quota - throttling recommended"
    else:
        return 'critical', f"Projected usage is {percentage:.1f}% of quota - immediate action required"


def generate_recommendations(
    risk_level: str,
    projected_total: int,
    quota_limit: int
) -> List[str]:
    """Generate actionable recommendations based on risk."""
    recommendations = []

    overage = projected_total - quota_limit

    if risk_level == 'low':
        recommendations.append("Continue normal operations")
        recommendations.append("Review pattern automation opportunities to reduce costs")

    elif risk_level == 'medium':
        recommendations.append("Monitor usage daily")
        recommendations.append("Enable pattern-based tool routing to reduce tokens")
        recommendations.append("Consider deferring non-urgent workflows")

    elif risk_level == 'high':
        recommendations.append(f"⚠️ ENABLE THROTTLING - projected to exceed by {overage:,} tokens")
        recommendations.append("Delay low-priority workflows until next month")
        recommendations.append("Switch simple tasks to Haiku model")
        recommendations.append("Activate all available pattern automation")

    else:  # critical
        recommendations.append(f"🚨 IMMEDIATE ACTION REQUIRED - projected to exceed by {overage:,} tokens")
        recommendations.append("Pause all non-essential workflows")
        recommendations.append("Upgrade quota tier or wait for monthly reset")
        recommendations.append("Review large workflows for optimization")

    return recommendations


# ============================================================================
# MAIN FORECASTING FUNCTION
# ============================================================================

def forecast_monthly_usage(db_connection = None) -> Dict:
    """
    Main forecasting function - analyzes usage and projects forward.

    Returns:
        {
            'current_month_tokens': 185_000_000,
            'days_elapsed': 16,
            'days_remaining': 14,
            'daily_avg_tokens': 11_562_500,
            'projected_total': 345_625_000,
            'quota_limit': 300_000_000,
            'risk_level': 'high',
            'will_exceed_by': 45_625_000,
            'confidence': 0.85,
            'recommendations': [...]
        }
    """
    # Connect to database if not provided
    if db_connection is None:
        project_root = Path(__file__).parent.parent.parent
        db_path = project_root / "app" / "server" / "db" / "workflow_history.db"
        db_connection = sqlite3.connect(str(db_path))
        should_close = True
    else:
        should_close = False

    try:
        # Gather data
        recent_usage = get_recent_token_usage(db_connection, days=7)
        current_month = get_current_month_usage(db_connection)

        if not recent_usage:
            # Not enough data for forecasting
            return {
                'current_month_tokens': current_month['total_tokens'],
                'days_elapsed': current_month['days_elapsed'],
                'days_remaining': 0,
                'daily_avg_tokens': 0,
                'projected_total': current_month['total_tokens'],
                'quota_limit': ANTHROPIC_QUOTA_LIMIT,
                'risk_level': 'unknown',
                'will_exceed_by': 0,
                'confidence': 0.0,
                'recommendations': ["Insufficient data for forecasting"],
                'error': "Not enough recent usage data"
            }

        # Calculate forecast
        daily_avg = calculate_daily_average(recent_usage)
        projection = project_end_of_month(current_month, daily_avg)

        # Assess risk
        risk_level, risk_explanation = assess_risk_level(
            projection['projected_total'],
            ANTHROPIC_QUOTA_LIMIT
        )

        # Calculate overage/underage
        will_exceed_by = projection['projected_total'] - ANTHROPIC_QUOTA_LIMIT

        # Confidence based on data consistency
        # Higher confidence if recent days have consistent usage
        token_variance = calculate_variance([d['total_tokens'] for d in recent_usage])
        confidence = 1.0 / (1.0 + token_variance / 1_000_000_000)  # Normalize

        # Generate recommendations
        recommendations = generate_recommendations(
            risk_level,
            projection['projected_total'],
            ANTHROPIC_QUOTA_LIMIT
        )

        logger.info(
            f"[Forecast] Projected: {projection['projected_total']:,} / "
            f"{ANTHROPIC_QUOTA_LIMIT:,} tokens ({risk_level} risk)"
        )

        return {
            'current_month_tokens': current_month['total_tokens'],
            'days_elapsed': current_month['days_elapsed'],
            'days_remaining': projection['days_remaining'],
            'daily_avg_tokens': int(daily_avg),
            'projected_total': projection['projected_total'],
            'quota_limit': ANTHROPIC_QUOTA_LIMIT,
            'risk_level': risk_level,
            'risk_explanation': risk_explanation,
            'will_exceed_by': will_exceed_by,
            'confidence': round(confidence, 2),
            'recommendations': recommendations,
            'recent_usage_days': len(recent_usage)
        }

    finally:
        if should_close:
            db_connection.close()


def calculate_variance(values: List[float]) -> float:
    """Calculate variance of values."""
    if len(values) < 2:
        return 0.0

    mean = sum(values) / len(values)
    return sum((x - mean) ** 2 for x in values) / len(values)


# ============================================================================
# THROTTLING LOGIC
# ============================================================================

def should_throttle_workflows(db_connection = None) -> Tuple[bool, str]:
    """
    Determine if workflows should be throttled based on forecast.

    Returns:
        (should_throttle: bool, reason: str)
    """
    forecast = forecast_monthly_usage(db_connection)

    if forecast.get('error'):
        # Can't forecast, allow workflows
        return False, "Insufficient data for throttling decision"

    risk_level = forecast['risk_level']

    if risk_level in ['high', 'critical']:
        return True, f"Quota risk: {risk_level} - {forecast['risk_explanation']}"

    if forecast['projected_total'] > forecast['quota_limit'] * 0.90:
        return True, f"Approaching 90% of monthly quota ({forecast['projected_total']:,} / {forecast['quota_limit']:,})"

    # Check for usage spike (today's usage >> avg)
    if db_connection:
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT SUM(total_tokens)
            FROM workflow_history
            WHERE DATE(created_at) = DATE('now')
            AND status IN ('completed', 'failed')
        """)
        today_usage = cursor.fetchone()[0] or 0

        if today_usage > forecast['daily_avg_tokens'] * 2:
            return True, f"Usage spike detected: {today_usage:,} tokens today (avg: {forecast['daily_avg_tokens']:,})"

    return False, "Quota risk acceptable"


# ============================================================================
# DASHBOARD ENDPOINT DATA
# ============================================================================

def get_quota_dashboard_data(db_connection = None) -> Dict:
    """
    Get comprehensive quota data for dashboard display.

    Returns full forecast plus recent usage trends.
    """
    forecast = forecast_monthly_usage(db_connection)

    if db_connection is None:
        project_root = Path(__file__).parent.parent.parent
        db_path = project_root / "app" / "server" / "db" / "workflow_history.db"
        db_connection = sqlite3.connect(str(db_path))
        should_close = True
    else:
        should_close = False

    try:
        # Get recent trends
        recent_usage = get_recent_token_usage(db_connection, days=14)

        # Calculate trend direction
        if len(recent_usage) >= 7:
            recent_7d = recent_usage[:7]
            older_7d = recent_usage[7:]
            recent_avg = sum(d['total_tokens'] for d in recent_7d) / len(recent_7d)
            older_avg = sum(d['total_tokens'] for d in older_7d) / len(older_7d) if older_7d else recent_avg

            if recent_avg > older_avg * 1.1:
                trend = 'increasing'
            elif recent_avg < older_avg * 0.9:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'unknown'

        return {
            **forecast,
            'trend': trend,
            'recent_usage': recent_usage[:7],  # Last 7 days
            'timestamp': datetime.now().isoformat()
        }

    finally:
        if should_close:
            db_connection.close()
```

---

### Step 5.2: Create Workflow Budgeting
**File:** `app/server/core/workflow_budgets.py`

```python
# app/server/core/workflow_budgets.py

"""
Workflow Token Budgeting

Estimates token usage before workflow execution and enforces budgets.
"""

import sqlite3
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Default budget: 5M tokens per workflow
MAX_TOKENS_PER_WORKFLOW = 5_000_000


# ============================================================================
# COST ESTIMATION
# ============================================================================

def estimate_workflow_cost(
    issue_body: str,
    workflow_type: str,
    db_connection = None
) -> Dict:
    """
    Estimate token usage based on similar historical workflows.

    Args:
        issue_body: GitHub issue description
        workflow_type: 'planning', 'testing', 'building', etc.
        db_connection: SQLite connection (optional)

    Returns:
        {
            'estimated_input_tokens': 2_500_000,
            'estimated_output_tokens': 150_000,
            'estimated_total_tokens': 2_650_000,
            'estimated_cost_usd': 0.0265,
            'confidence': 0.85,
            'based_on_workflows': ['adw-abc', 'adw-def'],
            'warnings': []
        }
    """
    if db_connection is None:
        project_root = Path(__file__).parent.parent.parent
        db_path = project_root / "app" / "server" / "db" / "workflow_history.db"
        db_connection = sqlite3.connect(str(db_path))
        should_close = True
    else:
        should_close = False

    try:
        # Calculate input characteristics
        word_count = len(issue_body.split())
        has_code_blocks = '```' in issue_body
        is_complex = word_count > 200 or issue_body.count('\n') > 20

        # Find similar workflows
        similar = find_similar_workflows(
            word_count,
            workflow_type,
            is_complex,
            db_connection
        )

        if not similar:
            # No similar workflows, use defaults
            return get_default_estimate(word_count, is_complex)

        # Calculate average from similar workflows
        avg_input = sum(w['input_tokens'] for w in similar) / len(similar)
        avg_output = sum(w['output_tokens'] for w in similar) / len(similar)
        avg_total = sum(w['total_tokens'] for w in similar) / len(similar)

        # Adjust based on input size difference
        size_ratio = word_count / (sum(w['word_count'] for w in similar) / len(similar))
        adjusted_total = avg_total * size_ratio

        # Calculate confidence
        # Higher if we have many similar workflows with consistent costs
        variance = calculate_variance([w['total_tokens'] for w in similar])
        confidence = min(1.0, len(similar) / 10) * (1.0 / (1.0 + variance / 1_000_000))

        # Check for warnings
        warnings = []
        if adjusted_total > MAX_TOKENS_PER_WORKFLOW:
            warnings.append(f"Estimated tokens ({adjusted_total:,.0f}) exceeds budget ({MAX_TOKENS_PER_WORKFLOW:,})")
        if word_count > 500:
            warnings.append("Large input may benefit from splitting into smaller issues")

        logger.info(
            f"[Budget] Estimated {adjusted_total:,.0f} tokens "
            f"(confidence: {confidence:.0%}, based on {len(similar)} similar workflows)"
        )

        return {
            'estimated_input_tokens': int(avg_input * size_ratio),
            'estimated_output_tokens': int(avg_output * size_ratio),
            'estimated_total_tokens': int(adjusted_total),
            'estimated_cost_usd': (adjusted_total / 1000) * 0.003,  # $0.003/1K tokens
            'confidence': round(confidence, 2),
            'based_on_workflows': [w['adw_id'] for w in similar[:5]],
            'warnings': warnings
        }

    finally:
        if should_close:
            db_connection.close()


def find_similar_workflows(
    word_count: int,
    workflow_type: str,
    is_complex: bool,
    db_connection
) -> List[Dict]:
    """Find workflows with similar characteristics."""
    cursor = db_connection.cursor()

    # Query for similar workflows
    cursor.execute("""
        SELECT
            adw_id,
            nl_input_word_count as word_count,
            input_tokens,
            output_tokens,
            total_tokens,
            workflow_type
        FROM workflow_history
        WHERE workflow_type = ?
        AND status = 'completed'
        AND total_tokens IS NOT NULL
        AND nl_input_word_count BETWEEN ? AND ?
        ORDER BY created_at DESC
        LIMIT 20
    """, (
        workflow_type,
        int(word_count * 0.7),  # -30%
        int(word_count * 1.3)   # +30%
    ))

    return [dict(row) for row in cursor.fetchall()]


def get_default_estimate(word_count: int, is_complex: bool) -> Dict:
    """Provide default estimate when no similar workflows exist."""
    # Rule of thumb: ~100 tokens per word for input context
    # Output is typically 5-10% of input
    base_tokens = word_count * 100

    if is_complex:
        base_tokens *= 2  # Complex workflows load more context

    estimated_input = int(base_tokens)
    estimated_output = int(base_tokens * 0.08)
    estimated_total = estimated_input + estimated_output

    return {
        'estimated_input_tokens': estimated_input,
        'estimated_output_tokens': estimated_output,
        'estimated_total_tokens': estimated_total,
        'estimated_cost_usd': (estimated_total / 1000) * 0.003,
        'confidence': 0.3,  # Low confidence for default estimates
        'based_on_workflows': [],
        'warnings': ["No similar workflows found - using default estimation"]
    }


def calculate_variance(values: List[float]) -> float:
    """Calculate variance."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return sum((x - mean) ** 2 for x in values) / len(values)


# ============================================================================
# BUDGET ENFORCEMENT
# ============================================================================

def check_budget(
    estimated_tokens: int,
    max_tokens: int = MAX_TOKENS_PER_WORKFLOW
) -> Tuple[bool, Optional[str]]:
    """
    Verify workflow doesn't exceed budget.

    Args:
        estimated_tokens: Estimated token usage
        max_tokens: Maximum allowed (default 5M)

    Returns:
        (within_budget: bool, message: Optional[str])
    """
    if estimated_tokens > max_tokens:
        return False, (
            f"Estimated {estimated_tokens:,} tokens exceeds budget of {max_tokens:,}. "
            f"Consider splitting into smaller workflows."
        )

    # Warning if approaching budget
    if estimated_tokens > max_tokens * 0.8:
        return True, (
            f"Estimated {estimated_tokens:,} tokens is 80%+ of budget. "
            f"Workflow may be complex."
        )

    return True, None
```

---

### Step 5.3: Integrate Pre-Flight Checks
**File:** `adws/adw_sdlc_iso.py` (modify existing)

```python
# Add imports
from app.server.core.quota_forecaster import should_throttle_workflows, forecast_monthly_usage
from app.server.core.workflow_budgets import estimate_workflow_cost, check_budget


def can_start_adw(issue_number: int, workflow_type: str) -> Tuple[bool, str]:
    """
    Comprehensive pre-flight checks before starting workflow.

    Returns:
        (can_start: bool, reason: str)
    """
    db_path = project_root / "app" / "server" / "db" / "workflow_history.db"
    db_conn = sqlite3.connect(str(db_path))

    try:
        # Check 1: API quota available (existing check)
        from app.server.core.api_quota import can_start_adw as check_quota
        quota_ok, quota_msg = check_quota()

        if not quota_ok:
            post_github_comment(
                issue_number,
                f"❌ **Cannot Start Workflow**\n\n"
                f"**Reason:** {quota_msg}\n\n"
                f"Please wait for API quota to reset or upgrade your plan."
            )
            return False, quota_msg

        # Check 2: Monthly forecast
        should_throttle, throttle_msg = should_throttle_workflows(db_conn)

        if should_throttle:
            forecast = forecast_monthly_usage(db_conn)

            post_github_comment(
                issue_number,
                f"⏸️ **Workflow Throttled**\n\n"
                f"**Reason:** {throttle_msg}\n\n"
                f"**Monthly Forecast:**\n"
                f"- Current: {forecast['current_month_tokens']:,} tokens\n"
                f"- Projected: {forecast['projected_total']:,} tokens\n"
                f"- Limit: {forecast['quota_limit']:,} tokens\n"
                f"- Risk: {forecast['risk_level']}\n\n"
                f"**Recommendations:**\n" +
                "\n".join(f"- {rec}" for rec in forecast['recommendations'])
            )
            return False, throttle_msg

        # Check 3: Workflow budget
        issue = get_issue(issue_number)
        estimate = estimate_workflow_cost(issue['body'], workflow_type, db_conn)

        budget_ok, budget_msg = check_budget(estimate['estimated_total_tokens'])

        if not budget_ok:
            post_github_comment(
                issue_number,
                f"💰 **Budget Exceeded**\n\n"
                f"**Estimated tokens:** {estimate['estimated_total_tokens']:,}\n"
                f"**Budget limit:** {MAX_TOKENS_PER_WORKFLOW:,}\n\n"
                f"**Recommendation:** Split this into smaller, focused issues.\n\n"
                f"**Warnings:**\n" +
                "\n".join(f"- {w}" for w in estimate['warnings'])
            )
            return False, budget_msg

        # All checks passed
        forecast = forecast_monthly_usage(db_conn)

        post_github_comment(
            issue_number,
            f"✅ **Pre-Flight Checks Passed**\n\n"
            f"**Estimated tokens:** {estimate['estimated_total_tokens']:,}\n"
            f"**Confidence:** {estimate['confidence']:.0%}\n"
            f"**Monthly forecast:** {forecast['risk_level']} risk\n"
            f"**Quota available:** Yes\n\n"
            f"🚀 Starting workflow..."
        )

        return True, "All checks passed"

    finally:
        db_conn.close()
```

---

### Step 5.4: Add Dashboard Endpoint
**File:** `app/server/server.py` (add endpoint)

```python
from core.quota_forecaster import get_quota_dashboard_data

@app.get("/api/quota/forecast")
async def get_quota_forecast():
    """Get monthly usage forecast for monitoring dashboard."""
    try:
        data = get_quota_dashboard_data()
        return JSONResponse(data)
    except Exception as e:
        logger.error(f"Error getting quota forecast: {e}")
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )
```

---

## Testing Strategy

```bash
# Test 1: Forecasting
python -c "
from app.server.core.quota_forecaster import forecast_monthly_usage
forecast = forecast_monthly_usage()
print(f'Current: {forecast[\"current_month_tokens\"]:,} tokens')
print(f'Projected: {forecast[\"projected_total\"]:,} tokens')
print(f'Risk: {forecast[\"risk_level\"]}')
print(f'Recommendations: {len(forecast[\"recommendations\"])}')
"

# Test 2: Budget estimation
python -c "
from app.server.core.workflow_budgets import estimate_workflow_cost, check_budget

estimate = estimate_workflow_cost(
    'Run comprehensive integration tests on all API endpoints',
    'testing'
)

print(f'Estimated: {estimate[\"estimated_total_tokens\"]:,} tokens')
print(f'Confidence: {estimate[\"confidence\"]:.0%}')

budget_ok, msg = check_budget(estimate['estimated_total_tokens'])
print(f'Budget OK: {budget_ok}')
if msg:
    print(f'Message: {msg}')
"

# Test 3: Pre-flight checks
cd adws/
uv run adw_sdlc_iso.py 42  # Should show detailed pre-flight status

# Test 4: Dashboard endpoint
curl http://localhost:8000/api/quota/forecast | python -m json.tool

# Test 5: Throttling simulation
# Temporarily lower ANTHROPIC_QUOTA_LIMIT to trigger throttling
export ANTHROPIC_QUOTA_LIMIT=100000000
cd adws/
uv run adw_sdlc_iso.py 43  # Should be throttled
```

---

## Success Criteria

- [ ] ✅ Forecast accuracy within 10% of actual usage
- [ ] ✅ Pre-flight checks prevent oversized workflows
- [ ] ✅ Throttling activates when risk is high
- [ ] ✅ GitHub comments inform users clearly
- [ ] ✅ No quota exhaustion incidents during testing
- [ ] ✅ Dashboard endpoint returns valid data
- [ ] ✅ Budget estimates based on real historical data

---

## Deliverables

1. ✅ `app/server/core/quota_forecaster.py` (500+ lines)
2. ✅ `app/server/core/workflow_budgets.py` (300+ lines)
3. ✅ Modified `adws/adw_sdlc_iso.py` (+150 lines)
4. ✅ Dashboard API endpoint (+50 lines)
5. ✅ Unit tests (200+ lines)
6. ✅ Configuration documentation

**Total Lines of Code:** ~1200 lines

---

## Configuration

```bash
# Set quota limit (get from Anthropic dashboard)
export ANTHROPIC_QUOTA_LIMIT=300000000  # 300M tokens/month

# Add to .env
echo "ANTHROPIC_QUOTA_LIMIT=300000000" >> .env

# Verify
python -c "
import os
limit = int(os.getenv('ANTHROPIC_QUOTA_LIMIT', 300000000))
print(f'Quota limit: {limit:,} tokens/month')
"
```

---

## Monitoring

```sql
-- Check throttled workflows
SELECT COUNT(*) as throttled_count
FROM workflow_history
WHERE status = 'throttled'
AND created_at > datetime('now', '-7 days');

-- Review quota status
SELECT
    DATE(created_at) as date,
    SUM(total_tokens) as daily_tokens,
    COUNT(*) as workflows
FROM workflow_history
WHERE created_at > datetime('now', '-30 days')
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

---

## Next Steps (After Phase 5)

1. Monitor forecast accuracy for 1 month
2. Adjust thresholds if too sensitive/lenient
3. Fine-tune budget estimates
4. Build visualization dashboard (optional)
5. Document quota management procedures

---

**🎉 ALL 5 PHASES COMPLETE! 🎉**

You now have a complete implementation plan for out-loop coding with:
- Pattern detection and learning
- Context efficiency analysis
- Automated tool routing
- Auto-discovery of opportunities
- Proactive quota management
