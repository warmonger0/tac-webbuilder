# Cost Efficiency Score Improvements - Implementation Plan

## Problem Statement

The cost efficiency score shows **0.0 for 92% of workflows** (25 out of 27) because they lack cost estimates. Only workflows for issues #40 and #47 have estimates populated in `cost_estimates_by_issue.json`, making the score meaningless for most workflows.

## Current Behavior

**Cost Efficiency Score Logic** (workflow_analytics.py:155-246):
```python
estimated_cost = workflow.get("estimated_cost_total")
if estimated_cost is None or estimated_cost == 0:
    return 0.0  # ← 92% of workflows hit this
```

**Data Availability:**
- ✅ `actual_cost_total`: Available for all workflows (from raw_output.jsonl)
- ❌ `estimated_cost_total`: Only available for 2/27 workflows (7%)
- ✅ `cache_efficiency_percent`: Available for all workflows
- ✅ `retry_count`: Available for all workflows

**Cost Estimates File:**
```json
{
    "40": { "estimated_cost_total": 4.0, ... },
    "47": { "estimated_cost_total": 4.0, ... }
}
```
Only 2 issues have estimates saved!

**Result:** Score is 0.0 for 92% of workflows due to missing estimates

## Proposed Solution

### Phase 1: Backfill Estimates for Existing Issues (High Priority)
Generate cost estimates for all historical issues that have completed or running workflows.

### Phase 2: Auto-Generate Estimates for New Issues (High Priority)
Ensure every new issue gets a cost estimate before workflow execution.

### Phase 3: Improve Estimate Accuracy (Medium Priority)
Refine estimation algorithm based on historical actual costs.

---

## Implementation Details

### Phase 1: Backfill Historical Estimates

#### 1.1 Identify Issues Needing Estimates

**File:** `scripts/backfill_cost_estimates.py` (new file)

```python
#!/usr/bin/env python3
"""
Backfill cost estimates for all issues with workflows.
"""

from core.workflow_history import get_db_connection
from core.cost_estimate_storage import save_cost_estimate
from core.cost_estimator import estimate_issue_cost
import json

def get_issues_without_estimates() -> list[int]:
    """Get list of issue numbers that need estimates."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT issue_number
            FROM workflow_history
            WHERE issue_number IS NOT NULL
              AND estimated_cost_total = 0.0
            ORDER BY issue_number
        """)
        return [row["issue_number"] for row in cursor.fetchall()]

def backfill_estimates():
    """Generate and save estimates for all issues without them."""
    issues = get_issues_without_estimates()
    print(f"Found {len(issues)} issues needing estimates")

    for issue_num in issues:
        try:
            # Fetch issue from GitHub
            issue_data = fetch_github_issue(issue_num)

            # Generate estimate
            estimate = estimate_issue_cost(
                title=issue_data["title"],
                body=issue_data["body"],
                labels=issue_data["labels"]
            )

            # Save estimate
            save_cost_estimate(issue_num, estimate)
            print(f"✓ Issue #{issue_num}: ${estimate['estimated_cost_total']:.2f}")

        except Exception as e:
            print(f"✗ Issue #{issue_num}: {e}")

if __name__ == "__main__":
    backfill_estimates()
```

#### 1.2 GitHub Issue Fetching

**File:** `core/github_integration.py` (expand existing or create new)

```python
import subprocess
import json

def fetch_github_issue(issue_number: int) -> dict:
    """
    Fetch issue details from GitHub using gh CLI.

    Returns:
        {
            "title": str,
            "body": str,
            "labels": list[str],
            "state": str
        }
    """
    try:
        result = subprocess.run(
            ["gh", "issue", "view", str(issue_number), "--json", "title,body,labels,state"],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to fetch issue #{issue_number}: {e.stderr}")
```

#### 1.3 Cost Estimation Logic

**File:** `core/cost_estimator.py` (new file or expand existing)

```python
def estimate_issue_cost(title: str, body: str, labels: list[str]) -> dict:
    """
    Estimate workflow cost based on issue details.

    Uses heuristics based on:
    - Issue complexity indicators (keywords, length)
    - Labels (feature/bug/chore)
    - Historical data for similar issues

    Returns:
        {
            "estimated_cost_total": float,
            "estimated_cost_breakdown": dict,  # by phase
            "level": str,  # simple/medium/complex
            "confidence": float,  # 0-1
            "reasoning": str
        }
    """
    # Analyze issue text for complexity signals
    complexity_score = analyze_complexity(title, body, labels)

    # Map complexity to cost ranges
    if complexity_score < 0.3:
        level = "simple"
        base_cost = 1.5  # $1.50 base
    elif complexity_score < 0.7:
        level = "medium"
        base_cost = 3.0  # $3.00 base
    else:
        level = "complex"
        base_cost = 5.0  # $5.00 base

    # Adjust based on specific signals
    cost_multiplier = 1.0
    reasoning_parts = []

    # Check for database changes
    if any(keyword in body.lower() for keyword in ["database", "schema", "migration", "sql"]):
        cost_multiplier *= 1.3
        reasoning_parts.append("Database changes required")

    # Check for frontend changes
    if any(keyword in body.lower() for keyword in ["frontend", "ui", "component", "react"]):
        cost_multiplier *= 1.2
        reasoning_parts.append("Frontend changes required")

    # Check for testing requirements
    if any(keyword in body.lower() for keyword in ["test", "e2e", "integration"]):
        cost_multiplier *= 1.15
        reasoning_parts.append("Testing required")

    # Check for documentation
    if any(keyword in body.lower() for keyword in ["docs", "documentation", "readme"]):
        cost_multiplier *= 1.1
        reasoning_parts.append("Documentation required")

    estimated_total = base_cost * cost_multiplier

    # Phase breakdown (typical SDLC)
    breakdown = {
        "plan": estimated_total * 0.20,
        "build": estimated_total * 0.35,
        "test": estimated_total * 0.25,
        "review": estimated_total * 0.10,
        "document": estimated_total * 0.10
    }

    return {
        "estimated_cost_total": round(estimated_total, 2),
        "estimated_cost_breakdown": breakdown,
        "level": level,
        "confidence": 0.7,  # Medium confidence for heuristic-based estimates
        "reasoning": " | ".join(reasoning_parts) if reasoning_parts else f"Base {level} complexity"
    }

def analyze_complexity(title: str, body: str, labels: list[str]) -> float:
    """
    Analyze issue complexity (0-1 scale).

    Factors:
    - Title/body length and detail
    - Presence of complexity indicators
    - Label analysis
    """
    score = 0.0

    # Length-based heuristic
    text = f"{title} {body}"
    if len(text) > 1000:
        score += 0.3
    elif len(text) > 500:
        score += 0.2
    else:
        score += 0.1

    # Keyword analysis
    complex_keywords = [
        "refactor", "architecture", "integrate", "migration",
        "performance", "optimization", "scale", "distributed"
    ]
    simple_keywords = [
        "typo", "update", "fix", "minor", "small"
    ]

    text_lower = text.lower()
    for keyword in complex_keywords:
        if keyword in text_lower:
            score += 0.15
            break

    for keyword in simple_keywords:
        if keyword in text_lower:
            score -= 0.15
            break

    # Label analysis
    label_names = [label.get("name", "") if isinstance(label, dict) else str(label) for label in labels]
    if any("complex" in label.lower() or "large" in label.lower() for label in label_names):
        score += 0.3
    if any("simple" in label.lower() or "trivial" in label.lower() for label in label_names):
        score -= 0.2

    return max(0.0, min(1.0, score))
```

#### 1.4 Run Backfill

**Execution:**
```bash
cd app/server
uv run python scripts/backfill_cost_estimates.py
```

#### 1.5 Update Workflow History

After estimates are backfilled, re-sync workflows to populate the database:
```bash
uv run python -c "
from core.workflow_history import sync_workflow_history
synced = sync_workflow_history()
print(f'Updated {synced} workflows with new estimates')
"
```

---

### Phase 2: Auto-Generate Estimates for New Issues

#### 2.1 Webhook Integration

**File:** `app/server/server.py` - Add webhook handler

```python
@app.post("/webhooks/github")
async def github_webhook(request: Request):
    """
    Handle GitHub webhook events.

    Trigger: issue opened, issue labeled
    Action: Generate cost estimate
    """
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event")

    if event_type == "issues":
        action = payload.get("action")
        if action in ["opened", "labeled"]:
            issue = payload["issue"]
            issue_number = issue["number"]

            # Generate estimate
            try:
                estimate = estimate_issue_cost(
                    title=issue["title"],
                    body=issue["body"] or "",
                    labels=issue["labels"]
                )

                save_cost_estimate(issue_number, estimate)
                logger.info(f"Generated estimate for issue #{issue_number}: ${estimate['estimated_cost_total']:.2f}")

            except Exception as e:
                logger.error(f"Failed to generate estimate for issue #{issue_number}: {e}")

    return {"status": "ok"}
```

#### 2.2 Fallback Estimation

**File:** `adws/adw_sdlc_iso.py` (or similar workflow entry point)

Add estimate generation at workflow start if not already present:
```python
def run_workflow(issue_number: int):
    """Run SDLC workflow for an issue."""

    # Check if estimate exists
    estimate = get_cost_estimate(issue_number)

    if not estimate:
        # Generate estimate on-the-fly
        issue_data = fetch_github_issue(issue_number)
        estimate = estimate_issue_cost(
            title=issue_data["title"],
            body=issue_data["body"],
            labels=issue_data["labels"]
        )
        save_cost_estimate(issue_number, estimate)
        logger.info(f"Generated estimate for issue #{issue_number}: ${estimate['estimated_cost_total']:.2f}")

    # Continue with workflow...
```

---

### Phase 3: Improve Estimate Accuracy

#### 3.1 Historical Data Analysis

**File:** `scripts/analyze_estimate_accuracy.py` (new file)

```python
#!/usr/bin/env python3
"""
Analyze estimate accuracy to improve future estimates.
"""

from core.workflow_history import get_db_connection
import statistics

def analyze_accuracy():
    """Compare estimates vs actual costs."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                issue_number,
                estimated_cost_total,
                actual_cost_total,
                (actual_cost_total - estimated_cost_total) as delta,
                (actual_cost_total / estimated_cost_total) as ratio
            FROM workflow_history
            WHERE estimated_cost_total > 0
              AND actual_cost_total > 0
              AND status IN ('completed', 'failed')
        """)
        results = cursor.fetchall()

    if not results:
        print("No data available for analysis")
        return

    ratios = [r["ratio"] for r in results]
    deltas = [r["delta"] for r in results]

    print(f"Analyzed {len(results)} workflows")
    print(f"\nAccuracy Metrics:")
    print(f"  Mean ratio (actual/estimated): {statistics.mean(ratios):.2f}")
    print(f"  Median ratio: {statistics.median(ratios):.2f}")
    print(f"  Mean delta (actual-estimated): ${statistics.mean(deltas):.2f}")
    print(f"  Std deviation of ratio: {statistics.stdev(ratios) if len(ratios) > 1 else 0:.2f}")

    # Categorize accuracy
    accurate = sum(1 for r in ratios if 0.8 <= r <= 1.2)
    over_estimated = sum(1 for r in ratios if r < 0.8)
    under_estimated = sum(1 for r in ratios if r > 1.2)

    print(f"\nAccuracy Distribution:")
    print(f"  Accurate (±20%): {accurate} ({accurate/len(ratios)*100:.1f}%)")
    print(f"  Over-estimated: {over_estimated} ({over_estimated/len(ratios)*100:.1f}%)")
    print(f"  Under-estimated: {under_estimated} ({under_estimated/len(ratios)*100:.1f}%)")

if __name__ == "__main__":
    analyze_accuracy()
```

#### 3.2 Machine Learning Model (Optional Advanced)

**File:** `core/ml_cost_estimator.py` (new file)

```python
"""
ML-based cost estimation using historical workflow data.

Features:
- Issue text embeddings (title + body)
- Label encoding
- Historical similar issue costs
- Complexity indicators

Model: Simple regression or gradient boosting
"""

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer

class MLCostEstimator:
    def __init__(self):
        self.model = GradientBoostingRegressor(n_estimators=100)
        self.vectorizer = TfidfVectorizer(max_features=100)
        self.trained = False

    def train(self, training_data: list[dict]):
        """
        Train model on historical workflow data.

        training_data: [
            {
                "title": str,
                "body": str,
                "labels": list[str],
                "actual_cost": float
            },
            ...
        ]
        """
        # Extract features
        texts = [f"{d['title']} {d['body']}" for d in training_data]
        X_text = self.vectorizer.fit_transform(texts).toarray()

        # Add label features
        # Add complexity features
        # ...

        y = np.array([d["actual_cost"] for d in training_data])

        self.model.fit(X_text, y)
        self.trained = True

    def predict(self, title: str, body: str, labels: list[str]) -> float:
        """Predict cost for a new issue."""
        if not self.trained:
            raise RuntimeError("Model not trained")

        text = f"{title} {body}"
        X = self.vectorizer.transform([text]).toarray()

        return float(self.model.predict(X)[0])
```

---

## Testing Plan

### Unit Tests

**File:** `tests/test_cost_estimator.py`

```python
def test_simple_issue_estimate():
    """Test estimation for simple issues"""
    estimate = estimate_issue_cost(
        title="Fix typo in README",
        body="Change 'teh' to 'the' in line 42",
        labels=[]
    )

    assert estimate["level"] == "simple"
    assert estimate["estimated_cost_total"] < 2.0

def test_complex_issue_estimate():
    """Test estimation for complex issues"""
    estimate = estimate_issue_cost(
        title="Refactor database architecture for horizontal scaling",
        body="Migrate to distributed database system with sharding...",
        labels=["complex", "database"]
    )

    assert estimate["level"] == "complex"
    assert estimate["estimated_cost_total"] > 4.0

def test_estimate_breakdown_sums():
    """Test phase breakdown sums to total"""
    estimate = estimate_issue_cost(
        title="Add new feature",
        body="Implement user authentication",
        labels=[]
    )

    breakdown_sum = sum(estimate["estimated_cost_breakdown"].values())
    assert abs(breakdown_sum - estimate["estimated_cost_total"]) < 0.01
```

### Integration Tests

1. **Backfill Script**: Run on test database, verify estimates generated
2. **Webhook Handler**: Mock GitHub webhook, verify estimate creation
3. **Score Calculation**: Verify cost efficiency scores update after backfill

### Manual Testing

1. Run backfill script on production database
2. Verify all issues have estimates in `cost_estimates_by_issue.json`
3. Check workflow history shows non-zero cost efficiency scores
4. Validate estimate quality by comparing to actual costs

---

## Migration Strategy

### Step 1: Test Estimation Logic
```bash
# Test estimator on a few known issues
cd app/server
uv run python -c "
from core.cost_estimator import estimate_issue_cost
from core.github_integration import fetch_github_issue

for issue_num in [1, 3, 5]:
    issue = fetch_github_issue(issue_num)
    estimate = estimate_issue_cost(issue['title'], issue['body'], issue['labels'])
    print(f'Issue #{issue_num}: \${estimate[\"estimated_cost_total\"]:.2f} ({estimate[\"level\"]})')
"
```

### Step 2: Backfill All Historical Issues
```bash
# Generate estimates for all issues
uv run python scripts/backfill_cost_estimates.py
```

### Step 3: Re-sync Workflow History
```bash
# Update workflow_history table with new estimates
uv run python -c "
from core.workflow_history import sync_workflow_history
synced = sync_workflow_history()
print(f'Updated {synced} workflows')
"
```

### Step 4: Verify Score Distribution
```bash
# Check cost efficiency score distribution
sqlite3 db/workflow_history.db "
    SELECT
        ROUND(cost_efficiency_score/10)*10 as score_bucket,
        COUNT(*) as count
    FROM workflow_history
    WHERE cost_efficiency_score > 0
    GROUP BY score_bucket
    ORDER BY score_bucket
"
```

---

## Acceptance Criteria

### Phase 1 (Backfill)
- [ ] Backfill script generates estimates for all historical issues
- [ ] All workflows have `estimated_cost_total > 0`
- [ ] Cost efficiency scores show differentiation (not all 0.0)
- [ ] Estimates saved to `cost_estimates_by_issue.json`

### Phase 2 (Auto-Generation)
- [ ] New issues automatically get estimates via webhook
- [ ] Fallback estimation works when webhook misses an issue
- [ ] Estimates generated before workflow execution

### Phase 3 (Accuracy)
- [ ] Analysis script shows mean ratio within ±30% of 1.0
- [ ] At least 50% of estimates within ±20% of actual cost
- [ ] Improved estimation logic reduces variance

---

## Timeline Estimate

- **Phase 1**: 6-8 hours (backfill logic + execution)
- **Phase 2**: 4-6 hours (webhook + fallback)
- **Phase 3**: 8-12 hours (ML model + analysis)

**Total**: 18-26 hours for complete implementation

---

## Dependencies

- GitHub CLI (`gh`) or API token for issue fetching
- Access to all repository issues (including closed)
- Sufficient API quota for batch issue fetching
- (Phase 3) scikit-learn for ML model

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| GitHub API rate limits | Slow backfill | Batch requests, add delays, use GraphQL API |
| Estimate accuracy low | Scores not meaningful | Start conservative, refine with historical data |
| Closed issues inaccessible | Incomplete backfill | Focus on open/recent issues first |
| Webhook delivery failures | Missing estimates | Implement fallback estimation in workflow |

---

## Future Enhancements

1. **Adaptive estimates**: Learn from actual costs and auto-adjust
2. **Model fine-tuning**: Use workflow feedback to improve accuracy
3. **Real-time budget tracking**: Alert when workflow exceeds estimate
4. **Multi-model ensembles**: Combine heuristic + ML for better estimates
5. **Cost prediction intervals**: Provide confidence ranges (e.g., $3-5)
