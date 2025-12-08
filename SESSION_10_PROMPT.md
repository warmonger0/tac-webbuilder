# Task: Error Analytics System

## Context
I'm working on the tac-webbuilder project. The system logs errors in workflow_history (failure_reason, phase_errors) and hook_events, but there's no systematic error analysis. This session implements an error analytics system to identify error patterns, failure-prone phases, and root causes for proactive debugging.

## Objective
Create an error analytics system that analyzes failure patterns, identifies common error types, tracks error rates by phase, and provides actionable debugging recommendations.

## Background Information
- **Data Sources:** workflow_history.failure_reason, workflow_history.phase_errors (JSON), hook_events (error events)
- **Current Gap:** No error pattern analysis or root cause identification
- **Use Cases:** Identify recurring failures, debug systematically, prevent future errors
- **Output:** Error reports, pattern detection, debugging recommendations

---

## Implementation Steps

### Step 1: Error Analytics Service (90 min)

**Create:** `app/server/services/error_analytics_service.py` (~300 lines)

**Template:** See `.claude/templates/SERVICE_LAYER.md`

**Key Methods:**
```python
class ErrorAnalyticsService:
    def get_error_summary(self, days=30) -> ErrorSummary
    def analyze_by_phase(self, days=30) -> PhaseErrorBreakdown
    def find_error_patterns(self, days=30) -> List[ErrorPattern]
    def get_failure_trends(self, days=30) -> TrendData
    def get_debugging_recommendations() -> List[Recommendation]
```

**Error Pattern Detection:**
```python
def find_error_patterns(self, days=30):
    """Detect recurring error patterns."""
    # Group errors by similarity (keyword matching)
    # Common patterns:
    # - "Module not found" → Import errors
    # - "ECONNREFUSED" → Connection errors
    # - "timeout" → Timeout errors
    # - "404" → Missing resource errors
    # Count occurrences and rank by frequency
```

**Phase Error Analysis:**
```python
def analyze_by_phase(self, days=30):
    """Analyze error rates by ADW phase."""
    # Parse phase_errors JSON from workflow_history
    # Calculate failure rate per phase
    # Identify phases with >10% failure rate
    # Return breakdown with error counts and types
```

**Reference:** `services/workflow_service.py` for database queries

---

### Step 2: Pydantic Models (20 min)

**Modify:** `app/server/models/workflow.py`

**Add Models:**
```python
@dataclass
class ErrorSummary:
    total_workflows: int
    failed_workflows: int
    failure_rate: float
    top_errors: List[Tuple[str, int]]  # (error_type, count)
    most_problematic_phase: str

@dataclass
class PhaseErrorBreakdown:
    phase_error_counts: Dict[str, int]
    phase_failure_rates: Dict[str, float]
    total_errors: int

@dataclass
class ErrorPattern:
    pattern_name: str  # "Import Error", "Connection Error"
    occurrences: int
    example_message: str
    affected_phases: List[str]
    recommendation: str

@dataclass
class DebugRecommendation:
    issue: str
    severity: str  # 'high', 'medium', 'low'
    root_cause: str
    solution: str
    estimated_fix_time: str
```

---

### Step 3: API Routes (30 min)

**Create:** `app/server/routes/error_analytics_routes.py` (~150 lines)

**Endpoints:**
```python
@router.get("/api/error-analytics/summary")
async def get_error_summary(days: int = 30)

@router.get("/api/error-analytics/by-phase")
async def get_phase_errors(days: int = 30)

@router.get("/api/error-analytics/patterns")
async def get_error_patterns(days: int = 30)

@router.get("/api/error-analytics/trends")
async def get_failure_trends(days: int = 30)

@router.get("/api/error-analytics/recommendations")
async def get_debugging_recommendations()
```

**Register in `server.py`:**
```python
from app.server.routes.error_analytics_routes import router as error_analytics_router
app.include_router(error_analytics_router)
```

---

### Step 4: CLI Tool (60 min)

**Create:** `scripts/analyze_errors.py` (~250 lines)

**Template:** See `.claude/templates/CLI_TOOL.md`

**CLI Commands:**
```python
class ErrorAnalysisCLI:
    def show_summary(self, days=30)
    def show_phase_breakdown(self, days=30)
    def show_patterns(self, days=30)
    def show_trends(self, days=30)
    def show_recommendations()
    def generate_report(self, output_file)
```

**Arguments:**
```python
parser.add_argument('--days', type=int, default=30)
parser.add_argument('--summary', action='store_true')
parser.add_argument('--phase', action='store_true')
parser.add_argument('--patterns', action='store_true')
parser.add_argument('--trends', action='store_true')
parser.add_argument('--recommendations', action='store_true')
parser.add_argument('--report', action='store_true')
parser.add_argument('--output', type=str, default='error_analysis_report.md')
```

**Output Format:**
```
================================================================================
ERROR ANALYSIS - Last 30 Days
================================================================================

SUMMARY
Total workflows: 145
Failed workflows: 12
Failure rate: 8.3%
Most problematic phase: Test (5 failures)

TOP ERROR PATTERNS
1. Import Error (7 occurrences)
   Example: "ModuleNotFoundError: No module named 'requests'"
   Recommendation: Add missing dependencies to requirements.txt

2. Connection Error (3 occurrences)
   Example: "ECONNREFUSED localhost:9100"
   Recommendation: Check port availability before starting services

3. Timeout Error (2 occurrences)
   Example: "Command timed out after 120s"
   Recommendation: Increase timeout or optimize long-running operations

PHASE BREAKDOWN
Plan:     0 errors (0.0%)
Build:    4 errors (5.2%)
Test:     5 errors (6.5%)
Lint:     3 errors (3.9%)
```

---

### Step 5: Pattern Matching Rules (30 min)

**Add to error_analytics_service.py:**

**Error Classification:**
```python
ERROR_PATTERNS = {
    'import_error': {
        'keywords': ['ModuleNotFoundError', 'ImportError', 'No module named'],
        'category': 'Dependency Issue',
        'recommendation': 'Add missing package to requirements.txt'
    },
    'connection_error': {
        'keywords': ['ECONNREFUSED', 'Connection refused', 'Failed to connect'],
        'category': 'Network Issue',
        'recommendation': 'Check service availability and port allocation'
    },
    'timeout_error': {
        'keywords': ['timeout', 'timed out', 'TimeoutError'],
        'category': 'Performance Issue',
        'recommendation': 'Increase timeout or optimize operation'
    },
    'syntax_error': {
        'keywords': ['SyntaxError', 'invalid syntax'],
        'category': 'Code Quality',
        'recommendation': 'Run linter before committing'
    },
    'type_error': {
        'keywords': ['TypeError', 'type object'],
        'category': 'Type Issue',
        'recommendation': 'Add type hints and use mypy'
    }
}

def classify_error(self, error_message: str) -> str:
    """Classify error message into pattern category."""
    for pattern_name, pattern_info in ERROR_PATTERNS.items():
        if any(kw in error_message for kw in pattern_info['keywords']):
            return pattern_name
    return 'unknown'
```

---

### Step 6: Tests (45 min)

**Create:** `app/server/tests/services/test_error_analytics_service.py` (~150 lines)

**Template:** See `.claude/templates/PYTEST_TESTS.md`

**Test Cases:**
1. `test_get_error_summary` - Summary statistics
2. `test_analyze_by_phase` - Phase error breakdown
3. `test_find_error_patterns` - Pattern detection
4. `test_classify_error` - Error classification accuracy
5. `test_empty_error_data` - Handle no errors gracefully
6. `test_json_phase_errors_parsing` - Parse phase_errors JSON

**Fixture:**
```python
@pytest.fixture
def sample_failed_workflows(db_connection):
    """Create sample workflows with errors."""
    workflows = [
        {
            'status': 'failed',
            'failure_reason': 'ModuleNotFoundError: No module named requests',
            'phase_errors': json.dumps({'Build': 'Import failed'}),
            'created_at': '2025-12-01'
        },
        {
            'status': 'failed',
            'failure_reason': 'ECONNREFUSED localhost:9100',
            'phase_errors': json.dumps({'Test': 'Connection refused'}),
            'created_at': '2025-12-02'
        },
        # More samples...
    ]
```

**Run tests:**
```bash
pytest app/server/tests/services/test_error_analytics_service.py -v
```

---

### Step 7: Documentation (20 min)

**Create:** `docs/features/error-analytics.md` (~200 lines)

**Sections:**
- Overview and use cases
- Error pattern catalog
- API endpoint reference
- CLI usage examples
- Debugging workflow
- Prevention strategies

---

## Success Criteria

- ✅ Service analyzes errors by phase, pattern, and trend
- ✅ Pattern detection identifies recurring error types
- ✅ 5 API endpoints for error analytics
- ✅ CLI tool generates error reports with recommendations
- ✅ Error classification system with 5+ patterns
- ✅ All tests passing (6/6)
- ✅ Documentation with debugging guide

---

## Files Expected to Change

**Created (5):**
- `app/server/services/error_analytics_service.py` (~300 lines)
- `app/server/routes/error_analytics_routes.py` (~150 lines)
- `scripts/analyze_errors.py` (~250 lines)
- `app/server/tests/services/test_error_analytics_service.py` (~150 lines)
- `docs/features/error-analytics.md` (~200 lines)

**Modified (2):**
- `app/server/models/workflow.py` (add 4 error analytics models)
- `app/server/server.py` (register routes)

---

## Quick Reference

**Run CLI:**
```bash
python scripts/analyze_errors.py --summary --days 30
python scripts/analyze_errors.py --patterns
python scripts/analyze_errors.py --recommendations
python scripts/analyze_errors.py --report
```

**Test API:**
```bash
curl http://localhost:8000/api/error-analytics/summary?days=30
curl http://localhost:8000/api/error-analytics/patterns
```

**Run tests:**
```bash
pytest app/server/tests/services/test_error_analytics_service.py -v
```

---

## Estimated Time

- Step 1 (Service): 90 min
- Step 2 (Models): 20 min
- Step 3 (API): 30 min
- Step 4 (CLI): 60 min
- Step 5 (Pattern Rules): 30 min
- Step 6 (Tests): 45 min
- Step 7 (Docs): 20 min

**Total: 3-4 hours**

---

## Session Completion Template

```markdown
## ✅ Session 10 Complete - Error Analytics

**Duration:** ~X hours
**Status:** Complete ✅
**Next:** Ready for Session 11 (Latency Analytics)

### What Was Done
- Error analytics service with pattern detection
- 5 API endpoints for error analysis
- CLI tool with debugging recommendations
- Error classification system (X patterns)
- 6/6 tests passing

### Key Results
- Identified X error patterns
- Most common error: [Pattern] (X occurrences)
- Most problematic phase: [Phase] (X% failure rate)
- X debugging recommendations generated

### Files Changed
**Created (5):**
- services/error_analytics_service.py
- routes/error_analytics_routes.py
- scripts/analyze_errors.py
- tests/services/test_error_analytics_service.py
- docs/features/error-analytics.md

**Modified (2):**
- models/workflow.py
- server.py

### Next Session
Session 11: Latency Analytics (3-4 hours)
```
