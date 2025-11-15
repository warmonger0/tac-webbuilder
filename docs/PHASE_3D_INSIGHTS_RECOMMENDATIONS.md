# Phase 3D: Insights & Recommendations

**Status:** Not Started
**Complexity:** MEDIUM-HIGH
**Estimated Cost:** $1-2 (Sonnet)
**Execution:** **ADW WORKFLOW** (complex pattern detection)
**Duration:** 1.5-2 hours

## Overview

Implement anomaly detection and optimization recommendation generation to provide actionable intelligence. This phase transforms raw analytics into insights that help users improve their workflows.

## Why This Needs ADW

- **Complex heuristics** - Anomaly detection requires statistical analysis
- **Pattern matching** - Recommendations based on multiple data points
- **Business logic** - Needs to understand workflow context
- **Testing complexity** - Many edge cases to cover
- **Codebase integration** - Must integrate with existing UI patterns

## Dependencies

- **Phase 3A completed** - Infrastructure must exist
- **Phase 3B completed** - Scoring functions must work
- **Phase 3C optional** - UI integration easier if scores display working
- Historical workflow data for comparison

## Scope

### 1. Anomaly Detection

**Function:** `detect_anomalies(workflow: Dict, historical_data: List[Dict]) -> List[str]`

**File:** `app/server/core/workflow_analytics.py`

```python
def detect_anomalies(workflow: Dict, historical_data: List[Dict]) -> List[str]:
    """
    Detect anomalies in workflow execution.

    Detects:
    1. Cost anomalies (>2x average)
    2. Duration anomalies (>2x average)
    3. Retry anomalies (unusually high)
    4. Error category anomalies (unexpected errors)
    5. Cache efficiency anomalies (unusually low)

    Args:
        workflow: Current workflow data
        historical_data: List of historical workflows for comparison

    Returns:
        List of anomaly descriptions (human-readable)
    """
    anomalies = []

    # Filter historical data to similar workflows
    similar_workflows = [
        w for w in historical_data
        if w.get('classification_type') == workflow.get('classification_type')
        and w.get('workflow_template') == workflow.get('workflow_template')
        and w['adw_id'] != workflow['adw_id']  # Exclude self
    ]

    if len(similar_workflows) < 3:
        # Not enough data for meaningful comparison
        return anomalies

    # 1. Cost Anomaly
    if workflow.get('actual_cost') and similar_workflows:
        avg_cost = sum(w.get('actual_cost', 0) for w in similar_workflows) / len(similar_workflows)
        if workflow['actual_cost'] > avg_cost * 2:
            anomalies.append(
                f"Cost is {workflow['actual_cost'] / avg_cost:.1f}x higher than average "
                f"(${workflow['actual_cost']:.2f} vs ${avg_cost:.2f} avg)"
            )

    # 2. Duration Anomaly
    if workflow.get('total_duration_seconds') and similar_workflows:
        avg_duration = sum(w.get('total_duration_seconds', 0) for w in similar_workflows) / len(similar_workflows)
        if workflow['total_duration_seconds'] > avg_duration * 2:
            anomalies.append(
                f"Duration is {workflow['total_duration_seconds'] / avg_duration:.1f}x longer than average "
                f"({workflow['total_duration_seconds'] / 60:.1f} min vs {avg_duration / 60:.1f} min avg)"
            )

    # 3. Retry Anomaly
    retry_count = workflow.get('retry_count', 0)
    if retry_count >= 3:
        anomalies.append(
            f"High retry count ({retry_count} retries) indicates potential instability"
        )

    # 4. Error Category Anomaly
    errors = workflow.get('errors', [])
    if errors:
        error_types = set(e.get('category', 'unknown') for e in errors)
        common_error_types = {'syntax_error', 'type_error', 'api_error'}

        unexpected_errors = error_types - common_error_types
        if unexpected_errors:
            anomalies.append(
                f"Unexpected error types encountered: {', '.join(unexpected_errors)}"
            )

    # 5. Cache Efficiency Anomaly
    cache_read = workflow.get('cache_read_tokens', 0)
    total_input = workflow.get('input_tokens', 0)
    if total_input > 0:
        cache_rate = cache_read / total_input
        if cache_rate < 0.2 and total_input > 5000:  # Low cache on large inputs
            anomalies.append(
                f"Cache efficiency is unusually low ({cache_rate * 100:.1f}%) for large input"
            )

    return anomalies
```

### 2. Optimization Recommendations

**Function:** `generate_optimization_recommendations(workflow: Dict) -> List[str]`

**File:** `app/server/core/workflow_analytics.py`

```python
def generate_optimization_recommendations(workflow: Dict) -> List[str]:
    """
    Generate actionable optimization recommendations.

    Categories:
    1. Model selection recommendations
    2. Cache optimization tips
    3. Input quality improvements
    4. Workflow structure suggestions
    5. Cost reduction strategies

    Args:
        workflow: Workflow data dictionary

    Returns:
        List of recommendation strings (prioritized, most impactful first)
    """
    recommendations = []

    # 1. Model Selection Recommendations
    complexity = detect_complexity(workflow)
    model = workflow.get('model', '')

    if complexity == 'simple' and 'sonnet' in model.lower():
        estimated_savings = workflow.get('actual_cost', 0) * 0.7  # ~70% savings with Haiku
        recommendations.append(
            f"💡 Consider using Haiku model for similar simple tasks (potential savings: ${estimated_savings:.2f})"
        )

    if complexity == 'complex' and 'haiku' in model.lower():
        recommendations.append(
            "⚠️ Complex task used Haiku - consider Sonnet for better quality and fewer retries"
        )

    # 2. Cache Optimization
    cache_read = workflow.get('cache_read_tokens', 0)
    total_input = workflow.get('input_tokens', 0)

    if total_input > 0:
        cache_rate = cache_read / total_input
        if cache_rate < 0.3:
            recommendations.append(
                "📦 Low cache hit rate - consider restructuring prompts to improve caching"
            )

    # 3. Input Quality Improvements
    clarity_score = workflow.get('nl_input_clarity_score', 0)

    if clarity_score < 50:
        word_count = workflow.get('nl_input_word_count', 0)
        if word_count < 30:
            recommendations.append(
                "📝 NL input is too brief - add acceptance criteria and technical details for better results"
            )
        else:
            recommendations.append(
                "📝 NL input lacks structure - use bullet points and specific requirements"
            )

    # 4. Workflow Structure Suggestions
    phases = workflow.get('phase_metrics', [])
    if phases:
        # Find bottleneck phases (>50% of total time)
        total_duration = workflow.get('total_duration_seconds', 1)
        for phase in phases:
            phase_duration = phase.get('duration_seconds', 0)
            if phase_duration / total_duration > 0.5:
                recommendations.append(
                    f"⏱️ '{phase['phase_name']}' phase is bottleneck ({phase_duration / 60:.1f} min) - "
                    f"consider breaking into smaller subtasks"
                )

    # 5. Cost Reduction Strategies
    retry_count = workflow.get('retry_count', 0)
    if retry_count > 0:
        retry_cost = workflow.get('actual_cost', 0) * (retry_count / (retry_count + 1))
        recommendations.append(
            f"💰 {retry_count} retries added ${retry_cost:.2f} to cost - improve error handling"
        )

    # 6. Error Prevention
    errors = workflow.get('errors', [])
    if len(errors) > 5:
        recommendations.append(
            "🐛 High error count - review error logs and add validation steps"
        )

    # 7. Performance Optimization
    performance_score = workflow.get('performance_score', 100)
    if performance_score < 50:
        recommendations.append(
            "🚀 Performance below average - review workflow structure and remove unnecessary steps"
        )

    # Return top 5 most impactful recommendations
    return recommendations[:5]


def detect_complexity(workflow: Dict) -> str:
    """
    Detect workflow complexity level.

    Returns: "simple", "medium", "complex"
    """
    word_count = workflow.get('nl_input_word_count', 0)
    duration = workflow.get('total_duration_seconds', 0)
    error_count = len(workflow.get('errors', []))

    if word_count < 50 and duration < 300 and error_count < 3:
        return "simple"
    elif word_count > 200 or duration > 1800 or error_count > 5:
        return "complex"
    else:
        return "medium"
```

### 3. Integration into Sync Process

**File:** `app/server/core/workflow_history.py`

Update `sync_workflow_history()` to calculate insights:

```python
def sync_workflow_history() -> int:
    """Sync with anomaly detection and recommendations."""

    # ... existing sync logic ...

    # Get all workflows for comparison
    all_workflows = fetch_all_workflows()

    for workflow in workflows:
        # ... existing score calculations ...

        # Detect anomalies
        workflow['anomaly_flags'] = detect_anomalies(workflow, all_workflows)

        # Generate recommendations
        workflow['optimization_recommendations'] = generate_optimization_recommendations(workflow)

        # Serialize JSON arrays for SQLite
        workflow['anomaly_flags'] = json.dumps(workflow['anomaly_flags'])
        workflow['optimization_recommendations'] = json.dumps(workflow['optimization_recommendations'])

    # ... rest of sync logic ...
```

### 4. Frontend UI Integration

**File:** `app/client/src/components/WorkflowHistoryCard.tsx`

Add Insights & Recommendations section after Efficiency Scores:

```tsx
{/* Insights & Recommendations Section */}
{(workflow.anomaly_flags && workflow.anomaly_flags.length > 0) ||
(workflow.optimization_recommendations && workflow.optimization_recommendations.length > 0) ? (
  <div className="border-b border-gray-200 pb-6">
    <h3 className="text-base font-semibold text-gray-800 mb-4">
      💡 Insights & Recommendations
    </h3>

    {/* Anomaly Alerts */}
    {workflow.anomaly_flags && workflow.anomaly_flags.length > 0 && (
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-orange-700 mb-2 flex items-center gap-2">
          <span>⚠️</span>
          <span>Anomalies Detected</span>
        </h4>
        <ul className="space-y-2">
          {workflow.anomaly_flags.map((anomaly: string, idx: number) => (
            <li
              key={idx}
              className="bg-orange-50 border border-orange-200 rounded p-3 text-sm text-gray-700"
            >
              {anomaly}
            </li>
          ))}
        </ul>
      </div>
    )}

    {/* Optimization Recommendations */}
    {workflow.optimization_recommendations && workflow.optimization_recommendations.length > 0 && (
      <div>
        <h4 className="text-sm font-semibold text-green-700 mb-2 flex items-center gap-2">
          <span>✅</span>
          <span>Optimization Tips</span>
        </h4>
        <ul className="space-y-2">
          {workflow.optimization_recommendations.map((rec: string, idx: number) => (
            <li
              key={idx}
              className="bg-green-50 border border-green-200 rounded p-3 text-sm text-gray-700"
            >
              {rec}
            </li>
          ))}
        </ul>
      </div>
    )}
  </div>
) : null}
```

### 5. Data Deserialization

**File:** `app/server/core/workflow_history.py`

Ensure JSON arrays are deserialized when fetching:

```python
def get_workflow_history(filters: Optional[Dict] = None) -> List[WorkflowHistoryItem]:
    """Fetch workflow history with deserialized JSON fields."""

    # ... query database ...

    for workflow in workflows:
        # Deserialize JSON fields
        if workflow.get('anomaly_flags'):
            workflow['anomaly_flags'] = json.loads(workflow['anomaly_flags'])
        else:
            workflow['anomaly_flags'] = []

        if workflow.get('optimization_recommendations'):
            workflow['optimization_recommendations'] = json.loads(workflow['optimization_recommendations'])
        else:
            workflow['optimization_recommendations'] = []

        # ... other deserialization ...

    return workflows
```

## Acceptance Criteria

- [ ] `detect_anomalies()` function implemented
- [ ] Detects cost anomalies (>2x average)
- [ ] Detects duration anomalies (>2x average)
- [ ] Detects retry anomalies (3+ retries)
- [ ] Detects cache efficiency anomalies
- [ ] Handles insufficient historical data gracefully
- [ ] `generate_optimization_recommendations()` implemented
- [ ] Recommends model changes when appropriate
- [ ] Recommends cache optimizations
- [ ] Recommends input quality improvements
- [ ] Recommends workflow restructuring for bottlenecks
- [ ] Returns max 5 recommendations (prioritized)
- [ ] `detect_complexity()` helper function created
- [ ] Sync process populates anomaly_flags and recommendations
- [ ] JSON serialization/deserialization works correctly
- [ ] Insights section added to WorkflowHistoryCard UI
- [ ] Anomalies display with orange warning styling
- [ ] Recommendations display with green positive styling
- [ ] Section hidden when no insights available
- [ ] Unit tests for anomaly detection (5+ test cases)
- [ ] Unit tests for recommendations (5+ test cases)
- [ ] Integration tests verify insights populated
- [ ] No TypeScript/Python errors

## Testing Requirements

### Unit Tests

**File:** `app/server/tests/test_workflow_analytics_insights.py`

```python
import pytest
from core.workflow_analytics import detect_anomalies, generate_optimization_recommendations, detect_complexity

class TestAnomalyDetection:
    def test_cost_anomaly_detected(self):
        workflow = {'actual_cost': 10.0, 'classification_type': 'feature', 'workflow_template': 'standard', 'adw_id': '1'}
        historical = [
            {'actual_cost': 2.0, 'classification_type': 'feature', 'workflow_template': 'standard', 'adw_id': '2'},
            {'actual_cost': 2.5, 'classification_type': 'feature', 'workflow_template': 'standard', 'adw_id': '3'},
            {'actual_cost': 3.0, 'classification_type': 'feature', 'workflow_template': 'standard', 'adw_id': '4'},
        ]

        anomalies = detect_anomalies(workflow, historical)
        assert len(anomalies) > 0
        assert 'Cost is' in anomalies[0]

    def test_duration_anomaly_detected(self):
        workflow = {'total_duration_seconds': 3600, 'classification_type': 'bug', 'workflow_template': 'hotfix', 'adw_id': '1'}
        historical = [
            {'total_duration_seconds': 600, 'classification_type': 'bug', 'workflow_template': 'hotfix', 'adw_id': '2'},
            {'total_duration_seconds': 700, 'classification_type': 'bug', 'workflow_template': 'hotfix', 'adw_id': '3'},
            {'total_duration_seconds': 800, 'classification_type': 'bug', 'workflow_template': 'hotfix', 'adw_id': '4'},
        ]

        anomalies = detect_anomalies(workflow, historical)
        assert any('Duration is' in a for a in anomalies)

    def test_retry_anomaly_detected(self):
        workflow = {'retry_count': 5, 'classification_type': 'feature', 'adw_id': '1'}

        anomalies = detect_anomalies(workflow, [])
        assert any('retry' in a.lower() for a in anomalies)

    def test_no_anomalies_for_normal_workflow(self):
        workflow = {
            'actual_cost': 2.2,
            'total_duration_seconds': 650,
            'retry_count': 0,
            'errors': [],
            'cache_read_tokens': 8000,
            'input_tokens': 10000,
            'classification_type': 'feature',
            'workflow_template': 'standard',
            'adw_id': '1'
        }
        historical = [
            {'actual_cost': 2.0, 'total_duration_seconds': 600, 'classification_type': 'feature', 'workflow_template': 'standard', 'adw_id': '2'},
            {'actual_cost': 2.5, 'total_duration_seconds': 700, 'classification_type': 'feature', 'workflow_template': 'standard', 'adw_id': '3'},
        ]

        anomalies = detect_anomalies(workflow, historical)
        assert len(anomalies) == 0

    def test_insufficient_data_returns_empty(self):
        workflow = {'actual_cost': 100, 'classification_type': 'feature', 'adw_id': '1'}
        historical = [
            {'actual_cost': 2.0, 'classification_type': 'feature', 'adw_id': '2'}
        ]  # Only 1 similar workflow

        anomalies = detect_anomalies(workflow, historical)
        assert len(anomalies) == 0


class TestRecommendations:
    def test_model_downgrade_recommendation(self):
        workflow = {
            'model': 'claude-sonnet-3.5',
            'nl_input_word_count': 20,
            'total_duration_seconds': 180,
            'errors': [],
            'actual_cost': 1.50
        }

        recs = generate_optimization_recommendations(workflow)
        assert any('Haiku' in r for r in recs)

    def test_cache_optimization_recommendation(self):
        workflow = {
            'cache_read_tokens': 1000,
            'input_tokens': 10000,
            'model': 'claude-sonnet-3.5'
        }

        recs = generate_optimization_recommendations(workflow)
        assert any('cache' in r.lower() for r in recs)

    def test_input_quality_recommendation(self):
        workflow = {
            'nl_input_clarity_score': 30,
            'nl_input_word_count': 15,
            'model': 'claude-haiku-3.5'
        }

        recs = generate_optimization_recommendations(workflow)
        assert any('input' in r.lower() or 'NL' in r for r in recs)

    def test_max_5_recommendations(self):
        # Workflow with many issues
        workflow = {
            'model': 'claude-sonnet-3.5',
            'nl_input_word_count': 20,
            'cache_read_tokens': 100,
            'input_tokens': 10000,
            'nl_input_clarity_score': 25,
            'retry_count': 3,
            'errors': ['e1', 'e2', 'e3', 'e4', 'e5', 'e6'],
            'performance_score': 30,
            'actual_cost': 5.0,
            'total_duration_seconds': 200
        }

        recs = generate_optimization_recommendations(workflow)
        assert len(recs) <= 5


class TestComplexityDetection:
    def test_simple_workflow(self):
        workflow = {'nl_input_word_count': 30, 'total_duration_seconds': 200, 'errors': []}
        assert detect_complexity(workflow) == 'simple'

    def test_complex_workflow(self):
        workflow = {'nl_input_word_count': 250, 'total_duration_seconds': 2000, 'errors': list(range(6))}
        assert detect_complexity(workflow) == 'complex'

    def test_medium_workflow(self):
        workflow = {'nl_input_word_count': 100, 'total_duration_seconds': 900, 'errors': [1, 2]}
        assert detect_complexity(workflow) == 'medium'
```

## Files to Create

- `app/server/tests/test_workflow_analytics_insights.py`

## Files to Modify

- `app/server/core/workflow_analytics.py` (add 3 functions)
- `app/server/core/workflow_history.py` (integrate insights into sync)
- `app/client/src/components/WorkflowHistoryCard.tsx` (add insights section)

## Time Estimate

- Anomaly detection: 45 minutes
- Recommendations: 45 minutes
- Complexity detection: 15 minutes
- Sync integration: 20 minutes
- UI integration: 30 minutes
- Unit tests: 45 minutes
- Testing/debugging: 30 minutes
- **Total: 3.5 hours**

## ADW Workflow Recommendations

**Classification:** `standard`
**Model:** Sonnet (complex heuristics)
**Issue Title:** "Implement Phase 3D: Anomaly Detection & Optimization Recommendations"

**Issue Description:**
```markdown
Add anomaly detection and optimization recommendations to workflow analytics.

Requirements:
- Detect 5 types of anomalies (cost, duration, retry, error, cache)
- Generate prioritized optimization recommendations
- Integrate with sync process
- Add Insights section to UI
- Comprehensive unit tests

See: docs/PHASE_3D_INSIGHTS_RECOMMENDATIONS.md
```

## Success Metrics

- Anomaly detection identifies real outliers
- Recommendations are specific and actionable
- UI displays insights clearly
- All tests pass (15+ test cases)
- No false positives on normal workflows

## Next Phase

After Phase 3D is complete:
- **Phase 3E** will add similar workflow detection and comparison
- Users can benchmark their workflows against similar ones
- Comparative analytics enable data-driven optimization

## Notes

- **Statistical rigor** - Use 2x threshold to reduce false positives
- **Actionable recommendations** - Every recommendation should be specific
- **Prioritization** - Return max 5 recommendations, most impactful first
- **Context-aware** - Consider workflow type and complexity
- **User-friendly language** - Avoid technical jargon in messages
