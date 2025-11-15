# Cost Optimization Intelligence System

**Status:** Design Phase
**Priority:** HIGH - Strategic cost reduction across all workflows
**Impact:** 30-60% cost reduction potential

## Overview

This system adds intelligence layers to reduce LLM costs while maintaining flexibility:

1. **Input Size Analysis** - Detect oversized requests that should be split
2. **Pattern Detection** - Identify repetitive operations for script offloading
3. **Context Reduction** - Delegate deterministic tasks to Python scripts
4. **Pattern Learning** - Build library of offloadable patterns over time

## Problem Statement

**Current Cost Drivers:**
- LLMs process verbose inputs that could be split into smaller, cheaper tasks
- LLMs perform deterministic operations (running tests, file operations) that Python could handle
- LLMs load full context when only summary data is needed
- No feedback loop to learn which patterns can be automated

**Cost Example:**
```
Running test suite via LLM:
- LLM loads all test code: 50,000 tokens
- LLM interprets results: 10,000 tokens
- Total: 60,000 tokens × $0.003/1K = $0.18

Running test suite via Python script:
- Python runs tests, returns only failures
- LLM processes: 2,000 tokens × $0.003/1K = $0.006
- Savings: 97% ($0.174 saved)
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Input (GitHub Issue)                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: INPUT SIZE ANALYZER                                │
│  • Analyze word count, complexity signals                    │
│  • Determine optimal task size (sweet spot: 50-300 words)   │
│  • Recommend split if >300 words + multiple concerns         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: PATTERN MATCHER                                    │
│  • Check against known patterns (test runs, builds, etc.)   │
│  • Route to Python script if deterministic                   │
│  • Pass to LLM if creative work required                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: CONTEXT REDUCTION                                  │
│  • Scripts execute deterministic tasks                       │
│  • Return only relevant data (errors, diffs, summaries)     │
│  • LLM processes compact results, not raw outputs            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: PATTERN LEARNING                                   │
│  • Track which operations were successful                    │
│  • Build library of offloadable patterns                     │
│  • Suggest new automation opportunities                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Input Size Analyzer

**Goal:** Prevent oversized, multi-concern requests from creating bloated workflows

### Detection Criteria

```python
def should_split_request(nl_input: str, metadata: Dict) -> Dict:
    """
    Analyze if request should be split into multiple issues.

    Returns:
        {
            "should_split": bool,
            "reason": str,
            "suggested_splits": List[str],  # Suggested issue titles
            "estimated_savings": float      # Cost savings if split
        }
    """
    word_count = len(nl_input.split())

    # Red flags for splitting
    concerns = detect_concerns(nl_input)  # Frontend + backend + tests + docs = 4 concerns
    has_multiple_features = count_bullet_points(nl_input) > 3
    estimated_complexity = estimate_complexity_from_input(nl_input)

    # Decision logic
    if word_count > 300 and len(concerns) > 2:
        return {
            "should_split": True,
            "reason": f"Large input ({word_count} words) with {len(concerns)} distinct concerns",
            "suggested_splits": generate_split_suggestions(nl_input, concerns),
            "estimated_savings": calculate_split_savings(estimated_complexity, len(concerns))
        }

    # Check for diminishing returns (too small = overhead cost)
    if word_count < 30:
        return {
            "should_split": False,
            "reason": "Input too small - splitting would add overhead",
            "suggested_splits": [],
            "estimated_savings": 0.0
        }

    return {"should_split": False, ...}
```

### Concern Detection

**Technical concerns to identify:**
- Frontend work (`UI`, `component`, `React`, `styling`)
- Backend work (`API`, `endpoint`, `database`, `server`)
- Testing (`test`, `coverage`, `validation`)
- Documentation (`docs`, `README`, `guide`)
- Infrastructure (`deploy`, `CI/CD`, `build`)

**Split Example:**

**Original Issue (500 words):**
> "Add user authentication system with JWT tokens, create login UI with form validation,
> update database schema for user table, write integration tests, document the API
> endpoints in OpenAPI spec, and update deployment scripts for new env vars..."

**Recommended Split:**
1. Issue #1: "Backend - Add JWT authentication endpoints and database schema"
2. Issue #2: "Frontend - Create login UI with form validation"
3. Issue #3: "Testing - Add integration tests for auth flow"
4. Issue #4: "Docs - Document authentication API in OpenAPI"

**Cost Impact:**
- Original (1 large workflow): ~$2.50 estimated
- Split (4 focused workflows): ~$1.20 total (52% savings)

### Sweet Spot Optimization

```python
OPTIMAL_RANGES = {
    "word_count": (50, 300),      # Clarity sweet spot
    "concerns": (1, 2),           # Focus sweet spot
    "estimated_duration": (300, 1800),  # 5-30 minutes
}

def calculate_split_benefit_score(current: Dict, after_split: List[Dict]) -> float:
    """
    Score whether splitting provides net benefit.
    Returns negative if splitting would cost more.
    """
    # Factor in:
    # - Reduced context per workflow (positive)
    # - Workflow overhead (negative)
    # - Parallelization potential (positive)
    # - Dependency coordination cost (negative)
    pass
```

---

## Layer 2: Pattern Detection & Script Offloading

**Goal:** Route deterministic operations to Python scripts instead of LLM

### Known Patterns Library

**Pattern Registry** (`scripts/patterns/registry.json`):

```json
{
  "test_runner": {
    "triggers": ["run tests", "test suite", "pytest", "vitest"],
    "script": "scripts/smart_test_runner.py",
    "description": "Run tests and return only failures with error context",
    "avg_cost_llm": 0.18,
    "avg_cost_script": 0.006,
    "savings_percent": 97
  },
  "build_validator": {
    "triggers": ["build", "compile", "typecheck"],
    "script": "scripts/smart_build.py",
    "description": "Run build and return only errors with file locations",
    "avg_cost_llm": 0.15,
    "avg_cost_script": 0.004,
    "savings_percent": 97
  },
  "dependency_updater": {
    "triggers": ["update dependencies", "npm update", "upgrade packages"],
    "script": "scripts/smart_dependency_update.py",
    "description": "Update deps, run tests, report breaking changes only",
    "avg_cost_llm": 0.25,
    "avg_cost_script": 0.008,
    "savings_percent": 97
  },
  "code_formatter": {
    "triggers": ["format code", "prettier", "black"],
    "script": "scripts/smart_formatter.py",
    "description": "Run formatter and return diff summary",
    "avg_cost_llm": 0.10,
    "avg_cost_script": 0.002,
    "savings_percent": 98
  }
}
```

### Pattern Matching Engine

```python
def match_pattern(nl_input: str, task_context: Dict) -> Optional[str]:
    """
    Match input against known patterns.

    Returns:
        Script path if pattern matched, None otherwise
    """
    patterns = load_pattern_registry()

    for pattern_name, pattern_config in patterns.items():
        # Check triggers
        if any(trigger in nl_input.lower() for trigger in pattern_config["triggers"]):
            # Verify context is appropriate
            if is_safe_to_offload(task_context, pattern_config):
                return pattern_config["script"]

    return None
```

### Smart Test Runner Example

**Script:** `scripts/smart_test_runner.py`

```python
#!/usr/bin/env python3
"""
Smart test runner that reduces LLM context by 95%.

Instead of LLM loading all test code and interpreting results,
this script runs tests and returns ONLY:
- Summary (X passed, Y failed)
- Failed test details (name, error, relevant code)
- Actionable next steps

LLM only processes failures, not full test suite output.
"""

import subprocess
import json
from typing import Dict, List

def run_tests() -> Dict:
    """Run test suite and extract meaningful data."""

    # Run pytest with JSON output
    result = subprocess.run(
        ["pytest", "--json-report", "--json-report-file=test_results.json"],
        capture_output=True,
        text=True
    )

    with open("test_results.json") as f:
        test_data = json.load(f)

    # Extract only failures
    failures = []
    for test in test_data.get("tests", []):
        if test["outcome"] == "failed":
            failures.append({
                "name": test["nodeid"],
                "error": test["call"]["longrepr"],
                "file": test["file"],
                "line": test["line"]
            })

    return {
        "summary": {
            "total": test_data["summary"]["total"],
            "passed": test_data["summary"]["passed"],
            "failed": test_data["summary"]["failed"]
        },
        "failures": failures,
        "next_steps": generate_next_steps(failures)
    }

def generate_next_steps(failures: List[Dict]) -> List[str]:
    """Generate actionable recommendations."""
    if not failures:
        return ["All tests passing - ready to commit"]

    steps = []
    for failure in failures:
        steps.append(f"Fix {failure['name']} in {failure['file']}:{failure['line']}")

    return steps

if __name__ == "__main__":
    results = run_tests()

    # Print compact JSON for LLM consumption
    print(json.dumps(results, indent=2))
```

**LLM Integration:**

```python
# In ADW workflow
def handle_test_request(nl_input: str) -> str:
    """Handle test running with smart offloading."""

    # Check if this can be offloaded
    if "run tests" in nl_input.lower():
        # Offload to script
        result = subprocess.run(
            ["python3", "scripts/smart_test_runner.py"],
            capture_output=True,
            text=True
        )

        test_results = json.loads(result.stdout)

        # LLM only processes compact results
        prompt = f"""
        Test Results:
        - Passed: {test_results['summary']['passed']}
        - Failed: {test_results['summary']['failed']}

        Failures:
        {json.dumps(test_results['failures'], indent=2)}

        Please fix the failing tests.
        """

        # LLM processes ~2K tokens instead of ~60K tokens
        return call_llm(prompt)
```

---

## Layer 3: Context Reduction Strategies

**Goal:** Minimize tokens loaded into LLM context

### Strategy Table

| Operation | Traditional Approach | Optimized Approach | Token Savings |
|-----------|---------------------|-------------------|---------------|
| Run tests | Load all test files (50K tokens) | Script returns failures only (2K tokens) | 96% |
| Build project | Load build output (30K tokens) | Script returns errors only (1K tokens) | 97% |
| Git diff | Full diff (20K tokens) | Summary + changed files (3K tokens) | 85% |
| Dependency check | Full package.json + lock file (40K tokens) | Outdated packages list (2K tokens) | 95% |
| Log analysis | Full logs (100K tokens) | Error patterns + context (5K tokens) | 95% |

### Context Reduction Helpers

**File:** `app/server/core/context_optimizer.py`

```python
def optimize_test_context(test_results: Dict) -> str:
    """Reduce test output to essential information."""
    if test_results["summary"]["failed"] == 0:
        return f"All {test_results['summary']['total']} tests passed."

    # Only include failures
    context = f"Tests: {test_results['summary']['passed']} passed, {test_results['summary']['failed']} failed\n\n"
    context += "Failures:\n"
    for failure in test_results["failures"]:
        context += f"- {failure['name']}\n"
        context += f"  Error: {failure['error'][:200]}...\n"  # Truncate long errors

    return context

def optimize_build_context(build_output: str) -> str:
    """Extract only errors from build output."""
    lines = build_output.split("\n")
    error_lines = [line for line in lines if "error" in line.lower() or "failed" in line.lower()]

    if not error_lines:
        return "Build successful"

    return "Build errors:\n" + "\n".join(error_lines[:20])  # Max 20 errors

def optimize_git_diff(diff_output: str) -> str:
    """Summarize git diff instead of showing full changes."""
    files_changed = extract_changed_files(diff_output)
    stats = calculate_diff_stats(diff_output)

    summary = f"Changed files: {len(files_changed)}\n"
    summary += f"Lines added: {stats['additions']}, removed: {stats['deletions']}\n\n"
    summary += "Files:\n" + "\n".join(f"- {f}" for f in files_changed[:10])

    return summary
```

---

## Layer 4: Pattern Learning System

**Goal:** Automatically identify new automation opportunities

### Learning Database

**Table:** `pattern_learning` (SQLite)

```sql
CREATE TABLE pattern_learning (
    id INTEGER PRIMARY KEY,
    operation_name TEXT NOT NULL,
    trigger_keywords TEXT NOT NULL,  -- JSON array
    frequency_count INTEGER DEFAULT 1,
    avg_llm_tokens INTEGER,
    avg_llm_cost REAL,
    estimated_script_cost REAL,
    potential_savings REAL,
    confidence_score REAL,  -- 0-100, based on repetition
    status TEXT DEFAULT 'candidate',  -- candidate, approved, implemented
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Learning Algorithm

```python
def track_operation(workflow: Dict):
    """Track operations for pattern learning."""

    nl_input = workflow["nl_input"]
    actual_cost = workflow["actual_cost_total"]
    tokens_used = workflow.get("total_tokens", 0)

    # Extract operation keywords
    keywords = extract_operation_keywords(nl_input)

    # Check if we've seen this pattern before
    for keyword in keywords:
        pattern = db.query("SELECT * FROM pattern_learning WHERE operation_name = ?", keyword)

        if pattern:
            # Update existing pattern
            pattern["frequency_count"] += 1
            pattern["avg_llm_cost"] = (pattern["avg_llm_cost"] + actual_cost) / 2
            pattern["avg_llm_tokens"] = (pattern["avg_llm_tokens"] + tokens_used) / 2
            pattern["confidence_score"] = calculate_confidence(pattern["frequency_count"])
            pattern["last_seen"] = datetime.now()

            db.update(pattern)

            # Check if pattern is candidate for automation
            if pattern["frequency_count"] >= 5 and pattern["confidence_score"] > 70:
                suggest_automation(pattern)
        else:
            # Create new pattern
            db.insert({
                "operation_name": keyword,
                "trigger_keywords": json.dumps([keyword]),
                "frequency_count": 1,
                "avg_llm_tokens": tokens_used,
                "avg_llm_cost": actual_cost,
                "estimated_script_cost": estimate_script_cost(keyword),
                "confidence_score": 10,
                "status": "candidate"
            })

def suggest_automation(pattern: Dict):
    """Suggest creating automation script for this pattern."""

    potential_savings = (pattern["avg_llm_cost"] - pattern["estimated_script_cost"]) * pattern["frequency_count"]

    if potential_savings > 0.50:  # Threshold: $0.50 savings potential
        # Create GitHub issue suggesting automation
        create_github_issue(
            title=f"Automation Opportunity: {pattern['operation_name']}",
            body=f"""
## Pattern Detected

**Operation:** {pattern['operation_name']}
**Frequency:** {pattern['frequency_count']} times
**Avg LLM Cost:** ${pattern['avg_llm_cost']:.4f}
**Estimated Script Cost:** ${pattern['estimated_script_cost']:.4f}
**Potential Savings:** ${potential_savings:.2f}

### Recommendation

Create a Python script to handle this operation deterministically.

**Triggers:** {pattern['trigger_keywords']}
**Status:** {pattern['status']}
**Confidence:** {pattern['confidence_score']}%

This pattern has been observed {pattern['frequency_count']} times with high consistency.
Automating it could save approximately ${potential_savings:.2f} in LLM costs.
            """,
            labels=["optimization", "automation-candidate"]
        )
```

---

## Implementation Plan

### Phase 1: Input Size Analyzer (Week 1)

1. Create `app/server/core/input_analyzer.py`
2. Implement `should_split_request()` logic
3. Add GitHub webhook handler to analyze new issues
4. Auto-comment on issues with split recommendations

### Phase 2: Smart Test Runner (Week 1-2)

1. Create `scripts/smart_test_runner.py`
2. Integrate with ADW workflow detection
3. Measure cost savings on 10 test workflows

### Phase 3: Pattern Registry (Week 2)

1. Create `scripts/patterns/registry.json`
2. Implement pattern matching engine
3. Add 5 initial patterns (tests, build, format, deps, git)

### Phase 4: Context Optimization (Week 3)

1. Create `app/server/core/context_optimizer.py`
2. Implement helper functions for each operation type
3. Integrate with workflow execution

### Phase 5: Pattern Learning (Week 4)

1. Create pattern_learning database table
2. Implement tracking in workflow sync
3. Auto-generate automation suggestions

---

## Success Metrics

**Target Cost Reduction:** 30-60% across all workflows

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Avg workflow cost | $0.50 | $0.25 | workflow_history.actual_cost_total |
| Avg tokens per workflow | 80K | 40K | workflow_history.total_tokens |
| Script offload rate | 0% | 40% | Count of script-handled operations |
| Split recommendation acceptance | N/A | 60% | Issues split after recommendation |
| Pattern library size | 0 | 20+ | Number of automated patterns |

---

## Cost-Benefit Analysis

**Investment:**
- Development time: ~4 weeks
- Initial testing: ~1 week
- Total: ~$5K in development cost

**Returns (Monthly):**
- Current workflow costs: ~$200/month (assumption)
- With 40% reduction: ~$80/month savings
- ROI timeline: ~5-6 months

**Long-term:**
- Pattern library grows automatically
- Savings compound over time
- Reduced vendor lock-in (less dependent on LLM pricing)

---

## References

- Current analytics: `app/server/core/workflow_analytics.py`
- Workflow history: `app/server/core/workflow_history.py`
- Phase 3B scoring: `docs/PHASE_3B_COMPLETION_HANDOFF.md`

---

## Next Steps

1. Review and approve this design
2. Prioritize which layer to implement first
3. Create implementation issues for each phase
4. Start with highest-impact, lowest-effort items (Smart Test Runner)
