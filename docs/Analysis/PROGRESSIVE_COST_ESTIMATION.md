# Progressive Cost Estimation System

**Goal:** Learn from historical data to provide increasingly accurate cost predictions

---

## Architecture

### Data Flow:

```
Issue Created
    ↓
Historical Analysis ──→ Cost Prediction (confidence: low → high over time)
    ↓
User Approval (if > threshold)
    ↓
Workflow Execution
    ↓
Actual Cost Tracking
    ↓
Update Historical Database ──→ Improve Future Predictions
```

---

## Phase 1: Cost Tracking Infrastructure

### A. Cost History Database

**File:** `costs/cost_history.jsonl`

**Format:** One JSON object per line (append-only)

```json
{
  "timestamp": "2025-11-14T06:51:09Z",
  "issue_number": 1,
  "issue_title": "Add workflows documentation tab with 2-column layout",
  "issue_body_preview": "Add a new sub-tab or section within...",
  "classification": "feature",
  "complexity_analysis": {
    "level": "lightweight",
    "confidence": 0.85,
    "reasoning": "Simple UI change detected | Single file scope"
  },
  "workflow_used": "adw_sdlc_zte_iso",
  "predicted_cost": 0.50,
  "actual_cost": 4.91,
  "variance_pct": 882.0,
  "phases": {
    "plan": {"cost": 0.29, "tokens": 315000},
    "build": {"cost": 2.87, "tokens": 6505384},
    "test": {"cost": 0.15, "tokens": 159000},
    "review": {"cost": 0.53, "tokens": 822000},
    "document": {"cost": 0.17, "tokens": 181000},
    "ship": {"cost": 0.90, "tokens": 320000}
  },
  "cache_efficiency": 0.953,
  "total_tokens": 9383819,
  "files_changed": ["app/client/src/workflows.ts", "app/client/src/main.ts", ...],
  "lines_changed": 689
}
```

### B. Enhanced Cost Analysis Script

**Update:** `scripts/analyze_adw_cost.py`

Add historical tracking:

```python
def save_to_history(adw_id: str, analysis: dict):
    """Append cost analysis to historical database"""
    history_file = Path("costs/cost_history.jsonl")
    history_file.parent.mkdir(exist_ok=True)

    # Load issue metadata from state
    state = ADWState.load(adw_id)
    issue = fetch_issue(state.issue_number)

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "adw_id": adw_id,
        "issue_number": state.issue_number,
        "issue_title": issue.title,
        "issue_body_preview": issue.body[:200] if issue.body else "",
        "classification": state.issue_class,
        "workflow_used": determine_workflow_used(state),
        "actual_cost": analysis["total_cost"],
        "phases": analysis["phases"],
        "cache_efficiency": analysis["cache_efficiency"],
        "total_tokens": analysis["total_tokens"],
        "files_changed": get_changed_files(adw_id),
        "lines_changed": get_lines_changed(adw_id)
    }

    with history_file.open("a") as f:
        f.write(json.dumps(record) + "\n")
```

---

## Phase 2: Prediction Engine

### A. Feature Extraction

```python
from dataclasses import dataclass
from typing import List

@dataclass
class IssueFeatures:
    """Extracted features for cost prediction"""

    # Text features
    title_length: int
    body_length: int
    has_code_blocks: bool
    has_file_paths: bool

    # Keyword features
    ui_keywords_count: int  # button, color, style, layout
    backend_keywords_count: int  # api, database, server
    complexity_keywords_count: int  # refactor, migration, integration

    # Scope indicators
    mentioned_files_count: int
    mentioned_directories: List[str]
    frontend_only: bool
    backend_only: bool
    full_stack: bool
    docs_only: bool

    # Classification
    issue_type: str  # feature, bug, chore

def extract_features(issue: GitHubIssue) -> IssueFeatures:
    """Extract predictive features from issue"""
    text = f"{issue.title} {issue.body}".lower()

    return IssueFeatures(
        title_length=len(issue.title),
        body_length=len(issue.body) if issue.body else 0,
        has_code_blocks="```" in issue.body if issue.body else False,
        has_file_paths="/" in text or ".tsx" in text or ".py" in text,
        ui_keywords_count=sum(1 for kw in UI_KEYWORDS if kw in text),
        backend_keywords_count=sum(1 for kw in BACKEND_KEYWORDS if kw in text),
        complexity_keywords_count=sum(1 for kw in COMPLEXITY_KEYWORDS if kw in text),
        mentioned_files_count=count_file_mentions(text),
        mentioned_directories=extract_directories(text),
        frontend_only="app/client" in text and "app/server" not in text,
        backend_only="app/server" in text and "app/client" not in text,
        full_stack="app/client" in text and "app/server" in text,
        docs_only=is_docs_only(text)
    )
```

### B. Similarity Search

```python
def find_similar_issues(
    target_issue: GitHubIssue,
    history: List[dict],
    top_k: int = 5
) -> List[dict]:
    """Find historically similar issues using feature similarity"""

    target_features = extract_features(target_issue)

    similarities = []
    for historical_record in history:
        # Reconstruct historical issue features
        hist_issue = reconstruct_issue(historical_record)
        hist_features = extract_features(hist_issue)

        # Calculate similarity score
        similarity = calculate_feature_similarity(
            target_features,
            hist_features
        )

        similarities.append({
            "record": historical_record,
            "similarity": similarity
        })

    # Return top K most similar
    similarities.sort(key=lambda x: x["similarity"], reverse=True)
    return [s["record"] for s in similarities[:top_k]]


def calculate_feature_similarity(f1: IssueFeatures, f2: IssueFeatures) -> float:
    """Calculate similarity score between two feature sets"""

    score = 0.0

    # Boolean features (exact match)
    if f1.frontend_only == f2.frontend_only:
        score += 0.2
    if f1.backend_only == f2.backend_only:
        score += 0.2
    if f1.full_stack == f2.full_stack:
        score += 0.2
    if f1.docs_only == f2.docs_only:
        score += 0.2

    # Classification
    if f1.issue_type == f2.issue_type:
        score += 0.15

    # Numeric features (normalized distance)
    keyword_similarity = 1 - abs(
        f1.ui_keywords_count - f2.ui_keywords_count
    ) / max(f1.ui_keywords_count, f2.ui_keywords_count, 1)
    score += 0.05 * keyword_similarity

    return score
```

### C. Cost Prediction

```python
@dataclass
class CostPrediction:
    """Predicted cost with confidence interval"""
    estimated_cost: float
    confidence_interval: Tuple[float, float]  # (low, high)
    confidence_score: float  # 0.0 to 1.0
    similar_issues_count: int
    reasoning: str


def predict_cost(issue: GitHubIssue) -> CostPrediction:
    """Predict cost using historical data"""

    # Load history
    history = load_cost_history()

    if len(history) < 5:
        # Not enough data - use heuristics only
        return predict_cost_heuristic(issue)

    # Find similar issues
    similar = find_similar_issues(issue, history, top_k=5)

    if not similar:
        return predict_cost_heuristic(issue)

    # Calculate weighted average
    costs = [record["actual_cost"] for record in similar]
    similarities = [
        calculate_feature_similarity(
            extract_features(issue),
            extract_features(reconstruct_issue(record))
        )
        for record in similar
    ]

    # Weighted mean
    total_weight = sum(similarities)
    weighted_cost = sum(
        cost * sim for cost, sim in zip(costs, similarities)
    ) / total_weight

    # Confidence based on data consistency
    cost_variance = np.var(costs)
    confidence = min(1.0, 1.0 / (1.0 + cost_variance))

    # Confidence interval (wider for low confidence)
    margin = weighted_cost * (0.5 - 0.3 * confidence)

    return CostPrediction(
        estimated_cost=weighted_cost,
        confidence_interval=(
            max(0, weighted_cost - margin),
            weighted_cost + margin
        ),
        confidence_score=confidence,
        similar_issues_count=len(similar),
        reasoning=format_reasoning(similar, similarities)
    )
```

---

## Phase 3: User Interface

### A. Pre-Flight Cost Warning

```python
def show_cost_warning(issue_number: int):
    """Show cost prediction before starting workflow"""

    issue = fetch_issue(issue_number)
    prediction = predict_cost(issue)

    print(f"\n{'='*80}")
    print(f"💰 Cost Prediction for Issue #{issue_number}")
    print(f"{'='*80}\n")

    print(f"Estimated Cost: ${prediction.estimated_cost:.2f}")
    print(f"Confidence Interval: ${prediction.confidence_interval[0]:.2f} - ${prediction.confidence_interval[1]:.2f}")
    print(f"Confidence: {prediction.confidence_score:.0%}")
    print(f"Based on {prediction.similar_issues_count} similar issues\n")

    print(f"Reasoning:")
    print(f"{prediction.reasoning}\n")

    # Warning for high costs
    if prediction.estimated_cost > 2.00:
        print(f"⚠️  WARNING: This is predicted to be an expensive operation!")
        print(f"   Consider:")
        print(f"   1. Breaking into smaller issues")
        print(f"   2. Using manual implementation")
        print(f"   3. Narrowing scope\n")

    # Prompt user
    response = input("Proceed with workflow? (y/n): ")
    return response.lower() == 'y'
```

### B. Cost Tracking Dashboard

```bash
# scripts/cost_dashboard.py
uv run scripts/cost_dashboard.py

# Output:
╔════════════════════════════════════════════════════════════╗
║              ADW Cost Dashboard                            ║
╠════════════════════════════════════════════════════════════╣
║  Total Issues: 15                                          ║
║  Total Cost: $42.18                                        ║
║  Average Cost: $2.81                                       ║
╠════════════════════════════════════════════════════════════╣
║  Cost by Type:                                             ║
║    Lightweight (5): $1.20 (avg $0.24)                      ║
║    Standard (7): $18.90 (avg $2.70)                        ║
║    Complex (3): $22.08 (avg $7.36)                         ║
╠════════════════════════════════════════════════════════════╣
║  Prediction Accuracy:                                      ║
║    Mean Absolute Error: $0.45                              ║
║    Accuracy: 84%                                           ║
╚════════════════════════════════════════════════════════════╝

Recent Issues:
  #15 | Add export feature | Predicted: $1.20 | Actual: $1.35 | 12% over
  #14 | Fix button styling | Predicted: $0.30 | Actual: $0.28 | 7% under
  #13 | Database migration | Predicted: $4.50 | Actual: $4.92 | 9% over
```

---

## Phase 4: Continuous Improvement

### Learning Cycle:

```
1. Execute workflow
2. Track actual cost
3. Compare to prediction
4. Calculate error
5. Update model weights
6. Improve next prediction
```

### Adaptive Thresholds:

```python
# Adjust complexity thresholds based on accuracy

if prediction_accuracy > 0.90:
    # Predictions are reliable - be more aggressive with routing
    LIGHTWEIGHT_THRESHOLD = -1  # Route more to lightweight
else:
    # Predictions uncertain - be conservative
    LIGHTWEIGHT_THRESHOLD = -3  # Only route obvious cases
```

---

## Implementation Timeline

### Week 1: Infrastructure

- ✅ Create cost_history.jsonl format
- ✅ Update analyze_adw_cost.py to save history
- ✅ Test with existing Issue #1 data

### Week 2: Prediction Engine

- [ ] Implement feature extraction
- [ ] Implement similarity search
- [ ] Implement cost prediction
- [ ] Test with 5+ historical issues

### Week 3: User Interface

- [ ] Add pre-flight cost warning
- [ ] Integrate into workflow entry points
- [ ] Create cost dashboard
- [ ] Documentation

### Week 4: Refinement

- [ ] Gather prediction accuracy data
- [ ] Tune feature weights
- [ ] Adjust thresholds
- [ ] Deploy to production

---

## Success Metrics

### Targets:

- **Prediction Accuracy:** 80%+ within 20% of actual cost
- **User Satisfaction:** 90%+ find predictions helpful
- **Cost Reduction:** 70%+ overall cost reduction from baseline
- **Confidence Growth:** Prediction confidence increases from 40% → 90% over 20 issues

### Monitoring:

```python
# Track continuously
metrics = {
    "total_predictions": 0,
    "accurate_predictions": 0,  # Within 20% of actual
    "prediction_errors": [],
    "confidence_trend": []
}
```

---

## Future Enhancements

1. **ML Model:** Replace heuristics with trained model (scikit-learn, XGBoost)
2. **Text Embeddings:** Use semantic similarity (sentence-transformers)
3. **Time-based Patterns:** Account for time of day, day of week
4. **User Feedback:** Allow users to rate prediction accuracy
5. **Cost Optimization Suggestions:** Automatically suggest ways to reduce cost

---

## Appendix: Heuristic Baseline

For cold start (< 5 historical issues):

```python
def predict_cost_heuristic(issue: GitHubIssue) -> CostPrediction:
    """Baseline prediction using only heuristics"""

    features = extract_features(issue)
    base_cost = 2.00  # Default

    # Adjustments
    if features.docs_only:
        base_cost = 0.25
    elif features.frontend_only:
        base_cost = 1.00
    elif features.backend_only:
        base_cost = 1.50
    elif features.full_stack:
        base_cost = 3.50

    # Complexity adjustments
    base_cost *= (1 + 0.1 * features.complexity_keywords_count)

    return CostPrediction(
        estimated_cost=base_cost,
        confidence_interval=(base_cost * 0.5, base_cost * 1.5),
        confidence_score=0.4,  # Low confidence without data
        similar_issues_count=0,
        reasoning="Heuristic-based prediction (insufficient historical data)"
    )
```
