# Phases 3-5: Implementation Summary

Quick reference for automated tool routing, auto-discovery, and quota management.

---

## Phase 3: Automated Tool Routing (Week 2)

### Goal
Automatically route operations to specialized tools when high-confidence pattern match detected.

### Key Components

**1. Pattern Matcher (`app/server/core/pattern_matcher.py`)**
```python
def match_input_to_pattern(nl_input: str) -> Optional[Dict]:
    """
    Query operation_patterns where automation_status='active'.
    Return best match if confidence >= 70%.
    """

def route_to_tool(pattern: Dict, workflow_context: Dict) -> Dict:
    """
    Execute specialized tool (adw_test_workflow.py, etc.).
    Return compact results + tokens_saved.
    """
```

**2. ADW Executor Integration (`adws/adw_sdlc_iso.py`)**
```python
def execute_adw(issue_number, adw_id):
    # Check for pattern match
    pattern = pattern_matcher.match_input_to_pattern(state['nl_input'])

    if pattern and pattern['automation_status'] == 'active':
        # Route to specialized tool
        result = pattern_matcher.route_to_tool(pattern, state)

        # Log cost savings
        log_cost_savings(
            optimization_type='pattern_offload',
            tokens_saved=result['tokens_saved']
        )

        return result
    else:
        # Fallback to LLM
        return execute_with_llm(state)
```

**3. Tool Registry Population (`scripts/register_tools.py`)**
```python
# Register existing external tools
register_tool(
    tool_name='run_test_workflow',
    script_path='adws/adw_test_workflow.py',
    input_patterns=['run tests', 'test suite', 'pytest', 'vitest'],
    status='active'
)
```

### Testing
```bash
# Test pattern matching
python -c "
from app.server.core.pattern_matcher import match_input_to_pattern
result = match_input_to_pattern('run the backend tests')
print(f'Matched: {result[\"pattern_signature\"]} ({result[\"confidence_score\"]:.1f}%)')
"

# Test tool routing
cd adws/
uv run adw_sdlc_iso.py 43  # Should auto-route to test tool

# Verify cost savings logged
sqlite3 app/server/db/workflow_history.db "
SELECT optimization_type, tokens_saved, cost_saved_usd
FROM cost_savings_log
WHERE optimization_type = 'pattern_offload';
"
```

### Success Criteria
- [ ] Pattern matcher returns high-confidence matches
- [ ] Tool routing works for test/build operations
- [ ] Cost savings accurately tracked
- [ ] 40%+ of test/build operations auto-routed
- [ ] Fallback to LLM works on low confidence

### Deliverables
- `app/server/core/pattern_matcher.py` (400 lines)
- Modified `adws/adw_sdlc_iso.py` (+100 lines)
- `scripts/register_tools.py` (150 lines)
- Unit tests (200 lines)

---

## Phase 4: Auto-Discovery & Recommendations (Week 3)

### Goal
System automatically suggests new automation opportunities via GitHub issues.

### Key Components

**1. Pattern Analysis Job (`scripts/analyze_patterns.py`)**
```python
def analyze_automation_candidates():
    """
    Find patterns meeting threshold:
    - occurrence_count >= 5
    - confidence_score >= 70
    - potential_monthly_savings >= $0.50
    - automation_status = 'detected' or 'candidate'
    """

    candidates = db.query("""
        SELECT * FROM operation_patterns
        WHERE occurrence_count >= 5
        AND confidence_score >= 70
        AND potential_monthly_savings >= 0.50
        AND automation_status IN ('detected', 'candidate')
        ORDER BY potential_monthly_savings DESC
    """)

    for pattern in candidates:
        # Update status
        db.update_pattern_status(pattern['id'], 'candidate')

        # Create GitHub issue
        create_automation_suggestion_issue(pattern)
```

**2. GitHub Issue Creator**
```python
def create_automation_suggestion_issue(pattern: Dict):
    """
    Create issue with title:
    "🤖 Automation Opportunity: {pattern_signature}"

    Include:
    - Frequency (occurrence_count)
    - Potential savings ($/month and $/year)
    - Current vs optimized approach comparison
    - Recent workflow examples
    - Implementation recommendations
    """
```

**3. Cron Job Setup**
```bash
# Add to crontab (runs weekly on Sundays at midnight)
0 0 * * 0 cd /path/to/tac-webbuilder && python scripts/analyze_patterns.py
```

### Testing
```bash
# Manual trigger
python scripts/analyze_patterns.py

# Check for created issues
gh issue list --label automation-candidate

# Verify pattern status updated
sqlite3 app/server/db/workflow_history.db "
SELECT pattern_signature, automation_status, potential_monthly_savings
FROM operation_patterns
WHERE automation_status = 'candidate';
"
```

### GitHub Issue Template Example
```markdown
## 🤖 Automation Opportunity Detected

**Pattern:** `dependency-update:npm:all`
**Frequency:** Observed 7 times
**Potential Savings:** $1.20/month ($14.40/year)
**Confidence:** 82%

### Analysis

**Current approach (LLM):**
- Avg tokens: 125,000
- Avg cost: $0.375

**Optimized approach (Tool):**
- Estimated tokens: 6,250
- Estimated cost: $0.019
- **Savings per use:** $0.356 (95%)

### Recommended Implementation

Create script: `adws/adw_deps_update_workflow.py`

**Input patterns:**
- "update dependencies"
- "npm update"
- "upgrade packages"

**Expected behavior:**
1. Run `npm outdated`
2. Update package.json
3. Run tests
4. Return only breaking changes

### Recent Examples
- Workflow: adw-abc123 (2025-11-10)
- Workflow: adw-def456 (2025-11-08)
- Workflow: adw-ghi789 (2025-11-05)

---
**Labels:** automation-candidate, cost-optimization
**Priority:** medium
**Estimated ROI:** High (95% cost reduction)
```

### Success Criteria
- [ ] Analysis job runs successfully
- [ ] GitHub issues created automatically
- [ ] Issues contain actionable recommendations
- [ ] 2+ automation opportunities identified
- [ ] Pattern status updated correctly

### Deliverables
- `scripts/analyze_patterns.py` (300 lines)
- Cron job configuration
- GitHub issue template
- Documentation

---

## Phase 5: Proactive Quota Management (Week 3-4)

### Goal
Prevent API quota exhaustion through intelligent forecasting and throttling.

### Key Components

**1. Token Usage Forecaster (`app/server/core/quota_forecaster.py`)**
```python
def forecast_monthly_usage() -> Dict:
    """
    Returns:
        {
            'current_month_tokens': 185_000_000,
            'days_elapsed': 16,
            'days_remaining': 14,
            'daily_avg': 11_562_500,
            'projected_total': 345_625_000,
            'quota_limit': 300_000_000,  # Known from ANTHROPIC_QUOTA_LIMIT env
            'risk_level': 'high',  # low, medium, high, critical
            'will_exceed_by': 45_625_000,
            'recommendations': [
                'Enable throttling for low-priority workflows',
                'Switch simple tasks to Haiku model',
                'Delay non-urgent workflows until next month'
            ]
        }
    """
    # Analyze last 7 days usage
    # Calculate daily average
    # Project to end of month
    # Compare to limit
```

**2. Workflow Budgeting (`app/server/core/workflow_budgets.py`)**
```python
def estimate_workflow_cost(issue_body: str, workflow_type: str) -> Dict:
    """
    Predict token usage based on similar historical workflows.

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

def check_budget(estimated_tokens: int) -> Tuple[bool, str]:
    """Default budget: 5M tokens per workflow."""
    MAX_TOKENS_PER_WORKFLOW = 5_000_000

    if estimated_tokens > MAX_TOKENS_PER_WORKFLOW:
        return False, f"Estimated {estimated_tokens:,} exceeds budget"

    return True, None
```

**3. Throttling Logic**
```python
def should_throttle_workflows() -> Tuple[bool, str]:
    """
    Decide if new workflows should be delayed.

    Throttle when:
    - Risk level is 'high' or 'critical'
    - Projected usage > 90% of quota
    - Last 24h usage spike detected
    """
    forecast = forecast_monthly_usage()

    if forecast['risk_level'] in ['high', 'critical']:
        return True, f"Quota risk: {forecast['risk_level']}"

    if forecast['projected_total'] > forecast['quota_limit'] * 0.9:
        return True, "Approaching 90% of monthly quota"

    return False, None
```

**4. ADW Pre-Flight Checks (`adws/adw_sdlc_iso.py`)**
```python
def can_start_adw(issue_number: int, workflow_type: str) -> Tuple[bool, str]:
    """Comprehensive pre-flight checks."""

    # Check 1: API quota available
    quota_ok, quota_msg = api_quota.can_start_adw()
    if not quota_ok:
        post_github_comment(issue_number, f"❌ Cannot start: {quota_msg}")
        return False, quota_msg

    # Check 2: Monthly forecast
    should_throttle, throttle_msg = quota_forecaster.should_throttle_workflows()
    if should_throttle:
        post_github_comment(issue_number, f"⏸️ Throttled: {throttle_msg}")
        return False, throttle_msg

    # Check 3: Workflow budget
    issue = get_issue(issue_number)
    estimate = workflow_budgets.estimate_workflow_cost(issue['body'], workflow_type)
    budget_ok, budget_msg = workflow_budgets.check_budget(estimate['estimated_total_tokens'])
    if not budget_ok:
        post_github_comment(issue_number, f"💰 Budget exceeded: {budget_msg}")
        return False, budget_msg

    # All checks passed
    post_github_comment(
        issue_number,
        f"✅ Pre-flight checks passed\n"
        f"- Estimated: {estimate['estimated_total_tokens']:,} tokens\n"
        f"- Monthly forecast: {forecast['risk_level']} risk\n"
        f"- Quota available: {quota_msg or 'Yes'}\n"
        f"🚀 Starting workflow..."
    )
    return True, None
```

**5. Dashboard Endpoint (`app/server/server.py`)**
```python
@app.get("/api/quota/forecast")
async def get_quota_forecast():
    """Return monthly usage forecast for dashboard."""
    forecast = quota_forecaster.forecast_monthly_usage()
    return JSONResponse(forecast)
```

### Testing
```bash
# Test forecasting
python -c "
from app.server.core.quota_forecaster import forecast_monthly_usage
forecast = forecast_monthly_usage()
print(f'Current: {forecast[\"current_month_tokens\"]:,} tokens')
print(f'Projected: {forecast[\"projected_total\"]:,} tokens')
print(f'Limit: {forecast[\"quota_limit\"]:,} tokens')
print(f'Risk: {forecast[\"risk_level\"]}')
print(f'Will exceed: {forecast.get(\"will_exceed_by\", 0):,} tokens')
"

# Test budget checking
python -c "
from app.server.core.workflow_budgets import estimate_workflow_cost, check_budget
estimate = estimate_workflow_cost('Run the backend test suite', 'testing')
print(f'Estimated: {estimate[\"estimated_total_tokens\"]:,} tokens')
budget_ok, msg = check_budget(estimate['estimated_total_tokens'])
print(f'Budget OK: {budget_ok} - {msg}')
"

# Test pre-flight checks
cd adws/
uv run adw_sdlc_iso.py 42  # Should show pre-flight status

# Test dashboard endpoint
curl http://localhost:8000/api/quota/forecast | python -m json.tool
```

### Configuration
```bash
# Set environment variable for quota limit (get from Anthropic dashboard)
export ANTHROPIC_QUOTA_LIMIT=300000000  # 300M tokens/month

# Add to .env
echo "ANTHROPIC_QUOTA_LIMIT=300000000" >> .env
```

### Success Criteria
- [ ] Monthly usage forecast accurate (within 10%)
- [ ] Throttling activates when risk is high
- [ ] Budget checks prevent oversized workflows
- [ ] GitHub comments inform users of status
- [ ] No quota exhaustion incidents during testing
- [ ] Dashboard displays real-time forecast

### Deliverables
- `app/server/core/quota_forecaster.py` (400 lines)
- `app/server/core/workflow_budgets.py` (300 lines)
- Modified `adws/adw_sdlc_iso.py` (+150 lines)
- Dashboard endpoint (+50 lines)
- Unit tests (250 lines)
- Configuration documentation

---

## Integration Timeline

### Week 1: Foundation
- **Phase 1:** Pattern detection (Days 1-5)
- **Phase 2:** Context tracking (Days 3-7, overlaps with Phase 1)

### Week 2: Automation
- **Phase 3:** Tool routing (Days 8-14)
- Test integration, fix issues

### Week 3: Intelligence
- **Phase 4:** Auto-discovery (Days 15-19)
- **Phase 5:** Quota management (Days 15-21, parallel with Phase 4)

### Week 4: Testing & Refinement
- End-to-end testing
- Performance optimization
- Documentation
- User training

---

## Rollback Strategy

Each phase independent:

**Phase 3:** Set all patterns to `automation_status='deprecated'`
**Phase 4:** Disable cron job, close auto-created issues
**Phase 5:** Remove pre-flight checks from ADW executor

---

## Monitoring & Metrics

### Phase 3 Metrics
```sql
-- Tool routing success rate
SELECT
    COUNT(*) as total_routes,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
    AVG(tokens_saved) as avg_tokens_saved
FROM tool_calls
WHERE called_at > datetime('now', '-7 days');
```

### Phase 4 Metrics
```sql
-- Automation candidates generated
SELECT COUNT(*) FROM operation_patterns
WHERE automation_status = 'candidate'
AND updated_at > datetime('now', '-7 days');
```

### Phase 5 Metrics
```sql
-- Workflows throttled
SELECT COUNT(*) FROM workflow_history
WHERE status = 'throttled'
AND created_at > datetime('now', '-7 days');
```

---

## Final Validation

After all phases complete:

1. **Pattern Learning Working:** 10+ patterns detected
2. **Context Optimization:** 30%+ efficiency improvement
3. **Tool Routing:** 40%+ test/build operations automated
4. **Auto-Discovery:** 2+ GitHub issues created
5. **Quota Safety:** No exhaustion incidents for 1 month
6. **Cost Reduction:** 30-60% measured savings

**Success = All 6 criteria met**
